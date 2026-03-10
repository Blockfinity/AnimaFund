"""
Multi-source data pipeline for the Anima Fund dashboard.

Architecture:
  - ONE unified refresh cycle gathers all external data in parallel
  - Webhook handler provides instant agent activity updates
  - SSE stream is the single source of truth for the entire frontend

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

logger = logging.getLogger("sandbox_poller")

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
USDC_CONTRACT = os.environ.get("USDC_CONTRACT", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")


def _get_conway_api_key() -> str:
    """Get Conway API key for the active agent — reads per-agent provisioning status first."""
    agent_id = _get_active_agent_id()
    home = os.path.expanduser("~")
    if agent_id == "anima-fund":
        prov_path = os.path.join(home, ".anima", "provisioning-status.json")
    else:
        prov_path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")
    try:
        with open(prov_path, "r") as f:
            key = json.load(f).get("conway_api_key", "")
            if key:
                return key
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return os.environ.get("CONWAY_API_KEY", "")

_cache = {
    # ── On-chain wallet (source: Base RPC) ──
    "wallet_address": "",
    "wallet_usdc": 0.0,
    "wallet_eth": 0.0,
    "wallet_last_check": None,
    "wallet_error": None,

    # ── Conway API credits (source: Conway API) ──
    "conway_credits_cents": 0,
    "conway_credits_last_check": None,
    "conway_credits_error": None,

    # ── Agent activity (source: webhook from sandbox daemon) ──
    "economics": {},
    "revenue_log": [],
    "decisions_log": [],
    "creator_split_log": [],
    "phase_state": {},
    "agent_stdout": "",
    "agent_stderr": "",
    "engine_running": False,

    # ── Meta ──
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
    """Wake all SSE listeners."""
    _update_event.set()
    _update_event.clear()


# ═══════════════════════════════════════════════════════════
# WEBHOOK — instant agent activity updates from sandbox daemon
# ═══════════════════════════════════════════════════════════

def update_from_webhook(data: dict):
    """Called by webhook endpoint — instant cache update + SSE notify."""
    if data.get("economics") and isinstance(data["economics"], dict):
        _cache["economics"] = data["economics"]
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


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _load_prov_status() -> dict:
    """Load provisioning status for the active agent."""
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
        return {}


def _get_active_agent_id() -> str:
    try:
        with open("/tmp/anima_active_agent_id", "r") as f:
            return f.read().strip() or "anima-fund"
    except FileNotFoundError:
        return "anima-fund"


def _get_sandbox_id():
    prov = _load_prov_status()
    return prov.get("sandbox", {}).get("id") or None


def _get_wallet_address() -> str:
    prov = _load_prov_status()
    return prov.get("wallet_address", "")


# ═══════════════════════════════════════════════════════════
# UNIFIED REFRESH — one cycle, all external sources, parallel
# ═══════════════════════════════════════════════════════════

async def _check_onchain_balance(wallet_address: str) -> dict:
    """Check USDC + ETH balance on Base chain via RPC."""
    if not wallet_address or not wallet_address.startswith("0x"):
        return {"usdc": 0.0, "eth": 0.0, "error": None}
    try:
        addr_padded = "0x70a08231" + wallet_address[2:].lower().zfill(64)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            # Parallel: USDC balance + ETH balance
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
    """Fetch Conway API credits balance for the active agent's key."""
    api_key = _get_conway_api_key()
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


async def _unified_refresh_loop():
    """Single background task: refreshes ALL external data in parallel every 10s.
    Wallet balance + Conway credits fetched together, cache updated atomically."""
    while True:
        try:
            wallet_addr = _get_wallet_address()
            _cache["sandbox_id"] = _get_sandbox_id()
            if wallet_addr:
                _cache["wallet_address"] = wallet_addr

            # Fetch all external data in parallel
            wallet_result, credits_result = await asyncio.gather(
                _check_onchain_balance(wallet_addr) if wallet_addr else _noop_wallet(),
                _fetch_conway_credits(),
                return_exceptions=True,
            )

            changed = False

            # Update wallet balance
            if isinstance(wallet_result, dict):
                if (_cache["wallet_usdc"] != wallet_result["usdc"]
                        or _cache["wallet_eth"] != wallet_result["eth"]):
                    changed = True
                _cache["wallet_usdc"] = wallet_result["usdc"]
                _cache["wallet_eth"] = wallet_result["eth"]
                _cache["wallet_error"] = wallet_result.get("error")
                _cache["wallet_last_check"] = datetime.now(timezone.utc).isoformat()

            # Update Conway credits
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


async def _noop_wallet():
    return {"usdc": 0.0, "eth": 0.0, "error": None}


# ═══════════════════════════════════════════════════════════
# SANDBOX POLL — fallback for agent data when webhooks are stale
# ═══════════════════════════════════════════════════════════

async def _sandbox_exec(sandbox_id, command):
    api_key = _get_conway_api_key()
    if not api_key:
        return ""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.post(f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/exec",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"command": command}) as r:
                if r.status == 200:
                    return (await r.json()).get("stdout", "")
        return ""
    except Exception:
        return ""


async def _sandbox_poll_loop():
    """Fallback: polls sandbox agent files every 20s if webhooks are stale."""
    while True:
        try:
            sandbox_id = _get_sandbox_id()
            _cache["sandbox_id"] = sandbox_id
            if not sandbox_id:
                _cache["poll_error"] = "no_sandbox"
                await asyncio.sleep(20)
                continue

            # Skip if webhook data is fresh (< 20s old)
            if _cache["last_update"] and _cache["update_source"] == "webhook":
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(_cache["last_update"])).total_seconds()
                    if age < 20:
                        await asyncio.sleep(20)
                        continue
                except Exception:
                    pass

            raw = await _sandbox_exec(sandbox_id, (
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
