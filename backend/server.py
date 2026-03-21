"""
Anima Platform API — Main Server
Thin control plane: provisions environments, monitors Animas, serves spawn API.
Anima Machina agents run everywhere and report state via webhook.
"""
import os
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from config import CREATOR_WALLET
from database import init_db, close_db, get_db
from agent_state import set_active_agent_id
from agent_state_store import load_states_from_db

# Import routers
from routers import agents, telegram, webhook
from routers.provision import router as provision_router
from routers.monitor import router as monitor_router
from routers.spawn import router as spawn_router

# Ultimus prediction engine
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ultimus.api import router as ultimus_router
from ultimus.dimensions import router as dimensions_router

# Keep these for backward compat until fully replaced
from routers import conway, openclaw, credits


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await _restore_active_agent()
    await load_states_from_db()
    yield
    close_db()


async def _restore_active_agent():
    """On startup, restore active agent state from MongoDB."""
    try:
        db = get_db()
        default_agent = await db.agents.find_one(
            {"agent_id": "anima-fund", "conway_api_key": {"$exists": True, "$ne": ""}},
            {"_id": 0, "conway_api_key": 1}
        )
        if default_agent and default_agent.get("conway_api_key"):
            os.environ["CONWAY_API_KEY"] = default_agent["conway_api_key"]
            logging.info("Active agent 'anima-fund' key loaded from MongoDB")
        set_active_agent_id("anima-fund")
    except Exception as e:
        logging.warning(f"Could not restore agent state: {e}")


app = FastAPI(title="Anima Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routers
app.include_router(agents.router)
app.include_router(provision_router)
app.include_router(monitor_router)
app.include_router(spawn_router)
app.include_router(webhook.router)
app.include_router(telegram.router)
app.include_router(ultimus_router)
app.include_router(dimensions_router)

# Provider-specific (kept for Conway compatibility)
app.include_router(conway.router)
app.include_router(openclaw.router)
app.include_router(credits.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "engine_live": False,
        "engine_db_exists": False,
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/payments/status")
async def payments_status():
    return {"status": "sandbox_managed", "message": "Payments handled inside sandbox via x402."}
