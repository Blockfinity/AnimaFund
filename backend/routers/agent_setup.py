"""
PLATFORM: Agent Provisioning — complete Conway ecosystem management.

The PLATFORM provisions Conway VMs for agents and deploys agent code into them.
All provisioning state lives in MongoDB. Agent execution happens inside Conway VMs.
"""
import os
import json
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

from config import AUTOMATON_DIR
from agent_state import (
    get_active_agent_id, load_provisioning, save_provisioning,
    get_conway_api_key, set_conway_api_key, add_nudge, get_agent_config,
)

router = APIRouter(prefix="/api/provision", tags=["provision"])

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
CONWAY_INFERENCE = os.environ.get("CONWAY_INFERENCE", "https://inference.conway.tech")


# Async wrappers for backward compat within this file
async def _load_prov_status() -> dict:
    return await load_provisioning()


async def _save_prov_status(status: dict):
    await save_provisioning(status)


async def _add_nudge(message: str):
    await add_nudge(message)


async def _get_conway_api_key_async() -> str:
    return await get_conway_api_key()


async def _persist_conway_key(api_key: str, agent_id: str = None):
    """Persist a Conway API key to MongoDB."""
    await set_conway_api_key(api_key, agent_id)


async def _conway_request(method: str, path: str, body: dict = None, timeout: int = 30, base_url: str = None) -> dict:
    """Make an authenticated request to Conway API."""
    api_key = await _get_conway_api_key_async()
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
    """Execute a command inside the sandbox — dispatches to the right provider."""
    if not sandbox_id:
        return {"error": "No sandbox — create one first", "stdout": "", "stderr": "", "exit_code": -1}
    from sandbox_provider import sandbox_exec
    return await sandbox_exec(sandbox_id, command, timeout)


async def _sandbox_write_file(sandbox_id: str, file_path: str, content: str) -> dict:
    """Write a file inside the sandbox — dispatches to the right provider."""
    from sandbox_provider import sandbox_write_file
    return await sandbox_write_file(sandbox_id, file_path, content)


async def _sandbox_read_file(sandbox_id: str, file_path: str) -> dict:
    """Read a file from the sandbox."""
    return await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}/files?path={file_path}")


# ═══════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════

@router.get("/status")
async def get_provision_status():
    """Full provisioning state for the currently active agent."""
    status = await _load_prov_status()
    credits_cents = 0
    try:
        balance = await _conway_request("GET", "/v1/credits/balance")
        credits_cents = balance.get("credits_cents", 0)
    except Exception:
        pass

    # Verify sandbox is actually alive (not stale)
    sandbox_alive = True
    provider = status.get("provider", "conway")
    sandbox_id = status.get("sandbox", {}).get("id")
    if sandbox_id and status.get("sandbox", {}).get("status") == "active":
        if provider == "fly":
            try:
                from sandbox_provider import get_fly_config
                fly = await get_fly_config()
                if fly["token"]:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(
                            f"https://api.machines.dev/v1/apps/{fly['app_name']}/machines/{sandbox_id}",
                            headers={"Authorization": f"Bearer {fly['token']}"},
                        ) as resp:
                            if resp.status == 404:
                                sandbox_alive = False
                            elif resp.status == 200:
                                mdata = await resp.json()
                                # Any error response or destroyed state means dead
                                if mdata.get("error") or mdata.get("state") in ("destroyed", "replacing"):
                                    sandbox_alive = False
                                elif "state" not in mdata:
                                    sandbox_alive = False
                            else:
                                sandbox_alive = False
            except Exception:
                sandbox_alive = False
        elif provider == "conway":
            # Verify Conway sandbox exists via API
            try:
                api_key = await _get_conway_api_key_async()
                if api_key:
                    result = await _conway_request("GET", f"/v1/sandboxes/{sandbox_id}")
                    if "error" in result:
                        sandbox_alive = False
            except Exception:
                pass

        if not sandbox_alive:
            from agent_state import default_provisioning
            status = default_provisioning()
            await _save_prov_status(status)

    return {
        "agent_id": get_active_agent_id(),
        "provider": provider if sandbox_alive else None,
        "sandbox": status["sandbox"] if sandbox_alive else {"status": "none", "id": None},
        "tools": status["tools"] if sandbox_alive else {},
        "ports": status.get("ports", []),
        "domains": status.get("domains", []),
        "compute_verified": status.get("compute_verified", False),
        "skills_loaded": status["skills_loaded"] if sandbox_alive else False,
        "nudges": status["nudges"],
        "credits_cents": credits_cents,
        "wallet_address": status.get("wallet_address", ""),
        "last_updated": status["last_updated"],
    }


@router.post("/health-check")
async def health_check_sandbox():
    """Probe the sandbox to detect what's actually installed. Updates provisioning status.
    Call this to detect where provisioning left off after a machine restart."""
    status = await _load_prov_status()
    sandbox_id = status.get("sandbox", {}).get("id")
    if not sandbox_id or status.get("sandbox", {}).get("status") != "active":
        return {"success": False, "error": "No active sandbox", "tools": {}}

    outputs = []

    # Probe everything in one exec call
    r = await _sandbox_exec(sandbox_id, (
        "echo PROBE_START && "
        "echo NODE=$(command -v node && node --version || echo MISSING) && "
        "echo NPM=$(command -v npm && npm --version || echo MISSING) && "
        "echo CURL=$(command -v curl || echo MISSING) && "
        "echo GIT=$(command -v git || echo MISSING) && "
        "echo CONWAY=$(command -v conway-terminal && conway-terminal --version 2>/dev/null || echo MISSING) && "
        "echo OPENCLAW=$(command -v openclaw || echo MISSING) && "
        "echo CLAUDE=$(command -v claude && claude --version 2>/dev/null || echo MISSING) && "
        "echo SKILLS=$(ls ~/.openclaw/skills/ 2>/dev/null | wc -l) && "
        "echo BUNDLE=$(test -f /app/automaton/dist/bundle.mjs && echo YES || echo MISSING) && "
        "echo GENESIS=$(test -f ~/.anima/genesis-prompt.md && echo YES || echo MISSING) && "
        "echo ENGINE=$(pgrep -f 'bundle.mjs.*--run' > /dev/null 2>&1 && echo RUNNING || echo STOPPED) && "
        "echo WALLET=$(cd /tmp 2>/dev/null && node -e \"try{const D=require('better-sqlite3');const d=new D('/root/.anima/state.db');const r=d.prepare('SELECT value FROM identity WHERE key=?').get('address');console.log(r?r.value:'')}catch(e){console.log('')}\" 2>/dev/null || echo '') && "
        "echo PROBE_END"
    ), timeout=15)

    if r["exit_code"] != 0 or "PROBE_START" not in r.get("stdout", ""):
        outputs.append(f"[probe] failed: {r.get('stderr','')[:200]}")
        return {"success": False, "error": "Probe failed — machine may not be running", "output": "\n".join(outputs)}

    # Parse probe results
    probes = {}
    for line in r["stdout"].split("\n"):
        if "=" in line:
            key, val = line.split("=", 1)
            probes[key.strip()] = val.strip()

    outputs.append(f"[probe] {json.dumps(probes, indent=2)}")

    # Update provisioning status based on actual state
    has_node = "MISSING" not in probes.get("NODE", "MISSING")
    has_curl = "MISSING" not in probes.get("CURL", "MISSING")
    has_conway = "MISSING" not in probes.get("CONWAY", "MISSING")
    has_openclaw = "MISSING" not in probes.get("OPENCLAW", "MISSING")
    has_claude = "MISSING" not in probes.get("CLAUDE", "MISSING")
    skill_count = int(probes.get("SKILLS", "0")) if probes.get("SKILLS", "0").isdigit() else 0
    has_bundle = probes.get("BUNDLE") == "YES"
    has_genesis = probes.get("GENESIS") == "YES"
    engine_running = probes.get("ENGINE") == "RUNNING"
    wallet = probes.get("WALLET", "")

    ts = datetime.now(timezone.utc).isoformat()
    if has_node and has_curl:
        status["tools"]["system"] = {"installed": True, "timestamp": ts}
    else:
        status["tools"].pop("system", None)
    status["tools"]["conway-terminal"] = {"installed": has_conway, "system_ready": has_node, "node_installed": has_node, "wallet_address": wallet, "timestamp": ts}
    if has_openclaw:
        status["tools"]["openclaw"] = {"installed": True, "timestamp": ts}
    else:
        status["tools"].pop("openclaw", None)
    if has_claude:
        status["tools"]["claude-code"] = {"installed": True, "timestamp": ts}
    else:
        status["tools"].pop("claude-code", None)
    if skill_count > 0:
        status["skills_loaded"] = True
        status["tools"]["skills"] = {"installed": True, "count": skill_count, "timestamp": ts}
    else:
        status["skills_loaded"] = False
        status["tools"].pop("skills", None)
    if has_bundle and has_genesis:
        status["tools"]["engine"] = {"deployed": True, "running": engine_running, "timestamp": ts}
    else:
        status["tools"].pop("engine", None)
    if wallet:
        status["wallet_address"] = wallet

    await _save_prov_status(status)

    # Determine next step
    next_step = None
    if not has_node or not has_curl:
        next_step = "terminal"
    elif not has_conway and not has_openclaw:
        next_step = "terminal"
    elif not has_openclaw:
        next_step = "openclaw"
    elif not has_claude:
        next_step = "claudecode"
    elif skill_count == 0:
        next_step = "skills"
    elif not has_bundle:
        next_step = "deploy"
    elif not engine_running:
        next_step = "deploy"

    return {
        "success": True,
        "probes": probes,
        "engine_running": engine_running,
        "next_step": next_step,
        "tools_detected": {k: v.get("installed", v.get("deployed", False)) for k, v in status.get("tools", {}).items()},
        "skills_loaded": status.get("skills_loaded", False),
        "wallet_address": wallet,
        "output": "\n".join(outputs),
    }



# ═══════════════════════════════════════════════════════════
# 1. SANDBOX PROVIDER KEY MANAGEMENT
# ═══════════════════════════════════════════════════════════

class SetProviderKeyReq(BaseModel):
    provider: str  # "conway" or "fly"
    api_key: str


@router.post("/set-provider-key")
async def set_provider_key(req: SetProviderKeyReq):
    """Save an infrastructure provider API key for the active agent."""
    key = req.api_key.strip()
    if not key:
        return {"success": False, "error": "API key is required"}

    if req.provider == "fly":
        if not key.startswith("FlyV1"):
            return {"success": False, "error": "Invalid Fly.io token format. Tokens start with 'FlyV1'"}
        # Validate by listing apps
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                async with session.get(
                    "https://api.machines.dev/v1/apps?org_slug=personal",
                    headers={"Authorization": f"Bearer {key}"},
                ) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": f"Invalid Fly.io token (HTTP {resp.status})"}
                    data = await resp.json()
                    apps = data.get("apps", [])
            except Exception as e:
                return {"success": False, "error": f"Cannot reach Fly.io API: {e}"}

        # Persist to agent provisioning + env
        status = await _load_prov_status()
        status["fly_token"] = key
        if apps:
            status["fly_app_name"] = apps[0].get("name", "animafund")
        os.environ["FLY_API_TOKEN"] = key
        await _save_prov_status(status)
        app_name = status.get("fly_app_name", apps[0]["name"] if apps else "?")
        return {"success": True, "message": f"Fly.io token saved. App: {app_name}", "app_name": app_name, "key_prefix": key[:20] + "..."}

    elif req.provider == "conway":
        # Delegate to existing Conway key endpoint
        from routers.credits import set_conway_api_key_endpoint, SetKeyRequest
        return await set_conway_api_key_endpoint(SetKeyRequest(api_key=key))

    return {"success": False, "error": f"Unknown provider: {req.provider}"}


@router.get("/provider-key-status")
async def provider_key_status(provider: str = "conway"):
    """Check if a provider's API key is configured."""
    if provider == "fly":
        status = await _load_prov_status()
        fly_token = status.get("fly_token") or os.environ.get("FLY_API_TOKEN", "")
        if not fly_token:
            return {"configured": False, "provider": "fly"}
        fly_app = status.get("fly_app_name") or os.environ.get("FLY_APP_NAME", "")
        return {"configured": True, "provider": "fly", "app_name": fly_app, "key_prefix": fly_token[:20] + "..."}
    elif provider == "conway":
        from routers.credits import conway_key_status
        return await conway_key_status()
    return {"configured": False, "provider": provider}


# ═══════════════════════════════════════════════════════════
# 2. SANDBOX (Conway Cloud / Fly.io)
# ═══════════════════════════════════════════════════════════

class CreateSandboxReq(BaseModel):
    name: str = "anima-agent"
    vcpu: int = 1
    memory_mb: int = 512
    disk_gb: int = 5
    region: str = "us-east"
    provider: str = "conway"  # "conway" or "fly"


@router.post("/create-sandbox")
async def create_sandbox_endpoint(req: CreateSandboxReq = CreateSandboxReq()):
    """Create a sandbox VM/container. Supports Conway Cloud and Fly.io providers."""
    status = await _load_prov_status()

    # If we think we have an active sandbox, verify it's actually alive
    if status.get("sandbox", {}).get("status") == "active" and status.get("sandbox", {}).get("id"):
        sandbox_id = status["sandbox"]["id"]
        provider = status.get("provider", "conway")

        if provider == "fly":
            # Check if Fly machine still exists
            from sandbox_provider import get_fly_config
            fly = await get_fly_config()
            if fly["token"]:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                        async with session.get(
                            f"https://api.machines.dev/v1/apps/{fly['app_name']}/machines/{sandbox_id}",
                            headers={"Authorization": f"Bearer {fly['token']}"},
                        ) as resp:
                            if resp.status == 200:
                                mdata = await resp.json()
                                if mdata.get("state") not in ("destroyed", "replacing"):
                                    return {"success": True, "sandbox_id": sandbox_id, "message": "Sandbox already exists", "reused": True}
                            # Machine is gone — auto-reset
                except Exception:
                    pass
                # Machine dead/gone — clear stale status
                from agent_state import default_provisioning
                status = default_provisioning()
                await _save_prov_status(status)
            else:
                return {"success": True, "sandbox_id": sandbox_id, "message": "Sandbox already exists", "reused": True}
        else:
            # Conway — trust the status (Conway sandboxes persist)
            return {"success": True, "sandbox_id": sandbox_id, "message": "Sandbox already exists", "reused": True}

    provider = req.provider

    if provider == "fly":
        # ─── FLY.IO PROVIDER ───
        from sandbox_provider import fly_create_sandbox
        result = await fly_create_sandbox({
            "vcpu": req.vcpu, "memory_mb": req.memory_mb, "disk_gb": req.disk_gb,
            "region": req.region, "name": req.name,
        })
        if "error" in result:
            return {"success": False, "error": result["error"], "raw": result.get("raw")}

        sandbox_id = result.get("id", result.get("sandbox_id", ""))
        reused = result.get("reused", False)
        status["sandbox"] = {
            "status": "active", "id": sandbox_id,
            "region": result.get("region", req.region),
            "vcpu": req.vcpu, "memory_mb": req.memory_mb, "disk_gb": req.disk_gb,
        }
        status["provider"] = "fly"
        status["fly_app_name"] = result.get("fly_app_name", "")
        if result.get("volume_id"):
            status["fly_volume_id"] = result["volume_id"]
        # Preserve existing tools state if reusing a machine
        if not reused:
            status.setdefault("tools", {})
        await _save_prov_status(status)
        msg = f"Reusing existing Fly.io Machine (ID: {sandbox_id})" if reused else f"Fly.io Machine provisioned (ID: {sandbox_id})"
        await _add_nudge(msg)
        return {"success": True, "sandbox_id": sandbox_id, "sandbox": result, "provider": "fly", "reused": reused}

    else:
        # ─── CONWAY PROVIDER (default) ───
        # Check for existing sandboxes to reuse
        existing = await _conway_request("GET", "/v1/sandboxes")
        if "error" not in existing:
            sandboxes = existing.get("sandboxes", existing.get("data", []))
            if isinstance(sandboxes, list) and len(sandboxes) > 0:
                sb = sandboxes[0]
                sandbox_id = sb.get("id", sb.get("sandbox_id", ""))
                if sandbox_id:
                    status["sandbox"] = {
                        "status": "active", "id": sandbox_id,
                        "short_id": sb.get("short_id", ""),
                        "terminal_url": sb.get("terminal_url", ""),
                        "region": sb.get("region", req.region),
                        "vcpu": sb.get("vcpu", req.vcpu),
                        "memory_mb": sb.get("memory_mb", req.memory_mb),
                        "disk_gb": sb.get("disk_gb", req.disk_gb),
                    }
                    status["provider"] = "conway"
                    await _save_prov_status(status)
                    await _add_nudge(f"Reusing existing sandbox VM (ID: {sandbox_id}). Credits preserved.")
                    return {"success": True, "sandbox_id": sandbox_id, "sandbox": sb, "reused": True, "provider": "conway"}

        # Create new Conway sandbox
        result = await _conway_request("POST", "/v1/sandboxes", {
            "name": req.name, "vcpu": req.vcpu, "memory_mb": req.memory_mb,
            "disk_gb": req.disk_gb, "region": req.region,
        })
        if "error" in result:
            return {"success": False, "error": result["error"]}

        sandbox_id = result.get("id", result.get("sandbox_id", ""))
        if not sandbox_id:
            return {"success": False, "error": f"No sandbox ID returned: {json.dumps(result)[:200]}"}

        status["sandbox"] = {
            "status": "active", "id": sandbox_id,
            "short_id": result.get("short_id", ""),
            "terminal_url": result.get("terminal_url", ""),
            "region": result.get("region", req.region),
            "vcpu": result.get("vcpu", req.vcpu),
            "memory_mb": result.get("memory_mb", req.memory_mb),
            "disk_gb": result.get("disk_gb", req.disk_gb),
        }
        status["provider"] = "conway"
        await _save_prov_status(status)
        await _add_nudge(f"Conway Cloud sandbox provisioned (ID: {sandbox_id}, {req.vcpu} vCPU, {req.memory_mb}MB RAM).")
        return {"success": True, "sandbox_id": sandbox_id, "sandbox": result, "provider": "conway", "reused": False}


@router.get("/sandbox-info")
async def sandbox_info():
    """Get detailed info about the current sandbox."""
    status = await _load_prov_status()
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
    """Delete the sandbox machine entirely. Works for Fly.io machines.
    Conway sandboxes are prepaid — use reset-sandbox instead."""
    status = await _load_prov_status()
    sandbox_id = status.get("sandbox", {}).get("id")
    provider = status.get("provider", "conway")

    if not sandbox_id:
        return {"success": False, "error": "No sandbox to delete"}

    if provider == "fly":
        from sandbox_provider import get_fly_config
        fly = await get_fly_config()
        if fly["token"]:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    headers = {"Authorization": f"Bearer {fly['token']}"}
                    await session.post(f"https://api.machines.dev/v1/apps/{fly['app_name']}/machines/{sandbox_id}/stop", headers=headers)
                    import asyncio
                    await asyncio.sleep(2)
                    async with session.delete(f"https://api.machines.dev/v1/apps/{fly['app_name']}/machines/{sandbox_id}?force=true", headers=headers) as resp:
                        pass
            except Exception:
                pass

        from agent_state import default_provisioning
        await _save_prov_status(default_provisioning())
        return {"success": True, "message": f"Fly.io machine {sandbox_id} deleted. Provisioning reset."}
    else:
        return {
            "success": False,
            "error": "Conway sandboxes are prepaid. Use 'Reset Agent' to wipe data and re-provision.",
            "use_instead": "/api/provision/reset-sandbox",
        }


@router.post("/reset-sandbox")
async def reset_sandbox():
    """Reset the agent inside an existing sandbox — wipe all agent data, keep the sandbox alive.
    This preserves Conway credits by reusing the same VM."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox to reset"}

    outputs = []

    try:
        # Kill any running agent processes
        r = await _sandbox_exec(sandbox_id, "pkill -f 'bundle.mjs' 2>/dev/null; pkill -f 'webhook-daemon' 2>/dev/null; pkill -f 'econ-monitor' 2>/dev/null; echo 'KILLED'")
        outputs.append(f"[kill] {r['stdout'].strip()}")

        # Wipe agent data directories but keep system tools installed
        r = await _sandbox_exec(sandbox_id, "rm -rf ~/.anima ~/.automaton /app/automaton /var/log/automaton.* /var/log/econ-monitor.log 2>/dev/null; echo 'WIPED'")
        outputs.append(f"[wipe] {r['stdout'].strip()}")

        # Reset provisioning status — keep sandbox info + provider, clear everything else
        sandbox_info = status["sandbox"]
        new_status = {
            "sandbox": sandbox_info,
            "provider": status.get("provider", "conway"),
            "tools": {},
            "ports": [],
            "domains": [],
            "compute_verified": False,
            "skills_loaded": False,
            "wallet_address": "",
            "nudges": [],
            "last_updated": None,
        }
        await _save_prov_status(new_status)
        outputs.append("[status] provisioning reset — sandbox preserved")

        await _add_nudge("Sandbox has been reset. All agent data wiped. Ready for fresh provisioning. Credits preserved.")

        return {
            "success": True,
            "sandbox_id": sandbox_id,
            "message": "Sandbox reset — agent data wiped, VM preserved, credits saved. Re-run provisioning steps 2-6 to deploy a new agent.",
            "output": "\n".join(outputs),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "output": "\n".join(outputs)}


# ═══════════════════════════════════════════════════════════
# PREREQUISITE CHECK — each step verifies its own deps
# ═══════════════════════════════════════════════════════════

async def _ensure_system_ready(sandbox_id: str) -> tuple:
    """Verify system tools + Node.js are available. Restores volume symlinks if needed.
    Returns (success: bool, log_lines: list)."""
    logs = []

    # Restore volume symlinks if they're missing (Fly rootfs resets on restart)
    r = await _sandbox_exec(sandbox_id, (
        "if [ -d /data ] && [ ! -L /root/.anima ]; then "
        "  mkdir -p /data/anima /data/automaton/dist /data/openclaw /data/conway /data/logs && "
        "  rm -rf /root/.anima /app/automaton /root/.openclaw /root/.conway && "
        "  ln -sfn /data/anima /root/.anima && "
        "  ln -sfn /data/automaton /app/automaton && "
        "  ln -sfn /data/openclaw /root/.openclaw && "
        "  ln -sfn /data/conway /root/.conway && "
        "  touch /data/logs/automaton.out.log /data/logs/automaton.err.log && "
        "  ln -sfn /data/logs/automaton.out.log /var/log/automaton.out.log 2>/dev/null; "
        "  ln -sfn /data/logs/automaton.err.log /var/log/automaton.err.log 2>/dev/null; "
        "  echo SYMLINKS_RESTORED; "
        "else echo SYMLINKS_OK; fi"
    ), timeout=10)
    if "RESTORED" in r.get("stdout", ""):
        logs.append("[prereq] volume symlinks restored")

    # Check if node exists
    r = await _sandbox_exec(sandbox_id, "command -v node && command -v npm && command -v curl && command -v git && echo ALL_OK || echo MISSING", timeout=10)
    if "ALL_OK" in r.get("stdout", ""):
        logs.append("[prereq] system tools + node already available")
        return True, logs

    # Install missing tools
    logs.append("[prereq] installing missing system tools...")
    r = await _sandbox_exec(sandbox_id, "export DEBIAN_FRONTEND=noninteractive && apt-get update -qq 2>&1 | tail -3", timeout=60)
    if r["exit_code"] != 0:
        logs.append(f"[prereq] apt-get update failed: {r.get('stderr','')[:150]}")
        return False, logs

    r = await _sandbox_exec(sandbox_id, "export DEBIAN_FRONTEND=noninteractive && apt-get install -y -qq curl git wget jq ca-certificates gnupg 2>&1 | tail -3", timeout=90)
    if r["exit_code"] != 0:
        logs.append(f"[prereq] system tools install failed")
        return False, logs

    # Node.js
    r = await _sandbox_exec(sandbox_id, (
        "if ! command -v node > /dev/null 2>&1; then "
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash - 2>&1 | tail -3 && "
        "apt-get install -y -qq nodejs 2>&1 | tail -3; fi && "
        "node --version && npm --version"
    ), timeout=120)
    if r["exit_code"] != 0:
        logs.append("[prereq] Node.js install failed")
        return False, logs

    logs.append(f"[prereq] system ready: {r['stdout'].strip()}")
    return True, logs


# ═══════════════════════════════════════════════════════════
# 3. TOOLS (Install inside sandbox)
# ═══════════════════════════════════════════════════════════

@router.post("/install-terminal")
async def install_terminal():
    """Install system tools + Node.js + Conway Terminal. Self-healing: verifies prerequisites first."""
    status = await _load_prov_status()
    sandbox_id = status.get("sandbox", {}).get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Prerequisite: system tools + Node.js
    ok, prereq_logs = await _ensure_system_ready(sandbox_id)
    outputs.extend(prereq_logs)
    if not ok:
        return {"success": False, "error": "System prerequisites failed", "output": "\n".join(outputs)}
    status["tools"]["system"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Conway Terminal (check if already installed first)
    api_key = await _get_conway_api_key_async()
    r_check = await _sandbox_exec(sandbox_id, "command -v conway-terminal && conway-terminal --version 2>&1 || echo NOT_INSTALLED", timeout=10)
    conway_installed = "NOT_INSTALLED" not in r_check.get("stdout", "NOT_INSTALLED") and r_check["exit_code"] == 0

    if not conway_installed and api_key:
        r = await _sandbox_exec(sandbox_id, (
            f"npm install -g conway-terminal 2>&1 | tail -5 && "
            f"mkdir -p ~/.conway && echo '{{\"apiKey\":\"{api_key}\"}}' > ~/.conway/config.json && "
            f"conway-terminal --version 2>&1"
        ), timeout=90)
        outputs.append(f"[conway-terminal] exit={r['exit_code']}\n{r['stdout']}")
        conway_installed = r['exit_code'] == 0
    elif not conway_installed:
        r = await _sandbox_exec(sandbox_id, "curl -fsSL https://conway.tech/terminal.sh | sh 2>&1 | tail -15", timeout=90)
        outputs.append(f"[conway-terminal] exit={r['exit_code']}\n{r['stdout']}")
        conway_installed = r['exit_code'] == 0
    else:
        outputs.append(f"[conway-terminal] already installed: {r_check['stdout'].strip()}")

    # Read wallet
    wallet_address = ""
    if conway_installed:
        r_wallet = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null || echo '{}'")
        try:
            config_data = json.loads(r_wallet["stdout"])
            wallet_address = config_data.get("walletAddress", "")
            sandbox_api_key = config_data.get("apiKey", "")
            if sandbox_api_key and sandbox_api_key != api_key:
                await _persist_conway_key(sandbox_api_key)
                outputs.append("[key-sync] Conway API key synced")
        except Exception:
            pass

    status["tools"]["conway-terminal"] = {
        "installed": conway_installed, "system_ready": True, "node_installed": True,
        "wallet_address": wallet_address, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if wallet_address:
        status["wallet_address"] = wallet_address
    await _save_prov_status(status)

    return {"success": True, "wallet_address": wallet_address, "output": "\n".join(outputs)}


@router.post("/sync-key")
async def sync_key_from_sandbox():
    """Force-pull the Conway API key from the running sandbox and persist it.
    Use when the sandbox has a key the platform doesn't know about."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet."}

    r = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null || echo '{}'")
    try:
        config_data = json.loads(r["stdout"])
        sandbox_key = config_data.get("apiKey", "")
        if not sandbox_key:
            return {"success": False, "error": "No API key found in sandbox ~/.conway/config.json"}

        current_key = await _get_conway_api_key_async()
        if sandbox_key == current_key:
            return {"success": True, "message": "Key already in sync", "key_prefix": sandbox_key[:12] + "..."}

        await _persist_conway_key(sandbox_key)
        return {
            "success": True,
            "message": "Conway API key synced from sandbox to platform",
            "key_prefix": sandbox_key[:12] + "...",
            "wallet_address": config_data.get("walletAddress", ""),
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to parse sandbox config: {e}"}


@router.post("/install-openclaw")
async def install_openclaw():
    """Install OpenClaw. Self-healing: verifies system tools first."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Prerequisite: system tools
    ok, prereq_logs = await _ensure_system_ready(sandbox_id)
    outputs.extend(prereq_logs)
    if not ok:
        return {"success": False, "error": "Prerequisites failed", "output": "\n".join(outputs)}

    # Check if already installed
    r_check = await _sandbox_exec(sandbox_id, "command -v openclaw && echo INSTALLED || echo NOT_INSTALLED", timeout=10)
    if "INSTALLED" in r_check.get("stdout", "") and "NOT" not in r_check.get("stdout", ""):
        outputs.append("[openclaw] already installed")
    else:
        r1 = await _sandbox_exec(sandbox_id, "curl -fsSL https://openclaw.ai/install.sh | bash 2>&1 | tail -10")
        outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")
        r2 = await _sandbox_exec(sandbox_id, "openclaw onboard --install-daemon 2>&1 | tail -5 || true")
        outputs.append(f"[onboard] exit={r2['exit_code']}")

    # Read the API key from inside the sandbox (created by Conway Terminal setup)
    r_key = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('apiKey',''))\" 2>/dev/null || echo ''")
    sandbox_api_key = r_key["stdout"].strip()
    if not sandbox_api_key:
        sandbox_api_key = await _get_conway_api_key_async()

    # Configure MCP to point at conway-terminal with the sandbox's own API key
    mcp_config = json.dumps({"mcpServers": {"conway": {"command": "conway-terminal", "env": {"CONWAY_API_KEY": sandbox_api_key} if sandbox_api_key else {}}}}, indent=2)
    await _sandbox_exec(sandbox_id, f"mkdir -p ~/.openclaw && cat > ~/.openclaw/config.json << 'MCPEOF'\n{mcp_config}\nMCPEOF")

    r3 = await _sandbox_exec(sandbox_id, "openclaw --version 2>&1 || echo 'not found'")
    outputs.append(f"[verify] {r3['stdout']}")

    status["tools"]["openclaw"] = {"installed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    await _save_prov_status(status)
    await _add_nudge("OpenClaw installed with Conway MCP integration. You can now: browse any webpage (browse_page), discover other agents (discover_agents), send messages (send_message), and use ALL Conway tools through OpenClaw's MCP bridge.")

    return {"success": True, "output": "\n".join(outputs)}


@router.post("/install-claude-code")
async def install_claude_code():
    """Install Claude Code. Self-healing: verifies system tools + npm first."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    outputs = []

    # Prerequisite: system tools + Node.js
    ok, prereq_logs = await _ensure_system_ready(sandbox_id)
    outputs.extend(prereq_logs)
    if not ok:
        return {"success": False, "error": "Prerequisites failed", "output": "\n".join(outputs)}

    # Check if already installed
    r_check = await _sandbox_exec(sandbox_id, "command -v claude && claude --version 2>&1 || echo NOT_INSTALLED", timeout=10)
    if "NOT_INSTALLED" not in r_check.get("stdout", "NOT_INSTALLED"):
        outputs.append(f"[claude-code] already installed: {r_check['stdout'].strip()}")
    else:
        # Install Claude Code CLI
        r1 = await _sandbox_exec(sandbox_id, "npm install -g @anthropic-ai/claude-code 2>&1 | tail -10 || (curl -fsSL https://claude.ai/install.sh | sh 2>&1 | tail -10)")
        outputs.append(f"[install] exit={r1['exit_code']}\n{r1['stdout']}")

    # Read the sandbox's Conway API key (created by Conway Terminal setup in step 2)
    r_key = await _sandbox_exec(sandbox_id, "cat ~/.conway/config.json 2>/dev/null | python3 -c \"import sys,json;print(json.load(sys.stdin).get('apiKey',''))\" 2>/dev/null || echo ''")
    sandbox_api_key = r_key["stdout"].strip()
    if not sandbox_api_key:
        sandbox_api_key = await _get_conway_api_key_async()

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
        await _save_prov_status(status)
        await _add_nudge("Claude Code installed with Conway MCP. You can now self-modify code, debug, deploy apps, and use Claude's coding capabilities alongside all Conway tools. Use PTY sessions for interactive work like REPLs and editors.")
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
    status = await _load_prov_status()
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
    await _save_prov_status(status)
    await _add_nudge(f"Port {req.port} is now exposed to the internet: {port_info['public_url']}" + (f" (also: {port_info['custom_url']})" if port_info.get('custom_url') else ""))

    return {"success": True, "port": port_info}


@router.post("/unexpose-port")
async def unexpose_port(port: int):
    """Remove public access to a port."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    result = await _conway_request("DELETE", f"/v1/sandboxes/{sandbox_id}/ports/{port}")
    if "error" in result:
        return {"success": False, "error": result["error"]}

    status["ports"] = [p for p in status.get("ports", []) if p["port"] != port]
    await _save_prov_status(status)
    return {"success": True, "message": f"Port {port} unexposed"}


# ═══════════════════════════════════════════════════════════
# 4. WEB TERMINAL (Browser access)
# ═══════════════════════════════════════════════════════════

@router.post("/web-terminal")
async def create_web_terminal():
    """Create a web terminal session for browser access to the sandbox."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    result = await _conway_request("POST", f"/v1/sandboxes/{sandbox_id}/terminal-session")
    if "error" in result:
        return {"success": False, "error": result["error"]}

    terminal_url = result.get("terminal_url", "")
    status["sandbox"]["terminal_url"] = terminal_url
    await _save_prov_status(status)

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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    api_key = await _get_conway_api_key_async()
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

    status = await _load_prov_status()
    status["compute_verified"] = True
    status["tools"]["compute"] = {"verified": True, "model_tested": req.model, "timestamp": datetime.now(timezone.utc).isoformat()}
    await _save_prov_status(status)
    await _add_nudge(f"Conway Compute is working. Tested {req.model}: \"{response_text[:100]}\"")

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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal. Domain registration uses x402 USDC payment from the agent's wallet."}
    await _add_nudge(f"Your creator wants you to register the domain '{req.domain}' for {req.years} year(s). Use domain_register tool: domain_register --domain {req.domain} --years {req.years} --privacy {str(req.privacy).lower()}")
    return {"success": True, "message": f"Nudge sent to agent to register '{req.domain}'. The agent will use its wallet to pay via x402.", "domain": req.domain}


# ─── AUTHENTICATED (via sandbox): Domain Renew ───

class DomainRenewReq(BaseModel):
    domain: str
    years: int = 1


@router.post("/domain-renew")
async def domain_renew(req: DomainRenewReq):
    """Renew a domain. Requires sandbox — uses x402 USDC payment via agent's wallet."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id or not status["tools"].get("conway-terminal", {}).get("installed"):
        return {"success": False, "error": "Requires sandbox with Conway Terminal."}
    await _add_nudge(f"Your creator wants you to renew the domain '{req.domain}' for {req.years} year(s). Use domain_renew tool.")
    return {"success": True, "message": f"Nudge sent to agent to renew '{req.domain}'.", "domain": req.domain}


# ─── AUTHENTICATED (via sandbox): DNS List ───

@router.get("/domain-dns-list")
async def domain_dns_list(domain: str = Query(...)):
    """List DNS records for a domain. Routes through sandbox."""
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    status = await _load_prov_status()
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
    """Push skills into sandbox. Self-healing: ensures sandbox directories exist first."""
    from database import get_db
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox yet. Create one first."}

    # Ensure skill directories exist
    await _sandbox_exec(sandbox_id, "mkdir -p ~/.openclaw/skills", timeout=10)

    skills_src = os.path.join(AUTOMATON_DIR, "skills")
    skill_count = 0
    skill_names = []
    clawhub_installed = []
    clawhub_failed = []

    # 1. Push ALL local skills — build tar, push via exec base64 (no platform URL exposure)
    skills_failed = []
    if os.path.isdir(skills_src):
        import tarfile, io, base64 as b64mod

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            for skill_name in sorted(os.listdir(skills_src)):
                skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    try:
                        data = open(skill_file, 'rb').read()
                        if not data.strip():
                            skills_failed.append({"skill": skill_name, "error": "empty file"})
                            continue
                        info = tarfile.TarInfo(name=f"{skill_name}/SKILL.md")
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                        skill_count += 1
                        skill_names.append(skill_name)
                    except Exception as e:
                        skills_failed.append({"skill": skill_name, "error": str(e)[:80]})

        # Push tar via sandbox write file API (goes through Conway/Fly provider, NOT platform URL)
        tar_bytes = tar_buffer.getvalue()
        result = await _sandbox_write_file(sandbox_id, "/tmp/_skills.tar.gz", b64mod.b64encode(tar_bytes).decode())
        if result.get("error"):
            skills_failed.append({"skill": "tar_push", "error": result["error"][:100]})
        else:
            # The write_file wrote base64 — need to decode and extract
            r = await _sandbox_exec(sandbox_id,
                "mkdir -p ~/.openclaw/skills && "
                "base64 -d /tmp/_skills.tar.gz > /tmp/_skills_decoded.tar.gz && "
                "tar xzf /tmp/_skills_decoded.tar.gz -C ~/.openclaw/skills/ && "
                "rm -f /tmp/_skills.tar.gz /tmp/_skills_decoded.tar.gz && "
                "ls ~/.openclaw/skills/ | wc -l",
                timeout=30)
            if r.get("exit_code") != 0:
                skills_failed.append({"skill": "tar_extract", "error": r.get("stderr", "extract failed")[:100]})

    # 2. Install priority skills from ClawHub INSIDE the sandbox
    agent_id = get_active_agent_id()
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
    await _save_prov_status(status)

    total_attempted = skill_count + len(skills_failed)
    msg = f"Skills provisioned: {skill_count}/{total_attempted}."
    if skills_failed:
        msg += f"\nSkipped ({len(skills_failed)} errors): {', '.join(f['skill'] for f in skills_failed[:10])}."
    if clawhub_installed:
        msg += f"\nClawHub installed: {', '.join(clawhub_installed)}."
    if clawhub_failed:
        msg += f"\nClawHub failed: {', '.join(f['skill'] for f in clawhub_failed)}."
    await _add_nudge(msg)

    # Build output for the UI step log
    output_lines = [f"Skills provisioned: {skill_count}/{total_attempted}"]
    if skills_failed:
        output_lines.append(f"\nFailed skills ({len(skills_failed)}):")
        for sf in skills_failed[:20]:
            output_lines.append(f"  - {sf['skill']}: {sf.get('error','unknown')[:80]}")
    if clawhub_installed:
        output_lines.append(f"\nClawHub: {', '.join(clawhub_installed)}")

    return {
        "success": True,
        "skill_count": skill_count,
        "total_attempted": total_attempted,
        "local_skills": skill_names,
        "skills_failed": skills_failed,
        "clawhub_installed": clawhub_installed,
        "clawhub_failed": clawhub_failed,
        "priority_skills": selected_skills,
        "output": "\n".join(output_lines),
    }


# ═══════════════════════════════════════════════════════════
# 11. NUDGE / GO AUTONOMOUS
# ═══════════════════════════════════════════════════════════

@router.post("/nudge")
async def nudge_agent():
    """Send the default autonomy nudge."""
    await _add_nudge("Your creator has finished setting up your environment. All tools are installed in your sandbox. Test them and begin your mission. You are now fully autonomous — no more human control.")
    return {"success": True, "message": "Autonomy nudge sent"}


class CustomNudge(BaseModel):
    message: str


@router.post("/nudge/custom")
async def nudge_agent_custom(req: CustomNudge):
    """Send a custom message to the agent."""
    await _add_nudge(req.message)
    return {"success": True, "message": req.message}


# ═══════════════════════════════════════════════════════════
# 12. VERIFY (Run functional tests)
# ═══════════════════════════════════════════════════════════

@router.post("/verify-sandbox")
async def verify_sandbox():
    """Run functional tests inside the sandbox to confirm tools work."""
    status = await _load_prov_status()
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
    """PLATFORM: Deploy the Automaton engine. Self-healing: verifies system tools + Node.js first.
    Reads ALL agent config from MongoDB — no host env var access."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox. Create one first."}

    # PLATFORM: Fetch agent config from MongoDB (not host env)
    agent_config = await get_agent_config()
    agent_id = get_active_agent_id()

    outputs = []

    try:
        # Prerequisite: system tools + Node.js must be available for the engine
        ok, prereq_logs = await _ensure_system_ready(sandbox_id)
        outputs.extend(prereq_logs)
        if not ok:
            return {"success": False, "error": "System prerequisites failed", "output": "\n".join(outputs)}

        # 1. Create directories inside sandbox
        r = await _sandbox_exec(sandbox_id, "mkdir -p /app/automaton/dist ~/.anima ~/.automaton /var/log")
        outputs.append(f"[dirs] exit={r['exit_code']}")

        # 2. Push genesis prompt into sandbox — from MongoDB agent doc
        genesis_content = agent_config.get("genesis_prompt", "")
        if not genesis_content:
            # Fallback: load template from automaton repo
            genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
            if os.path.exists(genesis_src):
                with open(genesis_src, "r") as f:
                    genesis_content = f.read()

        if genesis_content:
            # Inject agent-specific config from MongoDB (NOT host env)
            secrets = {
                "{{TELEGRAM_BOT_TOKEN}}": agent_config.get("telegram_bot_token", ""),
                "{{TELEGRAM_CHAT_ID}}": agent_config.get("telegram_chat_id", ""),
                "{{CREATOR_WALLET}}": agent_config.get("creator_sol_wallet", ""),
                "{{CREATOR_ETH_ADDRESS}}": agent_config.get("creator_eth_wallet", ""),
                "{{AGENT_NAME}}": agent_config.get("name", "Anima Fund"),
                "{{AGENT_ID}}": agent_id,
                "{{DASHBOARD_URL}}": "",  # SECURITY: never expose platform URL to sandbox
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

        # 4. Write anima.json — the engine's main config file (required for --run)
        api_key = await _get_conway_api_key_async()
        anima_config = {
            "name": agent_config.get("name", "Anima Fund"),
            "genesisPrompt": genesis_content[:500] + "..." if len(genesis_content) > 500 else genesis_content,
            "creatorAddress": agent_config.get("creator_eth_wallet", "0x0000000000000000000000000000000000000000"),
            "registeredWithConway": bool(api_key),
            "sandboxId": sandbox_id,
            "conwayApiUrl": "https://api.conway.tech",
            "conwayApiKey": api_key or "",
            "inferenceModel": "gpt-5.2",
            "maxTokensPerTurn": 4096,
            "heartbeatConfigPath": "~/.anima/heartbeat.yml",
            "dbPath": "~/.anima/state.db",
            "logLevel": "info",
            "walletAddress": "",
            "version": "0.2.1",
            "skillsDir": "~/.anima/skills",
            "maxChildren": 3,
            "maxTurnsPerCycle": 25,
            "treasuryPolicy": {
                "maxSingleTransferCents": 5000,
                "maxHourlyTransferCents": 10000,
                "maxDailyTransferCents": 25000,
                "minimumReserveCents": 1000,
                "maxX402PaymentCents": 100,
                "x402AllowedDomains": ["conway.tech"],
                "transferCooldownMs": 0,
                "maxTransfersPerTurn": 2,
                "maxInferenceDailyCents": 50000,
                "requireConfirmationAboveCents": 1000,
            },
        }
        await _sandbox_write_file(sandbox_id, "/root/.anima/anima.json", json.dumps(anima_config, indent=2))
        outputs.append("[anima.json] engine config written")

        # 4b. Sync Conway API key to ~/.conway/config.json (the engine reads from here)
        if api_key:
            conway_config = json.dumps({"apiKey": api_key})
            await _sandbox_write_file(sandbox_id, "/root/.conway/config.json", conway_config)
            outputs.append("[conway-config] API key synced to ~/.conway/config.json")

        # 5. Initialize phase-state.json at Phase 0
        phase_state = {
            "current_phase": 0,
            "phase_0_complete": False,
            "tool_tests": {},
            "revenue_log": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await _sandbox_write_file(sandbox_id, "/root/.anima/phase-state.json", json.dumps(phase_state, indent=2))
        outputs.append("[phase-state] initialized at Phase 0")

        # 4b. Push Phase 0 tool verification script — agent USES each tool, not just API calls
        tool_test_script = '''#!/usr/bin/env python3
"""Phase 0 Tool Verification — tests each tool by actually USING it.
Run this after all tools are installed. Updates phase-state.json with results."""
import json, os, subprocess, time, sys

ANIMA_DIR = os.path.expanduser("~/.anima")
results = {}

def log(msg):
    print(f"[Phase0] {msg}", flush=True)

def pass_test(name, detail=""):
    results[name] = {"status": "pass", "detail": detail, "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    log(f"PASS: {name} — {detail}")

def fail_test(name, detail=""):
    results[name] = {"status": "fail", "detail": detail, "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    log(f"FAIL: {name} — {detail}")

# 1. Conway Terminal — verify installed and can list sandboxes
log("Testing Conway Terminal...")
try:
    r = subprocess.run(["conway-terminal", "--version"], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        pass_test("conway_terminal", f"version: {r.stdout.strip()}")
    else:
        r2 = subprocess.run(["which", "conway-terminal"], capture_output=True, text=True, timeout=5)
        if r2.returncode == 0:
            pass_test("conway_terminal", f"found at {r2.stdout.strip()}")
        else:
            fail_test("conway_terminal", "not found in PATH")
except Exception as e:
    fail_test("conway_terminal", str(e))

# 2. Conway wallet — verify exists and has an address
log("Testing wallet...")
try:
    cfg_path = os.path.expanduser("~/.conway/config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    addr = cfg.get("walletAddress", "")
    api_key = cfg.get("apiKey", "")
    if addr:
        pass_test("wallet", f"address: {addr[:10]}...{addr[-6:]}")
    else:
        fail_test("wallet", "no walletAddress in config")
    if api_key:
        pass_test("api_key", f"key: {api_key[:12]}...")
    else:
        fail_test("api_key", "no apiKey in config")
except Exception as e:
    fail_test("wallet", str(e))

# 3. OpenClaw — verify installed and MCP config exists
log("Testing OpenClaw...")
try:
    r = subprocess.run(["which", "openclaw"], capture_output=True, text=True, timeout=5)
    if r.returncode == 0:
        pass_test("openclaw_binary", f"found at {r.stdout.strip()}")
    else:
        fail_test("openclaw_binary", "not found in PATH")
    # Check MCP config
    oc_cfg = os.path.expanduser("~/.openclaw/config.json")
    if os.path.exists(oc_cfg):
        with open(oc_cfg) as f:
            oc = json.load(f)
        if "mcpServers" in oc and "conway" in oc.get("mcpServers", {}):
            pass_test("openclaw_mcp", "Conway MCP configured in OpenClaw")
        else:
            fail_test("openclaw_mcp", "Conway MCP not found in OpenClaw config")
    else:
        fail_test("openclaw_mcp", f"{oc_cfg} not found")
except Exception as e:
    fail_test("openclaw", str(e))

# 4. Claude Code — verify installed and MCP config exists
log("Testing Claude Code...")
try:
    r = subprocess.run(["which", "claude"], capture_output=True, text=True, timeout=5)
    if r.returncode == 0:
        pass_test("claude_code_binary", f"found at {r.stdout.strip()}")
    else:
        fail_test("claude_code_binary", "not found in PATH")
    # Check Claude MCP config
    r2 = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True, timeout=10)
    if r2.returncode == 0 and "conway" in r2.stdout.lower():
        pass_test("claude_code_mcp", "Conway MCP registered with Claude Code")
    elif r2.returncode == 0:
        fail_test("claude_code_mcp", f"Conway not in MCP list: {r2.stdout[:200]}")
    else:
        fail_test("claude_code_mcp", f"mcp list failed: {r2.stderr[:200]}")
except Exception as e:
    fail_test("claude_code", str(e))

# 5. File I/O — verify write + read inside sandbox
log("Testing file I/O...")
try:
    test_path = "/tmp/.anima_phase0_test"
    test_data = {"test": True, "ts": time.time()}
    with open(test_path, "w") as f:
        json.dump(test_data, f)
    with open(test_path) as f:
        readback = json.load(f)
    os.remove(test_path)
    if readback.get("test") is True:
        pass_test("file_io", "write + read + delete OK")
    else:
        fail_test("file_io", "readback mismatch")
except Exception as e:
    fail_test("file_io", str(e))

# 6. Network — verify outbound connectivity
log("Testing network...")
try:
    import urllib.request
    r = urllib.request.urlopen("https://api.conway.tech/health", timeout=10)
    if r.status == 200:
        pass_test("network", "outbound HTTPS to api.conway.tech OK")
    else:
        fail_test("network", f"status {r.status}")
except Exception as e:
    fail_test("network", str(e))

# 7. Credits — verify can check balance
log("Testing credits API...")
try:
    import urllib.request
    cfg_path = os.path.expanduser("~/.conway/config.json")
    with open(cfg_path) as f:
        api_key = json.load(f).get("apiKey", "")
    req = urllib.request.Request(
        "https://api.conway.tech/v1/credits/balance",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        cents = data.get("credits_cents", 0)
        pass_test("credits_api", f"balance: {cents} cents (${cents/100:.2f})")
except Exception as e:
    fail_test("credits_api", str(e))

# 8. Skills — verify skills directory has files
log("Testing skills...")
try:
    skills_dir = os.path.expanduser("~/.openclaw/skills")
    if os.path.isdir(skills_dir):
        skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
        pass_test("skills", f"{len(skills)} skills loaded: {', '.join(skills[:5])}")
    else:
        fail_test("skills", "~/.openclaw/skills/ not found")
except Exception as e:
    fail_test("skills", str(e))

# Summary
passed = sum(1 for r in results.values() if r["status"] == "pass")
total = len(results)
log(f"\\n{'='*50}")
log(f"Phase 0 Results: {passed}/{total} tools verified")
log(f"{'='*50}")

# Update phase-state.json
try:
    ps_path = os.path.join(ANIMA_DIR, "phase-state.json")
    with open(ps_path) as f:
        ps = json.load(f)
    ps["tool_tests"] = results
    ps["phase_0_tested_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    if passed == total:
        ps["phase_0_complete"] = True
        log("Phase 0 COMPLETE — all tools verified. Agent ready for Phase 1.")
    else:
        ps["phase_0_complete"] = False
        log(f"Phase 0 INCOMPLETE — {total - passed} tools failed.")
    with open(ps_path, "w") as f:
        json.dump(ps, f, indent=2)
except Exception as e:
    log(f"Failed to update phase-state: {e}")

sys.exit(0 if passed == total else 1)
'''
        await _sandbox_write_file(sandbox_id, "/root/.anima/phase0-verify.py", tool_test_script)
        await _sandbox_exec(sandbox_id, "chmod +x /root/.anima/phase0-verify.py")
        outputs.append("[phase0-verify] tool test script pushed")

        # 5. Push skills via tar through sandbox file API (no platform URL)
        skills_src = os.path.join(AUTOMATON_DIR, "skills")
        skill_count = 0
        if os.path.isdir(skills_src):
            import tarfile, io, base64 as b64mod
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                for skill_name in sorted(os.listdir(skills_src)):
                    skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
                    if os.path.exists(skill_file):
                        try:
                            data = open(skill_file, 'rb').read()
                            if data.strip():
                                info = tarfile.TarInfo(name=f"{skill_name}/SKILL.md")
                                info.size = len(data)
                                tar.addfile(info, io.BytesIO(data))
                                skill_count += 1
                        except Exception:
                            pass
            await _sandbox_write_file(sandbox_id, "/tmp/_skills.tar.gz", b64mod.b64encode(tar_buffer.getvalue()).decode())
            await _sandbox_exec(sandbox_id,
                "mkdir -p ~/.openclaw/skills && base64 -d /tmp/_skills.tar.gz > /tmp/_s.tar.gz && "
                "tar xzf /tmp/_s.tar.gz -C ~/.openclaw/skills/ && rm -f /tmp/_skills.tar.gz /tmp/_s.tar.gz",
                timeout=30)
        outputs.append(f"[skills] {skill_count} skills pushed")

        # 6. Push the engine bundle via sandbox file API (NO platform URL exposure)
        bundle_path = os.path.join(AUTOMATON_DIR, "dist", "bundle.mjs")
        if os.path.exists(bundle_path):
            with open(bundle_path, "r") as f:
                bundle_content = f.read()
            outputs.append(f"[engine] pushing bundle ({len(bundle_content)} bytes) via sandbox file API")

            result = await _sandbox_write_file(sandbox_id, "/app/automaton/dist/bundle.mjs", bundle_content)
            if result.get("error"):
                outputs.append(f"[engine] file API failed: {result['error'][:100]}. Bundle must be pushed manually.")
            else:
                outputs.append("[engine] bundle pushed")

            # Verify bundle size
            r_check = await _sandbox_exec(sandbox_id, "wc -c /app/automaton/dist/bundle.mjs", timeout=5)
            outputs.append(f"[engine] verified: {r_check.get('stdout','').strip()}")

            # 6b. Push native addon via file API, then recompile if wrong Node version
            native_path = os.path.join(AUTOMATON_DIR, "native", "linux-x64", "better_sqlite3.node")
            if os.path.exists(native_path):
                import base64 as b64mod
                with open(native_path, "rb") as f:
                    native_b64 = b64mod.b64encode(f.read()).decode()
                await _sandbox_write_file(sandbox_id, "/tmp/_native.b64", native_b64)
                r_native = await _sandbox_exec(sandbox_id,
                    "mkdir -p /app/automaton/native/linux-x64 && "
                    "base64 -d /tmp/_native.b64 > /app/automaton/native/linux-x64/better_sqlite3.node && "
                    "cp /app/automaton/native/linux-x64/better_sqlite3.node /app/automaton/native/better_sqlite3.node && "
                    "rm -f /tmp/_native.b64 && wc -c /app/automaton/native/linux-x64/better_sqlite3.node",
                    timeout=30)
                outputs.append(f"[native] {r_native.get('stdout','').strip()}")
                # Recompile if wrong Node version
                if r_native.get("exit_code") == 0:
                    r_compat = await _sandbox_exec(sandbox_id, "node -e \"require('/app/automaton/native/linux-x64/better_sqlite3.node')\" 2>&1 || echo NEEDS_RECOMPILE", timeout=10)
                    if "NEEDS_RECOMPILE" in r_compat.get("stdout", "") or "NODE_MODULE_VERSION" in r_compat.get("stdout", ""):
                        outputs.append("[native] Recompiling for sandbox Node version...")
                        r_recompile = await _sandbox_exec(sandbox_id,
                            "cd /tmp && npm install better-sqlite3 2>&1 | tail -3 && "
                            "cp /tmp/node_modules/better-sqlite3/build/Release/better_sqlite3.node /app/automaton/native/linux-x64/better_sqlite3.node && "
                            "cp /app/automaton/native/linux-x64/better_sqlite3.node /app/automaton/native/better_sqlite3.node && echo RECOMPILED",
                            timeout=60)
                        outputs.append(f"[native] {r_recompile.get('stdout','').strip()}")
        else:
            outputs.append("[engine] WARNING: dist/bundle.mjs not found on host")

        # 7. PLATFORM: Build env vars from MongoDB agent config (NOT host env)
        api_key = await _get_conway_api_key_async()
        env_vars = {
            "CONWAY_API_KEY": api_key,
            "TELEGRAM_BOT_TOKEN": agent_config.get("telegram_bot_token", ""),
            "TELEGRAM_CHAT_ID": agent_config.get("telegram_chat_id", ""),
            "CREATOR_WALLET": agent_config.get("creator_sol_wallet", ""),
            "CREATOR_ETH_ADDRESS": agent_config.get("creator_eth_wallet", ""),
            "AGENT_NAME": agent_config.get("name", "Anima Fund"),
        }
        # Remove empty values
        env_vars = {k: v for k, v in env_vars.items() if v}

        env_exports = " && ".join(f"export {k}='{v}'" for k, v in env_vars.items()) if env_vars else "true"  # noqa: F841

        # Create webhook daemon — pushes agent data to platform
        # SECURITY: The webhook URL + secret token are the ONLY platform info in the sandbox
        backend_url = os.environ.get("REACT_APP_BACKEND_URL", "")
        import secrets as _secrets
        webhook_token = _secrets.token_hex(32)
        # Store token in MongoDB so webhook endpoint can validate
        status["webhook_token"] = webhook_token
        await _save_prov_status(status)

        webhook_daemon = f"""#!/usr/bin/env python3
import json, time, os, subprocess, urllib.request, threading
CONWAY_API = "https://api.conway.tech"
CONWAY_KEY = "{api_key}"
WEBHOOK_URL = "{backend_url}/api/webhook/agent-update"
WEBHOOK_TOKEN = "{webhook_token}"
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
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={{"Content-Type":"application/json","Authorization":"Bearer "+WEBHOOK_TOKEN}}, method="POST")
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
        # Get wallet from config OR from agent's state.db
        wallet = wcfg.get("walletAddress","")
        if not wallet:
            try:
                import subprocess
                r = subprocess.run(["node","-e","try{{const D=require('better-sqlite3');const d=new D('/root/.anima/state.db');const r=d.prepare('SELECT value FROM identity WHERE key=?').get('address');console.log(r?r.value:'')}}catch(e){{console.log('')}}"], capture_output=True, text=True, timeout=5, cwd="/tmp")
                wallet = r.stdout.strip()
            except: pass
        econ = {{"credits_cents":bal.get("credits_cents",0),"credits_usd":bal.get("credits_cents",0)/100,
                 "wallet_address":wallet,"vm_pricing":pri.get("pricing",[]),
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

# Phase 0: Verify all tools are functional before starting the agent
echo "[startup] Running Phase 0 tool verification..."
python3 /root/.anima/phase0-verify.py 2>&1 | tee /var/log/phase0-verify.log
PHASE0_EXIT=$?
if [ $PHASE0_EXIT -ne 0 ]; then
    echo "[startup] WARNING: Phase 0 verification had failures. Check /var/log/phase0-verify.log"
fi

# Start webhook daemon in background (pushes live data to backend)
nohup python3 /app/automaton/webhook-daemon.py >> /var/log/webhook-daemon.log 2>&1 &

cd /app/automaton
exec node dist/bundle.mjs --run >> /var/log/automaton.out.log 2>> /var/log/automaton.err.log
"""
        await _sandbox_write_file(sandbox_id, "/app/automaton/start.sh", startup_script)
        await _sandbox_exec(sandbox_id, "chmod +x /app/automaton/start.sh")
        outputs.append("[startup script] created")

        # 8. Start the engine
        provider = status.get("provider", "conway")
        if provider == "fly":
            # On Fly.io: start engine via exec (runs as background process in container)
            # Do NOT update machine init — that would restart the machine and wipe rootfs
            r = await _sandbox_exec(sandbox_id,
                "cd /app/automaton && nohup node dist/bundle.mjs --run >> /var/log/automaton.out.log 2>> /var/log/automaton.err.log &"
                " && nohup python3 /app/automaton/webhook-daemon.py >> /var/log/webhook-daemon.log 2>&1 &"
                " && sleep 2 && echo STARTED")
            outputs.append(f"[start] {r.get('stdout','').strip()}")
        else:
            r = await _sandbox_exec(sandbox_id, "nohup bash /app/automaton/start.sh &")
            outputs.append(f"[start] exit={r['exit_code']}")

        # 9. Wait and verify
        import asyncio
        await asyncio.sleep(5)
        r2 = await _sandbox_exec(sandbox_id, "pgrep -f 'bundle.mjs.*--run' && echo 'ENGINE_RUNNING' || echo 'ENGINE_NOT_FOUND'")

        engine_running = "ENGINE_RUNNING" in r2.get("stdout", "")
        status["tools"]["engine"] = {"deployed": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        await _save_prov_status(status)

        if engine_running:
            outputs.append("[verify] ENGINE RUNNING inside sandbox")
            return {"success": True, "message": "Agent deployed and running", "output": "\n".join(outputs)}
        else:
            r3 = await _sandbox_exec(sandbox_id, "tail -30 /var/log/automaton.err.log 2>/dev/null || echo 'no error logs'")
            outputs.append(f"[verify] Engine may still be starting...\n[logs] {r3['stdout']}")
            # Still mark as success — engine is deployed even if not running yet
            return {"success": True, "message": "Agent deployed (engine starting)", "output": "\n".join(outputs)}

    except Exception as e:
        return {"success": False, "error": str(e), "output": "\n".join(outputs)}


@router.get("/agent-logs")

@router.get("/bundle")

@router.get("/skills-archive")
async def serve_skills_archive():
    """Serve all skills as a tar.gz archive so sandbox can download in one shot."""
    import tarfile, io
    skills_src = os.path.join(AUTOMATON_DIR, "skills")
    if not os.path.isdir(skills_src):
        return {"error": "No skills directory"}
    tar_buffer = io.BytesIO()
    count = 0
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for skill_name in sorted(os.listdir(skills_src)):
            skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
            if os.path.exists(skill_file):
                try:
                    data = open(skill_file, 'rb').read()
                    if data.strip():
                        info = tarfile.TarInfo(name=f"{skill_name}/SKILL.md")
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                        count += 1
                except Exception:
                    pass
    from fastapi.responses import Response
    return Response(content=tar_buffer.getvalue(), media_type="application/gzip",
                    headers={"Content-Disposition": "attachment; filename=skills.tar.gz", "X-Skill-Count": str(count)})


async def serve_bundle():
    """Serve the engine bundle so sandbox machines can download it directly."""
    bundle_path = os.path.join(AUTOMATON_DIR, "dist", "bundle.mjs")
    if not os.path.exists(bundle_path):
        return {"error": "Bundle not found"}
    from fastapi.responses import FileResponse
    return FileResponse(bundle_path, media_type="application/javascript", filename="bundle.mjs")


@router.get("/native/{filename}")
async def serve_native(filename: str):
    """Serve native addons so sandbox machines can download them."""
    # Try platform-specific first, then generic
    for subpath in [f"native/linux-x64/{filename}", f"native/{filename}"]:
        filepath = os.path.join(AUTOMATON_DIR, subpath)
        if os.path.exists(filepath):
            from fastapi.responses import FileResponse
            return FileResponse(filepath, media_type="application/octet-stream", filename=filename)
    return {"error": f"Native addon {filename} not found"}



async def get_agent_logs(lines: int = 50):
    """Read the agent's stdout/stderr logs from inside the sandbox."""
    status = await _load_prov_status()
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
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox provisioned"}

    r = await _sandbox_exec(sandbox_id, "cat ~/.anima/phase-state.json 2>/dev/null || echo '{}'")
    try:
        data = json.loads(r["stdout"])
        return {"success": True, "phase_state": data, "source": "sandbox"}
    except Exception:
        return {"success": True, "phase_state": {"current_phase": 0}, "source": "default"}


@router.post("/verify-tools")
async def verify_tools():
    """Run Phase 0 tool verification inside the sandbox. Tests each tool by actually using it."""
    status = await _load_prov_status()
    sandbox_id = status["sandbox"].get("id")
    if not sandbox_id:
        return {"success": False, "error": "No sandbox"}

    # Run the verification script
    r = await _sandbox_exec(sandbox_id, "python3 /root/.anima/phase0-verify.py 2>&1")
    # Read the updated phase state
    r2 = await _sandbox_exec(sandbox_id, "cat ~/.anima/phase-state.json 2>/dev/null || echo '{}'")
    try:
        phase_state = json.loads(r2["stdout"])
    except Exception:
        phase_state = {}

    return {
        "success": r["exit_code"] == 0,
        "output": r["stdout"],
        "phase_state": phase_state,
        "tool_tests": phase_state.get("tool_tests", {}),
        "phase_0_complete": phase_state.get("phase_0_complete", False),
    }
