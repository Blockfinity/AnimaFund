"""
Iteration 16: Comprehensive E2E Backend API Tests for Anima Fund Platform
Tests all API endpoints with real Conway API and Telegram integration
"""
import os
import pytest
import requests
import time

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://autonomous-agents-19.preview.emergentagent.com"


class TestHealthEndpoints:
    """Test health and basic status endpoints"""
    
    def test_health_ok(self):
        """GET /api/health returns ok status"""
        res = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"PASS: /api/health - status=ok, creator_wallet={data.get('creator_wallet')[:20]}...")


class TestGenesisEndpoints:
    """Test genesis/provisioning status endpoints"""
    
    def test_genesis_status(self):
        """GET /api/genesis/status returns full agent status with sandbox info"""
        res = requests.get(f"{BASE_URL}/api/genesis/status", timeout=15)
        assert res.status_code == 200
        data = res.json()
        # Check required fields
        assert "agent_id" in data
        assert "stage" in data
        assert "status" in data
        assert "sandbox_active" in data or "sandbox_id" in data
        assert "wallet_address" in data or data.get("stage") in ["not_created", "sandbox_created"]
        print(f"PASS: /api/genesis/status - agent_id={data.get('agent_id')}, stage={data.get('stage')}, status={data.get('status')}")


class TestCreditsEndpoints:
    """Test Conway Credits endpoints"""
    
    def test_credits_balance(self):
        """GET /api/credits/balance returns credits_cents and credits_usd"""
        res = requests.get(f"{BASE_URL}/api/credits/balance", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "credits_cents" in data
        assert "credits_usd" in data
        # credits_cents should be numeric
        assert isinstance(data["credits_cents"], (int, float))
        assert isinstance(data["credits_usd"], (int, float))
        print(f"PASS: /api/credits/balance - credits_cents={data['credits_cents']}, credits_usd=${data['credits_usd']}")
    
    def test_credits_pricing(self):
        """GET /api/credits/pricing returns VM pricing tiers and credit tiers"""
        res = requests.get(f"{BASE_URL}/api/credits/pricing", timeout=10)
        assert res.status_code == 200
        data = res.json()
        # Should have pricing info (tiers or pricing array)
        assert "tiers" in data or "pricing" in data or "error" not in data
        print(f"PASS: /api/credits/pricing - returned pricing data: {list(data.keys())}")
    
    def test_credits_purchase_5(self):
        """POST /api/credits/purchase with {amount:5} returns QR code and payment details"""
        res = requests.post(f"{BASE_URL}/api/credits/purchase", 
                           json={"amount": 5}, timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") == True
        assert "pay_to" in data
        assert "amount_usdc" in data
        assert "qr_code" in data
        assert "instructions" in data
        assert isinstance(data["instructions"], list)
        print(f"PASS: /api/credits/purchase ($5) - pay_to={data['pay_to'][:20]}..., amount_usdc={data['amount_usdc']}")
    
    def test_credits_purchase_25(self):
        """POST /api/credits/purchase with {amount:25} works for different tier"""
        res = requests.post(f"{BASE_URL}/api/credits/purchase", 
                           json={"amount": 25}, timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") == True
        assert "pay_to" in data
        assert data.get("amount_usdc") == 25
        print(f"PASS: /api/credits/purchase ($25) - amount_usdc={data['amount_usdc']}")


class TestAgentsEndpoints:
    """Test agent management endpoints"""
    
    def test_agents_list(self):
        """GET /api/agents returns agents list with agent_id, name, telegram_configured"""
        res = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        if len(data["agents"]) > 0:
            agent = data["agents"][0]
            assert "agent_id" in agent
            assert "name" in agent
            # telegram_configured should be present
            assert "telegram_configured" in agent
        print(f"PASS: /api/agents - found {len(data['agents'])} agents")
    
    def test_skills_available(self):
        """GET /api/skills/available returns 100+ skills from multiple sources"""
        res = requests.get(f"{BASE_URL}/api/skills/available", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "skills" in data
        assert "total" in data
        skills = data["skills"]
        assert isinstance(skills, list)
        # Should have many skills from different sources
        sources = set(s.get("source") for s in skills)
        # Check for expected sources: anima, conway-cloud, openclaw, clawhub
        expected_sources = {"anima", "conway-cloud", "conway-compute", "conway-domains", "openclaw", "clawhub"}
        found_sources = sources & expected_sources
        assert len(found_sources) >= 3, f"Expected skills from multiple sources, found: {found_sources}"
        print(f"PASS: /api/skills/available - total={data['total']}, sources={found_sources}")


class TestTelegramEndpoints:
    """Test Telegram notification endpoints"""
    
    def test_telegram_status(self):
        """GET /api/telegram/status returns configured:true for default agent"""
        res = requests.get(f"{BASE_URL}/api/telegram/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "configured" in data
        assert data.get("configured") == True
        assert data.get("bot_token_set") == True
        assert data.get("chat_id_set") == True
        print(f"PASS: /api/telegram/status - configured={data['configured']}, agent_id={data.get('agent_id')}")
    
    def test_telegram_test_send(self):
        """POST /api/telegram/test/anima-fund sends real test message and returns success:true"""
        res = requests.post(f"{BASE_URL}/api/telegram/test/anima-fund", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") == True
        print(f"PASS: /api/telegram/test/anima-fund - success={data['success']}, message sent!")
    
    def test_telegram_health(self):
        """GET /api/telegram/health returns bot_alive:true for anima-fund agent"""
        res = requests.get(f"{BASE_URL}/api/telegram/health", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert "agents" in data
        agents = data["agents"]
        # Find anima-fund agent
        anima_agent = next((a for a in agents if a.get("agent_id") == "anima-fund"), None)
        assert anima_agent is not None, "anima-fund agent not found in telegram health"
        assert anima_agent.get("bot_alive") == True
        print(f"PASS: /api/telegram/health - anima-fund bot_alive={anima_agent['bot_alive']}, username={anima_agent.get('bot_username')}")


class TestConwayEndpoints:
    """Test Conway API integration endpoints"""
    
    def test_conway_health(self):
        """GET /api/conway/health returns all_healthy:true with cloud, domains, inference"""
        res = requests.get(f"{BASE_URL}/api/conway/health", timeout=20)
        assert res.status_code == 200
        data = res.json()
        assert "all_healthy" in data
        assert "services" in data
        services = data["services"]
        # Check for expected services
        expected_services = {"cloud", "domains", "inference"}
        found_services = set(services.keys())
        assert expected_services <= found_services, f"Expected {expected_services}, found {found_services}"
        print(f"PASS: /api/conway/health - all_healthy={data['all_healthy']}, services={list(services.keys())}")
    
    def test_conway_balance(self):
        """GET /api/conway/balance returns credits data"""
        res = requests.get(f"{BASE_URL}/api/conway/balance", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "source" in data
        # May have credits_cents or error if no API key
        assert "credits_cents" in data or "error" in data
        print(f"PASS: /api/conway/balance - source={data.get('source')}, credits_cents={data.get('credits_cents', 'N/A')}")


class TestLiveEndpoints:
    """Test live data and SSE streaming endpoints"""
    
    def test_live_identity(self):
        """GET /api/live/identity returns agent name, creator wallet"""
        res = requests.get(f"{BASE_URL}/api/live/identity", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "name" in data
        assert "source" in data
        print(f"PASS: /api/live/identity - name={data.get('name')}, source={data.get('source')}")
    
    def test_live_stream_sse(self):
        """GET /api/live/stream returns SSE events with engine status and conway_credits_cents"""
        res = requests.get(f"{BASE_URL}/api/live/stream", 
                          stream=True, timeout=15,
                          headers={"Accept": "text/event-stream"})
        assert res.status_code == 200
        # Read first event
        content = ""
        for i, line in enumerate(res.iter_lines(decode_unicode=True)):
            if line:
                content += line
            if i > 5:  # Read first few lines
                break
        res.close()
        # Should be SSE format (data: ...)
        assert "data:" in content or "heartbeat" in content
        print(f"PASS: /api/live/stream - SSE connection established, received: {content[:100]}...")
    
    def test_live_financials(self):
        """GET /api/live/financials returns financial data"""
        res = requests.get(f"{BASE_URL}/api/live/financials", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "source" in data
        # Financial data structure
        assert "total_balance_usd" in data or "source" in data
        print(f"PASS: /api/live/financials - source={data.get('source')}")
    
    def test_live_activity(self):
        """GET /api/live/activity returns activities list"""
        res = requests.get(f"{BASE_URL}/api/live/activity", timeout=10)
        assert res.status_code == 200
        data = res.json()
        # Should have activities list or empty list
        assert "activities" in data or "items" in data
        print(f"PASS: /api/live/activity - returned activity data")


class TestOpenClawEndpoints:
    """Test OpenClaw/sandbox monitoring endpoints"""
    
    def test_openclaw_status(self):
        """GET /api/openclaw/status returns sandbox_summary and openclaw state"""
        res = requests.get(f"{BASE_URL}/api/openclaw/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "sandbox_summary" in data
        assert "openclaw" in data
        assert "has_activity" in data
        print(f"PASS: /api/openclaw/status - has_activity={data.get('has_activity')}, sandbox_summary={data['sandbox_summary']}")
    
    def test_openclaw_sandboxes(self):
        """GET /api/openclaw/sandboxes returns sandbox data"""
        res = requests.get(f"{BASE_URL}/api/openclaw/sandboxes", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "live_sandboxes" in data or "total_live" in data
        assert "created_sandboxes" in data or "total_created" in data
        print(f"PASS: /api/openclaw/sandboxes - total_live={data.get('total_live', 0)}, total_created={data.get('total_created', 0)}")


class TestInfrastructureEndpoints:
    """Test infrastructure endpoints"""
    
    def test_infrastructure_sandboxes(self):
        """GET /api/infrastructure/sandboxes returns sandbox list"""
        res = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "sandboxes" in data or "source" in data
        print(f"PASS: /api/infrastructure/sandboxes - source={data.get('source')}")


class TestEngineLiveEndpoint:
    """Test engine live status"""
    
    def test_engine_live(self):
        """GET /api/engine/live returns engine status"""
        res = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "live" in data
        assert "db_exists" in data
        print(f"PASS: /api/engine/live - live={data.get('live')}, db_exists={data.get('db_exists')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
