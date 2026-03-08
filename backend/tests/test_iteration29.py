"""
Iteration 29 Backend Tests — Telegram Config, Sidebar, Agent Mind

Test features:
1. PUT /api/agents/{id}/telegram validates and updates Telegram config
2. PUT /api/agents/{id}/telegram rejects invalid tokens
3. POST /api/agents/create rejects missing Telegram fields
4. GET /api/agents never exposes telegram_bot_token (SECURITY)
5. GET /api/telegram/health returns bot_alive status
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestTelegramConfig:
    """Telegram configuration and security tests"""

    def test_health_endpoint(self):
        """GET /api/health returns status=ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ GET /api/health works")

    def test_telegram_health_returns_bot_alive(self):
        """GET /api/telegram/health returns bot_alive status for agents"""
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "checked_at" in data
        # Each agent should have bot_alive field
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "bot_alive" in agent
            assert "configured" in agent
            assert isinstance(agent["bot_alive"], bool)
        print(f"✅ GET /api/telegram/health returns {len(data['agents'])} agents with bot_alive status")

    def test_agents_never_expose_bot_token(self):
        """GET /api/agents never exposes telegram_bot_token (SECURITY)"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        for agent in data["agents"]:
            assert "telegram_bot_token" not in agent, f"SECURITY VIOLATION: telegram_bot_token exposed for agent {agent.get('agent_id')}"
        print("✅ GET /api/agents does NOT expose telegram_bot_token (SECURITY OK)")

    def test_create_agent_rejects_missing_telegram(self):
        """POST /api/agents/create rejects missing Telegram fields"""
        response = requests.post(f"{BASE_URL}/api/agents/create", json={
            "name": "TEST_NO_TG",
            "genesis_prompt": "Test agent without telegram"
        })
        # Should return 400 error
        assert response.status_code == 400
        data = response.json()
        assert "Telegram" in data.get("detail", "")
        print("✅ POST /api/agents/create rejects missing Telegram fields")

    def test_put_telegram_rejects_invalid_token(self):
        """PUT /api/agents/{id}/telegram rejects invalid tokens"""
        # Use existing test agent
        response = requests.get(f"{BASE_URL}/api/agents")
        agents = response.json().get("agents", [])
        test_agent = None
        for a in agents:
            if not a.get("is_default"):
                test_agent = a
                break
        
        if not test_agent:
            pytest.skip("No non-default agent to test PUT /api/agents/{id}/telegram")
        
        agent_id = test_agent["agent_id"]
        
        # Try to update with invalid token
        response = requests.put(f"{BASE_URL}/api/agents/{agent_id}/telegram", json={
            "telegram_bot_token": "invalid_token_abc123",
            "telegram_chat_id": "123456789"
        })
        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data.get("detail", "") or "invalid" in data.get("detail", "").lower()
        print(f"✅ PUT /api/agents/{agent_id}/telegram rejects invalid token")

    def test_put_telegram_missing_fields(self):
        """PUT /api/agents/{id}/telegram rejects missing fields"""
        response = requests.get(f"{BASE_URL}/api/agents")
        agents = response.json().get("agents", [])
        test_agent = None
        for a in agents:
            if not a.get("is_default"):
                test_agent = a
                break
        
        if not test_agent:
            pytest.skip("No non-default agent")
        
        agent_id = test_agent["agent_id"]
        
        # Try empty token
        response = requests.put(f"{BASE_URL}/api/agents/{agent_id}/telegram", json={
            "telegram_bot_token": "",
            "telegram_chat_id": "123"
        })
        assert response.status_code == 400
        print(f"✅ PUT /api/agents/{agent_id}/telegram rejects empty token")

    def test_put_telegram_nonexistent_agent(self):
        """PUT /api/agents/{id}/telegram returns 404 for nonexistent agent"""
        response = requests.put(f"{BASE_URL}/api/agents/nonexistent-agent-xyz/telegram", json={
            "telegram_bot_token": "123456:ABC-DEF",
            "telegram_chat_id": "123456789"
        })
        assert response.status_code == 404
        print("✅ PUT /api/agents/{nonexistent}/telegram returns 404")


class TestSkillsEndpoint:
    """Skills listing tests"""

    def test_skills_available(self):
        """GET /api/skills/available returns skills with sources"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert data["total"] > 0
        
        # Verify skills have required fields
        sources = set()
        for skill in data["skills"]:
            assert "name" in skill
            assert "source" in skill
            sources.add(skill["source"])
        
        print(f"✅ GET /api/skills/available returns {data['total']} skills from {len(sources)} sources")
        print(f"   Sources: {sorted(sources)}")


class TestFundHQData:
    """Test Fund HQ data endpoints"""

    def test_engine_live(self):
        """GET /api/engine/live returns engine status"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        # Should have at least these fields
        assert "db_exists" in data or "live" in data
        print(f"✅ GET /api/engine/live returns engine status: db_exists={data.get('db_exists')}")

    def test_live_agents(self):
        """GET /api/live/agents returns agents data"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"✅ GET /api/live/agents returns {len(data.get('agents', []))} agents")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
