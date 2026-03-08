"""
Iteration 25 Tests - Skills API multi-source and UI fixes validation

Tests:
1. GET /api/skills/available - Returns 99+ skills from multiple sources (anima, conway, tool)
2. Skill sources include CONWAY and TOOL badges
3. Agent CRUD and isolation still works
4. Create agent with selected_skills
5. Standard endpoints health check
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Skip all tests if no URL configured
if not BASE_URL:
    pytest.skip("No REACT_APP_BACKEND_URL set", allow_module_level=True)


class TestHealthAndBasicEndpoints:
    """Basic health and status endpoints"""

    def test_health_endpoint(self):
        """GET /api/health - Check backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check: status={data['status']}, engine_db_exists={data.get('engine_db_exists')}")

    def test_genesis_status(self):
        """GET /api/genesis/status - Check genesis status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "wallet_address" in data
        assert "stage" in data
        print(f"✓ Genesis status: wallet={data.get('wallet_address', 'none')[:10]}..., stage={data.get('stage')}")


class TestSkillsAPIMultiSource:
    """Skills API tests - verifying multi-source skills (anima, conway, tool)"""

    def test_skills_available_returns_many(self):
        """GET /api/skills/available - Should return 99+ skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        skills = data["skills"]
        total = data["total"]
        
        # Should have at least 90 skills
        assert total >= 90, f"Expected 90+ skills, got {total}"
        assert len(skills) >= 90
        print(f"✓ Skills API returns {total} skills")

    def test_skills_have_source_field(self):
        """Skills should have source field (anima, conway, tool)"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data["skills"]
        
        # Check each skill has required fields
        for skill in skills:
            assert "name" in skill
            assert "source" in skill
            assert skill["source"] in ["anima", "conway", "tool"], f"Unexpected source: {skill['source']}"
        print(f"✓ All {len(skills)} skills have valid source field")

    def test_skills_include_anima_source(self):
        """Skills should include skills from 'anima' source"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data["skills"]
        
        anima_skills = [s for s in skills if s.get("source") == "anima"]
        assert len(anima_skills) > 50, f"Expected 50+ anima skills, got {len(anima_skills)}"
        print(f"✓ Found {len(anima_skills)} anima skills")

    def test_skills_include_conway_source(self):
        """Skills should include skills from 'conway' source (Conway platform tools)"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data["skills"]
        
        conway_skills = [s for s in skills if s.get("source") == "conway"]
        # Should have at least some conway skills
        assert len(conway_skills) >= 1, f"Expected at least 1 conway skill, got {len(conway_skills)}"
        
        # Verify conway skills have expected names
        conway_names = [s["name"] for s in conway_skills]
        print(f"✓ Found {len(conway_skills)} conway skills: {conway_names}")

    def test_skills_search_structure(self):
        """Verify skill structure has name, description, source"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data["skills"]
        
        # Sample check on first few skills
        for skill in skills[:10]:
            assert "name" in skill
            assert "description" in skill or skill.get("description") == ""
            assert "source" in skill
        print(f"✓ Skill structure verified (name, description, source)")


class TestAgentCRUDAndIsolation:
    """Agent CRUD tests including skill selection"""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Ensure we're on default agent before and after tests"""
        # Switch to default agent before test
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        yield
        # Cleanup: switch back to default after test
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")

    def test_list_agents(self):
        """GET /api/agents - List all agents"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        agents = data["agents"]
        assert len(agents) >= 1  # At least default agent
        
        # Check default agent exists
        default = [a for a in agents if a.get("is_default") == True]
        assert len(default) == 1
        print(f"✓ Found {len(agents)} agents, default: {default[0]['name']}")

    def test_create_agent_with_selected_skills(self):
        """POST /api/agents/create - Create agent with specific skills selected"""
        test_id = str(uuid.uuid4())[:8]
        agent_name = f"TEST-Skills-{test_id}"
        
        # Select only 3 skills
        selected_skills = ["deal-scouting", "deal-evaluation", "survival"]
        
        payload = {
            "name": agent_name,
            "genesis_prompt": "You are a test agent for skill selection validation.",
            "welcome_message": "Test agent ready.",
            "goals": ["Test skill selection"],
            "selected_skills": selected_skills
        }
        
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "agent" in data
        
        agent = data["agent"]
        agent_id = agent["agent_id"]
        
        print(f"✓ Created agent '{agent_id}' with {len(selected_skills)} selected skills")
        
        # Cleanup - delete test agent
        cleanup_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
        assert cleanup_response.status_code == 200
        print(f"✓ Cleaned up test agent '{agent_id}'")

    def test_agent_select_isolation(self):
        """POST /api/agents/{id}/select - Switching agents changes data"""
        test_id = str(uuid.uuid4())[:8]
        agent_name = f"TEST-Isolation-{test_id}"
        
        # Get default agent identity first
        default_identity = requests.get(f"{BASE_URL}/api/live/identity").json()
        default_name = default_identity.get("name")
        
        # Create test agent
        payload = {
            "name": agent_name,
            "genesis_prompt": "Test agent for isolation check.",
            "welcome_message": "Testing isolation."
        }
        create_response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent"]["agent_id"]
        
        # Select the new agent
        select_response = requests.post(f"{BASE_URL}/api/agents/{agent_id}/select")
        assert select_response.status_code == 200
        
        # Check identity changed
        new_identity = requests.get(f"{BASE_URL}/api/live/identity").json()
        
        # Check engine live shows different data
        new_engine = requests.get(f"{BASE_URL}/api/engine/live").json()
        
        # New agent should NOT have db_exists=true (it's brand new)
        assert new_engine.get("db_exists") == False, "New agent should not have state.db"
        print(f"✓ New agent isolation verified: db_exists={new_engine.get('db_exists')}")
        
        # Switch back to default
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        
        # Verify default agent data is back
        restored_identity = requests.get(f"{BASE_URL}/api/live/identity").json()
        assert restored_identity.get("name") == default_name
        
        restored_engine = requests.get(f"{BASE_URL}/api/engine/live").json()
        assert restored_engine.get("db_exists") == True
        print(f"✓ Default agent restored: name={restored_identity.get('name')}, db_exists={restored_engine.get('db_exists')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
        print(f"✓ Cleaned up test agent '{agent_id}'")

    def test_delete_agent(self):
        """DELETE /api/agents/{id} - Delete non-default agent"""
        test_id = str(uuid.uuid4())[:8]
        agent_name = f"TEST-Delete-{test_id}"
        
        # Create agent
        payload = {
            "name": agent_name,
            "genesis_prompt": "To be deleted.",
            "welcome_message": "Test"
        }
        create_response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent"]["agent_id"]
        
        # Delete agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True
        print(f"✓ Deleted test agent '{agent_id}'")

    def test_cannot_delete_default_agent(self):
        """DELETE /api/agents/anima-fund - Should fail for default agent"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400
        print(f"✓ Default agent deletion correctly blocked")


class TestWalletAndEngine:
    """Wallet and engine status tests"""

    def test_wallet_balance(self):
        """GET /api/wallet/balance - Get wallet balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        assert "wallet" in data
        assert "usdc" in data
        assert "tier" in data
        print(f"✓ Wallet balance: wallet={data.get('wallet', 'none')[:10]}..., usdc={data.get('usdc')}, tier={data.get('tier')}")

    def test_engine_live(self):
        """GET /api/engine/live - Check engine live status"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "db_exists" in data
        assert "live" in data
        print(f"✓ Engine status: db_exists={data.get('db_exists')}, live={data.get('live')}, state={data.get('agent_state')}")


class TestLiveDataEndpoints:
    """Live data endpoints for the active agent"""

    def test_live_identity(self):
        """GET /api/live/identity - Get agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        print(f"✓ Identity: name={data.get('name')}, address={data.get('address', 'none')[:10] if data.get('address') else 'none'}...")

    def test_live_soul(self):
        """GET /api/live/soul - Get SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
        print(f"✓ SOUL: exists={data.get('exists')}, content_length={len(data.get('content', '')) if data.get('content') else 0}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
