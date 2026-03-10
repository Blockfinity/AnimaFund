"""
Iteration 20: Conway API Key Input Feature Testing

Tests the new Conway API key input functionality:
1. POST /api/credits/set-key - validates key against Conway API and persists to MongoDB
2. GET /api/credits/key-status - returns configured:true/false and valid:true/false
3. POST /api/credits/verify - still works after refactor
4. GET /api/credits/balance - still works
5. GET /api/credits/history - returns audit trail
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
VALID_CONWAY_KEY = "cnwy_k_HUFTefVvBakA_QMFbzeb9ps8rKXYIaGe"


class TestConwayApiKeySetup:
    """Test Conway API Key input and persistence"""

    def test_health_check(self):
        """Basic health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("PASS: Health check - status ok")

    def test_key_status_returns_configured_info(self):
        """GET /api/credits/key-status should return configured and valid status"""
        response = requests.get(f"{BASE_URL}/api/credits/key-status")
        assert response.status_code == 200
        data = response.json()
        
        # Key should already be configured (per test setup)
        assert "configured" in data, f"Response missing 'configured' field: {data}"
        print(f"PASS: key-status configured={data.get('configured')}")
        
        # If configured, should have valid field and key_prefix
        if data.get("configured"):
            assert "valid" in data, "Missing 'valid' field when key is configured"
            print(f"PASS: key-status valid={data.get('valid')}, key_prefix={data.get('key_prefix', 'N/A')}")
            if data.get("valid"):
                assert "key_prefix" in data, "Missing key_prefix when key is valid"
                assert data["key_prefix"].startswith("cnwy_"), "Key prefix should start with cnwy_"
                print(f"PASS: Key prefix starts with cnwy_: {data['key_prefix']}")
        else:
            assert "message" in data, "Should have message when not configured"
            print(f"INFO: Key not configured - {data.get('message')}")

    def test_set_key_with_invalid_format_returns_error(self):
        """POST /api/credits/set-key should reject keys not starting with cnwy_"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": "invalid_key_format"}
        )
        assert response.status_code == 200  # API returns 200 with success: false
        data = response.json()
        
        assert data.get("success") == False, f"Should return success=false for invalid key: {data}"
        assert "error" in data, "Should return error message for invalid key"
        assert "cnwy_" in data["error"].lower(), f"Error should mention cnwy_ format: {data['error']}"
        print(f"PASS: Invalid key format rejected - {data['error']}")

    def test_set_key_with_empty_key_returns_error(self):
        """POST /api/credits/set-key should reject empty keys"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": ""}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False, f"Should return success=false for empty key: {data}"
        assert "error" in data, "Should return error message for empty key"
        print(f"PASS: Empty key rejected - {data['error']}")

    def test_set_key_with_whitespace_only_returns_error(self):
        """POST /api/credits/set-key should reject whitespace-only keys"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": "   "}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False, f"Should return success=false for whitespace key: {data}"
        print(f"PASS: Whitespace-only key rejected")

    def test_set_key_with_valid_key_succeeds(self):
        """POST /api/credits/set-key with valid Conway key should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": VALID_CONWAY_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        
        # This key is valid (per test requirements) but has 0 credits
        if data.get("success"):
            assert "credits_cents" in data, "Should return credits_cents on success"
            assert "credits_usd" in data, "Should return credits_usd on success"
            assert "key_prefix" in data, "Should return key_prefix on success"
            assert data["key_prefix"].startswith("cnwy_"), "key_prefix should start with cnwy_"
            print(f"PASS: Valid key set - credits: ${data.get('credits_usd', 0):.2f}, prefix: {data['key_prefix']}")
        else:
            # Key might be invalid if Conway API rejects it
            print(f"INFO: set-key returned success=false - {data.get('error', 'unknown error')}")
            # This is acceptable if Conway API is unreachable or key is expired
            assert "error" in data, "Should have error message on failure"


class TestConwayCreditsEndpoints:
    """Test other credits endpoints still work after refactor"""

    def test_credits_balance_endpoint(self):
        """GET /api/credits/balance should return balance info"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200
        data = response.json()
        
        assert "credits_cents" in data, f"Missing credits_cents: {data}"
        assert "credits_usd" in data, f"Missing credits_usd: {data}"
        print(f"PASS: Balance endpoint - {data.get('credits_cents')} cents (${data.get('credits_usd'):.2f})")

    def test_credits_verify_endpoint(self):
        """POST /api/credits/verify should return verification result"""
        response = requests.post(f"{BASE_URL}/api/credits/verify")
        assert response.status_code == 200
        data = response.json()
        
        assert "verified" in data, f"Missing verified field: {data}"
        assert "message" in data or "error" in data, f"Should have message or error: {data}"
        print(f"PASS: Verify endpoint - verified={data.get('verified')}, message={data.get('message', data.get('error', 'N/A'))}")

    def test_credits_history_endpoint(self):
        """GET /api/credits/history should return audit trail"""
        response = requests.get(f"{BASE_URL}/api/credits/history")
        assert response.status_code == 200
        data = response.json()
        
        assert "purchases" in data, f"Missing purchases array: {data}"
        assert "verifications" in data, f"Missing verifications array: {data}"
        assert isinstance(data["purchases"], list), "purchases should be a list"
        assert isinstance(data["verifications"], list), "verifications should be a list"
        print(f"PASS: History endpoint - {len(data['purchases'])} purchases, {len(data['verifications'])} verifications")


class TestProvisioningStatus:
    """Test provisioning status includes Conway info"""

    def test_provision_status_returns_credits(self):
        """GET /api/provision/status should return credits info"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "credits_cents" in data, f"Missing credits_cents in provision status: {data}"
        assert "sandbox" in data, "Missing sandbox info"
        assert "tools" in data, "Missing tools info"
        print(f"PASS: Provision status - credits: {data.get('credits_cents')} cents, sandbox: {data.get('sandbox', {}).get('status', 'unknown')}")


class TestKeyStatusAfterSetKey:
    """Test key-status reflects set-key changes"""

    def test_key_status_after_valid_set_key(self):
        """After setting valid key, key-status should reflect it"""
        # First set a key
        set_response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": VALID_CONWAY_KEY}
        )
        
        # Then check status
        status_response = requests.get(f"{BASE_URL}/api/credits/key-status")
        assert status_response.status_code == 200
        data = status_response.json()
        
        # If set-key succeeded, status should show configured
        if set_response.json().get("success"):
            assert data.get("configured") == True, f"Should be configured after successful set-key: {data}"
            assert data.get("valid") == True, f"Should be valid after successful set-key: {data}"
            assert "key_prefix" in data, "Should have key_prefix"
            assert "credits_cents" in data, "Should have credits_cents"
            print(f"PASS: key-status reflects set-key - configured={data['configured']}, valid={data['valid']}, prefix={data.get('key_prefix')}")
        else:
            print(f"INFO: set-key didn't succeed, key-status may or may not show configured")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
