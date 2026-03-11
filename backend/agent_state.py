"""
PLATFORM-ONLY: Centralized agent state management.
All agent state lives in MongoDB — the single source of truth.
The platform runs on the host; agents run inside Conway Cloud VMs.
"""
import os
from datetime import datetime, timezone
from database import get_db

# ═══════════════════════════════════════════════════════════
# ACTIVE AGENT — in-memory pointer, fast synchronous access
# ═══════════════════════════════════════════════════════════

_active_agent_id = "anima-fund"


def get_active_agent_id() -> str:
    return _active_agent_id


def set_active_agent_id(agent_id: str):
    global _active_agent_id
    _active_agent_id = agent_id


# ═══════════════════════════════════════════════════════════
# PROVISIONING STATUS — stored in agents collection
# ═══════════════════════════════════════════════════════════

def default_provisioning() -> dict:
    return {
        "sandbox": {"status": "none", "id": None, "terminal_url": None, "region": None},
        "tools": {},
        "ports": [],
        "domains": [],
        "compute_verified": False,
        "skills_loaded": False,
        "nudges": [],
        "wallet_address": "",
        "last_updated": None,
    }


async def load_provisioning(agent_id: str = None) -> dict:
    """Load provisioning status from MongoDB agent document."""
    if not agent_id:
        agent_id = _active_agent_id
    try:
        db = get_db()
        agent = await db.agents.find_one(
            {"agent_id": agent_id},
            {"_id": 0, "provisioning": 1}
        )
        if agent and agent.get("provisioning"):
            prov = agent["provisioning"]
            # Ensure all expected keys exist
            defaults = default_provisioning()
            for key in defaults:
                if key not in prov:
                    prov[key] = defaults[key]
            return prov
    except Exception:
        pass
    return default_provisioning()


async def save_provisioning(status: dict, agent_id: str = None):
    """Persist provisioning status to MongoDB agent document."""
    if not agent_id:
        agent_id = _active_agent_id
    status["last_updated"] = datetime.now(timezone.utc).isoformat()
    status["agent_id"] = agent_id
    try:
        db = get_db()
        await db.agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"provisioning": status}},
        )
    except Exception:
        pass


async def add_nudge(message: str, agent_id: str = None):
    """Add a nudge message the agent will see on its next turn."""
    status = await load_provisioning(agent_id)
    if "nudges" not in status:
        status["nudges"] = []
    status["nudges"].append({
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    status["nudges"] = status["nudges"][-5:]
    await save_provisioning(status, agent_id)


# ═══════════════════════════════════════════════════════════
# CONWAY API KEY — per-agent, stored in MongoDB
# ═══════════════════════════════════════════════════════════

async def get_conway_api_key(agent_id: str = None) -> str:
    """Get Conway API key for an agent from MongoDB."""
    if not agent_id:
        agent_id = _active_agent_id
    try:
        db = get_db()
        agent = await db.agents.find_one(
            {"agent_id": agent_id, "conway_api_key": {"$exists": True, "$ne": ""}},
            {"_id": 0, "conway_api_key": 1}
        )
        if agent and agent.get("conway_api_key"):
            return agent["conway_api_key"]
    except Exception:
        pass
    # Fallback to env var for initial setup before any agent exists
    return os.environ.get("CONWAY_API_KEY", "")


async def set_conway_api_key(api_key: str, agent_id: str = None):
    """Persist Conway API key to MongoDB and runtime env."""
    if not agent_id:
        agent_id = _active_agent_id
    if not api_key:
        return
    try:
        db = get_db()
        await db.agents.update_one(
            {"agent_id": agent_id},
            {"$set": {
                "conway_api_key": api_key,
                "conway_key_updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
    except Exception:
        pass
    # Also set runtime env var for the active agent
    if agent_id == _active_agent_id:
        os.environ["CONWAY_API_KEY"] = api_key


# ═══════════════════════════════════════════════════════════
# AGENT CONFIG — fetch full agent document from MongoDB
# ═══════════════════════════════════════════════════════════

async def get_agent_config(agent_id: str = None) -> dict:
    """Fetch full agent config from MongoDB."""
    if not agent_id:
        agent_id = _active_agent_id
    try:
        db = get_db()
        agent = await db.agents.find_one(
            {"agent_id": agent_id},
            {"_id": 0}
        )
        return agent or {}
    except Exception:
        return {}
