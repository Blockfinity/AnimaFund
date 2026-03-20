"""
BYOI Provider Interface — Generic base class for any VM provider.
Each provider implements: create_vm, exec_in_vm, destroy_vm, get_status.
"""
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract interface for BYOI VM providers."""

    def __init__(self, api_key: str, api_url: str = ""):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    async def create_vm(self, tier: str = "hobby", region: str = "us") -> dict:
        """Create a VM. Returns: { vm_id, terminal_url, ip, ... }"""
        pass

    @abstractmethod
    async def exec_in_vm(self, vm_id: str, command: str, timeout: int = 30) -> dict:
        """Execute a command in a VM. Returns: { output, exit_code }"""
        pass

    @abstractmethod
    async def destroy_vm(self, vm_id: str) -> dict:
        """Destroy a VM. Returns: { success }"""
        pass

    @abstractmethod
    async def get_status(self, vm_id: str) -> dict:
        """Get VM status. Returns: { status, uptime, ... }"""
        pass

    @abstractmethod
    async def write_file(self, vm_id: str, path: str, content: str) -> dict:
        """Write a file to a VM. Returns: { success }"""
        pass
