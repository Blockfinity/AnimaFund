"""
Ultimus API — Runs live multi-agent simulations, not static graph generation.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_db
from ultimus.simulation import Simulation, generate_personas_from_knowledge, Persona
from ultimus.knowledge import build_knowledge_graph, build_from_web_search
from ultimus.calculator import Calculator
from ultimus.executor import Executor

router = APIRouter(prefix="/api/ultimus", tags=["ultimus"])
logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"

_simulations: Dict[str, Simulation] = {}
_calculator = Calculator()
_executor = Executor()


class PredictRequest(BaseModel):
    goal: str
    mode: str = "quick"
    num_personas: int = 10
    num_rounds: int = 5
    seed_capital: float = 10.0
    seed_data: str = ""


class ExecuteRequest(BaseModel):
    prediction_id: str


@router.post("/predict")
async def run_prediction(req: PredictRequest):
    """Start a LIVE multi-agent simulation. Agents interact across rounds producing emergent behavior."""
    sim_id = f"sim-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Step 1: Build knowledge from seed data
    kg_context = ""
    kg_data = None
    if req.mode == "deep" or req.mode == "iterative":
        kg = await build_from_web_search(req.goal)
        kg_context = kg.get_context_for_simulation()
        kg_data = kg.to_dict()
    elif req.mode == "expert" and req.seed_data:
        kg = await build_knowledge_graph(req.seed_data, req.goal)
        kg_context = kg.get_context_for_simulation()
        kg_data = kg.to_dict()

    # Step 2: Generate personas from knowledge
    personas = await generate_personas_from_knowledge(req.goal, kg_context or req.goal, req.num_personas)

    # Step 3: Run the simulation
    sim = Simulation(sim_id, req.goal, personas, req.num_rounds)
    _simulations[sim_id] = sim

    # Collect events for response
    events = []
    sim.on_event(lambda e: events.append(e))

    result = await sim.run()

    # Step 4: Calculate costs
    # Build strategy summary from simulation results
    strategy = await _generate_strategy_from_simulation(sim)
    cost_model = _calculator.calculate(strategy, req.seed_capital) if strategy else None

    # Save to MongoDB
    db = get_db()
    if db is not None:
        doc = {
            **result,
            "mode": req.mode,
            "knowledge_graph": kg_data,
            "strategy": strategy,
            "cost_model": cost_model,
            "events": events[-50:],  # Keep last 50 events
        }
        await db.predictions.insert_one(doc)

    return {
        **result,
        "mode": req.mode,
        "knowledge_graph": kg_data,
        "strategy": strategy,
        "cost_model": cost_model,
        "events_count": len(events),
    }


@router.post("/predict/stream")
async def run_prediction_stream(req: PredictRequest):
    """Start simulation with SSE streaming — frontend sees agents act in real-time."""
    sim_id = f"sim-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    kg_context = ""
    if req.mode == "deep":
        kg = await build_from_web_search(req.goal)
        kg_context = kg.get_context_for_simulation()

    personas = await generate_personas_from_knowledge(req.goal, kg_context or req.goal, req.num_personas)
    sim = Simulation(sim_id, req.goal, personas, req.num_rounds)
    _simulations[sim_id] = sim

    queue = asyncio.Queue()
    sim.on_event(lambda e: queue.put_nowait(e))

    async def event_stream():
        # Start simulation in background
        task = asyncio.create_task(sim.run())
        try:
            while not task.done() or not queue.empty():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            # Send final result
            result = await task
            yield f"data: {json.dumps({'type': 'result', **result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/predictions")
async def list_predictions():
    db = get_db()
    if db is not None:
        preds = await db.predictions.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
        return {"predictions": preds}
    return {"predictions": [s.to_dict() for s in _simulations.values()]}


@router.get("/predictions/{sim_id}")
async def get_prediction(sim_id: str):
    db = get_db()
    if db is not None:
        pred = await db.predictions.find_one({"id": sim_id}, {"_id": 0})
        if pred:
            return pred
    sim = _simulations.get(sim_id)
    if sim:
        return sim.to_dict()
    raise HTTPException(404, f"Simulation '{sim_id}' not found")


@router.post("/execute")
async def execute_prediction(req: ExecuteRequest):
    db = get_db()
    pred = None
    if db is not None:
        pred = await db.predictions.find_one({"id": req.prediction_id}, {"_id": 0})
    if not pred:
        raise HTTPException(404, "Prediction not found")

    strategy = pred.get("strategy", {})
    cost_model = pred.get("cost_model", {})
    result = await _executor.execute(req.prediction_id, strategy, pred.get("goal", ""), cost_model, db)

    if db is not None:
        await db.predictions.update_one({"id": req.prediction_id}, {"$set": {"status": "executing", "execution": result}})

    return result


@router.get("/status")
async def ultimus_status():
    db = get_db()
    count = 0
    if db is not None:
        count = await db.predictions.count_documents({})
    running = [s for s in _simulations.values() if s.status == "running"]
    return {"status": "ready", "predictions_total": count, "active_simulations": len(running)}


async def _generate_strategy_from_simulation(sim: Simulation) -> Dict:
    """Analyze simulation results and produce deployment strategy."""
    llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not llm_key:
        return {}

    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini",
        api_key=llm_key, url=LLM_URL,
    )

    # Summarize what happened in the simulation
    summary_parts = [f"Goal: {sim.goal}", f"Rounds: {sim.num_rounds}", f"Personas: {len(sim.personas)}"]
    summary_parts.append(f"Total posts: {len(sim.platform.posts)}, comments: {len(sim.platform.comments)}, follows: {len(sim.platform.follows)}")

    for p in sim.personas:
        summary_parts.append(f"- {p.name} ({p.role}): {len(p.actions)} actions. Last action: {p.actions[-1]['content'][:60] if p.actions else 'none'}")

    # Top posts by engagement
    top_posts = sorted(sim.platform.posts, key=lambda p: len(p.get("comments", [])) + len(p.get("reactions", [])), reverse=True)[:5]
    for p in top_posts:
        summary_parts.append(f"Top post by {p['author']}: \"{p['content'][:80]}\" ({len(p.get('comments',[]))} comments, {len(p.get('reactions',[]))} reactions)")

    prompt = f"""Analyze this completed simulation and produce a deployment strategy.

Simulation data:
{chr(10).join(summary_parts)}

Return JSON:
{{"summary": "strategy summary", "recommended_agents": [{{"role": "...", "genesis_prompt_focus": "...", "priority": "high/medium/low", "estimated_cost": 0.0}}], "total_seed_cost": 0.0, "estimated_break_even_hours": 0, "confidence_score": 0.0, "risks": ["..."], "key_actions": ["..."]}}
Return ONLY valid JSON."""

    agent = ChatAgent(system_message="Analyze simulation results. Return JSON.", model=model)
    response = agent.step(prompt)
    content = response.msgs[0].content if response.msgs else "{}"

    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except json.JSONDecodeError:
        return {"summary": "Strategy analysis failed", "confidence_score": 0.0}
