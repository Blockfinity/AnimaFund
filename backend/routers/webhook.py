"""
Webhook receiver — the sandbox daemon POSTs here when agent data changes.
Instant updates, no polling delay.
"""
from fastapi import APIRouter, Request
from sandbox_poller import update_from_webhook, get_cache

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/agent-update")
async def receive_agent_update(request: Request):
    """Receives real-time data pushes from the webhook daemon inside the sandbox."""
    data = await request.json()
    update_from_webhook(data)
    return {"received": True}


@router.get("/status")
async def webhook_status():
    """Check if webhooks are being received."""
    cache = get_cache()
    return {
        "last_update": cache["last_update"],
        "update_source": cache["update_source"],
        "engine_running": cache["engine_running"],
        "sandbox_id": cache["sandbox_id"],
    }
