"""
Genesis agent status, wallet, and engine routes.
ALL state comes from the Conway Cloud sandbox — nothing runs on the host.
"""
import os
import io
import json
import base64
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import qrcode
import aiohttp

from config import AUTOMATON_DIR, CREATOR_WALLET, CREATOR_ETH_ADDRESS, USDC_CONTRACT, BASE_RPC
from database import get_db

router = APIRouter(prefix="/api", tags=["genesis"])

# ─── Helpers ────────────────────────────────────────────

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
CONWAY_API_KEY = os.environ.get("CONWAY_API_KEY", "")

def _get_active_agent_id() -> str:
    try:
        with open("/tmp/anima_active_agent_id", "r") as f:
            return f.read().strip() or "anima-fund"
    except FileNotFoundError:
        return "anima-fund"


def _load_prov_status() -> dict:
    """Load provisioning status for the active agent — this IS the source of truth."""
    agent_id = _get_active_agent_id()
    home = os.path.expanduser("~")
    if agent_id == "anima-fund":
        path = os.path.join(home, ".anima", "provisioning-status.json")
    else:
        path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sandbox": {"status": "none", "id": ""}, "tools": {}, "skills_loaded": False,
                "nudges": [], "wallet_address": "", "last_updated": ""}


async def _conway_get(path: str) -> dict:
    """GET request to Conway API using the API key."""
    if not CONWAY_API_KEY:
        return {"error": "No CONWAY_API_KEY configured"}
    url = f"{CONWAY_API}{path}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(url, headers={"Authorization": f"Bearer {CONWAY_API_KEY}"}) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


async def _sandbox_exec(sandbox_id: str, command: str, timeout: int = 30) -> dict:
    """Execute a command inside the sandbox."""
    if not CONWAY_API_KEY:
        return {"stdout": "", "stderr": "No CONWAY_API_KEY", "exit_code": 1}
    url = f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/exec"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout + 5)) as session:
        try:
            async with session.post(url,
                headers={"Authorization": f"Bearer {CONWAY_API_KEY}", "Content-Type": "application/json"},
                json={"command": command, "timeout": timeout}) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                return {"stdout": "", "stderr": f"HTTP {resp.status}", "exit_code": 1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": 1}


async def _check_onchain_balance(wallet_address: str) -> dict:
    """Check USDC + ETH balance on Base chain via RPC."""
    if not wallet_address or not wallet_address.startswith("0x"):
        return {"usdc": 0, "eth": 0, "error": None}
    try:
        addr_padded = "0x70a08231" + wallet_address[2:].lower().zfill(64)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.post(BASE_RPC, json={
                "jsonrpc": "2.0", "id": 1, "method": "eth_call",
                "params": [{"to": USDC_CONTRACT, "data": addr_padded}, "latest"]
            }) as resp:
                data = await resp.json()
                usdc = int(data.get("result", "0x0"), 16) / 1e6

            async with session.post(BASE_RPC, json={
                "jsonrpc": "2.0", "id": 2, "method": "eth_getBalance",
                "params": [wallet_address, "latest"]
            }) as resp:
                data = await resp.json()
                eth = int(data.get("result", "0x0"), 16) / 1e18

        return {"usdc": usdc, "eth": eth, "error": None}
    except Exception as e:
        return {"usdc": 0, "eth": 0, "error": str(e)}


def _generate_qr(wallet_address: str) -> str:
    """Generate QR code as base64 data URI."""
    try:
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(wallet_address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
# GENESIS STATUS — reads from sandbox provisioning state
# ═══════════════════════════════════════════════════════════

@router.get("/genesis/status")
async def genesis_status():
    """Agent status — all state comes from the sandbox provisioning status.
    Nothing is read from the host filesystem except the provisioning JSON."""
    agent_id = _get_active_agent_id()
    prov = _load_prov_status()

    sandbox_active = prov["sandbox"].get("status") == "active"
    sandbox_id = prov["sandbox"].get("id", "")
    terminal_installed = prov["tools"].get("conway-terminal", {}).get("installed", False)
    engine_deployed = prov["tools"].get("engine", {}).get("deployed", False)
    wallet_address = prov.get("wallet_address", "")
    skills_loaded = prov.get("skills_loaded", False)

    # Determine stage from provisioning state
    if engine_deployed:
        stage = "running"
    elif skills_loaded:
        stage = "skills_loaded"
    elif terminal_installed:
        stage = "provisioning"
    elif sandbox_active:
        stage = "sandbox_created"
    else:
        stage = "not_created"

    # Check if engine is actually running inside the sandbox
    engine_running = False
    engine_live = False
    turn_count = 0
    engine_state = None

    if engine_deployed and sandbox_id:
        try:
            r = await _sandbox_exec(sandbox_id, "pgrep -f 'bundle.mjs.*--run' > /dev/null 2>&1 && echo RUNNING || echo STOPPED", timeout=10)
            engine_running = "RUNNING" in r.get("stdout", "")
            if engine_running:
                engine_live = True
                # Try to get turn count from sandbox state.db
                r2 = await _sandbox_exec(sandbox_id, "sqlite3 ~/.anima/state.db 'SELECT COUNT(*) FROM turns' 2>/dev/null || echo 0", timeout=10)
                try:
                    turn_count = int(r2.get("stdout", "0").strip())
                except ValueError:
                    turn_count = 0
                # Get engine state
                r3 = await _sandbox_exec(sandbox_id, "sqlite3 ~/.anima/state.db \"SELECT value FROM kv WHERE key='agent_state' LIMIT 1\" 2>/dev/null || echo ''", timeout=10)
                engine_state = r3.get("stdout", "").strip().strip('"') or None
        except Exception:
            pass

    # QR code for wallet
    qr_b64 = _generate_qr(wallet_address) if wallet_address else None

    # Per-agent creator wallets from MongoDB
    agent_creator_wallet = CREATOR_WALLET
    agent_creator_eth = CREATOR_ETH_ADDRESS
    agent_name = None
    agent_goals = []

    try:
        col = get_db()["agents"]
        agent_doc = await col.find_one({"agent_id": agent_id}, {"_id": 0})
        if agent_doc:
            if agent_doc.get("creator_sol_wallet"):
                agent_creator_wallet = agent_doc["creator_sol_wallet"]
            if agent_doc.get("creator_eth_wallet"):
                agent_creator_eth = agent_doc["creator_eth_wallet"]
            agent_name = agent_doc.get("name")
            agent_goals = agent_doc.get("goals", [])
    except Exception:
        pass

    return {
        "agent_id": agent_id,
        "wallet_address": wallet_address,
        "engine_wallet": wallet_address,  # same — wallet lives in sandbox
        "wallet_mismatch": False,
        "qr_code": qr_b64,
        "config_exists": engine_deployed,
        "wallet_exists": bool(wallet_address),
        "api_key_exists": terminal_installed,
        "genesis_staged": engine_deployed,
        "engine_live": engine_live,
        "engine_running": engine_running,
        "engine_state": engine_state,
        "fund_name": agent_name or "Anima Fund",
        "turn_count": turn_count,
        "creator_wallet": agent_creator_wallet,
        "creator_eth_address": agent_creator_eth,
        "goals": agent_goals,
        "stage": stage,
        "status": "running" if engine_running else ("created" if engine_deployed else "not_created"),
        # Sandbox info for dashboard
        "sandbox_active": sandbox_active,
        "sandbox_id": sandbox_id,
        "tools_installed": {k: v.get("installed", False) for k, v in prov["tools"].items()},
    }


# ═══════════════════════════════════════════════════════════
# CREATE — DISABLED. Use provisioning stepper.
# ═══════════════════════════════════════════════════════════

@router.post("/genesis/create")
async def create_genesis_agent():
    """DISABLED — agents must be created through the provisioning stepper.
    The agent runs inside a Conway Cloud sandbox, not on the host."""
    return {
        "success": False,
        "error": "Direct agent creation is disabled. Use the provisioning stepper to create a sandbox, install tools, and deploy the agent inside the sandboxed environment. Nothing runs on the host.",
    }


# ═══════════════════════════════════════════════════════════
# RESET — Clears provisioning state
# ═══════════════════════════════════════════════════════════

@router.post("/genesis/reset")
async def reset_genesis_agent():
    """Reset provisioning state. Optionally deletes the sandbox."""
    agent_id = _get_active_agent_id()
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")

    # Optionally delete the sandbox from Conway Cloud
    if sandbox_id:
        try:
            await _conway_get(f"/v1/sandboxes/{sandbox_id}")  # verify it exists
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.delete(f"{CONWAY_API}/v1/sandboxes/{sandbox_id}",
                    headers={"Authorization": f"Bearer {CONWAY_API_KEY}"}) as _:
                    pass
        except Exception:
            pass

    # Clear the provisioning status file
    home = os.path.expanduser("~")
    if agent_id == "anima-fund":
        path = os.path.join(home, ".anima", "provisioning-status.json")
    else:
        path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    return {"success": True, "message": "Provisioning state cleared. Sandbox deleted. Ready for fresh provisioning."}


# ═══════════════════════════════════════════════════════════
# WALLET BALANCE — reads from sandbox wallet via on-chain RPC
# ═══════════════════════════════════════════════════════════

@router.get("/wallet/balance")
async def wallet_balance():
    """On-chain balance for the agent's sandbox wallet + Conway credits."""
    agent_id = _get_active_agent_id()
    prov = _load_prov_status()
    wallet_address = prov.get("wallet_address", "")

    if not wallet_address:
        # Check MongoDB for any stored wallet
        try:
            col = get_db()["agents"]
            agent_doc = await col.find_one({"agent_id": agent_id}, {"_id": 0})
            if agent_doc and agent_doc.get("creator_eth_wallet"):
                wallet_address = agent_doc["creator_eth_wallet"]
        except Exception:
            pass

    if not wallet_address:
        return {"usdc": 0, "eth": 0, "credits_cents": 0, "wallet": None,
                "error": "No wallet — agent not provisioned yet. Run 'Install Terminal' step to create the wallet inside the sandbox."}

    onchain = await _check_onchain_balance(wallet_address)

    # Conway credits (from API key, not agent wallet)
    credits_cents = 0
    tier = "unknown"
    credits_data = await _conway_get("/v1/credits/balance")
    if "error" not in credits_data:
        credits_cents = credits_data.get("credits_cents", credits_data.get("creditsCents", credits_data.get("credits", 0)))
        if isinstance(credits_cents, (int, float)):
            credits_cents = int(credits_cents)
            if credits_cents <= 0:
                tier = "critical"
            elif credits_cents < 50:
                tier = "survival"
            elif credits_cents < 500:
                tier = "conservation"
            else:
                tier = "normal"

    return {
        "wallet": wallet_address,
        "usdc": onchain["usdc"],
        "eth": onchain["eth"],
        "credits_cents": credits_cents,
        "tier": tier,
        "onchain_error": onchain["error"],
        "wallet_mismatch": False,
        "source": "sandbox",
    }


# ═══════════════════════════════════════════════════════════
# ENGINE STATUS & LOGS — from sandbox, not host
# ═══════════════════════════════════════════════════════════

@router.get("/engine/status")
async def engine_status():
    """Engine status — reads from sandbox, not host."""
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")
    engine_deployed = prov["tools"].get("engine", {}).get("deployed", False)

    skills = []
    skills_dir = os.path.join(AUTOMATON_DIR, "skills")
    if os.path.isdir(skills_dir):
        for s in os.listdir(skills_dir):
            if os.path.exists(os.path.join(skills_dir, s, "SKILL.md")):
                skills.append(s)

    return {
        "engine": "Anima Fund Runtime",
        "version": "sandbox",
        "repo_present": os.path.isdir(AUTOMATON_DIR),
        "built": os.path.exists(os.path.join(AUTOMATON_DIR, "dist", "bundle.mjs")),
        "genesis_prompt_lines": 0,
        "skills": skills,
        "creator_wallet": CREATOR_WALLET,
        "active_data_dir": f"sandbox:{sandbox_id}" if sandbox_id else "none",
        "sandbox_id": sandbox_id,
        "engine_deployed": engine_deployed,
        "source": "sandbox",
    }


@router.get("/engine/logs")
async def engine_logs(lines: int = Query(default=50, le=200)):
    """Engine logs — reads from inside the sandbox, not host filesystem."""
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")

    if not sandbox_id:
        return {"stdout": "", "stderr": "", "agent_id": _get_active_agent_id(),
                "error": "No sandbox — provision one first.", "source": "none"}

    r_out = await _sandbox_exec(sandbox_id, f"tail -{lines} /var/log/automaton.out.log 2>/dev/null || echo ''")
    r_err = await _sandbox_exec(sandbox_id, f"tail -{lines} /var/log/automaton.err.log 2>/dev/null || echo ''")

    return {
        "stdout": r_out.get("stdout", ""),
        "stderr": r_err.get("stdout", ""),
        "agent_id": _get_active_agent_id(),
        "source": "sandbox",
    }


@router.get("/engine/live")
async def engine_live():
    """Engine live status — checks sandbox, not host."""
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")
    engine_deployed = prov["tools"].get("engine", {}).get("deployed", False)

    if not sandbox_id or not engine_deployed:
        return {"live": False, "db_exists": False, "agent_state": None, "turn_count": 0, "source": "none"}

    try:
        r = await _sandbox_exec(sandbox_id, "pgrep -f 'bundle.mjs.*--run' > /dev/null 2>&1 && echo RUNNING || echo STOPPED", timeout=10)
        is_running = "RUNNING" in r.get("stdout", "")

        turn_count = 0
        agent_state = None
        db_exists = False

        if is_running:
            r2 = await _sandbox_exec(sandbox_id, "test -f ~/.anima/state.db && echo EXISTS || echo NONE", timeout=5)
            db_exists = "EXISTS" in r2.get("stdout", "")

            if db_exists:
                r3 = await _sandbox_exec(sandbox_id, "sqlite3 ~/.anima/state.db 'SELECT COUNT(*) FROM turns' 2>/dev/null || echo 0", timeout=10)
                try:
                    turn_count = int(r3.get("stdout", "0").strip())
                except ValueError:
                    pass
                r4 = await _sandbox_exec(sandbox_id, "sqlite3 ~/.anima/state.db \"SELECT value FROM kv WHERE key='agent_state' LIMIT 1\" 2>/dev/null || echo ''", timeout=10)
                agent_state = r4.get("stdout", "").strip().strip('"') or None

        return {"live": is_running, "db_exists": db_exists, "agent_state": agent_state,
                "turn_count": turn_count, "source": "sandbox"}
    except Exception as e:
        return {"live": False, "db_exists": False, "agent_state": None, "turn_count": 0,
                "error": str(e), "source": "sandbox"}


# ═══════════════════════════════════════════════════════════
# CONSTITUTION & PROMPT
# ═══════════════════════════════════════════════════════════

@router.get("/constitution")
async def get_constitution():
    """Read constitution from the source repo (template, not agent-specific)."""
    for path in [
        os.path.join(AUTOMATON_DIR, "constitution.md"),
    ]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return {"content": f.read(), "path": path}
    return {"content": "Constitution not found.", "path": None}


@router.get("/genesis/prompt-template")
async def get_prompt_template():
    """Return the genesis prompt template (from source repo, not host state)."""
    template_path = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return {"content": f.read()}
    return {"content": "Genesis prompt template not found."}


# ═══════════════════════════════════════════════════════════
# SOUL PATCH — writes to sandbox, not host
# ═══════════════════════════════════════════════════════════

class PatchSoulRequest(BaseModel):
    content: str


@router.post("/agents/{agent_id}/patch-soul")
async def patch_soul(agent_id: str, req: PatchSoulRequest):
    """Write SOUL.md into the sandbox, not the host filesystem."""
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")
    if not sandbox_id:
        raise HTTPException(400, "No sandbox provisioned. Cannot patch soul.")

    from routers.agent_setup import _sandbox_write_file
    await _sandbox_write_file(sandbox_id, "/root/.anima/SOUL.md", req.content)

    return {
        "success": True,
        "agent_id": agent_id,
        "soul_size": len(req.content),
        "message": f"SOUL.md written to sandbox ({len(req.content)} chars). Agent will use new soul on next turn.",
        "target": "sandbox",
    }


@router.get("/agents/{agent_id}/soul")
async def get_agent_soul(agent_id: str):
    """Read SOUL.md from the sandbox, not the host."""
    prov = _load_prov_status()
    sandbox_id = prov["sandbox"].get("id", "")
    if not sandbox_id:
        return {"content": None, "exists": False, "agent_id": agent_id, "error": "No sandbox provisioned."}

    r = await _sandbox_exec(sandbox_id, "cat ~/.anima/SOUL.md 2>/dev/null")
    content = r.get("stdout", "")
    if not content or r.get("exit_code", 1) != 0:
        return {"content": None, "exists": False, "agent_id": agent_id}

    return {"content": content, "exists": True, "size": len(content), "agent_id": agent_id, "source": "sandbox"}
