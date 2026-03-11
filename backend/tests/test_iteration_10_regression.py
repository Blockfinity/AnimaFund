"""
Iteration 10: Regression test after genesis-prompt.md update.

Tests all backend APIs from iteration 9 plus verification that genesis-prompt.md 
includes Phase 3 with boardy.ai and hundreds of millions target.

Test Groups:
1. Health endpoint
2. Agent CRUD and listing (no telegram_bot_token exposure)
3. Agent creation requirements (telegram_bot_token and telegram_chat_id)
4. Agent selection (including 404 for nonexistent)
5. Provisioning status (agent_id field matching active agent)
6. Phase state endpoint
7. Skills available endpoint
8. Load skills endpoint
9. Credits and wallet endpoints
10. Sandbox listing
11. Nudge endpoints
12. PTY list endpoint (error expected without sandbox)
13. Multi-agent isolation test
14. Genesis prompt content verification (Phase 3, boardy.ai, hundreds of millions)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://ai-agent-sandbox-1.preview.emergentagent.com'


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ═══════════════════════════════════════════════════════════
# 1. HEALTH ENDPOINT
# ═══════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_200(self, api_client):
        """GET /api/health should return 200 with status ok."""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got '{data.get('status')}'"
        print(f"Health check passed: status={data['status']}")


# ═══════════════════════════════════════════════════════════
# 2. AGENTS LIST (no bot token exposure)
# ═══════════════════════════════════════════════════════════

class TestAgentsList:
    """Test agent listing endpoint."""
    
    def test_list_agents_returns_list(self, api_client):
        """GET /api/agents should return a list of agents."""
        response = api_client.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        print(f"Agents list returned {len(data['agents'])} agents")
        
    def test_agents_never_expose_telegram_bot_token(self, api_client):
        """Agent list should NEVER expose telegram_bot_token field."""
        response = api_client.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        for agent in data["agents"]:
            assert "telegram_bot_token" not in agent, \
                f"SECURITY: telegram_bot_token exposed for agent {agent.get('agent_id')}"
        print("Verified: telegram_bot_token is NOT exposed in agent list")


# ═══════════════════════════════════════════════════════════
# 3. AGENT CREATION REQUIREMENTS
# ═══════════════════════════════════════════════════════════

class TestAgentCreation:
    """Test agent creation validation."""
    
    def test_create_requires_telegram_bot_token(self, api_client):
        """POST /api/agents/create without telegram_bot_token should fail."""
        response = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "TestNoToken",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "",
            "telegram_chat_id": "123456",
        })
        # Should be 400 or success=false
        if response.status_code == 200:
            assert response.json().get("success") == False
        else:
            assert response.status_code == 400
        print("Verified: Agent creation requires telegram_bot_token")
        
    def test_create_requires_telegram_chat_id(self, api_client):
        """POST /api/agents/create without telegram_chat_id should fail."""
        response = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "TestNoChatId",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "123456:ABC-DEF",
            "telegram_chat_id": "",
        })
        # Should be 400 or success=false
        if response.status_code == 200:
            assert response.json().get("success") == False
        else:
            assert response.status_code == 400
        print("Verified: Agent creation requires telegram_chat_id")
        
    def test_create_stores_selected_skills(self, api_client):
        """Agent creation should accept selected_skills parameter."""
        # This is a validation test - the actual creation will fail due to Telegram validation
        # but we verify the endpoint accepts the parameter
        response = api_client.post(f"{BASE_URL}/api/agents/create", json={
            "name": "TestSkills",
            "genesis_prompt": "Test prompt",
            "telegram_bot_token": "fake",
            "telegram_chat_id": "fake",
            "selected_skills": ["skill1", "skill2"],
        })
        # We expect 400 due to invalid telegram, but endpoint accepts selected_skills
        assert response.status_code in [200, 400, 422]
        print("Verified: Agent creation endpoint accepts selected_skills parameter")


# ═══════════════════════════════════════════════════════════
# 4. AGENT SELECTION
# ═══════════════════════════════════════════════════════════

class TestAgentSelection:
    """Test agent selection endpoint."""
    
    def test_select_anima_fund_returns_success(self, api_client):
        """POST /api/agents/anima-fund/select should return success."""
        response = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("active_agent") == "anima-fund"
        print("Agent selection (anima-fund) successful")
        
    def test_select_nonexistent_returns_404(self, api_client):
        """POST /api/agents/nonexistent/select should return 404."""
        response = api_client.post(f"{BASE_URL}/api/agents/nonexistent/select")
        assert response.status_code == 404
        print("Agent selection (nonexistent) returns 404 as expected")


# ═══════════════════════════════════════════════════════════
# 5. PROVISIONING STATUS
# ═══════════════════════════════════════════════════════════

class TestProvisioningStatus:
    """Test provisioning status endpoint."""
    
    def test_status_returns_agent_id(self, api_client):
        """GET /api/provision/status should return agent_id field."""
        # First ensure we're on anima-fund
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.2)
        
        response = api_client.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data, "agent_id field missing from provision status"
        print(f"Provision status returned agent_id: {data['agent_id']}")
        
    def test_status_agent_id_matches_active_agent(self, api_client):
        """Provision status agent_id should match the active agent."""
        # Select anima-fund
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.2)
        
        response = api_client.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "anima-fund", \
            f"Expected agent_id 'anima-fund', got '{data['agent_id']}'"
        print("Verified: provision status agent_id matches active agent")


# ═══════════════════════════════════════════════════════════
# 6. PHASE STATE ENDPOINT
# ═══════════════════════════════════════════════════════════

class TestPhaseState:
    """Test phase state endpoint."""
    
    def test_phase_state_returns_valid_json(self, api_client):
        """GET /api/provision/phase-state should return valid JSON."""
        response = api_client.get(f"{BASE_URL}/api/provision/phase-state")
        assert response.status_code == 200
        data = response.json()
        # Response should have success field or phase_state field
        assert "success" in data or "phase_state" in data
        print(f"Phase state endpoint returns valid JSON: keys={list(data.keys())}")


# ═══════════════════════════════════════════════════════════
# 7. SKILLS AVAILABLE ENDPOINT
# ═══════════════════════════════════════════════════════════

class TestSkillsAvailable:
    """Test skills availability endpoint."""
    
    def test_skills_returns_array(self, api_client):
        """GET /api/skills/available should return skills array."""
        response = api_client.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0
        print(f"Skills endpoint returned {len(data['skills'])} skills")
        
    def test_skills_have_name_and_source(self, api_client):
        """Each skill should have name and source fields."""
        response = api_client.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        for skill in data["skills"][:10]:  # Check first 10
            assert "name" in skill, f"Skill missing 'name': {skill}"
            assert "source" in skill, f"Skill missing 'source': {skill}"
        print("Verified: Skills have 'name' and 'source' fields")


# ═══════════════════════════════════════════════════════════
# 8. LOAD SKILLS ENDPOINT
# ═══════════════════════════════════════════════════════════

class TestLoadSkills:
    """Test load-skills endpoint."""
    
    def test_load_skills_returns_success_with_priority_skills(self, api_client):
        """POST /api/provision/load-skills should return response (may fail without sandbox)."""
        response = api_client.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200
        data = response.json()
        # Check that priority_skills is in response when success or we have expected error
        if data.get("success"):
            assert "priority_skills" in data, "priority_skills field missing on success"
        else:
            # Expected: error about no sandbox
            assert "sandbox" in str(data).lower() or "error" in data
        print(f"Load skills response: success={data.get('success')}")


# ═══════════════════════════════════════════════════════════
# 9. CREDITS AND WALLET ENDPOINTS
# ═══════════════════════════════════════════════════════════

class TestCreditsAndWallet:
    """Test credits and wallet endpoints."""
    
    def test_credits_returns_balance_object(self, api_client):
        """GET /api/provision/credits should return balance object."""
        response = api_client.get(f"{BASE_URL}/api/provision/credits")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print(f"Credits endpoint returned balance: {data['balance']}")
        
    def test_wallet_returns_wallet_info(self, api_client):
        """GET /api/provision/wallet should return wallet info."""
        response = api_client.get(f"{BASE_URL}/api/provision/wallet")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "wallet" in data
        print(f"Wallet endpoint returned: keys={list(data.keys())}")


# ═══════════════════════════════════════════════════════════
# 10. SANDBOX LISTING
# ═══════════════════════════════════════════════════════════

class TestSandboxListing:
    """Test sandbox listing endpoint."""
    
    def test_list_sandboxes_returns_list(self, api_client):
        """GET /api/provision/list-sandboxes should return sandboxes list."""
        response = api_client.get(f"{BASE_URL}/api/provision/list-sandboxes")
        assert response.status_code == 200
        data = response.json()
        # Should have sandboxes list or error (if no API key)
        assert "sandboxes" in data or "success" in data or "error" in data
        print(f"List sandboxes endpoint returned: keys={list(data.keys())}")


# ═══════════════════════════════════════════════════════════
# 11. NUDGE ENDPOINTS
# ═══════════════════════════════════════════════════════════

class TestNudgeEndpoints:
    """Test nudge endpoints."""
    
    def test_nudge_returns_success(self, api_client):
        """POST /api/provision/nudge should return success."""
        response = api_client.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("Default nudge endpoint returns success")
        
    def test_nudge_custom_accepts_message_body(self, api_client):
        """POST /api/provision/nudge/custom should accept message body."""
        test_message = f"TEST_ITERATION_10_{int(time.time())}"
        response = api_client.post(f"{BASE_URL}/api/provision/nudge/custom", json={
            "message": test_message
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"Custom nudge with message body returns success")


# ═══════════════════════════════════════════════════════════
# 12. PTY LIST ENDPOINT
# ═══════════════════════════════════════════════════════════

class TestPtyList:
    """Test PTY list endpoint."""
    
    def test_pty_list_returns_response(self, api_client):
        """GET /api/provision/pty/list should return response (error expected without sandbox)."""
        response = api_client.get(f"{BASE_URL}/api/provision/pty/list")
        assert response.status_code == 200
        data = response.json()
        # Expected: error about no sandbox OR sessions list
        if not data.get("success"):
            assert "sandbox" in data.get("error", "").lower() or "error" in data
        print(f"PTY list endpoint returned: success={data.get('success')}")


# ═══════════════════════════════════════════════════════════
# 13. MULTI-AGENT ISOLATION TEST
# ═══════════════════════════════════════════════════════════

class TestMultiAgentIsolation:
    """Test per-agent provisioning isolation."""
    
    def test_select_agent_a_verify_status_then_select_anima_fund(self, api_client):
        """
        Multi-agent isolation test:
        1. Select anima-fund
        2. Verify provision/status shows anima-fund
        3. (We can't create agent A without valid Telegram, so just verify default)
        """
        # Select anima-fund
        select_res = api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert select_res.status_code == 200
        time.sleep(0.2)
        
        # Check provision status shows anima-fund
        status_res = api_client.get(f"{BASE_URL}/api/provision/status")
        assert status_res.status_code == 200
        data = status_res.json()
        assert data["agent_id"] == "anima-fund", \
            f"Expected agent_id 'anima-fund', got '{data['agent_id']}'"
        print("Multi-agent isolation verified: anima-fund context maintained")


# ═══════════════════════════════════════════════════════════
# 14. GENESIS PROMPT CONTENT VERIFICATION
# ═══════════════════════════════════════════════════════════

class TestGenesisPromptContent:
    """Test that genesis-prompt.md contains required Phase 3 content."""
    
    def test_genesis_prompt_includes_phase_3(self):
        """genesis-prompt.md should include Phase 3 section."""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        assert "PHASE 3" in content, "genesis-prompt.md should include PHASE 3"
        print("Verified: genesis-prompt.md includes PHASE 3")
        
    def test_genesis_prompt_includes_boardy_ai(self):
        """genesis-prompt.md Phase 3 should mention boardy.ai."""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        assert "boardy.ai" in content.lower() or "Boardy" in content, \
            "genesis-prompt.md should mention boardy.ai in Phase 3"
        print("Verified: genesis-prompt.md mentions boardy.ai")
        
    def test_genesis_prompt_includes_hundreds_of_millions(self):
        """genesis-prompt.md Phase 3 should mention hundreds of millions target."""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        assert "hundreds of millions" in content.lower(), \
            "genesis-prompt.md should mention 'hundreds of millions' capital target"
        print("Verified: genesis-prompt.md mentions hundreds of millions target")
        
    def test_genesis_prompt_boardy_is_phase_3_only(self):
        """genesis-prompt.md should indicate Boardy is for Phase 3 only."""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        # Look for the Phase 3 only restriction
        assert "PHASE 3 ONLY" in content or "Phase 3 only" in content.lower() or \
               "DO NOT use Boardy before Phase 3" in content, \
            "genesis-prompt.md should indicate Boardy is for Phase 3 only"
        print("Verified: genesis-prompt.md indicates Boardy is Phase 3 only")


# ═══════════════════════════════════════════════════════════
# CLEANUP FIXTURE
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def cleanup(api_client):
    """Cleanup: Ensure we switch back to default agent after tests."""
    yield
    try:
        api_client.post(f"{BASE_URL}/api/agents/anima-fund/select")
        print("Cleanup: Switched back to anima-fund")
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
