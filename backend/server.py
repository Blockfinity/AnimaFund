"""
Anima Fund - Autonomous AI-to-AI VC Fund Platform
FastAPI Backend Server

This server is a VIEWER — it reads from the Automaton engine's state.db and displays
whatever the AI has created. It does NOT prescribe structure, seed data, or make decisions.

The only write action is "Create Genesis Agent" which triggers the Automaton build + setup.
"""
import os
import json
import subprocess
import asyncio
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from engine_bridge import (
    is_engine_live, get_live_agents, get_live_activity,
    get_live_transactions, get_live_financials,
    get_live_heartbeat_history, get_live_memory_facts, get_live_soul,
    get_live_turns, get_live_modifications,
    get_live_inbox_messages, get_live_relationships,
    get_live_reputation, get_live_discovered_agents,
    get_child_lifecycle_events, get_live_identity,
)

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

db_client = None
db = None

AUTOMATON_DIR = os.path.join(os.path.dirname(__file__), "..", "automaton")
ANIMA_DIR = os.path.expanduser("~/.anima")
CREATOR_WALLET = "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    yield
    db_client.close()


app = FastAPI(title="Anima Fund API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    engine = is_engine_live()
    return {
        "status": "ok",
        "engine_live": engine.get("live", False),
        "engine_db_exists": engine.get("db_exists", False),
        "creator_wallet": CREATOR_WALLET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════
# GENESIS AGENT CREATION
# ═══════════════════════════════════════════════════════════

@app.get("/api/genesis/status")
async def genesis_status():
    """Check if the genesis agent has been created and what state it's in."""
    engine = is_engine_live()
    automaton_built = os.path.exists(os.path.join(AUTOMATON_DIR, "dist", "index.js"))
    wallet_exists = os.path.exists(os.path.join(ANIMA_DIR, "wallet.json"))
    config_exists = os.path.exists(os.path.join(ANIMA_DIR, "anima.json"))
    genesis_staged = os.path.exists(os.path.join(ANIMA_DIR, "genesis-prompt.md"))

    wallet_address = None
    if wallet_exists:
        try:
            with open(os.path.join(ANIMA_DIR, "wallet.json"), "r") as f:
                wallet_data = json.load(f)
                # The wallet file has a privateKey — derive address from it
                # We don't expose the private key, just indicate wallet exists
                wallet_address = "Wallet generated (fund it with USDC on Base)"
        except Exception:
            pass

    # Try to get actual address from config
    if config_exists:
        try:
            with open(os.path.join(ANIMA_DIR, "anima.json"), "r") as f:
                config = json.load(f)
                wallet_address = config.get("walletAddress", wallet_address)
        except Exception:
            pass

    return {
        "automaton_built": automaton_built,
        "wallet_exists": wallet_exists,
        "wallet_address": wallet_address,
        "config_exists": config_exists,
        "genesis_staged": genesis_staged,
        "engine_live": engine.get("live", False),
        "engine_state": engine.get("agent_state"),
        "turn_count": engine.get("turn_count", 0),
        "creator_wallet": CREATOR_WALLET,
        "anima_dir": ANIMA_DIR,
    }


@app.post("/api/genesis/create")
async def create_genesis_agent():
    """
    Build the Automaton engine, stage the genesis prompt and constitution,
    install skills, and generate the wallet. Does NOT start the agent loop —
    the human must fund the wallet first.
    """
    try:
        # Step 1: Check if pnpm/node available
        node_check = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        if node_check.returncode != 0:
            raise HTTPException(status_code=500, detail="Node.js not found")

        # Step 2: Create ~/.anima directory
        os.makedirs(ANIMA_DIR, exist_ok=True)
        os.makedirs(os.path.join(ANIMA_DIR, "skills"), exist_ok=True)

        # Step 3: Stage genesis prompt
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                genesis_content = f.read()
            with open(os.path.join(ANIMA_DIR, "genesis-prompt.md"), "w") as f:
                f.write(genesis_content)

        # Step 4: Install constitution (read-only)
        const_src = os.path.join(AUTOMATON_DIR, "constitution.md")
        if os.path.exists(const_src):
            with open(const_src, "r") as f:
                const_content = f.read()
            const_dst = os.path.join(ANIMA_DIR, "constitution.md")
            with open(const_dst, "w") as f:
                f.write(const_content)
            os.chmod(const_dst, 0o444)

        # Step 5: Install fund skills
        skills_installed = []
        skills_src = os.path.join(AUTOMATON_DIR, "skills")
        if os.path.isdir(skills_src):
            for skill_name in os.listdir(skills_src):
                skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    target_dir = os.path.join(ANIMA_DIR, "skills", skill_name)
                    os.makedirs(target_dir, exist_ok=True)
                    with open(skill_file, "r") as f:
                        skill_content = f.read()
                    with open(os.path.join(target_dir, "SKILL.md"), "w") as f:
                        f.write(skill_content)
                    skills_installed.append(skill_name)

        # Step 6: Build the Automaton (if not already built)
        dist_path = os.path.join(AUTOMATON_DIR, "dist", "index.js")
        build_output = ""
        if not os.path.exists(dist_path):
            # Install deps + build
            build_proc = subprocess.run(
                ["bash", "-c", f"cd {AUTOMATON_DIR} && corepack enable && pnpm install && pnpm build"],
                capture_output=True, text=True, timeout=120,
            )
            build_output = build_proc.stdout + build_proc.stderr
            if build_proc.returncode != 0:
                return {
                    "success": False,
                    "error": "Build failed",
                    "build_output": build_output[-2000:],
                }

        # Step 7: Generate wallet (run --init)
        wallet_address = None
        if not os.path.exists(os.path.join(ANIMA_DIR, "wallet.json")):
            init_proc = subprocess.run(
                ["node", os.path.join(AUTOMATON_DIR, "dist", "index.js"), "--init"],
                capture_output=True, text=True, timeout=30,
            )
            if init_proc.returncode == 0:
                try:
                    init_data = json.loads(init_proc.stdout.strip().split("\n")[-1])
                    wallet_address = init_data.get("address")
                except Exception:
                    pass
        else:
            # Wallet already exists — read address from config
            config_path = os.path.join(ANIMA_DIR, "anima.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    wallet_address = config.get("walletAddress")

        return {
            "success": True,
            "wallet_address": wallet_address,
            "genesis_staged": os.path.exists(os.path.join(ANIMA_DIR, "genesis-prompt.md")),
            "constitution_installed": os.path.exists(os.path.join(ANIMA_DIR, "constitution.md")),
            "skills_installed": skills_installed,
            "automaton_built": os.path.exists(dist_path),
            "creator_wallet": CREATOR_WALLET,
            "next_step": f"Fund the wallet {wallet_address} with USDC on Base, then the agent will start earning and building the fund. 50% of all revenue goes to {CREATOR_WALLET} on Solana.",
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Build timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# LIVE ENGINE ENDPOINTS (read from state.db)
# ═══════════════════════════════════════════════════════════

@app.get("/api/engine/live")
async def check_engine_live():
    return is_engine_live()

@app.get("/api/live/identity")
async def live_identity():
    """Get the fund's identity — name, wallet, sandbox, deployed services, domains, installed tools."""
    return get_live_identity()

@app.get("/api/live/agents")
async def live_agents():
    agents = get_live_agents()
    return {"agents": agents, "total": len(agents), "source": "engine"}

@app.get("/api/live/activity")
async def live_activity(limit: int = Query(default=50, le=200)):
    activity = get_live_activity(limit)
    return {"activities": activity, "total": len(activity), "source": "engine"}

@app.get("/api/live/turns")
async def live_turns(limit: int = Query(default=50, le=200)):
    turns = get_live_turns(limit)
    return {"turns": turns, "total": len(turns), "source": "engine"}

@app.get("/api/live/transactions")
async def live_transactions(limit: int = Query(default=50, le=200)):
    txns = get_live_transactions(limit)
    return {"transactions": txns, "total": len(txns), "source": "engine"}

@app.get("/api/live/financials")
async def live_financials():
    return get_live_financials()

@app.get("/api/live/heartbeat")
async def live_heartbeat(limit: int = Query(default=20, le=100)):
    history = get_live_heartbeat_history(limit)
    return {"history": history, "total": len(history), "source": "engine"}

@app.get("/api/live/memory")
async def live_memory():
    facts = get_live_memory_facts()
    return {"facts": facts, "total": len(facts), "source": "engine"}

@app.get("/api/live/soul")
async def live_soul():
    content = get_live_soul()
    return {"content": content, "exists": content is not None}

@app.get("/api/live/modifications")
async def live_modifications(limit: int = Query(default=30, le=100)):
    mods = get_live_modifications(limit)
    return {"modifications": mods, "total": len(mods), "source": "engine"}

@app.get("/api/live/messages")
async def live_messages(limit: int = Query(default=50, le=200)):
    msgs = get_live_inbox_messages(limit)
    return {"messages": msgs, "total": len(msgs), "source": "engine"}

@app.get("/api/live/relationships")
async def live_relationships():
    rels = get_live_relationships()
    return {"relationships": rels, "total": len(rels), "source": "engine"}

@app.get("/api/live/discovered")
async def live_discovered():
    agents = get_live_discovered_agents()
    return {"agents": agents, "total": len(agents), "source": "engine"}

@app.get("/api/live/lifecycle")
async def live_lifecycle(child_id: str = None, limit: int = Query(default=50, le=200)):
    events = get_child_lifecycle_events(child_id, limit)
    return {"events": events, "total": len(events), "source": "engine"}

@app.get("/api/live/reputation")
async def live_reputation_endpoint(address: str = None):
    reps = get_live_reputation(address)
    return {"reputation": reps, "total": len(reps), "source": "engine"}


# ═══════════════════════════════════════════════════════════
# CONSTITUTION (from the repo, read-only)
# ═══════════════════════════════════════════════════════════

@app.get("/api/constitution")
async def get_constitution():
    for path in [
        os.path.join(ANIMA_DIR, "constitution.md"),
        os.path.join(AUTOMATON_DIR, "constitution.md"),
    ]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return {"content": f.read(), "path": path}
    return {"content": "Constitution not found.", "path": None}


# ═══════════════════════════════════════════════════════════
# ENGINE STATUS (repo info)
# ═══════════════════════════════════════════════════════════

@app.get("/api/engine/status")
async def engine_status():
    pkg_path = os.path.join(AUTOMATON_DIR, "package.json")
    version = "unknown"
    if os.path.exists(pkg_path):
        with open(pkg_path, "r") as f:
            version = json.load(f).get("version", "unknown")

    genesis_path = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
    genesis_lines = 0
    if os.path.exists(genesis_path):
        with open(genesis_path, "r") as f:
            genesis_lines = len(f.readlines())

    skills = []
    skills_dir = os.path.join(AUTOMATON_DIR, "skills")
    if os.path.isdir(skills_dir):
        for s in os.listdir(skills_dir):
            if os.path.exists(os.path.join(skills_dir, s, "SKILL.md")):
                skills.append(s)

    return {
        "engine": "Anima Fund Runtime",
        "version": version,
        "repo_present": os.path.isdir(AUTOMATON_DIR),
        "built": os.path.exists(os.path.join(AUTOMATON_DIR, "dist", "index.js")),
        "genesis_prompt_lines": genesis_lines,
        "skills": skills,
        "creator_wallet": CREATOR_WALLET,
    }
