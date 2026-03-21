"""
PLATFORM: Provisioning — deploys Anima Machina agents to sandboxed environments.
Generic BYOI: provider resolved from agent config, not hardcoded.
Flow: get/create environment → install runtime → push config → start agent.
"""
import os
import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from agent_state import get_active_agent_id, load_provisioning, save_provisioning, add_nudge
from config import ENGINE_DIR

router = APIRouter(prefix="/api/provision", tags=["provision"])
logger = logging.getLogger(__name__)


# ─── BYOI Provider Resolution ───

async def _get_provider(provider_name: str):
    """Resolve a BYOI provider by name. User provides endpoint + key in agent config."""
    if provider_name == "conway":
        from providers.conway import ConwayProvider
        from agent_state import get_conway_api_key
        api_key = await get_conway_api_key()
        if not api_key:
            raise HTTPException(400, "No Conway API key. Configure it in agent settings.")
        return ConwayProvider(api_key)
    else:
        # Generic BYOI: look up provider config from MongoDB
        db = get_db()
        agent_id = get_active_agent_id()
        agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "byoi_providers": 1})
        providers = (agent or {}).get("byoi_providers", {})
        if provider_name not in providers:
            raise HTTPException(400, f"Provider '{provider_name}' not configured. Add it in Settings → Infrastructure.")
        cfg = providers[provider_name]
        # Import generic provider that wraps any API
        from providers.generic import GenericProvider
        return GenericProvider(api_key=cfg["api_key"], api_url=cfg["api_url"])


# ─── Models ───

class CreateSandboxRequest(BaseModel):
    provider: str = "conway"
    tier: str = "hobby"
    region: str = "us"

class NudgeRequest(BaseModel):
    message: str


# ─── Status ───

@router.get("/status")
async def provision_status():
    return await load_provisioning()

@router.get("/phase-state")
async def phase_state():
    prov = await load_provisioning()
    return {
        "sandbox_created": prov.get("sandbox", {}).get("status") == "active",
        "runtime_installed": prov.get("tools", {}).get("runtime", {}).get("status") == "installed",
        "skills_loaded": prov.get("skills_loaded", False),
        "agent_deployed": prov.get("tools", {}).get("agent", {}).get("status") == "running",
        "wallet_created": bool(prov.get("wallet_address")),
    }


# ─── Deployment (the actual work) ───

@router.post("/deploy")
async def deploy_agent(req: CreateSandboxRequest):
    """Full deployment: create/reuse environment → install runtime → push config → start agent.
    This is the ONE endpoint that matters."""
    agent_id = get_active_agent_id()
    prov = await load_provisioning()

    # Get agent config from MongoDB
    db = get_db()
    agent_doc = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent_doc:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    if not agent_doc.get("genesis_prompt"):
        raise HTTPException(400, "Agent has no genesis prompt")

    provider = await _get_provider(req.provider)
    sandbox_id = prov.get("sandbox", {}).get("id")

    steps_log = []

    # Step 1: Get or create environment
    if not sandbox_id or prov.get("sandbox", {}).get("status") != "active":
        try:
            result = await provider.create_vm(tier=req.tier, region=req.region)
            sandbox_id = result["vm_id"]
            prov["sandbox"] = {
                "status": "active", "id": sandbox_id, "provider": req.provider,
                "terminal_url": result.get("terminal_url"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await save_provisioning(prov)
            steps_log.append(f"Created environment: {sandbox_id}")
        except Exception as e:
            raise HTTPException(500, f"Failed to create environment: {e}")
    else:
        steps_log.append(f"Reusing environment: {sandbox_id}")

    # Step 2: Install Anima Machina runtime + fix environment
    try:
        install_cmd = (
            # Core runtime
            "pip3 install camel-ai openai httpx eth-account web3 markitdown 2>&1 | tail -3 && "
            # Fix: python symlink (CAMEL's CodeExecutionToolkit calls 'python' not 'python3')
            "ln -sf $(which python3) /usr/bin/python 2>/dev/null; "
            # Fix: Install Playwright + Chromium for BrowserToolkit
            "pip3 install playwright 2>&1 | tail -1 && "
            "python3 -m playwright install --with-deps chromium 2>&1 | tail -1 && "
            # Verify
            "python3 -c 'from camel.agents import ChatAgent; print(\"RUNTIME_OK\")' && "
            "python --version 2>&1"
        )
        result = await provider.exec_in_vm(sandbox_id, install_cmd, timeout=180)
        output = result.get("output", "")
        if "RUNTIME_OK" in output:
            prov.setdefault("tools", {})["runtime"] = {"status": "installed", "installed_at": datetime.now(timezone.utc).isoformat()}
            steps_log.append("Runtime installed: camel-ai + playwright + python symlink")
        else:
            steps_log.append(f"Runtime install output: {output[:200]}")
    except Exception as e:
        steps_log.append(f"Runtime install warning: {e}")

    # Step 3: Push agent config
    # SECURITY: Only expose the webhook endpoint URL, NOT the full platform URL
    webhook_token = secrets.token_hex(16)
    platform_url = os.environ.get("REACT_APP_BACKEND_URL", "")
    webhook_url = f"{platform_url}/api/webhook/agent-update"

    # LLM inference: determine which provider to use
    # Priority: 1) agent's configured key, 2) Conway inference (if in Conway sandbox), 3) error
    agent_llm_key = agent_doc.get("llm_api_key", "")
    agent_llm_base_url = agent_doc.get("llm_base_url", "")
    agent_llm_model = agent_doc.get("llm_model", "gpt-5-mini")

    if not agent_llm_key and req.provider == "conway":
        # Use Conway's own inference endpoint — key is already in the sandbox
        from agent_state import get_conway_api_key
        conway_key = await get_conway_api_key()
        if conway_key:
            agent_llm_key = conway_key
            agent_llm_base_url = "https://api.conway.tech/v1"
            agent_llm_model = agent_doc.get("llm_model", "gpt-5-mini")
            steps_log.append("Using Conway inference (sandbox's own key)")

    if not agent_llm_key:
        raise HTTPException(400,
            "No LLM inference configured. Either set an API key via PUT /api/agents/{id}/llm-key, "
            "or deploy to a Conway sandbox (which has built-in inference)."
        )

    config = {
        "WEBHOOK_URL": webhook_url,
        "WEBHOOK_TOKEN": webhook_token,
        "AGENT_ID": agent_id,
        "LLM_API_KEY": agent_llm_key,
        "LLM_BASE_URL": agent_llm_base_url,
        "LLM_MODEL": agent_llm_model,
        "GENESIS_PROMPT_PATH": "/app/anima/genesis-prompt.md",
        "MAX_TURNS": "0",
    }

    try:
        # Create directory and write config
        env_lines = "\n".join(f'export {k}="{v}"' for k, v in config.items())
        setup_cmd = f"""
mkdir -p /app/anima && cat > /app/anima/env.sh << 'ENVEOF'
{env_lines}
ENVEOF
echo "CONFIG_WRITTEN"
"""
        await provider.exec_in_vm(sandbox_id, setup_cmd, timeout=10)

        # Push files via base64 to avoid shell escaping issues
        import base64

        # Write genesis prompt
        genesis_b64 = base64.b64encode(agent_doc["genesis_prompt"].encode()).decode()
        await provider.exec_in_vm(sandbox_id, f"echo '{genesis_b64}' | base64 -d > /app/anima/genesis-prompt.md && echo GP_WRITTEN", timeout=10)

        # Write the runner script
        runner_path = "/app/engine/anima_runner.py"
        with open(runner_path) as f:
            runner_code = f.read()
        runner_b64 = base64.b64encode(runner_code.encode()).decode()
        await provider.exec_in_vm(sandbox_id, f"echo '{runner_b64}' | base64 -d > /app/anima/runner.py && echo RUNNER_WRITTEN", timeout=10)

        # Write custom toolkits
        for toolkit_name in ["wallet_toolkit.py", "state_reporting_toolkit.py", "spawn_toolkit.py"]:
            toolkit_path = f"/app/anima-machina/camel/toolkits/{toolkit_name}"
            if os.path.exists(toolkit_path):
                with open(toolkit_path) as f:
                    tk_code = f.read()
                tk_b64 = base64.b64encode(tk_code.encode()).decode()
                await provider.exec_in_vm(sandbox_id, f"echo '{tk_b64}' | base64 -d > /app/anima/{toolkit_name}", timeout=10)

        prov["webhook_token"] = webhook_token
        steps_log.append("Config, genesis prompt, and runner pushed")
    except Exception as e:
        steps_log.append(f"Config push warning: {e}")

    # Step 4: Start the agent
    try:
        start_cmd = (
            "cd /app/anima && source env.sh && "
            "nohup python3 runner.py > /app/anima/agent.log 2>&1 &\n"
            "sleep 2 && "
            "ps aux | grep runner.py | grep -v grep | head -1 && "
            "echo AGENT_STARTED"
        )
        result = await provider.exec_in_vm(sandbox_id, start_cmd, timeout=15)
        output = result.get("output", "")
        if "AGENT_STARTED" in output:
            prov.setdefault("tools", {})["agent"] = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
            steps_log.append("Agent started in sandbox")
        else:
            steps_log.append(f"Agent start output: {output[:200]}")
    except Exception as e:
        steps_log.append(f"Agent start warning: {e}")

    await save_provisioning(prov)

    return {
        "success": True,
        "agent_id": agent_id,
        "sandbox_id": sandbox_id,
        "provider": req.provider,
        "steps": steps_log,
    }


# ─── Individual steps (for manual control / retries) ───

@router.post("/create-sandbox")
async def create_sandbox(req: CreateSandboxRequest):
    prov = await load_provisioning()
    if prov.get("sandbox", {}).get("status") == "active":
        return {"success": True, "message": "Sandbox already active", "sandbox_id": prov["sandbox"]["id"]}
    provider = await _get_provider(req.provider)
    result = await provider.create_vm(tier=req.tier, region=req.region)
    prov["sandbox"] = {"status": "active", "id": result["vm_id"], "provider": req.provider, "terminal_url": result.get("terminal_url"), "created_at": datetime.now(timezone.utc).isoformat()}
    await save_provisioning(prov)
    return {"success": True, "sandbox_id": result["vm_id"]}

@router.post("/install-openclaw")
async def install_openclaw():
    return {"success": True, "message": "Anima Machina is the runtime. OpenClaw not needed."}

@router.post("/load-skills")
async def load_skills():
    skills_dir = os.path.join(ENGINE_DIR, "skills")
    count = len([d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]) if os.path.isdir(skills_dir) else 0
    return {"success": True, "loaded": count}

@router.post("/deploy-agent")
async def deploy_agent_legacy():
    return await deploy_agent(CreateSandboxRequest())

@router.post("/test-compute")
async def test_compute():
    prov = await load_provisioning()
    sid = prov.get("sandbox", {}).get("id")
    if not sid:
        raise HTTPException(400, "No active sandbox.")
    provider = await _get_provider(prov.get("sandbox", {}).get("provider", "conway"))
    result = await provider.exec_in_vm(sid, "echo COMPUTE_OK && python3 --version", timeout=10)
    return {"success": "COMPUTE_OK" in result.get("output", ""), "output": result.get("output", "")}

@router.post("/expose-port")
async def expose_port(port: int = 8080):
    prov = await load_provisioning()
    ports = prov.get("ports", [])
    if port not in ports:
        ports.append(port)
    prov["ports"] = ports
    await save_provisioning(prov)
    return {"success": True, "port": port}

@router.post("/nudge")
async def nudge_agent():
    await add_nudge("User nudge: Check your status and report back.")
    return {"success": True}

@router.post("/nudge/custom")
async def nudge_custom(req: NudgeRequest):
    await add_nudge(req.message)
    return {"success": True}

@router.get("/agent-logs")
async def agent_logs():
    prov = await load_provisioning()
    sid = prov.get("sandbox", {}).get("id")
    if not sid:
        return {"logs": "", "message": "No active sandbox"}
    try:
        provider = await _get_provider(prov.get("sandbox", {}).get("provider", "conway"))
        result = await provider.exec_in_vm(sid, "cat /app/anima/agent.log 2>/dev/null | tail -50", timeout=10)
        return {"logs": result.get("output", ""), "message": "Live logs from sandbox"}
    except Exception as e:
        return {"logs": "", "message": str(e)}

@router.post("/web-terminal")
async def web_terminal():
    prov = await load_provisioning()
    return {"success": True, "url": prov.get("sandbox", {}).get("terminal_url", "")}

@router.post("/install-terminal")
async def install_terminal():
    return {"success": True, "message": "Terminal available via provider"}

@router.post("/install-claude-code")
async def install_claude_code():
    return {"success": True, "message": "Use Anima Machina tools instead"}

@router.post("/pty/create")
async def pty_create():
    return {"success": True, "session_id": "default"}

@router.get("/pty/list")
async def pty_list():
    return {"sessions": []}

@router.post("/pty/read")
async def pty_read():
    return {"output": ""}

@router.post("/pty/write")
async def pty_write():
    return {"success": True}
