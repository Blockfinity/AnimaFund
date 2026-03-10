"""
Iteration 8 Backend API Tests - PTY Sessions & Port URL Endpoints

Tests new features added in iteration 8:
- POST /api/provision/pty/create - Create PTY session
- POST /api/provision/pty/write - Write to PTY session
- GET /api/provision/pty/read - Read from PTY session
- POST /api/provision/pty/resize - Resize PTY session
- DELETE /api/provision/pty/{session_id} - Close PTY session
- GET /api/provision/pty/list - List PTY sessions
- GET /api/provision/port-url - Get public URL for a port

All PTY endpoints should return {"success": false, "error": "No sandbox"} when no sandbox provisioned.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


# ═══════════════════════════════════════════════════════════
# PTY CREATE ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyCreate:
    """Tests for POST /api/provision/pty/create endpoint"""
    
    def test_pty_create_no_sandbox_returns_error(self):
        """pty/create should return success=false when no sandbox provisioned"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/create",
            json={"command": "bash", "cols": 120, "rows": 40}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_create_default_params(self):
        """pty/create should accept request with default parameters"""
        response = requests.post(f"{BASE_URL}/api/provision/pty/create", json={})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox
        assert "error" in data
    
    def test_pty_create_custom_command(self):
        """pty/create should accept custom command parameter"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/create",
            json={"command": "python3", "cols": 80, "rows": 24}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox
        assert "sandbox" in data.get("error", "").lower()


# ═══════════════════════════════════════════════════════════
# PTY WRITE ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyWrite:
    """Tests for POST /api/provision/pty/write endpoint"""
    
    def test_pty_write_no_sandbox_returns_error(self):
        """pty/write should return success=false when no sandbox provisioned"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/write",
            json={"session_id": "test-session-123", "input": "ls -la\n"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_write_with_enter_key(self):
        """pty/write should accept input with newline character"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/write",
            json={"session_id": "fake-session", "input": "echo hello\n"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox
    
    def test_pty_write_with_ctrl_c(self):
        """pty/write should accept control characters like Ctrl+C (\\x03)"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/write",
            json={"session_id": "fake-session", "input": "\x03"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox


# ═══════════════════════════════════════════════════════════
# PTY READ ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyRead:
    """Tests for GET /api/provision/pty/read endpoint"""
    
    def test_pty_read_no_sandbox_returns_error(self):
        """pty/read should return success=false when no sandbox provisioned"""
        response = requests.get(f"{BASE_URL}/api/provision/pty/read?session_id=test-session-123")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_read_with_full_param(self):
        """pty/read should accept full=true parameter"""
        response = requests.get(f"{BASE_URL}/api/provision/pty/read?session_id=test-session&full=true")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox
    
    def test_pty_read_without_full_param(self):
        """pty/read should work without full parameter (defaults to false)"""
        response = requests.get(f"{BASE_URL}/api/provision/pty/read?session_id=test-session")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox


# ═══════════════════════════════════════════════════════════
# PTY RESIZE ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyResize:
    """Tests for POST /api/provision/pty/resize endpoint"""
    
    def test_pty_resize_no_sandbox_returns_error(self):
        """pty/resize should return success=false when no sandbox provisioned"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/resize",
            json={"session_id": "test-session-123", "cols": 160, "rows": 50}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_resize_various_sizes(self):
        """pty/resize should accept different terminal sizes"""
        response = requests.post(
            f"{BASE_URL}/api/provision/pty/resize",
            json={"session_id": "fake-session", "cols": 80, "rows": 24}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox


# ═══════════════════════════════════════════════════════════
# PTY CLOSE (DELETE) ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyClose:
    """Tests for DELETE /api/provision/pty/{session_id} endpoint"""
    
    def test_pty_close_no_sandbox_returns_error(self):
        """pty close (DELETE) should return success=false when no sandbox provisioned"""
        response = requests.delete(f"{BASE_URL}/api/provision/pty/test-session-123")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_close_with_different_session_ids(self):
        """pty close should handle various session ID formats"""
        response = requests.delete(f"{BASE_URL}/api/provision/pty/abc-123-def-456")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False  # No sandbox


# ═══════════════════════════════════════════════════════════
# PTY LIST ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPtyList:
    """Tests for GET /api/provision/pty/list endpoint"""
    
    def test_pty_list_no_sandbox_returns_error(self):
        """pty/list should return success=false when no sandbox provisioned"""
        response = requests.get(f"{BASE_URL}/api/provision/pty/list")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_pty_list_response_structure(self):
        """pty/list should have expected response structure (even with error)"""
        response = requests.get(f"{BASE_URL}/api/provision/pty/list")
        assert response.status_code == 200
        data = response.json()
        # When success, should have sessions and total
        # When fail, should have error
        assert "success" in data
        if data.get("success"):
            assert "sessions" in data
            assert "total" in data


# ═══════════════════════════════════════════════════════════
# PORT-URL ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestPortUrl:
    """Tests for GET /api/provision/port-url endpoint"""
    
    def test_port_url_no_sandbox_returns_error(self):
        """port-url should return success=false when no sandbox provisioned"""
        response = requests.get(f"{BASE_URL}/api/provision/port-url?port=3000")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        assert "sandbox" in data.get("error", "").lower(), f"Error should mention sandbox: {data}"
    
    def test_port_url_various_ports(self):
        """port-url should accept various port numbers"""
        for port in [80, 443, 3000, 8000, 8080, 9000]:
            response = requests.get(f"{BASE_URL}/api/provision/port-url?port={port}")
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") == False  # No sandbox
    
    def test_port_url_response_structure_with_error(self):
        """port-url should return expected fields even on error"""
        response = requests.get(f"{BASE_URL}/api/provision/port-url?port=5000")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "error" in data or "port" in data


# ═══════════════════════════════════════════════════════════
# EXISTING ENDPOINTS STILL WORK TESTS
# ═══════════════════════════════════════════════════════════

class TestExistingEndpointsStillWork:
    """Verify existing provision endpoints still work after adding PTY endpoints"""
    
    def test_status_endpoint_works(self):
        """GET /api/provision/status should still work"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox" in data
        assert "tools" in data
    
    def test_web_terminal_endpoint_works(self):
        """POST /api/provision/web-terminal should still work"""
        response = requests.post(f"{BASE_URL}/api/provision/web-terminal")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # Should fail without sandbox
        assert data.get("success") == False
    
    def test_create_sandbox_endpoint_works(self):
        """POST /api/provision/create-sandbox should still work"""
        response = requests.post(f"{BASE_URL}/api/provision/create-sandbox", json={})
        assert response.status_code == 200
        data = response.json()
        # Should fail with no credits/error but endpoint works
        assert "success" in data or "error" in data
    
    def test_list_sandboxes_endpoint_works(self):
        """GET /api/provision/list-sandboxes should still work"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data or "error" in data
    
    def test_nudge_endpoint_works(self):
        """POST /api/provision/nudge should still work"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_custom_nudge_endpoint_works(self):
        """POST /api/provision/nudge/custom should still work"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            json={"message": "TEST_ITERATION_8_NUDGE"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_credits_endpoint_works(self):
        """GET /api/provision/credits should still work"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
    
    def test_wallet_endpoint_works(self):
        """GET /api/provision/wallet should still work"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "wallet" in data
    
    def test_phase_state_endpoint_works(self):
        """GET /api/provision/phase-state should still work"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "phase_state" in data or "error" in data


# ═══════════════════════════════════════════════════════════
# ENDPOINT ROUTING TESTS
# ═══════════════════════════════════════════════════════════

class TestEndpointRouting:
    """Test that PTY endpoints are correctly routed"""
    
    def test_pty_endpoints_under_provision_prefix(self):
        """All PTY endpoints should be under /api/provision/pty/"""
        # Test each endpoint with valid body to avoid 422 validation errors
        endpoints = [
            ("POST", "/api/provision/pty/create", {"command": "bash"}),
            ("POST", "/api/provision/pty/write", {"session_id": "test", "input": "ls"}),
            ("GET", "/api/provision/pty/read?session_id=test", None),
            ("POST", "/api/provision/pty/resize", {"session_id": "test", "cols": 80, "rows": 24}),
            ("DELETE", "/api/provision/pty/test-session", None),
            ("GET", "/api/provision/pty/list", None),
        ]
        for method, endpoint, body in endpoints:
            if method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=body or {})
            elif method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}")
            
            # Should get 200 OK (not 404)
            assert response.status_code == 200, f"{method} {endpoint} returned {response.status_code}"
    
    def test_port_url_under_provision_prefix(self):
        """port-url endpoint should be under /api/provision/"""
        response = requests.get(f"{BASE_URL}/api/provision/port-url?port=3000")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
