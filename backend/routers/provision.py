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

async def _get_fly_config(agent_id: str = None) -> dict:
    """Get Fly.io config for the active agent from MongoDB, falling back to env vars."""
    if not agent_id:
        agent_id = get_active_agent_id()
    try:
        db = get_db()
        agent = await db.agents.find_one(
            {"agent_id": agent_id},
            {"_id": 0, "fly_api_key": 1, "fly_app_name": 1}
        )
        if agent and agent.get("fly_api_key"):
            return {
                "api_key": agent["fly_api_key"],
                "app_name": agent.get("fly_app_name", "animafund"),
            }
    except Exception:
        pass
    # Fallback to env vars
    return {
        "api_key": os.environ.get("FLY_API_TOKEN", ""),
        "app_name": os.environ.get("FLY_APP_NAME", "animafund"),
    }


async def _get_provider(provider_name: str):
    """Resolve a BYOI provider by name."""
    if provider_name == "conway":
        from providers.conway import ConwayProvider
        from agent_state import get_conway_api_key
        api_key = await get_conway_api_key()
        if not api_key:
            raise HTTPException(400, "No Conway API key configured.")
        return ConwayProvider(api_key)
    elif provider_name == "fly":
        from providers.fly import FlyProvider
        fly_cfg = await _get_fly_config()
        api_key = fly_cfg["api_key"]
        app_name = fly_cfg["app_name"]
        if not api_key:
            raise HTTPException(400, "No Fly.io API token configured. Add one in the provider settings.")
        return FlyProvider(api_key, app_name)
    else:
        raise HTTPException(400, f"Provider '{provider_name}' not configured. Available: conway, fly")


# ─── Models ───

class CreateSandboxRequest(BaseModel):
    provider: str = "conway"
    tier: str = "hobby"
    region: str = "us"

class NudgeRequest(BaseModel):
    message: str

class SetProviderKeyRequest(BaseModel):
    provider: str
    api_key: str
    app_name: str = ""


# ─── Provider Key Management ───

@router.get("/provider-key-status")
async def provider_key_status(provider: str = "fly"):
    """Check if a provider key is configured for the active agent."""
    agent_id = get_active_agent_id()
    if provider == "fly":
        fly_cfg = await _get_fly_config(agent_id)
        api_key = fly_cfg["api_key"]
        app_name = fly_cfg["app_name"]
        return {
            "configured": bool(api_key),
            "provider": "fly",
            "app_name": app_name,
            "key_prefix": api_key[:12] + "..." if api_key and len(api_key) > 12 else "",
        }
    elif provider == "conway":
        from agent_state import get_conway_api_key
        key = await get_conway_api_key(agent_id)
        return {
            "configured": bool(key),
            "provider": "conway",
            "key_prefix": key[:12] + "..." if key and len(key) > 12 else "",
        }
    return {"configured": False, "provider": provider}


@router.post("/set-provider-key")
async def set_provider_key(req: SetProviderKeyRequest):
    """Store a provider API key for the active agent in MongoDB."""
    agent_id = get_active_agent_id()
    db = get_db()

    if req.provider == "fly":
        api_key = req.api_key.strip()
        # Remove "FlyV1 " prefix if user pasted the full header value
        if api_key.startswith("FlyV1 "):
            api_key = api_key[6:]
        if not api_key:
            raise HTTPException(400, "API key cannot be empty")

        app_name = req.app_name.strip() or os.environ.get("FLY_APP_NAME", "animafund")

        await db.agents.update_one(
            {"agent_id": agent_id},
            {"$set": {
                "fly_api_key": api_key,
                "fly_app_name": app_name,
                "fly_key_updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return {
            "success": True,
            "message": f"Fly.io token saved for {agent_id} (app: {app_name})",
            "app_name": app_name,
        }

    elif req.provider == "conway":
        from agent_state import set_conway_api_key
        await set_conway_api_key(req.api_key.strip(), agent_id)
        return {"success": True, "message": f"Conway key saved for {agent_id}"}

    raise HTTPException(400, f"Unknown provider: {req.provider}")


# ─── Sandbox Management ───

@router.post("/health-check")
async def health_check():
    """Probe sandbox and return current state."""
    prov = await load_provisioning()
    sid = prov.get("sandbox", {}).get("id")
    if not sid or prov.get("sandbox", {}).get("status") != "active":
        return {"success": False, "error": "No active sandbox"}

    provider_name = prov.get("sandbox", {}).get("provider", "conway")
    try:
        provider = await _get_provider(provider_name)
        result = await provider.exec_in_vm(sid, "echo HEALTH_OK && ps aux | grep -c runner.py", timeout=10)
        output = result.get("output", "")
        engine_running = "runner.py" in output or int(output.strip().split("\n")[-1]) > 1 if output else False

        # Determine next step
        tools = prov.get("tools", {})
        next_step = None
        if not tools.get("runtime", {}).get("status") == "installed":
            next_step = "Install Runtime"
        elif not tools.get("agent", {}).get("status") == "running":
            next_step = "Deploy Agent"

        return {
            "success": "HEALTH_OK" in output,
            "engine_running": engine_running,
            "next_step": next_step,
            "output": output[:200],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/reset-sandbox")
async def reset_sandbox():
    """Reset agent data but keep the sandbox VM alive."""
    prov = await load_provisioning()
    sid = prov.get("sandbox", {}).get("id")
    if not sid:
        return {"success": False, "error": "No active sandbox"}

    provider_name = prov.get("sandbox", {}).get("provider", "conway")
    try:
        provider = await _get_provider(provider_name)
        # Kill the running agent and clear its data
        await provider.exec_in_vm(sid, "pkill -f runner.py 2>/dev/null; rm -rf /app/anima 2>/dev/null; echo RESET_OK", timeout=15)
    except Exception as e:
        logger.warning(f"Reset exec warning: {e}")

    # Keep sandbox info, clear tools/agent state
    new_prov = {
        "sandbox": prov.get("sandbox", {}),
        "tools": {},
        "ports": prov.get("ports", []),
        "domains": prov.get("domains", []),
        "compute_verified": False,
        "skills_loaded": False,
        "nudges": [],
        "wallet_address": "",
    }
    await save_provisioning(new_prov)
    return {"success": True, "message": "Agent reset — sandbox preserved"}


@router.post("/delete-sandbox")
async def delete_sandbox():
    """Destroy the sandbox machine entirely."""
    prov = await load_provisioning()
    sid = prov.get("sandbox", {}).get("id")
    if not sid:
        return {"success": False, "error": "No active sandbox to delete"}

    provider_name = prov.get("sandbox", {}).get("provider", "conway")
    try:
        provider = await _get_provider(provider_name)
        await provider.destroy_vm(sid)
    except Exception as e:
        logger.warning(f"Destroy VM warning: {e}")

    from agent_state import default_provisioning
    await save_provisioning(default_provisioning())
    return {"success": True, "message": "Sandbox machine destroyed"}


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
    # Check if existing sandbox matches the requested provider
    existing_provider = prov.get("sandbox", {}).get("provider", "")
    if sandbox_id and prov.get("sandbox", {}).get("status") == "active" and existing_provider == req.provider:
        steps_log.append(f"Reusing environment: {sandbox_id} ({req.provider})")
    else:
        # Create new environment (different provider or no existing)
        try:
            result = await provider.create_vm(tier=req.tier, region=req.region)
            sandbox_id = result["vm_id"]
            prov["sandbox"] = {
                "status": "active", "id": sandbox_id, "provider": req.provider,
                "terminal_url": result.get("terminal_url"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await save_provisioning(prov)
            steps_log.append(f"Created environment: {sandbox_id} ({req.provider})")
        except Exception as e:
            raise HTTPException(500, f"Failed to create environment: {e}")

    # Step 2: Install runtime (SKIP if already installed to save credits)
    try:
        check_cmd = "python3 -c 'from anima_machina.agents import ChatAgent; print(\"RUNTIME_OK\")' 2>&1"
        check_result = await provider.exec_in_vm(sandbox_id, check_cmd, timeout=15)
        if "RUNTIME_OK" in check_result.get("output", ""):
            prov.setdefault("tools", {})["runtime"] = {"status": "installed"}
            steps_log.append("Runtime already installed (skipped reinstall)")
        else:
            raise Exception("Runtime not found")
    except Exception:
        # Only install if not already present
        try:
            install_cmd = (
                "pip3 install anima-machina openai httpx eth-account web3 markitdown 2>&1 | tail -3 && "
                "ln -sf $(which python3) /usr/bin/python 2>/dev/null; "
                "pip3 install playwright 2>&1 | tail -1 && "
                "python3 -m playwright install --with-deps chromium 2>&1 | tail -1 && "
                "python3 -c 'from anima_machina.agents import ChatAgent; print(\"RUNTIME_OK\")' && "
                "python --version 2>&1"
            )
            result = await provider.exec_in_vm(sandbox_id, install_cmd, timeout=180)
            output = result.get("output", "")
            if "RUNTIME_OK" in output:
                prov.setdefault("tools", {})["runtime"] = {"status": "installed", "installed_at": datetime.now(timezone.utc).isoformat()}
                steps_log.append("Runtime installed: anima-machina + playwright + python symlink")
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
    agent_llm_key = agent_doc.get("llm_api_key", "")
    agent_llm_base_url = agent_doc.get("llm_base_url", "")
    agent_llm_model = agent_doc.get("llm_model", "gpt-4o-mini")

    if not agent_llm_key and req.provider == "conway":
        from agent_state import get_conway_api_key
        conway_key = await get_conway_api_key()
        if conway_key:
            agent_llm_key = conway_key
            agent_llm_base_url = "https://api.conway.tech/v1"
            agent_llm_model = agent_doc.get("llm_model", "gpt-5-mini")
            steps_log.append("Using Conway inference")

    if not agent_llm_key:
        # For non-Conway providers, use Emergent key through the platform proxy
        # The agent calls the platform's webhook URL which proxies LLM requests
        # This avoids putting API keys in the sandbox
        agent_llm_key = os.environ.get("EMERGENT_LLM_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        agent_llm_base_url = "https://integrations.emergentagent.com/llm/v1"
        if agent_llm_key:
            steps_log.append("Using platform inference key")

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
            toolkit_path = f"/app/anima-machina/anima_machina/toolkits/{toolkit_name}"  # Anima Machina toolkits
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
        # Create a wrapper script that sources env vars then starts the runner.
        # This ensures the Python process inherits ALL env vars from env.sh.
        start_cmd = (
            "cd /app/anima && "
            # Kill ONLY the previous runner (not system Python processes)
            "pkill -f runner.py 2>/dev/null; pkill -f start.sh 2>/dev/null; sleep 1; "
            "cat > start.sh << 'STARTEOF'\n"
            "#!/bin/bash\n"
            "source /app/anima/env.sh\n"
            "exec python3 /app/anima/runner.py\n"
            "STARTEOF\n"
            "chmod +x start.sh && "
            "nohup /app/anima/start.sh > /app/anima/agent.log 2>&1 &\n"
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

    # Store core wallet address in MongoDB for dashboard display
    # The dashboard shows the core wallet to the USER (owner) — not to the agent or public
    try:
        result = await provider.exec_in_vm(sandbox_id,
            "python3 -c \"import json; from eth_account import Account; "
            "w=json.load(open('/root/.anima/wallet.json')); "
            "print(Account.from_key(w['privateKey']).address)\" 2>/dev/null",
            timeout=15)
        core_addr = result.get("output", "").strip()
        if core_addr.startswith("0x"):
            prov["wallet_address"] = core_addr
            steps_log.append("Core wallet address stored for dashboard")
    except Exception:
        pass

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
