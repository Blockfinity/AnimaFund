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
CONWAY_DOMAINS_API = "https://api.conway.domains"
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
    """Full provisioning state."""
    status = _load_prov_status()
    credits_cents = 0
    try:
        balance = await _conway_request("GET", "/v1/credits/balance")
        credits_cents = balance.get("credits_cents", 0)
    except Exception:
        pass

    return {
        "sandbox": status["sandbox"],
        "tools": status["tools"],
        "ports": status.get("ports", []),
        "domains": status.get("domains", []),
        "compute_verified": status.get("compute_verified", False),
        "skills_loaded": status["skills_loaded"],
        "nudges": status["nudges"],
        "credits_cents": credits_cents,
        "last_updated": status["last_updated"],
    }


# ═══════════════════════════════════════════════════════════
# 1. SANDBOX (Conway Cloud)
# ═══════════════════════════════════════════════════════════

class CreateSandboxReq(BaseModel):
    name: str = "anima-agent"
    vcpu: int = 2
    memory_mb: int = 4096
    disk_gb: int = 40
    region: str = "us-east"


@router.post("/create-sandbox")
async def create_sandbox(req: CreateSandboxReq = CreateSandboxReq()):
    """Create a Conway Cloud sandbox VM for the agent."""
    status = _load_prov_status()

    if status["sandbox"]["status"] == "active" and status["sandbox"]["id"]:
        return {"success": True, "sandbox_id": status["sandbox"]["id"], "message": "Sandbox already exists"}

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
    _add_nudge(f"Your creator just provisioned a Conway Cloud sandbox VM for you (ID: {sandbox_id}, {req.vcpu} vCPU, {req.memory_mb}MB RAM, {req.disk_gb}GB disk, {req.region}). You now have your own isolated Linux environment.")

    return {"success": True, "sandbox_id": sandbox_id, "sandbox": result}


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
    """Delete the current sandbox. WARNING: Irreversible."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox to delete"}

    result = await _conway_request("DELETE", f"/v1/sandboxes/{sandbox_id}")
    if "error" in result:
        return {"success": False, "error": result["error"]}

    status["sandbox"] = {"status": "none", "id": None, "terminal_url": None, "region": None}
    status["tools"] = {}
    status["ports"] = []
    status["skills_loaded"] = False
    _save_prov_status(status)
    _add_nudge("Your sandbox has been deleted. All tools and data inside it are gone.")

    return {"success": True, "message": "Sandbox deleted"}


# ═══════════════════════════════════════════════════════════
# 2. TOOLS (Install inside sandbox)
# ═══════════════════════════════════════════════════════════

@router.post("/install-terminal")
async def install_terminal():
    """Install Conway Terminal (MCP server) inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # System tools if not done
    if "system" not in status["tools"]:
        r = await _sandbox_exec(sandbox_id, "apt-get update -qq && apt-get install -y -qq curl git wget build-essential jq python3 2>&1 | tail -5")
        outputs.append(f"[system tools] exit={r['exit_code']}")
        if r["exit_code"] == 0:
            status["tools"]["system"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Node.js
    r = await _sandbox_exec(sandbox_id, "command -v node || (curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs) 2>&1 | tail -5")
    outputs.append(f"[node] exit={r['exit_code']}")

    # Conway Terminal
    r = await _sandbox_exec(sandbox_id, "npm install -g conway-terminal 2>&1 | tail -10 && conway-terminal --version")
    outputs.append(f"[conway-terminal] exit={r['exit_code']}\n{r['stdout']}")

    if r["exit_code"] == 0:
        status["tools"]["conway-terminal"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        _save_prov_status(status)
        _add_nudge("Your creator installed conway-terminal in your sandbox. You now have the Conway CLI — manage VMs, run inference, register domains, manage files, and pay with USDC. All via MCP tools.")
        return {"success": True, "output": "\n".join(outputs)}
    else:
        return {"success": False, "error": "Install failed", "output": "\n".join(outputs)}


@router.post("/install-openclaw")
async def install_openclaw():
    """Install OpenClaw (autonomous browser agent) inside the sandbox."""
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []
    r1 = await _sandbox_exec(sandbox_id, "curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tail -10")
    outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")

    r2 = await _sandbox_exec(sandbox_id, "openclaw onboard --install-daemon 2>&1 | tail -5 || true")
    outputs.append(f"[onboard] exit={r2['exit_code']}")

    # Configure MCP to point at conway-terminal
    api_key = _get_conway_api_key()
    mcp_config = json.dumps({"mcpServers": {"conway": {"command": "conway-terminal", "env": {"CONWAY_API_KEY": api_key} if api_key else {}}}}, indent=2)
    await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw && cat > ~/.openclaw/config.json << 'MCPEOF'\n{mcp_config}\nMCPEOF")

    r3 = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'not found'")
    outputs.append(f"[verify] {r3['stdout']}")

    status["tools"]["openclaw"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge("Your creator installed OpenClaw in your sandbox with conway-terminal MCP integration. You can now browse the web, interact with websites, and use all Conway tools autonomously.")

    return {"success": True, "output": "\n".join(outputs)}


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

class DomainSearchReq(BaseModel):
    query: str
    tlds: str = "com,io,ai,xyz,dev"


@router.post("/domain-search")
async def domain_search(req: DomainSearchReq):
    """Search for available domains."""
    # Use the Conway Terminal tool via sandbox exec if available, else direct API
    status = _load_prov_status()
    sandbox_id = status["sandbox"].get("id")

    if sandbox_id and status["tools"].get("conway-terminal", {}).get("installed"):
        # Use conway-terminal inside sandbox for domain search
        r = await _sandbox_exec(sandbox_id, f"conway-terminal domain_search --query '{req.query}' --tlds '{req.tlds}' 2>&1 || echo 'TOOL_FAILED'")
        return {"success": "TOOL_FAILED" not in r["stdout"], "output": r["stdout"], "source": "sandbox"}
    else:
        # Direct API call (SIWE auth may be needed for domains API — use credits API path)
        result = await _conway_request("GET", f"/v1/domains/search?query={req.query}&tlds={req.tlds}")
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "domains": result, "source": "api"}


@router.get("/domain-list")
async def domain_list():
    """List all registered domains."""
    result = await _conway_request("GET", "/v1/domains")
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "domains": result}


class DomainDnsReq(BaseModel):
    domain: str
    record_type: str = "A"
    host: str = "@"
    value: str = ""
    ttl: int = 3600


@router.post("/domain-dns-add")
async def domain_dns_add(req: DomainDnsReq):
    """Add a DNS record to a domain."""
    result = await _conway_request("POST", f"/v1/domains/{req.domain}/dns", {
        "type": req.record_type,
        "host": req.host,
        "value": req.value,
        "ttl": req.ttl,
    })
    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "record": result}


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
    """Push skills from automaton source into the sandbox."""
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
                await _sandbox_write_file(sandbox_id, f"/root/.anima/skills/{skill_name}/SKILL.md", content)
                skill_count += 1
                skill_names.append(skill_name)

    status["skills_loaded"] = True
    status["tools"]["skills"] = {"installed": True, "count": skill_count, "names": skill_names, "timestamp": datetime.now(timezone.utc).isoformat()}
    _save_prov_status(status)
    _add_nudge(f"Your creator loaded {skill_count} skills into your sandbox: {', '.join(skill_names[:10])}{'...' if len(skill_names) > 10 else ''}. Explore them in ~/.anima/skills/")

    return {"success": True, "skill_count": skill_count, "skills": skill_names}


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
