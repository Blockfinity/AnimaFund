"""
Telegram notification routes — agent-aware, with health dashboard.
"""
import os
import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from telegram_notify import send_telegram, send_telegram_direct
from database import get_db

router = APIRouter(prefix="/api", tags=["telegram"])


class TelegramMessage(BaseModel):
    text: str
    agent_id: str = None


@router.post("/telegram/send")
async def telegram_send(msg: TelegramMessage):
    """Send a custom message to the agent's Telegram (or global default)."""
    ok = await send_telegram(msg.text, agent_id=msg.agent_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Telegram send failed. Check bot token and chat ID.")
    return {"success": True}


@router.get("/telegram/status")
async def telegram_status(agent_id: str = Query(default=None)):
    """Check Telegram config for a specific agent or the global default."""
    if agent_id and agent_id != "anima-fund":
        db = get_db()
        agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "telegram_bot_token": 1, "telegram_chat_id": 1, "name": 1})
        if agent:
            has_token = bool(agent.get("telegram_bot_token"))
            has_chat = bool(agent.get("telegram_chat_id"))
            return {
                "configured": has_token and has_chat,
                "bot_token_set": has_token,
                "chat_id_set": has_chat,
                "agent_id": agent_id,
                "uses_own_bot": has_token and has_chat,
            }
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return {
        "configured": bool(token and chat_id),
        "bot_token_set": bool(token),
        "chat_id_set": bool(chat_id),
        "agent_id": "anima-fund",
        "uses_own_bot": True,
    }


@router.post("/telegram/test/{agent_id}")
async def telegram_test(agent_id: str):
    """Send a test message to verify the agent's Telegram bot is working."""
    if agent_id == "anima-fund":
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        agent_name = "Anima Fund"
    else:
        db = get_db()
        agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        token = agent.get("telegram_bot_token")
        chat_id = agent.get("telegram_chat_id")
        agent_name = agent.get("name", agent_id)

    if not token or not chat_id:
        raise HTTPException(400, f"Agent '{agent_id}' has no Telegram bot configured")

    ok = await send_telegram_direct(
        f"<b>TEST</b> — Telegram bot verified for agent: <b>{agent_name}</b>",
        token=token,
        chat_id=chat_id,
    )
    if not ok:
        raise HTTPException(500, "Telegram test failed. Check bot token and chat ID are correct.")
    return {"success": True, "agent_id": agent_id, "message": f"Test message sent for {agent_name}"}


@router.get("/telegram/health")
async def telegram_health():
    """Return Telegram health for ALL agents — used by the dashboard."""
    db = get_db()
    agents = await db.agents.find({}, {"_id": 0}).to_list(100)

    # Track per-agent Telegram notification log from MongoDB
    results = []
    for agent in agents:
        agent_id = agent.get("agent_id", "unknown")
        is_default = agent.get("is_default", False)
        name = agent.get("name", agent_id)

        if is_default:
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        else:
            token = agent.get("telegram_bot_token", "")
            chat_id = agent.get("telegram_chat_id", "")

        configured = bool(token and chat_id)

        # Try to check bot health by calling getMe
        bot_alive = False
        bot_username = None
        if configured:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.telegram.org/bot{token}/getMe",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        data = await resp.json()
                        if data.get("ok"):
                            bot_alive = True
                            bot_username = data.get("result", {}).get("username", "")
            except Exception:
                pass

        # Get last notification log from MongoDB
        last_log = await db.telegram_logs.find_one(
            {"agent_id": agent_id},
            {"_id": 0},
            sort=[("timestamp", -1)],
        )

        results.append({
            "agent_id": agent_id,
            "name": name,
            "configured": configured,
            "bot_alive": bot_alive,
            "bot_username": f"@{bot_username}" if bot_username else None,
            "uses_own_bot": not is_default and configured,
            "last_message": last_log.get("message", None) if last_log else None,
            "last_message_time": last_log.get("timestamp", None) if last_log else None,
            "last_delivery_ok": last_log.get("success", None) if last_log else None,
        })

    return {"agents": results, "checked_at": datetime.now(timezone.utc).isoformat()}


@router.post("/telegram/log")
async def log_telegram_event(agent_id: str = Query(...), message: str = Query(""), success: bool = Query(True)):
    """Log a Telegram notification event (called by the backend monitor)."""
    db = get_db()
    await db.telegram_logs.insert_one({
        "agent_id": agent_id,
        "message": message[:500],
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"logged": True}

