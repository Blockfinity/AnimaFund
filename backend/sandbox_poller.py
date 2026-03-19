"""
PLATFORM: Multi-source data pipeline for the Anima Fund dashboard.
Monitors REMOTE agent VMs via Conway API. No host engine.

Data sources:
  - On-chain RPC (Base)  → wallet USDC + ETH balance
  - Conway API           → API key credits
  - Sandbox daemon       → agent activity (webhook, instant)
  - Sandbox exec         → agent data fallback (poll, only if webhook stale)
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone

import aiohttp

from agent_state import get_active_agent_id, get_conway_api_key, load_provisioning

logger = logging.getLogger("sandbox_poller")

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
USDC_CONTRACT = os.environ.get("USDC_CONTRACT", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")

_cache = {
    "wallet_address": "",
    "wallet_usdc": 0.0,
    "wallet_eth": 0.0,
    "wallet_last_check": None,
    "wallet_error": None,
    "conway_credits_cents": 0,
    "conway_credits_last_check": None,
    "conway_credits_error": None,
    "economics": {},
    "revenue_log": [],
    "decisions_log": [],
    "creator_split_log": [],
    "phase_state": {},
    "agent_stdout": "",
    "agent_stderr": "",
    "engine_running": False,
    "sandbox_id": None,
    "last_update": None,
    "update_source": None,
    "poll_error": None,
}

_update_event = asyncio.Event()
_refresh_task = None
_sandbox_poll_task = None


def get_cache():
    return _cache


def get_update_event():
    return _update_event


def _notify():
    _update_event.set()
    _update_event.clear()


# ═══════════════════════════════════════════════════════════
# WEBHOOK — instant agent activity updates from sandbox daemon
# ═══════════════════════════════════════════════════════════

def update_from_webhook(data: dict):
    if data.get("economics") and isinstance(data["economics"], dict):
        _cache["economics"] = data["economics"]
        # Extract wallet address from economics and save to provisioning
        wallet = data["economics"].get("wallet_address", "")
        if wallet and wallet.startswith("0x"):
            _cache["wallet_address"] = wallet
            # Persist to MongoDB provisioning (async — fire and forget)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_save_wallet_to_db(wallet))
            except Exception:
                pass
    if data.get("revenue_log") is not None:
        _cache["revenue_log"] = data["revenue_log"] if isinstance(data["revenue_log"], list) else []
    if data.get("decisions_log") is not None:
        _cache["decisions_log"] = data["decisions_log"] if isinstance(data["decisions_log"], list) else []
    if data.get("creator_split_log") is not None:
        _cache["creator_split_log"] = data["creator_split_log"] if isinstance(data["creator_split_log"], list) else []
    if data.get("phase_state") is not None and isinstance(data.get("phase_state"), dict):
        _cache["phase_state"] = data["phase_state"]
    if data.get("agent_stdout") is not None:
        _cache["agent_stdout"] = data["agent_stdout"]
    if data.get("agent_stderr") is not None:
        _cache["agent_stderr"] = data["agent_stderr"]
    if "engine_running" in data:
        _cache["engine_running"] = bool(data["engine_running"])
    _cache["last_update"] = datetime.now(timezone.utc).isoformat()
    _cache["update_source"] = "webhook"
    _notify()


async def _save_wallet_to_db(wallet: str):
    """Persist wallet address from webhook data to MongoDB provisioning."""
    try:
        from agent_state import save_provisioning, load_provisioning
        prov = await load_provisioning()
        if prov.get("wallet_address") != wallet:
            prov["wallet_address"] = wallet
            await save_provisioning(prov)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# HELPERS — read from MongoDB via agent_state
# ═══════════════════════════════════════════════════════════

async def _get_sandbox_id():
    prov = await load_provisioning()
    return prov.get("sandbox", {}).get("id") or None


async def _get_wallet_address() -> str:
    prov = await load_provisioning()
    return prov.get("wallet_address", "")


async def _check_onchain_balance(wallet_address: str) -> dict:
    if not wallet_address or not wallet_address.startswith("0x"):
        return {"usdc": 0.0, "eth": 0.0, "error": None}
    try:
        addr_padded = "0x70a08231" + wallet_address[2:].lower().zfill(64)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            usdc_task = session.post(BASE_RPC, json={
                "jsonrpc": "2.0", "id": 1, "method": "eth_call",
                "params": [{"to": USDC_CONTRACT, "data": addr_padded}, "latest"]
            })
            eth_task = session.post(BASE_RPC, json={
                "jsonrpc": "2.0", "id": 2, "method": "eth_getBalance",
                "params": [wallet_address, "latest"]
            })
            async with usdc_task as usdc_resp, eth_task as eth_resp:
                usdc_data = await usdc_resp.json()
                eth_data = await eth_resp.json()
            usdc = int(usdc_data.get("result", "0x0"), 16) / 1e6
            eth = int(eth_data.get("result", "0x0"), 16) / 1e18
        return {"usdc": usdc, "eth": eth, "error": None}
    except Exception as e:
        return {"usdc": 0.0, "eth": 0.0, "error": str(e)}


async def _fetch_conway_credits() -> dict:
    api_key = await get_conway_api_key()
    if not api_key:
        return {"credits_cents": 0, "error": "No API key"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(
                f"{CONWAY_API}/v1/credits/balance",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"credits_cents": data.get("credits_cents", 0), "error": None}
                return {"credits_cents": 0, "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"credits_cents": 0, "error": str(e)}


async def _noop_wallet():
    return {"usdc": 0.0, "eth": 0.0, "error": None}


# ═══════════════════════════════════════════════════════════
# UNIFIED REFRESH — all external sources, parallel, every 10s
# ═══════════════════════════════════════════════════════════

async def _unified_refresh_loop():
    while True:
        try:
            wallet_addr = await _get_wallet_address()
            _cache["sandbox_id"] = await _get_sandbox_id()
            if wallet_addr:
                _cache["wallet_address"] = wallet_addr

            wallet_result, credits_result = await asyncio.gather(
                _check_onchain_balance(wallet_addr) if wallet_addr else _noop_wallet(),
                _fetch_conway_credits(),
                return_exceptions=True,
            )

            changed = False

            if isinstance(wallet_result, dict):
                if (_cache["wallet_usdc"] != wallet_result["usdc"]
                        or _cache["wallet_eth"] != wallet_result["eth"]):
                    changed = True
                _cache["wallet_usdc"] = wallet_result["usdc"]
                _cache["wallet_eth"] = wallet_result["eth"]
                _cache["wallet_error"] = wallet_result.get("error")
                _cache["wallet_last_check"] = datetime.now(timezone.utc).isoformat()

            if isinstance(credits_result, dict):
                if _cache["conway_credits_cents"] != credits_result["credits_cents"]:
                    changed = True
                _cache["conway_credits_cents"] = credits_result["credits_cents"]
                _cache["conway_credits_error"] = credits_result.get("error")
                _cache["conway_credits_last_check"] = datetime.now(timezone.utc).isoformat()

            if changed:
                _notify()

        except Exception as e:
            logger.error(f"Unified refresh: {e}")
        await asyncio.sleep(10)


# ═══════════════════════════════════════════════════════════
# SANDBOX POLL — fallback when webhooks are stale
# ═══════════════════════════════════════════════════════════

async def _sandbox_exec_poll(sandbox_id, command):
    """Execute a command in the sandbox using the correct provider."""
    from sandbox_provider import sandbox_exec
    try:
        result = await sandbox_exec(sandbox_id, command, timeout=15)
        return result.get("stdout", "")
    except Exception:
        return ""


async def _sandbox_poll_loop():
    while True:
        try:
            sandbox_id = await _get_sandbox_id()
            _cache["sandbox_id"] = sandbox_id
            if not sandbox_id:
                _cache["poll_error"] = "no_sandbox"
                await asyncio.sleep(20)
                continue

            if _cache["last_update"] and _cache["update_source"] == "webhook":
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(_cache["last_update"])).total_seconds()
                    if age < 20:
                        await asyncio.sleep(20)
                        continue
                except Exception:
                    pass

            raw = await _sandbox_exec_poll(sandbox_id, (
                "echo '===ECONOMICS===' && cat ~/.anima/economics.json 2>/dev/null || echo 'null' && "
                "echo '===REVENUE===' && cat ~/.anima/revenue-log.json 2>/dev/null || echo '[]' && "
                "echo '===DECISIONS===' && cat ~/.anima/decisions-log.json 2>/dev/null || echo '[]' && "
                "echo '===PHASE===' && cat ~/.anima/phase-state.json 2>/dev/null || echo '{}' && "
                "echo '===ENGINE===' && pgrep -f 'bundle.mjs' > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED' && "
                "echo '===STDOUT===' && tail -80 /var/log/automaton.out.log 2>/dev/null || echo ''"
            ))
            if not raw:
                await asyncio.sleep(20)
                continue

            sections = {}
            key, lines = None, []
            for line in raw.split("\n"):
                if line.startswith("===") and line.endswith("==="):
                    if key:
                        sections[key] = "\n".join(lines).strip()
                    key, lines = line.strip("="), []
                else:
                    lines.append(line)
            if key:
                sections[key] = "\n".join(lines).strip()

            def p(s, d):
                if not s or s == "null":
                    return d
                try:
                    return json.loads(s)
                except Exception:
                    return d

            _cache["economics"] = p(sections.get("ECONOMICS"), _cache["economics"])
            _cache["revenue_log"] = p(sections.get("REVENUE"), _cache["revenue_log"])
            _cache["decisions_log"] = p(sections.get("DECISIONS"), _cache["decisions_log"])
            _cache["phase_state"] = p(sections.get("PHASE"), _cache["phase_state"])
            _cache["engine_running"] = sections.get("ENGINE", "").strip() == "RUNNING"
            _cache["agent_stdout"] = sections.get("STDOUT", "")
            _cache["poll_error"] = None
            _cache["last_update"] = datetime.now(timezone.utc).isoformat()
            _cache["update_source"] = "poll"
            _notify()
        except Exception as e:
            _cache["poll_error"] = str(e)
            logger.error(f"Sandbox poll: {e}")
        await asyncio.sleep(20)


# ═══════════════════════════════════════════════════════════
# LIFECYCLE
# ═══════════════════════════════════════════════════════════

def start_poller():
    global _refresh_task, _sandbox_poll_task
    if not _refresh_task:
        _refresh_task = asyncio.create_task(_unified_refresh_loop())
    if not _sandbox_poll_task:
        _sandbox_poll_task = asyncio.create_task(_sandbox_poll_loop())


def stop_poller():
    global _refresh_task, _sandbox_poll_task
    for t in [_refresh_task, _sandbox_poll_task]:
        if t:
            t.cancel()
    _refresh_task = None
    _sandbox_poll_task = None
