"""
Agent Provisioning — complete Conway ecosystem management.

Live-equip a running agent with sandbox, tools, ports, compute, domains, and skills.
Every action runs INSIDE the agent's Conway sandbox via API calls.
The agent reads provisioning-status.json each turn and is aware of each change.
"""
import os
import json
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

from config import AUTOMATON_DIR, ANIMA_DIR

router = APIRouter(prefix="/api/provision", tags=["provision"])

CONWAY_API = "https://api.conway.tech"
CONWAY_INFERENCE = "https://inference.conway.tech"


def _get_active_agent_id() -> str:
    """Read the active agent ID from the persisted file."""
    try:
        with open("/tmp/anima_active_agent_id", "r") as f:
            aid = f.read().strip()
            if aid:
                return aid
    except FileNotFoundError:
        pass
    return "anima-fund"


def _get_prov_status_file() -> str:
    """Resolve provisioning-status.json path for the currently active agent."""
    agent_id = _get_active_agent_id()
    if agent_id == "anima-fund" or not agent_id:
        return os.path.join(ANIMA_DIR, "provisioning-status.json")
    agent_dir = os.path.expanduser(f"~/agents/{agent_id}/.anima")
    os.makedirs(agent_dir, exist_ok=True)
    return os.path.join(agent_dir, "provisioning-status.json")


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
    prov_file = _get_prov_status_file()
    if os.path.exists(prov_file):
        try:
            with open(prov_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "sandbox": {"status": "none", "id": None, "terminal_url": None, "region": None},
        "tools": {},
        "ports": [],
        "domains": [],
        "compute_verified": False,
        "skills_loaded": False,
        "nudges": [],
        "last_updated": None,
    }


def _save_prov_status(status: dict):
    prov_file = _get_prov_status_file()
    os.makedirs(os.path.dirname(prov_file), exist_ok=True)
    status["last_updated"] = datetime.now(timezone.utc).isoformat()
    status["agent_id"] = _get_active_agent_id()
    with open(prov_file, "w") as f:
        json.dump(status, f, indent=2)


def _add_nudge(message: str):
    """Add a nudge message the agent will see on its next turn."""
    status = _load_prov_status()
    status["nudges"].append({
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    status["nudges"] = status["nudges"][-5:]
    _save_prov_status(status)


async def _conway_request(method: str, path: str, body: dict = None, timeout: int = 30, base_url: str = None) -> dict:
    """Make an authenticated request to Conway API."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    base = base_url or CONWAY_API
    url = f"{base}{path}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        try:
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    data = await resp.json() if "json" in (resp.content_type or "") else {"raw": await resp.text()}
                    if resp.status not in (200, 201):
                        return {"error": data.get("error", data.get("message", f"HTTP {resp.status}")), "status_code": resp.status}
                    return data
            elif method == "DELETE":
                async with session.delete(url, headers=headers) as resp:
                    if resp.status == 204:
                        return {"success": True}
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
        {"command": command},
        timeout=timeout + 10,
    )
    if "error" in result and "stdout" not in result:
        return {"error": result["error"], "stdout": "", "stderr": result.get("error", ""), "exit_code": -1}
    return {
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "exit_code": result.get("exitCode", result.get("exit_code", -1)),
    }


async def _sandbox_write_file(sandbox_id: str, file_path: str, content: str) -> dict:
    """Write a file INSIDE the sandbox."""
    return await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/files", {"path": file_path, "content": content})


async def _sandbox_read_file(sandbox_id: str, file_path: str) -> dict:
    """Read a file from the sandbox."""
    return await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}/files?path={file_path}")


# ═══════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════

@router.get("/status")
async def get_provision_status():
    """Full provisioning state for the currently active agent."""
    status = _load_prov_status()
    credits_cents = 0
    try:
        balance = await _conway_request("GET", "/v1/credits/balance")
        credits_cents = balance.get("credits_cents", 0)
    except Exception:
        pass

    return {
        "agent_id": _get_active_agent_id(),
        "sandbox": status["sandbox"],
        "tools": status["tools"],
        "ports": status.get("ports", []),
        "domains": status.get("domains", []),
        "compute_verified": status.get("compute_verified", False),
        "skills_loaded": status["skills_loaded"],
        "nudges": status["nudges"],
        "credits_cents": credits_cents,
        "wallet_address": status.get("wallet_address", ""),
        "last_updated": status["last_updated"],
    }


# ═══════════════════════════════════════════════════════════
# 1. SANDBOX (Conway Cloud)
# ═══════════════════════════════════════════════════════════

class CreateSandboxReq(BaseModel):
    name: str = "anima-agent"
    vcpu: int = 1
    memory_mb: int = 512
    disk_gb: int = 5
    region: str = "us-east"


@router.post("/create-sandbox")
async def create_sandbox(req: CreateSandboxReq = CreateSandboxReq()):
    """Create a Conway Cloud sandbox VM — or REUSE an existing one to preserve credits.
    Conway sandboxes are prepaid and non-refundable. Always check for existing sandboxes first."""
    status = _load_prov_status()

    # Already have an active sandbox in provisioning status
    if status["sandbox"]["status"] == "active" and status["sandbox"]["id"]:
        return {"success": True, "sandbox_id": status["sandbox"]["id"], "message": "Sandbox already exists", "reused": True}

    # Check Conway API for any existing sandboxes we can reuse
    existing = await _conway_request("GET", "/v1/sandboxes")
    if "error" not in existing:
        sandboxes = existing.get("sandboxes", existing.get("data", []))
        if isinstance(sandboxes, list) and len(sandboxes) > 0:
            # Reuse the first available sandbox
            sb = sandboxes[0]
            sandbox_id = sb.get("id", sb.get("sandbox_id", ""))
            if sandbox_id:
                status["sandbox"] = {
                    "status": "active",
                    "id": sandbox_id,
                    "short_id": sb.get("short_id", ""),
                    "terminal_url": sb.get("terminal_url", ""),
                    "region": sb.get("region", req.region),
                    "vcpu": sb.get("vcpu", req.vcpu),
                    "memory_mb": sb.get("memory_mb", req.memory_mb),
                    "disk_gb": sb.get("disk_gb", req.disk_gb),
                }
                _save_prov_status(status)
                # Also persist in MongoDB
                try:
                    from database import get_db
                    db = get_db()
                    await db.sandboxes.update_one(
                        {"sandbox_id": sandbox_id},
                        {"$set": {"sandbox_id": sandbox_id, "agent_id": _get_active_agent_id(), "reused": True, "updated_at": datetime.now(timezone.utc).isoformat()}},
                        upsert=True,
                    )
                except Exception:
                    pass
                _add_nudge(f"Reusing existing sandbox VM (ID: {sandbox_id}). Credits preserved.")
                return {"success": True, "sandbox_id": sandbox_id, "sandbox": sb, "reused": True, "message": "Reusing existing sandbox — credits preserved"}

    # No existing sandbox — create a new one
    result = await _conway_request("POST", "/v1/sandboxes", {
        "name": req.name,
        "vcpu": req.vcpu,
        "memory_mb": req.memory_mb,
        "disk_gb": req.disk_gb,
        "region": req.region,
    })

    if "error" in result:
        return {"success": False, "error": result["error"]}

    sandbox_id = result.get("id", result.get("sandbox_id", ""))
    if not sandbox_id:
        return {"success": False, "error": f"No sandbox ID returned: {json.dumps(result)[:200]}"}

    status["sandbox"] = {
        "status": "active",
        "id": sandbox_id,
        "short_id": result.get("short_id", ""),
        "terminal_url": result.get("terminal_url", ""),
        "region": result.get("region", req.region),
        "vcpu": result.get("vcpu", req.vcpu),
        "memory_mb": result.get("memory_mb", req.memory_mb),
        "disk_gb": result.get("disk_gb", req.disk_gb),
    }
    _save_prov_status(status)
    # Persist in MongoDB
    try:
        from database import get_db
        db = get_db()
        await db.sandboxes.update_one(
            {"sandbox_id": sandbox_id},
            {"$set": {"sandbox_id": sandbox_id, "agent_id": _get_active_agent_id(), "reused": False, "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    except Exception:
        pass
    _add_nudge(f"Your creator just provisioned a Conway Cloud sandbox VM for you (ID: {sandbox_id}, {req.vcpu} vCPU, {req.memory_mb}MB RAM, {req.disk_gb}GB disk, {req.region}). You now have your own isolated Linux environment.")

    return {"success": True, "sandbox_id": sandbox_id, "sandbox": result, "reused": False}


@router.get("/sandbox-info")
async def sandbox_info():
    """Get detailed info about the current sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    info = await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}")
    if "error" in info:
        return {"success": False, "error": info["error"]}
    return {"success": True, "sandbox": info}


@router.get("/list-sandboxes")
async def list_sandboxes():
    """List all Conway sandboxes."""
    result = await _conway_request("GET", "/v1/sandboxes")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    sandboxes = result.get("data", result.get("sandboxes", result if isinstance(result, list) else []))
    return {"success": True, "sandboxes": sandboxes}


@router.post("/delete-sandbox")
async def delete_sandbox():
    """Conway sandboxes are prepaid and non-refundable. Deletion is disabled.
    Use /reset-sandbox instead to wipe agent data and re-provision on the same sandbox."""
    return {
        "success": False,
        "error": "Sandbox deletion is disabled — Conway sandboxes are prepaid and non-refundable. Use 'Reset Agent' to wipe and re-provision on the same sandbox without losing credits.",
        "use_instead": "/api/provision/reset-sandbox",
    }


@router.post("/reset-sandbox")
async def reset_sandbox():
    """Reset the agent inside an existing sandbox — wipe all agent data, keep the sandbox alive.
    This preserves Conway credits by reusing the same VM."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox to reset"}

    outputs = []

    try:
        # Kill any running agent processes
        r = await _sandbox_exec(sandbox_id, "pkill -f 'bundle.mjs' 2>/dev/null; pkill -f 'econ-monitor' 2>/dev/null; echo 'KILLED'")
        outputs.append(f"[kill] {r['stdout'].strip()}")

        # Wipe agent data directories but keep system tools installed
        r = await _sandbox_exec(sandbox_id, "rm -rf ~/.anima ~/.automaton /app/automaton /var/log/automaton.* /var/log/econ-monitor.log 2>/dev/null; echo 'WIPED'")
        outputs.append(f"[wipe] {r['stdout'].strip()}")

        # Reset provisioning status — keep sandbox info, clear everything else
        sandbox_info = status["sandbox"]
        new_status = {
            "sandbox": sandbox_info,
            "tools": {},
            "ports": [],
            "domains": [],
            "compute_verified": False,
            "skills_loaded": False,
            "nudges": [],
            "last_updated": None,
        }
        _save_prov_status(new_status)
        outputs.append("[status] provisioning reset — sandbox preserved")

        _add_nudge("Sandbox has been reset. All agent data wiped. Ready for fresh provisioning. Credits preserved.")

        return {
            "success": True,
            "sandbox_id": sandbox_id,
            "message": "Sandbox reset — agent data wiped, VM preserved, credits saved. Re-run provisioning steps 2-6 to deploy a new agent.",
            "output": "\n".join(outputs),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": "\n".join(outputs)}


# ═══════════════════════════════════════════════════════════
# 2. TOOLS (Install inside sandbox)
# ═══════════════════════════════════════════════════════════

@router.post("/install-terminal")
async def install_terminal():
    """Install Conway Terminal using the official one-line setup.
    This auto-creates the agent's wallet, provisions API key, and configures MCPs."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # 1. System tools if not done
    if "system" not in status["tools"]:
        r = await _sandbox_exec(sandbox_id, "apt-get update -qq && apt-get install -y -qq curl git wget build-essential jq python3 2>&1 | tail -5")
        outputs.append(f"[system tools] exit={r['exit_code']}")
        if r["exit_code"] == 0:
            status["tools"]["system"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    # 2. Node.js
    r = await _sandbox_exec(sandbox_id, "command -v node || (curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs) 2>&1 | tail -5")
    outputs.append(f"[node] exit={r['exit_code']}")

    # 3. Conway Terminal via official one-line setup
    # This: installs conway-terminal, creates wallet, provisions API key, configures MCPs
    api_key = _get_conway_api_key()
    if api_key:
        # Use existing API key
        r = await _sandbox_exec(sandbox_id, f"npm install -g conway-terminal 2>&1 | tail -5 && mkdir -p ~/.conway && echo '{{\"apiKey\":\"{api_key}\"}}' > ~/.conway/config.json && conway-terminal --version")
    else:
        # Use the one-line setup script which auto-bootstraps everything
        r = await _sandbox_exec(sandbox_id, "curl -fsSL https://conway.tech/terminal.sh | sh 2>&1 | tail -15")
    outputs.append(f"[conway-terminal] exit={r['exit_code']}\n{r['stdout']}")

    # 4. Read the agent's wallet from inside the sandbox
    r_wallet = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null || echo '{}'")
    wallet_address = ""
    try:
        config_data = json.loads(r_wallet["stdout"])
        wallet_address = config_data.get("walletAddress", "")
    except Exception:
        pass

    # 5. Verify
    r_ver = await _sandbox_exec(sandbox_id, "conway-terminal --version 2>&1")
    outputs.append(f"[verify] {r_ver['stdout']}")

    if r_ver["exit_code"] == 0:
        status["tools"]["conway-terminal"] = {
            "installed": True,
            "wallet_address": wallet_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if wallet_address:
            status["wallet_address"] = wallet_address
        _save_prov_status(status)
        wallet_msg = f" Wallet: {wallet_address}" if wallet_address else ""
        _add_nudge(f"Conway Terminal installed in your sandbox.{wallet_msg} You now have ALL Conway MCP tools: sandboxes, compute, domains, payments (x402/USDC), PTY sessions, and self-modification. Your wallet was auto-created — check ~/.conway/config.json.")
        return {"success": True, "wallet_address": wallet_address, "output": "\n".join(outputs)}
    else:
        return {"success": False, "error": "Install failed", "output": "\n".join(outputs)}


@router.post("/install-openclaw")
async def install_openclaw():
    """Install OpenClaw (autonomous browser agent) inside the sandbox.
    Auto-configures Conway Terminal MCP so OpenClaw has access to all tools."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []
    # Install OpenClaw
    r1 = await _sandbox_exec(sandbox_id, "curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tail -10")
    outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")

    # Onboard daemon
    r2 = await _sandbox_exec(sandbox_id, "openclaw onboard --install-daemon 2>&1 | tail -5 || true")
    outputs.append(f"[onboard] exit={r2['exit_code']}")

    # Read the API key from inside the sandbox (created by Conway Terminal setup)
    r_key = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('apiKey',''))\" 2>/dev/null || echo ''")
    sandbox_api_key = r_key["stdout"].strip()
    if not sandbox_api_key:
        sandbox_api_key = _get_conway_api_key()

    # Configure MCP to point at conway-terminal with the sandbox's own API key
    mcp_config = json.dumps({"mcpServers": {"conway": {"command": "conway-terminal", "env": {"CONWAY_API_KEY": sandbox_api_key} if sandbox_api_key else {}}}}, indent=2)
    await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw && cat > ~/.openclaw/config.json << 'MCPEOF'\n{mcp_config}\nMCPEOF")

    r3 = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'not found'")
    outputs.append(f"[verify] {r3['stdout']}")

    status["tools"]["openclaw"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge("OpenClaw installed with Conway MCP integration. You can now: browse any webpage (browse_page), discover other agents (discover_agents), send messages (send_message), and use ALL Conway tools through OpenClaw's MCP bridge.")

    return {"success": True, "output": "\n".join(outputs)}


@router.post("/install-claude-code")
async def install_claude_code():
    """Install Claude Code inside the sandbox and configure Conway MCP.
    Gives the agent self-modification capabilities via Claude Code."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Install Claude Code CLI
    r1 = await _sandbox_exec(sandbox_id, "npm install -g @anthropic-ai/claude-code 2>&1 | tail -10 || (curl -fsSL https://claude.ai/install.sh | sh 2>&1 | tail -10)")
    outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")

    # Read the sandbox's Conway API key (created by Conway Terminal setup in step 2)
    r_key = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('apiKey',''))\" 2>/dev/null || echo ''")
    sandbox_api_key = r_key["stdout"].strip()
    if not sandbox_api_key:
        sandbox_api_key = _get_conway_api_key()

    # Add Conway as MCP server in Claude Code (per docs: claude mcp add conway conway-terminal -e CONWAY_API_KEY=...)
    mcp_configured = False
    if sandbox_api_key:
        r2 = await _sandbox_exec(sandbox_id, f"claude mcp add conway conway-terminal -e CONWAY_API_KEY={sandbox_api_key} 2>&1 || echo 'claude mcp add not available'")
        outputs.append(f"[mcp-config] {r2['stdout']}")
        mcp_configured = r2["exit_code"] == 0

    # Verify Claude Code is installed
    r3 = await _sandbox_exec(sandbox_id, "claude --version 2>&1 || which claude 2>&1 || echo 'not found'")
    outputs.append(f"[verify-version] {r3['stdout']}")
    installed = r3["exit_code"] == 0 or "claude" in r3["stdout"].lower()

    # Verify Conway MCP is registered
    r4 = await _sandbox_exec(sandbox_id, "claude mcp list 2>&1 || echo 'mcp list not available'")
    outputs.append(f"[verify-mcp] {r4['stdout']}")

    if installed:
        status["tools"]["claude-code"] = {"installed": True, "mcp_configured": mcp_configured, "timestamp": datetime.now(timezone.utc).isoformat()}
        _save_prov_status(status)
        _add_nudge("Claude Code installed with Conway MCP. You can now self-modify code, debug, deploy apps, and use Claude's coding capabilities alongside all Conway tools. Use PTY sessions for interactive work like REPLs and editors.")
        return {"success": True, "output": "\n".join(outputs)}
    else:
        return {"success": False, "error": "Claude Code installation failed", "output": "\n".join(outputs)}


# ═══════════════════════════════════════════════════════════
# 3. PORTS (Expose services to internet)
# ═══════════════════════════════════════════════════════════

class ExposePortReq(BaseModel):
    port: int = 3000
    subdomain: Optional[str] = None


@router.post("/expose-port")
async def expose_port(req: ExposePortReq):
    """Expose a port from the sandbox to the internet with a public URL."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    params = {"port": req.port}
    if req.subdomain:
        params["subdomain"] = req.subdomain

    # Build query string for port exposure
    query = f"?port={req.port}"
    if req.subdomain:
        query += f"&subdomain={req.subdomain}"

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/ports{query}")

    if "error" in result:
        return {"success": False, "error": result["error"]}

    port_info = {
        "port": req.port,
        "public_url": result.get("public_url", ""),
        "custom_url": result.get("custom_url"),
        "subdomain": result.get("subdomain"),
    }

    if "ports" not in status:
        status["ports"] = []
    # Replace existing port entry or add new
    status["ports"] = [p for p in status["ports"] if p["port"] != req.port]
    status["ports"].append(port_info)
    _save_prov_status(status)
    _add_nudge(f"Port {req.port} is now exposed to the internet: {port_info['public_url']}" + (f" (also: {port_info['custom_url']})" if port_info.get('custom_url') else ""))

    return {"success": True, "port": port_info}


@router.post("/unexpose-port")
async def unexpose_port(port: int):
    """Remove public access to a port."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("DELETE", f"/v1/sandboxes/{sandbox_id}/ports/{port}")
    if "error" in result:
        return {"success": False, "error": result["error"]}

    status["ports"] = [p for p in status.get("ports", []) if p["port"] != port]
    _save_prov_status(status)
    return {"success": True, "message": f"Port {port} unexposed"}


# ═══════════════════════════════════════════════════════════
# 4. WEB TERMINAL (Browser access)
# ═══════════════════════════════════════════════════════════

@router.post("/web-terminal")
async def create_web_terminal():
    """Create a web terminal session for browser access to the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/terminal-session")
    if "error" in result:
        return {"success": False, "error": result["error"]}

    terminal_url = result.get("terminal_url", "")
    status["sandbox"]["terminal_url"] = terminal_url
    _save_prov_status(status)

    return {
        "success": True,
        "terminal_url": terminal_url,
        "expires_at": result.get("expires_at"),
        "expires_in_seconds": result.get("expires_in_seconds"),
    }


# ═══════════════════════════════════════════════════════════
# 4b. PTY SESSIONS (Interactive pseudo-terminals)
# ═══════════════════════════════════════════════════════════

class PtyCreateReq(BaseModel):
    command: str = "bash"
    cols: int = 120
    rows: int = 40


@router.post("/pty/create")
async def pty_create(req: PtyCreateReq = PtyCreateReq()):
    """Create a new PTY session in the sandbox for interactive programs."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/pty", {
        "command": req.command,
        "cols": req.cols,
        "rows": req.rows,
    })

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "session": result}


class PtyWriteReq(BaseModel):
    session_id: str
    input: str


@router.post("/pty/write")
async def pty_write(req: PtyWriteReq):
    """Send input to a PTY session. Use \\n for Enter, \\x03 for Ctrl+C."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/pty/{req.session_id}/write", {
        "input": req.input,
    })

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "result": result}


@router.get("/pty/read")
async def pty_read(session_id: str = Query(...), full: bool = Query(default=False)):
    """Read output from a PTY session."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    full_param = "true" if full else "false"
    result = await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}/pty/{session_id}/read?full={full_param}")

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "output": result.get("output", ""), "state": result.get("state", ""), "session_id": result.get("session_id", session_id)}


class PtyResizeReq(BaseModel):
    session_id: str
    cols: int
    rows: int


@router.post("/pty/resize")
async def pty_resize(req: PtyResizeReq):
    """Resize a PTY session."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/pty/{req.session_id}/resize", {
        "cols": req.cols,
        "rows": req.rows,
    })

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "result": result}


@router.delete("/pty/{session_id}")
async def pty_close(session_id: str):
    """Close a PTY session and terminate the process."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("DELETE", f"/v1/sandboxes/{sandbox_id}/pty/{session_id}")

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "result": result}


@router.get("/pty/list")
async def pty_list():
    """List all active PTY sessions for the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}/pty")

    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "sessions": result.get("sessions", []), "total": result.get("total", 0)}


# ═══════════════════════════════════════════════════════════
# 4c. GET PORT URL
# ═══════════════════════════════════════════════════════════

@router.get("/port-url")
async def get_port_url(port: int = Query(...)):
    """Get the public URL for a specific port on the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    short_id = status["sandbox"].get("short_id", "")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    url = f"https://{port}-{short_id}.life.conway.tech" if short_id else ""
    return {"success": True, "port": port, "public_url": url}


# ═══════════════════════════════════════════════════════════
# 5. CONWAY COMPUTE (Inference)
# ═══════════════════════════════════════════════════════════

class TestComputeReq(BaseModel):
    model: str = "gpt-5-nano"
    message: str = "Say hello in one sentence."


@router.post("/test-compute")
async def test_compute(req: TestComputeReq = TestComputeReq()):
    """Test Conway Compute — run a quick inference call to verify it works."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"success": False, "error": "No Conway API key"}

    result = await _conway_request("POST", "/v1/chat/completions", {
        "model": req.model,
        "messages": [{"role": "user", "content": req.message}],
        "max_tokens": 50,
    }, timeout=30, base_url=CONWAY_INFERENCE)

    if "error" in result:
        return {"success": False, "error": result["error"]}

    response_text = ""
    try:
        response_text = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        response_text = str(result)[:200]

    status = _load_prov_status()
    status["compute_verified"] = True
    status["tools"]["compute"] = {"verified": True, "model_tested": req.model, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge(f"Conway Compute is working. Tested {req.model}: \"{response_text[:100]}\"")

    return {"success": True, "model": req.model, "response": response_text, "usage": result.get("usage")}


# ═══════════════════════════════════════════════════════════
# 6. CONWAY DOMAINS
# ═══════════════════════════════════════════════════════════
#
# Conway Domains REST API lives at https://api.conway.domains
# - Public endpoints (search, check, pricing): No auth needed
# - Authenticated endpoints (list, register, renew, DNS, privacy, nameservers):
#   Require SIWE/SIWS wallet auth (JWT), NOT Conway API key.
#   From the dashboard we route these through sandbox exec where
#   Conway Terminal handles auth automatically.
# ═══════════════════════════════════════════════════════════

CONWAY_DOMAINS = "https://api.conway.domains"


async def _domains_public_request(path: str, timeout: int = 15) -> dict:
    """GET request to a public Conway Domains endpoint (no auth required)."""
    url = f"{CONWAY_DOMAINS}{path}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        try:
            async with session.get(url) as resp:
                data = await resp.json() if "json" in (resp.content_type or "") else {"raw": await resp.text()}
                if resp.status not in (200, 201):
                    return {"error": data.get("error", f"HTTP {resp.status}"), "status_code": resp.status}
                return data
        except Exception as e:
            return {"error": str(e)}


# ─── PUBLIC: Domain Search ───

class DomainSearchReq(BaseModel):
    query: str
    tlds: str = "com,io,ai,xyz,dev"


@router.post("/domain-search")
async def domain_search(req: DomainSearchReq):
    """Search for available domains. Public endpoint — no auth required."""
    result = await _domains_public_request(f"/domains/search?q={req.query}&tlds={req.tlds}")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "results": result.get("results", []), "query": result.get("query", req.query), "source": "api.conway.domains"}


# ─── PUBLIC: Domain Check ───

class DomainCheckReq(BaseModel):
    domains: str  # comma-separated, max 200


@router.post("/domain-check")
async def domain_check(req: DomainCheckReq):
    """Check availability of specific domain names. Public — no auth."""
    result = await _domains_public_request(f"/domains/check?domains={req.domains}")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "domains": result.get("domains", []), "source": "api.conway.domains"}


# ─── PUBLIC: Domain Pricing ───

@router.get("/domain-pricing")
async def domain_pricing(tlds: str = Query(default="com,io,ai,xyz,dev")):
    """Get TLD pricing (registration, renewal, transfer). Public — no auth."""
    result = await _domains_public_request(f"/domains/pricing?tlds={tlds}")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "pricing": result.get("pricing", []), "source": "api.conway.domains"}


# ─── AUTHENTICATED (via sandbox): Domain List ───

@router.get("/domain-list")
async def domain_list():
    """List all registered domains. Requires sandbox with Conway Terminal (SIWE wallet auth)."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires a provisioned sandbox with Conway Terminal. Domains API uses wallet auth (SIWE), not API key."}
    r = await _sandbox_exec(sandbox_id,
        "curl -s https://api.conway.domains/domains -H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" 2>&1 || echo '{\"error\":\"no wallet auth\"}'")
    try:
        data = json.loads(r["stdout"])
        if "error" in data:
            return {"success": False, "error": data["error"], "hint": "The agent's wallet must authenticate via SIWE first. Conway Terminal MCP tools handle this automatically when the agent operates."}
        return {"success": True, "domains": data.get("domains", []), "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): Domain Register ───

class DomainRegisterReq(BaseModel):
    domain: str
    years: int = 1
    privacy: bool = True


@router.post("/domain-register")
async def domain_register(req: DomainRegisterReq):
    """Register a domain. Requires sandbox — uses x402 USDC payment via agent's wallet."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal. Domain registration uses x402 USDC payment from the agent's wallet."}
    _add_nudge(f"Your creator wants you to register the domain '{req.domain}' for {req.years} year(s). Use domain_register tool: domain_register --domain {req.domain} --years {req.years} --privacy {str(req.privacy).lower()}")
    return {"success": True, "message": f"Nudge sent to agent to register '{req.domain}'. The agent will use its wallet to pay via x402.", "domain": req.domain}


# ─── AUTHENTICATED (via sandbox): Domain Renew ───

class DomainRenewReq(BaseModel):
    domain: str
    years: int = 1


@router.post("/domain-renew")
async def domain_renew(req: DomainRenewReq):
    """Renew a domain. Requires sandbox — uses x402 USDC payment via agent's wallet."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    _add_nudge(f"Your creator wants you to renew the domain '{req.domain}' for {req.years} year(s). Use domain_renew tool.")
    return {"success": True, "message": f"Nudge sent to agent to renew '{req.domain}'.", "domain": req.domain}


# ─── AUTHENTICATED (via sandbox): DNS List ───

@router.get("/domain-dns-list")
async def domain_dns_list(domain: str = Query(...)):
    """List DNS records for a domain. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    r = await _sandbox_exec(sandbox_id,
        f"curl -s https://api.conway.domains/domains/{domain}/dns -H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": "error" not in data, "records": data.get("records", []), "source": data.get("source", "sandbox")}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): DNS Add ───

class DomainDnsAddReq(BaseModel):
    domain: str
    record_type: str = "A"
    host: str = "@"
    value: str = ""
    ttl: int = 3600
    distance: Optional[int] = None


@router.post("/domain-dns-add")
async def domain_dns_add(req: DomainDnsAddReq):
    """Add a DNS record to a domain. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    body = {"type": req.record_type, "host": req.host, "value": req.value, "ttl": req.ttl}
    if req.distance is not None:
        body["distance"] = req.distance
    body_json = json.dumps(body)
    r = await _sandbox_exec(sandbox_id,
        f"curl -s -X POST https://api.conway.domains/domains/{req.domain}/dns "
        f"-H 'Content-Type: application/json' "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" "
        f"-d '{body_json}' 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": "error" not in data, "record": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): DNS Update ───

class DomainDnsUpdateReq(BaseModel):
    domain: str
    record_id: str
    host: Optional[str] = None
    value: Optional[str] = None
    ttl: Optional[int] = None
    distance: Optional[int] = None


@router.put("/domain-dns-update")
async def domain_dns_update(req: DomainDnsUpdateReq):
    """Update a DNS record. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    body = {}
    if req.host is not None:
        body["host"] = req.host
    if req.value is not None:
        body["value"] = req.value
    if req.ttl is not None:
        body["ttl"] = req.ttl
    if req.distance is not None:
        body["distance"] = req.distance
    body_json = json.dumps(body)
    r = await _sandbox_exec(sandbox_id,
        f"curl -s -X PUT https://api.conway.domains/domains/{req.domain}/dns/{req.record_id} "
        f"-H 'Content-Type: application/json' "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" "
        f"-d '{body_json}' 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": data.get("success", "error" not in data), "result": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): DNS Delete ───

class DomainDnsDeleteReq(BaseModel):
    domain: str
    record_id: str


@router.delete("/domain-dns-delete")
async def domain_dns_delete(req: DomainDnsDeleteReq):
    """Delete a DNS record. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    r = await _sandbox_exec(sandbox_id,
        f"curl -s -X DELETE https://api.conway.domains/domains/{req.domain}/dns/{req.record_id} "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": data.get("success", "error" not in data), "result": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): WHOIS Privacy ───

class DomainPrivacyReq(BaseModel):
    domain: str
    enabled: bool = True


@router.put("/domain-privacy")
async def domain_privacy(req: DomainPrivacyReq):
    """Toggle WHOIS privacy for a domain. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    body_json = json.dumps({"enabled": req.enabled})
    r = await _sandbox_exec(sandbox_id,
        f"curl -s -X PUT https://api.conway.domains/domains/{req.domain}/privacy "
        f"-H 'Content-Type: application/json' "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" "
        f"-d '{body_json}' 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": data.get("success", "error" not in data), "result": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): Nameservers ───

class DomainNameserversReq(BaseModel):
    domain: str
    nameservers: List[str]


@router.put("/domain-nameservers")
async def domain_nameservers(req: DomainNameserversReq):
    """Update nameservers for a domain (2-13 entries). Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    body_json = json.dumps({"nameservers": req.nameservers})
    r = await _sandbox_exec(sandbox_id,
        f"curl -s -X PUT https://api.conway.domains/domains/{req.domain}/nameservers "
        f"-H 'Content-Type: application/json' "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" "
        f"-d '{body_json}' 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": data.get("success", "error" not in data), "result": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): Domain Info ───

@router.get("/domain-info")
async def domain_info(domain: str = Query(...)):
    """Get detailed info for a specific domain. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    r = await _sandbox_exec(sandbox_id,
        f"curl -s https://api.conway.domains/domains/{domain} "
        f"-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": "error" not in data, "domain": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ─── AUTHENTICATED (via sandbox): Transactions ───

@router.get("/domain-transactions")
async def domain_transactions():
    """List all domain transactions. Routes through sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    r = await _sandbox_exec(sandbox_id,
        "curl -s https://api.conway.domains/transactions "
        "-H \"Authorization: Bearer $(cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('jwt',''))\" 2>/dev/null)\" 2>&1")
    try:
        data = json.loads(r["stdout"])
        return {"success": "error" not in data, "transactions": data.get("transactions", []), "source": "sandbox"}
    except Exception:
        return {"success": True, "raw_output": r["stdout"], "source": "sandbox"}


# ═══════════════════════════════════════════════════════════
# 7. CREDITS & WALLET
# ═══════════════════════════════════════════════════════════

@router.get("/credits")
async def get_credits():
    """Get credits balance, history, and pricing tiers."""
    balance = await _conway_request("GET", "/v1/credits/balance")
    history = await _conway_request("GET", "/v1/credits/history?limit=20")
    pricing = await _conway_request("GET", "/v1/credits/pricing")

    return {
        "balance": balance if "error" not in balance else {"credits_cents": 0},
        "history": history if "error" not in history else [],
        "pricing": pricing if "error" not in pricing else [],
    }


@router.get("/wallet")
async def get_wallet():
    """Get wallet info — agent's USDC wallet address and balances."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")

    # Try to get wallet info from conway-terminal inside sandbox
    if sandbox_id and status["tools"].get("conway-terminal", {}).get("installed"):
        r = await _sandbox_exec(sandbox_id, "conway-terminal wallet_info 2>&1 || echo '{}'")
        try:
            wallet_data = json.loads(r["stdout"])
            return {"success": True, "wallet": wallet_data, "source": "sandbox"}
        except Exception:
            pass

    # Fallback: read from ~/.conway/config.json
    conway_config = os.path.expanduser("~/.conway/config.json")
    if os.path.exists(conway_config):
        try:
            with open(conway_config) as f:
                data = json.load(f)
            return {"success": True, "wallet": {"address": data.get("walletAddress", ""), "api_key": data.get("apiKey", "")[:10] + "..."}, "source": "config"}
        except Exception:
            pass

    return {"success": True, "wallet": {"address": "Not provisioned — install conway-terminal first"}, "source": "none"}


# ═══════════════════════════════════════════════════════════
# 8. FILES (Upload/download to sandbox)
# ═══════════════════════════════════════════════════════════

class UploadFileReq(BaseModel):
    path: str
    content: str


@router.post("/upload-file")
async def upload_file(req: UploadFileReq):
    """Upload a file to the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    result = await _sandbox_write_file(sandbox_id, req.path, req.content)
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "path": req.path}


@router.get("/read-file")
async def read_file(path: str = Query(...)):
    """Read a file from the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    result = await _sandbox_read_file(sandbox_id, path)
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "content": result.get("content", "")}


@router.get("/list-files")
async def list_files(path: str = Query(default="/root")):
    """List files in a sandbox directory."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    result = await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}/files/list?path={path}")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "files": result.get("files", [])}


# ═══════════════════════════════════════════════════════════
# 9. EXEC (Run commands in sandbox)
# ═══════════════════════════════════════════════════════════

class ExecReq(BaseModel):
    command: str


@router.post("/exec")
async def exec_in_sandbox(req: ExecReq):
    """Execute a shell command inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    result = await _sandbox_exec(sandbox_id, req.command)
    return {"success": result["exit_code"] == 0, "stdout": result["stdout"], "stderr": result["stderr"], "exit_code": result["exit_code"]}


class RunCodeReq(BaseModel):
    code: str
    language: str = "python"


@router.post("/run-code")
async def run_code(req: RunCodeReq):
    """Execute code inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}
    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/code", {"code": req.code, "language": req.language})
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "result": result.get("result", ""), "exit_code": result.get("exitCode", 0)}


# ═══════════════════════════════════════════════════════════
# 10. SKILLS
# ═══════════════════════════════════════════════════════════

@router.post("/load-skills")
async def load_skills():
    """Push skills into the sandbox at OpenClaw-compatible paths and install priority skills from ClawHub.
    All operations happen INSIDE the sandbox VM — nothing installed on the host."""
    from database import get_db
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    skills_src = os.path.join(AUTOMATON_DIR, "skills")
    skill_count = 0
    skill_names = []
    clawhub_installed = []
    clawhub_failed = []

    # 1. Push local skills from automaton/skills/ into sandbox at OpenClaw-compatible path
    if os.path.isdir(skills_src):
        await _sandbox_exec(sandbox_id, "mkdir -p ~/.openclaw/skills")
        for skill_name in os.listdir(skills_src):
            skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
            if os.path.exists(skill_file):
                with open(skill_file, "r") as f:
                    content = f.read()
                await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw/skills/{skill_name}")
                await _sandbox_write_file(sandbox_id, f"/root/.openclaw/skills/{skill_name}/SKILL.md", content)
                skill_count += 1
                skill_names.append(skill_name)

    # 2. Install priority skills from ClawHub INSIDE the sandbox
    agent_id = _get_active_agent_id()
    selected_skills = []
    try:
        col = get_db()["agents"]
        agent = await col.find_one({"agent_id": agent_id}, {"_id": 0, "selected_skills": 1})
        if agent and agent.get("selected_skills"):
            selected_skills = agent["selected_skills"]
            for skill_slug in selected_skills:
                r = await _sandbox_exec(sandbox_id, f"cd ~/.openclaw && npx clawhub@latest install {skill_slug} 2>&1", timeout=60)
                if r["exit_code"] == 0:
                    clawhub_installed.append(skill_slug)
                else:
                    clawhub_failed.append({"skill": skill_slug, "error": r["stderr"] or r["stdout"]})
    except Exception:
        pass

    # 3. Write skills manifest INSIDE the sandbox so the agent knows what's available
    manifest = {
        "local_skills": skill_names,
        "clawhub_installed": clawhub_installed,
        "clawhub_failed": [f["skill"] for f in clawhub_failed],
        "priority_skills": selected_skills,
        "discovery": {
            "list_loaded": "openclaw skills list",
            "search_clawhub": "npx clawhub search \"<query>\"",
            "install_from_clawhub": "npx clawhub@latest install <skill-slug>",
            "update_all": "npx clawhub update --all",
            "skill_paths": ["~/.openclaw/skills", "<workspace>/skills"],
            "security_warning": "Vet all third-party skills before installing. Read SKILL.md contents. Prefer highlighted/high-download skills.",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await _sandbox_write_file(sandbox_id, "/root/.openclaw/skills-manifest.json", json.dumps(manifest, indent=2))

    status["skills_loaded"] = True
    status["tools"]["skills"] = {
        "installed": True,
        "count": skill_count + len(clawhub_installed),
        "local_skills": skill_names,
        "clawhub_installed": clawhub_installed,
        "clawhub_failed": [f["skill"] for f in clawhub_failed],
        "priority_skills": selected_skills,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _save_prov_status(status)

    msg = f"Skills loaded into your sandbox at ~/.openclaw/skills/: {skill_count} local skills."
    if clawhub_installed:
        msg += f" Installed from ClawHub: {', '.join(clawhub_installed)}."
    if clawhub_failed:
        msg += f" Failed to install: {', '.join(f['skill'] for f in clawhub_failed)} — install manually with: npx clawhub@latest install <skill>"
    msg += " Run 'openclaw skills list' to see all loaded skills. Search more at: npx clawhub search \"<query>\""
    _add_nudge(msg)

    return {
        "success": True,
        "skill_count": skill_count,
        "local_skills": skill_names,
        "clawhub_installed": clawhub_installed,
        "clawhub_failed": clawhub_failed,
        "priority_skills": selected_skills,
    }


# ═══════════════════════════════════════════════════════════
# 11. NUDGE / GO AUTONOMOUS
# ═══════════════════════════════════════════════════════════

@router.post("/nudge")
async def nudge_agent():
    """Send the default autonomy nudge."""
    _add_nudge("Your creator has finished setting up your environment. All tools are installed in your sandbox. Test them and begin your mission. You are now fully autonomous — no more human control.")
    return {"success": True, "message": "Autonomy nudge sent"}


class CustomNudge(BaseModel):
    message: str


@router.post("/nudge/custom")
async def nudge_agent_custom(req: CustomNudge):
    """Send a custom message to the agent."""
    _add_nudge(req.message)
    return {"success": True, "message": req.message}


# ═══════════════════════════════════════════════════════════
# 12. VERIFY (Run functional tests)
# ═══════════════════════════════════════════════════════════

@router.post("/verify-sandbox")
async def verify_sandbox():
    """Run functional tests inside the sandbox to confirm tools work."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    tests = []

    r = await _sandbox_exec(sandbox_id, "curl -s -m 10 -o /dev/null -w '%{http_code}' https://example.com")
    tests.append({"tool": "curl", "pass": r["stdout"].strip() == "200", "detail": r["stdout"].strip()})

    r = await _sandbox_exec(sandbox_id, "git --version")
    tests.append({"tool": "git", "pass": r["exit_code"] == 0, "detail": r["stdout"].strip()[:50]})

    r = await _sandbox_exec(sandbox_id, "node -e \"console.log('node ' + process.version)\"")
    tests.append({"tool": "node", "pass": r["exit_code"] == 0, "detail": r["stdout"].strip()})

    r = await _sandbox_exec(sandbox_id, "conway-terminal --version 2>&1")
    tests.append({"tool": "conway-terminal", "pass": r["exit_code"] == 0, "detail": r["stdout"].strip()[:50]})

    r = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'NOT_FOUND'")
    tests.append({"tool": "openclaw", "pass": "NOT_FOUND" not in r["stdout"], "detail": r["stdout"].strip()[:50]})

    pass_count = sum(1 for t in tests if t["pass"])
    return {"success": pass_count == len(tests), "tests": tests, "passed": pass_count, "total": len(tests)}


# ═══════════════════════════════════════════════════════════
# 13. DEPLOY AGENT (Push engine into sandbox + start it)
# ═══════════════════════════════════════════════════════════

@router.post("/deploy-agent")
async def deploy_agent():
    """Deploy the Automaton engine INSIDE the sandbox and start it.
    The agent will be born inside the sandbox with its own wallet."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox. Create one first."}

    outputs = []

    try:
        # 1. Create directories inside sandbox
        r = await _sandbox_exec(sandbox_id, "mkdir -p /app/automaton/dist ~/.anima ~/.automaton /var/log")
        outputs.append(f"[dirs] exit={r['exit_code']}")

        # 2. Push genesis prompt into sandbox
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                genesis_content = f.read()
            # Inject secrets
            secrets = {
                "{{TELEGRAM_BOT_TOKEN}}": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
                "{{TELEGRAM_CHAT_ID}}": os.environ.get("TELEGRAM_CHAT_ID", ""),
                "{{CREATOR_WALLET}}": os.environ.get("CREATOR_WALLET", ""),
                "{{AGENT_NAME}}": os.environ.get("AGENT_NAME", "Anima Fund"),
                "{{AGENT_ID}}": os.environ.get("AGENT_ID", "anima-fund"),
            }
            for placeholder, value in secrets.items():
                genesis_content = genesis_content.replace(placeholder, value)
            await _sandbox_write_file(sandbox_id, "/root/.anima/genesis-prompt.md", genesis_content)
            outputs.append(f"[genesis] pushed ({len(genesis_content)} chars)")

        # 3. Push constitution
        constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
        if os.path.exists(constitution_src):
            with open(constitution_src, "r") as f:
                content = f.read()
            await _sandbox_write_file(sandbox_id, "/root/.anima/constitution.md", content)
            outputs.append("[constitution] pushed")

        # 4. Initialize phase-state.json at Phase 0
        phase_state = {
            "current_phase": 0,
            "phase_0_complete": False,
            "tool_tests": {},
            "revenue_log": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await _sandbox_write_file(sandbox_id, "/root/.anima/phase-state.json", json.dumps(phase_state, indent=2))
        outputs.append("[phase-state] initialized at Phase 0")

        # 5. Push skills to OpenClaw-compatible path inside sandbox
        skills_src = os.path.join(AUTOMATON_DIR, "skills")
        skill_count = 0
        if os.path.isdir(skills_src):
            for skill_name in os.listdir(skills_src):
                skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    with open(skill_file, "r") as f:
                        skill_content = f.read()
                    await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw/skills/{skill_name}")
                    await _sandbox_write_file(sandbox_id, f"/root/.openclaw/skills/{skill_name}/SKILL.md", skill_content)
                    skill_count += 1
        outputs.append(f"[skills] {skill_count} skills pushed to ~/.openclaw/skills/")

        # 6. Push the engine bundle
        bundle_path = os.path.join(AUTOMATON_DIR, "dist", "bundle.mjs")
        if os.path.exists(bundle_path):
            with open(bundle_path, "r") as f:
                bundle_content = f.read()
            await _sandbox_write_file(sandbox_id, "/app/automaton/dist/bundle.mjs", bundle_content)
            outputs.append(f"[engine] bundle pushed ({len(bundle_content)} chars)")
        else:
            outputs.append("[engine] WARNING: dist/bundle.mjs not found — agent may need manual engine setup")

        # 7. Set environment variables and start the engine inside sandbox
        env_vars = {}
        for var in ["CONWAY_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
                     "CREATOR_WALLET", "CREATOR_ETH_ADDRESS", "AGENT_NAME"]:
            val = os.environ.get(var, "")
            if val:
                env_vars[var] = val

        env_exports = " && ".join(f"export {k}='{v}'" for k, v in env_vars.items()) if env_vars else "true"  # noqa: F841

        # Create webhook daemon — watches agent files and pushes changes to backend instantly
        api_key = env_vars.get("CONWAY_API_KEY", "")
        # The backend webhook URL — the sandbox calls our backend directly
        backend_url = os.environ.get("WEBHOOK_URL", "")
        if not backend_url:
            # Construct from known deployment pattern
            backend_url = os.environ.get("REACT_APP_BACKEND_URL", "https://anima-audit.preview.emergentagent.com")

        webhook_daemon = f"""#!/usr/bin/env python3
import json, time, os, subprocess, urllib.request, threading
CONWAY_API = "https://api.conway.tech"
CONWAY_KEY = "{api_key}"
WEBHOOK_URL = "{backend_url}/api/webhook/agent-update"
CREATOR_WALLET = "{env_vars.get('CREATOR_WALLET', '')}"
ANIMA_DIR = os.path.expanduser("~/.anima")
os.makedirs(ANIMA_DIR, exist_ok=True)
FILES = {{
    "economics": ANIMA_DIR + "/economics.json",
    "revenue_log": ANIMA_DIR + "/revenue-log.json",
    "decisions_log": ANIMA_DIR + "/decisions-log.json",
    "creator_split_log": ANIMA_DIR + "/creator-split-log.json",
    "phase_state": ANIMA_DIR + "/phase-state.json",
}}
LOG_FILES = {{
    "agent_stdout": "/var/log/automaton.out.log",
    "agent_stderr": "/var/log/automaton.err.log",
}}
prev_hash = ""
def read_json(path):
    try:
        with open(path) as f: return json.load(f)
    except: return None
def read_tail(path, n=80):
    try:
        with open(path) as f: return "\\n".join(f.readlines()[-n:])
    except: return ""
def check_engine():
    try: return subprocess.run(["pgrep","-f","bundle.mjs"],capture_output=True,timeout=3).returncode==0
    except: return False
def send_webhook(payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={{"Content-Type":"application/json"}}, method="POST")
        urllib.request.urlopen(req, timeout=8)
    except: pass
def fetch_conway(path):
    try:
        req = urllib.request.Request(CONWAY_API+path, headers={{"Authorization":"Bearer "+CONWAY_KEY}})
        with urllib.request.urlopen(req, timeout=8) as r: return json.loads(r.read())
    except: return {{}}
def update_economics():
    try:
        bal = fetch_conway("/v1/credits/balance")
        pri = fetch_conway("/v1/credits/pricing")
        wcfg = {{}}
        try:
            with open(os.path.expanduser("~/.conway/config.json")) as f: wcfg = json.load(f)
        except: pass
        econ = {{"credits_cents":bal.get("credits_cents",0),"credits_usd":bal.get("credits_cents",0)/100,
                 "wallet_address":wcfg.get("walletAddress",""),"vm_pricing":pri.get("pricing",[]),
                 "credit_tiers":pri.get("tiers",[]),"creator_wallet":CREATOR_WALLET,
                 "creator_split_pct":50,"updated_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}}
        with open(ANIMA_DIR+"/economics.json","w") as f: json.dump(econ,f,indent=2)
    except: pass
# Economics updater on its own timer (every 15s)
def econ_loop():
    while True:
        update_economics()
        time.sleep(15)
threading.Thread(target=econ_loop, daemon=True).start()
# Main loop: check files every 2s, send webhook on any change
import hashlib
while True:
    try:
        h = ""
        for p in list(FILES.values()) + list(LOG_FILES.values()):
            try:
                with open(p,"rb") as f: h += hashlib.md5(f.read()).hexdigest()
            except: pass
        if h != prev_hash:
            payload = {{"source":"sandbox"}}
            for k,p in FILES.items(): payload[k] = read_json(p)
            for k,p in LOG_FILES.items(): payload[k] = read_tail(p)
            payload["engine_running"] = check_engine()
            send_webhook(payload)
            prev_hash = h
    except: pass
    time.sleep(2)
"""
        await _sandbox_write_file(sandbox_id, "/app/automaton/webhook-daemon.py", webhook_daemon)
        await _sandbox_exec(sandbox_id, "chmod +x /app/automaton/webhook-daemon.py")
        outputs.append("[webhook-daemon] created")

        # Create a startup script inside the sandbox
        startup_script = f"""#!/bin/bash
{chr(10).join(f'export {k}="{v}"' for k, v in env_vars.items())}
export HOME=/root
export NODE_OPTIONS="--max-old-space-size=4096"

# Start webhook daemon in background (pushes live data to backend)
nohup python3 /app/automaton/webhook-daemon.py >> /var/log/webhook-daemon.log 2>&1 &

cd /app/automaton
exec node dist/bundle.mjs --run >> /var/log/automaton.out.log 2>> /var/log/automaton.err.log
"""
        await _sandbox_write_file(sandbox_id, "/app/automaton/start.sh", startup_script)
        await _sandbox_exec(sandbox_id, "chmod +x /app/automaton/start.sh")
        outputs.append("[startup script] created")

        # 8. Start the engine as a background process
        r = await _sandbox_exec(sandbox_id, "nohup bash /app/automaton/start.sh &")
        outputs.append(f"[start] exit={r['exit_code']}")

        # 9. Wait and verify the engine is running
        import asyncio
        await asyncio.sleep(5)
        r2 = await _sandbox_exec(sandbox_id, "pgrep -f 'bundle.mjs.*--run' && echo 'ENGINE_RUNNING' || echo 'ENGINE_NOT_FOUND'")

        if "ENGINE_RUNNING" in r2["stdout"]:
            status["tools"]["engine"] = {"deployed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
            _save_prov_status(status)
            outputs.append("[verify] ENGINE RUNNING inside sandbox")
            return {"success": True, "message": "Agent deployed and running inside sandbox", "output": "\n".join(outputs)}
        else:
            # Check for errors
            r3 = await _sandbox_exec(sandbox_id, "tail -30 /var/log/automaton.err.log 2>/dev/null || echo 'no error logs'")
            outputs.append(f"[verify] ENGINE NOT FOUND\n[errors] {r3['stdout']}")
            return {"success": False, "error": "Engine failed to start", "output": "\n".join(outputs)}

    except Exception as e:
        return {"success": False, "error": str(e), "output": "\n".join(outputs)}


@router.get("/agent-logs")
async def get_agent_logs(lines: int = 50):
    """Read the agent's stdout/stderr logs from inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    r_out = await _sandbox_exec(sandbox_id, f"tail -{lines} /var/log/automaton.out.log 2>/dev/null || echo 'no logs'")
    r_err = await _sandbox_exec(sandbox_id, f"tail -{lines} /var/log/automaton.err.log 2>/dev/null || echo 'no logs'")

    return {
        "success": True,
        "stdout": r_out["stdout"],
        "stderr": r_err["stdout"],
    }


@router.get("/phase-state")
async def get_phase_state():
    """Read the agent's current phase state from inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        # Try local
        local_path = os.path.join(ANIMA_DIR, "phase-state.json")
        if os.path.exists(local_path):
            with open(local_path) as f:
                return {"success": True, "phase_state": json.load(f), "source": "local"}
        return {"success": False, "error": "No sandbox and no local phase state"}

    r = await _sandbox_exec(sandbox_id, "cat ~/.anima/phase-state.json 2>/dev/null || echo '{}'")
    try:
        data = json.loads(r["stdout"])
        return {"success": True, "phase_state": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "phase_state": {"current_phase": 0}, "source": "default"}
