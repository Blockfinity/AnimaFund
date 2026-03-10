"""
Sandbox Poller — receives webhook pushes from the sandbox daemon.
Uses asyncio.Event for instant SSE notification on webhook arrival.
Falls back to polling if webhooks aren't coming through.
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
    "last_update": None,
    "update_source": None,
    "poll_error": None,
}

# SSE listeners wait on this — set() the instant a webhook arrives
_update_event = asyncio.Event()
_poll_task = None


def get_cache():
    return _cache


def get_update_event():
    return _update_event


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
    # Wake up all SSE listeners immediately
    _update_event.set()
    _update_event.clear()


def _get_sandbox_id():
    try:
        with open("/app/backend/provisioning-status.json") as f:
            return json.load(f).get("sandbox", {}).get("id") or None
    except Exception:
        return None


async def _sandbox_exec(sandbox_id, command):
    if not CONWAY_API_KEY:
        return ""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.post(f"{CONWAY_API}/v1/sandboxes/{sandbox_id}/exec",
                headers={"Authorization": f"Bearer {CONWAY_API_KEY}", "Content-Type": "application/json"},
                json={"command": command}) as r:
                if r.status == 200:
                    return (await r.json()).get("stdout", "")
        return ""
    except Exception:
        return ""


async def _poll_once():
    sandbox_id = _get_sandbox_id()
    _cache["sandbox_id"] = sandbox_id
    if not sandbox_id:
        _cache["poll_error"] = "no_sandbox"
        return
    if _cache["last_update"] and _cache["update_source"] == "webhook":
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(_cache["last_update"])).total_seconds() < 20:
                return
        except Exception:
            pass
    try:
        raw = await _sandbox_exec(sandbox_id, (
            "echo '===ECONOMICS===' && cat ~/.anima/economics.json 2>/dev/null || echo 'null' && "
            "echo '===REVENUE===' && cat ~/.anima/revenue-log.json 2>/dev/null || echo '[]' && "
            "echo '===DECISIONS===' && cat ~/.anima/decisions-log.json 2>/dev/null || echo '[]' && "
            "echo '===PHASE===' && cat ~/.anima/phase-state.json 2>/dev/null || echo '{}' && "
            "echo '===ENGINE===' && pgrep -f 'bundle.mjs' > /dev/null 2>&1 && echo 'RUNNING' || echo 'STOPPED' && "
            "echo '===STDOUT===' && tail -80 /var/log/automaton.out.log 2>/dev/null || echo ''"
        ))
        if not raw:
            return
        sections = {}
        key, lines = None, []
        for line in raw.split("\n"):
            if line.startswith("===") and line.endswith("==="):
                if key: sections[key] = "\n".join(lines).strip()
                key, lines = line.strip("="), []
            else: lines.append(line)
        if key: sections[key] = "\n".join(lines).strip()
        def p(s, d):
            if not s or s == "null": return d
            try: return json.loads(s)
            except: return d
        _cache["economics"] = p(sections.get("ECONOMICS"), _cache["economics"])
        _cache["revenue_log"] = p(sections.get("REVENUE"), _cache["revenue_log"])
        _cache["decisions_log"] = p(sections.get("DECISIONS"), _cache["decisions_log"])
        _cache["phase_state"] = p(sections.get("PHASE"), _cache["phase_state"])
        _cache["engine_running"] = sections.get("ENGINE", "").strip() == "RUNNING"
        _cache["agent_stdout"] = sections.get("STDOUT", "")
        _cache["poll_error"] = None
        _cache["last_update"] = datetime.now(timezone.utc).isoformat()
        _cache["update_source"] = "poll"
        _update_event.set()
        _update_event.clear()
    except Exception as e:
        _cache["poll_error"] = str(e)


async def _poll_loop():
    while True:
        try: await _poll_once()
        except Exception as e: logger.error(f"Poller: {e}")
        await asyncio.sleep(20)


def start_poller():
    global _poll_task
    if not _poll_task:
        _poll_task = asyncio.create_task(_poll_loop())


def stop_poller():
    global _poll_task
    if _poll_task:
        _poll_task.cancel()
        _poll_task = None
