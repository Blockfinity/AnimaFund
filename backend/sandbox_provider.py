"""
PLATFORM: Sandbox Provider — abstraction layer for VM/container providers.
Supports: Conway Cloud, Fly.io. Each provider implements the same interface.
"""
import os
import json
import base64
import aiohttp
import logging
from datetime import datetime, timezone

from agent_state import get_active_agent_id, load_provisioning, save_provisioning, get_conway_api_key

logger = logging.getLogger("sandbox_provider")

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
FLY_API = "https://api.machines.dev"


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
    # Longer timeout for large files (bundle.mjs is ~10MB)
    timeout = max(60, len(content) // 100000 + 30)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
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
# FLY.IO PROVIDER — persistent volume + native exec
# ═══════════════════════════════════════════════════════════

async def fly_create_sandbox(specs: dict, agent_id: str = None) -> dict:
    """Create a Fly.io Machine with persistent volume. node:22 image."""
    fly = await get_fly_config(agent_id)
    if not fly["token"]:
        return {"error": "No Fly.io API token configured"}

    memory_mb = max(512, specs.get("memory_mb", 512))
    cpus = specs.get("vcpu", 1)
    app_name = fly["app_name"]

    region_map = {"us-east": "iad", "us-west": "sjc", "eu-west": "lhr", "eu-central": "fra", "ap-southeast": "sin"}
    fly_region = region_map.get(specs.get("region", ""), specs.get("region", "iad"))

    headers = {"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        try:
            # 1. Find or create a persistent volume
            volume_id = None
            async with session.get(f"{FLY_API}/v1/apps/{app_name}/volumes", headers=headers) as resp:
                if resp.status == 200:
                    for v in await resp.json():
                        if v.get("region") == fly_region and v.get("attached_machine_id") in (None, ""):
                            volume_id = v["id"]
                            break
            if not volume_id:
                async with session.post(f"{FLY_API}/v1/apps/{app_name}/volumes",
                    headers=headers, json={"name": "anima_data", "size_gb": 1, "region": fly_region}) as resp:
                    if resp.status in (200, 201):
                        volume_id = (await resp.json()).get("id")

            # 2. Check for existing machines — reuse if found
            async with session.get(f"{FLY_API}/v1/apps/{app_name}/machines", headers=headers) as resp:
                existing_machines = await resp.json() if resp.status == 200 else []

            if existing_machines:
                # Reuse the first machine
                existing = existing_machines[0]
                machine_id = existing["id"]
                state = existing.get("state", "")

                # Start it if stopped
                if state != "started":
                    await session.post(f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/start", headers=headers)
                    try:
                        async with session.get(f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/wait?state=started&timeout=30", headers=headers) as wr:
                            await wr.read()
                    except Exception:
                        pass

                # Set up symlinks if volume is attached
                mounts = existing.get("config", {}).get("mounts", [])
                if mounts:
                    setup_cmd = (
                        "mkdir -p /data/anima /data/automaton/dist /data/openclaw /data/conway /data/logs && "
                        "test -L /root/.anima || (rm -rf /root/.anima && ln -sfn /data/anima /root/.anima) && "
                        "test -L /app/automaton || (rm -rf /app/automaton && ln -sfn /data/automaton /app/automaton) && "
                        "test -L /root/.openclaw || (rm -rf /root/.openclaw && ln -sfn /data/openclaw /root/.openclaw) && "
                        "test -L /root/.conway || (rm -rf /root/.conway && ln -sfn /data/conway /root/.conway) && "
                        "touch /data/logs/automaton.out.log /data/logs/automaton.err.log && "
                        "ln -sfn /data/logs/automaton.out.log /var/log/automaton.out.log 2>/dev/null; "
                        "ln -sfn /data/logs/automaton.err.log /var/log/automaton.err.log 2>/dev/null; "
                        "echo READY"
                    )
                    async with session.post(f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/exec",
                        headers=headers, json={"command": ["bash", "-c", setup_cmd], "timeout": 15}) as er:
                        pass

                return {
                    "id": machine_id, "sandbox_id": machine_id, "provider": "fly",
                    "fly_app_name": app_name, "volume_id": mounts[0]["volume"] if mounts else "",
                    "region": existing.get("region", fly_region), "state": "started",
                    "reused": True,
                }

            # 3. No existing machine — create new one
            machine_config = {
                "name": f"anima-{get_active_agent_id()}",
                "region": fly_region,
                "config": {
                    "image": "node:22",
                    "init": {"exec": ["tail", "-f", "/dev/null"]},
                    "guest": {"cpu_kind": "shared", "cpus": cpus, "memory_mb": memory_mb},
                    "restart": {"policy": "always"},
                    "auto_destroy": False,
                },
            }
            if volume_id:
                machine_config["config"]["mounts"] = [{"volume": volume_id, "path": "/data"}]

            async with session.post(f"{FLY_API}/v1/apps/{app_name}/machines",
                headers=headers, json=machine_config) as resp:
                data = await resp.json()
                if resp.status not in (200, 201):
                    return {"error": data.get("error", data.get("message", f"HTTP {resp.status}")), "raw": data}

                machine_id = data.get("id", "")
                try:
                    async with session.get(
                        f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/wait?state=started&timeout=30",
                        headers=headers) as wr:
                        await wr.read()
                except Exception:
                    pass

                # 3. Set up symlinks: agent data lives on the volume (survives restarts)
                if volume_id:
                    setup_cmd = (
                        "mkdir -p /data/anima /data/automaton/dist /data/openclaw /data/conway /data/logs && "
                        "rm -rf /root/.anima /app/automaton /root/.openclaw /root/.conway && "
                        "ln -sfn /data/anima /root/.anima && "
                        "ln -sfn /data/automaton /app/automaton && "
                        "ln -sfn /data/openclaw /root/.openclaw && "
                        "ln -sfn /data/conway /root/.conway && "
                        "touch /data/logs/automaton.out.log /data/logs/automaton.err.log && "
                        "ln -sfn /data/logs/automaton.out.log /var/log/automaton.out.log && "
                        "ln -sfn /data/logs/automaton.err.log /var/log/automaton.err.log && "
                        "echo VOLUME_READY"
                    )
                    # Use direct API call since fly_exec needs provisioning state saved first
                    async with session.post(
                        f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/exec",
                        headers=headers,
                        json={"command": ["bash", "-c", setup_cmd], "timeout": 15},
                    ) as _:
                        pass

                return {
                    "id": machine_id, "sandbox_id": machine_id, "provider": "fly",
                    "fly_app_name": app_name, "volume_id": volume_id or "",
                    "region": data.get("region", fly_region), "state": data.get("state", ""),
                }
        except Exception as e:
            return {"error": str(e)}


async def fly_update_machine_init(machine_id: str, init_cmd: list, agent_id: str = None) -> dict:
    """Update a Fly Machine's init command (e.g., to start the engine after deploy)."""
    fly = await get_fly_config(agent_id)
    if not fly["token"]:
        return {"error": "No Fly token"}
    headers = {"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"}
    app = fly["app_name"]

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        # Get current machine config
        async with session.get(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}", headers=headers) as resp:
            if resp.status != 200:
                return {"error": f"Cannot get machine: HTTP {resp.status}"}
            mdata = await resp.json()

        # Update init command
        config = mdata.get("config", {})
        config["init"] = {"exec": init_cmd}

        async with session.post(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}",
            headers=headers, json={"config": config}) as resp:
            if resp.status in (200, 201):
                return {"success": True}
            return {"error": f"Update failed: HTTP {resp.status}"}


async def fly_exec(machine_id: str, command: str, timeout: int = 120, agent_id: str = None) -> dict:
    """Execute a command inside a Fly Machine. Auto-starts if stopped."""
    fly = await get_fly_config(agent_id)
    if not fly["token"] or not machine_id:
        return {"stdout": "", "stderr": "No Fly token or machine ID", "exit_code": -1}

    headers = {"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"}
    app = fly["app_name"]

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 30)) as session:
        # Check machine exists and ensure running
        try:
            async with session.get(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}", headers=headers) as resp:
                if resp.status == 404:
                    await save_provisioning({"sandbox": {"status": "none", "id": None}, "tools": {}, "ports": [], "domains": [], "compute_verified": False, "skills_loaded": False, "nudges": [], "wallet_address": "", "last_updated": None}, agent_id)
                    return {"stdout": "", "stderr": "Machine not found — provisioning reset. Click 'Create Sandbox'.", "exit_code": -1}
                if resp.status == 200:
                    mdata = await resp.json()
                    state = mdata.get("state", "")
                    if state == "destroyed":
                        await save_provisioning({"sandbox": {"status": "none", "id": None}, "tools": {}, "ports": [], "domains": [], "compute_verified": False, "skills_loaded": False, "nudges": [], "wallet_address": "", "last_updated": None}, agent_id)
                        return {"stdout": "", "stderr": "Machine destroyed — provisioning reset. Click 'Create Sandbox'.", "exit_code": -1}
                    if state != "started":
                        logger.info(f"Machine {machine_id} is '{state}', starting...")
                        await session.post(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/start", headers=headers)
                        try:
                            async with session.get(f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/wait?state=started&timeout=30", headers=headers) as wr:
                                await wr.read()
                        except Exception:
                            pass
        except aiohttp.ClientError as e:
            return {"stdout": "", "stderr": f"Cannot reach Fly API: {e}", "exit_code": -1}

        # Execute
        try:
            async with session.post(
                f"{FLY_API}/v1/apps/{app}/machines/{machine_id}/exec",
                headers=headers, json={"command": ["bash", "-c", command], "timeout": timeout},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"stdout": data.get("stdout", ""), "stderr": data.get("stderr", ""),
                            "exit_code": data.get("exit_code", data.get("exitCode", -1))}
                body = await resp.text()
                return {"stdout": "", "stderr": f"Exec failed (HTTP {resp.status}): {body[:200]}", "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}


async def fly_write_file(machine_id: str, file_path: str, content: str, agent_id: str = None) -> dict:
    """Write a file inside a Fly Machine via exec. Handles large files via chunked base64."""
    encoded = base64.b64encode(content.encode()).decode()

    if len(encoded) > 60000:
        # Large file: write base64 in chunks to temp file, then decode
        chunk_size = 40000
        chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]

        # Clear temp file
        await fly_exec(machine_id, f"mkdir -p $(dirname '{file_path}') && rm -f /tmp/_b64chunk", timeout=10, agent_id=agent_id)

        # Write chunks
        for i, chunk in enumerate(chunks):
            op = ">" if i == 0 else ">>"
            r = await fly_exec(machine_id, f"printf '%s' '{chunk}' {op} /tmp/_b64chunk", timeout=15, agent_id=agent_id)
            if r.get("exit_code") != 0:
                return {"error": f"Chunk {i}/{len(chunks)} write failed: {r.get('stderr','')[:100]}"}

        # Decode and write to final path
        result = await fly_exec(machine_id,
            f"base64 -d /tmp/_b64chunk > '{file_path}' && rm -f /tmp/_b64chunk && wc -c < '{file_path}'",
            timeout=30, agent_id=agent_id)
        if result.get("exit_code") == 0:
            return {"ok": True, "size": result.get("stdout", "").strip()}
        return {"error": result.get("stderr", "decode failed")}
    else:
        result = await fly_exec(machine_id,
            f"mkdir -p $(dirname '{file_path}') && printf '%s' '{encoded}' | base64 -d > '{file_path}'",
            timeout=30, agent_id=agent_id)
        if result.get("exit_code") == 0:
            return {"ok": True}
        return {"error": result.get("stderr", "write failed")}


# ═══════════════════════════════════════════════════════════
# UNIFIED INTERFACE
# ═══════════════════════════════════════════════════════════

async def create_sandbox(specs: dict, provider: str = "conway", agent_id: str = None) -> dict:
    if provider == "fly":
        return await fly_create_sandbox(specs, agent_id)
    return {"error": "Use Conway create flow in agent_setup.py"}


async def sandbox_exec(sandbox_id: str, command: str, timeout: int = 120, agent_id: str = None) -> dict:
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")
    if provider == "fly":
        return await fly_exec(sandbox_id, command, timeout, agent_id)
    return await conway_exec(sandbox_id, command, timeout)


async def sandbox_write_file(sandbox_id: str, file_path: str, content: str, agent_id: str = None) -> dict:
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")
    if provider == "fly":
        return await fly_write_file(sandbox_id, file_path, content, agent_id)
    return await conway_write_file(sandbox_id, file_path, content)
