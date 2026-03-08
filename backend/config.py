"""
Shared constants used across routers.
"""
import os
from dotenv import load_dotenv

load_dotenv()

AUTOMATON_DIR = os.path.join(os.path.dirname(__file__), "..", "automaton")
ANIMA_DIR = os.path.expanduser("~/.anima")
CREATOR_WALLET = os.environ.get("CREATOR_WALLET")
CREATOR_ETH_ADDRESS = os.environ.get("CREATOR_ETH_ADDRESS")
ENGINE_PID_FILE = os.path.join(ANIMA_DIR, "engine.pid")
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_RPC = "https://mainnet.base.org"
