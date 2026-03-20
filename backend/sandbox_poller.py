"""
Sandbox poller stub — replaces the old 321-line broken poller.
Provides the same interface so existing routers don't crash.
Data comes from webhook updates (push model) not polling (pull model).
"""
import asyncio
from datetime import datetime, timezone

_cache = {}
_event = asyncio.Event()


def get_cache() -> dict:
    """Return cached webhook data from agent reports."""
    return _cache


def get_update_event() -> asyncio.Event:
    """Event that fires when new webhook data arrives."""
    return _event


def update_from_webhook(data: dict):
    """Called by webhook router when agent pushes a state update."""
    global _cache
    _cache.update(data)
    _cache["last_webhook_update"] = datetime.now(timezone.utc).isoformat()
    _event.set()
    _event.clear()


def start_poller():
    """No-op. Polling is replaced by webhook push model."""
    pass


def stop_poller():
    """No-op."""
    pass
