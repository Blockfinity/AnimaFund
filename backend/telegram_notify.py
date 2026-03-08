"""
Telegram notification service for Anima Fund.
Sends real-time alerts to the creator's Telegram for agent events.
"""
import os
import aiohttp
import logging

logger = logging.getLogger("telegram")


def _get_config():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    api_url = f"https://api.telegram.org/bot{token}" if token else None
    return api_url, chat_id


async def send_telegram(text: str, parse_mode: str = "HTML"):
    """Send a message to the creator's Telegram."""
    api_url, chat_id = _get_config()
    if not api_url or not chat_id:
        return False
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


async def notify_engine_started(wallet: str, creator_wallet: str):
    await send_telegram(
        f"<b>ENGINE STARTED</b>\n"
        f"Agent wallet: <code>{wallet}</code>\n"
        f"Creator wallet: <code>{creator_wallet}</code>"
    )


async def notify_state_change(old_state: str, new_state: str):
    icons = {
        "running": "🟢", "waking": "🔵", "sleeping": "😴",
        "critical": "🔴", "dead": "💀", "low_compute": "🟡",
        "setup": "⚙️",
    }
    icon = icons.get(new_state, "⚪")
    await send_telegram(f"{icon} <b>STATE: {new_state.upper()}</b>\n(was: {old_state})")


async def notify_balance_update(usdc: float, credits: float, eth: float, tier: str):
    icons = {"high": "🟢", "normal": "🟢", "low_compute": "🟡", "critical": "🔴", "dead": "💀"}
    icon = icons.get(tier, "⚪")
    await send_telegram(
        f"{icon} <b>BALANCE UPDATE</b>\n"
        f"USDC: ${usdc:.2f}\n"
        f"Credits: ${credits:.2f}\n"
        f"ETH: {eth:.4f}\n"
        f"Tier: <b>{tier.upper()}</b>"
    )


async def notify_turn(turn_num: int, thinking: str, tools_used: list):
    tools_str = ", ".join(tools_used[:5]) if tools_used else "none"
    think_preview = (thinking[:200] + "...") if thinking and len(thinking) > 200 else (thinking or "")
    await send_telegram(
        f"<b>TURN #{turn_num}</b>\n"
        f"Tools: {tools_str}\n"
        f"Thinking: {think_preview}"
    )


async def notify_transaction(tx_type: str, amount: float, to: str, details: str = ""):
    await send_telegram(
        f"💰 <b>TRANSACTION</b>\n"
        f"Type: {tx_type}\n"
        f"Amount: ${amount:.2f}\n"
        f"To: <code>{to}</code>\n"
        f"{details}"
    )


async def notify_error(error: str):
    preview = (error[:300] + "...") if len(error) > 300 else error
    await send_telegram(f"⚠️ <b>ERROR</b>\n<code>{preview}</code>")


async def notify_skill_loaded(count: int):
    await send_telegram(f"📚 <b>{count} skills loaded</b>")


async def notify_custom(message: str):
    await send_telegram(message)
