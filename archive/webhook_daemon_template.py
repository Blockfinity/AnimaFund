#!/usr/bin/env python3
"""Webhook daemon — runs inside sandbox, pushes agent data to the platform."""
import json, time, os, subprocess, urllib.request, hashlib

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
ANIMA_DIR = os.path.expanduser("~/.anima")
os.makedirs(ANIMA_DIR, exist_ok=True)

FILES = {
    "economics": ANIMA_DIR + "/economics.json",
    "revenue_log": ANIMA_DIR + "/revenue-log.json",
    "decisions_log": ANIMA_DIR + "/decisions-log.json",
    "phase_state": ANIMA_DIR + "/phase-state.json",
}
LOG_FILES = {
    "agent_stdout": "/var/log/automaton.out.log",
    "agent_stderr": "/var/log/automaton.err.log",
}
prev_hash = ""

def read_json(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None

def read_tail(p, n=80):
    try:
        with open(p) as f:
            lines = f.readlines()
            return "\n".join(lines[-n:])
    except Exception:
        return ""

def check_engine():
    try:
        return subprocess.run(["pgrep", "-f", "bundle.mjs"], capture_output=True, timeout=3).returncode == 0
    except Exception:
        return False

def send_webhook(payload):
    if not WEBHOOK_URL:
        return
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass

while True:
    try:
        h = ""
        for p in list(FILES.values()) + list(LOG_FILES.values()):
            try:
                with open(p, "rb") as f:
                    h += hashlib.md5(f.read()[-4096:]).hexdigest()
            except Exception:
                pass
        if h != prev_hash:
            payload = {"source": "sandbox"}
            for k, p in FILES.items():
                payload[k] = read_json(p)
            for k, p in LOG_FILES.items():
                payload[k] = read_tail(p)
            payload["engine_running"] = check_engine()
            send_webhook(payload)
            prev_hash = h
    except Exception:
        pass
    time.sleep(3)
