"""
Live engine data endpoints.
The engine runs inside the Conway Cloud sandbox — these endpoints return sandbox state
or empty defaults when no sandbox is provisioned.
"""
import os
import json as _json
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import aiohttp

router = APIRouter(prefix="/api", tags=["live"])

CONWAY_API_KEY = os.environ.get("CONWAY_API_KEY", "")


def _empty_list_response(key="items"):
    return {key: [], "total": 0, "source": "sandbox"}


@router.get("/engine/live")
async def check_engine_live():
    """Engine live status — delegates to genesis router."""
    from routers.genesis import engine_live
    return await engine_live()


@router.get("/live/identity")
async def live_identity():
    """Agent identity — from MongoDB, not host filesystem."""
    from routers.genesis import _get_active_agent_id, _load_prov_status
    from database import get_db
    agent_id = _get_active_agent_id()
    prov = _load_prov_status()
    try:
        col = get_db()["agents"]
        doc = await col.find_one({"agent_id": agent_id}, {"_id": 0})
        if doc:
            return {
                "name": doc.get("name", "Anima Fund"),
                "address": prov.get("wallet_address", ""),
                "creator": os.environ.get("CREATOR_WALLET", ""),
                "agent_id": agent_id,
                "source": "database",
            }
    except Exception:
        pass
    return {"name": "Anima Fund", "address": prov.get("wallet_address", ""), "agent_id": agent_id, "source": "database"}


@router.get("/live/agents")
async def live_agents():
    return _empty_list_response("agents")

@router.get("/live/activity")
async def live_activity(limit: int = Query(default=50, le=200)):
    return _empty_list_response("activities")

@router.get("/live/turns")
async def live_turns(limit: int = Query(default=50, le=200)):
    return _empty_list_response("turns")

@router.get("/live/transactions")
async def live_transactions(limit: int = Query(default=50, le=200)):
    return _empty_list_response("transactions")

@router.get("/live/financials")
async def live_financials():
    return {"total_balance_usd": 0, "total_spent_usd": 0, "total_earned_usd": 0, "source": "sandbox"}

@router.get("/live/heartbeat")
async def live_heartbeat(limit: int = Query(default=20, le=100)):
    return _empty_list_response("history")

@router.get("/live/memory")
async def live_memory():
    return _empty_list_response("facts")

@router.get("/live/soul")
async def live_soul():
    return {"content": None, "exists": False}

@router.get("/live/modifications")
async def live_modifications(limit: int = Query(default=30, le=100)):
    return _empty_list_response("modifications")

@router.get("/live/messages")
async def live_messages(limit: int = Query(default=50, le=200)):
    return _empty_list_response("messages")

@router.get("/live/relationships")
async def live_relationships():
    return _empty_list_response("relationships")

@router.get("/live/discovered")
async def live_discovered():
    return _empty_list_response("agents")

@router.get("/live/lifecycle")
async def live_lifecycle(child_id: str = None, limit: int = Query(default=50, le=200)):
    return _empty_list_response("events")

@router.get("/live/reputation")
async def live_reputation_endpoint(address: str = None):
    return _empty_list_response("reputation")

@router.get("/live/working-memory")
async def live_working_memory():
    return _empty_list_response()

@router.get("/live/episodic-memory")
async def live_episodic_memory(limit: int = Query(default=50, le=200)):
    return _empty_list_response("events")

@router.get("/live/procedural-memory")
async def live_procedural_memory():
    return _empty_list_response("procedures")

@router.get("/live/tools")
async def live_installed_tools():
    return _empty_list_response("tools")

@router.get("/live/skills")
async def live_skills():
    return _empty_list_response("skills")

@router.get("/live/skills-full")
async def live_skills_full():
    return {"skills": [], "models": [], "tool_usage": [], "source": "sandbox"}

@router.get("/live/metrics")
async def live_metrics(limit: int = Query(default=50, le=200)):
    return _empty_list_response("snapshots")

@router.get("/live/policy")
async def live_policy(limit: int = Query(default=50, le=200)):
    return _empty_list_response("decisions")

@router.get("/live/soul-history")
async def live_soul_history():
    return _empty_list_response("versions")

@router.get("/live/onchain")
async def live_onchain(limit: int = Query(default=50, le=200)):
    return _empty_list_response("transactions")

@router.get("/live/sessions")
async def live_sessions(limit: int = Query(default=20, le=100)):
    return _empty_list_response("sessions")

@router.get("/live/kv")
async def live_kv():
    return _empty_list_response()

@router.get("/live/wake-events")
async def live_wake_events(limit: int = Query(default=20, le=100)):
    return _empty_list_response("events")

@router.get("/live/heartbeat-schedule")
async def live_heartbeat_schedule():
    return _empty_list_response("tasks")


@router.get("/live/stream")
async def live_stream():
    """SSE endpoint — lightweight stream using provisioning status, no host engine dependency."""
    async def event_generator():
        prev_hash = ""
        while True:
            try:
                from routers.genesis import _load_prov_status, _get_active_agent_id
                prov = _load_prov_status()
                agent_id = _get_active_agent_id()
                sandbox_id = prov["sandbox"].get("id", "")
                engine_deployed = prov["tools"].get("engine", {}).get("deployed", False)

                # Conway credits
                conway_credits = 0
                if CONWAY_API_KEY:
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                            async with session.get("https://api.conway.tech/v1/credits/balance",
                                headers={"Authorization": f"Bearer {CONWAY_API_KEY}"}) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    conway_credits = data.get("credits_cents", 0)
                    except Exception:
                        pass

                payload = {
                    "engine": {
                        "live": False,
                        "db_exists": engine_deployed,
                        "agent_state": "sandbox" if engine_deployed else "",
                        "turn_count": 0,
                        "agent_id": agent_id,
                    },
                    "conway_credits_cents": conway_credits,
                    "agent_count": 0,
                    "latest_activity_id": 0,
                    "sandbox_id": sandbox_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                cur_hash = f"{engine_deployed}:{conway_credits}:{agent_id}"
                if cur_hash != prev_hash:
                    yield f"data: {_json.dumps(payload)}\n\n"
                    prev_hash = cur_hash
                else:
                    yield ": heartbeat\n\n"
            except Exception as e:
                yield f"data: {_json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(8)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
