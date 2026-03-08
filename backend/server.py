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
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, close_db
from config import CREATOR_WALLET
from engine_bridge import (
    is_engine_live, get_live_identity,
    get_live_turns, get_live_kv_store,
)
from telegram_notify import notify_state_change, notify_turn
from database import get_db
from payment_tracker import get_payment_status

from routers import agents, genesis, live, telegram

# ─── Telegram log monitor state ───
_monitor_task = None
_last_state = "unknown"
_last_turn_count = 0
_last_balance_tier = ""


async def _monitor_engine_logs():
    """Background task that watches engine state and sends Telegram notifications to the ACTIVE agent's bot."""
    global _last_state, _last_turn_count, _last_balance_tier
    while True:
        try:
            await asyncio.sleep(15)
            engine = is_engine_live()
            if not engine.get("db_exists"):
                continue

            # Determine which agent is currently active
            from engine_bridge import get_active_data_dir
            get_active_data_dir()  # ensure module is loaded
            agent_id = None
            # Try to find the agent_id from active_agent.txt or dir path
            try:
                with open("/tmp/anima_active_agent_dir", "r") as f:
                    d = f.read().strip()
                    if "agents/" in d:
                        agent_id = d.split("agents/")[-1].split("/")[0]
            except Exception:
                pass
            if not agent_id:
                agent_id = "anima-fund"  # Default

            identity = get_live_identity()
            current_state = identity.get("state", "unknown")
            if current_state != _last_state and _last_state != "unknown":
                await notify_state_change(_last_state, current_state, agent_id=agent_id)
                # Log the notification
                try:
                    db = get_db()
                    await db.telegram_logs.insert_one({
                        "agent_id": agent_id,
                        "message": f"State: {_last_state} -> {current_state}",
                        "success": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception:
                    pass
            _last_state = current_state

            turns = get_live_turns(limit=1)
            if turns:
                latest = turns[0]
                turn_num = latest.get("turn_number", 0)
                if turn_num > _last_turn_count:
                    tools = latest.get("tool_names", "").split(",") if latest.get("tool_names") else []
                    thinking = latest.get("thinking", "")
                    await notify_turn(turn_num, thinking, tools, agent_id=agent_id)
                    # Log the notification
                    try:
                        db = get_db()
                        await db.telegram_logs.insert_one({
                            "agent_id": agent_id,
                            "message": f"Turn #{turn_num}: {', '.join(tools[:3])}",
                            "success": True,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    except Exception:
                        pass
                    _last_turn_count = turn_num

            kv = get_live_kv_store()
            tier = ""
            for item in kv:
                if item.get("key") == "survival_tier":
                    tier = item.get("value", "")
                    break
            if tier and tier != _last_balance_tier:
                _last_balance_tier = tier

        except Exception:
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
