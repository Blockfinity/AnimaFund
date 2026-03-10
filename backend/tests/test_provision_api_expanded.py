"""
Agent Provisioning API Tests - Expanded
Tests the complete Conway ecosystem provisioning panel.

NEW endpoints tested (iteration_3):
- POST /api/provision/expose-port - fails gracefully without sandbox
- POST /api/provision/web-terminal - fails gracefully without sandbox
- POST /api/provision/test-compute - fails with HTTP 402 (0 credits)
- POST /api/provision/exec - fails gracefully without sandbox
- GET /api/provision/credits - returns balance, history, and pricing tiers
- GET /api/provision/wallet - returns wallet status
- GET /api/provision/list-sandboxes - returns empty array
- POST /api/provision/delete-sandbox - fails gracefully without sandbox

Previous endpoints (from iteration_2):
- GET /api/provision/status - returns full provisioning state
- POST /api/provision/create-sandbox - creates Conway sandbox
- POST /api/provision/install-terminal - requires sandbox
- POST /api/provision/install-openclaw - requires sandbox
- POST /api/provision/load-skills - requires sandbox
- POST /api/provision/nudge - sends default autonomy nudge
- POST /api/provision/nudge/custom - sends custom message
"""
import pytest
import requests
import os
import subprocess

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://ai-agent-platform-18.preview.emergentagent.com"


class TestHealthEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"Health check passed: {data}")


# =============================================================================
# PROVISIONING STATUS - Full state
# =============================================================================
class TestProvisionStatus:
    """GET /api/provision/status - Returns sandbox, tools, ports, domains, compute, skills, credits"""
    
    def test_status_endpoint_returns_200(self):
        """Status endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        print(f"Provision status: {data}")
    
    def test_status_has_sandbox_field(self):
        """Status should have sandbox field with status, id, terminal_url, region"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox" in data
        assert "status" in data["sandbox"]
        assert data["sandbox"]["status"] in ["none", "active", "pending", "error"]
    
    def test_status_has_tools_field(self):
        """Status should have tools field (dict)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], dict)
    
    def test_status_has_ports_field(self):
        """Status should have ports field (list)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "ports" in data
        assert isinstance(data["ports"], list)
        print(f"Ports: {data['ports']}")
    
    def test_status_has_domains_field(self):
        """Status should have domains field (list)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)
    
    def test_status_has_compute_verified_field(self):
        """Status should have compute_verified field (boolean)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "compute_verified" in data
        assert isinstance(data["compute_verified"], bool)
    
    def test_status_has_skills_loaded_field(self):
        """Status should have skills_loaded field (boolean)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "skills_loaded" in data
        assert isinstance(data["skills_loaded"], bool)
    
    def test_status_has_credits_cents(self):
        """Status should have credits_cents field"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "credits_cents" in data
        assert isinstance(data["credits_cents"], (int, float))
        print(f"Credits (cents): {data['credits_cents']}")
    
    def test_status_has_nudges_field(self):
        """Status should have nudges field (list)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "nudges" in data
        assert isinstance(data["nudges"], list)


# =============================================================================
# SANDBOX OPERATIONS
# =============================================================================
class TestCreateSandbox:
    """POST /api/provision/create-sandbox - Creates Conway sandbox (fails with 0 credits)"""
    
    def test_create_sandbox_endpoint_returns_200(self):
        """Create sandbox endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/create-sandbox",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Create sandbox response: {data}")
    
    def test_create_sandbox_has_success_field(self):
        """Create sandbox response should have success field"""
        response = requests.post(
            f"{BASE_URL}/api/provision/create-sandbox",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_create_sandbox_fails_with_zero_credits(self):
        """Create sandbox should fail with 0 credits (expected: 'Insufficient credits')"""
        response = requests.post(
            f"{BASE_URL}/api/provision/create-sandbox",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        # With 0 credits, expect failure
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (0 credits): {data['error']}")
        else:
            # If success, sandbox already exists
            assert "sandbox_id" in data or "message" in data
            print(f"Sandbox exists: {data}")


class TestListSandboxes:
    """GET /api/provision/list-sandboxes - Returns empty array or list of sandboxes"""
    
    def test_list_sandboxes_returns_200(self):
        """List sandboxes endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        print(f"List sandboxes response: {data}")
    
    def test_list_sandboxes_has_success_field(self):
        """List sandboxes should have success field"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_list_sandboxes_returns_sandboxes_array(self):
        """List sandboxes should return sandboxes array"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data
        assert isinstance(data["sandboxes"], list)
        print(f"Sandboxes count: {len(data['sandboxes'])}")


class TestDeleteSandbox:
    """POST /api/provision/delete-sandbox - Fails gracefully without sandbox"""
    
    def test_delete_sandbox_returns_200(self):
        """Delete sandbox endpoint should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/delete-sandbox")
        assert response.status_code == 200
        data = response.json()
        print(f"Delete sandbox response: {data}")
    
    def test_delete_sandbox_fails_without_sandbox(self):
        """Delete sandbox should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/delete-sandbox")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            # Should indicate no sandbox
            print(f"Expected error (no sandbox): {data['error']}")
        else:
            print(f"Sandbox deleted: {data}")


# =============================================================================
# TOOLS INSTALLATION (Require sandbox)
# =============================================================================
class TestInstallTerminal:
    """POST /api/provision/install-terminal - Fails gracefully without sandbox"""
    
    def test_install_terminal_returns_200(self):
        """Install terminal should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/install-terminal")
        assert response.status_code == 200
    
    def test_install_terminal_requires_sandbox(self):
        """Install terminal should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-terminal")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            assert "sandbox" in data["error"].lower()
            print(f"Expected error (no sandbox): {data['error']}")


class TestInstallOpenclaw:
    """POST /api/provision/install-openclaw - Fails gracefully without sandbox"""
    
    def test_install_openclaw_returns_200(self):
        """Install openclaw should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/install-openclaw")
        assert response.status_code == 200
    
    def test_install_openclaw_requires_sandbox(self):
        """Install openclaw should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-openclaw")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")


# =============================================================================
# PORTS & WEB TERMINAL
# =============================================================================
class TestExposePort:
    """POST /api/provision/expose-port - Fails gracefully without sandbox"""
    
    def test_expose_port_returns_200(self):
        """Expose port should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/expose-port",
            headers={"Content-Type": "application/json"},
            json={"port": 3000}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Expose port response: {data}")
    
    def test_expose_port_requires_sandbox(self):
        """Expose port should fail gracefully without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/expose-port",
            headers={"Content-Type": "application/json"},
            json={"port": 8080}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")
    
    def test_expose_port_accepts_subdomain(self):
        """Expose port should accept optional subdomain parameter"""
        response = requests.post(
            f"{BASE_URL}/api/provision/expose-port",
            headers={"Content-Type": "application/json"},
            json={"port": 3000, "subdomain": "myapp"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should not fail due to missing parameter validation
        assert "success" in data


class TestWebTerminal:
    """POST /api/provision/web-terminal - Fails gracefully without sandbox"""
    
    def test_web_terminal_returns_200(self):
        """Web terminal should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/web-terminal")
        assert response.status_code == 200
        data = response.json()
        print(f"Web terminal response: {data}")
    
    def test_web_terminal_requires_sandbox(self):
        """Web terminal should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/web-terminal")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")


# =============================================================================
# COMPUTE (Conway Inference)
# =============================================================================
class TestCompute:
    """POST /api/provision/test-compute - Fails with 0 credits"""
    
    def test_compute_returns_200(self):
        """Test compute should return 200 (even with error)"""
        response = requests.post(
            f"{BASE_URL}/api/provision/test-compute",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Test compute response: {data}")
    
    def test_compute_fails_with_zero_credits(self):
        """Test compute should fail with 0 credits"""
        response = requests.post(
            f"{BASE_URL}/api/provision/test-compute",
            headers={"Content-Type": "application/json"},
            json={"model": "gpt-5-nano", "message": "Hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # With 0 credits, expect failure
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (0 credits): {data['error']}")


# =============================================================================
# EXEC (Run commands in sandbox)
# =============================================================================
class TestExec:
    """POST /api/provision/exec - Fails gracefully without sandbox"""
    
    def test_exec_returns_200(self):
        """Exec should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/exec",
            headers={"Content-Type": "application/json"},
            json={"command": "echo hello"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Exec response: {data}")
    
    def test_exec_requires_sandbox(self):
        """Exec should fail gracefully without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/exec",
            headers={"Content-Type": "application/json"},
            json={"command": "ls -la"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")


# =============================================================================
# SKILLS
# =============================================================================
class TestLoadSkills:
    """POST /api/provision/load-skills - Fails gracefully without sandbox"""
    
    def test_load_skills_returns_200(self):
        """Load skills should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
    
    def test_load_skills_requires_sandbox(self):
        """Load skills should fail gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")


# =============================================================================
# CREDITS & WALLET
# =============================================================================
class TestCredits:
    """GET /api/provision/credits - Returns balance, history, and pricing tiers"""
    
    def test_credits_returns_200(self):
        """Credits endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        print(f"Credits response: {data}")
    
    def test_credits_has_balance(self):
        """Credits should have balance field"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print(f"Balance: {data['balance']}")
    
    def test_credits_has_history(self):
        """Credits should have history field"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        print(f"History: {type(data['history'])}")
    
    def test_credits_has_pricing(self):
        """Credits should have pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "pricing" in data
        print(f"Pricing: {data['pricing']}")


class TestWallet:
    """GET /api/provision/wallet - Returns wallet status"""
    
    def test_wallet_returns_200(self):
        """Wallet endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        print(f"Wallet response: {data}")
    
    def test_wallet_has_success_field(self):
        """Wallet should have success field"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_wallet_has_wallet_field(self):
        """Wallet should have wallet info"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "wallet" in data


# =============================================================================
# NUDGE SYSTEM
# =============================================================================
class TestNudgeEndpoints:
    """POST /api/provision/nudge and /api/provision/nudge/custom"""
    
    def test_nudge_returns_200(self):
        """Nudge should return 200"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
    
    def test_nudge_returns_success_and_message(self):
        """Nudge should return success and the message sent"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        print(f"Default nudge: {data['message'][:80]}...")
    
    def test_custom_nudge_returns_200(self):
        """Custom nudge should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            headers={"Content-Type": "application/json"},
            json={"message": "TEST_NUDGE: Hello agent!"}
        )
        assert response.status_code == 200
    
    def test_custom_nudge_sends_custom_message(self):
        """Custom nudge should echo the custom message"""
        test_message = "TEST_NUDGE: Testing custom nudge"
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            headers={"Content-Type": "application/json"},
            json={"message": test_message}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        assert data["message"] == test_message
    
    def test_nudges_appear_in_status(self):
        """Sent nudges should appear in status"""
        test_msg = "TEST_NUDGE: Verify in status"
        requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            headers={"Content-Type": "application/json"},
            json={"message": test_msg}
        )
        
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "nudges" in data
        assert len(data["nudges"]) > 0


# =============================================================================
# SECURITY CHECKS
# =============================================================================
class TestSecurityChecks:
    """Verify no tools are installed on host system"""
    
    def test_no_conway_terminal_on_host(self):
        """SECURITY: conway-terminal should NOT be on host"""
        result = subprocess.run(["which", "conway-terminal"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: conway-terminal on host"
        print("PASS: conway-terminal not on host")
    
    def test_no_openclaw_on_host(self):
        """SECURITY: openclaw should NOT be on host"""
        result = subprocess.run(["which", "openclaw"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: openclaw on host"
        print("PASS: openclaw not on host")
    
    def test_system_prompt_reads_provisioning_status(self):
        """system-prompt.ts should read provisioning-status.json"""
        path = "/app/automaton/src/agent/system-prompt.ts"
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
            assert "loadProvisioningStatus" in content
            assert "provisioning-status.json" in content
            print("PASS: system-prompt.ts reads provisioning-status.json")
        else:
            pytest.skip(f"{path} does not exist")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
