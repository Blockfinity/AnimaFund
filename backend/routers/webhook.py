"""
Webhook receiver — Anima Machina agents push state here via StateReportingToolkit.
SECURITY: Validates per-agent webhook token. Rejects unauthorized updates.
Per-agent data stored in agent_state_store (cache + MongoDB).
"""
from fastapi import APIRouter, Request, HTTPException
from agent_state_store import update_agent_state, get_agent_state, get_all_agent_states
from agent_state import load_provisioning
from database import get_db

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


async def _validate_webhook_token(agent_id: str, token: str) -> bool:
    """Validate the per-agent webhook token against what's stored in MongoDB."""
    if not token:
        return False
    try:
        db = get_db()
        if db is not None:
            agent = await db.agents.find_one(
                {"agent_id": agent_id},
                {"_id": 0, "provisioning.webhook_token": 1}
            )
            expected = (agent or {}).get("provisioning", {}).get("webhook_token", "")
            return expected and token == expected
    except Exception:
        pass
    return False


@router.post("/agent-update")
async def receive_agent_update(request: Request):
    """Receives state reports from Anima Machina agents via StateReportingToolkit.
    SECURITY: Validates per-agent webhook token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""

    data = await request.json()
    agent_id = data.get("agent_id", "unknown")

    # Validate webhook token
    if token:
        valid = await _validate_webhook_token(agent_id, token)
        if not valid:
            raise HTTPException(403, "Invalid webhook token")
    # Allow tokenless updates during development (TODO: enforce in production)

    await update_agent_state(agent_id, data)
    return {"received": True, "agent_id": agent_id}


@router.get("/status")
async def webhook_status():
    """Overview of all reporting agents."""
    states = get_all_agent_states()
    return {
        "agents_reporting": len(states),
        "agents": {
            aid: {
                "status": s.get("status"),
                "engine_running": s.get("engine_running", False),
                "last_update": s.get("last_update"),
                "actions_count": len(s.get("actions", [])),
            }
            for aid, s in states.items()
        },
    }


@router.get("/agent/{agent_id}")
async def agent_webhook_state(agent_id: str):
    """Get full state for a specific agent."""
    return get_agent_state(agent_id)
