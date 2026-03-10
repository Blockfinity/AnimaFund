"""
Live engine data endpoints.
Reads from the sandbox poller cache — real agent data from the Conway sandbox.
"""
import os
import json as _json
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import aiohttp

from sandbox_poller import get_cache

router = APIRouter(prefix="/api", tags=["live"])

CONWAY_API_KEY = os.environ.get("CONWAY_API_KEY", "")


@router.get("/live/identity")
async def live_identity():
    """Agent identity — from MongoDB."""
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


@router.get("/live/financials")
async def live_financials():
    """Real financial data from sandbox economics.json and revenue log."""
    cache = get_cache()
    econ = cache.get("economics", {})
    revenue = cache.get("revenue_log", [])
    splits = cache.get("creator_split_log", [])

    total_earned = sum(r.get("gross_revenue", r.get("net", 0)) for r in revenue if isinstance(r, dict))
    total_spent = sum(r.get("cost", 0) for r in revenue if isinstance(r, dict))
    creator_paid = sum(s.get("creator_share", 0) for s in splits if isinstance(s, dict))

    return {
        "credits_usd": econ.get("credits_usd", 0),
        "credits_cents": econ.get("credits_cents", 0),
        "wallet_address": econ.get("wallet_address", ""),
        "total_earned_usd": total_earned,
        "total_spent_usd": total_spent,
        "total_balance_usd": econ.get("credits_usd", 0),
        "creator_paid_usd": creator_paid,
        "creator_wallet": econ.get("creator_wallet", ""),
        "revenue_entries": len(revenue),
        "last_updated": econ.get("updated_at", ""),
        "source": "sandbox",
    }


@router.get("/live/activity")
async def live_activity(limit: int = Query(default=50, le=200)):
    """Agent decisions and revenue actions from sandbox logs."""
    cache = get_cache()
    decisions = cache.get("decisions_log", [])
    revenue = cache.get("revenue_log", [])

    # Merge and sort by timestamp
    activities = []
    for d in (decisions if isinstance(decisions, list) else []):
        if isinstance(d, dict):
            activities.append({**d, "_type": "decision"})
    for r in (revenue if isinstance(revenue, list) else []):
        if isinstance(r, dict):
            activities.append({**r, "_type": "revenue"})

    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {"activities": activities[:limit], "total": len(activities), "source": "sandbox"}


@router.get("/live/transactions")
async def live_transactions(limit: int = Query(default=50, le=200)):
    """Revenue transactions from the agent."""
    cache = get_cache()
    revenue = cache.get("revenue_log", [])
    if not isinstance(revenue, list):
        revenue = []
    return {"transactions": revenue[:limit], "total": len(revenue), "source": "sandbox"}


@router.get("/live/agents")
async def live_agents():
    """Active agent info."""
    cache = get_cache()
    if cache["sandbox_id"]:
        return {"agents": [{"sandbox_id": cache["sandbox_id"], "engine_running": cache["engine_running"]}], "total": 1, "source": "sandbox"}
    return {"agents": [], "total": 0, "source": "sandbox"}


@router.get("/live/turns")
async def live_turns(limit: int = Query(default=50, le=200)):
    """Agent turns — derived from decision log entries."""
    cache = get_cache()
    decisions = cache.get("decisions_log", [])
    if not isinstance(decisions, list):
        decisions = []
    return {"turns": decisions[:limit], "total": len(decisions), "source": "sandbox"}


@router.get("/live/memory")
async def live_memory():
    """Agent logs as memory."""
    cache = get_cache()
    stdout = cache.get("agent_stdout", "")
    entries = [{"content": line, "type": "stdout"} for line in stdout.split("\n") if line.strip()][-50:]
    return {"facts": entries, "total": len(entries), "source": "sandbox"}


@router.get("/live/tools")
async def live_installed_tools():
    """Installed tools from provisioning status."""
    from routers.genesis import _load_prov_status
    prov = _load_prov_status()
    tools = prov.get("tools", {})
    tool_list = [{"name": k, **v} for k, v in tools.items()]
    return {"tools": tool_list, "total": len(tool_list), "source": "sandbox"}


@router.get("/live/metrics")
async def live_metrics(limit: int = Query(default=50, le=200)):
    """Metrics — economics snapshots over time."""
    cache = get_cache()
    econ = cache.get("economics", {})
    if econ:
        snapshot = {
            "credits_usd": econ.get("credits_usd", 0),
            "credits_cents": econ.get("credits_cents", 0),
            "updated_at": econ.get("updated_at", ""),
        }
        return {"snapshots": [snapshot], "total": 1, "source": "sandbox"}
    return {"snapshots": [], "total": 0, "source": "sandbox"}


@router.get("/live/soul")
async def live_soul():
    """Agent phase state as 'soul'."""
    cache = get_cache()
    phase = cache.get("phase_state", {})
    if phase:
        return {"content": phase, "exists": True, "source": "sandbox"}
    return {"content": None, "exists": False, "source": "sandbox"}


# Pass-through endpoints that don't have sandbox data yet
@router.get("/live/heartbeat")
async def live_heartbeat(limit: int = Query(default=20, le=100)):
    cache = get_cache()
    if cache["last_poll"]:
        return {"history": [{"timestamp": cache["last_poll"], "engine_running": cache["engine_running"]}], "total": 1, "source": "sandbox"}
    return {"history": [], "total": 0, "source": "sandbox"}

@router.get("/live/modifications")
async def live_modifications(limit: int = Query(default=30, le=100)):
    return {"modifications": [], "total": 0, "source": "sandbox"}

@router.get("/live/messages")
async def live_messages(limit: int = Query(default=50, le=200)):
    return {"messages": [], "total": 0, "source": "sandbox"}

@router.get("/live/relationships")
async def live_relationships():
    return {"relationships": [], "total": 0, "source": "sandbox"}

@router.get("/live/discovered")
async def live_discovered():
    return {"agents": [], "total": 0, "source": "sandbox"}

@router.get("/live/lifecycle")
async def live_lifecycle(child_id: str = None, limit: int = Query(default=50, le=200)):
    return {"events": [], "total": 0, "source": "sandbox"}

@router.get("/live/reputation")
async def live_reputation_endpoint(address: str = None):
    return {"reputation": [], "total": 0, "source": "sandbox"}

@router.get("/live/working-memory")
async def live_working_memory():
    return {"items": [], "total": 0, "source": "sandbox"}

@router.get("/live/episodic-memory")
async def live_episodic_memory(limit: int = Query(default=50, le=200)):
    return {"events": [], "total": 0, "source": "sandbox"}

@router.get("/live/procedural-memory")
async def live_procedural_memory():
    return {"procedures": [], "total": 0, "source": "sandbox"}

@router.get("/live/skills")
async def live_skills():
    return {"skills": [], "total": 0, "source": "sandbox"}

@router.get("/live/skills-full")
async def live_skills_full():
    return {"skills": [], "models": [], "tool_usage": [], "source": "sandbox"}

@router.get("/live/policy")
async def live_policy(limit: int = Query(default=50, le=200)):
    return {"decisions": [], "total": 0, "source": "sandbox"}

@router.get("/live/soul-history")
async def live_soul_history():
    return {"versions": [], "total": 0, "source": "sandbox"}

@router.get("/live/onchain")
async def live_onchain(limit: int = Query(default=50, le=200)):
    return {"transactions": [], "total": 0, "source": "sandbox"}

@router.get("/live/sessions")
async def live_sessions(limit: int = Query(default=20, le=100)):
    return {"sessions": [], "total": 0, "source": "sandbox"}

@router.get("/live/kv")
async def live_kv():
    return {"items": [], "total": 0, "source": "sandbox"}

@router.get("/live/wake-events")
async def live_wake_events(limit: int = Query(default=20, le=100)):
    return {"events": [], "total": 0, "source": "sandbox"}

@router.get("/live/heartbeat-schedule")
async def live_heartbeat_schedule():
    return {"tasks": [], "total": 0, "source": "sandbox"}


@router.get("/live/stream")
async def live_stream():
    """SSE endpoint — streams real agent data from sandbox poller cache."""
    async def event_generator():
        while True:
            try:
                cache = get_cache()
                econ = cache.get("economics", {})
                phase = cache.get("phase_state", {})
                revenue = cache.get("revenue_log", [])
                decisions = cache.get("decisions_log", [])

                # Conway credits — from cache or direct API fallback
                credits_cents = econ.get("credits_cents", 0)
                if not credits_cents and CONWAY_API_KEY:
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                            async with session.get("https://api.conway.tech/v1/credits/balance",
                                headers={"Authorization": f"Bearer {CONWAY_API_KEY}"}) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    credits_cents = data.get("credits_cents", 0)
                    except Exception:
                        pass

                total_earned = sum(r.get("gross_revenue", r.get("net", 0)) for r in revenue if isinstance(r, dict))
                total_spent = sum(r.get("cost", 0) for r in revenue if isinstance(r, dict))
                revenue_count = len(revenue) if isinstance(revenue, list) else 0
                decision_count = len(decisions) if isinstance(decisions, list) else 0

                payload = {
                    "engine": {
                        "live": cache["engine_running"],
                        "db_exists": cache["sandbox_id"] is not None,
                        "agent_state": "running" if cache["engine_running"] else ("sandbox" if cache["sandbox_id"] else ""),
                        "turn_count": decision_count,
                        "agent_id": "anima-fund",
                    },
                    "conway_credits_cents": credits_cents,
                    "economics": econ,
                    "phase": phase.get("current_phase", 0) if isinstance(phase, dict) else 0,
                    "phase_state": phase,
                    "total_earned_usd": total_earned,
                    "total_spent_usd": total_spent,
                    "revenue_actions": revenue_count,
                    "decision_count": decision_count,
                    "wallet_address": econ.get("wallet_address", ""),
                    "sandbox_id": cache["sandbox_id"],
                    "poller_status": "ok" if not cache["poll_error"] else cache["poll_error"],
                    "last_poll": cache["last_poll"],
                    "recent_revenue": (revenue[:5] if isinstance(revenue, list) else []),
                    "recent_decisions": (decisions[:5] if isinstance(decisions, list) else []),
                    "agent_stdout_tail": cache.get("agent_stdout", "")[-500:],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                yield f"data: {_json.dumps(payload)}\n\n"
            except Exception as e:
                yield f"data: {_json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(4)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
