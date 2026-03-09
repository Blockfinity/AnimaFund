"""
OpenClaw VM Viewer — real-time browsing sessions, actions, and sandbox state.
Reads from engine state.db (tool calls involving browse_page, sandbox_*, openclaw)
and from Conway API for live sandbox data.
"""
import os
import json
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])


def _get_conway_api_key() -> str:
    key = os.environ.get("CONWAY_API_KEY", "")
    if not key:
        for path in [
            os.path.expanduser("~/.anima/config.json"),
            os.path.expanduser("~/.conway/config.json"),
        ]:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        key = json.load(f).get("apiKey", "")
                    if key:
                        break
                except Exception:
                    pass
    return key


def _get_openclaw_config() -> dict:
    """Read the OpenClaw config to understand MCP server connections."""
    for path in [
        os.path.expanduser("~/.openclaw/config.json"),
        os.path.expanduser("~/.openclaw/openclaw.json"),
    ]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


def _get_browsing_actions(limit: int = 100) -> list:
    """Extract browsing-related tool calls from agent turns in state.db."""
    from engine_bridge import get_engine_db
    conn = get_engine_db()
    if not conn:
        return []
    try:
        # Tool names that involve browsing/openclaw/sandbox operations
        browse_tools = (
            "browse_page", "sandbox_create", "sandbox_exec", "sandbox_write_file",
            "sandbox_read_file", "sandbox_expose_port", "sandbox_list", "sandbox_delete",
            "x402_fetch", "x402_discover", "discover_agents", "send_message",
            "check_social_inbox", "install_mcp_server", "install_skill",
        )
        placeholders = ",".join(["?" for _ in browse_tools])
        cursor = conn.execute(f"""
            SELECT tc.id, tc.name, tc.arguments, tc.result, tc.duration_ms, tc.error,
                   t.timestamp, t.state
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ({placeholders})
            ORDER BY t.timestamp DESC, tc.rowid ASC
            LIMIT ?
        """, (*browse_tools, limit))

        actions = []
        for row in cursor.fetchall():
            args = {}
            try:
                args = json.loads(row["arguments"]) if row["arguments"] else {}
            except Exception:
                pass
            result_text = row["result"] or ""
            # Truncate very large results for display
            if len(result_text) > 2000:
                result_text = result_text[:2000] + "... [truncated]"

            actions.append({
                "id": row["id"],
                "tool": row["name"],
                "arguments": args,
                "result": result_text,
                "duration_ms": row["duration_ms"],
                "error": row["error"],
                "timestamp": row["timestamp"],
                "turn_state": row["state"],
                "category": _categorize_action(row["name"]),
            })
        conn.close()
        return actions
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return []


def _categorize_action(tool_name: str) -> str:
    if tool_name == "browse_page":
        return "browsing"
    elif tool_name.startswith("sandbox_"):
        return "sandbox"
    elif tool_name.startswith("x402_"):
        return "payment"
    elif tool_name in ("discover_agents", "send_message", "check_social_inbox"):
        return "network"
    elif tool_name in ("install_mcp_server", "install_skill"):
        return "tools"
    return "other"


@router.get("/status")
async def openclaw_status():
    """Get OpenClaw installation status and MCP config."""
    config = _get_openclaw_config()
    mcp_servers = config.get("mcpServers", {})

    # Check if OpenClaw binary exists
    import shutil
    openclaw_installed = shutil.which("openclaw") is not None
    conway_terminal_installed = shutil.which("conway-terminal") is not None

    return {
        "openclaw_installed": openclaw_installed,
        "conway_terminal_installed": conway_terminal_installed,
        "mcp_servers": list(mcp_servers.keys()),
        "mcp_config": {
            name: {"command": srv.get("command", ""), "has_env": bool(srv.get("env", {}))}
            for name, srv in mcp_servers.items()
        },
        "config_path": next(
            (p for p in [
                os.path.expanduser("~/.openclaw/config.json"),
                os.path.expanduser("~/.openclaw/openclaw.json"),
            ] if os.path.exists(p)),
            None,
        ),
    }


@router.get("/actions")
async def openclaw_actions(limit: int = 100):
    """Get browsing & sandbox actions from agent turns."""
    actions = _get_browsing_actions(limit)
    categories = {}
    for a in actions:
        cat = a["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "actions": actions,
        "total": len(actions),
        "categories": categories,
    }


@router.get("/sandboxes")
async def openclaw_sandboxes():
    """Get live sandbox VMs from Conway API."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"sandboxes": [], "error": "No Conway API key configured"}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(
                "https://api.conway.tech/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sandboxes = data if isinstance(data, list) else data.get("sandboxes", [])
                    return {"sandboxes": sandboxes, "total": len(sandboxes)}
                return {"sandboxes": [], "error": f"Conway API returned {resp.status}"}
    except Exception as e:
        return {"sandboxes": [], "error": str(e)}


@router.get("/browsing-sessions")
async def browsing_sessions(limit: int = 50):
    """Extract browse_page calls as browsing sessions with URL, content, timing."""
    actions = _get_browsing_actions(limit)
    sessions = []
    for a in actions:
        if a["tool"] == "browse_page":
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


@router.get("/sandbox/{sandbox_id}/live")
async def sandbox_live_view(sandbox_id: str):
    """Get live state of a specific sandbox VM."""
    api_key = _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            # Get sandbox details
            async with session.get(
                f"https://api.conway.tech/v1/sandboxes/{sandbox_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 200:
                    sandbox_data = await resp.json()
                    return {
                        "sandbox": sandbox_data,
                        "sandbox_id": sandbox_id,
                        "public_urls": sandbox_data.get("exposed_ports", []),
                    }
                return {"error": f"Sandbox not found or Conway returned {resp.status}"}
    except Exception as e:
        return {"error": str(e)}
