"""
Anima Fund - Autonomous AI-to-AI VC Fund Platform
FastAPI Backend Server

This server is a VIEWER — it reads from the Automaton engine's state.db and displays
whatever the AI has created. It does NOT prescribe structure, seed data, or make decisions.

The only write action is "Create Genesis Agent" which stages config files for the
Automaton engine and starts it via supervisor. The engine handles everything else:
wallet generation, API key provisioning, constitution, SOUL, skills, heartbeat.
"""
import os
import io
import json
import base64
import subprocess
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import qrcode
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
)

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

db_client = None
db = None

AUTOMATON_DIR = os.path.join(os.path.dirname(__file__), "..", "automaton")
ANIMA_DIR = os.path.expanduser("~/.anima")
CREATOR_WALLET = os.environ.get("CREATOR_WALLET", "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r")


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

ENGINE_PID_FILE = os.path.join(ANIMA_DIR, "engine.pid")


def is_engine_process_running():
    """Check if the automaton engine process is alive."""
    # Check PID file
    if os.path.exists(ENGINE_PID_FILE):
        try:
            with open(ENGINE_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # signal 0 = just check if alive
            return True
        except (ProcessLookupError, ValueError, PermissionError):
            # Stale PID file
            try:
                os.remove(ENGINE_PID_FILE)
            except OSError:
                pass
    # Fallback: check for the process directly
    try:
        r = subprocess.run(["pgrep", "-f", "dist/index.js.*--run"], capture_output=True, text=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False


@app.get("/api/genesis/status")
async def genesis_status():
    """Check if the genesis agent has been created."""
    engine = is_engine_live()
    config_exists = os.path.exists(os.path.join(ANIMA_DIR, "anima.json"))
    genesis_staged = os.path.exists(os.path.join(ANIMA_DIR, "genesis-prompt.md"))

    # The Automaton stores the wallet address in anima.json after setup wizard runs
    wallet_address = None
    if config_exists:
        try:
            with open(os.path.join(ANIMA_DIR, "anima.json"), "r") as f:
                config = json.load(f)
                wallet_address = config.get("walletAddress")
        except Exception:
            pass

    # Check engine process
    engine_running = is_engine_process_running()

    # Generate QR if we have a real address from the engine
    qr_b64 = None
    if wallet_address and wallet_address.startswith("0x"):
        try:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(wallet_address)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            qr_b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception:
            pass

    return {
        "wallet_address": wallet_address,
        "qr_code": qr_b64,
        "config_exists": config_exists,
        "genesis_staged": genesis_staged,
        "engine_live": engine.get("live", False),
        "engine_running": engine_running,
        "engine_state": engine.get("agent_state"),
        "fund_name": engine.get("fund_name"),
        "turn_count": engine.get("turn_count", 0),
        "creator_wallet": CREATOR_WALLET,
        "status": "running" if engine_running else ("created" if config_exists else "not_created"),
    }


@app.post("/api/genesis/create")
async def create_genesis_agent():
    """
    Stage config files and start the Automaton engine as a background process.
    The engine handles everything: wallet, API key, constitution, SOUL, skills, heartbeat.
    We only provide the genesis prompt and auto-config for non-interactive setup.
    """
    try:
        # Check if already running
        if is_engine_process_running():
            return {"success": True, "message": "Engine already running"}

        # Verify the built engine exists
        dist_path = os.path.join(AUTOMATON_DIR, "dist", "index.js")
        if not os.path.exists(dist_path):
            return {"success": False, "error": "Engine not built. dist/index.js missing."}

        # Stage files to ~/.anima/ for the engine's setup wizard (non-interactive mode)
        os.makedirs(ANIMA_DIR, exist_ok=True)

        # 1. Stage genesis prompt
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                content = f.read()
            with open(os.path.join(ANIMA_DIR, "genesis-prompt.md"), "w") as f:
                f.write(content)

        # 2. Stage auto-config for non-interactive wizard
        with open(os.path.join(ANIMA_DIR, "auto-config.json"), "w") as f:
            json.dump({
                "name": "Anima Fund",
                "creatorAddress": "0x0000000000000000000000000000000000000000",
            }, f)

        # 3. Stage custom VC skills (fund-specific — engine installs its own defaults too)
        skills_src = os.path.join(AUTOMATON_DIR, "skills")
        if os.path.isdir(skills_src):
            skills_dst = os.path.join(ANIMA_DIR, "skills")
            os.makedirs(skills_dst, exist_ok=True)
            for skill_name in os.listdir(skills_src):
                skill_file = os.path.join(skills_src, skill_name, "SKILL.md")
                if os.path.exists(skill_file):
                    target = os.path.join(skills_dst, skill_name)
                    os.makedirs(target, exist_ok=True)
                    with open(skill_file, "r") as f:
                        content = f.read()
                    with open(os.path.join(target, "SKILL.md"), "w") as f:
                        f.write(content)

        # 4. Start the engine via /bin/bash (absolute path — no PATH dependency)
        log_out = open("/var/log/automaton.out.log", "a")
        log_err = open("/var/log/automaton.err.log", "a")
        proc = subprocess.Popen(
            ["/bin/bash", "/app/scripts/start_engine.sh"],
            stdout=log_out,
            stderr=log_err,
            start_new_session=True,
        )

        # Save PID for tracking
        os.makedirs(ANIMA_DIR, exist_ok=True)
        with open(ENGINE_PID_FILE, "w") as f:
            f.write(str(proc.pid))

        return {
            "success": True,
            "message": "Engine starting. The agent will generate its own wallet and begin operating.",
            "creator_wallet": CREATOR_WALLET,
        }

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


@app.get("/api/live/working-memory")
async def live_working_memory():
    return {"items": get_live_working_memory(), "source": "engine"}

@app.get("/api/live/episodic-memory")
async def live_episodic_memory(limit: int = Query(default=50, le=200)):
    return {"events": get_live_episodic_memory(limit), "source": "engine"}

@app.get("/api/live/procedural-memory")
async def live_procedural_memory():
    return {"procedures": get_live_procedural_memory(), "source": "engine"}

@app.get("/api/live/tools")
async def live_installed_tools():
    return {"tools": get_live_installed_tools(), "source": "engine"}

@app.get("/api/live/skills")
async def live_skills():
    return {"skills": get_live_skills(), "source": "engine"}

@app.get("/api/live/metrics")
async def live_metrics(limit: int = Query(default=50, le=200)):
    return {"snapshots": get_live_metric_snapshots(limit), "source": "engine"}

@app.get("/api/live/policy")
async def live_policy(limit: int = Query(default=50, le=200)):
    return {"decisions": get_live_policy_decisions(limit), "source": "engine"}

@app.get("/api/live/soul-history")
async def live_soul_history():
    return {"versions": get_live_soul_history(), "source": "engine"}

@app.get("/api/live/onchain")
async def live_onchain(limit: int = Query(default=50, le=200)):
    return {"transactions": get_live_onchain_transactions(limit), "source": "engine"}

@app.get("/api/live/sessions")
async def live_sessions(limit: int = Query(default=20, le=100)):
    return {"sessions": get_live_session_summaries(limit), "source": "engine"}


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
