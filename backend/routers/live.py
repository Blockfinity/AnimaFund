"""
Live engine data endpoints — read from state.db.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Query

from engine_bridge import (
    is_engine_live, get_live_agents, get_live_activity,
    get_live_transactions, get_live_financials,
    get_live_heartbeat_history, get_live_memory_facts, get_live_soul,
    get_live_turns, get_live_modifications,
    get_live_inbox_messages, get_live_relationships,
    get_live_reputation, get_live_discovered_agents,
    get_child_lifecycle_events, get_live_identity,
    get_live_working_memory, get_live_episodic_memory,
    get_live_procedural_memory, get_live_installed_tools,
    get_live_skills, get_live_metric_snapshots,
    get_live_policy_decisions, get_live_soul_history,
    get_live_onchain_transactions, get_live_session_summaries,
    get_live_kv_store, get_live_wake_events, get_live_heartbeat_schedule,
    get_live_skills_full, get_live_models, get_live_tool_usage,
    get_active_agent_id,
)

router = APIRouter(prefix="/api", tags=["live"])


@router.get("/engine/live")
async def check_engine_live():
    data = is_engine_live()
    data["agent_id"] = get_active_agent_id()
    return data

@router.get("/live/identity")
async def live_identity():
    return get_live_identity()

@router.get("/live/agents")
async def live_agents():
    agents = get_live_agents()
    return {"agents": agents, "total": len(agents), "source": "engine"}

@router.get("/live/activity")
async def live_activity(limit: int = Query(default=50, le=200)):
    activity = get_live_activity(limit)
    return {"activities": activity, "total": len(activity), "source": "engine"}

@router.get("/live/turns")
async def live_turns(limit: int = Query(default=50, le=200)):
    turns = get_live_turns(limit)
    return {"turns": turns, "total": len(turns), "source": "engine"}

@router.get("/live/transactions")
async def live_transactions(limit: int = Query(default=50, le=200)):
    txns = get_live_transactions(limit)
    return {"transactions": txns, "total": len(txns), "source": "engine"}

@router.get("/live/financials")
async def live_financials():
    return get_live_financials()

@router.get("/live/heartbeat")
async def live_heartbeat(limit: int = Query(default=20, le=100)):
    history = get_live_heartbeat_history(limit)
    return {"history": history, "total": len(history), "source": "engine"}

@router.get("/live/memory")
async def live_memory():
    facts = get_live_memory_facts()
    return {"facts": facts, "total": len(facts), "source": "engine"}

@router.get("/live/soul")
async def live_soul():
    content = get_live_soul()
    return {"content": content, "exists": content is not None}

@router.get("/live/modifications")
async def live_modifications(limit: int = Query(default=30, le=100)):
    mods = get_live_modifications(limit)
    return {"modifications": mods, "total": len(mods), "source": "engine"}

@router.get("/live/messages")
async def live_messages(limit: int = Query(default=50, le=200)):
    msgs = get_live_inbox_messages(limit)
    return {"messages": msgs, "total": len(msgs), "source": "engine"}

@router.get("/live/relationships")
async def live_relationships():
    rels = get_live_relationships()
    return {"relationships": rels, "total": len(rels), "source": "engine"}

@router.get("/live/discovered")
async def live_discovered():
    agents = get_live_discovered_agents()
    return {"agents": agents, "total": len(agents), "source": "engine"}

@router.get("/live/lifecycle")
async def live_lifecycle(child_id: str = None, limit: int = Query(default=50, le=200)):
    events = get_child_lifecycle_events(child_id, limit)
    return {"events": events, "total": len(events), "source": "engine"}

@router.get("/live/reputation")
async def live_reputation_endpoint(address: str = None):
    reps = get_live_reputation(address)
    return {"reputation": reps, "total": len(reps), "source": "engine"}

@router.get("/live/working-memory")
async def live_working_memory():
    return {"items": get_live_working_memory(), "source": "engine"}

@router.get("/live/episodic-memory")
async def live_episodic_memory(limit: int = Query(default=50, le=200)):
    return {"events": get_live_episodic_memory(limit), "source": "engine"}

@router.get("/live/procedural-memory")
async def live_procedural_memory():
    return {"procedures": get_live_procedural_memory(), "source": "engine"}

@router.get("/live/tools")
async def live_installed_tools():
    return {"tools": get_live_installed_tools(), "source": "engine"}

@router.get("/live/skills")
async def live_skills():
    return {"skills": get_live_skills(), "source": "engine"}

@router.get("/live/skills-full")
async def live_skills_full():
    """Aggregated skills view: Anima skills + Conway platform tools + MCP servers + models."""
    return {
        "skills": get_live_skills_full(),
        "models": get_live_models(),
        "tool_usage": get_live_tool_usage(),
        "source": "engine",
    }

@router.get("/live/metrics")
async def live_metrics(limit: int = Query(default=50, le=200)):
    return {"snapshots": get_live_metric_snapshots(limit), "source": "engine"}

@router.get("/live/policy")
async def live_policy(limit: int = Query(default=50, le=200)):
    return {"decisions": get_live_policy_decisions(limit), "source": "engine"}

@router.get("/live/soul-history")
async def live_soul_history():
    return {"versions": get_live_soul_history(), "source": "engine"}

@router.get("/live/onchain")
async def live_onchain(limit: int = Query(default=50, le=200)):
    return {"transactions": get_live_onchain_transactions(limit), "source": "engine"}

@router.get("/live/sessions")
async def live_sessions(limit: int = Query(default=20, le=100)):
    return {"sessions": get_live_session_summaries(limit), "source": "engine"}

@router.get("/live/kv")
async def live_kv():
    return {"items": get_live_kv_store(), "source": "engine"}

@router.get("/live/wake-events")
async def live_wake_events(limit: int = Query(default=20, le=100)):
    return {"events": get_live_wake_events(limit), "source": "engine"}

@router.get("/live/heartbeat-schedule")
async def live_heartbeat_schedule():
    return {"tasks": get_live_heartbeat_schedule(), "source": "engine"}


@router.get("/live/stream")
async def live_stream():
    """Server-Sent Events endpoint for real-time agent data.
    Pushes wallet, turns, engine status every 10 seconds."""
    import asyncio
    import json as _json
    import os
    import aiohttp
    from fastapi.responses import StreamingResponse

    async def event_generator():
        while True:
            try:
                # Gather live data
                engine = is_engine_live()
                engine["agent_id"] = get_active_agent_id()

                # Get Conway balance
                conway_credits = 0
                conway_key = os.environ.get("CONWAY_API_KEY", "")
                if not conway_key:
                    from engine_bridge import get_active_data_dir
                    active_dir = get_active_data_dir()
                    config_path = os.path.join(active_dir, "config.json")
                    if os.path.exists(config_path):
                        try:
                            with open(config_path) as f:
                                conway_key = _json.load(f).get("apiKey", "")
                        except Exception:
                            pass

                if conway_key:
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                            async with session.get(
                                "https://api.conway.tech/v1/credits/balance",
                                headers={"Authorization": f"Bearer {conway_key}"},
                            ) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    conway_credits = data.get("credits_cents", 0)
                    except Exception:
                        pass

                payload = {
                    "engine": engine,
                    "conway_credits_cents": conway_credits,
                    "turns_count": engine.get("turn_count", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {_json.dumps(payload)}\n\n"
            except Exception as e:
                yield f"data: {_json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
