"""
PLATFORM: Anima Fund API — Main Server
The platform monitors and manages agents. Agents run inside Conway Cloud VMs.
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
from telegram_notify import send_telegram, notify_error

# Import routers
from routers import (
    agents, genesis, live, telegram, infrastructure,
    conway, openclaw, agent_setup, credits, webhook,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await _restore_active_agent_from_db()
    from sandbox_poller import start_poller
    start_poller()
    yield
    from sandbox_poller import stop_poller
    stop_poller()
    close_db()


async def _restore_active_agent_from_db():
    """On startup, restore active agent state from MongoDB.
    Also runs health-check if agent has an active sandbox to detect wallet + tools."""
    try:
        from agent_state import set_active_agent_id, load_provisioning
        db = get_db()

        # Find the default agent and load its key
        default_agent = await db.agents.find_one(
            {"agent_id": "anima-fund", "conway_api_key": {"$exists": True, "$ne": ""}},
            {"_id": 0, "conway_api_key": 1}
        )
        if default_agent and default_agent.get("conway_api_key"):
            os.environ["CONWAY_API_KEY"] = default_agent["conway_api_key"]
            logging.info("Active agent 'anima-fund' Conway key loaded from MongoDB")

        set_active_agent_id("anima-fund")

        # If there's an active sandbox, run health-check to detect wallet + tool state
        prov = await load_provisioning()
        if prov.get("sandbox", {}).get("status") == "active" and prov.get("sandbox", {}).get("id"):
            try:
                from routers.agent_setup import health_check_sandbox
                result = await health_check_sandbox()
                if result.get("wallet_address"):
                    logging.info(f"Wallet detected on startup: {result['wallet_address'][:20]}...")
            except Exception as e:
                logging.warning(f"Startup health-check failed: {e}")
    except Exception as e:
        logging.warning(f"Could not restore agent state from DB: {e}")


app = FastAPI(title="Anima Fund API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PLATFORM ROUTERS
app.include_router(agents.router)
app.include_router(genesis.router)
app.include_router(live.router)
app.include_router(telegram.router)
app.include_router(infrastructure.router)
app.include_router(conway.router)
app.include_router(openclaw.router)
app.include_router(agent_setup.router)
app.include_router(credits.router)
app.include_router(webhook.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "engine_live": False,  # Engine runs in Conway VM, not host
        "engine_db_exists": False,
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/payments/status")
async def payments_status():
    """Payment compliance — handled inside Conway VMs via x402."""
    return {"status": "sandbox_managed", "message": "All payments are handled inside the sandbox via x402."}
