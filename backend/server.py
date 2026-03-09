"""
Anima Fund - Autonomous AI-to-AI VC Fund Platform
FastAPI Backend Server

This server is a VIEWER — it reads from the Automaton engine's state.db and displays
whatever the AI has created. It does NOT prescribe structure, seed data, or make decisions.

The only write action is "Create Genesis Agent" which stages config files for the
Automaton engine and starts it via supervisor. The engine handles everything else:
wallet generation, API key provisioning, constitution, SOUL, skills, heartbeat.
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, close_db
from config import CREATOR_WALLET
from engine_bridge import (
    is_engine_live, get_live_identity,
    get_live_turns, get_live_kv_store,
    get_engine_logs,
)
from telegram_notify import notify_state_change, notify_turn, notify_error, send_telegram
from database import get_db
from payment_tracker import get_payment_status

from routers import agents, genesis, live, telegram, infrastructure, conway, openclaw

# ─── Telegram log monitor state ───
_monitor_task = None
_last_state = "unknown"
_last_turn_id = None
_last_activity_id = 0
_last_log_lines = 0


def _append_to_log(log_path: str, message: str):
    """Append a log line to the dashboard log file. Never deletes existing content."""
    try:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        with open(log_path, "a") as f:
            for line in message.split("\n"):
                if line.strip():
                    f.write(f"[{ts}] {line}\n")
    except Exception:
        pass


async def _monitor_engine_logs():
    """Background task that forwards ALL engine actions, logs, and tool calls 
    to BOTH the dashboard log files AND Telegram."""
    global _last_state, _last_turn_id, _last_activity_id, _last_log_lines
    while True:
        try:
            await asyncio.sleep(8)
            engine = is_engine_live()
            if not engine.get("db_exists"):
                continue

            # Determine active agent
            from engine_bridge import get_active_data_dir, get_live_activity, get_engine_logs
            get_active_data_dir()
            agent_id = None
            try:
                active_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_agent.txt")
                if os.path.exists(active_file):
                    with open(active_file, "r") as f:
                        agent_id = f.read().strip()
            except Exception:
                pass
            if not agent_id:
                agent_id = "anima-fund"

            # Resolve log file path for this agent
            if agent_id == "anima-fund":
                dashboard_log = "/var/log/automaton.out.log"
            else:
                agent_home = os.path.dirname(get_active_data_dir())
                dashboard_log = os.path.join(agent_home, "engine.out.log")

            # 1. Forward state changes
            identity = get_live_identity()
            current_state = identity.get("state", engine.get("agent_state", "unknown"))
            if current_state != _last_state and _last_state != "unknown":
                await notify_state_change(_last_state, current_state, agent_id=agent_id)
                # Also write state change to dashboard log
                _append_to_log(dashboard_log, f"[STATE] State changed: {_last_state} -> {current_state}")
            _last_state = current_state

            # 2. Forward ALL new turns with full details (thinking + tool calls + results)
            turns = get_live_turns(limit=5)
            if turns:
                # Turns are returned newest first — process oldest new ones first
                new_turns = []
                for t in reversed(turns):
                    if _last_turn_id is None or t["turn_id"] != _last_turn_id:
                        if _last_turn_id is None:
                            _last_turn_id = t["turn_id"]
                            break  # Skip first run to avoid spamming old turns
                        new_turns.append(t)

                for turn in new_turns:
                    _last_turn_id = turn["turn_id"]
                    # Build detailed turn message
                    thinking = (turn.get("thinking") or "")[:300]
                    tools = turn.get("tool_calls", [])
                    cost = turn.get("cost_cents", 0)

                    msg_parts = [f"<b>TURN</b> | State: {turn.get('state', '?')} | Cost: {cost}c"]
                    if thinking:
                        msg_parts.append(f"\n<b>Thinking:</b> {thinking}{'...' if len(turn.get('thinking', '')) > 300 else ''}")

                    # Plain text version for dashboard log (no HTML tags)
                    log_parts = [f"TURN | State: {turn.get('state', '?')} | Cost: {cost}c"]
                    if thinking:
                        log_parts.append(f"  Thinking: {thinking}{'...' if len(turn.get('thinking', '')) > 300 else ''}")

                    for tc in tools[:6]:
                        tool_name = tc.get("tool", "?")
                        args = tc.get("arguments", {})
                        result = (tc.get("result") or "")[:200]
                        error = tc.get("error", "")
                        duration = tc.get("duration_ms", 0)

                        # Show the most useful argument (first key-value)
                        arg_preview = ""
                        if isinstance(args, dict):
                            for k, v in list(args.items())[:2]:
                                val = str(v)[:80]
                                arg_preview += f"\n  {k}: {val}"

                        tc_msg = f"\n<b>{tool_name}</b> ({duration}ms)"
                        tc_log = f"\n  {tool_name} ({duration}ms)"
                        if arg_preview:
                            tc_msg += arg_preview
                            tc_log += arg_preview
                        if error:
                            tc_msg += f"\n  ERROR: {error[:150]}"
                            tc_log += f"\n  ERROR: {error[:150]}"
                        elif result:
                            tc_msg += f"\n  Result: {result[:200]}"
                            tc_log += f"\n  Result: {result[:200]}"
                        msg_parts.append(tc_msg)
                        log_parts.append(tc_log)

                    if len(tools) > 6:
                        msg_parts.append(f"\n... +{len(tools) - 6} more tool calls")
                        log_parts.append(f"\n... +{len(tools) - 6} more tool calls")

                    full_msg = "\n".join(msg_parts)
                    # Telegram has 4096 char limit
                    if len(full_msg) > 4000:
                        full_msg = full_msg[:3997] + "..."

                    # Write to BOTH: dashboard log file AND Telegram
                    _append_to_log(dashboard_log, "\n".join(log_parts))
                    await send_telegram(full_msg, agent_id=agent_id)

            # 3. Forward engine log errors (stderr)
            try:
                logs = get_engine_logs()
                stderr = logs.get("stderr", "")
                if stderr:
                    err_lines = [line.strip() for line in stderr.split("\n") if line.strip()]
                    new_errors = err_lines[_last_log_lines:] if _last_log_lines < len(err_lines) else []
                    _last_log_lines = len(err_lines)
                    if new_errors:
                        err_msg = "\n".join(new_errors[-5:])  # Last 5 new error lines
                        await notify_error(err_msg, agent_id=agent_id)
            except Exception:
                pass

        except Exception as e:
            logging.getLogger("monitor").warning(f"Monitor error: {e}")
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitor_task
    init_db()
    _monitor_task = asyncio.create_task(_monitor_engine_logs())
    yield
    if _monitor_task:
        _monitor_task.cancel()
    close_db()


app = FastAPI(title="Anima Fund API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# INCLUDE ROUTERS
# ═══════════════════════════════════════════════════════════
app.include_router(agents.router)
app.include_router(genesis.router)
app.include_router(live.router)
app.include_router(telegram.router)
app.include_router(infrastructure.router)
app.include_router(conway.router)
app.include_router(openclaw.router)


# ═══════════════════════════════════════════════════════════
# HEALTH & PAYMENTS (kept in main for simplicity)
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    engine = is_engine_live()
    return {
        "status": "ok",
        "engine_live": engine.get("live", False),
        "engine_db_exists": engine.get("db_exists", False),
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/payments/status")
async def payments_status():
    """Real-time payment compliance check."""
    return get_payment_status()
