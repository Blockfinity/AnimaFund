"""
Ultimus API — Routes for the prediction engine.
Uses Anima Machina's Workforce for orchestration.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_db
from ultimus.predictor import UltimusPrediction, generate_personas
from ultimus.knowledge import build_knowledge_graph, build_from_web_search
from ultimus.calculator import Calculator
from ultimus.executor import Executor

router = APIRouter(prefix="/api/ultimus", tags=["ultimus"])
logger = logging.getLogger(__name__)

_predictions: Dict[str, UltimusPrediction] = {}
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
    """Run a multi-agent prediction using Workforce orchestration."""
    pred_id = f"pred-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Build knowledge context
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

    # Generate personas
    persona_defs = await generate_personas(req.goal, kg_context, req.num_personas)

    # Create and run prediction
    prediction = UltimusPrediction(pred_id, req.goal, persona_defs, req.num_rounds)
    _predictions[pred_id] = prediction

    result = await prediction.run()

    # Generate strategy analysis from result
    strategy = await _analyze_result(prediction)
    cost_model = _calculator.calculate(strategy, req.seed_capital) if strategy else None

    # Save to MongoDB
    db = get_db()
    if db is not None:
        doc = {**result, "mode": req.mode, "knowledge_graph": kg_data,
               "strategy": strategy, "cost_model": cost_model}
        await db.predictions.insert_one(doc)

    return {**result, "mode": req.mode, "knowledge_graph": kg_data,
            "strategy": strategy, "cost_model": cost_model}


@router.post("/predict/stream")
async def run_prediction_stream(req: PredictRequest):
    """SSE stream — frontend sees simulation events in real-time."""
    pred_id = f"pred-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    kg_context = ""
    if req.mode == "deep":
        kg = await build_from_web_search(req.goal)
        kg_context = kg.get_context_for_simulation()

    persona_defs = await generate_personas(req.goal, kg_context, req.num_personas)
    prediction = UltimusPrediction(pred_id, req.goal, persona_defs, req.num_rounds)
    _predictions[pred_id] = prediction

    queue = asyncio.Queue()
    prediction.on_event(lambda e: queue.put_nowait(e))

    async def stream():
        task = asyncio.create_task(prediction.run())
        try:
            while not task.done() or not queue.empty():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            result = await task
            yield f"data: {json.dumps({'type': 'complete', **result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/predictions")
async def list_predictions():
    db = get_db()
    if db is not None:
        preds = await db.predictions.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
        return {"predictions": preds}
    return {"predictions": [p.to_dict() for p in _predictions.values()]}


@router.get("/predictions/{pred_id}")
async def get_prediction(pred_id: str):
    db = get_db()
    if db is not None:
        pred = await db.predictions.find_one({"id": pred_id}, {"_id": 0})
        if pred:
            return pred
    p = _predictions.get(pred_id)
    if p:
        return p.to_dict()
    raise HTTPException(404, "Not found")


@router.post("/execute")
async def execute_prediction(req: ExecuteRequest):
    db = get_db()
    pred = None
    if db is not None:
        pred = await db.predictions.find_one({"id": req.prediction_id}, {"_id": 0})
    if not pred:
        raise HTTPException(404, "Not found")
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
    running = [p for p in _predictions.values() if p.status == "running"]
    return {"status": "ready", "predictions_total": count, "active_simulations": len(running)}


async def _analyze_result(prediction: UltimusPrediction) -> Dict:
    """Analyze multi-round simulation into a deployment strategy."""
    if not prediction.round_summaries:
        return {}

    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        return {}

    from anima_machina.agents import ChatAgent
    from anima_machina.models import ModelFactory
    from anima_machina.types import ModelPlatformType

    model = ModelFactory.create(model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini",
                                api_key=key, url="https://integrations.emergentagent.com/llm/v1")

    # Build simulation summary from round data
    sim_summary = f"Goal: {prediction.goal}\nAgents: {len(prediction.persona_defs)}\nRounds: {prediction.num_rounds}\n\n"
    for rs in prediction.round_summaries:
        sim_summary += f"Round {rs['round']}:\n"
        for agent, pos in list(rs.get("positions", {}).items())[:8]:
            sim_summary += f"  {agent}: {pos}\n"
        sim_summary += "\n"

    persona_summary = ", ".join(f"{p['name']} ({p['role']})" for p in prediction.persona_defs[:15])

    prompt = f"""Analyze this multi-round simulation and produce a deployment strategy.

{sim_summary[:3000]}

All personas: {persona_summary}

Identify: coalitions formed, strategies that emerged, risks discovered, who changed positions and why.

Return JSON:
{{"summary":"2-3 sentence strategy based on simulation","recommended_agents":[{{"role":"...","genesis_prompt_focus":"...","priority":"high/medium/low","estimated_cost":0.0}}],"total_seed_cost":0.0,"estimated_break_even_hours":0,"confidence_score":0.0,"risks":["..."],"key_actions":["..."],"coalitions_formed":["..."],"sentiment_shifts":["..."]}}
ONLY valid JSON."""

    agent = ChatAgent(system_message="Analyze simulation results. Return JSON only.", model=model)
    response = agent.step(prompt)
    content = response.msgs[0].content if response.msgs else "{}"
    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except json.JSONDecodeError:
        return {"summary": "Analysis failed", "confidence_score": 0.0}
