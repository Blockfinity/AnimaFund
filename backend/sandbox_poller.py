"""
Sandbox Poller — background task that reads agent data from the Conway sandbox.
Caches economics, revenue, decisions, phase state, and agent logs.
All live dashboard endpoints read from this cache.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone

import aiohttp

logger = logging.getLogger("sandbox_poller")

CONWAY_API = "https://api.conway.tech"
CONWAY_API_KEY = os.environ.get("CONWAY_API_KEY", "")

# Cached data — read by live endpoints
_cache = {
    "economics": {},
    "revenue_log": [],
    "decisions_log": [],
    "creator_split_log": [],
    "phase_state": {},
    "agent_stdout": "",
    "agent_stderr": "",
    "engine_running": False,
    "sandbox_id": None,
    "last_poll": None,
    "poll_error": None,
}

_poll_task = None


def get_cache():
    return _cache


def _get_sandbox_id():
    """Read sandbox ID from provisioning status."""
    try:
        with open("/app/backend/provisioning-status.json") as f:
            status = json.load(f)
        sid = status.get("sandbox", {}).get("id")
        return sid if sid else None
    except Exception:
        return None


async def _conway_get(path: str) -> dict:
    if not CONWAY_API_KEY:
        return {"error": "no key"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get(
                f"{CONWAY_API}{path}",
                headers={"Authorization": f"Bearer {CONWAY_API_KEY}"},
            ) as resp:
                return await resp.json()
    except Exception as e:
        return {"error": str(e)}


async def _sandbox_exec(sandbox_id: str, command: str) -> str:
    """Execute command in sandbox and return stdout."""
    if not CONWAY_API_KEY:
        return ""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(
                f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/exec",
                headers={"Authorization": f"Bearer {CONWAY_API_KEY}", "Content-Type": "application/json"},
                json={"command": command},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("stdout", data.get("output", ""))
                return ""
    except Exception:
        return ""


async def _read_json_file(sandbox_id: str, path: str) -> any:
    """Read a JSON file from the sandbox, return parsed data or empty fallback."""
    raw = await _sandbox_exec(sandbox_id, f"cat {path} 2>/dev/null || echo 'null'")
    raw = raw.strip()
    if not raw or raw == "null":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def _poll_once():
    """Single poll cycle — read all agent data from sandbox."""
    sandbox_id = _get_sandbox_id()
    if not sandbox_id:
        _cache["sandbox_id"] = None
        _cache["poll_error"] = "no_sandbox"
        return

    _cache["sandbox_id"] = sandbox_id

    try:
        # Read all files in one batch exec to minimize API calls
        batch_cmd = (
            "echo '===ECONOMICS===' && cat ~/.anima/economics.json 2>/dev/null || echo 'null' && "
            "echo '===REVENUE===' && cat ~/.anima/revenue-log.json 2>/dev/null || echo '[]' && "
            "echo '===DECISIONS===' && cat ~/.anima/decisions-log.json 2>/dev/null || echo '[]' && "
            "echo '===CREATOR_SPLIT===' && cat ~/.anima/creator-split-log.json 2>/dev/null || echo '[]' && "
            "echo '===PHASE===' && cat ~/.anima/phase-state.json 2>/dev/null || echo '{}' && "
            "echo '===ENGINE===' && pgrep -f 'bundle.mjs' > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED' && "
            "echo '===STDOUT===' && tail -80 /var/log/automaton.out.log 2>/dev/null || echo '' && "
            "echo '===STDERR===' && tail -40 /var/log/automaton.err.log 2>/dev/null || echo ''"
        )

        raw = await _sandbox_exec(sandbox_id, batch_cmd)
        if not raw:
            _cache["poll_error"] = "exec_empty"
            _cache["last_poll"] = datetime.now(timezone.utc).isoformat()
            return

        # Parse sections
        sections = {}
        current_key = None
        current_lines = []

        for line in raw.split("\n"):
            if line.startswith("===") and line.endswith("==="):
                if current_key:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = line.strip("=")
                current_lines = []
            else:
                current_lines.append(line)
        if current_key:
            sections[current_key] = "\n".join(current_lines).strip()

        # Parse each section
        def _parse_json(raw_str, fallback):
            if not raw_str or raw_str == "null":
                return fallback
            try:
                return json.loads(raw_str)
            except (json.JSONDecodeError, TypeError):
                return fallback

        _cache["economics"] = _parse_json(sections.get("ECONOMICS"), {})
        _cache["revenue_log"] = _parse_json(sections.get("REVENUE"), [])
        _cache["decisions_log"] = _parse_json(sections.get("DECISIONS"), [])
        _cache["creator_split_log"] = _parse_json(sections.get("CREATOR_SPLIT"), [])
        _cache["phase_state"] = _parse_json(sections.get("PHASE"), {})
        _cache["engine_running"] = sections.get("ENGINE", "").strip() == "RUNNING"
        _cache["agent_stdout"] = sections.get("STDOUT", "")
        _cache["agent_stderr"] = sections.get("STDERR", "")
        _cache["poll_error"] = None
        _cache["last_poll"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        _cache["poll_error"] = str(e)
        _cache["last_poll"] = datetime.now(timezone.utc).isoformat()


async def _poll_loop():
    """Background polling loop — runs every 10 seconds."""
    while True:
        try:
            await _poll_once()
        except Exception as e:
            logger.error(f"Sandbox poller error: {e}")
        await asyncio.sleep(5)


def start_poller():
    """Start the background polling task. Call this on app startup."""
    global _poll_task
    if _poll_task is None:
        _poll_task = asyncio.create_task(_poll_loop())
        logger.info("Sandbox poller started")


def stop_poller():
    """Stop the background polling task."""
    global _poll_task
    if _poll_task:
        _poll_task.cancel()
        _poll_task = None
