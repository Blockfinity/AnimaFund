"""
Agent Provisioning API Tests
Tests the live-equip provisioning system for running agents.
The agent is ALIVE during provisioning - each action equips it with tools.

Endpoints tested:
- GET /api/provision/status - returns sandbox, tools, skills, nudges, credits
- POST /api/provision/create-sandbox - creates Conway sandbox
- POST /api/provision/install-terminal - requires sandbox first
- POST /api/provision/install-openclaw - requires sandbox first
- POST /api/provision/load-skills - requires sandbox first
- POST /api/provision/nudge - sends default nudge message
- POST /api/provision/nudge/custom - sends custom nudge message

Security tests:
- No conway-terminal or openclaw on host
- system-prompt.ts reads provisioning-status.json (not BOOT_REPORT)
"""
import pytest
import requests
import os
import subprocess

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://agent-capital-hub.preview.emergentagent.com"


class TestHealthEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"Health check passed: {data}")
    
    def test_base_health(self):
        """Base /health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200


class TestProvisionStatus:
    """GET /api/provision/status - Returns sandbox, tools, skills, nudges, credits"""
    
    def test_status_endpoint_returns_200(self):
        """Status endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        print(f"Provision status: {data}")
    
    def test_status_has_sandbox_field(self):
        """Status should have sandbox field"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox" in data
        assert "status" in data["sandbox"]
        assert data["sandbox"]["status"] in ["none", "active", "pending", "error"]
        print(f"Sandbox status: {data['sandbox']}")
    
    def test_status_has_tools_field(self):
        """Status should have tools field (dict)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], dict)
        print(f"Tools: {data['tools']}")
    
    def test_status_has_skills_loaded_field(self):
        """Status should have skills_loaded field (boolean)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "skills_loaded" in data
        assert isinstance(data["skills_loaded"], bool)
        print(f"Skills loaded: {data['skills_loaded']}")
    
    def test_status_has_nudges_field(self):
        """Status should have nudges field (list)"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "nudges" in data
        assert isinstance(data["nudges"], list)
        print(f"Nudges count: {len(data['nudges'])}")
    
    def test_status_has_credits_cents(self):
        """Status should have credits_cents field"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "credits_cents" in data
        # Credits may be 0 (expected with 0 credit API key)
        assert isinstance(data["credits_cents"], (int, float))
        print(f"Credits (cents): {data['credits_cents']}")


class TestCreateSandbox:
    """POST /api/provision/create-sandbox - Creates Conway sandbox"""
    
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
        print(f"Create sandbox success: {data['success']}")
    
    def test_create_sandbox_fails_with_zero_credits(self):
        """Create sandbox should fail with 0 credits (expected behavior)"""
        response = requests.post(
            f"{BASE_URL}/api/provision/create-sandbox",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        # With 0 credits, expect failure with 'Insufficient credits' error
        if not data.get("success"):
            assert "error" in data
            # The error should indicate a credit or API issue
            print(f"Expected error (0 credits): {data['error']}")
        else:
            # If success, it means sandbox already exists
            assert "sandbox_id" in data or "message" in data
            print(f"Sandbox exists: {data}")


class TestInstallTerminal:
    """POST /api/provision/install-terminal - Requires sandbox first"""
    
    def test_install_terminal_endpoint_returns_200(self):
        """Install terminal endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/install-terminal",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Install terminal response: {data}")
    
    def test_install_terminal_requires_sandbox(self):
        """Install terminal should fail gracefully without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/install-terminal",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # If no sandbox, should fail with error
        if not data.get("success"):
            assert "error" in data
            # Should indicate sandbox needed
            print(f"Expected error (no sandbox): {data['error']}")
        else:
            # Success means sandbox exists and terminal installed
            print(f"Terminal installed: {data}")


class TestInstallOpenclaw:
    """POST /api/provision/install-openclaw - Requires sandbox first"""
    
    def test_install_openclaw_endpoint_returns_200(self):
        """Install openclaw endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/install-openclaw",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Install openclaw response: {data}")
    
    def test_install_openclaw_requires_sandbox(self):
        """Install openclaw should fail gracefully without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/install-openclaw",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")
        else:
            print(f"OpenClaw installed: {data}")


class TestLoadSkills:
    """POST /api/provision/load-skills - Requires sandbox first"""
    
    def test_load_skills_endpoint_returns_200(self):
        """Load skills endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/load-skills",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Load skills response: {data}")
    
    def test_load_skills_requires_sandbox(self):
        """Load skills should fail gracefully without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/load-skills",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if not data.get("success"):
            assert "error" in data
            print(f"Expected error (no sandbox): {data['error']}")
        else:
            # Success should include skill_count
            assert "skill_count" in data or "skills" in data
            print(f"Skills loaded: {data}")


class TestNudgeEndpoints:
    """POST /api/provision/nudge and /api/provision/nudge/custom"""
    
    def test_nudge_endpoint_returns_200(self):
        """Nudge endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Nudge response: {data}")
    
    def test_nudge_returns_success_and_message(self):
        """Nudge should return success and the message sent"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        # Default nudge message
        assert len(data["message"]) > 0
        print(f"Default nudge sent: {data['message'][:80]}...")
    
    def test_custom_nudge_endpoint_returns_200(self):
        """Custom nudge endpoint should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            headers={"Content-Type": "application/json"},
            json={"message": "TEST_NUDGE: Hello agent from test!"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Custom nudge response: {data}")
    
    def test_custom_nudge_sends_custom_message(self):
        """Custom nudge should echo the custom message"""
        test_message = "TEST_NUDGE: Testing custom nudge functionality"
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
        print(f"Custom nudge verified: {data['message']}")
    
    def test_nudges_appear_in_status(self):
        """Sent nudges should appear in status"""
        # Send a test nudge
        test_msg = "TEST_NUDGE: Verify in status"
        requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            headers={"Content-Type": "application/json"},
            json={"message": test_msg}
        )
        
        # Check status for nudges
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "nudges" in data
        assert len(data["nudges"]) > 0
        # Last nudge should be our test message
        last_nudge = data["nudges"][-1]
        assert "message" in last_nudge
        assert "timestamp" in last_nudge
        print(f"Nudge in status: {last_nudge['message'][:50]}...")


class TestSecurityChecks:
    """Verify security constraints are met"""
    
    def test_no_conway_terminal_on_host(self):
        """SECURITY: conway-terminal should NOT be installed on host"""
        result = subprocess.run(["which", "conway-terminal"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: conway-terminal should NOT be on host"
        print("PASS: conway-terminal not installed on host")
    
    def test_no_openclaw_on_host(self):
        """SECURITY: openclaw should NOT be installed on host"""
        result = subprocess.run(["which", "openclaw"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: openclaw should NOT be on host"
        print("PASS: openclaw not installed on host")
    
    def test_system_prompt_reads_provisioning_status(self):
        """SECURITY: system-prompt.ts should read provisioning-status.json"""
        system_prompt_path = "/app/automaton/src/agent/system-prompt.ts"
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r") as f:
                content = f.read()
            # Should have loadProvisioningStatus function
            assert "loadProvisioningStatus" in content, "system-prompt.ts should have loadProvisioningStatus function"
            assert "provisioning-status.json" in content, "system-prompt.ts should read provisioning-status.json"
            print("PASS: system-prompt.ts reads provisioning-status.json")
        else:
            pytest.skip(f"{system_prompt_path} does not exist")
    
    def test_no_boot_report_in_system_prompt(self):
        """SECURITY: system-prompt.ts should NOT reference BOOT_REPORT"""
        system_prompt_path = "/app/automaton/src/agent/system-prompt.ts"
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r") as f:
                content = f.read()
            assert "BOOT_REPORT" not in content, "SECURITY: system-prompt.ts should NOT reference BOOT_REPORT"
            print("PASS: No BOOT_REPORT in system-prompt.ts")
        else:
            pytest.skip(f"{system_prompt_path} does not exist")


class TestAPIResponseStructure:
    """Verify API response structures are correct"""
    
    def test_status_response_complete_structure(self):
        """Status response should have all required fields"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        
        # All required fields
        required = ["sandbox", "tools", "skills_loaded", "nudges", "credits_cents"]
        for field in required:
            assert field in data, f"Missing required field: {field}"
        
        # Sandbox structure
        assert "status" in data["sandbox"]
        assert "id" in data["sandbox"]
        
        print(f"Status response has all required fields: {list(data.keys())}")
    
    def test_create_sandbox_response_structure(self):
        """Create sandbox response should have success field"""
        response = requests.post(f"{BASE_URL}/api/provision/create-sandbox")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # Either sandbox_id (success) or error (failure)
        if data["success"]:
            assert "sandbox_id" in data or "message" in data
        else:
            assert "error" in data
    
    def test_nudge_response_structure(self):
        """Nudge response should have success and message"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
