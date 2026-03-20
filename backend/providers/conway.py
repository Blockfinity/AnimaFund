"""
Conway Cloud BYOI Provider — implements BaseProvider for Conway's sandbox API.
Conway is ONE optional provider. The platform does NOT depend on it.
"""
import logging
import aiohttp
from providers import BaseProvider


CONWAY_API = "https://api.conway.tech"


class ConwayProvider(BaseProvider):
    """Conway Cloud VM provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, api_url=CONWAY_API)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_vm(self, tier: str = "hobby", region: str = "us") -> dict:
        """Create a Conway sandbox (VM)."""
        tier_map = {"hobby": 2, "pro": 4}
        vcpus = tier_map.get(tier, 2)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/v1/sandboxes",
                headers=self._headers(),
                json={"vcpus": vcpus, "memory_mb": 8192, "disk_gb": 50},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Conway create_vm failed ({resp.status}): {text}")
                data = await resp.json()
                sandbox_id = data.get("id") or data.get("sandbox_id")
                return {
                    "vm_id": sandbox_id,
                    "terminal_url": f"https://terminal.conway.tech/{sandbox_id}",
                    "provider": "conway",
                }

    async def exec_in_vm(self, vm_id: str, command: str, timeout: int = 30) -> dict:
        """Execute a command in a Conway sandbox."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/v1/sandboxes/{vm_id}/exec",
                headers=self._headers(),
                json={"command": command},
                timeout=aiohttp.ClientTimeout(total=timeout + 5),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"output": f"exec failed: {text}", "exit_code": 1}
                data = await resp.json()
                return {
                    "output": data.get("output", ""),
                    "exit_code": data.get("exit_code", 0),
                }

    async def destroy_vm(self, vm_id: str) -> dict:
        """Destroy a Conway sandbox."""
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.api_url}/v1/sandboxes/{vm_id}",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                return {"success": resp.status == 200}

    async def get_status(self, vm_id: str) -> dict:
        """Get Conway sandbox status."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/v1/sandboxes/{vm_id}",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return {"status": "unknown"}
                data = await resp.json()
                return {
                    "status": data.get("status", "unknown"),
                    "uptime": data.get("uptime"),
                    "vm_id": vm_id,
                }

    async def write_file(self, vm_id: str, path: str, content: str) -> dict:
        """Write a file to a Conway sandbox."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/v1/sandboxes/{vm_id}/files",
                headers=self._headers(),
                json={"path": path, "content": content},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                return {"success": resp.status == 200}
