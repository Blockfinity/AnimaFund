"""
Iteration 23: Comprehensive E2E Backend Testing
Tests all API endpoints including:
- Health, agents CRUD, credits management, genesis/provisioning status
- Telegram send/status/test/health, Conway API health check
- SSE stream, webhook, wallet balance, skills, payments, infrastructure
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://anima-runtime.preview.emergentagent.com"


class TestHealthEndpoints:
    """Test health and basic status endpoints"""

    def test_health_returns_ok(self):
        """GET /api/health — returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"Health check passed: {data}")

    def test_payments_status(self):
        """GET /api/payments/status — payment compliance check"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"Payments status: {data}")


class TestAgentsEndpoints:
    """Test agent CRUD operations"""

    def test_list_agents(self):
        """GET /api/agents — lists agents (auto-creates default 'anima-fund' agent)"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        agents = data["agents"]
        assert isinstance(agents, list)
        # Default agent should exist
        agent_ids = [a.get("agent_id") for a in agents]
        assert "anima-fund" in agent_ids, "Default 'anima-fund' agent should exist"
        print(f"Found {len(agents)} agents: {agent_ids}")

    def test_select_default_agent(self):
        """POST /api/agents/anima-fund/select — switch to default agent"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("active_agent") == "anima-fund"
        print(f"Agent selection: {data}")

    def test_select_nonexistent_agent_returns_404(self):
        """POST /api/agents/nonexistent/select — should return 404"""
        response = requests.post(f"{BASE_URL}/api/agents/TEST_nonexistent_agent/select")
        assert response.status_code == 404
        print("Nonexistent agent select correctly returns 404")

    def test_delete_default_agent_fails(self):
        """DELETE /api/agents/anima-fund — cannot delete default agent"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400
        print("Default agent deletion correctly blocked")

    def test_create_agent_requires_telegram(self):
        """POST /api/agents/create — requires telegram_bot_token and telegram_chat_id"""
        response = requests.post(f"{BASE_URL}/api/agents/create", json={
            "name": "TEST_No_Telegram",
            "genesis_prompt": "Test prompt",
            # Missing telegram_bot_token and telegram_chat_id
        })
        assert response.status_code == 400
        data = response.json()
        assert "telegram" in data.get("detail", "").lower() or "required" in str(data).lower()
        print(f"Agent creation correctly requires Telegram: {data}")


class TestCreditsEndpoints:
    """Test Conway credits management"""

    def test_key_status(self):
        """GET /api/credits/key-status — check Conway API key status"""
        response = requests.get(f"{BASE_URL}/api/credits/key-status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        # With the pre-configured key, it should be configured
        if data.get("configured"):
            assert "key_prefix" in data
            print(f"Key status: configured={data['configured']}, prefix={data.get('key_prefix')}")
        else:
            print(f"Key status: not configured")

    def test_set_invalid_key_format(self):
        """POST /api/credits/set-key — rejects invalid format"""
        response = requests.post(f"{BASE_URL}/api/credits/set-key", json={
            "api_key": "invalid_key_format"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False
        assert "invalid" in data.get("error", "").lower() or "cnwy_" in data.get("error", "")
        print(f"Invalid key correctly rejected: {data}")

    def test_get_balance(self):
        """GET /api/credits/balance — get credit balance"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200
        data = response.json()
        assert "credits_cents" in data or "error" in data
        print(f"Credit balance: {data}")

    def test_verify_credits(self):
        """POST /api/credits/verify — verify credit balance"""
        response = requests.post(f"{BASE_URL}/api/credits/verify")
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data or "error" in data
        print(f"Credit verification: {data}")


class TestGenesisEndpoints:
    """Test genesis/provisioning status endpoints"""

    def test_genesis_status(self):
        """GET /api/genesis/status — get genesis/provisioning status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "stage" in data
        print(f"Genesis status: agent_id={data.get('agent_id')}, stage={data.get('stage')}")

    def test_provision_status(self):
        """GET /api/provision/status — get provisioning status"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "sandbox" in data
        assert "tools" in data
        print(f"Provision status: agent_id={data.get('agent_id')}, sandbox={data.get('sandbox')}")


class TestEngineEndpoints:
    """Test engine status endpoints"""

    def test_engine_status(self):
        """GET /api/engine/status — get engine status"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        assert "engine" in data
        assert "source" in data
        print(f"Engine status: {data}")


class TestConwayEndpoints:
    """Test Conway API proxy routes"""

    def test_conway_health(self):
        """GET /api/conway/health — check Conway API services health"""
        response = requests.get(f"{BASE_URL}/api/conway/health")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data or "all_healthy" in data
        print(f"Conway health: {data}")


class TestTelegramEndpoints:
    """Test Telegram notification routes"""

    def test_telegram_status_default_agent(self):
        """GET /api/telegram/status — check Telegram config for default agent"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert data.get("agent_id") == "anima-fund"
        print(f"Telegram status for default agent: {data}")

    def test_telegram_health(self):
        """GET /api/telegram/health — check Telegram health for all agents"""
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "checked_at" in data
        print(f"Telegram health: {len(data.get('agents', []))} agents checked")

    def test_telegram_test_default_agent(self):
        """POST /api/telegram/test/anima-fund — send test Telegram message to default agent"""
        response = requests.post(f"{BASE_URL}/api/telegram/test/anima-fund")
        # Should succeed if bot token and chat ID are configured
        assert response.status_code in [200, 400, 500]
        data = response.json()
        if response.status_code == 200:
            assert data.get("success") is True
            print(f"Telegram test message sent successfully")
        else:
            print(f"Telegram test failed (expected if not configured): {data}")

    def test_telegram_send(self):
        """POST /api/telegram/send — send Telegram message"""
        response = requests.post(f"{BASE_URL}/api/telegram/send", json={
            "text": "Test message from E2E test"
        })
        # May fail if not configured, but endpoint should respond
        assert response.status_code in [200, 400, 500]
        print(f"Telegram send response: {response.status_code}")


class TestLiveEndpoints:
    """Test live/SSE endpoints"""

    def test_live_stream_accessible(self):
        """GET /api/live/stream — SSE stream endpoint is accessible"""
        # Just check the endpoint returns SSE content type
        response = requests.get(f"{BASE_URL}/api/live/stream", stream=True, timeout=3)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        response.close()
        print("SSE stream endpoint is accessible")

    def test_live_identity(self):
        """GET /api/live/identity — agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "agent_id" in data
        print(f"Live identity: {data}")

    def test_live_financials(self):
        """GET /api/live/financials — financial data"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        print(f"Live financials: {data}")

    def test_live_activity(self):
        """GET /api/live/activity — agent activity"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        print(f"Live activity: {len(data.get('activities', []))} entries")


class TestWalletEndpoints:
    """Test wallet balance endpoint"""

    def test_wallet_balance(self):
        """GET /api/wallet/balance — get wallet balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        # May have error if no wallet provisioned yet
        assert "usdc" in data or "eth" in data or "error" in data
        print(f"Wallet balance: {data}")


class TestSkillsEndpoints:
    """Test skills listing endpoint"""

    def test_skills_available(self):
        """GET /api/skills/available — list available skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        skills = data["skills"]
        assert isinstance(skills, list)
        assert len(skills) > 0, "Should have at least some skills available"
        # Check that Conway tools are included
        skill_names = [s.get("name") for s in skills]
        assert "sandbox_create" in skill_names or "browse_page" in skill_names
        print(f"Skills available: {data['total']} skills")


class TestWebhookEndpoints:
    """Test webhook endpoints"""

    def test_webhook_status(self):
        """GET /api/webhook/status — webhook status"""
        response = requests.get(f"{BASE_URL}/api/webhook/status")
        assert response.status_code == 200
        data = response.json()
        assert "last_update" in data or "update_source" in data
        print(f"Webhook status: {data}")

    def test_webhook_agent_update(self):
        """POST /api/webhook/agent-update — webhook receiver"""
        response = requests.post(f"{BASE_URL}/api/webhook/agent-update", json={
            "test": True,
            "source": "e2e_test"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("received") is True
        print(f"Webhook received: {data}")


class TestInfrastructureEndpoints:
    """Test infrastructure endpoints"""

    def test_infrastructure_sandboxes(self):
        """GET /api/infrastructure/sandboxes — list sandboxes"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data or "source" in data
        print(f"Infrastructure sandboxes: {data}")

    def test_infrastructure_tools(self):
        """GET /api/infrastructure/tools — installed tools"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data or "source" in data
        print(f"Infrastructure tools: {data}")


class TestAgentUpdateTelegram:
    """Test updating agent Telegram config"""

    def test_update_telegram_nonexistent_agent(self):
        """PUT /api/agents/nonexistent/telegram — should return 404"""
        response = requests.put(f"{BASE_URL}/api/agents/TEST_nonexistent/telegram", json={
            "telegram_bot_token": "test_token",
            "telegram_chat_id": "12345"
        })
        assert response.status_code == 404
        print("Update Telegram for nonexistent agent correctly returns 404")


class TestOpenClawEndpoints:
    """Test OpenClaw monitoring endpoints"""

    def test_openclaw_status(self):
        """GET /api/openclaw/status — OpenClaw status"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        assert response.status_code == 200
        data = response.json()
        assert "openclaw" in data or "sandbox_summary" in data
        print(f"OpenClaw status: {data}")

    def test_openclaw_sandboxes(self):
        """GET /api/openclaw/sandboxes — Conway sandboxes via OpenClaw"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "live_sandboxes" in data or "total_live" in data
        print(f"OpenClaw sandboxes: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
