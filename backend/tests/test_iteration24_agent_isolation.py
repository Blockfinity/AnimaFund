"""
Iteration 24 - CRITICAL TEST: Agent Isolation Fix Validation

This test verifies that switching between agents returns COMPLETELY DIFFERENT data.
The bug was: switching to a new agent still showed the default agent's data.

Test Flow:
1. Health check
2. Create test agent -> should create fresh agent with no data
3. Select test agent -> should switch all data sources
4. Verify test agent returns NULL/empty data (no wallet, no engine, no SOUL)
5. Switch back to default agent (anima-fund)
6. Verify default agent returns REAL data (wallet, engine state, SOUL exists)
7. Cleanup test agent
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_AGENT_NAME = "Test Isolation Agent"
TEST_AGENT_ID = "test-isolation-agent"


class TestAgentIsolation:
    """Critical tests for agent data isolation - switching agents must show different data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_health_check(self, api_client):
        """Basic health check"""
        resp = api_client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print(f"Health: {data}")

    def test_02_create_test_agent(self, api_client):
        """Create a new test agent for isolation testing"""
        # First ensure it doesn't already exist
        resp = api_client.delete(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}")
        # Ignore result - might not exist
        
        # Create test agent
        resp = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": TEST_AGENT_NAME,
            "genesis_prompt": "Test agent for isolation testing",
            "welcome_message": "Hello test",
            "goals": ["Test isolation"],
            "selected_skills": []  # No skills needed for test
        })
        assert resp.status_code == 200, f"Failed to create agent: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["agent"]["agent_id"] == TEST_AGENT_ID
        print(f"Created test agent: {data['agent']}")

    def test_03_select_test_agent(self, api_client):
        """Select the test agent - all data sources should switch"""
        resp = api_client.post(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/select")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["active_agent"] == TEST_AGENT_ID
        print(f"Selected test agent: {data}")

    def test_04_genesis_status_for_new_agent(self, api_client):
        """CRITICAL: Genesis status for NEW agent should show null wallet and not_created stage"""
        time.sleep(0.3)  # Allow engine_bridge to switch
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        
        # NEW agent should have:
        # - wallet_address: null (no wallet yet)
        # - stage: not_created or similar
        # - engine_live: false
        # - config_exists: possibly true (auto-config.json exists from creation)
        print(f"Genesis status for NEW agent: {data}")
        
        # Key assertion: wallet_address should be null for a fresh agent
        assert data.get("wallet_address") is None, f"Expected null wallet for new agent, got: {data.get('wallet_address')}"
        # engine should not be live for a fresh agent
        assert data.get("engine_live") is False, f"Expected engine_live=false for new agent, got: {data.get('engine_live')}"
        
    def test_05_wallet_balance_for_new_agent(self, api_client):
        """CRITICAL: Wallet balance for NEW agent should return null wallet / error"""
        resp = api_client.get(f"{BASE_URL}/api/wallet/balance")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Wallet balance for NEW agent: {data}")
        
        # Should have null wallet or error indicating no wallet
        wallet = data.get("wallet")
        error = data.get("error")
        # Either wallet is null OR there's an error about no wallet
        assert wallet is None or "No wallet" in (error or ""), f"Expected null wallet for new agent, got wallet={wallet}, error={error}"

    def test_06_live_identity_for_new_agent(self, api_client):
        """CRITICAL: Live identity for NEW agent should return null name (no state.db)"""
        resp = api_client.get(f"{BASE_URL}/api/live/identity")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Live identity for NEW agent: {data}")
        
        # For a new agent without engine started, name should be null
        name = data.get("name")
        # Either null or the new agent name from auto-config.json, but NOT "Anima Fund"
        assert name != "Anima Fund", f"CRITICAL BUG: New agent returned default agent name 'Anima Fund'"
        print(f"Identity name for new agent: {name}")

    def test_07_live_soul_for_new_agent(self, api_client):
        """CRITICAL: Live soul for NEW agent should return exists=false (no SOUL.md)"""
        resp = api_client.get(f"{BASE_URL}/api/live/soul")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Live soul for NEW agent: {data}")
        
        exists = data.get("exists", False)
        content = data.get("content")
        # For a new agent, SOUL.md shouldn't exist
        assert exists is False, f"Expected exists=false for new agent SOUL, got: {exists}"
        assert content is None or content == "", f"Expected empty content for new agent SOUL"

    def test_08_engine_live_for_new_agent(self, api_client):
        """CRITICAL: Engine live check for NEW agent should return db_exists=false"""
        resp = api_client.get(f"{BASE_URL}/api/engine/live")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Engine live for NEW agent: {data}")
        
        db_exists = data.get("db_exists", False)
        live = data.get("live", False)
        # For a new agent without engine, db shouldn't exist
        assert db_exists is False, f"Expected db_exists=false for new agent, got: {db_exists}"
        assert live is False, f"Expected live=false for new agent, got: {live}"

    def test_09_switch_back_to_default_agent(self, api_client):
        """Switch back to default anima-fund agent"""
        resp = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["active_agent"] == "anima-fund"
        print(f"Switched back to default: {data}")

    def test_10_genesis_status_for_default_agent(self, api_client):
        """CRITICAL: Genesis status for DEFAULT agent should show wallet and created stage"""
        time.sleep(0.3)  # Allow engine_bridge to switch
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Genesis status for DEFAULT agent: {data}")
        
        # Default agent should have:
        # - wallet_address: 0x... (real wallet)
        # - stage: created or running
        wallet = data.get("wallet_address")
        assert wallet is not None, "Expected wallet for default agent, got None"
        assert wallet.startswith("0x"), f"Expected 0x wallet for default agent, got: {wallet}"

    def test_11_live_identity_for_default_agent(self, api_client):
        """CRITICAL: Live identity for DEFAULT agent should return 'Anima Fund' name"""
        resp = api_client.get(f"{BASE_URL}/api/live/identity")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Live identity for DEFAULT agent: {data}")
        
        name = data.get("name")
        # Default agent should have "Anima Fund" name
        assert name == "Anima Fund", f"Expected 'Anima Fund' for default agent, got: {name}"

    def test_12_live_soul_for_default_agent(self, api_client):
        """CRITICAL: Live soul for DEFAULT agent should return exists=true with SOUL.md content"""
        resp = api_client.get(f"{BASE_URL}/api/live/soul")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Live soul for DEFAULT agent: exists={data.get('exists')}, content_length={len(data.get('content') or '')}")
        
        exists = data.get("exists", False)
        content = data.get("content")
        # Default agent should have SOUL.md
        assert exists is True, f"Expected exists=true for default agent SOUL, got: {exists}"
        assert content is not None and len(content) > 0, "Expected non-empty SOUL.md content for default agent"

    def test_13_engine_live_for_default_agent(self, api_client):
        """CRITICAL: Engine live check for DEFAULT agent should return db_exists=true"""
        resp = api_client.get(f"{BASE_URL}/api/engine/live")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Engine live for DEFAULT agent: {data}")
        
        db_exists = data.get("db_exists", False)
        # Default agent should have state.db
        assert db_exists is True, f"Expected db_exists=true for default agent, got: {db_exists}"

    def test_14_skills_available(self, api_client):
        """Verify skills endpoint returns 96 skills"""
        resp = api_client.get(f"{BASE_URL}/api/skills/available")
        assert resp.status_code == 200
        data = resp.json()
        total = data.get("total", 0)
        print(f"Skills available: {total}")
        assert total == 96, f"Expected 96 skills, got: {total}"

    def test_15_agents_list(self, api_client):
        """Verify agents list includes both default and test agent"""
        resp = api_client.get(f"{BASE_URL}/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        agents = data.get("agents", [])
        agent_ids = [a.get("agent_id") for a in agents]
        print(f"Agents: {agent_ids}")
        assert "anima-fund" in agent_ids, "Default anima-fund agent should be in list"
        assert TEST_AGENT_ID in agent_ids, f"Test agent {TEST_AGENT_ID} should be in list"

    def test_16_cleanup_test_agent(self, api_client):
        """Delete the test agent"""
        resp = api_client.delete(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        print(f"Deleted test agent: {data}")

    def test_17_verify_cleanup(self, api_client):
        """Verify test agent is deleted"""
        resp = api_client.get(f"{BASE_URL}/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        agents = data.get("agents", [])
        agent_ids = [a.get("agent_id") for a in agents]
        assert TEST_AGENT_ID not in agent_ids, f"Test agent {TEST_AGENT_ID} should be deleted"
        print(f"Agents after cleanup: {agent_ids}")


class TestWalletBalanceEndpoint:
    """Test wallet/balance endpoint fields"""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_wallet_balance_fields(self, api_client):
        """Verify wallet/balance returns expected fields"""
        # First ensure we're on default agent
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.3)
        
        resp = api_client.get(f"{BASE_URL}/api/wallet/balance")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Wallet balance: {data}")
        
        # Verify wallet_mismatch field exists (critical fix from iteration 23)
        assert "wallet_mismatch" in data, "wallet_mismatch field should be present"
        
        # Verify other expected fields
        assert "wallet" in data
        assert "usdc" in data
        assert "eth" in data


class TestGenesisStatusEndpoint:
    """Test genesis/status endpoint fields"""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_genesis_status_fields(self, api_client):
        """Verify genesis/status returns expected fields including engine_wallet"""
        # First ensure we're on default agent
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.3)
        
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        print(f"Genesis status: {data}")
        
        # Verify critical fields exist
        required_fields = ["wallet_address", "engine_wallet", "wallet_mismatch", "stage", "status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
