"""
Iteration 19: Post-Audit Refactor Testing
Tests the refactored components after SSE audit:
1. Backend: /api/health, /api/credits/balance, /api/credits/verify, /api/credits/history
2. Backend: /api/provision/status, /api/live/stream (SSE), /api/payments/status
3. Verify SSE stream returns valid JSON data
4. Verify credits endpoints return expected fields
"""
import pytest
import requests
import json
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_ok(self):
        """GET /api/health returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        print(f"PASS: /api/health returns status=ok")


class TestCreditsEndpoints:
    """Credits router: /balance, /verify, /history"""
    
    def test_credits_balance_returns_credits_cents(self):
        """GET /api/credits/balance returns credits_cents field"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200
        data = response.json()
        assert "credits_cents" in data
        assert "credits_usd" in data
        # With 0 credits API key, expect 0 or error
        print(f"PASS: /api/credits/balance returns credits_cents={data['credits_cents']}")
    
    def test_credits_verify_returns_verified_and_message(self):
        """POST /api/credits/verify returns verified true and message"""
        response = requests.post(f"{BASE_URL}/api/credits/verify")
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        assert "message" in data
        # Should be verified=True (balance check succeeds) or False if error
        print(f"PASS: /api/credits/verify returns verified={data['verified']}, message={data['message']}")
    
    def test_credits_history_returns_arrays(self):
        """GET /api/credits/history returns purchases and verifications arrays"""
        response = requests.get(f"{BASE_URL}/api/credits/history")
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        assert "verifications" in data
        assert isinstance(data["purchases"], list)
        assert isinstance(data["verifications"], list)
        print(f"PASS: /api/credits/history returns purchases ({len(data['purchases'])} items) and verifications ({len(data['verifications'])} items)")


class TestProvisionStatus:
    """Provision status endpoint"""
    
    def test_provision_status_returns_sandbox_and_credits(self):
        """GET /api/provision/status returns sandbox and credits info"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        # Should have sandbox key (may be null if not provisioned)
        assert "sandbox" in data or "credits_cents" in data
        print(f"PASS: /api/provision/status returns sandbox info")


class TestSSEEndpoint:
    """SSE stream endpoint tests"""
    
    def test_live_stream_accessible_returns_data(self):
        """GET /api/live/stream SSE endpoint returns valid JSON data"""
        # Use streaming request with timeout
        response = requests.get(
            f"{BASE_URL}/api/live/stream",
            stream=True,
            timeout=10,
            headers={"Accept": "text/event-stream"}
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        
        # Read first few events
        events_received = 0
        data_valid = False
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    payload = json.loads(line[6:])
                    # Verify expected fields in SSE payload
                    assert "engine" in payload or "timestamp" in payload or "sandbox_id" in payload
                    data_valid = True
                    events_received += 1
                    print(f"SSE event received: {list(payload.keys())[:5]}...")
                    if events_received >= 1:
                        break
                except json.JSONDecodeError:
                    # Heartbeat or empty line
                    continue
            if events_received >= 1:
                break
        
        response.close()
        assert data_valid, "No valid JSON data received from SSE stream"
        print(f"PASS: /api/live/stream returns valid SSE data")


class TestPaymentsStatus:
    """Payments status endpoint"""
    
    def test_payments_status_returns_status_field(self):
        """GET /api/payments/status returns status field"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"PASS: /api/payments/status returns status={data['status']}")


class TestLiveEndpoints:
    """Additional live endpoint tests for completeness"""
    
    def test_live_identity(self):
        """GET /api/live/identity returns agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "agent_id" in data
        print(f"PASS: /api/live/identity returns identity")
    
    def test_live_financials(self):
        """GET /api/live/financials returns financial data"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        print(f"PASS: /api/live/financials returns data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
