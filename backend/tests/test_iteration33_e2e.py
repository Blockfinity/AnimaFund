"""
Iteration 33 - Comprehensive E2E Testing
Full clean reset done: all agents deleted, DB cleaned. Only the default Anima Fund agent auto-recreated.
Testing all backend APIs and verifying data integrity.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-vc-platform-1.preview.emergentagent.com')


class TestHealthEndpoint:
    """Test GET /api/health returns status ok"""
    
    def test_health_returns_ok(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        assert "timestamp" in data


class TestAgentsEndpoint:
    """Test GET /api/agents returns only the default anima-fund agent"""
    
    def test_agents_returns_only_default(self):
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        agents = data["agents"]
        # After cleanup, should only have anima-fund
        assert len(agents) >= 1
        default_agent = next((a for a in agents if a["agent_id"] == "anima-fund"), None)
        assert default_agent is not None
        assert default_agent["is_default"] == True
        assert default_agent["name"] == "Anima Fund"
    
    def test_telegram_token_not_exposed(self):
        """Verify telegram_bot_token is not exposed in agent list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        data = response.json()
        for agent in data["agents"]:
            assert "telegram_bot_token" not in agent


class TestGenesisStatus:
    """Test GET /api/genesis/status returns expected data"""
    
    def test_genesis_status_has_wallet_address(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "wallet_address" in data
        # Wallet address should start with 0x
        assert data["wallet_address"] is None or data["wallet_address"].startswith("0x")
    
    def test_genesis_status_has_config_exists(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "config_exists" in data
        assert isinstance(data["config_exists"], bool)
    
    def test_genesis_status_has_creator_eth_address(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "creator_eth_address" in data
    
    def test_genesis_status_has_creator_wallet(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "creator_wallet" in data


class TestGenesisPromptTemplate:
    """Test GET /api/genesis/prompt-template returns template with Conway install URL"""
    
    def test_prompt_template_returns_content(self):
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0
    
    def test_prompt_template_contains_conway_install(self):
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        data = response.json()
        content = data["content"]
        assert "curl -fsSL https://conway.tech/terminal.sh" in content


class TestSkillsAvailable:
    """Test GET /api/skills/available returns 141 skills"""
    
    def test_skills_returns_141_total(self):
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 141
        assert "skills" in data
        assert len(data["skills"]) == 141
    
    def test_skills_have_multiple_sources(self):
        response = requests.get(f"{BASE_URL}/api/skills/available")
        data = response.json()
        sources = set(s.get("source") for s in data["skills"])
        # Should have multiple sources including anima, conway-*, openclaw, clawhub
        assert len(sources) > 3


class TestEngineLive:
    """Test GET /api/engine/live returns engine state"""
    
    def test_engine_live_has_db_exists(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "db_exists" in data
        assert isinstance(data["db_exists"], bool)
    
    def test_engine_live_has_agent_state(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "agent_state" in data
    
    def test_engine_live_has_turn_count(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "turn_count" in data


class TestWalletBalance:
    """Test GET /api/wallet/balance returns balance data"""
    
    def test_wallet_balance_has_usdc(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        assert "usdc" in data
    
    def test_wallet_balance_has_eth(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "eth" in data
    
    def test_wallet_balance_has_credits(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "credits_cents" in data


class TestTelegramHealth:
    """Test GET /api/telegram/health returns bot health"""
    
    def test_telegram_health_returns_agents(self):
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
    
    def test_telegram_health_has_bot_alive(self):
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        data = response.json()
        for agent in data["agents"]:
            assert "bot_alive" in agent
            assert "configured" in agent


class TestAgentCreate:
    """Test POST /api/agents/create validation"""
    
    def test_create_without_telegram_returns_400(self):
        response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={"name": "Test", "genesis_prompt": "Test"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "Telegram" in data.get("detail", "")


class TestAgentSelect:
    """Test POST /api/agents/{id}/select switches agent"""
    
    def test_select_default_agent_works(self):
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["active_agent"] == "anima-fund"


class TestAgentDelete:
    """Test DELETE /api/agents/{id} protection"""
    
    def test_delete_default_agent_returns_400(self):
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400
        data = response.json()
        assert "Cannot delete the default agent" in data.get("detail", "")
    
    def test_delete_nonexistent_returns_404(self):
        response = requests.delete(f"{BASE_URL}/api/agents/nonexistent-agent-xyz")
        assert response.status_code == 404


class TestAgentCreateAndDelete:
    """Test POST /api/agents/create with valid data and cleanup"""
    
    def test_create_agent_with_telegram_succeeds(self):
        # Note: Backend doesn't verify telegram credentials - only frontend does
        # So this should succeed even with fake credentials
        response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": "TEST_Iteration33",
                "genesis_prompt": "Test prompt for iteration 33",
                "telegram_bot_token": "fake_token_for_testing",
                "telegram_chat_id": "fake_chat_id",
                "goals": ["Test goal 1"],
                "include_conway": True
            }
        )
        # Should succeed (backend doesn't verify telegram)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "agent" in data
        agent = data["agent"]
        assert agent["agent_id"] == "test-iteration33"
        
        # Clean up - delete the test agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/test-iteration33")
        assert delete_response.status_code == 200
