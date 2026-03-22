"""
Anima Platform API — Main Server
Health endpoint responds immediately. Heavy imports (Ultimus/Anima Machina) loaded eagerly but don't block health.
"""
import os
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import CREATOR_WALLET
from database import init_db, close_db, get_db
from agent_state import set_active_agent_id
from agent_state_store import load_states_from_db

# Import routers
from routers import agents, telegram, webhook
from routers.provision import router as provision_router
from routers.monitor import router as monitor_router
from routers.spawn import router as spawn_router

# Ultimus — import eagerly (routes must be registered before startup)
try:
    from ultimus.api import router as ultimus_router
    from ultimus.dimensions import router as dimensions_router
    ULTIMUS_AVAILABLE = True
except Exception as e:
    logging.warning(f"Ultimus import failed: {e}")
    ULTIMUS_AVAILABLE = False

# Legacy routers
from routers import conway, openclaw, credits


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        await _restore_active_agent()
    except Exception as e:
        logging.warning(f"Agent restore: {e}")
    try:
        await load_states_from_db()
    except Exception as e:
        logging.warning(f"State load: {e}")
    yield
    close_db()


async def _restore_active_agent():
    try:
        db = get_db()
        if db is not None:
            agent = await db.agents.find_one(
                {"agent_id": "anima-fund", "conway_api_key": {"$exists": True, "$ne": ""}},
                {"_id": 0, "conway_api_key": 1}
            )
            if agent and agent.get("conway_api_key"):
                os.environ["CONWAY_API_KEY"] = agent["conway_api_key"]
        set_active_agent_id("anima-fund")
    except Exception as e:
        logging.warning(f"Restore agent: {e}")


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

# Ultimus routers (if available)
if ULTIMUS_AVAILABLE:
    app.include_router(ultimus_router)
    app.include_router(dimensions_router)

# Legacy
app.include_router(conway.router)
app.include_router(openclaw.router)
app.include_router(credits.router)


# Health endpoints — MUST respond immediately regardless of other components
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "ultimus": ULTIMUS_AVAILABLE,
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/payments/status")
async def payments_status():
    return {"status": "sandbox_managed", "message": "Payments handled via x402."}
