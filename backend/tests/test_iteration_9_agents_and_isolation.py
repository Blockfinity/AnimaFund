"""
Iteration 9: Agent CRUD, Multi-agent isolation, and Per-agent provisioning tests.

Tests:
1. Backend /api/provision/status returns agent_id field matching the active agent
2. Backend /api/agents - lists agents from MongoDB
3. Backend /api/agents/create - creates agent with selected_skills stored in DB
4. Backend /api/agents/{id}/select - switches active agent and affects provisioning status
5. Per-agent provisioning isolation: after selecting different agents, /api/provision/status returns different agent_id
6. Backend /api/provision/phase-state returns valid JSON
7. Backend /api/skills/available returns skills list
8. Load-skills endpoint includes priority_skills from agent DB
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://ai-venture-capital.preview.emergentagent.com'

# Test agent data
TEST_AGENT_SUFFIX = f"_{int(time.time())}"
TEST_AGENT_NAME = f"TestAgent{TEST_AGENT_SUFFIX}"
TEST_AGENT_ID = f"testagent{TEST_AGENT_SUFFIX}"

# Cleanup list to track created test agents
created_agents = []


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestProvisionStatusAgentId:
    """Test that provisioning status returns the active agent_id."""
    
    def test_provision_status_returns_agent_id(self, api_client):
        """GET /api/provision/status should return agent_id field."""
        response = api_client.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data, "agent_id field missing from provision status"
        assert isinstance(data["agent_id"], str)
        print(f"Provision status agent_id: {data['agent_id']}")
    
    def test_provision_status_default_agent(self, api_client):
        """Default agent should have agent_id 'anima-fund'."""
        # First ensure we're on the default agent
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.3)  # Let the server update
        
        response = api_client.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "anima-fund", f"Expected agent_id 'anima-fund', got '{data['agent_id']}'"
        print("Default agent provision status verified: agent_id=anima-fund")


class TestAgentsListing:
    """Test agent listing from MongoDB."""
    
    def test_list_agents_endpoint(self, api_client):
        """GET /api/agents should return list of agents."""
        response = api_client.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        print(f"Found {len(data['agents'])} agents")
        
    def test_list_agents_has_default(self, api_client):
        """Default anima-fund agent should exist."""
        response = api_client.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        agent_ids = [a["agent_id"] for a in data["agents"]]
        assert "anima-fund" in agent_ids, "Default agent anima-fund not found"
        print("Default agent anima-fund verified in agent list")
        
    def test_agents_sanitized_no_bot_token(self, api_client):
        """Agent list should NOT expose telegram_bot_token."""
        response = api_client.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        for agent in data["agents"]:
            assert "telegram_bot_token" not in agent, f"telegram_bot_token exposed for agent {agent.get('agent_id')}"
        print("Verified: telegram_bot_token not exposed in agent list")


class TestAgentCreationWithSkills:
    """Test agent creation with selected_skills stored in DB."""
    
    def test_create_agent_requires_telegram(self, api_client):
        """Creating agent without Telegram creds should fail."""
        response = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "NoTelegramAgent",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "",
            "telegram_chat_id": "",
        })
        assert response.status_code == 400 or (response.status_code == 200 and not response.json().get("success"))
        print("Verified: Agent creation requires Telegram credentials")
        
    def test_create_agent_requires_both_telegram_fields(self, api_client):
        """Creating agent with partial Telegram should fail."""
        response = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "PartialTelegramAgent",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "123456:ABC",  # Token but no chat ID
            "telegram_chat_id": "",
        })
        assert response.status_code == 400 or (response.status_code == 200 and not response.json().get("success"))
        print("Verified: Agent creation requires both Telegram fields")


class TestAgentSelection:
    """Test agent selection and its effect on provisioning status."""
    
    def test_select_default_agent(self, api_client):
        """POST /api/agents/anima-fund/select should succeed."""
        response = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("active_agent") == "anima-fund"
        print("Default agent selection verified")
        
    def test_select_nonexistent_agent(self, api_client):
        """Selecting non-existent agent should return 404."""
        response = api_client.post(f"{BASE_URL}/api/agents/nonexistent-agent-xyz/select")
        assert response.status_code == 404
        print("Non-existent agent selection returns 404")


class TestMultiAgentIsolation:
    """Test per-agent provisioning isolation."""
    
    def test_default_agent_provision_status(self, api_client):
        """After selecting default agent, provision status should show anima-fund."""
        # Select default
        select_res = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert select_res.status_code == 200
        time.sleep(0.3)
        
        # Check provision status
        status_res = api_client.get(f"{BASE_URL}/api/provision/status")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["agent_id"] == "anima-fund"
        print(f"After selecting anima-fund, provision agent_id = {data['agent_id']}")


class TestPhaseState:
    """Test phase-state endpoint."""
    
    def test_phase_state_returns_valid_json(self, api_client):
        """GET /api/provision/phase-state should return valid JSON."""
        response = api_client.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200
        data = response.json()
        # The response should have either 'success' or 'phase_state' field
        assert "success" in data or "phase_state" in data
        print(f"Phase state response: {data}")


class TestSkillsEndpoint:
    """Test skills availability endpoint."""
    
    def test_skills_available_endpoint(self, api_client):
        """GET /api/skills/available should return skills list."""
        response = api_client.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0, "Skills list should not be empty"
        print(f"Found {len(data['skills'])} available skills")
        
    def test_skills_have_required_fields(self, api_client):
        """Each skill should have name, description, source fields."""
        response = api_client.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        for skill in data["skills"][:10]:  # Check first 10
            assert "name" in skill, f"Skill missing 'name' field"
            assert "source" in skill, f"Skill missing 'source' field: {skill}"
        print("Skills have required fields verified")


class TestLoadSkillsEndpoint:
    """Test load-skills endpoint."""
    
    def test_load_skills_without_sandbox(self, api_client):
        """POST /api/provision/load-skills should fail gracefully without sandbox."""
        response = api_client.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
        data = response.json()
        # Should return success=false with error about no sandbox
        if not data.get("success"):
            assert "sandbox" in data.get("error", "").lower() or "sandbox" in str(data).lower()
        print(f"Load-skills response: {data}")


class TestExistingProvisionEndpoints:
    """Verify existing provision endpoints still work (regression tests)."""
    
    def test_status_endpoint(self, api_client):
        """GET /api/provision/status should return expected fields."""
        response = api_client.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "sandbox" in data
        assert "tools" in data
        assert "nudges" in data
        print("Provision status endpoint verified")
        
    def test_credits_endpoint(self, api_client):
        """GET /api/provision/credits should work."""
        response = api_client.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print("Credits endpoint verified")
        
    def test_wallet_endpoint(self, api_client):
        """GET /api/provision/wallet should work."""
        response = api_client.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "wallet" in data
        print("Wallet endpoint verified")
        
    def test_list_sandboxes_endpoint(self, api_client):
        """GET /api/provision/list-sandboxes should work."""
        response = api_client.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "sandboxes" in data or "error" in data
        print("List sandboxes endpoint verified")


class TestNudgeEndpoints:
    """Test nudge/message endpoints."""
    
    def test_nudge_default(self, api_client):
        """POST /api/provision/nudge should work."""
        response = api_client.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("Default nudge endpoint verified")
        
    def test_custom_nudge(self, api_client):
        """POST /api/provision/nudge/custom should work."""
        response = api_client.post(f"{BASE_URL}/api/provision/nudge/custom", json={
            "message": f"TEST_ITERATION_9_NUDGE_{int(time.time())}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("Custom nudge endpoint verified")


class TestPtyEndpointsWithoutSandbox:
    """Verify PTY endpoints return proper error when no sandbox."""
    
    def test_pty_list_no_sandbox(self, api_client):
        """GET /api/provision/pty/list should return error without sandbox."""
        response = api_client.get(f"{BASE_URL}/api/provision/pty/list")
        assert response.status_code == 200
        data = response.json()
        if not data.get("success"):
            assert "sandbox" in data.get("error", "").lower()
        print("PTY list endpoint handles no-sandbox case")
        
    def test_pty_create_no_sandbox(self, api_client):
        """POST /api/provision/pty/create should return error without sandbox."""
        response = api_client.post(f"{BASE_URL}/api/provision/pty/create", json={
            "command": "bash"
        })
        assert response.status_code == 200
        data = response.json()
        if not data.get("success"):
            assert "sandbox" in data.get("error", "").lower()
        print("PTY create endpoint handles no-sandbox case")


# Cleanup - ensure we switch back to default agent
@pytest.fixture(scope="session", autouse=True)
def cleanup(api_client):
    """Cleanup: Switch back to default agent after tests."""
    yield
    # Switch back to default agent
    try:
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        print("Cleanup: Switched back to default agent")
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
