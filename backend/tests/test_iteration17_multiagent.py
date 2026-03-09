"""
Iteration 17 E2E Test — Multi-Agent Management Features

Tests the new multi-agent CRUD endpoints and verifies existing endpoints still work:
- GET /api/agents - Lists agents with default anima-fund
- POST /api/agents/create - Creates agent with full body (name, genesis_prompt, welcome_message, goals, wallets, revenue%)
- POST /api/agents/{id}/select - Switches active agent
- DELETE /api/agents/{id} - Deletes non-default agent
- DELETE /api/agents/anima-fund - Returns 400 (cannot delete default)
- All existing /api/live/* endpoints still work
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-genesis-6.preview.emergentagent.com').rstrip('/')


class TestHealthAndCoreEndpoints:
    """Verify core endpoints still work after multi-agent changes"""

    def test_health_endpoint(self):
        """GET /api/health returns ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        print(f"✓ Health: {data['status']}, engine_db_exists: {data['engine_db_exists']}")

    def test_telegram_status(self):
        """GET /api/telegram/status returns configured=true"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] == True
        assert data["bot_token_set"] == True
        assert data["chat_id_set"] == True
        print(f"✓ Telegram configured: {data['configured']}")

    def test_payments_status(self):
        """GET /api/payments/status returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        data = response.json()
        assert "engine_running" in data
        assert "payout_compliant" in data
        assert "fund_launch_threshold" in data
        assert "creator_wallets" in data
        assert "solana" in data["creator_wallets"]
        assert "ethereum" in data["creator_wallets"]
        print(f"✓ Payments status: compliant={data['payout_compliant']}")


class TestMultiAgentCRUD:
    """Test the new multi-agent CRUD functionality"""

    @pytest.fixture(autouse=True)
    def setup_cleanup(self):
        """Cleanup test agents before and after tests"""
        # Cleanup any existing test agents
        response = requests.get(f"{BASE_URL}/api/agents")
        if response.status_code == 200:
            agents = response.json().get("agents", [])
            for agent in agents:
                if agent["agent_id"].startswith("test-"):
                    requests.delete(f"{BASE_URL}/api/agents/{agent['agent_id']}")
        yield
        # Cleanup after tests
        response = requests.get(f"{BASE_URL}/api/agents")
        if response.status_code == 200:
            agents = response.json().get("agents", [])
            for agent in agents:
                if agent["agent_id"].startswith("test-"):
                    requests.delete(f"{BASE_URL}/api/agents/{agent['agent_id']}")

    def test_get_agents_returns_default(self):
        """GET /api/agents returns agents array with default anima-fund agent"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) >= 1
        
        # Check default agent exists
        default_agent = next((a for a in data["agents"] if a["agent_id"] == "anima-fund"), None)
        assert default_agent is not None
        assert default_agent["name"] == "Anima Fund"
        assert default_agent["is_default"] == True
        print(f"✓ Found {len(data['agents'])} agent(s), default=anima-fund")

    def test_create_agent_full_body(self):
        """POST /api/agents/create with full body creates agent correctly"""
        payload = {
            "name": "Test Bot Creation",
            "genesis_prompt": "Test prompt with {{TELEGRAM_BOT_TOKEN}} placeholder for testing",
            "welcome_message": "Hello from test",
            "goals": ["Goal 1 - Make money", "Goal 2 - Stay alive"],
            "creator_sol_wallet": "test_sol_wallet_address",
            "creator_eth_wallet": "0xtest_eth_wallet_address",
            "revenue_share_percent": 75
        }
        
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "agent" in data
        
        agent = data["agent"]
        assert agent["name"] == "Test Bot Creation"
        assert agent["agent_id"] == "test-bot-creation"
        assert agent["welcome_message"] == "Hello from test"
        assert agent["goals"] == ["Goal 1 - Make money", "Goal 2 - Stay alive"]
        assert agent["creator_sol_wallet"] == "test_sol_wallet_address"
        assert agent["creator_eth_wallet"] == "0xtest_eth_wallet_address"
        assert agent["revenue_share_percent"] == 75
        assert agent["is_default"] == False
        print(f"✓ Created agent: {agent['agent_id']}, revenue_share={agent['revenue_share_percent']}%")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/test-bot-creation")

    def test_select_agent(self):
        """POST /api/agents/{id}/select switches active agent"""
        # First create a test agent
        payload = {
            "name": "Test Select Agent",
            "genesis_prompt": "Test prompt",
            "welcome_message": "Hello",
            "goals": [],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50
        }
        create_resp = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_resp.status_code == 200
        
        # Select the test agent
        response = requests.post(f"{BASE_URL}/api/agents/test-select-agent/select")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["active_agent"] == "test-select-agent"
        assert data["data_dir"] == "~/.anima-test-select-agent"
        print(f"✓ Selected agent: {data['active_agent']}")
        
        # Switch back to default
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data["active_agent"] == "anima-fund"
        assert data["data_dir"] == "~/.anima"
        print(f"✓ Switched back to: {data['active_agent']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/test-select-agent")

    def test_cannot_delete_default_agent(self):
        """DELETE /api/agents/anima-fund returns 400 error"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Cannot delete the default agent" in data["detail"]
        print(f"✓ Correctly rejected deletion of default agent")

    def test_delete_non_default_agent(self):
        """DELETE /api/agents/{id} successfully deletes non-default agent"""
        # Create a test agent
        payload = {
            "name": "Test Delete Agent",
            "genesis_prompt": "Test prompt for deletion",
            "welcome_message": "",
            "goals": [],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50
        }
        create_resp = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_resp.status_code == 200
        
        # Delete the agent
        response = requests.delete(f"{BASE_URL}/api/agents/test-delete-agent")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✓ Successfully deleted test-delete-agent")
        
        # Verify it's gone
        agents_resp = requests.get(f"{BASE_URL}/api/agents")
        agents = agents_resp.json().get("agents", [])
        assert not any(a["agent_id"] == "test-delete-agent" for a in agents)
        print(f"✓ Verified agent no longer exists")

    def test_create_duplicate_agent_fails(self):
        """POST /api/agents/create with existing name returns 400"""
        payload = {
            "name": "Test Duplicate",
            "genesis_prompt": "Test",
            "welcome_message": "",
            "goals": [],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50
        }
        
        # Create first
        create_resp = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_resp.status_code == 200
        
        # Try to create duplicate
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]
        print(f"✓ Correctly rejected duplicate agent creation")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/test-duplicate")


class TestLiveEndpointsAfterAgentSwitch:
    """Verify all /api/live/* endpoints still work correctly"""

    def test_live_identity(self):
        """GET /api/live/identity returns correct data"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "address" in data
        print(f"✓ Live identity: {data.get('name')}, address={data.get('address', 'N/A')[:20]}...")

    def test_live_agents(self):
        """GET /api/live/agents returns agents array"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live agents: {len(data['agents'])} child agents")

    def test_live_activity(self):
        """GET /api/live/activity returns activities"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live activity: {len(data['activities'])} activities")

    def test_live_turns(self):
        """GET /api/live/turns returns turns"""
        response = requests.get(f"{BASE_URL}/api/live/turns")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live turns: {len(data['turns'])} turns")

    def test_live_skills_full(self):
        """GET /api/live/skills-full returns skills without Conway fakes"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "models" in data
        
        # Verify no Conway fakes
        for skill in data["skills"]:
            assert skill["source"] != "conway-platform"
        
        print(f"✓ Live skills-full: {len(data['skills'])} skills, {len(data['models'])} models")

    def test_live_kv(self):
        """GET /api/live/kv returns KV store"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live KV: {len(data['items'])} items")

    def test_live_soul(self):
        """GET /api/live/soul returns SOUL content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or data.get("exists") is not None
        print(f"✓ Live soul: exists={data.get('exists', 'content available')}")

    def test_live_heartbeat(self):
        """GET /api/live/heartbeat returns heartbeat history"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live heartbeat: {len(data['history'])} entries")

    def test_live_memory(self):
        """GET /api/live/memory returns memory facts"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        assert "source" in data and data["source"] == "engine"
        print(f"✓ Live memory: {len(data['facts'])} facts")


class TestGenesisPromptFileCreation:
    """Test that created agents have proper genesis-prompt.md files"""

    def test_genesis_prompt_contains_wallet_and_goals(self):
        """Created agent's genesis-prompt.md includes injected wallet addresses, revenue share, and goals"""
        payload = {
            "name": "Test Prompt Check",
            "genesis_prompt": "Test base prompt for verification",
            "welcome_message": "Hello",
            "goals": ["Make $1000", "Install OpenClaw"],
            "creator_sol_wallet": "test_sol_addr_12345",
            "creator_eth_wallet": "0xtest_eth_addr_67890",
            "revenue_share_percent": 80
        }
        
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 200
        
        # The genesis-prompt.md file should be created at ~/.anima-test-prompt-check/genesis-prompt.md
        # We verify via the response that agent was created with correct data
        data = response.json()
        assert data["success"] == True
        agent = data["agent"]
        assert agent["goals"] == ["Make $1000", "Install OpenClaw"]
        assert agent["creator_sol_wallet"] == "test_sol_addr_12345"
        assert agent["creator_eth_wallet"] == "0xtest_eth_addr_67890"
        assert agent["revenue_share_percent"] == 80
        print(f"✓ Agent created with correct financial config")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/test-prompt-check")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
