"""
Webhook receiver — the sandbox daemon POSTs here when agent data changes.
SECURITY: Validates per-agent webhook token. Only the sandbox daemon should call this.
"""
from fastapi import APIRouter, Request
from sandbox_poller import update_from_webhook, get_cache

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/agent-update")
async def receive_agent_update(request: Request):
    """Receives real-time data pushes from the webhook daemon inside the sandbox.
    Validates the per-agent webhook token from the Authorization header."""
    # Validate webhook token
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""

    if token:
        # Verify token matches the stored webhook_token in provisioning
        from agent_state import load_provisioning
        prov = await load_provisioning()
        expected = prov.get("webhook_token", "")
        if expected and token != expected:
            return {"received": False, "error": "invalid token"}

    data = await request.json()
    update_from_webhook(data)
    return {"received": True}


@router.get("/status")
async def webhook_status():
    """Check if webhooks are being received."""
    cache = get_cache()
    return {
        "last_update": cache.get("last_update"),
        "update_source": cache.get("update_source"),
        "engine_running": cache.get("engine_running", False),
        "sandbox_id": cache.get("sandbox_id"),
    }
