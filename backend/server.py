"""
Anima Fund API — Main Server
All agent operations happen inside Conway Cloud sandboxes. Nothing runs on the host.
"""
import os
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
    conway, openclaw, agent_setup, credits,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from sandbox_poller import start_poller
    start_poller()
    yield
    from sandbox_poller import stop_poller
    stop_poller()
    close_db()


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
