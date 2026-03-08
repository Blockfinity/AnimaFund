"""
Iteration 19 Tests: Skill Selector, New Gambling Skills, Parallel Execution
Testing:
- GET /api/skills/available returns 95 skills including gambling-mastery and rainbet-betting-mastery
- POST /api/agents/create with selected_skills=['gambling-mastery','rainbet-betting-mastery'] creates agent with ONLY those 2 skills
- POST /api/agents/create with selected_skills=[] (empty) copies ALL skills
- GET /api/agents returns agents list
- All existing endpoints still work
- Genesis prompt contains PARALLEL EXECUTION instructions
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSkillsAvailable:
    """Test /api/skills/available endpoint"""
    
    def test_get_skills_returns_95_skills(self):
        """Verify endpoint returns 95 skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "skills" in data, "Response missing 'skills' field"
        assert "total" in data, "Response missing 'total' field"
        assert data["total"] == 95, f"Expected 95 skills, got {data['total']}"
        assert len(data["skills"]) == 95, f"Expected 95 skills in list, got {len(data['skills'])}"
    
    def test_skills_contain_gambling_mastery(self):
        """Verify gambling-mastery skill is present"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skill_names = [s["name"] for s in data["skills"]]
        assert "gambling-mastery" in skill_names, "gambling-mastery skill not found"
        
        # Find and verify description
        gambling_skill = next((s for s in data["skills"] if s["name"] == "gambling-mastery"), None)
        assert gambling_skill is not None
        assert gambling_skill["description"], "gambling-mastery should have a description"
        assert "gambling" in gambling_skill["description"].lower(), "Description should mention gambling"
    
    def test_skills_contain_rainbet_betting_mastery(self):
        """Verify rainbet-betting-mastery skill is present"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skill_names = [s["name"] for s in data["skills"]]
        assert "rainbet-betting-mastery" in skill_names, "rainbet-betting-mastery skill not found"
        
        # Find and verify description
        rainbet_skill = next((s for s in data["skills"] if s["name"] == "rainbet-betting-mastery"), None)
        assert rainbet_skill is not None
        assert rainbet_skill["description"], "rainbet-betting-mastery should have a description"
    
    def test_each_skill_has_name_and_description(self):
        """Verify each skill has name and description fields"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        for skill in data["skills"]:
            assert "name" in skill, f"Skill missing 'name' field: {skill}"
            assert isinstance(skill["name"], str), "Skill name should be a string"
            assert len(skill["name"]) > 0, "Skill name should not be empty"
            assert "description" in skill, f"Skill missing 'description' field: {skill}"


class TestAgentCreationWithSelectedSkills:
    """Test agent creation with selected_skills parameter"""
    
    @pytest.fixture(autouse=True)
    def cleanup_test_agents(self):
        """Cleanup test agents after each test"""
        yield
        # Cleanup
        for agent_id in ["test-skills-selected", "test-skills-all", "test-skills-empty"]:
            try:
                requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
            except:
                pass
    
    def test_create_agent_with_selected_skills_only(self):
        """Create agent with only gambling-mastery and rainbet-betting-mastery skills"""
        agent_data = {
            "name": "Test Skills Selected",
            "genesis_prompt": "Test agent for skill selection verification.",
            "welcome_message": "Testing skill selector",
            "goals": [],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50,
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "selected_skills": ["gambling-mastery", "rainbet-betting-mastery"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True, f"Creation failed: {data}"
        assert "agent" in data
        
        agent = data["agent"]
        assert agent["agent_id"] == "test-skills-selected"
        assert agent["name"] == "Test Skills Selected"
        
        # Verify only selected skills were copied by checking the directory
        agent_home = os.path.expanduser(agent["agent_home"])
        skills_dir = os.path.join(agent_home, ".automaton", "skills")
        
        if os.path.exists(skills_dir):
            copied_skills = os.listdir(skills_dir)
            assert len(copied_skills) == 2, f"Expected 2 skills, got {len(copied_skills)}: {copied_skills}"
            assert "gambling-mastery" in copied_skills, "gambling-mastery not in copied skills"
            assert "rainbet-betting-mastery" in copied_skills, "rainbet-betting-mastery not in copied skills"
            
            # Verify SKILL.md files exist
            assert os.path.exists(os.path.join(skills_dir, "gambling-mastery", "SKILL.md"))
            assert os.path.exists(os.path.join(skills_dir, "rainbet-betting-mastery", "SKILL.md"))
    
    def test_create_agent_with_empty_selected_skills_copies_all(self):
        """Create agent with empty selected_skills copies ALL 95 skills"""
        agent_data = {
            "name": "Test Skills All",
            "genesis_prompt": "Test agent for all skills copy.",
            "welcome_message": "Testing all skills",
            "goals": [],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50,
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "selected_skills": []  # Empty = copy all
        }
        
        response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
        
        agent = data["agent"]
        agent_home = os.path.expanduser(agent["agent_home"])
        skills_dir = os.path.join(agent_home, ".automaton", "skills")
        
        if os.path.exists(skills_dir):
            copied_skills = os.listdir(skills_dir)
            assert len(copied_skills) == 95, f"Expected 95 skills, got {len(copied_skills)}"
            # Verify new gambling skills are included
            assert "gambling-mastery" in copied_skills
            assert "rainbet-betting-mastery" in copied_skills
    
    def test_create_agent_without_selected_skills_field_copies_all(self):
        """Create agent without selected_skills field should copy all skills (default behavior)"""
        agent_data = {
            "name": "Test Skills Empty",
            "genesis_prompt": "Test agent without selected_skills field.",
            "welcome_message": "Testing default behavior"
            # No selected_skills field - should default to []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
        
        agent = data["agent"]
        agent_home = os.path.expanduser(agent["agent_home"])
        skills_dir = os.path.join(agent_home, ".automaton", "skills")
        
        if os.path.exists(skills_dir):
            copied_skills = os.listdir(skills_dir)
            assert len(copied_skills) == 95, f"Expected 95 skills (all), got {len(copied_skills)}"


class TestExistingEndpoints:
    """Verify all existing endpoints still work"""
    
    def test_health_check(self):
        """Health endpoint works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_get_agents_list(self):
        """GET /api/agents returns list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        # Should have at least the default anima-fund agent
        agent_ids = [a["agent_id"] for a in data["agents"]]
        assert "anima-fund" in agent_ids, "Default agent should exist"
    
    def test_genesis_status(self):
        """GET /api/genesis/status works"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "creator_wallet" in data
    
    def test_engine_status(self):
        """GET /api/engine/status works and shows 95 skills"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) == 95, f"Expected 95 skills, got {len(data['skills'])}"
        assert "gambling-mastery" in data["skills"]
        assert "rainbet-betting-mastery" in data["skills"]
    
    def test_engine_live(self):
        """GET /api/engine/live works"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
    
    def test_select_default_agent(self):
        """POST /api/agents/anima-fund/select works"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["active_agent"] == "anima-fund"


class TestGamblingSkillsContent:
    """Verify gambling skill SKILL.md files have correct content"""
    
    def test_gambling_mastery_skill_file_exists(self):
        """gambling-mastery SKILL.md exists and has content"""
        skill_path = "/app/automaton/skills/gambling-mastery/SKILL.md"
        assert os.path.exists(skill_path), f"File not found: {skill_path}"
        
        with open(skill_path, 'r') as f:
            content = f.read()
        
        assert len(content) > 100, "SKILL.md should have substantial content"
        assert "name: gambling-mastery" in content
        assert "description:" in content
    
    def test_rainbet_betting_mastery_skill_file_exists(self):
        """rainbet-betting-mastery SKILL.md exists and has content"""
        skill_path = "/app/automaton/skills/rainbet-betting-mastery/SKILL.md"
        assert os.path.exists(skill_path), f"File not found: {skill_path}"
        
        with open(skill_path, 'r') as f:
            content = f.read()
        
        assert len(content) > 100, "SKILL.md should have substantial content"
        assert "name: rainbet-betting-mastery" in content
        assert "description:" in content


class TestGenesisPromptParallelExecution:
    """Verify genesis prompt contains PARALLEL EXECUTION instructions"""
    
    def test_genesis_prompt_has_parallel_execution_section(self):
        """Genesis prompt must contain PARALLEL EXECUTION section"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        assert os.path.exists(genesis_path), "genesis-prompt.md not found"
        
        with open(genesis_path, 'r') as f:
            content = f.read()
        
        assert "PARALLEL EXECUTION" in content, "Missing PARALLEL EXECUTION section"
        
        # Verify specific parallel execution instructions
        assert "create multiple goals simultaneously" in content.lower() or "Create multiple goals" in content
        assert "spawn" in content.lower() or "Spawn" in content
        assert "child" in content.lower() or "children" in content.lower()
    
    def test_genesis_prompt_parallel_execution_has_instructions(self):
        """Verify PARALLEL EXECUTION section has specific instructions"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        
        with open(genesis_path, 'r') as f:
            content = f.read()
        
        # Check for key parallel execution concepts
        assert "create_goal" in content, "Should mention create_goal for parallel goals"
        assert "spawn_child" in content, "Should mention spawn_child for child agents"
        assert "code_execution" in content, "Should mention code_execution for concurrent scripts"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
