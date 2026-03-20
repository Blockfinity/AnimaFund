"""
Agent State Store — Per-agent state backed by MongoDB.
Handles: multiple agents, server restarts, concurrent updates.
Dashboard reads from here. StateReportingToolkit writes here via webhook.
"""
import logging
from datetime import datetime, timezone
from collections import defaultdict
from database import get_db

logger = logging.getLogger(__name__)

# In-memory cache per agent (fast reads, populated from webhook + MongoDB)
_agent_states = defaultdict(lambda: {
    "status": "unknown",
    "engine_running": False,
    "message": "",
    "goal_progress": 0.0,
    "actions": [],
    "errors": [],
    "financials": {},
    "last_update": None,
})


def get_agent_state(agent_id: str) -> dict:
    """Get current state for one agent."""
    return dict(_agent_states[agent_id])


def get_all_agent_states() -> dict:
    """Get states for all agents."""
    return {k: dict(v) for k, v in _agent_states.items()}


async def update_agent_state(agent_id: str, data: dict):
    """Update state for one agent from webhook data. Writes to cache + MongoDB."""
    state = _agent_states[agent_id]
    update_type = data.get("type", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    if update_type == "state":
        state["status"] = data.get("status", state["status"])
        state["engine_running"] = data.get("engine_running", state["engine_running"])
        state["message"] = data.get("message", "")
        state["goal_progress"] = data.get("goal_progress", state["goal_progress"])

    elif update_type == "action":
        action_entry = {
            "action": data.get("action", ""),
            "tool_name": data.get("tool_name", ""),
            "result": data.get("result", ""),
            "timestamp": now,
        }
        state["actions"].append(action_entry)
        state["actions"] = state["actions"][-100:]  # Keep last 100

    elif update_type == "error":
        error_entry = {
            "error": data.get("error", ""),
            "severity": data.get("severity", "warning"),
            "timestamp": now,
        }
        state["errors"].append(error_entry)
        state["errors"] = state["errors"][-50:]

    elif update_type == "financial":
        state["financials"] = {
            "wallet_address": data.get("wallet_address", ""),
            "usdc_balance": data.get("usdc_balance", 0.0),
            "revenue": data.get("revenue", 0.0),
            "expenses": data.get("expenses", 0.0),
            "updated_at": now,
        }

    state["last_update"] = now
    _agent_states[agent_id] = state

    # Persist to MongoDB (async, non-blocking for cache reads)
    try:
        db = get_db()
        if db is not None:
            await db.agent_states.update_one(
                {"agent_id": agent_id},
                {"$set": {"agent_id": agent_id, **state}},
                upsert=True,
            )
    except Exception as e:
        logger.warning(f"Failed to persist agent state to MongoDB: {e}")


async def load_states_from_db():
    """Load all agent states from MongoDB on server startup."""
    try:
        db = get_db()
        if db is not None:
            async for doc in db.agent_states.find({}, {"_id": 0}):
                agent_id = doc.get("agent_id")
                if agent_id:
                    _agent_states[agent_id].update(doc)
            logger.info(f"Loaded {len(_agent_states)} agent states from MongoDB")
    except Exception as e:
        logger.warning(f"Failed to load agent states from MongoDB: {e}")
