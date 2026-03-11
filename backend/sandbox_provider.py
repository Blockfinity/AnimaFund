"""
PLATFORM: Sandbox Provider — abstraction layer for VM/container providers.
Supports: Conway Cloud, Fly.io. Each provider implements the same interface.
The provisioning steps work identically regardless of provider.
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

# ═══════════════════════════════════════════════════════════
# EXEC API — embedded in Fly Machines for remote command execution
# ═══════════════════════════════════════════════════════════

EXEC_API_SCRIPT = '''#!/usr/bin/env python3
"""Tiny HTTP exec API — runs inside Fly Machines so the platform can exec commands remotely.
Equivalent to Conway's sandbox_exec endpoint."""
import json, subprocess, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

AUTH_TOKEN = os.environ.get("EXEC_TOKEN", "")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _auth(self):
        if AUTH_TOKEN and self.headers.get("Authorization") != f"Bearer {AUTH_TOKEN}":
            self.send_response(401); self.end_headers(); return False
        return True
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    def do_POST(self):
        if not self._auth(): return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.path == "/exec":
            cmd = body.get("command", "")
            timeout = body.get("timeout", 120)
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                self._json(200, {"stdout": r.stdout, "stderr": r.stderr, "exitCode": r.returncode})
            except subprocess.TimeoutExpired:
                self._json(200, {"stdout": "", "stderr": "timeout", "exitCode": -1})
            except Exception as e:
                self._json(200, {"stdout": "", "stderr": str(e), "exitCode": -1})
        elif self.path == "/write-file":
            path = body.get("path", "")
            content = body.get("content", "")
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f: f.write(content)
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(500, {"error": str(e)})
        elif self.path == "/read-file":
            path = body.get("path", "")
            try:
                with open(path) as f: self._json(200, {"content": f.read()})
            except Exception as e:
                self._json(404, {"error": str(e)})
        elif self.path == "/health":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(b\'{"status":"ok"}\')
        else:
            self.send_response(404); self.end_headers()

print("Exec API starting on :8080", flush=True)
HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
'''


# ═══════════════════════════════════════════════════════════
# PROVIDER: Get the right provider for the active agent
# ═══════════════════════════════════════════════════════════

async def get_provider_type(agent_id: str = None) -> str:
    """Get the sandbox provider type for an agent from its provisioning status."""
    prov = await load_provisioning(agent_id)
    return prov.get("provider", "conway")


async def get_fly_config(agent_id: str = None) -> dict:
    """Get Fly.io config from agent's provisioning or env."""
    prov = await load_provisioning(agent_id)
    return {
        "token": prov.get("fly_token") or os.environ.get("FLY_API_TOKEN", ""),
        "app_name": prov.get("fly_app_name") or os.environ.get("FLY_APP_NAME", "animafund"),
        "exec_token": prov.get("fly_exec_token", ""),
        "exec_url": prov.get("fly_exec_url", ""),
    }


# ═══════════════════════════════════════════════════════════
# CONWAY PROVIDER
# ═══════════════════════════════════════════════════════════

async def conway_create_sandbox(specs: dict) -> dict:
    """Create a Conway Cloud sandbox VM."""
    api_key = await get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        try:
            async with session.post(
                f"{CONWAY_API}/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=specs,
            ) as resp:
                data = await resp.json()
                if resp.status not in (200, 201):
                    return {"error": data.get("error", data.get("message", f"HTTP {resp.status}"))}
                return data
        except Exception as e:
            return {"error": str(e)}


async def conway_exec(sandbox_id: str, command: str, timeout: int = 120) -> dict:
    """Execute a command inside a Conway sandbox."""
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
    """Write a file inside a Conway sandbox."""
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


async def conway_list_sandboxes() -> dict:
    """List Conway sandboxes."""
    api_key = await get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# FLY.IO PROVIDER
# ═══════════════════════════════════════════════════════════

async def fly_create_sandbox(specs: dict, agent_id: str = None) -> dict:
    """Create a Fly.io Machine with embedded exec API."""
    fly = await get_fly_config(agent_id)
    if not fly["token"]:
        return {"error": "No Fly.io API token configured"}

    import secrets
    exec_token = secrets.token_hex(16)

    memory_mb = specs.get("memory_mb", 512)
    cpus = specs.get("vcpu", 1)

    # Map Conway-style regions to Fly regions
    region_map = {"us-east": "iad", "us-west": "sjc", "eu-west": "lhr", "eu-central": "fra", "ap-southeast": "sin"}
    fly_region = region_map.get(specs.get("region", ""), specs.get("region", "iad"))

    exec_api_b64 = base64.b64encode(EXEC_API_SCRIPT.encode()).decode()

    machine_config = {
        "name": f"anima-{get_active_agent_id()}",
        "region": fly_region,
        "config": {
            "image": "python:3.11-slim",
            "env": {
                "EXEC_TOKEN": exec_token,
            },
            "files": [
                {"guest_path": "/root/exec-api.py", "raw_value": exec_api_b64},
            ],
            "init": {
                "exec": ["/usr/local/bin/python3", "/root/exec-api.py"],
            },
            "guest": {
                "cpu_kind": "shared",
                "cpus": cpus,
                "memory_mb": max(256, memory_mb),
            },
            "services": [
                {
                    "ports": [
                        {"port": 443, "handlers": ["tls", "http"]},
                        {"port": 80, "handlers": ["http"]},
                    ],
                    "protocol": "tcp",
                    "internal_port": 8080,
                    "autostart": True,
                    "autostop": "off",
                }
            ],
            "restart": {"policy": "always"},
        },
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        try:
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

                # Ensure the app has IPs allocated (needed for public access)
                try:
                    async with session.post(
                        "https://api.fly.io/graphql",
                        headers={"Authorization": f"Bearer {fly['token']}", "Content-Type": "application/json"},
                        json={"query": f'mutation {{ allocateIpAddress(input: {{appId: "{app_name}", type: v6}}) {{ ipAddress {{ address }} }} }}'},
                    ) as _:
                        pass
                except Exception:
                    pass

                # Wait for Machine to start
                try:
                    async with session.get(
                        f"{FLY_API}/v1/apps/{app_name}/machines/{machine_id}/wait?state=started&timeout=30",
                        headers={"Authorization": f"Bearer {fly['token']}"},
                    ) as wait_resp:
                        pass
                except Exception:
                    pass

                exec_url = f"https://{app_name}.fly.dev"

                return {
                    "id": machine_id,
                    "sandbox_id": machine_id,
                    "provider": "fly",
                    "exec_url": exec_url,
                    "exec_token": exec_token,
                    "fly_app_name": app_name,
                    "region": data.get("region", ""),
                    "state": data.get("state", ""),
                    "private_ip": data.get("private_ip", ""),
                }
        except Exception as e:
            return {"error": str(e)}


async def fly_exec(exec_url: str, exec_token: str, command: str, timeout: int = 120) -> dict:
    """Execute a command inside a Fly Machine via the embedded exec API."""
    if not exec_url:
        return {"stdout": "", "stderr": "No exec URL", "exit_code": -1}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 10)) as session:
        try:
            async with session.post(
                f"{exec_url}/exec",
                headers={"Authorization": f"Bearer {exec_token}", "Content-Type": "application/json"},
                json={"command": command, "timeout": timeout},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"stdout": data.get("stdout", ""), "stderr": data.get("stderr", ""),
                            "exit_code": data.get("exitCode", -1)}
                return {"stdout": "", "stderr": f"HTTP {resp.status}", "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1}


async def fly_write_file(exec_url: str, exec_token: str, file_path: str, content: str) -> dict:
    """Write a file inside a Fly Machine via the embedded exec API."""
    if not exec_url:
        return {"error": "No exec URL"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        try:
            async with session.post(
                f"{exec_url}/write-file",
                headers={"Authorization": f"Bearer {exec_token}", "Content-Type": "application/json"},
                json={"path": file_path, "content": content},
            ) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# UNIFIED INTERFACE — dispatches to the right provider
# ═══════════════════════════════════════════════════════════

async def create_sandbox(specs: dict, provider: str = "conway", agent_id: str = None) -> dict:
    """Create a sandbox VM/container with the specified provider."""
    if provider == "fly":
        return await fly_create_sandbox(specs, agent_id)
    return await conway_create_sandbox(specs)


async def sandbox_exec(sandbox_id: str, command: str, timeout: int = 120, agent_id: str = None) -> dict:
    """Execute a command inside a sandbox. Routes to the right provider."""
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")

    if provider == "fly":
        exec_url = prov.get("fly_exec_url", "")
        exec_token = prov.get("fly_exec_token", "")
        return await fly_exec(exec_url, exec_token, command, timeout)
    return await conway_exec(sandbox_id, command, timeout)


async def sandbox_write_file(sandbox_id: str, file_path: str, content: str, agent_id: str = None) -> dict:
    """Write a file inside a sandbox. Routes to the right provider."""
    prov = await load_provisioning(agent_id)
    provider = prov.get("provider", "conway")

    if provider == "fly":
        exec_url = prov.get("fly_exec_url", "")
        exec_token = prov.get("fly_exec_token", "")
        return await fly_write_file(exec_url, exec_token, file_path, content)
    return await conway_write_file(sandbox_id, file_path, content)
