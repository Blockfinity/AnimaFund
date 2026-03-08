"""
Telegram notification routes.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telegram_notify import send_telegram

router = APIRouter(prefix="/api", tags=["telegram"])


class TelegramMessage(BaseModel):
    text: str


@router.post("/telegram/send")
async def telegram_send(msg: TelegramMessage):
    """Send a custom message to the creator's Telegram."""
    ok = await send_telegram(msg.text)
    if not ok:
        raise HTTPException(status_code=500, detail="Telegram send failed. Check bot token and chat ID.")
    return {"success": True}


@router.get("/telegram/status")
async def telegram_status():
    """Check if Telegram notifications are configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return {
        "configured": bool(token and chat_id),
        "bot_token_set": bool(token),
        "chat_id_set": bool(chat_id),
    }
