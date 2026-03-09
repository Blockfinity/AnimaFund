"""
Agent Log Webhook — Receives turn/action logs directly from the production agent.

The agent sends structured log data to this endpoint after each turn.
This is the PRIMARY data source for the dashboard — not Telegram forwarding.
Logs are NEVER deleted. All data is persisted in MongoDB permanently.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from database import get_db

router = APIRouter(prefix="/api", tags=["agent-logs"])
logger = logging.getLogger("agent-logs")


class AgentLogEntry(BaseModel):
    agent_id: str = "anima-fund"
    turn: Optional[int] = None
    state: Optional[str] = None
    cost_cents: Optional[int] = None
    tool_calls: Optional[list] = None
    thinking: Optional[str] = None
    message: Optional[str] = None
    log_type: str = "turn"  # turn, error, heartbeat, state_change, finance, info
    balance_credits: Optional[float] = None
    balance_usdc: Optional[float] = None
    tier: Optional[str] = None


@router.post("/agent-logs/webhook")
async def receive_agent_log(entry: AgentLogEntry):
    """
    Webhook endpoint that the agent calls directly to report its activity.
    The agent POSTs here after each turn/action, same as it sends to Telegram.
    """
    db = get_db()
    col = db["agent_logs"]

    doc = {
        "agent_id": entry.agent_id,
        "turn": entry.turn,
        "state": entry.state,
        "cost_cents": entry.cost_cents,
        "tool_calls": entry.tool_calls or [],
        "thinking": entry.thinking or "",
        "message": entry.message or "",
        "log_type": entry.log_type,
        "balance_credits": entry.balance_credits,
        "balance_usdc": entry.balance_usdc,
        "tier": entry.tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await col.insert_one(doc)

    return {"ok": True}


@router.post("/agent-logs/bulk")
async def receive_bulk_logs(request: Request):
    """
    Bulk webhook — agent sends multiple log entries at once.
    Accepts a JSON array of log entries.
    """
    db = get_db()
    col = db["agent_logs"]

    body = await request.json()
    entries = body if isinstance(body, list) else [body]

    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for e in entries:
        docs.append({
            "agent_id": e.get("agent_id", "anima-fund"),
            "turn": e.get("turn"),
            "state": e.get("state"),
            "cost_cents": e.get("cost_cents"),
            "tool_calls": e.get("tool_calls", []),
            "thinking": e.get("thinking", ""),
            "message": e.get("message", ""),
            "log_type": e.get("log_type", "info"),
            "balance_credits": e.get("balance_credits"),
            "balance_usdc": e.get("balance_usdc"),
            "tier": e.get("tier"),
            "timestamp": e.get("timestamp", now),
        })

    if docs:
        await col.insert_many(docs)

    return {"ok": True, "ingested": len(docs)}


@router.get("/agent-logs")
async def get_agent_logs(
    agent_id: str = "anima-fund",
    limit: int = 200,
    offset: int = 0,
    log_type: str = None,
):
    """Get agent logs. NEVER deletes — returns all stored logs."""
    db = get_db()
    col = db["agent_logs"]

    await col.create_index([("agent_id", 1), ("timestamp", -1)])

    query = {"agent_id": agent_id}
    if log_type:
        query["log_type"] = log_type

    total = await col.count_documents(query)
    logs = await col.find(
        query,
        {"_id": 0},
    ).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)

    return {
        "logs": logs,
        "total": total,
        "offset": offset,
        "limit": limit,
        "source": "agent_webhook",
    }


@router.get("/agent-logs/stats")
async def get_agent_log_stats(agent_id: str = "anima-fund"):
    """Get statistics about received agent logs."""
    db = get_db()
    col = db["agent_logs"]

    total = await col.count_documents({"agent_id": agent_id})
    turns = await col.count_documents({"agent_id": agent_id, "log_type": "turn"})
    errors = await col.count_documents({"agent_id": agent_id, "log_type": "error"})

    # Total cost
    pipeline = [
        {"$match": {"agent_id": agent_id, "cost_cents": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "total_cost": {"$sum": "$cost_cents"}}},
    ]
    cost_result = await col.aggregate(pipeline).to_list(1)
    total_cost = cost_result[0]["total_cost"] if cost_result else 0

    # Latest log
    latest = await col.find_one(
        {"agent_id": agent_id},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "timestamp": 1, "state": 1, "log_type": 1}
    )

    # Latest balance
    latest_balance = await col.find_one(
        {"agent_id": agent_id, "balance_credits": {"$exists": True, "$ne": None}},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "balance_credits": 1, "balance_usdc": 1, "tier": 1, "timestamp": 1}
    )

    return {
        "total_logs": total,
        "turns": turns,
        "errors": errors,
        "total_cost_cents": total_cost,
        "latest": latest,
        "latest_balance": latest_balance,
        "source": "agent_webhook",
    }
