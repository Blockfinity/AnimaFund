"""
Test Suite for Iteration 26 - Major Skills Overhaul

Tests:
1. Skills API returns 140+ skills from 9+ sources
2. ClawHub skills marked as 'installed=false' (available for install)
3. All core endpoints working (health, agents, genesis, wallet, live, engine)
4. Multi-source skill selection in agent creation
5. Agent isolation (select, delete)
"""

import pytest
import requests
import os
import time
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-genesis-6.preview.emergentagent.com').rstrip('/')


class TestSkillsAPI:
    """Test the enhanced skills/available endpoint - 141 skills from 9 sources"""

    def test_skills_endpoint_returns_140_plus_skills(self):
        """Verify skills API returns 140+ skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'skills' in data, "Response should contain 'skills' array"
        assert 'total' in data, "Response should contain 'total' count"
        
        total_skills = data['total']
        assert total_skills >= 140, f"Expected 140+ skills, got {total_skills}"
        print(f"Total skills: {total_skills}")

    def test_skills_have_source_field(self):
        """All skills should have a 'source' field"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skills = data['skills']
        
        for skill in skills:
            assert 'source' in skill, f"Skill {skill.get('name')} missing 'source' field"
            assert skill['source'], f"Skill {skill.get('name')} has empty source"

    def test_nine_plus_sources_present(self):
        """Verify 9+ distinct sources exist"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        sources = set(s['source'] for s in data['skills'])
        
        print(f"Sources found: {sorted(sources)}")
        assert len(sources) >= 9, f"Expected 9+ sources, got {len(sources)}: {sources}"
        
        # Verify expected sources are present
        expected_sources = ['anima', 'clawhub', 'openclaw', 'conway-cloud', 'conway-compute', 
                          'conway-domains', 'conway-x402', 'conway-credits']
        for expected in expected_sources:
            assert expected in sources, f"Source '{expected}' not found in {sources}"

    def test_anima_skills_present(self):
        """Verify Anima Fund custom skills are present"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        anima_skills = [s for s in data['skills'] if s['source'] == 'anima']
        
        print(f"Anima skills count: {len(anima_skills)}")
        assert len(anima_skills) >= 80, f"Expected 80+ anima skills, got {len(anima_skills)}"

    def test_conway_cloud_tools_present(self):
        """Verify Conway Cloud tools are present"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        conway_cloud_skills = [s for s in data['skills'] if s['source'] == 'conway-cloud']
        
        expected_tools = ['sandbox_create', 'sandbox_exec', 'sandbox_expose_port']
        found_names = [s['name'] for s in conway_cloud_skills]
        
        for tool in expected_tools:
            assert tool in found_names, f"Conway Cloud tool '{tool}' not found"
        print(f"Conway Cloud tools found: {found_names}")

    def test_openclaw_tools_present(self):
        """Verify OpenClaw built-in tools are present"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        openclaw_skills = [s for s in data['skills'] if s['source'] == 'openclaw']
        
        expected_tools = ['browse_page', 'browser', 'discover_agents', 'send_message', 'create_skill']
        found_names = [s['name'] for s in openclaw_skills]
        
        for tool in expected_tools:
            assert tool in found_names, f"OpenClaw tool '{tool}' not found"
        print(f"OpenClaw tools found: {found_names}")

    def test_clawhub_skills_marked_not_installed(self):
        """ClawHub marketplace skills should have installed=false"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        clawhub_skills = [s for s in data['skills'] if s['source'] == 'clawhub']
        
        assert len(clawhub_skills) >= 10, f"Expected 10+ ClawHub skills, got {len(clawhub_skills)}"
        
        for skill in clawhub_skills:
            assert skill.get('installed') == False, f"ClawHub skill '{skill['name']}' should have installed=false"
        
        print(f"ClawHub skills (all marked not installed): {[s['name'] for s in clawhub_skills]}")

    def test_non_clawhub_skills_marked_installed(self):
        """Non-ClawHub skills should have installed=true"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        non_clawhub_skills = [s for s in data['skills'] if s['source'] != 'clawhub']
        
        for skill in non_clawhub_skills:
            assert skill.get('installed') == True, f"Non-ClawHub skill '{skill['name']}' (source={skill['source']}) should be installed"


class TestCoreEndpoints:
    """Test all core API endpoints"""

    def test_health_endpoint(self):
        """Test GET /api/health"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('status') == 'ok', f"Health check failed: {data}"
        print(f"Health: {data}")

    def test_agents_list(self):
        """Test GET /api/agents"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert 'agents' in data
        agents = data['agents']
        assert len(agents) >= 1, "Should have at least one agent (anima-fund)"
        
        # Default agent should exist
        agent_ids = [a['agent_id'] for a in agents]
        assert 'anima-fund' in agent_ids, "Default anima-fund agent not found"
        print(f"Agents: {agent_ids}")

    def test_genesis_status(self):
        """Test GET /api/genesis/status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'wallet_address' in data, "Should have wallet_address"
        assert 'stage' in data or 'status' in data, "Should have stage or status"
        print(f"Genesis status: wallet={data.get('wallet_address')}, stage={data.get('stage')}")

    def test_wallet_balance(self):
        """Test GET /api/wallet/balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert 'wallet' in data, "Should have wallet address"
        assert 'usdc' in data, "Should have usdc balance"
        assert 'tier' in data, "Should have tier"
        print(f"Wallet balance: wallet={data.get('wallet')}, usdc=${data.get('usdc')}, tier={data.get('tier')}")

    def test_live_identity(self):
        """Test GET /api/live/identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        
        data = response.json()
        assert 'name' in data, "Should have name"
        assert 'address' in data, "Should have address"
        print(f"Identity: name={data.get('name')}, address={data.get('address')}")

    def test_live_soul(self):
        """Test GET /api/live/soul"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        
        data = response.json()
        assert 'content' in data, "Should have content field"
        assert len(data['content']) > 100, "Soul content should have substantial text"
        print(f"Soul content length: {len(data['content'])} chars")

    def test_engine_live(self):
        """Test GET /api/engine/live"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        
        data = response.json()
        assert 'db_exists' in data, "Should have db_exists field"
        assert 'fund_name' in data, "Should have fund_name field"
        print(f"Engine live: db_exists={data.get('db_exists')}, state={data.get('agent_state')}")


class TestAgentCreationWithSkills:
    """Test agent creation with multi-source skill selection"""

    @pytest.fixture(autouse=True)
    def cleanup_test_agent(self):
        """Clean up test agent after each test"""
        yield
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/agents/test-skills-agent-26")
        except:
            pass

    def test_create_agent_with_selected_skills(self):
        """Test POST /api/agents/create with skills from different sources"""
        # Select skills from different sources
        selected_skills = [
            'deal-evaluation',      # anima
            'sandbox_create',       # conway-cloud
            'browse_page',          # openclaw
            'web-browsing',         # clawhub
        ]
        
        payload = {
            "name": "Test Skills Agent 26",
            "genesis_prompt": "You are a test agent for iteration 26 skill selection testing.",
            "welcome_message": "Test agent activated.",
            "goals": ["Test multi-source skills"],
            "selected_skills": selected_skills,
        }
        
        response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert data.get('success') == True, f"Create not successful: {data}"
        assert data.get('agent', {}).get('agent_id') == 'test-skills-agent-26'
        print(f"Created agent with skills from multiple sources: {selected_skills}")
        
        # Cleanup
        delete_response = requests.delete(f"{BASE_URL}/api/agents/test-skills-agent-26")
        assert delete_response.status_code == 200


class TestAgentIsolation:
    """Test agent isolation - select and delete"""

    @pytest.fixture(autouse=True)
    def cleanup_test_agents(self):
        """Clean up test agents after each test"""
        yield
        for agent_id in ['test-isolation-agent-26', 'test-isolation-agent-26-b']:
            try:
                requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
            except:
                pass

    def test_select_default_agent(self):
        """Test selecting the default anima-fund agent"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get('success') == True
        assert data.get('active_agent') == 'anima-fund'
        print(f"Selected default agent: {data}")

    def test_create_select_and_delete_agent(self):
        """Test full agent lifecycle: create -> select -> delete"""
        # Create
        payload = {
            "name": "Test Isolation Agent 26",
            "genesis_prompt": "Test agent for isolation testing.",
            "selected_skills": ['deal-evaluation'],
        }
        create_response = requests.post(f"{BASE_URL}/api/agents/create", json=payload)
        assert create_response.status_code == 200
        
        agent_id = create_response.json()['agent']['agent_id']
        assert agent_id == 'test-isolation-agent-26'
        
        # Select
        select_response = requests.post(f"{BASE_URL}/api/agents/{agent_id}/select")
        assert select_response.status_code == 200
        assert select_response.json().get('active_agent') == agent_id
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
        assert delete_response.status_code == 200
        assert delete_response.json().get('success') == True
        
        # Verify deleted
        select_again = requests.post(f"{BASE_URL}/api/agents/{agent_id}/select")
        assert select_again.status_code == 404, "Deleted agent should not be selectable"
        
        print("Agent isolation test passed: create -> select -> delete -> verify deleted")

    def test_cannot_delete_default_agent(self):
        """Test that default agent cannot be deleted"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400, f"Should not be able to delete default agent, got {response.status_code}"
        print("Correctly prevented deletion of default agent")


class TestSkillSourceCounts:
    """Verify skill counts by source match expected values"""

    def test_source_distribution(self):
        """Verify skill distribution across sources"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        sources = {}
        for skill in data['skills']:
            src = skill['source']
            sources[src] = sources.get(src, 0) + 1
        
        print("\nSkill distribution:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"  {src}: {count}")
        
        # Expected minimums
        assert sources.get('anima', 0) >= 80, "Should have 80+ anima skills"
        assert sources.get('clawhub', 0) >= 10, "Should have 10+ clawhub skills"
        assert sources.get('openclaw', 0) >= 10, "Should have 10+ openclaw skills"
        assert sources.get('conway-cloud', 0) >= 5, "Should have 5+ conway-cloud tools"
        assert sources.get('conway-compute', 0) >= 1, "Should have 1+ conway-compute tools"
        assert sources.get('conway-domains', 0) >= 2, "Should have 2+ conway-domains tools"
        assert sources.get('conway-x402', 0) >= 2, "Should have 2+ conway-x402 tools"
        assert sources.get('conway-credits', 0) >= 2, "Should have 2+ conway-credits tools"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
