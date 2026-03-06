"""
Anima Fund - Autonomous AI-to-AI VC Fund Platform
FastAPI Backend Server

This server is a VIEWER — it reads from the Automaton engine's state.db and displays
whatever the AI has created. It does NOT prescribe structure, seed data, or make decisions.

The only write action is "Create Genesis Agent" which generates a wallet and stages config.
"""
import os
import io
import json
import base64
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from eth_account import Account
import qrcode
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

@app.get("/api/genesis/status")
async def genesis_status():
    """Check if the genesis agent has been created and what state it's in."""
    engine = is_engine_live()
    wallet_exists = os.path.exists(os.path.join(ANIMA_DIR, "wallet.json"))
    genesis_staged = os.path.exists(os.path.join(ANIMA_DIR, "genesis-prompt.md"))

    wallet_address = None
    if wallet_exists:
        try:
            with open(os.path.join(ANIMA_DIR, "wallet.json"), "r") as f:
                wallet_data = json.load(f)
                acct = Account.from_key(wallet_data["privateKey"])
                wallet_address = acct.address
        except Exception:
            pass

    # Also check MongoDB for stored genesis data
    mongo_genesis = await db.genesis.find_one({"type": "founder"}, {"_id": 0})

    # If wallet file doesn't exist but MongoDB has stale data, clean it
    if not wallet_exists and mongo_genesis:
        await db.genesis.delete_many({"type": "founder"})
        mongo_genesis = None

    return {
        "wallet_exists": wallet_exists,
        "wallet_address": wallet_address,
        "genesis_staged": genesis_staged,
        "engine_live": engine.get("live", False),
        "engine_state": engine.get("agent_state"),
        "turn_count": engine.get("turn_count", 0),
        "creator_wallet": CREATOR_WALLET,
        "status": (mongo_genesis or {}).get("status", "not_created"),
    }


@app.post("/api/genesis/create")
async def create_genesis_agent():
    """
    Create the genesis agent:
    1. Generate EVM wallet
    2. Stage genesis prompt, constitution, skills
    3. Build the Automaton runtime (pnpm install + build)
    4. Return wallet address + QR code for funding
    """
    try:
        # Step 1: Create directories
        os.makedirs(ANIMA_DIR, exist_ok=True)
        os.makedirs(os.path.join(ANIMA_DIR, "skills"), exist_ok=True)

        # Step 2: Generate EVM wallet
        wallet_path = os.path.join(ANIMA_DIR, "wallet.json")
        if os.path.exists(wallet_path):
            with open(wallet_path, "r") as f:
                wallet_data = json.load(f)
                acct = Account.from_key(wallet_data["privateKey"])
                wallet_address = acct.address
        else:
            acct = Account.create()
            pk = acct.key.hex() if isinstance(acct.key, bytes) else acct.key
            if not pk.startswith("0x"):
                pk = "0x" + pk
            wallet_data = {"privateKey": pk, "createdAt": datetime.now(timezone.utc).isoformat()}
            with open(wallet_path, "w") as f:
                json.dump(wallet_data, f, indent=2)
            os.chmod(wallet_path, 0o600)
            wallet_address = acct.address

        # Step 3: Stage genesis prompt
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        genesis_staged = False
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                content = f.read()
            with open(os.path.join(ANIMA_DIR, "genesis-prompt.md"), "w") as f:
                f.write(content)
            genesis_staged = True

        # Step 4: Install constitution (read-only)
        const_src = os.path.join(AUTOMATON_DIR, "constitution.md")
        const_installed = False
        if os.path.exists(const_src):
            with open(const_src, "r") as f:
                content = f.read()
            const_dst = os.path.join(ANIMA_DIR, "constitution.md")
            with open(const_dst, "w") as f:
                f.write(content)
            try:
                os.chmod(const_dst, 0o444)
            except Exception:
                pass
            const_installed = True

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
                        content = f.read()
                    with open(os.path.join(target_dir, "SKILL.md"), "w") as f:
                        f.write(content)
                    skills_installed.append(skill_name)

        # Step 6: Write auto-config for non-interactive wizard
        auto_config = {
            "name": "Anima Fund",
            "creatorAddress": "0x0000000000000000000000000000000000000000",
        }
        with open(os.path.join(ANIMA_DIR, "auto-config.json"), "w") as f:
            json.dump(auto_config, f, indent=2)

        # Step 7: Build the Automaton runtime
        import subprocess
        dist_path = os.path.join(AUTOMATON_DIR, "dist", "index.js")
        build_status = "already_built" if os.path.exists(dist_path) else "building"
        build_error = None

        if not os.path.exists(dist_path):
            try:
                # Enable corepack + install pnpm + build
                build_cmd = f"cd {AUTOMATON_DIR} && /usr/bin/corepack enable 2>/dev/null; /usr/bin/pnpm install --no-frozen-lockfile 2>&1 && /usr/bin/pnpm build 2>&1"
                proc = subprocess.run(
                    ["bash", "-c", build_cmd],
                    capture_output=True, text=True, timeout=180,
                    env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
                )
                if proc.returncode == 0:
                    build_status = "built"
                else:
                    build_status = "build_failed"
                    build_error = (proc.stdout + proc.stderr)[-1000:]
            except subprocess.TimeoutExpired:
                build_status = "build_timeout"
                build_error = "Build timed out after 180 seconds"
            except Exception as e:
                build_status = "build_error"
                build_error = str(e)

        # Step 7: Generate QR code
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(wallet_address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # Step 8: Store in MongoDB
        await db.genesis.update_one(
            {"type": "founder"},
            {"$set": {
                "wallet_address": wallet_address,
                "creator_wallet": CREATOR_WALLET,
                "genesis_staged": genesis_staged,
                "constitution_installed": const_installed,
                "skills_installed": skills_installed,
                "build_status": build_status,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "created_awaiting_funding",
            }},
            upsert=True,
        )

        return {
            "success": build_status in ("built", "already_built"),
            "wallet_address": wallet_address,
            "qr_code": f"data:image/png;base64,{qr_b64}",
            "genesis_staged": genesis_staged,
            "constitution_installed": const_installed,
            "skills_installed": skills_installed,
            "build_status": build_status,
            "build_error": build_error,
            "creator_wallet": CREATOR_WALLET,
            "next_step": f"Fund wallet {wallet_address} with USDC on Base to start the agent.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/genesis/qr/{address}")
async def genesis_qr(address: str):
    """Generate a QR code for a wallet address."""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(address)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/genesis/start")
async def start_genesis_engine():
    """Start the Automaton engine as a background process."""
    import subprocess

    dist_path = os.path.join(AUTOMATON_DIR, "dist", "index.js")

    # If Automaton isn't built, build it now
    if not os.path.exists(dist_path):
        try:
            build_cmd = f"cd {AUTOMATON_DIR} && /usr/bin/corepack enable 2>/dev/null; /usr/bin/pnpm install --no-frozen-lockfile 2>&1 && /usr/bin/pnpm build 2>&1"
            proc = subprocess.run(
                ["bash", "-c", build_cmd],
                capture_output=True, text=True, timeout=180,
                env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
            )
            if proc.returncode != 0:
                return {"started": False, "error": f"Build failed: {(proc.stdout + proc.stderr)[-500:]}"}
        except subprocess.TimeoutExpired:
            return {"started": False, "error": "Build timed out"}

    wallet_path = os.path.join(ANIMA_DIR, "wallet.json")

    # If wallet file missing but we have it in MongoDB, recreate
    if not os.path.exists(wallet_path):
        mongo_genesis = await db.genesis.find_one({"type": "founder"})
        if not mongo_genesis or not mongo_genesis.get("wallet_address"):
            return {"started": False, "error": "No agent created yet. Click 'Create Genesis Agent' first."}
        # Need to create a new wallet since we can't recover the private key from just the address
        # Force user to re-create
        return {"started": False, "error": "Wallet files missing (new deployment). Click 'Create Genesis Agent' to generate a new wallet."}

    # Ensure genesis prompt and constitution are staged
    genesis_path = os.path.join(ANIMA_DIR, "genesis-prompt.md")
    if not os.path.exists(genesis_path):
        genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(genesis_src):
            with open(genesis_src, "r") as f:
                content = f.read()
            with open(genesis_path, "w") as f:
                f.write(content)

    const_path = os.path.join(ANIMA_DIR, "constitution.md")
    if not os.path.exists(const_path):
        const_src = os.path.join(AUTOMATON_DIR, "constitution.md")
        if os.path.exists(const_src):
            with open(const_src, "r") as f:
                content = f.read()
            with open(const_path, "w") as f:
                f.write(content)

    # Check if already running
    try:
        check = subprocess.run(["pgrep", "-f", "dist/index.js.*--run"], capture_output=True, text=True)
        if check.returncode == 0:
            return {"started": True, "message": "Engine already running", "pid": check.stdout.strip()}
    except Exception:
        pass

    # Start the engine
    try:
        proc = subprocess.Popen(
            ["/usr/bin/node", dist_path, "--run"],
            cwd=AUTOMATON_DIR,
            stdout=open("/var/log/automaton.out.log", "a"),
            stderr=open("/var/log/automaton.err.log", "a"),
            env={**os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin"},
            start_new_session=True,
        )

        await db.genesis.update_one(
            {"type": "founder"},
            {"$set": {"status": "engine_starting", "pid": proc.pid, "started_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

        return {"started": True, "pid": proc.pid, "message": "Engine starting."}

    except Exception as e:
        return {"started": False, "error": str(e)}


@app.get("/api/genesis/qr-base64/{address}")
async def genesis_qr_base64(address: str):
    """Generate a QR code as base64 string for embedding in frontend."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(address)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return {"qr": f"data:image/png;base64,{b64}", "address": address}


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


@app.post("/api/genesis/stop")
async def stop_genesis_engine():
    """Stop the Automaton engine process."""
    import subprocess
    try:
        result = subprocess.run(["pkill", "-f", "dist/index.js.*--run"], capture_output=True, text=True)
        if result.returncode == 0:
            await db.genesis.update_one({"type": "founder"}, {"$set": {"status": "stopped"}}, upsert=True)
            return {"stopped": True}
        return {"stopped": False, "error": "No engine process found"}
    except Exception as e:
        return {"stopped": False, "error": str(e)}

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
