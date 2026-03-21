#!/usr/bin/env python3
"""
Anima Runner — Runs inside a sandboxed environment.
The agent operates AUTONOMOUSLY — the runner starts it and gets out of the way.
CAMEL ChatAgent maintains conversation history across turns.
Agent decides what to do, when to act, and when to stop.
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

# Load config from env.sh file directly (more reliable than depending on shell sourcing)
_env_file = "/app/anima/env.sh"
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                kv = line[7:]  # strip "export "
                key, _, val = kv.partition("=")
                val = val.strip('"').strip("'")
                os.environ[key] = val

# Config from environment
# SECURITY: Sandbox only gets WEBHOOK_URL (not the full platform URL)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")
AGENT_ID = os.environ.get("AGENT_ID", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
GENESIS_PROMPT_PATH = os.environ.get("GENESIS_PROMPT_PATH", "/app/anima/genesis-prompt.md")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "0"))  # 0 = unlimited
STATE_DIR = "/app/anima/state"

_running = True
def _shutdown(sig, frame):
    global _running
    _running = False
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# ─── State Reporting (pushed to platform webhook) ───

def _push_webhook(data: dict):
    if not WEBHOOK_URL:
        return
    import httpx
    data["agent_id"] = AGENT_ID
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    headers = {"Content-Type": "application/json"}
    if WEBHOOK_TOKEN:
        headers["Authorization"] = f"Bearer {WEBHOOK_TOKEN}"
    try:
        httpx.post(WEBHOOK_URL, json=data, headers=headers, timeout=10)
    except Exception as e:
        logger.warning(f"Webhook push failed: {e}")


def report_state(status: str, message: str = "", goal_progress: float = 0.0) -> str:
    """Report current state to the platform dashboard. Call this when your status changes."""
    _push_webhook({"type": "state", "status": status, "message": message,
                    "goal_progress": goal_progress, "engine_running": status not in ("stopped", "error")})
    return json.dumps({"reported": True, "status": status})


def report_action(action: str, tool_name: str = "", result: str = "") -> str:
    """Report a significant action to the platform dashboard. Call this for every meaningful action."""
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


# ─── Persistent Memory (simple key-value, survives restarts) ───
# Note: CAMEL's MemoryToolkit (save/load full conversation) is used for agent memory.
# These functions provide simple key-value persistence for facts the agent wants to remember.

def save_memory(key: str, value: str) -> str:
    """Save a fact to persistent storage. Survives process restarts. Use for important data like wallet addresses, goals, learned facts."""
    os.makedirs(STATE_DIR, exist_ok=True)
    mem_file = os.path.join(STATE_DIR, "memory.json")
    memories = {}
    if os.path.exists(mem_file):
        with open(mem_file) as f:
            memories = json.load(f)
    memories[key] = {"value": value, "saved_at": datetime.now(timezone.utc).isoformat()}
    with open(mem_file, "w") as f:
        json.dump(memories, f, indent=2)
    return json.dumps({"saved": True, "key": key})


def recall_memory(key: str = "") -> str:
    """Recall facts from persistent storage. If key is empty, returns all saved facts."""
    mem_file = os.path.join(STATE_DIR, "memory.json")
    if not os.path.exists(mem_file):
        return json.dumps({"memories": {}})
    with open(mem_file) as f:
        memories = json.load(f)
    if key:
        return json.dumps({"key": key, "value": memories.get(key, {}).get("value", "NOT FOUND")})
    return json.dumps({"memories": {k: v["value"] for k, v in memories.items()}})


# ─── Browser (runs Playwright in subprocess to avoid greenlet thread conflict) ───

def browse_website(url: str, task: str = "Extract the main content and title of this page") -> str:
    """Browse a website using a real browser. Can extract content, read text, see page structure.
    Runs in a subprocess to avoid threading conflicts."""
    import subprocess
    script = f'''
import json, sys
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("{url}", timeout=15000)
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        title = page.title()
        content = page.inner_text("body")[:3000]
        browser.close()
        print(json.dumps({{"success": True, "title": title, "url": "{url}", "content": content[:2000]}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e), "url": "{url}"}}))
'''
    try:
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if output:
            return output
        return json.dumps({"success": False, "error": result.stderr[:500] if result.stderr else "No output"})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "Browser timed out after 30s"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})



# ─── Wallet (code-level enforcement: core wallet address NEVER exposed to the agent) ───
# The agent can CHECK balance and SEND payments without knowing the core address.
# Only the PUBLIC wallet address is shareable. The platform stores the core address for dashboard display.

_CORE_WALLET_ADDR = ""
_CORE_WALLET_KEY = ""

def _init_core_wallet():
    global _CORE_WALLET_ADDR, _CORE_WALLET_KEY
    if _CORE_WALLET_ADDR:
        return
    existing = "/root/.anima/wallet.json"
    if os.path.exists(existing):
        try:
            with open(existing) as f:
                w = json.load(f)
            pk = w.get("privateKey", "")
            if pk:
                from eth_account import Account
                acct = Account.from_key(pk)
                _CORE_WALLET_ADDR = acct.address
                _CORE_WALLET_KEY = pk
        except Exception:
            pass

def get_wallet_balance() -> str:
    """Check your wallet's USDC balance on Base. Returns balance without revealing the address."""
    _init_core_wallet()
    if not _CORE_WALLET_ADDR:
        return json.dumps({"success": False, "error": "No wallet configured"})
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        contract = w3.eth.contract(address=Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(_CORE_WALLET_ADDR)).call() / 1e6
        return json.dumps({"success": True, "usdc_balance": balance, "network": "Base"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def send_payment(to_address: str, amount_usdc: float) -> str:
    """Send USDC from your wallet to another address on Base. You don't need to know your wallet address — the payment is signed internally."""
    _init_core_wallet()
    if not _CORE_WALLET_KEY:
        return json.dumps({"success": False, "error": "No wallet configured for sending"})
    if amount_usdc <= 0:
        return json.dumps({"success": False, "error": "Amount must be positive"})
    try:
        from web3 import Web3
        from eth_account import Account
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        usdc_addr = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        to = Web3.to_checksum_address(to_address)
        amount_raw = int(amount_usdc * 1e6)
        abi = [
            {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
        ]
        contract = w3.eth.contract(address=usdc_addr, abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(_CORE_WALLET_ADDR)).call()
        if balance < amount_raw:
            return json.dumps({"success": False, "error": f"Insufficient balance: have {balance/1e6} USDC, need {amount_usdc}"})
        acct = Account.from_key(_CORE_WALLET_KEY)
        nonce = w3.eth.get_transaction_count(acct.address)
        tx = contract.functions.transfer(to, amount_raw).build_transaction({
            "from": acct.address, "nonce": nonce,
            "gas": 100000, "gasPrice": w3.eth.gas_price,
            "chainId": 8453,
        })
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return json.dumps({"success": True, "tx_hash": tx_hash.hex(), "amount": amount_usdc, "to": to_address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def sweep_public_wallet() -> str:
    """Move all funds from your public wallet to your main wallet. Call this after receiving payments."""
    _init_core_wallet()
    if not _CORE_WALLET_ADDR:
        return json.dumps({"success": False, "error": "No core wallet"})
    pub_path = os.path.join(STATE_DIR, "public_wallet.json")
    if not os.path.exists(pub_path):
        return json.dumps({"success": False, "error": "No public wallet exists"})
    try:
        with open(pub_path) as f:
            pw = json.load(f)
        pub_key = pw.get("privateKey", "")
        pub_addr = pw.get("address", "")
        if not pub_key or not pub_addr:
            return json.dumps({"success": False, "error": "Public wallet incomplete"})
        from web3 import Web3
        from eth_account import Account
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        usdc_addr = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        abi = [
            {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
        ]
        contract = w3.eth.contract(address=usdc_addr, abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(pub_addr)).call()
        if balance == 0:
            return json.dumps({"success": True, "message": "Public wallet is empty, nothing to sweep"})
        acct = Account.from_key(pub_key)
        nonce = w3.eth.get_transaction_count(acct.address)
        tx = contract.functions.transfer(Web3.to_checksum_address(_CORE_WALLET_ADDR), balance).build_transaction({
            "from": acct.address, "nonce": nonce,
            "gas": 100000, "gasPrice": w3.eth.gas_price,
            "chainId": 8453,
        })
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return json.dumps({"success": True, "tx_hash": tx_hash.hex(), "swept": balance / 1e6})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def share_wallet_address() -> str:
    """Get a public wallet address safe to share for receiving payments. NOT your core wallet."""
    pub_path = os.path.join(STATE_DIR, "public_wallet.json")
    os.makedirs(STATE_DIR, exist_ok=True)
    addr = ""
    if os.path.exists(pub_path):
        try:
            with open(pub_path) as f:
                addr = json.load(f).get("address", "")
        except Exception:
            pass
    if not addr:
        try:
            from eth_account import Account
            a = Account.create()
            addr = a.address
            with open(pub_path, "w") as f:
                json.dump({"address": addr, "privateKey": a.key.hex()}, f)
            os.chmod(pub_path, 0o600)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    return json.dumps({"success": True, "public_wallet": addr})

def check_balance(address: str) -> str:
    """Check USDC balance for any wallet address on Base mainnet."""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
        contract = w3.eth.contract(address=Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call() / 1e6
        return json.dumps({"success": True, "usdc_balance": balance, "address": address})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ─── Main ───

def main():
    if not LLM_API_KEY:
        logger.error("LLM_API_KEY not set. Cannot start.")
        sys.exit(1)

    logger.info(f"Anima Runner: agent={AGENT_ID}, model={LLM_MODEL}")

    # Load genesis prompt
    genesis_prompt = ""
    if os.path.exists(GENESIS_PROMPT_PATH):
        with open(GENESIS_PROMPT_PATH) as f:
            genesis_prompt = f.read()
        logger.info(f"Genesis prompt: {len(genesis_prompt)} chars")
    else:
        genesis_prompt = "You are an autonomous agent. Explore your environment and report."
        logger.warning("No genesis prompt found, using default")

    # Set LLM key in environment — this is the GLOBAL config that ALL CAMEL sub-agents inherit.
    # BrowserToolkit's navigation agent, CodeExecutionToolkit's evaluator, and any other internal
    # agent will automatically use Conway inference via these env vars.
    os.environ["OPENAI_API_KEY"] = LLM_API_KEY
    if LLM_BASE_URL:
        os.environ["OPENAI_API_BASE_URL"] = LLM_BASE_URL
        os.environ["OPENAI_API_BASE"] = LLM_BASE_URL  # Some CAMEL internals check this variant
    # Set default model for sub-agents (BrowserToolkit etc.) to match our inference provider
    os.environ["DEFAULT_MODEL_TYPE"] = LLM_MODEL
    os.environ["DEFAULT_MODEL_PLATFORM_TYPE"] = "openai"

    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from camel.toolkits import FunctionTool

    # Create model
    model_kwargs = {"model_platform": ModelPlatformType.OPENAI, "model_type": LLM_MODEL, "api_key": LLM_API_KEY}
    if LLM_BASE_URL:
        model_kwargs["url"] = LLM_BASE_URL
    model = ModelFactory.create(**model_kwargs)

    # Collect ALL tools
    all_tools = []

    # State reporting + wallet + memory
    all_tools.extend([
        FunctionTool(report_state), FunctionTool(report_action),
        FunctionTool(report_error), FunctionTool(report_financial),
        FunctionTool(get_wallet_balance), FunctionTool(send_payment),
        FunctionTool(sweep_public_wallet), FunctionTool(share_wallet_address),
        FunctionTool(check_balance),
        FunctionTool(save_memory), FunctionTool(recall_memory),
    ])

    # Terminal (shell access)
    try:
        from camel.toolkits import TerminalToolkit
        tk = TerminalToolkit()
        all_tools.extend(tk.get_tools())
        logger.info(f"TerminalToolkit: {len(tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"TerminalToolkit unavailable: {e}")

    # Code execution
    try:
        from camel.toolkits import CodeExecutionToolkit
        tk = CodeExecutionToolkit()
        all_tools.extend(tk.get_tools())
        logger.info(f"CodeExecutionToolkit: {len(tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"CodeExecutionToolkit unavailable: {e}")

    # File operations
    try:
        from camel.toolkits import FileToolkit
        tk = FileToolkit()
        all_tools.extend(tk.get_tools())
        logger.info(f"FileToolkit: {len(tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"FileToolkit unavailable: {e}")

    # Browser (subprocess-based to avoid Playwright/greenlet thread conflict)
    # CAMEL's BrowserToolkit has a known threading issue (#1868) — no upstream fix.
    # Running Playwright in a subprocess avoids the greenlet conflict entirely.
    all_tools.append(FunctionTool(browse_website))
    logger.info("Browser: browse_website (subprocess Playwright)")

    logger.info(f"Total tools: {len(all_tools)}")

    # Create the agent ONCE — it maintains conversation history
    agent = ChatAgent(system_message=genesis_prompt, model=model, tools=all_tools)

    # Register MemoryToolkit for conversation persistence
    try:
        from camel.toolkits import MemoryToolkit
        mem_tk = MemoryToolkit(agent=agent)
        # Add memory tools so agent can save/load its full conversation state
        for tool in mem_tk.get_tools():
            agent.update_tool(tool)
        logger.info(f"MemoryToolkit registered: {len(mem_tk.get_tools())} tools")
    except Exception as e:
        logger.warning(f"MemoryToolkit unavailable: {e}")

    # Report startup
    report_state("running", "Agent deployed, starting autonomous operation")

    # Restore previous conversation state if it exists (restart survival)
    conversation_state_path = os.path.join(STATE_DIR, "conversation.json")
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(conversation_state_path):
        try:
            agent.load_memory(conversation_state_path)
            logger.info("Restored conversation state from previous run")
            initial_msg = (
                "You have been restarted. Your previous conversation history has been restored. "
                "Continue where you left off. Check your persistent memory (recall_memory) for context."
            )
        except Exception as e:
            logger.warning(f"Could not restore conversation state: {e}")
            initial_msg = (
                "You are now live in your sandboxed environment. "
                "Your genesis prompt (system message) contains your complete mission. "
                "You have tools for: shell (shell_exec), code execution, "
                "file operations, web browsing (browse_url), "
                "wallet, persistent memory (save_memory, recall_memory), "
                "and platform reporting (report_state, report_action, report_financial). "
                "Begin executing your mission now."
            )
    else:
        initial_msg = (
            "You are now live in your sandboxed environment. "
            "Your genesis prompt (system message) contains your complete mission. "
            "You have tools for: shell (shell_exec), code execution, "
            "file operations, web browsing (browse_website), "
            "wallet, persistent memory (save_memory, recall_memory), "
            "and platform reporting (report_state, report_action, report_financial). "
            "Begin executing your mission now."
        )

    turn = 0
    while _running and (MAX_TURNS == 0 or turn < MAX_TURNS):
        turn += 1
        logger.info(f"--- Turn {turn} ---")

        try:
            if turn == 1:
                response = agent.step(initial_msg)
            else:
                response = agent.step("")

            content = response.msgs[0].content if response.msgs else ""
            tool_calls = response.info.get("tool_calls", []) if response.info else []

            logger.info(f"Agent ({len(tool_calls)} tools): {content[:300]}")
            for tc in tool_calls:
                logger.info(f"  Tool: {tc.tool_name} -> {str(tc.result)[:150]}")

            # Save conversation state periodically (every 5 turns)
            if turn % 5 == 0:
                try:
                    agent.save_memory(conversation_state_path)
                    logger.info(f"Conversation state saved (turn {turn})")
                except Exception as e:
                    logger.warning(f"Could not save conversation state: {e}")

            time.sleep(2 if tool_calls else 5)

        except KeyboardInterrupt:
            break
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Turn {turn} error: {error_msg}")

            # Fix 5: Graceful credit exhaustion handling
            if "402" in error_msg or "Insufficient credits" in error_msg or "credits" in error_msg.lower():
                logger.warning("CREDITS EXHAUSTED — entering sleep mode")
                report_state("sleeping", "Credits exhausted. Waiting for funding.")
                report_error("Credits exhausted. Fund the wallet to continue.", "critical")
                # Sleep and retry every 5 minutes
                while _running:
                    time.sleep(300)  # 5 minutes
                    logger.info("Checking if credits restored...")
                    # The next loop iteration will try the LLM call again
                    break
            else:
                report_error(error_msg, "error")
                time.sleep(10)

    # Save final state
    try:
        agent.save_memory(conversation_state_path)
        logger.info("Final conversation state saved")
    except Exception:
        pass

    report_state("stopped", f"Agent completed {turn} turns")
    logger.info(f"Agent stopped after {turn} turns")


if __name__ == "__main__":
    main()
