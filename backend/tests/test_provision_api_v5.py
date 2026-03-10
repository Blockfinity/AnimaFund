"""
Iteration 5 Backend API Tests for Anima Fund Agent Provisioning
Tests new features:
- install-claude-code endpoint (fails gracefully without sandbox)
- wallet_address field in status endpoint
- install-terminal with auto-wallet creation
- install-openclaw reads sandbox's own API key
- deploy-agent pushes engine + genesis + phase-state into sandbox
- phase-state and agent-logs endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStatusEndpoint:
    """Test GET /api/provision/status endpoint"""
    
    def test_status_returns_wallet_address_field(self):
        """Status should include wallet_address field (new in iteration 5)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        # wallet_address should be a field (even if empty)
        assert "wallet_address" in data, "wallet_address field missing from status"
        assert isinstance(data.get("wallet_address"), str), "wallet_address should be a string"
    
    def test_status_returns_expected_fields(self):
        """Status should return all expected fields"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        expected_fields = ["sandbox", "tools", "ports", "domains", "compute_verified", 
                         "skills_loaded", "nudges", "credits_cents", "wallet_address", "last_updated"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_status_sandbox_structure(self):
        """Sandbox field should have expected structure"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        sandbox = data.get("sandbox", {})
        assert "status" in sandbox
        assert "id" in sandbox


class TestInstallClaudeCode:
    """Test POST /api/provision/install-claude-code endpoint (new in iteration 5)"""
    
    def test_install_claude_code_no_sandbox(self):
        """install-claude-code should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-claude-code")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "sandbox" in data.get("error", "").lower() or "No sandbox" in data.get("error", "")
    
    def test_install_claude_code_error_message(self):
        """install-claude-code error should mention creating sandbox first"""
        response = requests.post(f"{BASE_URL}/api/provision/install-claude-code")
        assert response.status_code == 200
        data = response.json()
        # Should mention needing a sandbox
        error_msg = data.get("error", "")
        assert "sandbox" in error_msg.lower() or "create" in error_msg.lower()


class TestInstallTerminal:
    """Test POST /api/provision/install-terminal endpoint"""
    
    def test_install_terminal_no_sandbox(self):
        """install-terminal should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-terminal")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "sandbox" in data.get("error", "").lower()
    
    def test_install_terminal_error_message_mentions_sandbox(self):
        """install-terminal error should mention sandbox requirement"""
        response = requests.post(f"{BASE_URL}/api/provision/install-terminal")
        data = response.json()
        error_msg = data.get("error", "")
        assert "sandbox" in error_msg.lower()


class TestInstallOpenClaw:
    """Test POST /api/provision/install-openclaw endpoint"""
    
    def test_install_openclaw_no_sandbox(self):
        """install-openclaw should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-openclaw")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "sandbox" in data.get("error", "").lower()


class TestDeployAgent:
    """Test POST /api/provision/deploy-agent endpoint"""
    
    def test_deploy_agent_no_sandbox(self):
        """deploy-agent should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/deploy-agent")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "sandbox" in data.get("error", "").lower()
    
    def test_deploy_agent_error_message(self):
        """deploy-agent error should mention creating sandbox first"""
        response = requests.post(f"{BASE_URL}/api/provision/deploy-agent")
        data = response.json()
        error_msg = data.get("error", "")
        assert "sandbox" in error_msg.lower() or "create" in error_msg.lower()


class TestPhaseState:
    """Test GET /api/provision/phase-state endpoint"""
    
    def test_phase_state_returns_data(self):
        """phase-state endpoint should return some phase state"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200
        data = response.json()
        # May succeed with local file or fail without sandbox
        assert "success" in data or "phase_state" in data or "error" in data
    
    def test_phase_state_structure(self):
        """phase-state should return expected structure when successful"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        data = response.json()
        # If successful, should have phase_state and source fields
        if data.get("success"):
            assert "phase_state" in data
            assert "source" in data


class TestAgentLogs:
    """Test GET /api/provision/agent-logs endpoint"""
    
    def test_agent_logs_no_sandbox(self):
        """agent-logs should fail gracefully without sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/agent-logs")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False or "error" in data.get("error", "").lower() or "sandbox" in str(data).lower()


class TestCreateSandbox:
    """Test POST /api/provision/create-sandbox endpoint"""
    
    def test_create_sandbox_fails_with_zero_credits(self):
        """create-sandbox should fail when account has zero credits"""
        response = requests.post(f"{BASE_URL}/api/provision/create-sandbox")
        assert response.status_code == 200
        data = response.json()
        # With 0 credits, sandbox creation should fail
        # May return "Insufficient credits" or similar error
        assert data.get("success") == False or "error" in data


class TestNudge:
    """Test nudge endpoints"""
    
    def test_nudge_sends_message(self):
        """POST /api/provision/nudge should send autonomy message"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_custom_nudge_sends_message(self):
        """POST /api/provision/nudge/custom should send custom message"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            json={"message": "TEST_V5_CUSTOM_NUDGE"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
    
    def test_custom_nudge_appears_in_status(self):
        """Custom nudge should appear in status nudges"""
        # First send a unique nudge
        unique_msg = "TEST_V5_VERIFY_NUDGE"
        requests.post(f"{BASE_URL}/api/provision/nudge/custom", json={"message": unique_msg})
        
        # Then check status
        response = requests.get(f"{BASE_URL}/api/provision/status")
        data = response.json()
        nudges = data.get("nudges", [])
        messages = [n.get("message", "") for n in nudges]
        assert unique_msg in messages, f"Nudge not found in status. Nudges: {messages}"


class TestOtherEndpoints:
    """Test other provision endpoints"""
    
    def test_sandbox_info_no_sandbox(self):
        """sandbox-info should fail gracefully without sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/sandbox-info")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_list_sandboxes(self):
        """list-sandboxes should return sandbox list or error"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        # Should either return sandboxes list or an error
        assert "sandboxes" in data or "error" in data or "success" in data
    
    def test_verify_sandbox_no_sandbox(self):
        """verify-sandbox should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/verify-sandbox")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False or "error" in data
    
    def test_load_skills_no_sandbox(self):
        """load-skills should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_test_compute(self):
        """test-compute may fail with no credits or succeed"""
        response = requests.post(f"{BASE_URL}/api/provision/test-compute")
        assert response.status_code == 200
        data = response.json()
        # Either succeeds or fails with error - just needs to not crash
        assert "success" in data or "error" in data
    
    def test_web_terminal_no_sandbox(self):
        """web-terminal should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/web-terminal")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_expose_port_no_sandbox(self):
        """expose-port should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/expose-port", json={"port": 3000})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_credits(self):
        """credits endpoint should return balance info"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
    
    def test_wallet(self):
        """wallet endpoint should return wallet info"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "wallet" in data


class TestExecEndpoints:
    """Test exec endpoints require sandbox"""
    
    def test_exec_no_sandbox(self):
        """exec should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/exec", json={"command": "echo test"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_run_code_no_sandbox(self):
        """run-code should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/run-code", json={"code": "print('test')"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False


class TestFileEndpoints:
    """Test file endpoints require sandbox"""
    
    def test_upload_file_no_sandbox(self):
        """upload-file should fail without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/upload-file", json={"path": "/tmp/test.txt", "content": "test"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_read_file_no_sandbox(self):
        """read-file should fail without sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/read-file?path=/tmp/test.txt")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
    
    def test_list_files_no_sandbox(self):
        """list-files should fail without sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/list-files?path=/root")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False


class TestDomainEndpoints:
    """Test domain endpoints"""
    
    def test_domain_list(self):
        """domain-list should return list or error"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-list")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "domains" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
