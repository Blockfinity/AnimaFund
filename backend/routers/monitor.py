"""
Monitor router — Serves real agent data to ALL dashboard pages.
Replaces genesis.py + live.py + infrastructure.py with one clean router.
Reads from agent_state_store (populated by StateReportingToolkit via webhook).
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agent_state_store import get_agent_state, get_all_agent_states
from agent_state import get_active_agent_id, load_provisioning
from database import get_db

router = APIRouter(prefix="/api", tags=["monitor"])


# ─── Engine / Genesis endpoints (used by AgentMind page) ───

@router.get("/engine/status")
async def engine_status():
    """Engine status for the active agent."""
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {
        "status": "running" if state.get("engine_running") else "offline",
        "agent_id": agent_id,
        "message": state.get("message", ""),
        "goal_progress": state.get("goal_progress", 0.0),
        "last_update": state.get("last_update"),
        "db_connected": True,
        "turns": len(state.get("actions", [])),
        "agents": 1,
        "log_lines": len(state.get("actions", [])),
    }


@router.get("/engine/logs")
async def engine_logs(limit: int = 50, lines: int = 100):
    """Recent agent actions as log entries. Returns stdout/stderr format for frontend."""
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    actions = state.get("actions", [])[-max(limit, lines):]
    errors = state.get("errors", [])[-20:]

    # Format as stdout lines (what the frontend expects)
    stdout_lines = []
    for a in actions:
        ts = a.get("timestamp", "")
        tool = a.get("tool_name", "")
        msg = a.get("action", "")
        result = a.get("result", "")
        if tool:
            stdout_lines.append(f"[{ts}] TOOL: {tool} — {msg}")
            if result:
                stdout_lines.append(f"[{ts}] RESULT: {result[:200]}")
        else:
            stdout_lines.append(f"[{ts}] {msg}")

    stderr_lines = []
    for e in errors:
        stderr_lines.append(f"[{e.get('timestamp', '')}] {e.get('severity', 'ERROR').upper()}: {e.get('error', '')}")

    return {
        "stdout": "\n".join(stdout_lines),
        "stderr": "\n".join(stderr_lines),
        "logs": [{"timestamp": a.get("timestamp"), "type": "tool" if a.get("tool_name") else "action", "tool": a.get("tool_name", ""), "message": a.get("action", "")} for a in actions],
        "total": len(actions),
    }


@router.get("/engine/live")
async def engine_live():
    """Live engine data for the active agent. Fields must match frontend expectations."""
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    is_running = state.get("engine_running", False)
    actions = state.get("actions", [])
    return {
        # Fields the frontend expects
        "agent_state": state.get("status", "offline"),
        "db_exists": True,
        "live": is_running,
        "turn_count": len(actions),
        "agent_count": 1,
        "log_line_count": len(actions),
        # Extra data
        "engine_running": is_running,
        "status": state.get("status", "unknown"),
        "message": state.get("message", ""),
        "actions": actions[-20:],
        "errors": state.get("errors", [])[-10:],
    }


@router.get("/genesis/prompt-template")
async def genesis_prompt_template():
    """Get the genesis prompt for the active agent."""
    agent_id = get_active_agent_id()
    db = get_db()
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "genesis_prompt": 1})
    return {"prompt": agent.get("genesis_prompt", "") if agent else ""}


@router.get("/genesis/status")
async def genesis_status():
    """Get agent status — used by the frontend's status poller."""
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    prov = await load_provisioning()
    # Dashboard shows CORE wallet (from provisioning), not agent-reported public wallet
    core_wallet = prov.get("wallet_address", "")
    return {
        "status": state.get("status", "unknown"),
        "engine_running": state.get("engine_running", False),
        "message": state.get("message", ""),
        "wallet_address": core_wallet,
        "sandbox_id": prov.get("sandbox", {}).get("id"),
        "sandbox_status": prov.get("sandbox", {}).get("status", "none"),
        "last_update": state.get("last_update"),
    }


@router.get("/constitution")
async def get_constitution():
    """Get the constitution."""
    import os
    from config import ENGINE_DIR
    path = os.path.join(ENGINE_DIR, "templates", "constitution.md")
    if os.path.exists(path):
        with open(path) as f:
            return {"content": f.read()}
    return {"content": ""}


# ─── Live endpoints (used by multiple dashboard pages) ───

@router.get("/live/stream")
async def live_stream(request: Request):
    """SSE stream of agent state updates."""
    agent_id = get_active_agent_id()

    async def event_generator():
        last_update = None
        while True:
            if await request.is_disconnected():
                break
            state = get_agent_state(agent_id)
            current_update = state.get("last_update")
            if current_update != last_update:
                last_update = current_update
                yield f"data: {json.dumps(state, default=str)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/live/heartbeat")
async def heartbeat():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {
        "alive": state.get("engine_running", False),
        "agent_id": agent_id,
        "last_update": state.get("last_update"),
    }


@router.get("/live/heartbeat-schedule")
async def heartbeat_schedule():
    return {"interval_seconds": 30}


@router.get("/live/identity")
async def live_identity():
    agent_id = get_active_agent_id()
    db = get_db()
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "name": 1, "agent_id": 1})
    return agent or {"agent_id": agent_id, "name": agent_id}


@router.get("/live/soul")
async def live_soul():
    agent_id = get_active_agent_id()
    db = get_db()
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "genesis_prompt": 1})
    return {"soul": agent.get("genesis_prompt", "") if agent else ""}


@router.get("/live/financials")
async def live_financials():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    fin = state.get("financials", {})
    return {
        "wallet_address": fin.get("wallet_address", ""),
        "usdc_balance": fin.get("usdc_balance", 0.0),
        "revenue": fin.get("revenue", 0.0),
        "expenses": fin.get("expenses", 0.0),
        "credits": 0.0,
        "eth_balance": 0.0,
    }


@router.get("/live/transactions")
async def live_transactions():
    return {"transactions": []}


@router.get("/live/turns")
async def live_turns():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {"turns": len(state.get("actions", [])), "details": state.get("actions", [])[-20:]}


@router.get("/live/messages")
async def live_messages():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    msgs = []
    for a in state.get("actions", [])[-30:]:
        msgs.append({"role": "agent", "content": a.get("action", ""), "timestamp": a.get("timestamp", "")})
    return {"messages": msgs}


@router.get("/live/activity")
async def live_activity():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {"activity": state.get("actions", [])[-50:]}


@router.get("/live/agents")
async def live_agents():
    states = get_all_agent_states()
    return {"agents": [
        {"agent_id": aid, "status": s.get("status"), "engine_running": s.get("engine_running", False)}
        for aid, s in states.items()
    ]}


@router.get("/live/discovered")
async def live_discovered():
    return {"discovered": []}


@router.get("/live/kv")
async def live_kv():
    return {"kv": {}}


@router.get("/live/memory")
async def live_memory():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {"memories": [], "agent_id": agent_id}


@router.get("/live/wake-events")
async def live_wake_events():
    return {"events": []}


@router.get("/live/skills-full")
async def live_skills_full():
    return {"skills": []}


# ─── Infrastructure endpoints ───

@router.get("/infrastructure/overview")
async def infra_overview():
    agent_id = get_active_agent_id()
    prov = await load_provisioning()
    state = get_agent_state(agent_id)
    return {
        "agent_id": agent_id,
        "sandbox": prov.get("sandbox", {}),
        "engine_running": state.get("engine_running", False),
        "tools_installed": list(prov.get("tools", {}).keys()),
        "ports": prov.get("ports", []),
        "domains": prov.get("domains", []),
    }


@router.get("/infrastructure/sandboxes")
async def infra_sandboxes():
    prov = await load_provisioning()
    sandbox = prov.get("sandbox", {})
    if sandbox.get("id"):
        return {"sandboxes": [sandbox]}
    return {"sandboxes": []}


@router.get("/infrastructure/installed-tools")
async def infra_tools():
    prov = await load_provisioning()
    return {"tools": prov.get("tools", {})}


@router.get("/infrastructure/domains")
async def infra_domains():
    prov = await load_provisioning()
    return {"domains": prov.get("domains", [])}


@router.get("/infrastructure/terminal")
async def infra_terminal():
    prov = await load_provisioning()
    return {"terminal_url": prov.get("sandbox", {}).get("terminal_url", "")}


@router.get("/infrastructure/activity-feed")
async def infra_activity():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    return {"feed": state.get("actions", [])[-20:]}


# ─── Wallet endpoint ───

@router.get("/wallet/balance")
async def wallet_balance():
    agent_id = get_active_agent_id()
    state = get_agent_state(agent_id)
    fin = state.get("financials", {})
    prov = await load_provisioning()
    # Dashboard shows CORE wallet address (from provisioning record)
    core_wallet = prov.get("wallet_address", "")
    return {
        "wallet_address": core_wallet,
        "usdc_balance": fin.get("usdc_balance", 0.0),
        "eth_balance": 0.0,
        "credits": 0.0,
    }
