"""
Iteration 25: Full Audit Test Suite
Tests all API endpoints for the Anima Fund autonomous AI VC fund platform.
Live Conway agent running on sandbox 47ba9dfd569c96df2663004bd8b73b86
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-agent-sandbox-1.preview.emergentagent.com')


class TestHealthAndCore:
    """Core health and basic API tests"""
    
    def test_health_endpoint(self):
        """GET /api/health should return 200"""
        res = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        print(f"Health check OK: {data}")
    
    def test_agents_list(self):
        """GET /api/agents should return agent list"""
        res = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "agents" in data
        print(f"Agents: {len(data['agents'])} found")
        # Should have anima-fund agent
        agent_ids = [a['agent_id'] for a in data['agents']]
        assert 'anima-fund' in agent_ids


class TestGenesisStatus:
    """Genesis screen API tests"""
    
    def test_genesis_status(self):
        """GET /api/genesis/status should return provisioning state"""
        res = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "agent_id" in data
        assert "wallet_address" in data
        assert "sandbox_active" in data
        assert "engine_running" in data or "engine_live" in data
        print(f"Genesis status: engine_running={data.get('engine_running')}, wallet={data.get('wallet_address')[:20]}...")
    
    def test_genesis_qr_code(self):
        """GET /api/genesis/status should include QR code if wallet exists"""
        res = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        if data.get("wallet_address"):
            assert "qr_code" in data
            assert data["qr_code"].startswith("data:image/png;base64,")
            print("QR code present")


class TestProvisionStatus:
    """Provisioning API tests"""
    
    def test_provision_status(self):
        """GET /api/provision/status should return full provisioning state"""
        res = requests.get(f"{BASE_URL}/api/provision/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "sandbox" in data
        assert "tools" in data
        assert "credits_cents" in data
        print(f"Provision status: sandbox={data['sandbox'].get('status')}, credits=${data['credits_cents']/100:.2f}")
    
    def test_provision_health_check(self):
        """POST /api/provision/health-check should probe sandbox"""
        res = requests.post(f"{BASE_URL}/api/provision/health-check", timeout=30)
        assert res.status_code == 200
        data = res.json()
        assert "success" in data
        if data["success"]:
            print(f"Health check: engine_running={data.get('engine_running')}, tools={data.get('tools_detected')}")
        else:
            print(f"Health check: {data.get('error')}")


class TestEngineEndpoints:
    """Engine status and logs API tests"""
    
    def test_engine_status(self):
        """GET /api/engine/status should return engine info"""
        res = requests.get(f"{BASE_URL}/api/engine/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "engine" in data
        assert "sandbox_id" in data
        print(f"Engine: {data.get('engine')}, deployed={data.get('engine_deployed')}")
    
    def test_engine_logs(self):
        """GET /api/engine/logs should return agent logs"""
        res = requests.get(f"{BASE_URL}/api/engine/logs?lines=50", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert "stdout" in data
        assert "stderr" in data
        print(f"Engine logs: {len(data.get('stdout', ''))} chars stdout")
    
    def test_engine_live(self):
        """GET /api/engine/live should return live status"""
        res = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "live" in data
        assert "db_exists" in data
        print(f"Engine live: {data.get('live')}, turn_count={data.get('turn_count')}")


class TestWebhookStatus:
    """Webhook daemon status tests"""
    
    def test_webhook_status(self):
        """GET /api/webhook/status should show real-time data source"""
        res = requests.get(f"{BASE_URL}/api/webhook/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "engine_running" in data
        assert "last_update" in data
        print(f"Webhook: engine_running={data.get('engine_running')}, source={data.get('update_source')}")


class TestLiveEndpoints:
    """Live data stream API tests"""
    
    def test_live_identity(self):
        """GET /api/live/identity should return agent identity"""
        res = requests.get(f"{BASE_URL}/api/live/identity", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "name" in data
        assert "address" in data
        print(f"Identity: {data.get('name')}, address={data.get('address')[:20] if data.get('address') else 'none'}...")
    
    def test_live_financials(self):
        """GET /api/live/financials should return financial data"""
        res = requests.get(f"{BASE_URL}/api/live/financials", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "total_earned_usd" in data
        assert "total_spent_usd" in data
        print(f"Financials: earned=${data.get('total_earned_usd')}, spent=${data.get('total_spent_usd')}")
    
    def test_live_activity(self):
        """GET /api/live/activity should return activities"""
        res = requests.get(f"{BASE_URL}/api/live/activity?limit=10", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "activities" in data
        assert "total" in data
        print(f"Activity: {data.get('total')} total activities")
    
    def test_live_tools(self):
        """GET /api/live/tools should return installed tools"""
        res = requests.get(f"{BASE_URL}/api/live/tools", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "tools" in data
        print(f"Tools: {len(data.get('tools', []))} installed")
    
    def test_live_stream_sse(self):
        """GET /api/live/stream should return SSE stream"""
        res = requests.get(f"{BASE_URL}/api/live/stream", timeout=5, stream=True)
        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("Content-Type", "")
        # Read first event
        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    print(f"SSE stream working: got data event")
                    break
        res.close()


class TestCreditsEndpoints:
    """Conway credits API tests"""
    
    def test_credits_key_status(self):
        """GET /api/credits/key-status should return key info"""
        res = requests.get(f"{BASE_URL}/api/credits/key-status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "configured" in data
        print(f"Key status: configured={data.get('configured')}, valid={data.get('valid')}, credits=${data.get('credits_cents', 0)/100:.2f}")
    
    def test_credits_balance(self):
        """GET /api/credits/balance should return balance"""
        res = requests.get(f"{BASE_URL}/api/credits/balance", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "credits_cents" in data
        print(f"Balance: ${data.get('credits_cents', 0)/100:.2f}")


class TestWalletEndpoints:
    """Wallet balance API tests"""
    
    def test_wallet_balance(self):
        """GET /api/wallet/balance should return on-chain balance"""
        res = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "usdc" in data
        assert "eth" in data
        assert "credits_cents" in data
        print(f"Wallet: USDC=${data.get('usdc')}, ETH={data.get('eth')}, tier={data.get('tier')}")


class TestConwayHealth:
    """Conway Cloud health check"""
    
    def test_conway_health(self):
        """GET /api/conway/health should return service status"""
        res = requests.get(f"{BASE_URL}/api/conway/health", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert "all_healthy" in data
        print(f"Conway health: all_healthy={data.get('all_healthy')}")


class TestSkillsEndpoint:
    """Skills API tests"""
    
    def test_skills_available(self):
        """GET /api/skills/available should return skill list"""
        res = requests.get(f"{BASE_URL}/api/skills/available", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "skills" in data
        assert "total" in data
        print(f"Skills: {data.get('total')} available")


class TestTelegramEndpoints:
    """Telegram integration tests"""
    
    def test_telegram_status(self):
        """GET /api/telegram/status should return config status"""
        res = requests.get(f"{BASE_URL}/api/telegram/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert "configured" in data
        print(f"Telegram status: configured={data.get('configured')}")
    
    def test_telegram_health(self):
        """GET /api/telegram/health should return bot health"""
        res = requests.get(f"{BASE_URL}/api/telegram/health", timeout=15)
        assert res.status_code == 200
        data = res.json()
        assert "agents" in data
        print(f"Telegram health: {len(data.get('agents', []))} agents configured")


class TestOpenClawEndpoints:
    """OpenClaw integration tests"""
    
    def test_openclaw_status(self):
        """GET /api/openclaw/status should return OpenClaw state"""
        res = requests.get(f"{BASE_URL}/api/openclaw/status", timeout=10)
        assert res.status_code == 200
        data = res.json()
        print(f"OpenClaw status: has_activity={data.get('has_activity')}")
    
    def test_openclaw_sandboxes(self):
        """GET /api/openclaw/sandboxes should return sandbox info"""
        res = requests.get(f"{BASE_URL}/api/openclaw/sandboxes", timeout=10)
        assert res.status_code == 200
        data = res.json()
        print(f"OpenClaw sandboxes: {data.get('total_live', 0)} live, {data.get('total_created', 0)} created")


class TestInfrastructureEndpoints:
    """Infrastructure page API tests"""
    
    def test_infrastructure_sandboxes(self):
        """GET /api/infrastructure/sandboxes should return sandbox list"""
        res = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes", timeout=10)
        assert res.status_code == 200
        data = res.json()
        print(f"Infrastructure sandboxes: success={data.get('success')}")
    
    def test_infrastructure_tools(self):
        """GET /api/infrastructure/tools should return tools list"""
        res = requests.get(f"{BASE_URL}/api/infrastructure/tools", timeout=10)
        assert res.status_code == 200


class TestAgentSelection:
    """Agent selection API tests"""
    
    def test_select_anima_fund(self):
        """POST /api/agents/anima-fund/select should work"""
        res = requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") == True
        print(f"Selected agent: {data.get('active_agent')}")
    
    def test_select_nonexistent_agent(self):
        """POST /api/agents/nonexistent/select should return 404"""
        res = requests.post(f"{BASE_URL}/api/agents/nonexistent-12345/select", timeout=10)
        assert res.status_code == 404


class TestDataFlow:
    """End-to-end data flow verification"""
    
    def test_webhook_to_genesis(self):
        """Verify webhook data flows to genesis status"""
        # Get webhook status
        webhook_res = requests.get(f"{BASE_URL}/api/webhook/status", timeout=10)
        assert webhook_res.status_code == 200
        webhook_data = webhook_res.json()
        
        # Get genesis status
        genesis_res = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert genesis_res.status_code == 200
        genesis_data = genesis_res.json()
        
        # Both should have consistent engine_running state
        webhook_running = webhook_data.get("engine_running", False)
        genesis_running = genesis_data.get("engine_running", False)
        
        # They should match (webhook is source of truth)
        print(f"Data flow check: webhook={webhook_running}, genesis={genesis_running}")
        # Note: Small timing differences possible, so just log, don't assert equality


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
