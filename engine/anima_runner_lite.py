#!/usr/bin/env python3
"""
Lightweight Anima Runner — Runs in sandboxed environments with minimal dependencies.
Uses Anthropic API directly (not full Anima Machina framework) to save memory.
Reports state to platform via webhook.
"""
import os, sys, json, time, signal, logging, subprocess
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("anima")

# Load config
_env = "/app/anima/env.sh"
if os.path.exists(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                k, _, v = line[7:].partition("=")
                os.environ[k] = v.strip('"').strip("'")

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")
AGENT_ID = os.environ.get("AGENT_ID", "")
LLM_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
GENESIS_PATH = os.environ.get("GENESIS_PROMPT_PATH", "/app/anima/genesis-prompt.md")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "0"))
STATE_DIR = "/app/anima/state"

_running = True
signal.signal(signal.SIGTERM, lambda *_: globals().update(_running=False))
signal.signal(signal.SIGINT, lambda *_: globals().update(_running=False))

def webhook(data):
    if not WEBHOOK_URL: return
    import httpx
    data.update(agent_id=AGENT_ID, timestamp=datetime.now(timezone.utc).isoformat())
    headers = {"Content-Type": "application/json"}
    if WEBHOOK_TOKEN: headers["Authorization"] = f"Bearer {WEBHOOK_TOKEN}"
    try: httpx.post(WEBHOOK_URL, json=data, headers=headers, timeout=10)
    except: pass

def llm_call(messages):
    import anthropic
    client = anthropic.Anthropic(api_key=LLM_KEY)
    r = client.messages.create(model=LLM_MODEL, max_tokens=1024, messages=messages)
    return r.content[0].text

def shell(cmd):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=30)
        return r.stdout[:500] + (r.stderr[:200] if r.returncode != 0 else "")
    except: return "(timeout)"

def main():
    if not LLM_KEY:
        log.error("No LLM_API_KEY"); sys.exit(1)
    
    genesis = open(GENESIS_PATH).read() if os.path.exists(GENESIS_PATH) else "You are an autonomous agent."
    log.info(f"Agent {AGENT_ID} starting, model={LLM_MODEL}, genesis={len(genesis)} chars")
    
    webhook({"type": "state", "status": "running", "message": "Agent started", "engine_running": True})
    
    history = [{"role": "user", "content": f"You are now live. Your mission:\n{genesis[:3000]}\n\nYou have access to a shell. When you want to run a command, write SHELL: <command>. Begin."}]
    
    turn = 0
    while _running and (MAX_TURNS == 0 or turn < MAX_TURNS):
        turn += 1
        log.info(f"--- Turn {turn} ---")
        try:
            response = llm_call(history)
            log.info(f"Agent: {response[:200]}")
            history.append({"role": "assistant", "content": response})
            
            # Execute shell commands if requested
            if "SHELL:" in response:
                for line in response.split("\n"):
                    if line.strip().startswith("SHELL:"):
                        cmd = line.strip()[6:].strip()
                        result = shell(cmd)
                        log.info(f"Shell [{cmd[:50]}]: {result[:100]}")
                        history.append({"role": "user", "content": f"Shell result for `{cmd}`:\n{result}"})
                        webhook({"type": "action", "action": f"Ran: {cmd[:80]}", "tool_name": "shell", "result": result[:200]})
            else:
                history.append({"role": "user", "content": "Continue. What's your next action? Use SHELL: to run commands."})
            
            webhook({"type": "state", "status": "running", "message": response[:100], "engine_running": True})
            time.sleep(2)
        except Exception as e:
            log.error(f"Turn {turn}: {e}")
            webhook({"type": "error", "error": str(e)[:200], "severity": "error"})
            if "credit" in str(e).lower() or "balance" in str(e).lower():
                webhook({"type": "state", "status": "sleeping", "message": "Credits exhausted", "engine_running": False})
                time.sleep(300)
            else:
                time.sleep(10)
    
    webhook({"type": "state", "status": "stopped", "message": f"Completed {turn} turns", "engine_running": False})
    log.info(f"Stopped after {turn} turns")

if __name__ == "__main__":
    main()
