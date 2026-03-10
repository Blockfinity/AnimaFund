"""
Infrastructure Router — Sandbox/VM monitoring, terminal output, domains,
installed tools, and activity feed.
All data comes from sandbox or returns empty defaults — nothing from host engine.
"""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api", tags=["infrastructure"])


def _empty(key="items"):
    return {key: [], "total": 0, "source": "sandbox"}


@router.get("/infrastructure/sandboxes")
async def get_sandboxes():
    """Sandboxes managed by the agent — will be populated when engine runs in sandbox."""
    return _empty("sandboxes")


@router.get("/infrastructure/terminal")
async def get_terminal_output(limit: int = Query(default=50, le=200)):
    """Terminal commands run by the agent inside sandbox."""
    return _empty("commands")


@router.get("/infrastructure/domains")
async def get_domains():
    """Domains registered by the agent."""
    return _empty("domains")


@router.get("/infrastructure/tools")
async def get_installed_tools():
    """Tools installed by the agent inside sandbox."""
    return _empty("tools")


@router.get("/infrastructure/ports")
async def get_exposed_ports():
    """Ports exposed by the agent."""
    return _empty("ports")


@router.get("/infrastructure/activity")
async def get_activity_feed(limit: int = Query(default=100, le=500)):
    """Comprehensive activity feed from sandbox."""
    return _empty("activities")
