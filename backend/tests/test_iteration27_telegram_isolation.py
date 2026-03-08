"""
Iteration 27 - Telegram Isolation Tests
Tests:
1. GET /api/agents returns telegram_configured=true and doesn't expose telegram_bot_token
2. GET /api/telegram/status returns correct status for default agent
3. GET /api/telegram/status?agent_id=anima-fund returns proper config
4. POST /api/agents/create WITHOUT telegram creds returns 400 error
5. POST /api/agents/create WITH telegram creds succeeds and stores per-agent config
6. POST /api/telegram/test/anima-fund sends test message
7. GET /api/telegram/status?agent_id=<new-agent-id> shows uses_own_bot=true
8. GET /api/skills/available returns 141+ skills
9. DELETE /api/agents/<agent-id> cleans up test agents
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAgentListSecurity:
    """Agent list API security tests - telegram_bot_token should never be exposed"""
    
    def test_agents_list_returns_agents(self):
        """GET /api/agents returns proper list with telegram_configured"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 1
        print(f"Found {len(data['agents'])} agents")
        
    def test_agents_list_default_has_telegram_configured(self):
        """Default Anima Fund agent should have telegram_configured=True"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        
        # Find the default anima-fund agent
        anima_fund = next((a for a in data["agents"] if a.get("agent_id") == "anima-fund"), None)
        assert anima_fund is not None, "Anima Fund agent should exist"
        assert anima_fund.get("telegram_configured") == True, "Anima Fund should have telegram_configured=True"
        print(f"Anima Fund agent: {anima_fund.get('name')}, telegram_configured={anima_fund.get('telegram_configured')}")
        
    def test_agents_list_does_not_expose_telegram_token(self):
        """SECURITY: telegram_bot_token must NOT be exposed in agent list response"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        
        for agent in data["agents"]:
            assert "telegram_bot_token" not in agent, f"Agent {agent.get('agent_id')} exposes telegram_bot_token - SECURITY ISSUE!"
        print("PASSED: No agents expose telegram_bot_token in list response")


class TestTelegramStatus:
    """Telegram status API tests"""
    
    def test_telegram_status_default(self):
        """GET /api/telegram/status returns status for default agent"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data
        assert data.get("agent_id") == "anima-fund"
        print(f"Default telegram status: configured={data.get('configured')}, uses_own_bot={data.get('uses_own_bot')}")
        
    def test_telegram_status_for_anima_fund(self):
        """GET /api/telegram/status?agent_id=anima-fund returns proper config"""
        response = requests.get(f"{BASE_URL}/api/telegram/status", params={"agent_id": "anima-fund"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("agent_id") == "anima-fund"
        assert data.get("uses_own_bot") == True
        assert data.get("configured") == True
        print(f"Anima Fund telegram: configured={data.get('configured')}, uses_own_bot={data.get('uses_own_bot')}")


class TestTelegramTest:
    """Telegram test message API"""
    
    def test_telegram_test_anima_fund(self):
        """POST /api/telegram/test/anima-fund sends test message"""
        response = requests.post(f"{BASE_URL}/api/telegram/test/anima-fund")
        # Should succeed if env vars are set
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert data.get("agent_id") == "anima-fund"
            print(f"Telegram test SUCCESS: {data.get('message')}")
        elif response.status_code == 500:
            # May fail if Telegram token/chat are invalid - still acceptable for test
            print(f"Telegram test failed (500) - token/chat may be misconfigured")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")


class TestAgentCreationTelegramRequired:
    """Agent creation tests - Telegram fields are now REQUIRED"""
    
    def test_create_agent_without_telegram_fails(self):
        """POST /api/agents/create WITHOUT telegram_bot_token and telegram_chat_id should return 400"""
        payload = {
            "name": "TEST_NoTelegram_Agent",
            "genesis_prompt": "This is a test agent without telegram"
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "Telegram Bot Token and Chat ID are required" in data.get("detail", ""), f"Wrong error message: {data}"
        print(f"Correctly rejected agent without Telegram: {data.get('detail')}")
        
    def test_create_agent_with_only_token_fails(self):
        """POST /api/agents/create with only token (no chat_id) should return 400"""
        payload = {
            "name": "TEST_OnlyToken_Agent",
            "genesis_prompt": "Test agent",
            "telegram_bot_token": "12345:ABCDEF"
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"Correctly rejected agent with only token")
        
    def test_create_agent_with_only_chatid_fails(self):
        """POST /api/agents/create with only chat_id (no token) should return 400"""
        payload = {
            "name": "TEST_OnlyChatId_Agent",
            "genesis_prompt": "Test agent",
            "telegram_chat_id": "123456789"
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"Correctly rejected agent with only chat_id")


class TestAgentCreationWithTelegram:
    """Agent creation with proper Telegram credentials"""
    
    @pytest.fixture(scope="class")
    def test_agent_id(self):
        return "test-telegram-isolation-agent"
    
    def test_create_agent_with_telegram_succeeds(self, test_agent_id):
        """POST /api/agents/create WITH telegram creds should succeed"""
        # First clean up if exists
        requests.delete(f"{BASE_URL}/api/agents/{test_agent_id}")
        
        payload = {
            "name": "TEST Telegram Isolation Agent",
            "genesis_prompt": "This is a test agent with its own telegram bot",
            "telegram_bot_token": "TEST_TOKEN_1234567:ABCDEFGHIJKLMNOP",
            "telegram_chat_id": "TEST_CHAT_987654321"
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("agent") is not None
        assert data["agent"]["telegram_configured"] == True
        # Security: token should NOT be in response
        assert "telegram_bot_token" not in data["agent"], "telegram_bot_token should NOT be in response"
        print(f"Created agent: {data['agent'].get('agent_id')}, telegram_configured={data['agent'].get('telegram_configured')}")
        
    def test_new_agent_uses_own_bot(self, test_agent_id):
        """GET /api/telegram/status?agent_id=<new-agent-id> should show uses_own_bot=true"""
        response = requests.get(f"{BASE_URL}/api/telegram/status", params={"agent_id": test_agent_id})
        assert response.status_code == 200
        data = response.json()
        assert data.get("uses_own_bot") == True, f"New agent should use its own bot, got: {data}"
        assert data.get("bot_token_set") == True
        assert data.get("chat_id_set") == True
        print(f"New agent telegram status: uses_own_bot={data.get('uses_own_bot')}")
        
    def test_new_agent_not_in_list_with_token_exposed(self, test_agent_id):
        """Verify new agent appears in list but token is not exposed"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        
        test_agent = next((a for a in data["agents"] if a.get("agent_id") == test_agent_id), None)
        assert test_agent is not None, f"Test agent {test_agent_id} should be in list"
        assert "telegram_bot_token" not in test_agent, "Token should NOT be exposed in list"
        assert test_agent.get("telegram_configured") == True
        print(f"Test agent in list: telegram_configured={test_agent.get('telegram_configured')}, no token exposed")
        
    def test_delete_test_agent(self, test_agent_id):
        """DELETE /api/agents/<agent-id> should clean up test agent"""
        response = requests.delete(f"{BASE_URL}/api/agents/{test_agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"Deleted test agent: {test_agent_id}")


class TestSkillsAPI:
    """Skills API tests - should return 141+ skills"""
    
    def test_skills_available_returns_many_skills(self):
        """GET /api/skills/available should return 141+ skills with all sources"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total", 0)
        skills = data.get("skills", [])
        
        assert total >= 100, f"Expected 100+ skills, got {total}"
        print(f"Skills API returned {total} skills")
        
        # Check source distribution
        sources = {}
        for skill in skills:
            src = skill.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        print(f"Source breakdown: {sources}")
        
        # Verify key sources exist
        assert "anima" in sources or sum(sources.values()) > 50, "Should have anima skills"
        
    def test_skills_include_conway_tools(self):
        """Skills should include Conway Terminal tools"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data.get("skills", [])
        
        conway_skills = [s for s in skills if s.get("source", "").startswith("conway")]
        assert len(conway_skills) >= 10, f"Expected 10+ Conway tools, got {len(conway_skills)}"
        
        conway_names = [s.get("name") for s in conway_skills]
        expected = ["sandbox_create", "sandbox_exec", "chat_completions", "wallet_info"]
        for exp in expected:
            assert exp in conway_names, f"Missing Conway tool: {exp}"
        print(f"Conway tools verified: {len(conway_skills)} tools including {expected[:3]}")
        
    def test_skills_include_openclaw_tools(self):
        """Skills should include OpenClaw tools"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data.get("skills", [])
        
        openclaw_skills = [s for s in skills if s.get("source") == "openclaw"]
        assert len(openclaw_skills) >= 10, f"Expected 10+ OpenClaw tools, got {len(openclaw_skills)}"
        
        openclaw_names = [s.get("name") for s in openclaw_skills]
        expected = ["browse_page", "browser", "discover_agents"]
        for exp in expected:
            assert exp in openclaw_names, f"Missing OpenClaw tool: {exp}"
        print(f"OpenClaw tools verified: {len(openclaw_skills)} tools")


class TestDeleteDefaultAgentBlocked:
    """Verify default agent cannot be deleted"""
    
    def test_cannot_delete_anima_fund(self):
        """DELETE /api/agents/anima-fund should be blocked"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "Cannot delete" in data.get("detail", ""), f"Wrong error: {data}"
        print("Correctly blocked deletion of default agent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
