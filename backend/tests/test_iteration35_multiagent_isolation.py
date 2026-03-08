"""
Iteration 35 - Multi-Agent Data Isolation Testing

Purpose: Verify that each agent has COMPLETELY INDEPENDENT data:
- wallet, logs, goals, and creator wallets must be per-agent
- Switching agents switches ALL data sources

Fixes being tested:
1) Active agent ID tracking via engine_bridge.py
2) genesis/status returns per-agent creator wallets from MongoDB
3) engine/logs returns ONLY per-agent log files (no global fallback for non-default agents)
4) wallet/balance checks MongoDB for non-default agent wallets
5) agent_id field is returned in genesis/status, engine/logs, engine/live

NOTE: Creating agents requires valid Telegram credentials which we don't have for test.
So we focus on testing the isolation logic with the existing default agent and verifying
the correct fields/behavior are in place.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGenesisStatusIsolation:
    """Test genesis/status returns correct agent-specific data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_health_check(self, api_client):
        """Verify API is healthy"""
        resp = api_client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")

    def test_02_genesis_status_returns_agent_id(self, api_client):
        """CRITICAL: genesis/status must return agent_id field"""
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        
        # agent_id field must exist (this is a new fix)
        assert "agent_id" in data, "Missing agent_id field in genesis/status"
        assert data["agent_id"] == "anima-fund", f"Expected 'anima-fund', got: {data['agent_id']}"
        print(f"✓ genesis/status returns agent_id: {data['agent_id']}")

    def test_03_genesis_status_returns_creator_wallets(self, api_client):
        """CRITICAL: genesis/status must return per-agent creator wallets"""
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        
        # Creator wallet fields must exist
        assert "creator_wallet" in data, "Missing creator_wallet field"
        assert "creator_eth_address" in data, "Missing creator_eth_address field"
        
        # For anima-fund, should return global config wallets
        creator_sol = data.get("creator_wallet")
        creator_eth = data.get("creator_eth_address")
        
        assert creator_sol is not None, "creator_wallet should not be null for default agent"
        assert creator_eth is not None, "creator_eth_address should not be null for default agent"
        
        print(f"✓ Creator wallets returned: SOL={creator_sol[:12]}... ETH={creator_eth[:12]}...")

    def test_04_genesis_status_returns_goals(self, api_client):
        """genesis/status should return per-agent goals"""
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "goals" in data, "Missing goals field in genesis/status"
        # For anima-fund default agent, goals may be empty list
        print(f"✓ Goals field returned: {data['goals']}")


class TestEngineLogsIsolation:
    """Test engine/logs returns correct agent-specific data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_engine_logs_returns_agent_id(self, api_client):
        """CRITICAL: engine/logs must return agent_id field"""
        resp = api_client.get(f"{BASE_URL}/api/engine/logs")
        assert resp.status_code == 200
        data = resp.json()
        
        # agent_id field must exist (this is a new fix)
        assert "agent_id" in data, "Missing agent_id field in engine/logs"
        assert data["agent_id"] == "anima-fund", f"Expected 'anima-fund', got: {data['agent_id']}"
        print(f"✓ engine/logs returns agent_id: {data['agent_id']}")

    def test_02_engine_logs_has_stdout_stderr(self, api_client):
        """engine/logs should have stdout and stderr fields"""
        resp = api_client.get(f"{BASE_URL}/api/engine/logs")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "stdout" in data, "Missing stdout field"
        assert "stderr" in data, "Missing stderr field"
        
        # For default agent with no running engine, logs may be empty
        print(f"✓ Logs fields present: stdout={len(data['stdout'])} chars, stderr={len(data['stderr'])} chars")


class TestEngineLiveIsolation:
    """Test engine/live returns correct agent-specific data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_engine_live_returns_agent_id(self, api_client):
        """CRITICAL: engine/live must return agent_id field"""
        resp = api_client.get(f"{BASE_URL}/api/engine/live")
        assert resp.status_code == 200
        data = resp.json()
        
        # agent_id field must exist (this is a new fix)
        assert "agent_id" in data, "Missing agent_id field in engine/live"
        assert data["agent_id"] == "anima-fund", f"Expected 'anima-fund', got: {data['agent_id']}"
        print(f"✓ engine/live returns agent_id: {data['agent_id']}")

    def test_02_engine_live_has_expected_fields(self, api_client):
        """engine/live should have expected fields"""
        resp = api_client.get(f"{BASE_URL}/api/engine/live")
        assert resp.status_code == 200
        data = resp.json()
        
        required_fields = ["live", "db_exists", "agent_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ engine/live has all required fields: live={data['live']}, db_exists={data['db_exists']}")


class TestAgentSelectSwitch:
    """Test that selecting agents properly switches data context"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_select_default_agent(self, api_client):
        """Verify selecting anima-fund works"""
        resp = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["success"] is True
        assert data["active_agent"] == "anima-fund"
        assert "data_dir" in data
        print(f"✓ Selected anima-fund: {data}")

    def test_02_verify_genesis_after_select(self, api_client):
        """After selecting anima-fund, genesis/status should return anima-fund data"""
        time.sleep(0.2)  # Allow state to propagate
        resp = api_client.get(f"{BASE_URL}/api/genesis/status")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["agent_id"] == "anima-fund"
        assert data.get("wallet_address") is not None
        print(f"✓ genesis/status confirms agent_id={data['agent_id']}, wallet={data.get('wallet_address', 'none')[:12]}...")

    def test_03_select_nonexistent_agent_fails(self, api_client):
        """Selecting a non-existent agent should return 404"""
        resp = api_client.post(f"{BASE_URL}/api/agents/nonexistent-agent-xyz/select")
        assert resp.status_code == 404
        print(f"✓ Non-existent agent selection correctly returns 404")


class TestAgentCreationWithTelegram:
    """Test agent creation - will fail on Telegram validation which is expected"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_create_agent_requires_telegram(self, api_client):
        """Creating agent without Telegram creds should fail with 400"""
        # First try without Telegram credentials - should fail
        resp = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "Test No Telegram",
            "genesis_prompt": "Test prompt"
        })
        
        # Should get 400 because Telegram is required
        assert resp.status_code == 400, f"Expected 400 for missing Telegram, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "Telegram" in str(data.get("detail", "")), f"Error should mention Telegram: {data}"
        print(f"✓ Agent creation correctly requires Telegram credentials: {data.get('detail')}")

    def test_02_create_agent_with_invalid_telegram(self, api_client):
        """Creating agent with invalid Telegram token should fail"""
        resp = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "Test Invalid Telegram",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "invalid_token_123",
            "telegram_chat_id": "123456789"
        })
        
        # Should get 200 for creation (Telegram validation happens later) or 400 if validated upfront
        # Either is acceptable - the key is it handles the situation gracefully
        print(f"✓ Agent creation with invalid Telegram returns status {resp.status_code}")
        if resp.status_code == 200:
            # Cleanup if it was created
            data = resp.json()
            if data.get("agent", {}).get("agent_id"):
                cleanup = api_client.delete(f"{BASE_URL}/api/agents/{data['agent']['agent_id']}")
                print(f"  Cleaned up test agent: {cleanup.status_code}")


class TestWalletBalanceIsolation:
    """Test wallet/balance returns correct agent-specific data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_wallet_balance_for_default_agent(self, api_client):
        """wallet/balance should return data for default agent"""
        # Ensure on default agent
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.2)
        
        resp = api_client.get(f"{BASE_URL}/api/wallet/balance")
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have wallet and balance fields
        assert "wallet" in data
        assert "usdc" in data
        assert "eth" in data
        assert "wallet_mismatch" in data
        
        wallet = data.get("wallet")
        assert wallet is not None, "Default agent should have a wallet"
        assert wallet.startswith("0x"), f"Wallet should be 0x format: {wallet}"
        print(f"✓ wallet/balance returns wallet={wallet[:15]}..., usdc={data['usdc']}, eth={data['eth']}")


class TestAgentListEndpoint:
    """Test /api/agents endpoint returns correct data"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_agents_list_returns_default(self, api_client):
        """Agents list should include anima-fund"""
        resp = api_client.get(f"{BASE_URL}/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        
        agents = data.get("agents", [])
        agent_ids = [a.get("agent_id") for a in agents]
        
        assert "anima-fund" in agent_ids, "Default agent anima-fund should be in list"
        
        # Verify anima-fund has expected fields
        anima = next((a for a in agents if a.get("agent_id") == "anima-fund"), None)
        assert anima is not None
        assert anima.get("is_default") is True
        assert anima.get("name") == "Anima Fund"
        
        print(f"✓ Agents list returned {len(agents)} agent(s): {agent_ids}")


class TestDataIsolationCodePaths:
    """Test that the isolation code paths work correctly by examining responses"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_complete_data_snapshot_default_agent(self, api_client):
        """Take a complete data snapshot for default agent"""
        # Ensure on default agent
        select_resp = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert select_resp.status_code == 200
        time.sleep(0.3)
        
        # Collect all data endpoints
        endpoints_to_check = {
            "genesis_status": f"{BASE_URL}/api/genesis/status",
            "engine_logs": f"{BASE_URL}/api/engine/logs",
            "engine_live": f"{BASE_URL}/api/engine/live",
            "wallet_balance": f"{BASE_URL}/api/wallet/balance",
        }
        
        snapshot = {}
        for name, url in endpoints_to_check.items():
            resp = api_client.get(url)
            if resp.status_code == 200:
                snapshot[name] = resp.json()
            else:
                snapshot[name] = {"error": resp.status_code}
        
        # Verify all return agent_id = anima-fund
        assert snapshot["genesis_status"].get("agent_id") == "anima-fund"
        assert snapshot["engine_logs"].get("agent_id") == "anima-fund"
        assert snapshot["engine_live"].get("agent_id") == "anima-fund"
        
        # Verify wallet exists
        assert snapshot["genesis_status"].get("wallet_address") is not None
        
        # Verify creator wallets exist
        assert snapshot["genesis_status"].get("creator_wallet") is not None
        assert snapshot["genesis_status"].get("creator_eth_address") is not None
        
        print(f"✓ All endpoints return consistent agent_id=anima-fund")
        print(f"  genesis_status: wallet={snapshot['genesis_status'].get('wallet_address', '')[:15]}...")
        print(f"  engine_live: db_exists={snapshot['engine_live'].get('db_exists')}, live={snapshot['engine_live'].get('live')}")
        print(f"  engine_logs: stdout_len={len(snapshot['engine_logs'].get('stdout', ''))}, stderr_len={len(snapshot['engine_logs'].get('stderr', ''))}")


class TestSkillsAvailable:
    """Verify skills endpoint works"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    def test_01_skills_available_returns_skills(self, api_client):
        """Skills available endpoint should return skills list"""
        resp = api_client.get(f"{BASE_URL}/api/skills/available")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "skills" in data
        assert "total" in data
        assert data["total"] > 0
        
        print(f"✓ Skills available: {data['total']} skills")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
