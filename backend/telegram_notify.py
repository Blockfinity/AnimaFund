"""
Telegram notification service for Anima Fund.
Sends real-time alerts to the creator's Telegram for agent events.
Supports per-agent Telegram bot tokens.
"""
import os
import aiohttp
import logging

logger = logging.getLogger("telegram")


def _get_global_config():
    """Get the global (default Anima Fund) Telegram config from env vars."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


async def _get_agent_config(agent_id: str = None):
    """Get per-agent Telegram config from MongoDB. Falls back to global for default agent."""
    if not agent_id or agent_id == "anima-fund":
        token, chat_id = _get_global_config()
        return token, chat_id

    try:
        from database import get_db
        db = get_db()
        agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "telegram_bot_token": 1, "telegram_chat_id": 1})
        if agent and agent.get("telegram_bot_token") and agent.get("telegram_chat_id"):
            return agent["telegram_bot_token"], agent["telegram_chat_id"]
    except Exception as e:
        logger.warning(f"Failed to get agent Telegram config: {e}")

    # Fallback to global only for backward compat
    token, chat_id = _get_global_config()
    return token, chat_id


async def send_telegram(text: str, parse_mode: str = "HTML", agent_id: str = None):
    """Send a message to the agent's (or global default) Telegram."""
    token, chat_id = await _get_agent_config(agent_id)
    if not token or not chat_id:
        return False

    api_url = f"https://api.telegram.org/bot{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram send failed: {data}")
                return data.get("ok", False)
    except Exception as e:
        logger.warning(f"Telegram error: {e}")
        return False


async def send_telegram_direct(text: str, token: str, chat_id: str, parse_mode: str = "HTML"):
    """Send using explicit token/chat_id (no DB lookup)."""
    if not token or not chat_id:
        return False
    api_url = f"https://api.telegram.org/bot{token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                return data.get("ok", False)
    except Exception as e:
        logger.warning(f"Telegram error: {e}")
        return False


async def notify_engine_started(wallet: str, creator_wallet: str, agent_id: str = None):
    await send_telegram(
        f"<b>ENGINE STARTED</b>\n"
        f"Agent wallet: <code>{wallet}</code>\n"
        f"Creator wallet: <code>{creator_wallet}</code>",
        agent_id=agent_id,
    )


async def notify_state_change(old_state: str, new_state: str, agent_id: str = None):
    icons = {
        "running": "🟢", "waking": "🔵", "sleeping": "😴",
        "critical": "🔴", "dead": "💀", "low_compute": "🟡",
        "setup": "⚙️",
    }
    icon = icons.get(new_state, "⚪")
    await send_telegram(f"{icon} <b>STATE: {new_state.upper()}</b>\n(was: {old_state})", agent_id=agent_id)


async def notify_balance_update(usdc: float, credits: float, eth: float, tier: str, agent_id: str = None):
    icons = {"high": "🟢", "normal": "🟢", "low_compute": "🟡", "critical": "🔴", "dead": "💀"}
    icon = icons.get(tier, "⚪")
    await send_telegram(
        f"{icon} <b>BALANCE UPDATE</b>\n"
        f"USDC: ${usdc:.2f}\n"
        f"Credits: ${credits:.2f}\n"
        f"ETH: {eth:.4f}\n"
        f"Tier: <b>{tier.upper()}</b>",
        agent_id=agent_id,
    )


async def notify_turn(turn_num: int, thinking: str, tools_used: list, agent_id: str = None):
    tools_str = ", ".join(tools_used[:5]) if tools_used else "none"
    think_preview = (thinking[:200] + "...") if thinking and len(thinking) > 200 else (thinking or "")
    await send_telegram(
        f"<b>TURN #{turn_num}</b>\n"
        f"Tools: {tools_str}\n"
        f"Thinking: {think_preview}",
        agent_id=agent_id,
    )


async def notify_transaction(tx_type: str, amount: float, to: str, details: str = "", agent_id: str = None):
    await send_telegram(
        f"💰 <b>TRANSACTION</b>\n"
        f"Type: {tx_type}\n"
        f"Amount: ${amount:.2f}\n"
        f"To: <code>{to}</code>\n"
        f"{details}",
        agent_id=agent_id,
    )


async def notify_error(error: str, agent_id: str = None):
    preview = (error[:300] + "...") if len(error) > 300 else error
    await send_telegram(f"⚠️ <b>ERROR</b>\n<code>{preview}</code>", agent_id=agent_id)


async def notify_skill_loaded(count: int, agent_id: str = None):
    await send_telegram(f"📚 <b>{count} skills loaded</b>", agent_id=agent_id)


async def notify_custom(message: str, agent_id: str = None):
    await send_telegram(message, agent_id=agent_id)
