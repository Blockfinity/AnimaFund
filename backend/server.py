"""
Anima Platform API — Main Server
The platform provisions VMs, monitors Animas, and serves the spawn API.
Agents run inside VMs with OpenClaw. The platform is THIN.
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
from agent_state import set_active_agent_id, load_provisioning

# Import routers
from routers import agents, genesis, live, telegram, infrastructure
from routers import conway, openclaw, credits, webhook
from routers.provision import router as provision_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await _restore_active_agent()
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
app.include_router(telegram.router)
app.include_router(webhook.router)

# Data routers (reads from webhook cache — will be replaced by monitor.py)
app.include_router(genesis.router)
app.include_router(live.router)
app.include_router(infrastructure.router)

# Provider-specific (behind BYOI interface)
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
    """Payment compliance — handled inside VMs via x402."""
    return {"status": "sandbox_managed", "message": "Payments handled inside the sandbox via x402."}
