#!/usr/bin/env python3
"""
Agent Process — Runs as a SEPARATE PROCESS spawned by the Executor.
Each agent gets its own process, working directory, and environment.
Reads genesis prompt and config from its agent directory.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("agent")

agent_dir = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("AGENT_DIR", "/tmp/anima-agents/unknown")

# Load config
config = {}
config_path = os.path.join(agent_dir, "config.json")
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)

AGENT_ID = config.get("agent_id", "unknown")
WEBHOOK_URL = config.get("webhook_url", "")
WEBHOOK_TOKEN = config.get("webhook_token", "")
MAX_TURNS = config.get("max_turns", 5)

# Load genesis prompt
genesis_path = os.path.join(agent_dir, "genesis.md")
genesis = open(genesis_path).read() if os.path.exists(genesis_path) else "You are an autonomous agent."

log.info(f"Agent {AGENT_ID} starting (PID {os.getpid()}), genesis={len(genesis)} chars, max_turns={MAX_TURNS}")


def webhook(data):
    if not WEBHOOK_URL:
        return
    import httpx
    data.update(agent_id=AGENT_ID, timestamp=datetime.now(timezone.utc).isoformat())
    headers = {"Content-Type": "application/json"}
    if WEBHOOK_TOKEN:
        headers["Authorization"] = f"Bearer {WEBHOOK_TOKEN}"
    try:
        httpx.post(WEBHOOK_URL, json=data, headers=headers, timeout=10)
    except Exception as e:
        log.warning(f"Webhook failed: {e}")


def main():
    # Import Anima Machina
    from anima_machina.agents import ChatAgent
    from anima_machina.models import ModelFactory
    from anima_machina.types import ModelPlatformType
    from anima_machina.toolkits import TerminalToolkit, CodeExecutionToolkit, SearchToolkit, FunctionTool

    # Create model — use whatever is configured
    if os.environ.get("ANTHROPIC_API_KEY"):
        model = ModelFactory.create(
            model_platform=ModelPlatformType.ANTHROPIC,
            model_type="claude-sonnet-4-20250514",
            model_config_dict={"max_tokens": 1024},
        )
    else:
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            url=os.environ.get("OPENAI_API_BASE_URL", ""),
        )

    # Tools
    def report_state(status: str, message: str = "") -> str:
        webhook({"type": "state", "status": status, "message": message, "engine_running": status not in ("stopped", "error")})
        return json.dumps({"reported": True})

    def report_action(action: str, tool_name: str = "") -> str:
        webhook({"type": "action", "action": action, "tool_name": tool_name})
        return json.dumps({"reported": True})

    tools = (
        TerminalToolkit().get_tools() +
        CodeExecutionToolkit().get_tools() +
        SearchToolkit().get_tools() +
        [FunctionTool(report_state), FunctionTool(report_action)]
    )

    agent = ChatAgent(system_message=genesis, model=model, tools=tools)
    log.info(f"Agent created with {len(tools)} tools")

    webhook({"type": "state", "status": "running", "message": "Agent deployed and starting", "engine_running": True})

    for turn in range(1, MAX_TURNS + 1):
        log.info(f"Turn {turn}/{MAX_TURNS}")
        try:
            if turn == 1:
                r = agent.step("You are now live. Begin executing your mission. Use your tools.")
            else:
                r = agent.step("Continue your mission. Take your next action.")

            content = r.msgs[0].content if r.msgs else ""
            tc = r.info.get("tool_calls", []) if r.info else []
            log.info(f"Turn {turn}: {len(tc)} tools, {content[:100]}")

            webhook({"type": "state", "status": "running", "message": content[:100], "engine_running": True})
            time.sleep(2)

        except Exception as e:
            log.error(f"Turn {turn} error: {e}")
            webhook({"type": "error", "error": str(e)[:200], "severity": "error"})
            time.sleep(5)

    webhook({"type": "state", "status": "completed", "message": f"Completed {MAX_TURNS} turns", "engine_running": False})
    log.info(f"Agent {AGENT_ID} completed {MAX_TURNS} turns")


if __name__ == "__main__":
    main()
