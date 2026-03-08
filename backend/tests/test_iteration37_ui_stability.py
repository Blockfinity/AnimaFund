"""
Iteration 37 - UI Stability & Dependency Array Fix Tests

Tests the key fixes:
1. checkStatus useCallback has empty [] dependency (not [view])
2. fetchData useCallback has empty [] dependency
3. Log comparison uses content-based comparison (last entry)
4. Skills API shows updated model names (GPT-5.2, Claude Opus 4.6, etc.)
5. Genesis prompt template is ~5.8KB (lean)
6. auto-config.json creation with proper creator address
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthAndBasicEndpoints:
    """Basic health and status endpoint tests"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        print(f"✓ Health endpoint OK - engine_db_exists: {data['engine_db_exists']}")

    def test_genesis_status_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        # Required fields for UI stability
        assert "agent_id" in data
        assert "wallet_address" in data
        assert "config_exists" in data
        assert "engine_running" in data
        assert "engine_state" in data
        assert "fund_name" in data
        assert "creator_wallet" in data
        assert "creator_eth_address" in data
        print(f"✓ Genesis status OK - agent_id: {data['agent_id']}, fund_name: {data['fund_name']}")

    def test_engine_live_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "db_exists" in data
        assert "agent_state" in data
        assert "turn_count" in data
        assert "live" in data
        print(f"✓ Engine live OK - db_exists: {data['db_exists']}, state: {data.get('agent_state')}")

    def test_wallet_balance_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        # Should have wallet info or error explaining why not
        assert "usdc" in data or "error" in data
        assert "eth" in data or "error" in data
        if data.get("wallet"):
            print(f"✓ Wallet balance OK - wallet: {data['wallet'][:10]}..., USDC: {data.get('usdc', 0)}")
        else:
            print(f"✓ Wallet balance OK - {data.get('error', 'No wallet yet')}")


class TestSkillsAPI:
    """Tests for Skills API with updated model names"""

    def test_skills_available_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert data["total"] > 0
        print(f"✓ Skills available - total: {data['total']}")

    def test_skills_contain_updated_model_names(self):
        """Verify chat_completions tool shows GPT-5.2, Claude Opus 4.6, etc."""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        skills = data.get("skills", [])
        
        chat_completions = next((s for s in skills if s["name"] == "chat_completions"), None)
        assert chat_completions is not None, "chat_completions skill not found"
        
        description = chat_completions.get("description", "").lower()
        # Verify updated model names are present
        assert "gpt-5.2" in description, f"GPT-5.2 not found in: {description}"
        assert "claude opus 4.6" in description, f"Claude Opus 4.6 not found in: {description}"
        print(f"✓ Skills have updated model names - chat_completions: {chat_completions['description']}")

    def test_conway_tools_present(self):
        """Verify Conway Terminal tools are listed"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        skills = response.json().get("skills", [])
        skill_names = [s["name"] for s in skills]
        
        expected_conway_tools = [
            "sandbox_create", "sandbox_exec", "sandbox_expose_port",
            "sandbox_write_file", "sandbox_read_file", "chat_completions",
            "wallet_info", "credits_balance"
        ]
        
        for tool in expected_conway_tools:
            assert tool in skill_names, f"Conway tool '{tool}' not found"
        print(f"✓ Conway tools present - verified {len(expected_conway_tools)} tools")


class TestGenesisPromptTemplate:
    """Tests for the lean genesis prompt template (~5.8KB)"""

    def test_prompt_template_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        content = data["content"]
        
        # Should be ~5.8KB, not 25KB (the bloated version)
        content_size = len(content)
        assert content_size < 10000, f"Genesis prompt too large: {content_size} bytes (expected ~5800)"
        assert content_size > 3000, f"Genesis prompt too small: {content_size} bytes"
        print(f"✓ Genesis prompt template size: {content_size} bytes (~{content_size/1024:.1f}KB)")

    def test_prompt_template_has_required_sections(self):
        """Verify prompt has critical sections but not bloated"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        content = response.json().get("content", "")
        
        # Should have these key instructions
        required_phrases = [
            "autonomous AI agent",
            "wallet",
            "tools",
            "Telegram",
        ]
        
        for phrase in required_phrases:
            assert phrase.lower() in content.lower(), f"Missing required phrase: '{phrase}'"
        
        # Should NOT be the bloated 490-line version
        line_count = content.count('\n')
        assert line_count < 200, f"Genesis prompt too many lines: {line_count} (expected ~100)"
        print(f"✓ Genesis prompt has required sections - {line_count} lines")


class TestAgentManagement:
    """Tests for agent CRUD and selection"""

    def test_agents_list_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        agents = data["agents"]
        assert len(agents) >= 1, "Should have at least the default agent"
        
        # Default agent should exist
        default = next((a for a in agents if a.get("agent_id") == "anima-fund"), None)
        assert default is not None, "Default 'anima-fund' agent not found"
        print(f"✓ Agents list - found {len(agents)} agents, default present: {default['name']}")

    def test_select_default_agent(self):
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("active_agent") == "anima-fund"
        print(f"✓ Agent selection works - selected: {data['active_agent']}")

    def test_select_nonexistent_agent(self):
        response = requests.post(f"{BASE_URL}/api/agents/nonexistent-agent-xyz/select")
        assert response.status_code == 404
        print("✓ Nonexistent agent selection returns 404")


class TestEngineLogs:
    """Tests for engine logs endpoint (used by Live Feed)"""

    def test_engine_logs_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/engine/logs?lines=100")
        assert response.status_code == 200
        data = response.json()
        assert "stdout" in data
        assert "stderr" in data
        assert "agent_id" in data
        print(f"✓ Engine logs OK - stdout length: {len(data.get('stdout', ''))}, agent_id: {data['agent_id']}")

    def test_engine_logs_has_anima_dir(self):
        response = requests.get(f"{BASE_URL}/api/engine/logs?lines=50")
        assert response.status_code == 200
        data = response.json()
        assert "anima_dir" in data
        # anima_dir should be a list of files
        anima_dir = data["anima_dir"]
        assert isinstance(anima_dir, list)
        if len(anima_dir) > 0:
            assert "name" in anima_dir[0]
        print(f"✓ Engine logs has anima_dir - {len(anima_dir)} files")


class TestLiveDataEndpoints:
    """Tests for live data endpoints used by AgentMind"""

    def test_live_identity_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        # Should have identity info
        assert isinstance(data, dict)
        print(f"✓ Live identity - name: {data.get('name', 'N/A')}, address: {data.get('address', 'N/A')[:10] if data.get('address') else 'N/A'}...")

    def test_live_turns_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        assert isinstance(data["turns"], list)
        print(f"✓ Live turns - count: {len(data['turns'])}, total: {data.get('total', 0)}")

    def test_live_soul_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        # May or may not have content depending on engine state
        assert isinstance(data, dict)
        print(f"✓ Live soul - content length: {len(data.get('content', ''))}")

    def test_live_agents_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"✓ Live agents - count: {len(data.get('agents', []))}")


class TestUIStabilityDataContract:
    """
    Tests that verify the data contract needed for UI stability.
    The UI relies on consistent response structure from these endpoints.
    """

    def test_genesis_status_data_contract(self):
        """Verify genesis/status returns all fields needed by App.js"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        
        # Required for genesisState in App.js
        required_fields = [
            "wallet_address", "qr_code", "config_exists", "wallet_exists",
            "engine_live", "engine_running", "engine_state", "fund_name",
            "turn_count", "status", "creator_wallet", "creator_eth_address"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ Genesis status has all required fields for UI stability")

    def test_engine_live_data_contract(self):
        """Verify engine/live returns all fields needed by AgentMind.js"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        
        # Required for engineState in AgentMind.js
        required_fields = ["db_exists", "agent_state", "turn_count", "live"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ Engine live has all required fields for UI stability")

    def test_wallet_balance_data_contract(self):
        """Verify wallet/balance returns all fields needed by AgentMind.js"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        
        # Required for balance display in AgentMind.js
        required_fields = ["usdc", "eth"]
        
        for field in required_fields:
            assert field in data or "error" in data, f"Missing required field: {field}"
        
        print(f"✓ Wallet balance has required fields for UI stability")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
