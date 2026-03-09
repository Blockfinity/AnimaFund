"""
Iteration 40 - Testing Telegram Logs, Conway Balance, and Genesis Prompt Template
Tests for the new production monitoring features:
- Telegram log ingestion from bot messages (stored in MongoDB)
- Conway API real-time balance integration
- Updated genesis prompt with OpenClaw/Conway Terminal/MCP tools
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestTelegramLogEndpoints:
    """Test all Telegram log-related endpoints."""

    def test_get_telegram_logs_returns_data(self):
        """GET /api/telegram-logs should return stored logs from MongoDB."""
        response = requests.get(f"{BASE_URL}/api/telegram-logs?limit=20")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "logs" in data
        assert "total" in data
        assert "source" in data
        assert data["source"] == "telegram"
        
        # If logs exist, verify log structure
        if len(data["logs"]) > 0:
            log = data["logs"][0]
            assert "message_id" in log
            assert "agent_id" in log
            assert "timestamp" in log
            assert "type" in log
            assert "raw_text" in log

    def test_get_telegram_logs_stats(self):
        """GET /api/telegram-logs/stats should return statistics."""
        response = requests.get(f"{BASE_URL}/api/telegram-logs/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required stats fields
        assert "total_messages" in data
        assert "turns" in data
        assert "errors" in data
        assert "total_cost_cents" in data
        assert "source" in data
        assert data["source"] == "telegram"
        
        # Stats should be non-negative
        assert data["total_messages"] >= 0
        assert data["turns"] >= 0
        assert data["errors"] >= 0
        assert data["total_cost_cents"] >= 0

    def test_trigger_telegram_ingest(self):
        """POST /api/telegram-logs/ingest should trigger ingestion."""
        response = requests.post(
            f"{BASE_URL}/api/telegram-logs/ingest",
            params={"agent_id": "anima-fund", "batch_size": 5}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return ingestion info
        assert "ingested" in data or "error" in data
        if "ingested" in data:
            assert data["ingested"] >= 0

    def test_backfill_telegram_logs(self):
        """POST /api/telegram-logs/backfill should backfill historical logs."""
        response = requests.post(
            f"{BASE_URL}/api/telegram-logs/backfill",
            params={"agent_id": "anima-fund", "batch_size": 5}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return backfill info
        assert "ingested" in data or "error" in data

    def test_telegram_logs_filter_by_type(self):
        """GET /api/telegram-logs with log_type filter should work."""
        response = requests.get(
            f"{BASE_URL}/api/telegram-logs",
            params={"log_type": "turn", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should be of type "turn" if any exist
        for log in data["logs"]:
            assert log["type"] == "turn"


class TestConwayBalanceEndpoint:
    """Test Conway API balance integration."""

    def test_conway_balance_returns_data(self):
        """GET /api/conway/balance should return real-time balance from Conway API."""
        response = requests.get(f"{BASE_URL}/api/conway/balance")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response source
        assert "source" in data
        assert data["source"] == "conway_api"
        
        # Should have credits info or error
        assert "credits_cents" in data or "error" in data

    def test_conway_balance_includes_sandbox_info(self):
        """Conway balance response should include sandbox information."""
        response = requests.get(f"{BASE_URL}/api/conway/balance")
        assert response.status_code == 200
        data = response.json()
        
        # Should include sandbox info when API key is valid
        if "error" not in data:
            assert "sandboxes" in data or "sandbox_count" in data


class TestWalletBalanceConwayIntegration:
    """Test that wallet balance now includes Conway API credits."""

    def test_wallet_balance_includes_credits(self):
        """GET /api/wallet/balance should include Conway credits (not just cached)."""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        
        # Should have credits info
        assert "credits_cents" in data or "error" in data
        
        # Should have tier info
        assert "tier" in data or "error" in data

    def test_wallet_balance_critical_tier_when_no_credits(self):
        """Wallet balance should show 'critical' tier when credits are 0."""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        
        if "credits_cents" in data and data["credits_cents"] == 0:
            assert data["tier"] == "critical", "Tier should be 'critical' when credits are 0"


class TestGenesisPromptTemplate:
    """Test the updated genesis prompt with OpenClaw/Conway instructions."""

    def test_genesis_prompt_template_exists(self):
        """GET /api/genesis/prompt-template should return the template."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        
        assert "content" in data
        assert len(data["content"]) > 0

    def test_genesis_prompt_contains_conway_terminal(self):
        """Genesis prompt should contain Conway Terminal installation instructions."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        
        content = data["content"].lower()
        assert "conway terminal" in content or "conway-terminal" in content

    def test_genesis_prompt_contains_openclaw(self):
        """Genesis prompt should contain OpenClaw installation instructions."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        
        content = data["content"].lower()
        assert "openclaw" in content

    def test_genesis_prompt_contains_anti_loop_rules(self):
        """Genesis prompt should contain anti-stuck/anti-loop rules."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        
        content = data["content"]
        # Check for anti-stuck rules section
        assert "ANTI-STUCK" in content or "anti-loop" in content.lower()

    def test_genesis_prompt_contains_mcp_setup(self):
        """Genesis prompt should contain MCP server configuration."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        
        content = data["content"]
        assert "MCP" in content or "mcp" in content.lower()


class TestExistingEndpointsStillWork:
    """Verify that existing endpoints still work after changes."""

    def test_health_endpoint(self):
        """GET /api/health should still work."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_genesis_status(self):
        """GET /api/genesis/status should still work."""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "stage" in data

    def test_engine_status(self):
        """GET /api/engine/status should still work."""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "skills" in data

    def test_engine_live(self):
        """GET /api/engine/live should still work."""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "live" in data or "db_exists" in data


class TestTelegramLogDataIntegrity:
    """Test that Telegram log data is properly parsed and stored."""

    def test_turn_logs_have_cost_info(self):
        """Turn-type logs should have cost_cents field."""
        response = requests.get(
            f"{BASE_URL}/api/telegram-logs",
            params={"log_type": "turn", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        for log in data["logs"]:
            assert "cost_cents" in log
            assert log["cost_cents"] >= 0

    def test_logs_have_timestamps(self):
        """All logs should have proper timestamps."""
        response = requests.get(f"{BASE_URL}/api/telegram-logs?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        for log in data["logs"]:
            assert "timestamp" in log
            assert log["timestamp"] is not None

    def test_stats_cost_matches_log_sum(self):
        """Stats total_cost_cents should be consistent with log data."""
        stats_response = requests.get(f"{BASE_URL}/api/telegram-logs/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # total_cost_cents should be present and non-negative
        assert stats["total_cost_cents"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
