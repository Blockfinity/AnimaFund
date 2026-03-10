"""
Sandbox Poller — receives webhook pushes from the sandbox daemon.
Falls back to polling if webhooks aren't coming through.
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

# Cached data — written by webhook, read by live endpoints
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

_poll_task = None


def get_cache():
    return _cache


def update_from_webhook(data: dict):
    """Called by the webhook endpoint — instant update from sandbox."""
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


def _get_sandbox_id():
    try:
        with open("/app/backend/provisioning-status.json") as f:
            status = json.load(f)
        sid = status.get("sandbox", {}).get("id")
        return sid if sid else None
    except Exception:
        return None


async def _sandbox_exec(sandbox_id: str, command: str) -> str:
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


async def _poll_once():
    """Fallback poll — only runs if webhooks haven't updated recently."""
    sandbox_id = _get_sandbox_id()
    _cache["sandbox_id"] = sandbox_id
    if not sandbox_id:
        _cache["poll_error"] = "no_sandbox"
        return

    # Skip polling if webhook updated within last 10s
    if _cache["last_update"] and _cache["update_source"] == "webhook":
        try:
            last = datetime.fromisoformat(_cache["last_update"])
            if (datetime.now(timezone.utc) - last).total_seconds() < 10:
                return
        except Exception:
            pass

    try:
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
            return

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

        def _parse(raw_str, fallback):
            if not raw_str or raw_str == "null":
                return fallback
            try:
                return json.loads(raw_str)
            except (json.JSONDecodeError, TypeError):
                return fallback

        _cache["economics"] = _parse(sections.get("ECONOMICS"), _cache["economics"])
        _cache["revenue_log"] = _parse(sections.get("REVENUE"), _cache["revenue_log"])
        _cache["decisions_log"] = _parse(sections.get("DECISIONS"), _cache["decisions_log"])
        _cache["creator_split_log"] = _parse(sections.get("CREATOR_SPLIT"), _cache["creator_split_log"])
        _cache["phase_state"] = _parse(sections.get("PHASE"), _cache["phase_state"])
        _cache["engine_running"] = sections.get("ENGINE", "").strip() == "RUNNING"
        _cache["agent_stdout"] = sections.get("STDOUT", "")
        _cache["agent_stderr"] = sections.get("STDERR", "")
        _cache["poll_error"] = None
        _cache["last_update"] = datetime.now(timezone.utc).isoformat()
        _cache["update_source"] = "poll"
    except Exception as e:
        _cache["poll_error"] = str(e)


async def _poll_loop():
    """Fallback polling — every 15s, only if webhooks are stale."""
    while True:
        try:
            await _poll_once()
        except Exception as e:
            logger.error(f"Poller error: {e}")
        await asyncio.sleep(15)


def start_poller():
    global _poll_task
    if _poll_task is None:
        _poll_task = asyncio.create_task(_poll_loop())
        logger.info("Sandbox poller started (webhook primary, poll fallback)")


def stop_poller():
    global _poll_task
    if _poll_task:
        _poll_task.cancel()
        _poll_task = None
