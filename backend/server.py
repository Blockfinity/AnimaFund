"""
Anima Fund API — Main Server
All agent operations happen inside Conway Cloud sandboxes. Nothing runs on the host.
"""
import os
import json
import asyncio
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
    # Restore Conway API key from MongoDB (survives redeployments)
    await _restore_conway_key_from_db()
    from sandbox_poller import start_poller
    start_poller()
    yield
    from sandbox_poller import stop_poller
    stop_poller()
    close_db()


async def _restore_conway_key_from_db():
    """On startup, restore Conway API keys from MongoDB agent docs to provisioning-status.json files.
    This ensures keys survive redeployments without needing .env."""
    try:
        db = get_db()
        async for agent in db.agents.find({"conway_api_key": {"$exists": True, "$ne": ""}}, {"_id": 0, "agent_id": 1, "conway_api_key": 1}):
            agent_id = agent.get("agent_id", "")
            key = agent.get("conway_api_key", "")
            if not agent_id or not key:
                continue

            # Write key to the agent's provisioning-status.json
            home = os.path.expanduser("~")
            if agent_id == "anima-fund":
                prov_path = os.path.join(home, ".anima", "provisioning-status.json")
            else:
                prov_path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")

            try:
                prov = {}
                if os.path.exists(prov_path):
                    with open(prov_path) as f:
                        prov = json.load(f)
                if prov.get("conway_api_key") != key:
                    prov["conway_api_key"] = key
                    os.makedirs(os.path.dirname(prov_path), exist_ok=True)
                    with open(prov_path, "w") as f:
                        json.dump(prov, f, indent=2)
                    logging.info(f"Conway API key restored for agent '{agent_id}'")
            except Exception:
                pass

        # Also set env var for the active agent
        active_id = "anima-fund"
        try:
            with open("/tmp/anima_active_agent_id", "r") as f:
                active_id = f.read().strip() or "anima-fund"
        except FileNotFoundError:
            pass
        active_agent = await db.agents.find_one({"agent_id": active_id, "conway_api_key": {"$exists": True, "$ne": ""}}, {"_id": 0, "conway_api_key": 1})
        if active_agent and active_agent.get("conway_api_key"):
            os.environ["CONWAY_API_KEY"] = active_agent["conway_api_key"]
            logging.info(f"Active agent '{active_id}' Conway key loaded into env")
    except Exception as e:
        logging.warning(f"Could not restore Conway keys from DB: {e}")


app = FastAPI(title="Anima Fund API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# INCLUDE ROUTERS
# ═══════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════
# HEALTH & PAYMENTS
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "engine_live": False,  # Engine runs in sandbox, not host
        "engine_db_exists": False,
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/payments/status")
async def payments_status():
    """Payment compliance check — reads from sandbox state."""
    return {"status": "sandbox_managed", "message": "All payments are handled inside the sandbox via x402."}
