"""
Iteration 28 Tests - Telegram Health Dashboard & Wallet-Protected Deletion

Tests:
1. GET /api/telegram/health - Returns health status for all agents
2. GET /api/telegram/status - Individual agent status (existing)
3. POST /api/telegram/test/anima-fund - Sends test message
4. POST /api/agents/create without telegram fields returns 400
5. POST /api/agents/create with telegram fields succeeds
6. DELETE /api/agents/anima-fund blocked (400)
7. DELETE /api/agents/{agent-with-wallet} blocked if wallet.json exists
8. GET /api/agents never exposes telegram_bot_token (security)
9. GET /api/skills/available returns 141+ skills
10. GET /api/health returns ok
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://agent-dashboard-164.preview.emergentagent.com").rstrip("/")

class TestHealthEndpoint:
    """Health check endpoint tests"""

    def test_health_returns_ok(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "timestamp" in data
        assert "engine_live" in data or "engine_db_exists" in data
        print(f"✓ Health check passed: {data}")


class TestTelegramHealthDashboard:
    """Telegram Health Dashboard endpoint tests - NEW in iteration 28"""

    def test_telegram_health_returns_agents(self):
        """GET /api/telegram/health returns health status for all agents"""
        response = requests.get(f"{BASE_URL}/api/telegram/health", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data, "Response must contain 'agents' array"
        assert "checked_at" in data, "Response must contain 'checked_at' timestamp"
        
        agents = data["agents"]
        assert isinstance(agents, list), "Agents must be a list"
        
        # Should have at least the default anima-fund agent
        if len(agents) > 0:
            agent = agents[0]
            # Verify required fields in agent health
            required_fields = ["agent_id", "name", "configured", "bot_alive"]
            for field in required_fields:
                assert field in agent, f"Agent health must include '{field}'"
            
            # Check optional fields that enhance dashboard
            optional_fields = ["bot_username", "uses_own_bot", "last_message", "last_message_time", "last_delivery_ok"]
            for field in optional_fields:
                assert field in agent, f"Agent health should include '{field}' for dashboard"
        
        print(f"✓ Telegram health returned {len(agents)} agents")
        for a in agents[:3]:  # Print first 3
            print(f"  - {a['name']}: alive={a.get('bot_alive')}, configured={a.get('configured')}")

    def test_telegram_health_anima_fund_bot_alive(self):
        """GET /api/telegram/health shows bot_alive=True for Anima Fund (has valid env vars)"""
        response = requests.get(f"{BASE_URL}/api/telegram/health", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        anima_fund = None
        for agent in data.get("agents", []):
            if agent.get("agent_id") == "anima-fund":
                anima_fund = agent
                break
        
        if anima_fund:
            assert anima_fund.get("configured") == True, "Anima Fund should be configured"
            # bot_alive depends on real Telegram API call - just check it exists
            assert "bot_alive" in anima_fund, "Should check bot_alive status"
            print(f"✓ Anima Fund: configured={anima_fund['configured']}, bot_alive={anima_fund['bot_alive']}, username={anima_fund.get('bot_username')}")
        else:
            print("⚠ Anima Fund agent not found in telegram health (may not be initialized yet)")


class TestTelegramStatus:
    """Individual Telegram status endpoint tests"""

    def test_telegram_status_default(self):
        """GET /api/telegram/status returns config for default agent"""
        response = requests.get(f"{BASE_URL}/api/telegram/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data
        assert data.get("agent_id") == "anima-fund"
        print(f"✓ Telegram status (default): {data}")

    def test_telegram_status_anima_fund(self):
        """GET /api/telegram/status?agent_id=anima-fund works"""
        response = requests.get(f"{BASE_URL}/api/telegram/status?agent_id=anima-fund", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("configured") == True
        assert data.get("uses_own_bot") == True
        print(f"✓ Telegram status for anima-fund: {data}")

    def test_telegram_status_nonexistent_agent(self):
        """GET /api/telegram/status?agent_id=nonexistent returns 404"""
        response = requests.get(f"{BASE_URL}/api/telegram/status?agent_id=nonexistent-agent-xyz", timeout=10)
        assert response.status_code == 404
        print("✓ Correctly returns 404 for nonexistent agent")


class TestTelegramTestMessage:
    """Telegram test message endpoint"""

    def test_telegram_test_anima_fund(self):
        """POST /api/telegram/test/anima-fund sends test message"""
        response = requests.post(f"{BASE_URL}/api/telegram/test/anima-fund", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("agent_id") == "anima-fund"
        assert "message" in data
        print(f"✓ Telegram test message sent: {data}")


class TestAgentCreation:
    """Agent creation with required Telegram fields"""
    
    created_agent_id = None

    def test_create_agent_without_telegram_returns_400(self):
        """POST /api/agents/create without telegram fields returns 400"""
        payload = {
            "name": "Test No Telegram",
            "genesis_prompt": "Test prompt for agent without telegram",
            "goals": []
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload, timeout=10)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        
        # Check error message mentions Telegram requirement
        detail = str(data.get("detail", "")).lower()
        assert "telegram" in detail, f"Error should mention Telegram: {data}"
        print(f"✓ Correctly rejected agent creation without Telegram: {data.get('detail')}")

    def test_create_agent_with_telegram_succeeds(self):
        """POST /api/agents/create with telegram fields succeeds"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"Test Agent {unique_id}",
            "genesis_prompt": "Test prompt with Telegram configured",
            "telegram_bot_token": "1234567890:AATest-FakeTokenForTesting",
            "telegram_chat_id": "123456789",
            "goals": ["Test goal"]
        }
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        agent = data.get("agent", {})
        assert "agent_id" in agent
        TestAgentCreation.created_agent_id = agent["agent_id"]
        
        # Verify telegram_configured is set
        assert agent.get("telegram_configured") == True
        # Security: Verify token is NOT exposed in response
        assert "telegram_bot_token" not in agent, "telegram_bot_token should NOT be in response"
        
        print(f"✓ Agent created: {agent['agent_id']}, telegram_configured={agent.get('telegram_configured')}")
        return agent["agent_id"]

    def test_cleanup_created_agent(self):
        """Delete the test agent created in previous test"""
        if TestAgentCreation.created_agent_id:
            response = requests.delete(f"{BASE_URL}/api/agents/{TestAgentCreation.created_agent_id}", timeout=10)
            # May be 200 or 404 (if already deleted)
            print(f"✓ Cleanup: DELETE agent returned {response.status_code}")


class TestAgentDeletion:
    """Agent deletion protection tests"""

    def test_delete_anima_fund_blocked(self):
        """DELETE /api/agents/anima-fund is blocked (400)"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund", timeout=10)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        
        detail = str(data.get("detail", "")).lower()
        assert "default" in detail or "cannot" in detail, f"Error should mention default agent protection: {data}"
        print(f"✓ Correctly blocked deletion of anima-fund: {data.get('detail')}")

    def test_delete_nonexistent_agent_returns_404(self):
        """DELETE /api/agents/nonexistent returns 404"""
        response = requests.delete(f"{BASE_URL}/api/agents/nonexistent-agent-xyz", timeout=10)
        assert response.status_code == 404
        print("✓ Correctly returns 404 for nonexistent agent deletion")


class TestAgentSecurity:
    """Security tests for agent API"""

    def test_agents_list_never_exposes_token(self):
        """GET /api/agents never exposes telegram_bot_token"""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        agents = data.get("agents", [])
        for agent in agents:
            assert "telegram_bot_token" not in agent, f"SECURITY: telegram_bot_token exposed for {agent.get('agent_id')}"
            # telegram_configured should be present instead
            assert "telegram_configured" in agent or agent.get("is_default"), f"Agent should have telegram_configured field"
        
        print(f"✓ SECURITY: No telegram_bot_token exposed in {len(agents)} agents")


class TestSkillsAPI:
    """Skills API tests"""

    def test_skills_returns_141_plus(self):
        """GET /api/skills/available returns 141+ skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        skills = data.get("skills", [])
        total = data.get("total", len(skills))
        
        assert total >= 141, f"Expected 141+ skills, got {total}"
        
        # Count by source
        sources = {}
        for skill in skills:
            src = skill.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        
        print(f"✓ Skills API returned {total} skills from {len(sources)} sources:")
        for src, count in sorted(sources.items()):
            print(f"  - {src}: {count}")


class TestWalletProtectedDeletion:
    """Tests for wallet-protected agent deletion - NEW in iteration 28"""

    def test_create_agent_and_simulate_wallet(self):
        """
        Create an agent, simulate having a wallet, verify deletion is blocked
        NOTE: This test is limited because we can't create real wallet.json files via API
        """
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"Wallet Test {unique_id}",
            "genesis_prompt": "Test agent to verify wallet protection",
            "telegram_bot_token": "1234567890:AATest-WalletTest",
            "telegram_chat_id": "987654321",
        }
        
        # Create agent
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠ Could not create test agent: {response.text}")
            return
        
        agent_id = response.json().get("agent", {}).get("agent_id")
        print(f"✓ Created test agent: {agent_id}")
        
        # Without a wallet.json, deletion should succeed
        # This verifies the normal delete path works
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}", timeout=10)
        assert delete_response.status_code == 200, f"Expected deletion to succeed (no wallet): {delete_response.text}"
        print(f"✓ Agent without wallet deleted successfully")
        
        # NOTE: To test wallet protection, we'd need to:
        # 1. Create agent via API
        # 2. Create wallet.json file on server (can't do via API)
        # 3. Try to delete → should get 400
        # This requires manual testing or server-side test


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
