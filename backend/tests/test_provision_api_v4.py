"""
Test suite for Agent Provisioning API - Iteration 4
Tests new endpoints: deploy-agent, agent-logs, phase-state
Also verifies existing endpoints still work

Key changes in iteration 4:
- Deploy Agent endpoint (pushes engine into sandbox)
- Agent Logs endpoint (reads logs from sandbox)  
- Phase State endpoint (tracks phase 0/1/2/3)
- Engine status in tools dict
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestNewEndpointsIteration4:
    """Tests for new endpoints added in iteration 4"""

    def test_deploy_agent_no_sandbox(self):
        """POST /api/provision/deploy-agent fails gracefully without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/deploy-agent")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ deploy-agent fails gracefully without sandbox")

    def test_agent_logs_no_sandbox(self):
        """GET /api/provision/agent-logs fails gracefully without sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/agent-logs?lines=30")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ agent-logs fails gracefully without sandbox")

    def test_phase_state_no_sandbox_no_local(self):
        """GET /api/provision/phase-state returns error or default phase 0"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200
        data = response.json()
        # Either returns error (no sandbox no local) or default phase state
        if data.get("success") is False:
            assert "No sandbox" in data.get("error", "") or "no local" in data.get("error", "")
        else:
            # If success, should have phase_state with current_phase
            assert "phase_state" in data
        print("✓ phase-state endpoint works correctly")


class TestStatusEndpointIteration4:
    """Tests for status endpoint with new engine field"""

    def test_status_has_all_expected_fields(self):
        """GET /api/provision/status returns all expected fields including tools"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "sandbox" in data
        assert "tools" in data
        assert "ports" in data
        assert "domains" in data
        assert "compute_verified" in data
        assert "skills_loaded" in data
        assert "nudges" in data
        assert "credits_cents" in data
        assert "last_updated" in data
        print("✓ Status endpoint returns all expected fields")

    def test_status_tools_can_contain_engine(self):
        """Tools dict can contain engine when deployed"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        # tools is a dict that can contain engine when deployed
        assert isinstance(data["tools"], dict)
        # Engine not deployed without sandbox, so tools empty or no engine key
        if "engine" in data["tools"]:
            assert "deployed" in data["tools"]["engine"]
        print("✓ Tools dict structure is correct")


class TestExistingEndpointsIteration4:
    """Verify existing endpoints still work correctly"""

    def test_create_sandbox_insufficient_credits(self):
        """POST /api/provision/create-sandbox fails with insufficient credits"""
        response = requests.post(f"{BASE_URL}/api/provision/create-sandbox")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Insufficient credits" in data["error"] or "insufficient" in data["error"].lower()
        print("✓ create-sandbox fails with insufficient credits")

    def test_nudge_works(self):
        """POST /api/provision/nudge sends autonomy nudge"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("✓ nudge endpoint works")

    def test_custom_nudge_works(self):
        """POST /api/provision/nudge/custom sends custom message"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            json={"message": "TEST_V4_CUSTOM_NUDGE"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "TEST_V4_CUSTOM_NUDGE"
        print("✓ custom nudge endpoint works")

    def test_install_terminal_no_sandbox(self):
        """POST /api/provision/install-terminal fails without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-terminal")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ install-terminal fails gracefully without sandbox")

    def test_install_openclaw_no_sandbox(self):
        """POST /api/provision/install-openclaw fails without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/install-openclaw")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ install-openclaw fails gracefully without sandbox")

    def test_expose_port_no_sandbox(self):
        """POST /api/provision/expose-port fails without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/expose-port",
            json={"port": 3000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ expose-port fails gracefully without sandbox")

    def test_web_terminal_no_sandbox(self):
        """POST /api/provision/web-terminal fails without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/web-terminal")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ web-terminal fails gracefully without sandbox")

    def test_load_skills_no_sandbox(self):
        """POST /api/provision/load-skills fails without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ load-skills fails gracefully without sandbox")

    def test_credits_endpoint(self):
        """GET /api/provision/credits returns balance info"""
        response = requests.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print("✓ credits endpoint works")

    def test_wallet_endpoint(self):
        """GET /api/provision/wallet returns wallet info"""
        response = requests.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        print("✓ wallet endpoint works")

    def test_list_sandboxes(self):
        """GET /api/provision/list-sandboxes returns list"""
        response = requests.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        # May return success true with empty array or success false with error
        assert "success" in data or "sandboxes" in data
        print("✓ list-sandboxes endpoint works")

    def test_delete_sandbox_no_sandbox(self):
        """POST /api/provision/delete-sandbox fails without sandbox"""
        response = requests.post(f"{BASE_URL}/api/provision/delete-sandbox")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ delete-sandbox fails gracefully without sandbox")

    def test_exec_no_sandbox(self):
        """POST /api/provision/exec fails without sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/exec",
            json={"command": "ls -la"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No sandbox" in data["error"]
        print("✓ exec fails gracefully without sandbox")


class TestGenesisPromptContent:
    """Verify genesis prompt file has required content"""
    
    def test_genesis_prompt_has_phase_system(self):
        """Genesis prompt contains 4-phase system"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        # Check for phase 0, 1, 2, 3 mentions
        assert "PHASE 0" in content
        assert "PHASE 1" in content  
        assert "PHASE 2" in content
        assert "PHASE 3" in content
        assert "TOOL TESTING" in content
        assert "$5,000" in content or "$5000" in content
        assert "$10,000" in content or "$10000" in content
        print("✓ Genesis prompt has 4-phase system")

    def test_genesis_prompt_has_10_tool_tests(self):
        """Genesis prompt has 10 functional tool test definitions"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        # Check for key tool test mentions
        assert "CURL" in content
        assert "GIT" in content
        assert "NODE" in content
        assert "PYTHON3" in content
        assert "TELEGRAM" in content
        assert "CONWAY TERMINAL" in content
        assert "SANDBOX" in content
        assert "DOMAINS" in content
        assert "COMPUTE" in content
        assert "PORT EXPOSURE" in content
        print("✓ Genesis prompt has 10 functional tool tests")

    def test_genesis_prompt_revenue_targets(self):
        """Genesis prompt has $5k and $10k revenue targets"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        # Check for revenue targets
        assert "$5,000" in content or "$5000" in content
        assert "$10,000" in content or "$10000" in content
        assert "EARN" in content.upper() or "earn" in content
        print("✓ Genesis prompt has revenue targets")


class TestSystemPromptContent:
    """Verify system-prompt.ts has required content"""
    
    def test_system_prompt_has_load_phase_state(self):
        """system-prompt.ts has loadPhaseState function"""
        prompt_path = "/app/automaton/src/agent/system-prompt.ts"
        with open(prompt_path, "r") as f:
            content = f.read()
        
        assert "loadPhaseState" in content
        assert "phase-state.json" in content
        print("✓ system-prompt.ts has loadPhaseState function")

    def test_system_prompt_has_phase_enforcement(self):
        """system-prompt.ts has Layer 5.6 phase enforcement"""
        prompt_path = "/app/automaton/src/agent/system-prompt.ts"
        with open(prompt_path, "r") as f:
            content = f.read()
        
        assert "PHASE ENFORCEMENT" in content
        assert "current_phase" in content
        assert "PHASE 0" in content or "Phase 0" in content
        assert "PHASE 1" in content or "Phase 1" in content
        assert "PHASE 2" in content or "Phase 2" in content
        assert "PHASE 3" in content or "Phase 3" in content
        print("✓ system-prompt.ts has phase enforcement in Layer 5.6")


class TestSecurityChecks:
    """Security verification - no host installations"""
    
    def test_no_conway_terminal_on_host(self):
        """which conway-terminal returns nothing (not on host)"""
        import subprocess
        result = subprocess.run(
            ["which", "conway-terminal"],
            capture_output=True,
            text=True
        )
        # Should not find it or return empty
        assert result.returncode != 0 or result.stdout.strip() == ""
        print("✓ conway-terminal NOT installed on host")

    def test_no_openclaw_on_host(self):
        """which openclaw returns nothing (not on host)"""
        import subprocess
        result = subprocess.run(
            ["which", "openclaw"],
            capture_output=True,
            text=True
        )
        # Should not find it or return empty
        assert result.returncode != 0 or result.stdout.strip() == ""
        print("✓ openclaw NOT installed on host")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
