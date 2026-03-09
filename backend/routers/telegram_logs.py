"""
Telegram Log Ingestion — Fetches production agent logs from Telegram bot messages.

The production automaton sends detailed turn logs to Telegram via sendMessage.
This router fetches those messages using forwardMessage, stores them in MongoDB,
and serves them to the dashboard. This is the REAL production data pipeline.

NEVER deletes logs — all messages are persisted permanently.
"""
import os
import asyncio
import logging
import re
from datetime import datetime, timezone

import aiohttp
from fastapi import APIRouter, Query

from database import get_db

router = APIRouter(prefix="/api", tags=["telegram-logs"])
logger = logging.getLogger("telegram-logs")

# Background task handle
_ingest_task = None


def _get_bot_config(agent_id: str = None):
    """Get Telegram bot token and chat_id for the agent."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


async def _get_agent_bot_config(agent_id: str = None):
    """Get per-agent bot config from MongoDB."""
    if not agent_id or agent_id == "anima-fund":
        return _get_bot_config()
    try:
        db = get_db()
        agent = await db.agents.find_one(
            {"agent_id": agent_id},
            {"_id": 0, "telegram_bot_token": 1, "telegram_chat_id": 1}
        )
        if agent and agent.get("telegram_bot_token"):
            return agent["telegram_bot_token"], agent.get("telegram_chat_id", "")
    except Exception:
        pass
    return _get_bot_config()


def _parse_telegram_turn(text: str, message_id: int, date: int) -> dict:
    """Parse a Telegram message into a structured turn/log entry."""
    entry = {
        "message_id": message_id,
        "timestamp": datetime.fromtimestamp(date, tz=timezone.utc).isoformat(),
        "unix_ts": date,
        "raw_text": text,
        "type": "unknown",
        "state": "",
        "cost_cents": 0,
        "tool_calls": [],
        "thinking": "",
    }

    if not text:
        return entry

    # Parse TURN messages: "TURN | State: xxx | Cost: Xc"
    turn_match = re.match(r'TURN \| State: (\w+) \| Cost: (\d+)c', text)
    if turn_match:
        entry["type"] = "turn"
        entry["state"] = turn_match.group(1)
        entry["cost_cents"] = int(turn_match.group(2))

        # Parse tool calls from the message
        tool_pattern = re.compile(
            r'^(\w[\w_]+)\s+\((\d+)ms\)\s*\n((?:  .+\n)*?)(?:  Result: (.+?)(?:\n|$))?',
            re.MULTILINE
        )
        for m in tool_pattern.finditer(text):
            tc = {
                "tool": m.group(1),
                "duration_ms": int(m.group(2)),
                "args_text": m.group(3).strip() if m.group(3) else "",
                "result": m.group(4).strip() if m.group(4) else "",
            }
            # Parse error from result
            if tc["result"] and tc["result"].startswith("ERROR:"):
                tc["error"] = tc["result"]
                tc["result"] = ""
            entry["tool_calls"].append(tc)
        return entry

    # Parse STATE messages
    state_match = re.search(r'STATE: (\w+)', text)
    if state_match:
        entry["type"] = "state_change"
        entry["state"] = state_match.group(1).lower()
        return entry

    # Parse ENGINE messages
    if text.startswith("ENGINE STARTED"):
        entry["type"] = "engine_start"
        return entry

    # Parse HEARTBEAT
    if "HEARTBEAT" in text or "heartbeat" in text.lower():
        entry["type"] = "heartbeat"
        return entry

    # Parse WAKE UP
    if "WAKE UP" in text or "alive" in text.lower():
        entry["type"] = "wake"
        return entry

    # Parse SLEEP
    if "Sleeping" in text or "FATAL" in text:
        entry["type"] = "sleep"
        return entry

    # Parse ERROR
    if "ERROR" in text or "error" in text.lower():
        entry["type"] = "error"
        return entry

    # Parse FINANCE
    if "Credits" in text or "USDC" in text or "balance" in text.lower():
        entry["type"] = "finance"
        return entry

    entry["type"] = "info"
    return entry


async def _fetch_message(session, token, chat_id, message_id):
    """Forward a single message back to the same chat to read its content."""
    try:
        async with session.post(
            f"https://api.telegram.org/bot{token}/forwardMessage",
            json={
                "chat_id": chat_id,
                "from_chat_id": chat_id,
                "message_id": message_id,
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            data = await resp.json()
            if data.get("ok"):
                msg = data["result"]
                return {
                    "message_id": message_id,
                    "text": msg.get("text", ""),
                    "date": msg.get("forward_date", msg.get("date", 0)),
                }
    except Exception:
        pass
    return None


async def ingest_telegram_logs(agent_id: str = "anima-fund", batch_size: int = 50):
    """
    Fetch new Telegram messages and store in MongoDB.
    Uses a high-water mark (last known message_id) to only fetch new messages.
    NEVER deletes existing logs.
    """
    token, chat_id = await _get_agent_bot_config(agent_id)
    if not token or not chat_id:
        return {"ingested": 0, "error": "No Telegram config"}

    db = get_db()
    col = db["telegram_logs"]

    # Get the high-water mark — last ingested message_id
    await col.create_index([("message_id", -1)])
    await col.create_index([("agent_id", 1), ("message_id", -1)])

    last_doc = await col.find_one(
        {"agent_id": agent_id},
        sort=[("message_id", -1)],
        projection={"message_id": 1}
    )
    last_id = last_doc["message_id"] if last_doc else 0

    # Discover the latest message_id by sending a probe
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "[Dashboard] Syncing logs...",
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    return {"ingested": 0, "error": "Failed to probe latest message_id"}
                latest_id = data["result"]["message_id"]
        except Exception as e:
            return {"ingested": 0, "error": str(e)}

        # If no previous data, start from recent messages (last batch_size*2)
        if last_id == 0:
            start_id = max(1, latest_id - batch_size * 2)
        else:
            start_id = last_id + 1

        # Don't include our own probe messages
        end_id = latest_id - 1

        if start_id > end_id:
            return {"ingested": 0, "latest_id": latest_id}

        # Limit batch size to avoid rate limits
        if end_id - start_id > batch_size:
            start_id = end_id - batch_size + 1

        ingested = 0
        for mid in range(start_id, end_id + 1):
            msg = await _fetch_message(session, token, chat_id, mid)
            if msg and msg["text"]:
                # Skip our own dashboard probe messages
                if msg["text"].startswith("[Dashboard]") or msg["text"].startswith("[Anima Fund Dashboard]"):
                    continue

                parsed = _parse_telegram_turn(msg["text"], mid, msg["date"])
                parsed["agent_id"] = agent_id
                parsed["ingested_at"] = datetime.now(timezone.utc).isoformat()

                # Upsert to avoid duplicates
                await col.update_one(
                    {"agent_id": agent_id, "message_id": mid},
                    {"$set": parsed},
                    upsert=True,
                )
                ingested += 1

            # Small delay to avoid Telegram rate limits
            await asyncio.sleep(0.05)

        return {"ingested": ingested, "latest_id": latest_id, "range": f"{start_id}-{end_id}"}


async def _background_ingest_loop():
    """Background task that periodically ingests new Telegram logs."""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            result = await ingest_telegram_logs("anima-fund", batch_size=20)
            if result.get("ingested", 0) > 0:
                logger.info(f"Ingested {result['ingested']} new Telegram logs")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Telegram ingest error: {e}")
            await asyncio.sleep(60)


def start_ingest_background():
    """Start the background ingestion task."""
    global _ingest_task
    if _ingest_task is None or _ingest_task.done():
        _ingest_task = asyncio.create_task(_background_ingest_loop())
    return _ingest_task


def stop_ingest_background():
    """Stop the background ingestion task."""
    global _ingest_task
    if _ingest_task and not _ingest_task.done():
        _ingest_task.cancel()


# ─── API Endpoints ───


@router.post("/telegram-logs/ingest")
async def trigger_ingest(agent_id: str = "anima-fund", batch_size: int = 50):
    """Manually trigger Telegram log ingestion."""
    result = await ingest_telegram_logs(agent_id, batch_size)
    return result


@router.post("/telegram-logs/backfill")
async def backfill_logs(agent_id: str = "anima-fund", start_id: int = 1, end_id: int = 0, batch_size: int = 100):
    """Backfill historical Telegram logs from a specific range."""
    token, chat_id = await _get_agent_bot_config(agent_id)
    if not token or not chat_id:
        return {"error": "No Telegram config"}

    db = get_db()
    col = db["telegram_logs"]

    # If end_id not specified, probe for latest
    if end_id <= 0:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": "[Dashboard] Backfilling logs..."},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    end_id = data["result"]["message_id"] - 1

    ingested = 0
    async with aiohttp.ClientSession() as session:
        # Sample evenly across the range for large ranges
        total_range = end_id - start_id + 1
        if total_range > batch_size:
            step = total_range // batch_size
            ids = list(range(start_id, end_id + 1, step))[:batch_size]
        else:
            ids = list(range(start_id, end_id + 1))

        for mid in ids:
            msg = await _fetch_message(session, token, chat_id, mid)
            if msg and msg["text"]:
                if msg["text"].startswith("[Dashboard]") or msg["text"].startswith("[Anima Fund Dashboard]"):
                    continue
                parsed = _parse_telegram_turn(msg["text"], mid, msg["date"])
                parsed["agent_id"] = agent_id
                parsed["ingested_at"] = datetime.now(timezone.utc).isoformat()
                await col.update_one(
                    {"agent_id": agent_id, "message_id": mid},
                    {"$set": parsed},
                    upsert=True,
                )
                ingested += 1
            await asyncio.sleep(0.05)

    return {"ingested": ingested, "range": f"{start_id}-{end_id}", "sampled": len(ids)}


@router.get("/telegram-logs")
async def get_telegram_logs(
    agent_id: str = "anima-fund",
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    log_type: str = None,
):
    """Get stored Telegram logs. NEVER deletes — returns all stored logs."""
    db = get_db()
    col = db["telegram_logs"]

    query = {"agent_id": agent_id}
    if log_type:
        query["type"] = log_type

    total = await col.count_documents(query)
    logs = await col.find(
        query,
        {"_id": 0},
    ).sort("message_id", -1).skip(offset).limit(limit).to_list(limit)

    return {
        "logs": logs,
        "total": total,
        "offset": offset,
        "limit": limit,
        "source": "telegram",
    }


@router.get("/telegram-logs/stats")
async def get_telegram_stats(agent_id: str = "anima-fund"):
    """Get statistics about ingested Telegram logs."""
    db = get_db()
    col = db["telegram_logs"]

    total = await col.count_documents({"agent_id": agent_id})
    turns = await col.count_documents({"agent_id": agent_id, "type": "turn"})
    errors = await col.count_documents({"agent_id": agent_id, "type": "error"})
    state_changes = await col.count_documents({"agent_id": agent_id, "type": "state_change"})

    # Get latest and earliest message
    latest = await col.find_one({"agent_id": agent_id}, sort=[("message_id", -1)], projection={"_id": 0, "message_id": 1, "timestamp": 1})
    earliest = await col.find_one({"agent_id": agent_id}, sort=[("message_id", 1)], projection={"_id": 0, "message_id": 1, "timestamp": 1})

    # Calculate total cost
    pipeline = [
        {"$match": {"agent_id": agent_id, "type": "turn"}},
        {"$group": {"_id": None, "total_cost": {"$sum": "$cost_cents"}}},
    ]
    cost_result = await col.aggregate(pipeline).to_list(1)
    total_cost = cost_result[0]["total_cost"] if cost_result else 0

    return {
        "total_messages": total,
        "turns": turns,
        "errors": errors,
        "state_changes": state_changes,
        "total_cost_cents": total_cost,
        "latest": latest,
        "earliest": earliest,
        "source": "telegram",
    }


@router.get("/conway/balance")
async def get_conway_balance(agent_id: str = "anima-fund"):
    """Get REAL-TIME balance from Conway API — not cached local data."""
    # Try to get the Conway API key
    api_key = os.environ.get("CONWAY_API_KEY", "")

    # Also check agent's config file
    if not api_key:
        try:
            import json
            config_path = os.path.expanduser("~/.anima/config.json")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                    api_key = config.get("apiKey", "")
        except Exception:
            pass

    if not api_key:
        return {"error": "No Conway API key configured", "source": "conway_api"}

    result = {"source": "conway_api"}
    async with aiohttp.ClientSession() as session:
        # Fetch credits balance
        try:
            async with session.get(
                "https://api.conway.tech/v1/credits/balance",
                headers={"x-api-key": api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["credits_cents"] = data.get("credits_cents", 0)
                    result["credits_usd"] = data.get("credits_cents", 0) / 100
        except Exception:
            pass

        # Fetch sandboxes
        try:
            async with session.get(
                "https://api.conway.tech/v1/sandboxes",
                headers={"x-api-key": api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["sandboxes"] = data.get("sandboxes", [])
                    result["sandbox_count"] = data.get("count", 0)
        except Exception:
            pass

    return result
