"""
Agent Setup Wizard API Tests
Tests the 8-step setup wizard for provisioning agents inside Conway sandbox VMs.
Security-critical: Ensures tools are NOT installed on host system.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://ai-vc-platform-2.preview.emergentagent.com"


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


class TestAgentSetupStatus:
    """GET /api/agent-setup/status - Returns all 8 steps with status"""
    
    def test_status_endpoint_returns_all_steps(self):
        """Status endpoint should return all 8 steps"""
        response = requests.get(f"{BASE_URL}/api/agent-setup/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify steps array exists
        assert "steps" in data
        steps = data["steps"]
        assert len(steps) == 8, f"Expected 8 steps, got {len(steps)}"
        
        # Verify step names match expected order
        expected_steps = [
            "prerequisites",
            "create_sandbox",
            "install_system_tools",
            "install_conway_terminal",
            "install_openclaw",
            "configure_agent",
            "verify_tools",
            "start_agent"
        ]
        
        for i, step in enumerate(steps):
            assert step["name"] == expected_steps[i], f"Step {i} name mismatch: expected {expected_steps[i]}, got {step['name']}"
            assert "status" in step
            assert step["status"] in ["pending", "running", "complete", "failed"]
            assert "detail" in step
            assert "output" in step
        
        # Verify all_complete flag
        assert "all_complete" in data
        print(f"Status endpoint returned {len(steps)} steps. all_complete={data['all_complete']}")


class TestPrerequisitesStep:
    """POST /api/agent-setup/step/prerequisites - Check Conway API key and credits"""
    
    def test_prerequisites_endpoint(self):
        """Prerequisites step should check Conway API key"""
        response = requests.post(
            f"{BASE_URL}/api/agent-setup/step/prerequisites",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have success field
        assert "success" in data
        
        if data["success"]:
            # Success means API key is valid
            assert "credits_cents" in data or "credits_usd" in data
            assert "api_healthy" in data
            print(f"Prerequisites passed: credits_cents={data.get('credits_cents', 0)}, api_healthy={data.get('api_healthy')}")
        else:
            # Failure means API key issue - should have error message
            assert "error" in data
            print(f"Prerequisites returned error (expected if no credits): {data.get('error')}")


class TestCreateSandboxStep:
    """POST /api/agent-setup/step/create-sandbox - Create Conway Cloud sandbox"""
    
    def test_create_sandbox_endpoint(self):
        """Create sandbox step should attempt to create VM"""
        response = requests.post(
            f"{BASE_URL}/api/agent-setup/step/create-sandbox",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have success field
        assert "success" in data
        
        if data["success"]:
            # Success means sandbox was created or exists
            assert "sandbox_id" in data
            print(f"Sandbox created/exists: {data.get('sandbox_id')}")
        else:
            # Failure is expected due to 0 credits
            assert "error" in data
            print(f"Create sandbox returned error (expected - 0 credits): {data.get('error')}")


class TestResetSetup:
    """POST /api/agent-setup/reset - Reset setup state"""
    
    def test_reset_endpoint(self):
        """Reset endpoint should clear setup state"""
        response = requests.post(
            f"{BASE_URL}/api/agent-setup/reset",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        assert "message" in data
        print(f"Reset result: {data}")
    
    def test_status_after_reset(self):
        """After reset, all steps should be pending"""
        # First reset
        reset_response = requests.post(f"{BASE_URL}/api/agent-setup/reset")
        assert reset_response.status_code == 200
        
        # Check status - all should be pending
        status_response = requests.get(f"{BASE_URL}/api/agent-setup/status")
        assert status_response.status_code == 200
        data = status_response.json()
        
        # All steps should be pending after reset
        for step in data["steps"]:
            assert step["status"] == "pending", f"Step {step['name']} should be pending after reset, got {step['status']}"
        
        print("All steps are pending after reset")


class TestAPIStructure:
    """Verify API structure and response formats"""
    
    def test_status_response_structure(self):
        """Verify complete response structure"""
        response = requests.get(f"{BASE_URL}/api/agent-setup/status")
        assert response.status_code == 200
        data = response.json()
        
        # Required top-level keys
        assert "steps" in data
        assert "sandbox_id" in data or data.get("sandbox_id") is None
        assert "all_complete" in data
        
        # Each step structure
        for step in data["steps"]:
            assert "name" in step
            assert "status" in step
            assert "detail" in step
            assert "output" in step
    
    def test_prerequisites_response_structure(self):
        """Verify prerequisites response structure"""
        response = requests.post(f"{BASE_URL}/api/agent-setup/step/prerequisites")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        if data["success"]:
            # On success, should have credits info
            assert "credits_usd" in data or "credits_cents" in data
    
    def test_step_url_format(self):
        """Verify step URLs use hyphen format (not underscore)"""
        # Prerequisites uses hyphen format in URL
        response = requests.post(f"{BASE_URL}/api/agent-setup/step/prerequisites")
        assert response.status_code == 200
        
        # create-sandbox uses hyphen format
        response = requests.post(f"{BASE_URL}/api/agent-setup/step/create-sandbox")
        assert response.status_code == 200


class TestStepDependencies:
    """Test step execution order and dependencies"""
    
    def test_steps_can_be_executed_in_order(self):
        """Verify steps can be executed (even if they fail due to no credits)"""
        # Reset first
        requests.post(f"{BASE_URL}/api/agent-setup/reset")
        
        # Step 1: Prerequisites
        r1 = requests.post(f"{BASE_URL}/api/agent-setup/step/prerequisites")
        assert r1.status_code == 200
        print(f"Prerequisites: {r1.json()}")
        
        # Step 2: Create Sandbox (may fail due to credits)
        r2 = requests.post(f"{BASE_URL}/api/agent-setup/step/create-sandbox")
        assert r2.status_code == 200
        print(f"Create Sandbox: {r2.json()}")


# Security Tests - CRITICAL
class TestSecurityChecks:
    """Verify no tools are installed on host system"""
    
    def test_no_conway_terminal_on_host(self):
        """Verify conway-terminal is NOT installed on host"""
        import subprocess
        result = subprocess.run(["which", "conway-terminal"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: conway-terminal should NOT be on host"
        print("Security check passed: conway-terminal not on host")
    
    def test_no_openclaw_on_host(self):
        """Verify openclaw is NOT installed on host"""
        import subprocess
        result = subprocess.run(["which", "openclaw"], capture_output=True, text=True)
        assert result.returncode != 0, "SECURITY BREACH: openclaw should NOT be on host"
        print("Security check passed: openclaw not on host")
    
    def test_bootstrap_script_disabled(self):
        """Verify bootstrap_agent.sh exits immediately"""
        bootstrap_path = "/app/scripts/bootstrap_agent.sh"
        assert os.path.exists(bootstrap_path), "bootstrap_agent.sh should exist"
        
        with open(bootstrap_path, "r") as f:
            content = f.read()
        
        # Should contain exit 0 early in the script
        assert "exit 0" in content, "bootstrap_agent.sh should exit immediately"
        assert "disabled" in content.lower() or "DISABLED" in content, "bootstrap_agent.sh should indicate it's disabled"
        print("Security check passed: bootstrap_agent.sh is disabled")
    
    def test_no_boot_report_in_system_prompt(self):
        """Verify system-prompt.ts has no BOOT_REPORT references"""
        system_prompt_path = "/app/automaton/src/agent/system-prompt.ts"
        
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r") as f:
                content = f.read()
            assert "BOOT_REPORT" not in content, "SECURITY: system-prompt.ts should not reference BOOT_REPORT"
            print("Security check passed: no BOOT_REPORT in system-prompt.ts")
        else:
            print(f"Note: {system_prompt_path} does not exist (may be expected)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
