"""
PLATFORM: Sandbox Provider — abstraction layer for VM/container providers.
Supports: Conway Cloud, Fly.io. Each provider implements the same interface.
The provisioning steps work identically regardless of provider.
"""
import os
import json
import aiohttp
import logging
from datetime import datetime, timezone

from agent_state import get_active_agent_id, load_provisioning, save_provisioning, get_conway_api_key

logger = logging.getLogger("sandbox_provider")

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
FLY_API = "https://api.machines.dev"


# ═══════════════════════════════════════════════════════════
# PROVIDER CONFIG — read from agent provisioning state
# ═══════════════════════════════════════════════════════════

async def get_fly_config(agent_id: str = None) -> dict:
    prov = await load_provisioning(agent_id)
    return {
        "token": prov.get("fly_token") or os.environ.get("FLY_API_TOKEN", ""),
        "app_name": prov.get("fly_app_name") or os.environ.get("FLY_APP_NAME", "animafund"),
        "machine_id": prov.get("sandbox", {}).get("id", ""),
    }


# ═══════════════════════════════════════════════════════════
# CONWAY PROVIDER
# ═══════════════════════════════════════════════════════════

async def conway_exec(sandbox_id: str, command: str, timeout: int = 120) -> dict:
    api_key = await get_conway_api_key()
    if not api_key:
        return {"stdout": "", "stderr": "No Conway API key", "exit_code": -1}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 10)) as session:
        try:
            async with session.post(
                f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/exec",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"command": command, "timeout": timeout},
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"stdout": data.get("stdout", ""), "stderr": data.get("stderr", ""),
                            "exit_code": data.get("exitCode", data.get("exit_code", -1))}
                return {"stdout": "", "stderr": f"HTTP {resp.status}", "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}


async def conway_write_file(sandbox_id: str, file_path: str, content: str) -> dict:
    api_key = await get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        try:
            async with session.post(
                f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/files",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"path": file_path, "content": content},
            ) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# FLY.IO PROVIDER — uses native Machines API exec endpoint
# ═══════════════════════════════════════════════════════════

async def fly_create_sandbox(specs: dict, agent_id: str = None) -> dict:
    """Create a Fly.io Machine. Uses node:22 (has Node.js + npm + git + Debian)."""
    fly = await get_fly_config(agent_id)
    if not fly["token"]:
        return {"error": "No Fly.io API token configured"}

    memory_mb = max(512, specs.get("memory_mb", 512))
    cpus = specs.get("vcpu", 1)

    # Map Conway-style regions to Fly regions
    region_map = {"us-east": "iad", "us-west": "sjc", "eu-west": "lhr", "eu-central": "fra", "ap-southeast": "sin"}
    fly_region = region_map.get(specs.get("region", ""), specs.get("region", "iad"))

    machine_config = {
        "name": f"anima-{get_active_agent_id()}",
        "region": fly_region,
        "config": {
            "image": "node:22",
            "init": {"exec": ["tail", "-f", "/dev/null"]},
            "guest": {
                "cpu_kind": "shared",
                "cpus": cpus,
                "memory_mb": memory_mb,
            },
            "restart": {"policy": "always"},
            "auto_destroy": False,
        },
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        try:
            # Create Machine
            async with session.post(
                f"{FLY_API}/v1/apps/{fly['app_name']}/machines",
                headers={"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"},
                json=machine_config,
            ) as resp:
                data = await resp.json()
                if resp.status not in (200, 201):
                    return {"error": data.get("error", data.get("message", f"HTTP {resp.status}")), "raw": data}

                machine_id = data.get("id", "")
                app_name = fly["app_name"]

                # Wait for Machine to start
                try:
                    async with session.get(
                        f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/wait?state=started&timeout=30",
                        headers={"Authorization": f"Bearer {fly['token']}"},
                    ) as wait_resp:
                        await wait_resp.json()
                except Exception:
                    pass

                return {
                    "id": machine_id,
                    "sandbox_id": machine_id,
                    "provider": "fly",
                    "fly_app_name": app_name,
                    "region": data.get("region", fly_region),
                    "state": data.get("state", ""),
                    "private_ip": data.get("private_ip", ""),
                }
        except Exception as e:
            return {"error": str(e)}


async def fly_exec(machine_id: str, command: str, timeout: int = 120, agent_id: str = None) -> dict:
    """Execute a command inside a Fly Machine via native /exec endpoint.
    Auto-starts the Machine if it's stopped."""
    fly = await get_fly_config(agent_id)
    if not fly["token"] or not machine_id:
        return {"stdout": "", "stderr": "No Fly token or machine ID", "exit_code": -1}

    headers = {"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"}
    app = fly["app_name"]

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 30)) as session:
        # Ensure Machine is running
        try:
            async with session.get(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}", headers=headers) as resp:
                if resp.status == 200:
                    mdata = await resp.json()
                    if mdata.get("state") != "started":
                        await session.post(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/start", headers=headers)
                        await session.get(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/wait?state=started&timeout=30", headers=headers)
        except Exception:
            pass

        try:
            async with session.post(
                f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/exec",
                headers=headers,
                json={"command": ["bash", "-c", command], "timeout": timeout},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "stdout": data.get("stdout", ""),
                        "stderr": data.get("stderr", ""),
                        "exit_code": data.get("exit_code", data.get("exitCode", -1)),
                    }
                body = await resp.text()
                return {"stdout": "", "stderr": f"HTTP {resp.status}: {body[:200]}", "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}


async def fly_write_file(machine_id: str, file_path: str, content: str, agent_id: str = None) -> dict:
    """Write a file inside a Fly Machine by exec'ing a write command."""
    import base64
    encoded = base64.b64encode(content.encode()).decode()
    result = await fly_exec(
        machine_id,
        f"mkdir -p $(dirname '{file_path}') && echo '{encoded}' | base64 -d > '{file_path}'",
        timeout=30,
        agent_id=agent_id,
    )
    if result.get("exit_code") == 0:
        return {"ok": True}
    return {"error": result.get("stderr", "write failed")}


# ═══════════════════════════════════════════════════════════
# UNIFIED INTERFACE — dispatches to the right provider
# ═══════════════════════════════════════════════════════════

async def create_sandbox(specs: dict, provider: str = "conway", agent_id: str = None) -> dict:
    if provider == "fly":
        return await fly_create_sandbox(specs, agent_id)
    # Conway: handled directly in agent_setup.py via _conway_request
    return {"error": "Use Conway create flow in agent_setup.py"}


async def sandbox_exec(sandbox_id: str, command: str, timeout: int = 120, agent_id: str = None) -> dict:
    """Execute a command inside a sandbox. Routes to the right provider."""
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")

    if provider == "fly":
        return await fly_exec(sandbox_id, command, timeout, agent_id)
    return await conway_exec(sandbox_id, command, timeout)


async def sandbox_write_file(sandbox_id: str, file_path: str, content: str, agent_id: str = None) -> dict:
    """Write a file inside a sandbox. Routes to the right provider."""
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")

    if provider == "fly":
        return await fly_write_file(sandbox_id, file_path, content, agent_id)
    return await conway_write_file(sandbox_id, file_path, content)
