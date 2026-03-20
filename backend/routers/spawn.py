"""
Spawn router — Animas request new sandboxed environments through this API.
Called by SpawnToolkit from within running agents.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from database import get_db

router = APIRouter(prefix="/api/spawn", tags=["spawn"])
logger = logging.getLogger(__name__)


class SpawnRequest(BaseModel):
    purpose: str
    provider: str = "conway"
    tier: str = "hobby"
    parent_agent_id: str = ""
    genesis_prompt: str = ""


@router.post("/request")
async def request_spawn(req: SpawnRequest, request: Request):
    """An Anima requests a new sandboxed environment for a child agent."""
    db = get_db()
    spawn_id = f"spawn-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    spawn_record = {
        "spawn_id": spawn_id,
        "purpose": req.purpose,
        "provider": req.provider,
        "tier": req.tier,
        "parent_agent_id": req.parent_agent_id,
        "genesis_prompt": req.genesis_prompt,
        "status": "requested",
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.spawns.insert_one(spawn_record)
    del spawn_record["_id"]

    logger.info(f"Spawn requested: {spawn_id} by {req.parent_agent_id} for '{req.purpose}'")

    return {
        "success": True,
        "spawn_id": spawn_id,
        "status": "requested",
        "message": f"Environment request queued. Purpose: {req.purpose}",
    }


@router.get("/{spawn_id}/status")
async def spawn_status(spawn_id: str):
    """Check status of a spawn request."""
    db = get_db()
    record = await db.spawns.find_one({"spawn_id": spawn_id}, {"_id": 0})
    if not record:
        raise HTTPException(404, f"Spawn '{spawn_id}' not found")
    return record


@router.delete("/{spawn_id}")
async def destroy_spawn(spawn_id: str, reason: str = ""):
    """Destroy a spawned environment."""
    db = get_db()
    record = await db.spawns.find_one({"spawn_id": spawn_id}, {"_id": 0})
    if not record:
        raise HTTPException(404, f"Spawn '{spawn_id}' not found")

    await db.spawns.update_one(
        {"spawn_id": spawn_id},
        {"$set": {"status": "destroyed", "reason": reason, "destroyed_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"success": True, "spawn_id": spawn_id, "status": "destroyed"}


@router.get("/")
async def list_spawns():
    """List all spawn requests."""
    db = get_db()
    spawns = await db.spawns.find({}, {"_id": 0}).sort("requested_at", -1).to_list(100)
    return {"spawns": spawns}
