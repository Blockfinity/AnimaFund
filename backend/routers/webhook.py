"""
Webhook receiver — Anima Machina agents push state here via StateReportingToolkit.
Per-agent data stored in agent_state_store (cache + MongoDB).
"""
from fastapi import APIRouter, Request
from agent_state_store import update_agent_state, get_agent_state, get_all_agent_states

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/agent-update")
async def receive_agent_update(request: Request):
    """Receives state reports from Anima Machina agents via StateReportingToolkit."""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""

    data = await request.json()
    agent_id = data.get("agent_id", "unknown")

    # TODO: validate per-agent webhook token against MongoDB
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
