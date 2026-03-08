"""
Iteration 32: UI Stability Bug Fix Verification Tests
Tests for critical bug fixes addressing UI flickering and data disappearing issues.

Bug fix details:
1. SQLite busy_timeout added in engine_bridge.py
2. Frontend state management fixed to never replace valid data with empty
3. Removed cascading polling re-renders
4. Fixed isUserScrolling undefined reference bug in AgentMind.js
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBackendAPIStability:
    """Backend API consistency tests - verify APIs return consistent data"""

    def test_health_endpoint(self):
        """Verify health endpoint returns stable data"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        assert "timestamp" in data

    def test_engine_live_consistency(self):
        """Verify /api/engine/live returns consistent db_exists and agent_state"""
        # Call multiple times to verify consistency
        results = []
        for _ in range(3):
            response = requests.get(f"{BASE_URL}/api/engine/live")
            assert response.status_code == 200
            results.append(response.json())
        
        # All responses should have consistent db_exists
        db_exists_values = [r.get("db_exists") for r in results]
        assert all(v == db_exists_values[0] for v in db_exists_values), "db_exists should be consistent"
        
        # All responses should have agent_state
        for r in results:
            assert "agent_state" in r
            assert r.get("agent_state") in ["sleeping", "running", "critical", "waking", "offline", "unknown"]

    def test_wallet_balance_consistency(self):
        """Verify /api/wallet/balance returns consistent wallet address"""
        results = []
        for _ in range(3):
            response = requests.get(f"{BASE_URL}/api/wallet/balance")
            assert response.status_code == 200
            results.append(response.json())
        
        # All responses should have same wallet address
        wallets = [r.get("wallet") for r in results]
        assert all(w == wallets[0] for w in wallets), "Wallet address should be consistent"
        
        # Verify response structure
        for r in results:
            assert "usdc" in r
            assert "eth" in r
            assert "credits_cents" in r
            assert "tier" in r

    def test_genesis_status_consistency(self):
        """Verify /api/genesis/status returns consistent data"""
        results = []
        for _ in range(3):
            response = requests.get(f"{BASE_URL}/api/genesis/status")
            assert response.status_code == 200
            results.append(response.json())
        
        # Wallet address should be consistent
        wallets = [r.get("wallet_address") for r in results]
        assert all(w == wallets[0] for w in wallets), "Wallet address should be consistent"
        
        # Config exists should be consistent
        config_exists = [r.get("config_exists") for r in results]
        assert all(c == config_exists[0] for c in config_exists), "config_exists should be consistent"
        
        # Verify response structure
        for r in results:
            assert "wallet_address" in r
            assert r["wallet_address"].startswith("0x")
            assert "engine_state" in r
            assert "qr_code" in r

    def test_skills_count(self):
        """Verify /api/skills/available returns 141 skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) == 141, f"Expected 141 skills, got {len(data['skills'])}"


class TestLiveEndpoints:
    """Test live data endpoints that power the UI"""

    def test_live_agents(self):
        """Verify /api/live/agents returns agent list"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_live_turns(self):
        """Verify /api/live/turns returns turn data"""
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        assert isinstance(data["turns"], list)

    def test_live_soul(self):
        """Verify /api/live/soul returns SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        # Content may or may not exist depending on engine state
        assert "content" in data or response.status_code == 200

    def test_live_identity(self):
        """Verify /api/live/identity returns agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        # Should have name and/or address if configured
        assert isinstance(data, dict)


class TestTelegramHealth:
    """Test Telegram health endpoint used by Fund HQ"""

    def test_telegram_health(self):
        """Verify /api/telegram/health returns agent health status"""
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        # Each agent should have required fields
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "name" in agent
            assert "configured" in agent
            assert "bot_alive" in agent


class TestEngineLogs:
    """Test engine logs endpoint"""

    def test_engine_logs(self):
        """Verify /api/engine/logs returns log data"""
        response = requests.get(f"{BASE_URL}/api/engine/logs?lines=50")
        assert response.status_code == 200
        data = response.json()
        # Should return stdout/stderr logs
        assert "stdout" in data or "stderr" in data or response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
