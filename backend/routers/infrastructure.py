"""
Infrastructure Router — reads from provisioning status + webhook cache.
Shows sandboxes, tools, domains, and activity from the live agent.
"""
from fastapi import APIRouter, Query
from agent_state import load_provisioning, get_active_agent_id
from sandbox_poller import get_cache

router = APIRouter(prefix="/api", tags=["infrastructure"])


@router.get("/infrastructure/sandboxes")
async def get_sandboxes():
    """Sandboxes managed by the agent."""
    prov = await load_provisioning()
    sandbox = prov.get("sandbox", {})
    sandboxes = []
    if sandbox.get("id"):
        sandboxes.append({
            "id": sandbox["id"],
            "status": sandbox.get("status", "unknown"),
            "provider": prov.get("provider", "conway"),
            "region": sandbox.get("region", ""),
            "vcpu": sandbox.get("vcpu", 1),
            "memory_mb": sandbox.get("memory_mb", 512),
        })
    return {"sandboxes": sandboxes, "total": len(sandboxes), "source": "provisioning"}


@router.get("/infrastructure/terminal")
async def get_terminal_output(limit: int = Query(default=50, le=200)):
    """Terminal output from the agent's logs."""
    cache = get_cache()
    stdout = cache.get("agent_stdout", "")
    lines = stdout.split("\n")[-limit:] if stdout else []
    commands = [{"output": l, "type": "log"} for l in lines if l.strip()]
    return {"commands": commands, "total": len(commands), "source": "webhook"}


@router.get("/infrastructure/domains")
async def get_domains():
    """Domains registered by the agent."""
    prov = await load_provisioning()
    domains = prov.get("domains", [])
    return {"domains": domains, "total": len(domains), "source": "provisioning"}


@router.get("/infrastructure/tools")
async def get_installed_tools():
    """Tools installed in the sandbox."""
    prov = await load_provisioning()
    tools = prov.get("tools", {})
    tool_list = [{"name": k, "installed": v.get("installed", v.get("deployed", False)),
                  "timestamp": v.get("timestamp", "")} for k, v in tools.items()]
    return {"tools": tool_list, "total": len(tool_list), "source": "provisioning"}


@router.get("/infrastructure/ports")
async def get_exposed_ports():
    """Ports exposed by the agent."""
    prov = await load_provisioning()
    ports = prov.get("ports", [])
    return {"ports": ports, "total": len(ports), "source": "provisioning"}


@router.get("/infrastructure/activity-feed")
async def get_activity_feed(limit: int = Query(default=100, le=500)):
    """Activity feed — decisions + revenue from webhook cache."""
    cache = get_cache()
    decisions = cache.get("decisions_log", [])
    revenue = cache.get("revenue_log", [])
    activities = []
    for d in decisions[:limit]:
        if isinstance(d, dict):
            activities.append({**d, "category": "decision"})
    for r in revenue[:limit]:
        if isinstance(r, dict):
            activities.append({**r, "category": "revenue"})
    activities.sort(key=lambda x: x.get("timestamp", x.get("time", "")), reverse=True)
    return {"activities": activities[:limit], "total": len(activities), "source": "webhook"}


@router.get("/infrastructure/activity")
async def get_activity():
    """Alias for activity-feed."""
    return await get_activity_feed()


@router.get("/infrastructure/overview")
async def get_overview():
    """Overview stats for Infrastructure page."""
    prov = await load_provisioning()
    cache = get_cache()
    sandbox = prov.get("sandbox", {})
    tools = prov.get("tools", {})
    return {
        "sandboxes": 1 if sandbox.get("id") else 0,
        "domains": len(prov.get("domains", [])),
        "installed_tools": len(tools),
        "discovered_agents": len(cache.get("decisions_log", [])),
        "messages": 0,
        "public_urls": len(prov.get("ports", [])),
        "engine_running": cache.get("engine_running", False),
        "source": "provisioning",
    }


@router.get("/infrastructure/installed-tools")
async def get_installed_tools_detail():
    """Alias for /infrastructure/tools."""
    return await get_installed_tools()
