"""
Ultimus Dimensions — God's-eye view API.
Observe simulated or live personas, chat with them, inject variables.
Works in two modes:
  - Simulation mode: interact with simulated personas from a prediction
  - Live mode: interact with deployed Animas via their webhook data
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from agent_state_store import get_agent_state, get_all_agent_states

router = APIRouter(prefix="/api/dimensions", tags=["dimensions"])
logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"


class ChatRequest(BaseModel):
    prediction_id: str = ""
    persona_name: str = ""
    agent_id: str = ""
    message: str = ""
    mode: str = "simulation"  # simulation or live


class InjectRequest(BaseModel):
    prediction_id: str
    variable_name: str
    variable_value: str
    description: str = ""


@router.get("/status")
async def dimensions_status():
    """Dimensions engine status."""
    live_agents = get_all_agent_states()
    db = get_db()
    pred_count = 0
    if db is not None:
        pred_count = await db.predictions.count_documents({"status": "completed"})
    return {
        "status": "ready",
        "simulation_worlds": pred_count,
        "live_agents": len(live_agents),
    }


@router.get("/simulation/{prediction_id}")
async def get_simulation_world(prediction_id: str):
    """Get the full simulated world for a prediction — all personas, their actions, relationships."""
    db = get_db()
    if db is None:
        raise HTTPException(500, "Database not available")
    pred = await db.predictions.find_one({"id": prediction_id}, {"_id": 0})
    if not pred:
        raise HTTPException(404, f"Prediction '{prediction_id}' not found")

    personas = pred.get("personas", [])
    kg = pred.get("knowledge_graph", {})

    # Build relationships from knowledge graph if available, otherwise from persona pairs
    relationships = []
    if kg and kg.get("relationships"):
        for r in kg["relationships"]:
            relationships.append({"from": r["from"], "to": r["to"], "type": r.get("type", "related")})
    else:
        for persona in personas:
            for other in personas:
                if persona["name"] != other["name"]:
                    relationships.append({
                        "from": persona["name"], "to": other["name"],
                        "type": "collaborator" if persona.get("role") != other.get("role") else "peer",
                    })

    # Include knowledge graph entities as additional graph nodes
    kg_entities = kg.get("entities", []) if kg else []

    return {
        "prediction_id": prediction_id,
        "goal": pred.get("goal"),
        "status": pred.get("status"),
        "personas": personas,
        "relationships": relationships[:50],
        "knowledge_graph": kg,
        "rounds": pred.get("rounds_completed", 0),
        "strategy": pred.get("strategy"),
    }


@router.get("/live")
async def get_live_world():
    """Get the live world — all running Animas with their current state."""
    states = get_all_agent_states()
    db = get_db()
    agents = []
    if db is not None:
        async for doc in db.agents.find({}, {"_id": 0, "agent_id": 1, "name": 1, "genesis_prompt": 1, "prediction_id": 1}):
            agent_id = doc.get("agent_id", "")
            state = states.get(agent_id, {})
            agents.append({
                "agent_id": agent_id,
                "name": doc.get("name", agent_id),
                "status": state.get("status", "unknown"),
                "engine_running": state.get("engine_running", False),
                "actions_count": len(state.get("actions", [])),
                "goal_progress": state.get("goal_progress", 0),
                "last_update": state.get("last_update"),
                "prediction_id": doc.get("prediction_id"),
            })
    return {"agents": agents, "total": len(agents)}


@router.post("/chat")
async def chat_with_entity(req: ChatRequest):
    """Chat with a simulated persona or a live Anima. God's-eye view interaction."""
    llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not llm_key:
        raise HTTPException(500, "LLM key not configured")

    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-4o-mini",
        api_key=llm_key,
        url=LLM_URL,
    )

    if req.mode == "simulation":
        # Chat with a simulated persona
        db = get_db()
        pred = await db.predictions.find_one({"id": req.prediction_id}, {"_id": 0}) if db else None
        if not pred:
            raise HTTPException(404, "Prediction not found")

        persona = next((p for p in pred.get("personas", []) if p["name"] == req.persona_name), None)
        if not persona:
            raise HTTPException(404, f"Persona '{req.persona_name}' not found")

        system_msg = (
            f"You are {persona['name']}, a {persona['role']} in a simulated prediction scenario.\n"
            f"Your personality: {persona.get('personality', '')}\n"
            f"Your strategy: {persona.get('strategy', '')}\n"
            f"The goal being simulated: {pred.get('goal', '')}\n"
            f"You have completed {persona.get('actions_count', 0)} actions.\n"
            f"Revenue earned: ${persona.get('revenue', 0):.2f}, Expenses: ${persona.get('expenses', 0):.2f}\n\n"
            f"Answer as this persona. Stay in character. The user is observing from a God's-eye view."
        )
    else:
        # Chat with a live Anima
        state = get_agent_state(req.agent_id)
        system_msg = (
            f"You are representing the live Anima '{req.agent_id}'.\n"
            f"Current status: {state.get('status', 'unknown')}\n"
            f"Actions taken: {len(state.get('actions', []))}\n"
            f"Goal progress: {state.get('goal_progress', 0)}\n"
            f"Recent actions: {json.dumps(state.get('actions', [])[-5:])}\n\n"
            f"Answer based on this agent's actual state and history."
        )

    agent = ChatAgent(system_message=system_msg, model=model)
    response = agent.step(req.message)
    content = response.msgs[0].content if response.msgs else "No response"

    return {
        "response": content,
        "persona": req.persona_name or req.agent_id,
        "mode": req.mode,
    }


@router.post("/inject")
async def inject_variable(req: InjectRequest):
    """Inject a variable into a simulation — change conditions and see how personas react."""
    db = get_db()
    if db is None:
        raise HTTPException(500, "Database not available")

    pred = await db.predictions.find_one({"id": req.prediction_id}, {"_id": 0})
    if not pred:
        raise HTTPException(404, "Prediction not found")

    # Record the injection
    injection = {
        "variable": req.variable_name,
        "value": req.variable_value,
        "description": req.description,
        "injected_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.predictions.update_one(
        {"id": req.prediction_id},
        {"$push": {"injections": injection}},
    )

    return {
        "success": True,
        "prediction_id": req.prediction_id,
        "injection": injection,
        "message": f"Variable '{req.variable_name}' injected. Re-run simulation to see effects.",
    }
