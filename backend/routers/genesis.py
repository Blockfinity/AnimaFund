"""
PLATFORM: Genesis agent status, wallet, and engine routes.
All provisioning state lives in MongoDB. Agent execution happens in Conway VMs.
"""
import os
import io
import base64
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import qrcode
import aiohttp

from config import AUTOMATON_DIR, CREATOR_WALLET, CREATOR_ETH_ADDRESS, USDC_CONTRACT, BASE_RPC, CONWAY_API
from agent_state import (
    get_active_agent_id, load_provisioning, save_provisioning,
    get_conway_api_key, get_agent_config, add_nudge,
)
from database import get_db

router = APIRouter(prefix="/api", tags=["genesis"])


async def _conway_get(path: str) -> dict:
    api_key = await get_conway_api_key()
    if not api_key:
        return {"error": "No CONWAY_API_KEY configured"}
    url = f"{CONWAY_API}{path}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(url, headers={"Authorization": f"Bearer {api_key}"}) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


async def _sandbox_exec(sandbox_id: str, command: str, timeout: int = 30) -> dict:
    """Execute via the provider abstraction — works for both Conway and Fly."""
    from sandbox_provider import sandbox_exec
    return await sandbox_exec(sandbox_id, command, timeout)


async def _check_onchain_balance(wallet_address: str) -> dict:
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
# GENESIS STATUS — reads from MongoDB provisioning state
# ═══════════════════════════════════════════════════════════

@router.get("/genesis/status")
async def genesis_status():
    """Agent status — all state from MongoDB provisioning record."""
    agent_id = get_active_agent_id()
    prov = await load_provisioning()

    sandbox_active = prov.get("sandbox", {}).get("status") == "active"
    sandbox_id = prov.get("sandbox", {}).get("id", "")
    terminal_installed = prov.get("tools", {}).get("conway-terminal", {}).get("installed", False)
    engine_deployed = prov.get("tools", {}).get("engine", {}).get("deployed", False)
    wallet_address = prov.get("wallet_address", "")
    skills_loaded = prov.get("skills_loaded", False)

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

    engine_running = False
    engine_live = False
    turn_count = 0
    engine_state = None

    if engine_deployed:
        # Read from webhook cache — this IS real-time data pushed by the daemon inside the sandbox
        from sandbox_poller import get_cache
        cache = get_cache()
        engine_running = bool(cache.get("engine_running"))
        engine_live = engine_running
        phase = cache.get("phase_state", {})
        if phase:
            turn_count = phase.get("turn_count", 0)
            engine_state = phase.get("agent_state", None)

    qr_b64 = _generate_qr(wallet_address) if wallet_address else None

    # Per-agent config from MongoDB
    agent_config = await get_agent_config()
    agent_creator_wallet = agent_config.get("creator_sol_wallet") or CREATOR_WALLET
    agent_creator_eth = agent_config.get("creator_eth_wallet") or CREATOR_ETH_ADDRESS
    agent_name = agent_config.get("name")
    agent_goals = agent_config.get("goals", [])

    return {
        "agent_id": agent_id,
        "wallet_address": wallet_address,
        "engine_wallet": wallet_address,
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
        "sandbox_active": sandbox_active,
        "sandbox_id": sandbox_id,
        "tools_installed": {k: v.get("installed", False) for k, v in prov.get("tools", {}).items()},
    }


@router.post("/genesis/create")
async def create_genesis_agent():
    """DISABLED — agents are created through the provisioning stepper."""
    return {"success": False, "error": "Use the provisioning stepper to deploy the agent inside a Conway VM."}


@router.post("/genesis/reset")
async def reset_genesis_agent():
    """Reset provisioning state. Optionally deletes the sandbox."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id", "")

    if sandbox_id:
        try:
            api_key = await get_conway_api_key()
            if api_key:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.delete(f"{CONWAY_API}/v1/sandboxes/{sandbox_id}",
                        headers={"Authorization": f"Bearer {api_key}"}) as _:
                        pass
        except Exception:
            pass

    # Reset provisioning in MongoDB
    from agent_state import default_provisioning
    await save_provisioning(default_provisioning())

    return {"success": True, "message": "Provisioning state cleared. Ready for fresh provisioning."}


@router.get("/wallet/balance")
async def wallet_balance():
    """On-chain balance for the agent's sandbox wallet + Conway credits."""
    prov = await load_provisioning()
    wallet_address = prov.get("wallet_address", "")

    if not wallet_address:
        agent_config = await get_agent_config()
        if agent_config.get("creator_eth_wallet"):
            wallet_address = agent_config["creator_eth_wallet"]

    if not wallet_address:
        return {"usdc": 0, "eth": 0, "credits_cents": 0, "wallet": None,
                "error": "No wallet — agent not provisioned yet."}

    onchain = await _check_onchain_balance(wallet_address)

    credits_cents = 0
    tier = "unknown"
    credits_data = await _conway_get("/v1/credits/balance")
    if "error" not in credits_data:
        credits_cents = credits_data.get("credits_cents", 0)
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


@router.get("/engine/status")
async def engine_status():
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id", "")
    engine_deployed = prov.get("tools", {}).get("engine", {}).get("deployed", False)

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
        "skills": skills,
        "creator_wallet": CREATOR_WALLET,
        "sandbox_id": sandbox_id,
        "engine_deployed": engine_deployed,
        "source": "sandbox",
    }


@router.get("/engine/logs")
async def engine_logs(lines: int = Query(default=50, le=200)):
    """Engine logs — reads from real-time webhook data."""
    from sandbox_poller import get_cache
    cache = get_cache()
    stdout = cache.get("agent_stdout", "")
    stderr = cache.get("agent_stderr", "")

    # Trim to requested line count
    if stdout:
        stdout = "\n".join(stdout.split("\n")[-lines:])
    if stderr:
        stderr = "\n".join(stderr.split("\n")[-lines:])

    return {"stdout": stdout, "stderr": stderr,
            "agent_id": get_active_agent_id(), "source": "sandbox"}


@router.get("/engine/live")
async def engine_live():
    """Engine live status — reads from real-time webhook data."""
    from sandbox_poller import get_cache
    cache = get_cache()

    # Webhook cache IS the real-time truth — if it says engine is running, it is
    is_running = bool(cache.get("engine_running"))
    phase = cache.get("phase_state", {})

    # Also check provisioning status
    prov = await load_provisioning()
    engine_deployed = prov.get("tools", {}).get("engine", {}).get("deployed", False)

    return {
        "live": is_running,
        "db_exists": is_running or engine_deployed,
        "agent_state": phase.get("agent_state", "running" if is_running else None),
        "turn_count": phase.get("turn_count", 0),
        "source": "webhook" if is_running else ("sandbox" if engine_deployed else "none"),
    }


@router.get("/constitution")
async def get_constitution():
    path = os.path.join(AUTOMATON_DIR, "constitution.md")
    if os.path.exists(path):
        with open(path, "r") as f:
            return {"content": f.read(), "path": path}
    return {"content": "Constitution not found.", "path": None}


@router.get("/genesis/prompt-template")
async def get_prompt_template():
    template_path = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return {"content": f.read()}
    return {"content": "Genesis prompt template not found."}


class PatchSoulRequest(BaseModel):
    content: str


@router.post("/agents/{agent_id}/patch-soul")
async def patch_soul(agent_id: str, req: PatchSoulRequest):
    prov = await load_provisioning(agent_id)
    sandbox_id = prov.get("sandbox", {}).get("id", "")
    if not sandbox_id:
        raise HTTPException(400, "No sandbox provisioned. Cannot patch soul.")
    from routers.agent_setup import _sandbox_write_file
    await _sandbox_write_file(sandbox_id, "/root/.anima/SOUL.md", req.content)
    return {"success": True, "agent_id": agent_id, "soul_size": len(req.content),
            "message": "SOUL.md written to sandbox. Agent will use new soul on next turn.", "target": "sandbox"}


@router.get("/agents/{agent_id}/soul")
async def get_agent_soul(agent_id: str):
    prov = await load_provisioning(agent_id)
    sandbox_id = prov.get("sandbox", {}).get("id", "")
    if not sandbox_id:
        return {"content": None, "exists": False, "agent_id": agent_id, "error": "No sandbox provisioned."}
    r = await _sandbox_exec(sandbox_id, "cat ~/.anima/SOUL.md 2>/dev/null")
    content = r.get("stdout", "")
    if not content or r.get("exit_code", 1) != 0:
        return {"content": None, "exists": False, "agent_id": agent_id}
    return {"content": content, "exists": True, "size": len(content), "agent_id": agent_id, "source": "sandbox"}
