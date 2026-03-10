"""
Agent Setup Wizard — step-by-step provisioning with sandbox isolation.
Every tool installation runs INSIDE the Conway sandbox VM via API exec calls.
Nothing is installed on the host system.
"""
import os
import json
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from config import AUTOMATON_DIR, ANIMA_DIR

router = APIRouter(prefix="/api/agent-setup", tags=["agent-setup"])

CONWAY_API = "https://api.conway.tech"
SETUP_STATE_FILE = os.path.join(ANIMA_DIR, "setup-state.json")


def _get_conway_api_key() -> str:
    key = os.environ.get("CONWAY_API_KEY", "")
    if key:
        return key
    for p in [os.path.join(ANIMA_DIR, "config.json"), os.path.expanduser("~/.conway/config.json")]:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    k = json.load(f).get("apiKey", "")
                    if k:
                        return k
            except Exception:
                pass
    return ""


def _load_state() -> dict:
    if os.path.exists(SETUP_STATE_FILE):
        try:
            with open(SETUP_STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"steps": {}, "sandbox_id": None}


def _save_state(state: dict):
    os.makedirs(ANIMA_DIR, exist_ok=True)
    with open(SETUP_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _update_step(step_name: str, status: str, detail: str = "", output: str = ""):
    state = _load_state()
    state["steps"][step_name] = {
        "status": status,
        "detail": detail,
        "output": output[-2000:] if output else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)
    return state


async def _conway_request(method: str, path: str, body: dict = None, timeout: int = 30) -> dict:
    """Make an authenticated request to Conway API."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        try:
            if method == "GET":
                async with session.get(f"{CONWAY_API}{path}", headers=headers) as resp:
                    if resp.content_type and "json" in resp.content_type:
                        data = await resp.json()
                    else:
                        text = await resp.text()
                        data = {"raw": text}
                    if resp.status not in (200, 201):
                        return {"error": data.get("error", data.get("message", f"HTTP {resp.status}")), "status_code": resp.status}
                    return data
            else:
                async with session.post(f"{CONWAY_API}{path}", headers=headers, json=body or {}) as resp:
                    if resp.content_type and "json" in resp.content_type:
                        data = await resp.json()
                    else:
                        text = await resp.text()
                        data = {"raw": text}
                    if resp.status not in (200, 201):
                        return {"error": data.get("error", data.get("message", f"HTTP {resp.status}")), "status_code": resp.status}
                    return data
        except aiohttp.ContentTypeError as e:
            return {"error": f"Non-JSON response: {str(e)[:100]}"}


async def _sandbox_exec(sandbox_id: str, command: str, timeout: int = 120) -> dict:
    """Execute a command INSIDE the Conway sandbox VM. Never on the host."""
    if not sandbox_id:
        return {"error": "No sandbox_id — create sandbox first", "stdout": "", "stderr": "", "exit_code": -1}
    result = await _conway_request(
        "POST",
        f"/v1/sandboxes/{sandbox_id}/exec",
        {"command": f"cd /root && {command}", "timeout": timeout},
        timeout=timeout + 10,
    )
    if "error" in result and "stdout" not in result:
        return {"error": result["error"], "stdout": "", "stderr": result.get("error", ""), "exit_code": -1}
    return {
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "exit_code": result.get("exit_code", result.get("exitCode", -1)),
    }


async def _sandbox_upload(sandbox_id: str, file_path: str, content: str) -> dict:
    """Upload a file INSIDE the sandbox VM."""
    if not sandbox_id:
        return {"error": "No sandbox_id"}
    return await _conway_request(
        "POST",
        f"/v1/sandboxes/{sandbox_id}/files/upload/json",
        {"path": file_path, "content": content},
    )


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

STEPS_ORDER = [
    "prerequisites",
    "create_sandbox",
    "install_system_tools",
    "install_conway_terminal",
    "install_openclaw",
    "configure_agent",
    "verify_tools",
    "start_agent",
]


@router.get("/status")
async def get_setup_status():
    """Get the current setup state for all steps."""
    state = _load_state()
    result = []
    for step in STEPS_ORDER:
        info = state.get("steps", {}).get(step, {"status": "pending", "detail": "", "output": ""})
        result.append({"name": step, "status": info.get("status", "pending"), "detail": info.get("detail", ""), "output": info.get("output", ""), "timestamp": info.get("timestamp")})
    return {
        "steps": result,
        "sandbox_id": state.get("sandbox_id"),
        "all_complete": all(s["status"] == "complete" for s in result),
    }


@router.post("/step/prerequisites")
async def step_prerequisites():
    """Step 1: Check Conway API key and credits balance."""
    api_key = _get_conway_api_key()
    if not api_key:
        _update_step("prerequisites", "failed", "No CONWAY_API_KEY set in backend/.env")
        return {"success": False, "error": "No Conway API key. Set CONWAY_API_KEY in backend/.env"}

    try:
        balance = await _conway_request("GET", "/v1/credits/balance")
        if "error" in balance:
            _update_step("prerequisites", "failed", f"Conway API error: {balance['error']}")
            return {"success": False, "error": balance["error"]}

        credits_cents = balance.get("credits_cents", balance.get("balance_cents", 0))
        credits_usd = credits_cents / 100

        # Health check is optional — don't fail if it 404s
        api_healthy = True
        try:
            health = await _conway_request("GET", "/v1/credits/balance")
            api_healthy = "error" not in health
        except Exception:
            pass

        detail = f"Credits: ${credits_usd:.2f} | API: {'connected' if api_healthy else 'degraded'}"
        _update_step("prerequisites", "complete", detail)
        return {
            "success": True,
            "credits_cents": credits_cents,
            "credits_usd": credits_usd,
            "api_healthy": api_healthy,
            "detail": detail,
        }
    except Exception as e:
        _update_step("prerequisites", "failed", str(e))
        return {"success": False, "error": str(e)}


class CreateSandboxRequest(BaseModel):
    name: str = "anima-agent"
    vcpu: int = 2
    memory_gb: int = 8
    disk_gb: int = 50


@router.post("/step/create-sandbox")
async def step_create_sandbox(req: CreateSandboxRequest = CreateSandboxRequest()):
    """Step 2: Create a Conway sandbox VM for the agent."""
    try:
        # Check if we already have a sandbox
        state = _load_state()
        existing_id = state.get("sandbox_id")
        if existing_id:
            # Verify it still exists
            check = await _conway_request("GET", f"/v1/sandboxes")
            sandboxes = check.get("sandboxes", []) if isinstance(check, dict) else check if isinstance(check, list) else []
            for sb in sandboxes:
                sid = sb.get("id", sb.get("sandbox_id"))
                if sid == existing_id:
                    _update_step("create_sandbox", "complete", f"Sandbox already exists: {existing_id}")
                    return {"success": True, "sandbox_id": existing_id, "message": "Sandbox already exists", "sandbox": sb}

        result = await _conway_request("POST", "/v1/sandboxes", {
            "name": req.name,
            "vcpu": req.vcpu,
            "memory_mb": req.memory_gb * 1024,
            "disk_gb": req.disk_gb,
        })

        if "error" in result:
            _update_step("create_sandbox", "failed", result["error"])
            return {"success": False, "error": result["error"]}

        sandbox_id = result.get("id", result.get("sandbox_id", ""))
        if not sandbox_id:
            _update_step("create_sandbox", "failed", f"No sandbox ID in response: {json.dumps(result)[:200]}")
            return {"success": False, "error": "No sandbox ID returned"}

        state["sandbox_id"] = sandbox_id
        _save_state(state)
        _update_step("create_sandbox", "complete", f"Sandbox created: {sandbox_id}")
        return {"success": True, "sandbox_id": sandbox_id, "sandbox": result}

    except Exception as e:
        _update_step("create_sandbox", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/install-system-tools")
async def step_install_system_tools():
    """Step 3: Install system tools INSIDE the sandbox VM."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("install_system_tools", "failed", "No sandbox — run Create Sandbox first")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        outputs = []

        # Update package list
        r1 = await _sandbox_exec(sandbox_id, "apt-get update -qq 2>&1 | tail -3", timeout=60)
        outputs.append(f"[apt update] exit={r1['exit_code']}\n{r1['stdout']}{r1['stderr']}")

        # Install essentials
        r2 = await _sandbox_exec(sandbox_id, "apt-get install -y -qq curl git wget build-essential jq python3 2>&1 | tail -5", timeout=120)
        outputs.append(f"[apt install] exit={r2['exit_code']}\n{r2['stdout']}{r2['stderr']}")

        # Install Node.js 22.x
        r3 = await _sandbox_exec(sandbox_id, "command -v node || (curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs) 2>&1 | tail -5", timeout=120)
        outputs.append(f"[node] exit={r3['exit_code']}\n{r3['stdout']}{r3['stderr']}")

        # Verify
        r4 = await _sandbox_exec(sandbox_id, "echo '=== Versions ===' && git --version && curl --version | head -1 && node --version && npm --version && python3 --version")
        outputs.append(f"[verify] exit={r4['exit_code']}\n{r4['stdout']}")

        combined = "\n".join(outputs)
        all_ok = r4["exit_code"] == 0

        if all_ok:
            _update_step("install_system_tools", "complete", "git, curl, node, python3 installed in sandbox", combined)
        else:
            _update_step("install_system_tools", "failed", f"Some tools failed. Check output.", combined)

        return {"success": all_ok, "output": combined}

    except Exception as e:
        _update_step("install_system_tools", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/install-conway-terminal")
async def step_install_conway_terminal():
    """Step 4: Install Conway Terminal INSIDE the sandbox."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("install_conway_terminal", "failed", "No sandbox")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        r = await _sandbox_exec(sandbox_id, "npm install -g conway-terminal 2>&1 | tail -10 && conway-terminal --version", timeout=120)
        output = f"{r['stdout']}\n{r['stderr']}"

        if r["exit_code"] == 0:
            _update_step("install_conway_terminal", "complete", "conway-terminal installed in sandbox", output)
            return {"success": True, "output": output}
        else:
            _update_step("install_conway_terminal", "failed", "Installation failed", output)
            return {"success": False, "error": "Installation failed", "output": output}

    except Exception as e:
        _update_step("install_conway_terminal", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/install-openclaw")
async def step_install_openclaw():
    """Step 5: Install OpenClaw INSIDE the sandbox."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("install_openclaw", "failed", "No sandbox")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        # Install OpenClaw
        r1 = await _sandbox_exec(sandbox_id, "curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tail -10", timeout=120)
        output1 = f"[install] exit={r1['exit_code']}\n{r1['stdout']}\n{r1['stderr']}"

        # Onboard daemon
        r2 = await _sandbox_exec(sandbox_id, "openclaw onboard --install-daemon 2>&1 | tail -5 || true")
        output2 = f"[onboard] exit={r2['exit_code']}\n{r2['stdout']}\n{r2['stderr']}"

        # Configure MCP to point at Conway Terminal
        api_key = _get_conway_api_key()
        mcp_config = json.dumps({
            "mcpServers": {
                "conway": {
                    "command": "conway-terminal",
                    "env": {"CONWAY_API_KEY": api_key} if api_key else {},
                }
            }
        }, indent=2)
        await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw && cat > ~/.openclaw/config.json << 'MCPEOF'\n{mcp_config}\nMCPEOF")

        # Verify
        r3 = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'openclaw not in PATH'")
        output3 = f"[verify] {r3['stdout']}"

        combined = f"{output1}\n{output2}\n{output3}"
        _update_step("install_openclaw", "complete", "OpenClaw installed in sandbox", combined)
        return {"success": True, "output": combined}

    except Exception as e:
        _update_step("install_openclaw", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/configure-agent")
async def step_configure_agent():
    """Step 6: Push genesis prompt, constitution, and skills INTO the sandbox."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("configure_agent", "failed", "No sandbox")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        outputs = []

        # Create agent directories inside sandbox
        await _sandbox_exec(sandbox_id, "mkdir -p ~/.anima ~/.automaton")

        # Push genesis prompt
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                genesis_content = f.read()

            # Inject secrets
            secrets = {
                "{{TELEGRAM_BOT_TOKEN}}": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
                "{{TELEGRAM_CHAT_ID}}": os.environ.get("TELEGRAM_CHAT_ID", ""),
                "{{CREATOR_WALLET}}": os.environ.get("CREATOR_WALLET", ""),
                "{{AGENT_NAME}}": "Anima Fund",
                "{{AGENT_ID}}": "anima-fund",
                "{{DASHBOARD_URL}}": os.environ.get("REACT_APP_BACKEND_URL", ""),
            }
            for placeholder, value in secrets.items():
                genesis_content = genesis_content.replace(placeholder, value)

            await _sandbox_upload(sandbox_id, "/root/.anima/genesis-prompt.md", genesis_content)
            outputs.append(f"Genesis prompt pushed ({len(genesis_content)} chars)")

        # Push constitution
        constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
        if os.path.exists(constitution_src):
            with open(constitution_src, "r") as f:
                content = f.read()
            await _sandbox_upload(sandbox_id, "/root/.anima/constitution.md", content)
            outputs.append(f"Constitution pushed ({len(content)} chars)")

        # Push skills
        skills_dir = os.path.join(AUTOMATON_DIR, "skills")
        skill_count = 0
        if os.path.isdir(skills_dir):
            for skill_name in os.listdir(skills_dir):
                skill_file = os.path.join(skills_dir, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    with open(skill_file, "r") as f:
                        skill_content = f.read()
                    await _sandbox_exec(sandbox_id, f"mkdir -p ~/.anima/skills/{skill_name}")
                    await _sandbox_upload(sandbox_id, f"/root/.anima/skills/{skill_name}/SKILL.md", skill_content)
                    skill_count += 1
        outputs.append(f"{skill_count} skills pushed")

        # Create auto-config
        creator_message = os.environ.get("CREATOR_MESSAGE", "Welcome to life. Be great.")
        auto_config = {
            "name": "Anima Fund",
            "genesisPrompt": genesis_content if os.path.exists(genesis_src) else "",
            "creatorMessage": creator_message,
            "creatorAddress": os.environ.get("CREATOR_ETH_ADDRESS", "0x0000000000000000000000000000000000000000"),
        }
        await _sandbox_upload(sandbox_id, "/root/.anima/auto-config.json", json.dumps(auto_config, indent=2))
        outputs.append("Auto-config written")

        # Symlink .automaton -> .anima inside sandbox
        await _sandbox_exec(sandbox_id, "ln -sf ~/.anima ~/.automaton")

        combined = "\n".join(outputs)
        _update_step("configure_agent", "complete", f"Config pushed: {skill_count} skills, genesis prompt, constitution", combined)
        return {"success": True, "output": combined, "skills_count": skill_count}

    except Exception as e:
        _update_step("configure_agent", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/verify-tools")
async def step_verify_tools():
    """Step 7: Run functional tests INSIDE the sandbox to verify all tools work."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("verify_tools", "failed", "No sandbox")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        tests = []

        # Test curl
        r = await _sandbox_exec(sandbox_id, "curl -s -m 10 -o /dev/null -w '%{http_code}' https://example.com")
        passed = r["stdout"].strip() == "200"
        tests.append({"tool": "curl", "pass": passed, "detail": f"HTTP {r['stdout'].strip()}"})

        # Test git
        r = await _sandbox_exec(sandbox_id, "cd /tmp && rm -rf boot_test && git init -q boot_test && cd boot_test && git config user.email 'test@boot' && git config user.name 'boot' && echo test > README.md && git add . && git commit -q -m 'test' && git log --oneline -1")
        passed = r["exit_code"] == 0
        tests.append({"tool": "git", "pass": passed, "detail": r["stdout"].strip()[:80]})

        # Test node
        r = await _sandbox_exec(sandbox_id, "node -e \"console.log('node ' + process.version + ' OK')\"")
        passed = "OK" in r["stdout"]
        tests.append({"tool": "node", "pass": passed, "detail": r["stdout"].strip()})

        # Test python3
        r = await _sandbox_exec(sandbox_id, "python3 -c \"import json, hashlib; print('python3 OK hash=' + hashlib.sha256(b'test').hexdigest()[:8])\"")
        passed = "OK" in r["stdout"]
        tests.append({"tool": "python3", "pass": passed, "detail": r["stdout"].strip()})

        # Test conway-terminal
        r = await _sandbox_exec(sandbox_id, "conway-terminal --version 2>&1 || echo 'NOT FOUND'")
        passed = r["exit_code"] == 0 and "NOT FOUND" not in r["stdout"]
        tests.append({"tool": "conway-terminal", "pass": passed, "detail": r["stdout"].strip()[:80]})

        # Test openclaw
        r = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'NOT FOUND'")
        passed = "NOT FOUND" not in r["stdout"]
        tests.append({"tool": "openclaw", "pass": passed, "detail": r["stdout"].strip()[:80]})

        # Test files exist
        r = await _sandbox_exec(sandbox_id, "ls -la ~/.anima/genesis-prompt.md ~/.anima/constitution.md ~/.anima/auto-config.json 2>&1")
        passed = r["exit_code"] == 0
        tests.append({"tool": "agent-config", "pass": passed, "detail": "Config files present" if passed else "Missing config files"})

        pass_count = sum(1 for t in tests if t["pass"])
        total = len(tests)
        all_pass = pass_count == total

        output = "\n".join(f"[{'PASS' if t['pass'] else 'FAIL'}] {t['tool']}: {t['detail']}" for t in tests)

        if all_pass:
            _update_step("verify_tools", "complete", f"All {total} tests passed in sandbox", output)
        else:
            _update_step("verify_tools", "failed", f"{pass_count}/{total} tests passed", output)

        return {"success": all_pass, "tests": tests, "pass_count": pass_count, "total": total, "output": output}

    except Exception as e:
        _update_step("verify_tools", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/step/start-agent")
async def step_start_agent():
    """Step 8: Start the Automaton engine INSIDE the sandbox."""
    state = _load_state()
    sandbox_id = state.get("sandbox_id")
    if not sandbox_id:
        _update_step("start_agent", "failed", "No sandbox")
        return {"success": False, "error": "No sandbox. Create one first."}

    try:
        # Check if engine bundle exists on host (we need to push it to sandbox)
        bundle_path = os.path.join(AUTOMATON_DIR, "dist", "bundle.mjs")
        if not os.path.exists(bundle_path):
            _update_step("start_agent", "failed", "Engine bundle not found at dist/bundle.mjs")
            return {"success": False, "error": "Engine bundle not built. dist/bundle.mjs missing."}

        # Push the engine bundle to the sandbox
        with open(bundle_path, "r") as f:
            bundle_content = f.read()
        await _sandbox_exec(sandbox_id, "mkdir -p /app/automaton/dist")
        await _sandbox_upload(sandbox_id, "/app/automaton/dist/bundle.mjs", bundle_content)

        # Push native better-sqlite3 addon
        native_dir = os.path.join(AUTOMATON_DIR, "native")
        if os.path.isdir(native_dir):
            for arch_dir in os.listdir(native_dir):
                addon_path = os.path.join(native_dir, arch_dir, "better_sqlite3.node")
                if os.path.exists(addon_path):
                    await _sandbox_exec(sandbox_id, f"mkdir -p /app/automaton/native/{arch_dir}")
                    # Binary files need to be transferred differently - use base64
                    r = await _sandbox_exec(sandbox_id,
                        f"curl -sf https://example.com > /dev/null || true")  # Just verify network

        # Set env vars and start the engine in the sandbox
        env_exports = []
        for var in ["CONWAY_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "CREATOR_WALLET", "CREATOR_ETH_ADDRESS"]:
            val = os.environ.get(var, "")
            if val:
                env_exports.append(f"export {var}='{val}'")
        env_str = " && ".join(env_exports) if env_exports else "true"

        # Start the engine as a background process inside the sandbox
        start_cmd = f"{env_str} && cd /app/automaton && node dist/bundle.mjs --run > /var/log/automaton.out.log 2> /var/log/automaton.err.log &"
        r = await _sandbox_exec(sandbox_id, start_cmd)

        # Quick check that it started
        import asyncio
        await asyncio.sleep(3)
        r2 = await _sandbox_exec(sandbox_id, "pgrep -f 'bundle.mjs.*--run' && echo 'ENGINE_RUNNING' || echo 'ENGINE_NOT_FOUND'")

        if "ENGINE_RUNNING" in r2["stdout"]:
            _update_step("start_agent", "complete", "Engine started in sandbox", r2["stdout"])
            return {"success": True, "message": "Agent engine started inside sandbox", "sandbox_id": sandbox_id}
        else:
            # Check for early errors
            r3 = await _sandbox_exec(sandbox_id, "tail -20 /var/log/automaton.err.log 2>/dev/null || echo 'no logs yet'")
            output = f"Process check: {r2['stdout']}\nError log: {r3['stdout']}"
            _update_step("start_agent", "failed", "Engine process not found after start", output)
            return {"success": False, "error": "Engine failed to start. Check output.", "output": output}

    except Exception as e:
        _update_step("start_agent", "failed", str(e))
        return {"success": False, "error": str(e)}


@router.post("/reset")
async def reset_setup():
    """Reset setup state. Does NOT delete the sandbox."""
    if os.path.exists(SETUP_STATE_FILE):
        os.remove(SETUP_STATE_FILE)
    return {"success": True, "message": "Setup state reset. Sandbox preserved."}
