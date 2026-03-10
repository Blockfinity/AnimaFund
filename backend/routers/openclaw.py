"""
OpenClaw VM Viewer — Conway Sandbox + OpenClaw monitoring.

Architecture:
  - The agent creates Conway sandbox VMs via sandbox_create
  - The agent installs OpenClaw INSIDE those sandbox VMs via sandbox_exec
  - OpenClaw runs as a daemon inside the Conway VM (browser control, agent network, MCP)
  - All browsing, agent discovery, and MCP calls go through OpenClaw in the sandbox

This module reads:
  1. Conway API — live sandbox VMs (status, URLs, specs)
  2. Agent state.db — tool calls involving sandbox_* and browse_page
  3. Derived OpenClaw state from sandbox_exec commands (install, daemon, browse activity)
"""
import os
import json
import re
import aiohttp
from fastapi import APIRouter

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])


def _get_conway_api_key() -> str:
    """Conway API key — only from environment, never from host filesystem."""
    return os.environ.get("CONWAY_API_KEY", "")


def _get_tool_calls(tool_names: tuple, limit: int = 200) -> list:
    """Tool calls come from sandbox state.db — returns empty when no host engine.
    The engine runs inside the sandbox, not on the host."""
    return []


def _parse_openclaw_state(sandbox_actions: list) -> dict:
    """Derive OpenClaw installation/running state from sandbox_exec commands."""
    openclaw_installed = False
    openclaw_daemon_running = False
    mcp_configured = False
    conway_terminal_in_sandbox = False
    last_openclaw_action = None

    for a in sandbox_actions:
        if a["tool"] != "sandbox_exec":
            continue
        cmd = a["arguments"].get("command", "")
        result = a["result"] or ""

        # Detect OpenClaw install
        if "openclaw" in cmd.lower() and ("install" in cmd.lower() or "curl" in cmd.lower()):
            if a["error"] is None and ("INSTALLED" in result or "openclaw" in result.lower()):
                openclaw_installed = True
                last_openclaw_action = a["timestamp"]

        # Detect daemon running
        if "openclaw" in cmd.lower() and "daemon" in cmd.lower():
            openclaw_daemon_running = True
            last_openclaw_action = a["timestamp"]

        # Detect MCP config
        if "mcp" in cmd.lower() and ("config" in cmd.lower() or "openclaw" in cmd.lower()):
            mcp_configured = True

        # Detect Conway Terminal in sandbox
        if "conway-terminal" in cmd.lower() and ("install" in cmd.lower() or "npm" in cmd.lower()):
            if a["error"] is None:
                conway_terminal_in_sandbox = True

    return {
        "openclaw_installed": openclaw_installed,
        "openclaw_daemon_running": openclaw_daemon_running,
        "mcp_configured": mcp_configured,
        "conway_terminal_in_sandbox": conway_terminal_in_sandbox,
        "last_openclaw_action": last_openclaw_action,
    }


def _extract_sandbox_ids(actions: list) -> list:
    """Extract unique sandbox IDs from sandbox_create results and other sandbox_* calls."""
    sandbox_ids = set()
    for a in actions:
        if a["tool"] == "sandbox_create":
            # sandbox_create result usually contains the sandbox ID
            result = a["result"] or ""
            # Try to parse JSON result
            try:
                r = json.loads(result)
                sid = r.get("id") or r.get("sandbox_id") or r.get("sandboxId", "")
                if sid:
                    sandbox_ids.add(sid)
            except Exception:
                # Try regex for ULIDs or UUIDs
                matches = re.findall(r'[0-9a-fA-F-]{20,}|[A-Z0-9]{26}', result)
                for m in matches:
                    sandbox_ids.add(m)
        elif a["tool"].startswith("sandbox_") and a["tool"] != "sandbox_create":
            # Other sandbox calls have sandbox_id in arguments
            sid = a["arguments"].get("sandbox_id", a["arguments"].get("sandboxId", ""))
            if sid:
                sandbox_ids.add(sid)
    return list(sandbox_ids)


def _categorize_action(tool_name: str, args: dict) -> str:
    """Categorize a tool call by what it's doing in the Conway/OpenClaw context."""
    cmd = args.get("command", "").lower()

    if tool_name == "sandbox_create":
        return "vm_provision"
    elif tool_name == "sandbox_delete":
        return "vm_teardown"
    elif tool_name == "sandbox_expose_port":
        return "vm_network"
    elif tool_name == "sandbox_exec":
        if "openclaw" in cmd:
            return "openclaw_setup" if ("install" in cmd or "onboard" in cmd) else "openclaw_action"
        elif "conway-terminal" in cmd or "npm install" in cmd:
            return "tool_install"
        elif "node " in cmd or "npm start" in cmd or "python" in cmd:
            return "service_deploy"
        elif "apt" in cmd or "curl" in cmd or "wget" in cmd:
            return "system_setup"
        return "sandbox_exec"
    elif tool_name in ("sandbox_write_file", "sandbox_read_file"):
        return "sandbox_file"
    elif tool_name == "browse_page":
        return "browsing"
    elif tool_name.startswith("x402_"):
        return "payment"
    elif tool_name in ("discover_agents", "send_message", "check_social_inbox"):
        return "agent_network"
    return "other"


@router.get("/status")
async def openclaw_status():
    """Overall status: Conway sandboxes + OpenClaw state derived from agent activity."""
    # Get all sandbox-related tool calls
    sandbox_tools = (
        "sandbox_create", "sandbox_exec", "sandbox_write_file", "sandbox_read_file",
        "sandbox_expose_port", "sandbox_list", "sandbox_delete",
    )
    sandbox_actions = _get_tool_calls(sandbox_tools, limit=200)

    # Derive OpenClaw state from sandbox_exec commands
    openclaw_state = _parse_openclaw_state(sandbox_actions)

    # Get active sandbox IDs from tool calls
    sandbox_ids = _extract_sandbox_ids(sandbox_actions)

    # Count sandbox operations
    total_sandbox_ops = len(sandbox_actions)
    creates = sum(1 for a in sandbox_actions if a["tool"] == "sandbox_create")
    execs = sum(1 for a in sandbox_actions if a["tool"] == "sandbox_exec")
    exposed = sum(1 for a in sandbox_actions if a["tool"] == "sandbox_expose_port")

    # Get live sandboxes from Conway API
    live_sandboxes = await _fetch_conway_sandboxes()

    return {
        "openclaw": openclaw_state,
        "sandbox_summary": {
            "known_sandbox_ids": sandbox_ids,
            "live_sandboxes": len(live_sandboxes),
            "total_operations": total_sandbox_ops,
            "creates": creates,
            "execs": execs,
            "ports_exposed": exposed,
        },
        "has_activity": total_sandbox_ops > 0,
    }


@router.get("/actions")
async def openclaw_actions(limit: int = 100):
    """All Conway sandbox + OpenClaw + browsing actions from agent turns."""
    all_tools = (
        "sandbox_create", "sandbox_exec", "sandbox_write_file", "sandbox_read_file",
        "sandbox_expose_port", "sandbox_list", "sandbox_delete",
        "browse_page", "x402_fetch", "x402_discover",
        "discover_agents", "send_message", "check_social_inbox",
        "install_mcp_server", "install_skill",
    )
    actions = _get_tool_calls(all_tools, limit=limit)

    # Add category to each action
    categorized = []
    categories = {}
    for a in actions:
        cat = _categorize_action(a["tool"], a["arguments"])
        a["category"] = cat
        categories[cat] = categories.get(cat, 0) + 1
        categorized.append(a)

    return {
        "actions": categorized,
        "total": len(categorized),
        "categories": categories,
    }


async def _fetch_conway_sandboxes() -> list:
    """Fetch live sandbox VMs from Conway API."""
    api_key = _get_conway_api_key()
    if not api_key:
        return []
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(
                "https://api.conway.tech/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("sandboxes", data if isinstance(data, list) else [])
    except Exception:
        pass
    return []


@router.get("/sandboxes")
async def openclaw_sandboxes():
    """Live Conway sandbox VMs — these are where OpenClaw runs."""
    live = await _fetch_conway_sandboxes()

    # Also get sandbox IDs from agent tool calls for cross-reference
    sandbox_tools = ("sandbox_create", "sandbox_exec", "sandbox_expose_port", "sandbox_list")
    sandbox_actions = _get_tool_calls(sandbox_tools, limit=100)
    known_ids = _extract_sandbox_ids(sandbox_actions)

    # Extract exposed ports/URLs from tool call results
    exposed_urls = []
    for a in sandbox_actions:
        if a["tool"] == "sandbox_expose_port":
            result = a["result"] or ""
            urls = re.findall(r'https?://[^\s"\'<>]+', result)
            for url in urls:
                exposed_urls.append({
                    "url": url,
                    "sandbox_id": a["arguments"].get("sandbox_id", ""),
                    "port": a["arguments"].get("port", ""),
                    "timestamp": a["timestamp"],
                })

    # Extract sandbox specs from create results
    created_sandboxes = []
    for a in sandbox_actions:
        if a["tool"] == "sandbox_create":
            result = a["result"] or ""
            try:
                r = json.loads(result)
                created_sandboxes.append({
                    "id": r.get("id", r.get("sandbox_id", "")),
                    "spec": a["arguments"],
                    "timestamp": a["timestamp"],
                    "status": "created",
                })
            except Exception:
                created_sandboxes.append({
                    "id": "unknown",
                    "spec": a["arguments"],
                    "timestamp": a["timestamp"],
                    "result_raw": result[:500],
                })

    return {
        "live_sandboxes": live,
        "created_sandboxes": created_sandboxes,
        "exposed_urls": exposed_urls,
        "known_sandbox_ids": known_ids,
        "total_live": len(live),
        "total_created": len(created_sandboxes),
    }


@router.get("/browsing")
async def browsing_sessions(limit: int = 50):
    """Browsing sessions — browse_page calls that go through OpenClaw in the Conway sandbox."""
    browse_actions = _get_tool_calls(("browse_page",), limit=limit)
    sessions = []
    for a in browse_actions:
        url = a["arguments"].get("url", a["arguments"].get("target", ""))
        sessions.append({
            "url": url,
            "timestamp": a["timestamp"],
            "duration_ms": a["duration_ms"],
            "result_preview": a["result"][:500] if a["result"] else "",
            "success": a["error"] is None,
            "error": a["error"],
        })
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/sandbox-exec-log")
async def sandbox_exec_log(limit: int = 50):
    """Raw sandbox_exec commands — shows what's being run inside Conway VMs.
    This includes OpenClaw installs, service deployments, system setup, etc."""
    exec_actions = _get_tool_calls(("sandbox_exec",), limit=limit)
    log = []
    for a in exec_actions:
        cmd = a["arguments"].get("command", "")
        sandbox_id = a["arguments"].get("sandbox_id", a["arguments"].get("sandboxId", ""))
        log.append({
            "command": cmd,
            "sandbox_id": sandbox_id,
            "output": a["result"],
            "duration_ms": a["duration_ms"],
            "error": a["error"],
            "timestamp": a["timestamp"],
            "category": _categorize_action("sandbox_exec", a["arguments"]),
        })
    return {"log": log, "total": len(log)}


@router.get("/sandbox/{sandbox_id}")
async def sandbox_detail(sandbox_id: str):
    """Detail view for a specific Conway sandbox VM."""
    api_key = _get_conway_api_key()

    # Try Conway API first
    live_data = None
    if api_key:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(
                    f"https://api.conway.tech/v1/sandboxes/{sandbox_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                ) as resp:
                    if resp.status == 200:
                        live_data = await resp.json()
        except Exception:
            pass

    # Get all tool calls for this sandbox from state.db
    all_tools = (
        "sandbox_create", "sandbox_exec", "sandbox_write_file", "sandbox_read_file",
        "sandbox_expose_port", "sandbox_delete",
    )
    all_actions = _get_tool_calls(all_tools, limit=500)
    sandbox_actions = [
        a for a in all_actions
        if a["arguments"].get("sandbox_id", a["arguments"].get("sandboxId", "")) == sandbox_id
        or (a["tool"] == "sandbox_create" and sandbox_id in (a["result"] or ""))
    ]

    # Derive OpenClaw state from this sandbox's execs
    openclaw_state = _parse_openclaw_state(sandbox_actions)

    # Extract exposed URLs
    exposed_urls = []
    for a in sandbox_actions:
        if a["tool"] == "sandbox_expose_port":
            urls = re.findall(r'https?://[^\s"\'<>]+', a["result"] or "")
            for url in urls:
                exposed_urls.append({"url": url, "port": a["arguments"].get("port", "")})

    return {
        "sandbox_id": sandbox_id,
        "live": live_data,
        "openclaw": openclaw_state,
        "exposed_urls": exposed_urls,
        "actions": sandbox_actions[:50],
        "total_actions": len(sandbox_actions),
    }
