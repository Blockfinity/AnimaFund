"""
Test AnimaVM Backend APIs - Iteration 6

Tests for the new unified AnimaVM page:
- /api/provision/status - Returns provisioning status
- /api/provision/phase-state - Returns phase state
- /api/openclaw/status - Returns OpenClaw monitoring status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestProvisionStatus:
    """Tests for GET /api/provision/status endpoint"""
    
    def test_provision_status_returns_200(self):
        """GET /api/provision/status returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"SUCCESS: /api/provision/status returns 200")
    
    def test_provision_status_returns_valid_json(self):
        """GET /api/provision/status returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "sandbox" in data, "Missing 'sandbox' field"
        assert "tools" in data, "Missing 'tools' field"
        assert "ports" in data, "Missing 'ports' field"
        assert "domains" in data, "Missing 'domains' field"
        assert "compute_verified" in data, "Missing 'compute_verified' field"
        assert "skills_loaded" in data, "Missing 'skills_loaded' field"
        assert "nudges" in data, "Missing 'nudges' field"
        
        print(f"SUCCESS: /api/provision/status has all required fields")
    
    def test_provision_status_sandbox_structure(self):
        """GET /api/provision/status sandbox field has correct structure"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        data = response.json()
        
        sandbox = data.get("sandbox", {})
        assert "status" in sandbox, "sandbox missing 'status' field"
        assert "id" in sandbox, "sandbox missing 'id' field"
        
        print(f"SUCCESS: sandbox structure is correct (status={sandbox.get('status')})")
    
    def test_provision_status_nudges_are_list(self):
        """GET /api/provision/status nudges is a list"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        data = response.json()
        
        nudges = data.get("nudges", [])
        assert isinstance(nudges, list), "nudges should be a list"
        
        print(f"SUCCESS: nudges is a list with {len(nudges)} items")


class TestPhaseState:
    """Tests for GET /api/provision/phase-state endpoint"""
    
    def test_phase_state_returns_200(self):
        """GET /api/provision/phase-state returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"SUCCESS: /api/provision/phase-state returns 200")
    
    def test_phase_state_returns_valid_json(self):
        """GET /api/provision/phase-state returns valid JSON"""
        response = requests.get(f"{BASE_URL}/api/provision/phase-state")
        data = response.json()
        
        # Either success=true with phase_state, or success=false with error
        if data.get("success"):
            assert "phase_state" in data, "success=true but missing phase_state"
            phase_state = data["phase_state"]
            assert "current_phase" in phase_state, "phase_state missing current_phase"
            print(f"SUCCESS: phase_state has current_phase={phase_state.get('current_phase')}")
        else:
            # No sandbox - expected in test env
            assert "error" in data, "success=false but missing error"
            print(f"OK: No phase state available (no sandbox): {data.get('error')}")


class TestOpenClawStatus:
    """Tests for GET /api/openclaw/status endpoint"""
    
    def test_openclaw_status_returns_200(self):
        """GET /api/openclaw/status returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"SUCCESS: /api/openclaw/status returns 200")
    
    def test_openclaw_status_returns_valid_json(self):
        """GET /api/openclaw/status returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        data = response.json()
        
        # Check required fields
        assert "openclaw" in data, "Missing 'openclaw' field"
        assert "sandbox_summary" in data, "Missing 'sandbox_summary' field"
        assert "has_activity" in data, "Missing 'has_activity' field"
        
        print(f"SUCCESS: /api/openclaw/status has all required fields")
    
    def test_openclaw_status_openclaw_structure(self):
        """GET /api/openclaw/status openclaw field has correct structure"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        data = response.json()
        
        openclaw = data.get("openclaw", {})
        required_fields = [
            "openclaw_installed",
            "openclaw_daemon_running", 
            "mcp_configured",
            "conway_terminal_in_sandbox"
        ]
        
        for field in required_fields:
            assert field in openclaw, f"openclaw missing '{field}' field"
        
        print(f"SUCCESS: openclaw structure has all required fields")
    
    def test_openclaw_status_sandbox_summary_structure(self):
        """GET /api/openclaw/status sandbox_summary has correct structure"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        data = response.json()
        
        sandbox_summary = data.get("sandbox_summary", {})
        required_fields = [
            "known_sandbox_ids",
            "live_sandboxes",
            "total_operations",
            "creates",
            "execs",
            "ports_exposed"
        ]
        
        for field in required_fields:
            assert field in sandbox_summary, f"sandbox_summary missing '{field}' field"
        
        print(f"SUCCESS: sandbox_summary has all required fields")


class TestOpenClawActions:
    """Tests for GET /api/openclaw/actions endpoint"""
    
    def test_actions_returns_200(self):
        """GET /api/openclaw/actions returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/openclaw/actions")
        assert response.status_code == 200
        print(f"SUCCESS: /api/openclaw/actions returns 200")
    
    def test_actions_returns_valid_structure(self):
        """GET /api/openclaw/actions returns list of actions"""
        response = requests.get(f"{BASE_URL}/api/openclaw/actions")
        data = response.json()
        
        assert "actions" in data, "Missing 'actions' field"
        assert "total" in data, "Missing 'total' field"
        assert isinstance(data["actions"], list), "actions should be a list"
        
        print(f"SUCCESS: /api/openclaw/actions has {len(data['actions'])} actions")


class TestOpenClawSandboxes:
    """Tests for GET /api/openclaw/sandboxes endpoint"""
    
    def test_sandboxes_returns_200(self):
        """GET /api/openclaw/sandboxes returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandboxes")
        assert response.status_code == 200
        print(f"SUCCESS: /api/openclaw/sandboxes returns 200")
    
    def test_sandboxes_returns_valid_structure(self):
        """GET /api/openclaw/sandboxes returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandboxes")
        data = response.json()
        
        assert "live_sandboxes" in data, "Missing 'live_sandboxes' field"
        assert "created_sandboxes" in data, "Missing 'created_sandboxes' field"
        assert "total_live" in data, "Missing 'total_live' field"
        assert "total_created" in data, "Missing 'total_created' field"
        
        print(f"SUCCESS: sandboxes structure correct (live={data['total_live']}, created={data['total_created']})")


class TestOpenClawBrowsing:
    """Tests for GET /api/openclaw/browsing endpoint"""
    
    def test_browsing_returns_200(self):
        """GET /api/openclaw/browsing returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/openclaw/browsing")
        assert response.status_code == 200
        print(f"SUCCESS: /api/openclaw/browsing returns 200")
    
    def test_browsing_returns_valid_structure(self):
        """GET /api/openclaw/browsing returns sessions list"""
        response = requests.get(f"{BASE_URL}/api/openclaw/browsing")
        data = response.json()
        
        assert "sessions" in data, "Missing 'sessions' field"
        assert "total" in data, "Missing 'total' field"
        assert isinstance(data["sessions"], list), "sessions should be a list"
        
        print(f"SUCCESS: browsing has {len(data['sessions'])} sessions")


class TestOpenClawExecLog:
    """Tests for GET /api/openclaw/sandbox-exec-log endpoint"""
    
    def test_exec_log_returns_200(self):
        """GET /api/openclaw/sandbox-exec-log returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandbox-exec-log")
        assert response.status_code == 200
        print(f"SUCCESS: /api/openclaw/sandbox-exec-log returns 200")
    
    def test_exec_log_returns_valid_structure(self):
        """GET /api/openclaw/sandbox-exec-log returns log list"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandbox-exec-log")
        data = response.json()
        
        assert "log" in data, "Missing 'log' field"
        assert "total" in data, "Missing 'total' field"
        assert isinstance(data["log"], list), "log should be a list"
        
        print(f"SUCCESS: exec-log has {len(data['log'])} entries")


class TestNudgeEndpoints:
    """Tests for nudge/message endpoints"""
    
    def test_nudge_post_returns_200(self):
        """POST /api/provision/nudge returns 200 OK"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True, "nudge should return success=true"
        print(f"SUCCESS: /api/provision/nudge returns success")
    
    def test_custom_nudge_post_returns_200(self):
        """POST /api/provision/nudge/custom with message returns 200 OK"""
        response = requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            json={"message": "TEST_ITERATION_6_NUDGE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True, "custom nudge should return success=true"
        print(f"SUCCESS: /api/provision/nudge/custom returns success")
    
    def test_nudge_appears_in_status(self):
        """Nudges sent via API appear in provision status"""
        # Send a unique nudge
        unique_msg = "TEST_UNIQUE_ITER6_VERIFY"
        requests.post(
            f"{BASE_URL}/api/provision/nudge/custom",
            json={"message": unique_msg}
        )
        
        # Check it appears in status
        response = requests.get(f"{BASE_URL}/api/provision/status")
        data = response.json()
        
        nudges = data.get("nudges", [])
        messages = [n.get("message", "") for n in nudges]
        
        assert unique_msg in messages, f"Nudge '{unique_msg}' not found in status nudges"
        print(f"SUCCESS: Custom nudge appears in status")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
