#!/usr/bin/env python3
"""
Anima Runner — Runs inside a sandboxed environment.
Reads genesis prompt, creates an Anima Machina agent, operates autonomously.
Reports state to the platform via webhook.
"""
import os
import sys
import json
import time
import signal
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("anima-runner")

# Config from environment
PLATFORM_URL = os.environ.get("PLATFORM_URL", "")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")
AGENT_ID = os.environ.get("AGENT_ID", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
GENESIS_PROMPT_PATH = os.environ.get("GENESIS_PROMPT_PATH", "/app/anima/genesis-prompt.md")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "20"))

_running = True
def _shutdown(sig, frame):
    global _running
    logger.info(f"Received signal {sig}, shutting down...")
    _running = False
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# ─── State Reporting (standalone, no toolkit base class dependency) ───

def _push_state(data: dict):
    """Push data to the platform webhook."""
    if not PLATFORM_URL:
        return
    import httpx
    data["agent_id"] = AGENT_ID
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    headers = {"Content-Type": "application/json"}
    if WEBHOOK_TOKEN:
        headers["Authorization"] = f"Bearer {WEBHOOK_TOKEN}"
    try:
        httpx.post(f"{PLATFORM_URL}/api/webhook/agent-update", json=data, headers=headers, timeout=10)
    except Exception as e:
        logger.warning(f"State push failed: {e}")

def report_state(status: str, message: str = "", goal_progress: float = 0.0) -> str:
    """Report current agent state to the platform."""
    _push_state({"type": "state", "status": status, "message": message, "goal_progress": goal_progress, "engine_running": status not in ("stopped", "error")})
    return json.dumps({"reported": True, "status": status})

def report_action(action: str, tool_name: str = "", result: str = "") -> str:
    """Report an action the agent took."""
    _push_state({"type": "action", "action": action, "tool_name": tool_name, "result": result[:500]})
    return json.dumps({"reported": True, "action": action})

def report_error(error: str, severity: str = "warning") -> str:
    """Report an error."""
    _push_state({"type": "error", "error": error, "severity": severity})
    return json.dumps({"reported": True})

def report_financial(wallet_address: str = "", usdc_balance: float = 0.0, revenue: float = 0.0, expenses: float = 0.0) -> str:
    """Report financial state."""
    _push_state({"type": "financial", "wallet_address": wallet_address, "usdc_balance": usdc_balance, "revenue": revenue, "expenses": expenses})
    return json.dumps({"reported": True})

def get_wallet_info() -> str:
    """Get wallet status."""
    return json.dumps({"wallet_address": "Not yet created", "network": "Base"})

def create_wallet() -> str:
    """Create a new Ethereum wallet."""
    try:
        from eth_account import Account
        account = Account.create()
        return json.dumps({"success": True, "wallet_address": account.address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def check_balance(address: str) -> str:
    """Check USDC balance on Base."""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        contract = w3.eth.contract(address=Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call() / 1e6
        return json.dumps({"success": True, "usdc_balance": balance, "address": address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def load_genesis_prompt():
    if os.path.exists(GENESIS_PROMPT_PATH):
        with open(GENESIS_PROMPT_PATH) as f:
            return f.read()
    return "You are an autonomous agent. Explore your environment and report what you find."


def create_agent():
    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from camel.toolkits import FunctionTool

    model_kwargs = {"model_platform": ModelPlatformType.OPENAI, "model_type": LLM_MODEL, "api_key": LLM_API_KEY}
    if LLM_BASE_URL:
        model_kwargs["url"] = LLM_BASE_URL
    model = ModelFactory.create(**model_kwargs)

    tools = [
        FunctionTool(report_state),
        FunctionTool(report_action),
        FunctionTool(report_error),
        FunctionTool(report_financial),
        FunctionTool(create_wallet),
        FunctionTool(check_balance),
        FunctionTool(get_wallet_info),
    ]

    genesis_prompt = load_genesis_prompt()
    agent = ChatAgent(system_message=genesis_prompt, model=model, tools=tools)
    logger.info(f"Agent created with {len(tools)} tools")
    return agent


def run_agent(agent):
    report_state("running", "Agent started in sandbox, reading genesis prompt")
    logger.info("Agent started. Beginning autonomous operation.")

    turn_prompt = (
        "You have just been deployed into a sandboxed environment. "
        "Read your system prompt carefully. Begin executing your mission. "
        "Use report_state, report_action, and report_financial tools to report everything you do. "
        "Start by checking your wallet and reporting your financial state."
    )

    turn = 0
    while _running and turn < MAX_TURNS:
        turn += 1
        logger.info(f"--- Turn {turn}/{MAX_TURNS} ---")
        try:
            response = agent.step(turn_prompt)
            content = response.msgs[0].content if response.msgs else ""
            tool_calls = response.info.get("tool_calls", []) if response.info else []

            logger.info(f"Agent ({len(tool_calls)} tools): {content[:200]}")
            for tc in tool_calls:
                logger.info(f"  Tool: {tc.tool_name} -> {str(tc.result)[:100]}")

            turn_prompt = "Continue your mission. What should you do next? Report every action."
            time.sleep(5)
        except Exception as e:
            logger.error(f"Turn {turn} error: {e}")
            report_error(str(e))
            time.sleep(10)

    report_state("stopped", f"Agent completed {turn} turns")
    logger.info(f"Agent stopped after {turn} turns")


def main():
    if not LLM_API_KEY:
        logger.error("LLM_API_KEY not set")
        sys.exit(1)
    logger.info(f"Anima Runner: agent={AGENT_ID}, model={LLM_MODEL}, platform={PLATFORM_URL or 'NOT SET'}")
    agent = create_agent()
    run_agent(agent)


if __name__ == "__main__":
    main()
