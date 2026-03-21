"""
Fly.io BYOI Provider — deploys Anima Machina agents to Fly Machines.
"""
import logging
import aiohttp
from providers import BaseProvider

logger = logging.getLogger(__name__)

FLY_API = "https://api.machines.dev/v1"


class FlyProvider(BaseProvider):
    """Fly.io Machines API provider."""

    def __init__(self, api_key: str, app_name: str = "animafund"):
        super().__init__(api_key=api_key, api_url=FLY_API)
        self.app_name = app_name

    def _headers(self):
        return {
            "Authorization": f"FlyV1 {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_vm(self, tier: str = "hobby", region: str = "iad") -> dict:
        """Create a Fly Machine with Python + pip."""
        memory = 512 if tier == "hobby" else 1024
        config = {
            "config": {
                "image": "python:3.11-slim",
                "init": {"exec": ["/bin/bash", "-c", "apt-get update -qq && apt-get install -y -qq curl git && pip install camel-ai httpx eth-account web3 && sleep infinity"]},
                "guest": {"cpu_kind": "shared", "cpus": 1, "memory_mb": memory},
                "auto_destroy": False,
                "restart": {"policy": "on-failure"},
            },
            "region": region,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/apps/{self.app_name}/machines",
                headers=self._headers(),
                json=config,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise Exception(f"Fly create_vm failed ({resp.status}): {text}")
                data = await resp.json()
                machine_id = data.get("id", "")
                return {
                    "vm_id": machine_id,
                    "provider": "fly",
                    "region": region,
                }

    async def exec_in_vm(self, vm_id: str, command: str, timeout: int = 30) -> dict:
        """Execute a command in a Fly Machine via bash."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/apps/{self.app_name}/machines/{vm_id}/exec",
                headers=self._headers(),
                json={"command": ["bash", "-c", command]},
                timeout=aiohttp.ClientTimeout(total=timeout + 10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"output": f"exec failed ({resp.status}): {text[:200]}", "exit_code": 1}
                data = await resp.json()
                return {
                    "output": data.get("stdout", "") + data.get("stderr", ""),
                    "exit_code": data.get("exit_code", 0),
                }

    async def destroy_vm(self, vm_id: str) -> dict:
        """Destroy a Fly Machine."""
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/apps/{self.app_name}/machines/{vm_id}?force=true",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                return {"success": resp.status == 200}

    async def get_status(self, vm_id: str) -> dict:
        """Get Fly Machine status."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/apps/{self.app_name}/machines/{vm_id}",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return {"status": "unknown"}
                data = await resp.json()
                return {
                    "status": data.get("state", "unknown"),
                    "vm_id": vm_id,
                    "region": data.get("region", ""),
                }

    async def write_file(self, vm_id: str, path: str, content: str) -> dict:
        """Write a file via exec (base64 encode to avoid escaping issues)."""
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        cmd = f"echo '{b64}' | base64 -d > {path}"
        return await self.exec_in_vm(vm_id, cmd, timeout=10)
