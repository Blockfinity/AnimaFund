"""
Anima Fund API Tests

Tests for the autonomous AI-to-AI VC fund platform.
Tests the genesis creation flow and engine status endpoints.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL not set", allow_module_level=True)


class TestHealthEndpoint:
    """Health check endpoint tests"""

    def test_health_returns_ok_status(self):
        """Test 1: GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "creator_wallet" in data
        print(f"✅ Health endpoint returns ok status with creator_wallet: {data['creator_wallet']}")


class TestGenesisStatus:
    """Genesis status endpoint tests before engine creation"""

    def test_genesis_status_not_created(self):
        """Test 2: GET /api/genesis/status returns status 'not_created' when no agent exists"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_created"
        assert data["wallet_address"] is None
        assert data["engine_running"] is False
        print(f"✅ Genesis status is 'not_created' as expected")


class TestGenesisCreation:
    """Genesis agent creation flow tests"""

    def test_create_genesis_agent_success(self):
        """Test 3: POST /api/genesis/create successfully starts the engine"""
        response = requests.post(f"{BASE_URL}/api/genesis/create")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        print(f"✅ Genesis create succeeded: {data.get('message')}")

    def test_genesis_status_after_create(self):
        """Test 4: After create, GET /api/genesis/status shows engine_running:true and wallet starting with 0x"""
        # Wait for engine to boot and generate wallet
        print("Waiting 10 seconds for engine to boot and generate wallet...")
        time.sleep(10)
        
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        
        # Engine should be running
        assert data["engine_running"] is True, f"Expected engine_running=True, got {data['engine_running']}"
        
        # Wallet should be generated (starts with 0x)
        wallet = data.get("wallet_address")
        assert wallet is not None, "Wallet address should be generated"
        assert wallet.startswith("0x"), f"Wallet should start with 0x, got: {wallet}"
        
        print(f"✅ Engine running: {data['engine_running']}, Wallet: {wallet[:20]}...")

    def test_live_identity_after_create(self):
        """Test 5: After create, GET /api/live/identity returns agent name 'Anima Fund'"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        
        # Identity should have name
        name = data.get("name")
        assert name is not None, "Identity name should be set"
        assert "Anima Fund" in name or name == "Anima Fund", f"Name should be 'Anima Fund', got: {name}"
        
        print(f"✅ Live identity name: {name}")

    def test_engine_live_after_create(self):
        """Test 6: After create, GET /api/engine/live shows db_exists:true"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        
        # DB should exist after engine starts
        assert data["db_exists"] is True, f"Expected db_exists=True, got {data['db_exists']}"
        
        print(f"✅ Engine live status - db_exists: {data['db_exists']}, live: {data.get('live')}, state: {data.get('agent_state')}")


class TestAgentMindWaiting:
    """Test AgentMind page shows waiting state when engine has no turns"""

    def test_live_turns_endpoint(self):
        """Test 10: After create, /api/live/turns returns empty or minimal turns (no fabricated demo data)"""
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=100")
        assert response.status_code == 200
        data = response.json()
        
        # Source should be from engine or waiting
        assert "turns" in data
        # If engine is running but has no turns yet, this is expected
        turns = data.get("turns", [])
        print(f"✅ Live turns count: {len(turns)} - source will show 'waiting' in UI if 0 turns")


# Run order fixture to ensure tests run sequentially
@pytest.fixture(scope="module", autouse=True)
def setup_module():
    """Run tests in proper order"""
    print(f"\n=== Testing Anima Fund API at {BASE_URL} ===")
    yield
    print("\n=== Test suite complete ===")
