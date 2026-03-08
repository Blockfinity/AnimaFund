"""
Telegram Integration Tests for Anima Fund AI VC Platform
Tests the Telegram notification endpoints and core API functionality.

Features tested:
- Telegram status endpoint
- Telegram send endpoint (real message delivery)
- Health endpoint
- Genesis status endpoint
- Wallet balance endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestTelegramEndpoints:
    """Tests for Telegram notification API endpoints"""

    def test_telegram_status_configured(self):
        """GET /api/telegram/status returns configured: true with bot_token and chat_id set"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data
        
        # Verify Telegram is fully configured
        assert data["configured"] is True, "Telegram should be configured"
        assert data["bot_token_set"] is True, "Bot token should be set"
        assert data["chat_id_set"] is True, "Chat ID should be set"

    def test_telegram_send_success(self):
        """POST /api/telegram/send with valid text sends message and returns success"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/send",
            json={"text": "🧪 Pytest: Test message from test_telegram_integration.py"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True, "Telegram send should succeed"

    def test_telegram_send_with_html_formatting(self):
        """POST /api/telegram/send with HTML formatting works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/send",
            json={"text": "🧪 <b>Pytest:</b> Testing <code>HTML</code> <i>formatting</i>"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True

    def test_telegram_send_empty_text(self):
        """POST /api/telegram/send with empty text - should still work (Telegram handles it)"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/send",
            json={"text": ""},
            headers={"Content-Type": "application/json"}
        )
        # Note: This may fail at Telegram API level but shouldn't crash the server
        # Status could be 200 or 500 depending on Telegram's response
        assert response.status_code in [200, 500]

    def test_telegram_send_missing_text_field(self):
        """POST /api/telegram/send without text field should return 422 validation error"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/send",
            json={},
            headers={"Content-Type": "application/json"}
        )
        # Pydantic validation should catch missing required field
        assert response.status_code == 422


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_returns_ok(self):
        """GET /api/health returns status: ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_contains_required_fields(self):
        """GET /api/health contains all required fields"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["status", "engine_live", "engine_db_exists", "creator_wallet", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_health_creator_wallet_set(self):
        """GET /api/health returns the configured creator wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data["creator_wallet"] is not None
        assert len(data["creator_wallet"]) > 0


class TestGenesisStatus:
    """Tests for genesis status endpoint"""

    def test_genesis_status_returns_data(self):
        """GET /api/genesis/status returns status information"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        
        data = response.json()
        # Check required fields are present
        required_fields = [
            "wallet_address", "config_exists", "wallet_exists", 
            "engine_live", "engine_running", "stage", "status",
            "creator_wallet"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_genesis_status_creator_wallet(self):
        """GET /api/genesis/status returns correct creator wallet"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert data["creator_wallet"] == "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"

    def test_genesis_status_stage_valid(self):
        """GET /api/genesis/status returns a valid stage"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        valid_stages = ["not_created", "running", "provisioning", "configuring", "generating_wallet", "created"]
        assert data["stage"] in valid_stages, f"Invalid stage: {data['stage']}"


class TestWalletBalance:
    """Tests for wallet balance endpoint"""

    def test_wallet_balance_returns_data(self):
        """GET /api/wallet/balance returns balance data"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        
        data = response.json()
        # Should have balance fields (may be zero if no wallet)
        assert "usdc" in data or "error" in data
        assert "eth" in data or "error" in data

    def test_wallet_balance_numeric_values(self):
        """GET /api/wallet/balance returns numeric values for balances"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        
        if "usdc" in data:
            assert isinstance(data["usdc"], (int, float))
        if "eth" in data:
            assert isinstance(data["eth"], (int, float))


class TestTelegramSkillFile:
    """Tests for Telegram skill file existence"""

    def test_skill_file_exists(self):
        """Telegram skill file exists at expected path"""
        skill_path = "/app/automaton/skills/telegram-reporting/SKILL.md"
        assert os.path.exists(skill_path), f"Skill file not found at {skill_path}"

    def test_skill_file_content(self):
        """Telegram skill file contains required content"""
        skill_path = "/app/automaton/skills/telegram-reporting/SKILL.md"
        with open(skill_path, "r") as f:
            content = f.read()
        
        # Check for key content
        assert "telegram" in content.lower()
        assert "TELEGRAM_BOT_TOKEN" in content
        assert "TELEGRAM_CHAT_ID" in content
        assert "sendMessage" in content
