"""
Ultimus API — REST endpoints for the prediction engine.
Frontend calls these to create predictions, monitor simulations, and execute deployments.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import get_db
from ultimus.predictor import Predictor
from ultimus.calculator import Calculator
from ultimus.executor import Executor

router = APIRouter(prefix="/api/ultimus", tags=["ultimus"])
logger = logging.getLogger(__name__)

# Singleton instances
_predictor = Predictor()
_calculator = Calculator()
_executor = Executor()


class PredictionRequest(BaseModel):
    goal: str
    mode: str = "quick"  # quick, deep, expert, iterative
    num_personas: int = 5
    num_rounds: int = 3
    seed_capital: float = 10.0
    provider: str = "conway_hobby"
    model: str = "gpt-5-mini"
    seed_data: str = ""


class ExecuteRequest(BaseModel):
    prediction_id: str


@router.post("/predict")
async def create_prediction(req: PredictionRequest):
    """Create a new prediction. Simulates personas, calculates costs, produces strategy."""
    try:
        # Run prediction
        prediction = await _predictor.create_prediction(
            goal=req.goal, mode=req.mode,
            num_personas=req.num_personas, num_rounds=req.num_rounds,
            seed_data=req.seed_data,
        )

        # Calculate costs
        if prediction.strategy:
            cost_model = _calculator.calculate(
                prediction.strategy, seed_capital=req.seed_capital,
                provider=req.provider, model=req.model,
            )
            prediction.cost_model = cost_model

        # Save to MongoDB
        db = get_db()
        if db is not None:
            pred_doc = prediction.to_dict()
            pred_doc["_type"] = "prediction"
            await db.predictions.insert_one(pred_doc)

        return prediction.to_dict()

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")


@router.get("/predictions")
async def list_predictions():
    """List all predictions."""
    db = get_db()
    if db is not None:
        preds = await db.predictions.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
        return {"predictions": preds}
    return {"predictions": _predictor.list_predictions()}


@router.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: str):
    """Get a specific prediction with full details."""
    db = get_db()
    if db is not None:
        pred = await db.predictions.find_one({"id": prediction_id}, {"_id": 0})
        if pred:
            return pred
    pred = _predictor.get_prediction(prediction_id)
    if pred:
        return pred.to_dict()
    raise HTTPException(404, f"Prediction '{prediction_id}' not found")


@router.post("/execute")
async def execute_prediction(req: ExecuteRequest):
    """Execute a prediction — deploy real Animas based on the simulation results."""
    db = get_db()
    pred = None
    if db is not None:
        pred = await db.predictions.find_one({"id": req.prediction_id}, {"_id": 0})
    if not pred:
        p = _predictor.get_prediction(req.prediction_id)
        pred = p.to_dict() if p else None
    if not pred:
        raise HTTPException(404, f"Prediction '{req.prediction_id}' not found")
    if pred.get("status") != "completed":
        raise HTTPException(400, f"Prediction is '{pred.get('status')}', not completed")

    strategy = pred.get("strategy", {})
    cost_model = pred.get("cost_model", {})
    goal = pred.get("goal", "")

    result = await _executor.execute(req.prediction_id, strategy, goal, cost_model, db)

    # Update prediction status
    if db is not None:
        await db.predictions.update_one(
            {"id": req.prediction_id},
            {"$set": {"status": "executing", "execution": result}},
        )

    return result


@router.get("/status")
async def ultimus_status():
    """Ultimus engine status."""
    db = get_db()
    pred_count = 0
    if db is not None:
        pred_count = await db.predictions.count_documents({})
    return {
        "status": "ready",
        "predictions_total": pred_count,
        "active_predictions": len([p for p in _predictor.list_predictions() if p.get("status") == "simulating"]),
    }
