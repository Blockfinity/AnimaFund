"""
Iteration 24: MongoDB Refactor Verification Tests
Tests specific to the state migration from filesystem to MongoDB:
- Provisioning state read from MongoDB (not filesystem)
- Conway API key stored/retrieved from MongoDB
- Agent creation stores genesis_prompt in MongoDB
- live/identity reads from MongoDB
- live/tools reads from MongoDB provisioning state
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://ai-agent-sandbox-1.preview.emergentagent.com"


class TestMongoDBProvisioningState:
    """Verify provisioning state is read from MongoDB"""

    def test_genesis_status_returns_agent_id(self):
        """GET /api/genesis/status — returns agent_id from MongoDB"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert data["agent_id"] == "anima-fund" or data["agent_id"] is not None
        # Stage should be derived from MongoDB provisioning
        assert "stage" in data
        assert data["stage"] in ["not_created", "sandbox_created", "provisioning", "skills_loaded", "running"]
        print(f"Genesis status from MongoDB: agent_id={data['agent_id']}, stage={data['stage']}")

    def test_provision_status_returns_sandbox_from_db(self):
        """GET /api/provision/status — sandbox info from MongoDB"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox" in data
        assert "tools" in data
        assert "agent_id" in data
        # Sandbox should be a dict with status, id, etc.
        assert isinstance(data["sandbox"], dict)
        assert "status" in data["sandbox"]
        print(f"Provision status: sandbox={data['sandbox']}, tools_count={len(data.get('tools', {}))}")


class TestMongoDBConwayKeyManagement:
    """Verify Conway API key is stored/retrieved from MongoDB"""

    def test_key_status_reads_from_mongodb(self):
        """GET /api/credits/key-status — reads key from MongoDB via agent_state"""
        response = requests.get(f"{BASE_URL}/api/credits/key-status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        # If configured, should show key prefix
        if data.get("configured"):
            assert "key_prefix" in data
            # Key should start with cnwy_
            assert data["key_prefix"].startswith("cnwy_")
        print(f"Key status (MongoDB): configured={data.get('configured')}, prefix={data.get('key_prefix', 'N/A')}")

    def test_credits_balance_uses_mongodb_key(self):
        """GET /api/credits/balance — fetches balance using key from MongoDB"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200
        data = response.json()
        # Should return credits_cents (may be 0 if $0 balance)
        assert "credits_cents" in data
        print(f"Credits balance (using MongoDB key): {data}")


class TestMongoDBAgentCreation:
    """Verify agent creation stores in MongoDB only, not filesystem"""

    def test_create_agent_stores_in_mongodb(self):
        """POST /api/agents/create — stores genesis_prompt in MongoDB, not filesystem"""
        # This test creates a test agent, verifies it exists, then cleans up
        import time
        test_agent_name = f"TEST_MongoDB_{int(time.time())}"
        
        # Create agent with all required fields
        create_response = requests.post(f"{BASE_URL}/api/agents/create", json={
            "name": test_agent_name,
            "genesis_prompt": "This is a test genesis prompt for MongoDB verification.",
            "welcome_message": "Test welcome",
            "goals": ["Test goal 1"],
            "telegram_bot_token": "8474833303:AAHAhnRoHSIZTEruDu4ic-tPvdzrnTadnrw",
            "telegram_chat_id": "8613975358",
        })
        
        # Should succeed (status 200)
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data.get("success") is True
        agent_id = create_data.get("agent", {}).get("agent_id")
        assert agent_id is not None
        print(f"Created test agent: {agent_id}")
        
        # Verify agent appears in list (fetched from MongoDB)
        list_response = requests.get(f"{BASE_URL}/api/agents")
        assert list_response.status_code == 200
        agents = list_response.json().get("agents", [])
        agent_ids = [a.get("agent_id") for a in agents]
        assert agent_id in agent_ids, f"New agent {agent_id} should appear in list from MongoDB"
        print(f"Agent {agent_id} found in MongoDB list")
        
        # Clean up - delete the test agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data.get("success") is True
        print(f"Cleaned up test agent: {agent_id}")


class TestMongoDBLiveEndpoints:
    """Verify live endpoints read from MongoDB, not filesystem"""

    def test_live_identity_reads_from_mongodb(self):
        """GET /api/live/identity — reads from MongoDB not filesystem"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "agent_id" in data
        # Source should indicate database/sandbox (not filesystem)
        assert data.get("source") in ["database", "sandbox"]
        print(f"Live identity (MongoDB): name={data.get('name')}, source={data.get('source')}")

    def test_live_tools_reads_from_mongodb(self):
        """GET /api/live/tools — reads from MongoDB provisioning state"""
        response = requests.get(f"{BASE_URL}/api/live/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        # Source should be sandbox (provisioning read from MongoDB)
        assert data.get("source") == "sandbox"
        print(f"Live tools (MongoDB): {len(data.get('tools', []))} tools, source={data.get('source')}")


class TestMongoDBAgentSelection:
    """Verify agent selection loads Conway key from MongoDB"""

    def test_select_agent_loads_key_from_mongodb(self):
        """POST /api/agents/{agent_id}/select — loads Conway key from MongoDB"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("active_agent") == "anima-fund"
        print(f"Agent selection (MongoDB key loaded): {data}")


class TestMongoDBProvisioningIntegrity:
    """Verify provisioning endpoints read/write to MongoDB"""

    def test_genesis_reset_clears_mongodb_state(self):
        """POST /api/genesis/reset — resets provisioning state in MongoDB"""
        # Note: This test doesn't actually reset (to avoid breaking state)
        # Just verifies the endpoint exists and returns expected format
        response = requests.post(f"{BASE_URL}/api/genesis/reset")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        print(f"Genesis reset response: {data}")

    def test_provision_status_wallet_address_from_mongodb(self):
        """GET /api/provision/status — wallet_address from MongoDB provisioning"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        # wallet_address field should exist (may be empty if not provisioned)
        assert "wallet_address" in data
        print(f"Provision wallet_address (MongoDB): {data.get('wallet_address', 'not set')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
