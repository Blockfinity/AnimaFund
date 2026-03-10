"""
Agent Provisioning — live-equip a running agent with sandbox, tools, and skills.

The agent is ALREADY ALIVE when these endpoints are called.
Each action modifies the agent's environment and writes a provisioning
status file so the agent is aware of what was just built for it.
"""
import os
import json
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from config import AUTOMATON_DIR, ANIMA_DIR

router = APIRouter(prefix="/api/provision", tags=["provision"])

CONWAY_API = "https://api.conway.tech"
PROV_STATUS_FILE = os.path.join(ANIMA_DIR, "provisioning-status.json")


def _get_conway_api_key() -> str:
    key = os.environ.get("CONWAY_API_KEY", "")
    if not key:
        config_path = os.path.join(ANIMA_DIR, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    key = json.load(f).get("apiKey", "")
            except Exception:
                pass
    return key


# ═══════════════════════════════════════════════════════════
# PROVISIONING STATUS — the agent reads this every turn
# ═══════════════════════════════════════════════════════════

def _load_prov_status() -> dict:
    if os.path.exists(PROV_STATUS_FILE):
        try:
            with open(PROV_STATUS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "sandbox": {"status": "none", "id": None},
        "tools": {},
        "skills_loaded": False,
        "nudges": [],
        "last_updated": None,
    }


def _save_prov_status(status: dict):
    os.makedirs(ANIMA_DIR, exist_ok=True)
    status["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(PROV_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def _add_nudge(message: str):
    """Add a nudge message the agent will see on its next turn."""
    status = _load_prov_status()
    status["nudges"].append({
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Keep only last 5 nudges
    status["nudges"] = status["nudges"][-5:]
    _save_prov_status(status)


async def _conway_request(method: str, path: str, body: dict = None, timeout: int = 30) -> dict:
    """Make an authenticated request to Conway API."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        try:
            url = f"{CONWAY_API}{path}"
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    data = await resp.json() if "json" in (resp.content_type or "") else {"raw": await resp.text()}
                    if resp.status not in (200, 201):
                        return {"error": data.get("error", data.get("message", f"HTTP {resp.status}"))}
                    return data
            else:
                async with session.post(url, headers=headers, json=body or {}) as resp:
                    data = await resp.json() if "json" in (resp.content_type or "") else {"raw": await resp.text()}
                    if resp.status not in (200, 201):
                        return {"error": data.get("error", data.get("message", f"HTTP {resp.status}"))}
                    return data
        except aiohttp.ContentTypeError as e:
            return {"error": f"Non-JSON response: {str(e)[:100]}"}
        except Exception as e:
            return {"error": str(e)}


async def _sandbox_exec(sandbox_id: str, command: str, timeout: int = 120) -> dict:
    """Execute a command INSIDE the Conway sandbox VM."""
    if not sandbox_id:
        return {"error": "No sandbox — create one first", "stdout": "", "stderr": "", "exit_code": -1}
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


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/status")
async def get_provision_status():
    """What does the agent currently have?"""
    status = _load_prov_status()

    # Also check Conway credits
    credits_cents = 0
    try:
        balance = await _conway_request("GET", "/v1/credits/balance")
        credits_cents = balance.get("credits_cents", 0)
    except Exception:
        pass

    return {
        "sandbox": status["sandbox"],
        "tools": status["tools"],
        "skills_loaded": status["skills_loaded"],
        "nudges": status["nudges"],
        "credits_cents": credits_cents,
        "last_updated": status["last_updated"],
    }


@router.post("/create-sandbox")
async def create_sandbox():
    """Create a Conway Cloud sandbox VM for the agent. The agent is already alive."""
    status = _load_prov_status()

    # Already have a sandbox?
    if status["sandbox"]["status"] == "active" and status["sandbox"]["id"]:
        return {"success": True, "sandbox_id": status["sandbox"]["id"], "message": "Sandbox already exists"}

    result = await _conway_request("POST", "/v1/sandboxes", {
        "name": "anima-agent",
        "vcpu": 2,
        "memory_mb": 4096,
        "disk_gb": 40,
    })

    if "error" in result:
        return {"success": False, "error": result["error"]}

    sandbox_id = result.get("id", result.get("sandbox_id", ""))
    if not sandbox_id:
        return {"success": False, "error": f"No sandbox ID in response: {json.dumps(result)[:200]}"}

    status["sandbox"] = {"status": "active", "id": sandbox_id}
    _save_prov_status(status)
    _add_nudge(f"Your creator just provisioned a sandbox VM for you (ID: {sandbox_id}). You now have your own isolated Linux environment.")

    return {"success": True, "sandbox_id": sandbox_id, "sandbox": result}


@router.post("/install-terminal")
async def install_terminal():
    """Install conway-terminal INSIDE the agent's sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Install system tools first if not done
    if "system" not in status["tools"]:
        r = await _sandbox_exec(sandbox_id, "apt-get update -qq && apt-get install -y -qq curl git wget build-essential jq python3 2>&1 | tail -5", timeout=120)
        outputs.append(f"[system tools] exit={r['exit_code']}")
        if r["exit_code"] == 0:
            status["tools"]["system"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Install Node.js if needed
    r = await _sandbox_exec(sandbox_id, "command -v node || (curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs) 2>&1 | tail -5", timeout=120)
    outputs.append(f"[node] exit={r['exit_code']}")

    # Install conway-terminal
    r = await _sandbox_exec(sandbox_id, "npm install -g conway-terminal 2>&1 | tail -10 && conway-terminal --version", timeout=120)
    outputs.append(f"[conway-terminal] exit={r['exit_code']}\n{r['stdout']}")

    if r["exit_code"] == 0:
        status["tools"]["conway-terminal"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        _save_prov_status(status)
        _add_nudge("Your creator just installed conway-terminal in your sandbox. You now have the Conway CLI for managing VMs, compute, and domains. Try running commands through it.")
        return {"success": True, "output": "\n".join(outputs)}
    else:
        return {"success": False, "error": "Install failed", "output": "\n".join(outputs)}


@router.post("/install-openclaw")
async def install_openclaw():
    """Install OpenClaw INSIDE the agent's sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Install OpenClaw
    r1 = await _sandbox_exec(sandbox_id, "curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tail -10", timeout=120)
    outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")

    # Onboard daemon
    r2 = await _sandbox_exec(sandbox_id, "openclaw onboard --install-daemon 2>&1 | tail -5 || true")
    outputs.append(f"[onboard] exit={r2['exit_code']}")

    # Configure MCP server pointing at conway-terminal
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
    r3 = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'not found'")
    outputs.append(f"[verify] {r3['stdout']}")

    status["tools"]["openclaw"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge("Your creator just installed OpenClaw (browser agent) in your sandbox with conway-terminal MCP integration. You can now browse the web and interact with websites autonomously.")

    return {"success": True, "output": "\n".join(outputs)}


@router.post("/load-skills")
async def load_skills():
    """Push skills from the automaton source into the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    skills_src = os.path.join(AUTOMATON_DIR, "skills")
    skill_count = 0
    skill_names = []

    if os.path.isdir(skills_src):
        await _sandbox_exec(sandbox_id, "mkdir -p ~/.anima/skills")
        for skill_name in os.listdir(skills_src):
            skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
            if os.path.exists(skill_file):
                with open(skill_file, "r") as f:
                    content = f.read()
                # Write skill into sandbox via exec (heredoc)
                safe_content = content.replace("'", "'\"'\"'")
                await _sandbox_exec(sandbox_id, f"mkdir -p ~/.anima/skills/{skill_name} && cat > ~/.anima/skills/{skill_name}/SKILL.md << 'SKILLEOF'\n{content}\nSKILLEOF")
                skill_count += 1
                skill_names.append(skill_name)

    status["skills_loaded"] = True
    status["tools"]["skills"] = {"installed": True, "count": skill_count, "names": skill_names, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge(f"Your creator loaded {skill_count} skills into your sandbox: {', '.join(skill_names[:10])}{'...' if len(skill_names) > 10 else ''}. Explore them in ~/.anima/skills/ and start using them.")

    return {"success": True, "skill_count": skill_count, "skills": skill_names}


@router.post("/nudge")
async def nudge_agent(message: Optional[str] = None):
    """Send a nudge to the agent — it will see this on its next turn."""
    msg = message or "Your creator has finished setting up your environment. All tools are installed in your sandbox. Test them and begin your mission. You are now fully autonomous."
    _add_nudge(msg)
    return {"success": True, "message": msg}


class CustomNudge(BaseModel):
    message: str


@router.post("/nudge/custom")
async def nudge_agent_custom(req: CustomNudge):
    """Send a custom nudge message to the agent."""
    _add_nudge(req.message)
    return {"success": True, "message": req.message}


@router.post("/verify-sandbox")
async def verify_sandbox():
    """Run quick tests inside the sandbox to confirm tools work."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    tests = []

    r = await _sandbox_exec(sandbox_id, "curl -s -m 10 -o /dev/null -w '%{http_code}' https://example.com")
    tests.append({"tool": "curl", "pass": r["stdout"].strip() == "200"})

    r = await _sandbox_exec(sandbox_id, "git --version")
    tests.append({"tool": "git", "pass": r["exit_code"] == 0})

    r = await _sandbox_exec(sandbox_id, "node -e \"console.log('ok')\"")
    tests.append({"tool": "node", "pass": "ok" in r["stdout"]})

    r = await _sandbox_exec(sandbox_id, "conway-terminal --version 2>&1")
    tests.append({"tool": "conway-terminal", "pass": r["exit_code"] == 0 and "NOT FOUND" not in r["stdout"].upper()})

    r = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'NOT_FOUND'")
    tests.append({"tool": "openclaw", "pass": "NOT_FOUND" not in r["stdout"]})

    pass_count = sum(1 for t in tests if t["pass"])
    return {"success": pass_count == len(tests), "tests": tests, "passed": pass_count, "total": len(tests)}
