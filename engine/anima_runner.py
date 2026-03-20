#!/usr/bin/env python3
"""
Anima Runner — Runs inside a sandboxed environment.
Creates an Anima Machina agent with real tools, maintains conversation history,
operates autonomously, reports state to the platform.
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

# Config
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
    _running = False
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# ─── State Reporting (standalone functions, called as tools by the agent) ───

def _push_webhook(data: dict):
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
        logger.warning(f"Webhook push failed: {e}")


def report_state(status: str, message: str = "", goal_progress: float = 0.0) -> str:
    """Report current agent state to the platform dashboard."""
    _push_webhook({"type": "state", "status": status, "message": message,
                    "goal_progress": goal_progress, "engine_running": status not in ("stopped", "error")})
    return json.dumps({"reported": True, "status": status})


def report_action(action: str, tool_name: str = "", result: str = "") -> str:
    """Report a significant action to the platform dashboard."""
    _push_webhook({"type": "action", "action": action, "tool_name": tool_name, "result": result[:500]})
    return json.dumps({"reported": True, "action": action})


def report_error(error: str, severity: str = "warning") -> str:
    """Report an error to the platform dashboard."""
    _push_webhook({"type": "error", "error": error, "severity": severity})
    return json.dumps({"reported": True})


def report_financial(wallet_address: str = "", usdc_balance: float = 0.0,
                     revenue: float = 0.0, expenses: float = 0.0) -> str:
    """Report financial state to the platform dashboard."""
    _push_webhook({"type": "financial", "wallet_address": wallet_address,
                    "usdc_balance": usdc_balance, "revenue": revenue, "expenses": expenses})
    return json.dumps({"reported": True})


def create_wallet() -> str:
    """Create a new Ethereum wallet on Base network."""
    try:
        from eth_account import Account
        account = Account.create()
        return json.dumps({"success": True, "wallet_address": account.address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def check_balance(address: str) -> str:
    """Check USDC balance for a wallet address on Base network."""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        contract = w3.eth.contract(
            address=Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call() / 1e6
        return json.dumps({"success": True, "usdc_balance": balance, "address": address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def main():
    if not LLM_API_KEY:
        logger.error("LLM_API_KEY not set. Cannot start agent.")
        sys.exit(1)

    logger.info(f"Anima Runner starting: agent={AGENT_ID}, model={LLM_MODEL}")

    # Load genesis prompt
    genesis_prompt = ""
    if os.path.exists(GENESIS_PROMPT_PATH):
        with open(GENESIS_PROMPT_PATH) as f:
            genesis_prompt = f.read()
        logger.info(f"Genesis prompt loaded: {len(genesis_prompt)} chars")
    else:
        genesis_prompt = "You are an autonomous agent. Explore your environment and report what you find."
        logger.warning(f"No genesis prompt at {GENESIS_PROMPT_PATH}, using default")

    # Import CAMEL
    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from camel.toolkits import FunctionTool, CodeExecutionToolkit, FileToolkit

    # Try to import optional toolkits
    extra_tools = []
    try:
        from camel.toolkits import TerminalToolkit
        terminal_tk = TerminalToolkit()
        extra_tools.extend(terminal_tk.get_tools())
        logger.info(f"TerminalToolkit loaded: {len(terminal_tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"TerminalToolkit unavailable: {e}")

    try:
        code_tk = CodeExecutionToolkit()
        extra_tools.extend(code_tk.get_tools())
        logger.info(f"CodeExecutionToolkit loaded: {len(code_tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"CodeExecutionToolkit unavailable: {e}")

    try:
        file_tk = FileToolkit()
        extra_tools.extend(file_tk.get_tools())
        logger.info(f"FileToolkit loaded: {len(file_tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"FileToolkit unavailable: {e}")

    # Create model
    model_kwargs = {
        "model_platform": ModelPlatformType.OPENAI,
        "model_type": LLM_MODEL,
        "api_key": LLM_API_KEY,
    }
    if LLM_BASE_URL:
        model_kwargs["url"] = LLM_BASE_URL
    model = ModelFactory.create(**model_kwargs)

    # State reporting tools
    state_tools = [
        FunctionTool(report_state),
        FunctionTool(report_action),
        FunctionTool(report_error),
        FunctionTool(report_financial),
        FunctionTool(create_wallet),
        FunctionTool(check_balance),
    ]

    all_tools = state_tools + extra_tools
    logger.info(f"Agent created with {len(all_tools)} tools total")

    # Create the agent ONCE — it maintains conversation history across all turns
    agent = ChatAgent(
        system_message=genesis_prompt,
        model=model,
        tools=all_tools,
    )

    # Report startup
    report_state("running", "Agent deployed and starting autonomous operation")

    # Turn 1: Initial instruction (sent ONCE)
    turn = 0
    initial_msg = (
        "You have been deployed into a sandboxed Linux environment. "
        "You have tools for: shell commands (shell_exec), code execution, "
        "file operations, wallet management, and state reporting. "
        "Read your system prompt (genesis prompt) carefully. "
        "Report your state, then begin executing your mission. "
        "Start by exploring your environment (run 'uname -a', 'df -h', 'whoami') "
        "and checking your wallet."
    )

    while _running and turn < MAX_TURNS:
        turn += 1
        logger.info(f"--- Turn {turn}/{MAX_TURNS} ---")

        try:
            if turn == 1:
                response = agent.step(initial_msg)
            else:
                # After turn 1, the agent continues from its own context.
                # Give it a brief nudge, not a repeat of the initial prompt.
                response = agent.step("Continue. What's your next action?")

            content = response.msgs[0].content if response.msgs else ""
            tool_calls = response.info.get("tool_calls", []) if response.info else []

            logger.info(f"Response ({len(tool_calls)} tools): {content[:300]}")
            for tc in tool_calls:
                logger.info(f"  Tool: {tc.tool_name} -> {str(tc.result)[:150]}")

            # Wait between turns (agent paces itself)
            time.sleep(3)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Turn {turn} error: {e}")
            report_error(str(e), "error")
            time.sleep(10)

    report_state("stopped", f"Agent completed {turn} turns")
    logger.info(f"Agent stopped after {turn} turns")


if __name__ == "__main__":
    main()
