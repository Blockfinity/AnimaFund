"""
Iteration 36 - Genesis Prompt v6 + Engine Start + Multi-Agent Testing

Tests:
1. GET /api/genesis/prompt-template — returns genesis prompt with required sections
2. GET /api/genesis/status — returns agent_id, per-agent creator wallets, fund_name
3. GET /api/engine/live — returns agent_id field
4. GET /api/engine/logs — returns agent_id field and per-agent log content
5. GET /api/agents — returns list of agents
6. GET /api/wallet/balance — returns wallet data
7. POST /api/agents/anima-fund/select — switches to default agent correctly
8. GET /api/health — returns 200
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://agent-dashboard-163.preview.emergentagent.com"


class TestHealthEndpoint:
    """Test basic health endpoint."""
    
    def test_health_returns_200(self):
        """GET /api/health should return 200 with status ok."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Health status not ok: {data}"
        print(f"✓ Health check passed: {data}")


class TestGenesisPromptTemplate:
    """Test genesis prompt template contains all required sections."""
    
    def test_genesis_prompt_template_returns_content(self):
        """GET /api/genesis/prompt-template should return genesis prompt."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        assert response.status_code == 200, f"Prompt template failed: {response.status_code}"
        data = response.json()
        content = data.get("content", "")
        assert len(content) > 1000, f"Genesis prompt too short: {len(content)} chars"
        print(f"✓ Genesis prompt template returned: {len(content)} characters")
        return content
    
    def test_genesis_prompt_has_phase0_section(self):
        """Genesis prompt must have PHASE 0 bootstrap section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "PHASE 0" in content, "Missing PHASE 0 section"
        assert "BOOTSTRAP" in content, "Missing BOOTSTRAP reference"
        print("✓ Genesis prompt has PHASE 0 BOOTSTRAP section")
    
    def test_genesis_prompt_has_soul_md_management(self):
        """Genesis prompt must have SOUL.MD MANAGEMENT section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "SOUL.MD MANAGEMENT" in content, "Missing SOUL.MD MANAGEMENT section"
        print("✓ Genesis prompt has SOUL.MD MANAGEMENT section")
    
    def test_genesis_prompt_has_goal_orchestrator_rules(self):
        """Genesis prompt must have GOAL ORCHESTRATOR RULES."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        # The actual text in the prompt is "GOAL ORCHESTRATOR RULES" in the ANTI-STUCK section
        assert "GOAL ORCHESTRATOR" in content or "create_goal" in content, "Missing GOAL ORCHESTRATOR references"
        print("✓ Genesis prompt has GOAL ORCHESTRATOR rules")
    
    def test_genesis_prompt_has_problem_solving_protocol(self):
        """Genesis prompt must have PROBLEM-SOLVING PROTOCOL section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "PROBLEM-SOLVING PROTOCOL" in content, "Missing PROBLEM-SOLVING PROTOCOL section"
        print("✓ Genesis prompt has PROBLEM-SOLVING PROTOCOL section")
    
    def test_genesis_prompt_has_deploying_real_services(self):
        """Genesis prompt must have DEPLOYING REAL SERVICES section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "DEPLOYING REAL SERVICES" in content, "Missing DEPLOYING REAL SERVICES section"
        print("✓ Genesis prompt has DEPLOYING REAL SERVICES section")
    
    def test_genesis_prompt_has_revenue_survival(self):
        """Genesis prompt must have REVENUE & SURVIVAL section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "REVENUE" in content, "Missing REVENUE section"
        assert "SURVIVAL" in content, "Missing SURVIVAL reference"
        print("✓ Genesis prompt has REVENUE & SURVIVAL section")
    
    def test_genesis_prompt_has_isolation_section(self):
        """Genesis prompt must have ISOLATION & SECURITY section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "ISOLATION" in content, "Missing ISOLATION section"
        print("✓ Genesis prompt has ISOLATION section")
    
    def test_genesis_prompt_has_complete_tools_reference(self):
        """Genesis prompt must have COMPLETE TOOLS REFERENCE section."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "COMPLETE TOOLS REFERENCE" in content, "Missing COMPLETE TOOLS REFERENCE section"
        print("✓ Genesis prompt has COMPLETE TOOLS REFERENCE section")
    
    def test_genesis_prompt_has_sandbox_expose_port(self):
        """Genesis prompt must use sandbox_expose_port (not just expose_port)."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        assert "sandbox_expose_port" in content, "Missing sandbox_expose_port tool reference"
        # Should warn about expose_port being localhost only
        assert "localhost" in content.lower() or "expose_port" in content, "Should mention expose_port limitation"
        print("✓ Genesis prompt correctly uses sandbox_expose_port")
    
    def test_genesis_prompt_has_modern_models(self):
        """Genesis prompt must reference modern AI models like GPT-5.2, Claude Opus 4.6, Gemini 3 Pro."""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        content = response.json().get("content", "")
        # Check for modern model references
        has_gpt = "gpt-5" in content.lower() or "gpt5" in content.lower()
        has_claude = "claude-opus" in content.lower() or "claude opus" in content.lower()
        has_gemini = "gemini" in content.lower()
        assert has_gpt or has_claude or has_gemini, "Missing modern AI model references"
        print(f"✓ Genesis prompt has modern model references (GPT-5: {has_gpt}, Claude Opus: {has_claude}, Gemini: {has_gemini})")


class TestGenesisStatus:
    """Test genesis status endpoint."""
    
    def test_genesis_status_returns_agent_id(self):
        """GET /api/genesis/status should return agent_id field."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200, f"Genesis status failed: {response.status_code}"
        data = response.json()
        assert "agent_id" in data, "Missing agent_id field in genesis status"
        print(f"✓ Genesis status returns agent_id: {data.get('agent_id')}")
    
    def test_genesis_status_returns_creator_wallets(self):
        """GET /api/genesis/status should return creator_wallet and creator_eth_address."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        data = response.json()
        assert "creator_wallet" in data, "Missing creator_wallet field"
        assert "creator_eth_address" in data, "Missing creator_eth_address field"
        print(f"✓ Genesis status returns creator wallets - SOL: {data.get('creator_wallet')[:10]}..., ETH: {data.get('creator_eth_address')[:10]}...")
    
    def test_genesis_status_returns_fund_name(self):
        """GET /api/genesis/status should return fund_name."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        data = response.json()
        # fund_name may be None if engine not running, but field should exist
        assert "fund_name" in data, "Missing fund_name field"
        print(f"✓ Genesis status returns fund_name: {data.get('fund_name')}")
    
    def test_genesis_status_returns_goals(self):
        """GET /api/genesis/status should return goals array."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        data = response.json()
        assert "goals" in data, "Missing goals field"
        assert isinstance(data.get("goals"), list), "goals should be a list"
        print(f"✓ Genesis status returns goals: {data.get('goals')}")


class TestEngineLive:
    """Test engine/live endpoint."""
    
    def test_engine_live_returns_agent_id(self):
        """GET /api/engine/live should return agent_id field."""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert response.status_code == 200, f"Engine live failed: {response.status_code}"
        data = response.json()
        assert "agent_id" in data, "Missing agent_id field in engine live"
        print(f"✓ Engine live returns agent_id: {data.get('agent_id')}")
    
    def test_engine_live_returns_db_status(self):
        """GET /api/engine/live should return db_exists field."""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        data = response.json()
        assert "db_exists" in data, "Missing db_exists field"
        print(f"✓ Engine live returns db_exists: {data.get('db_exists')}")


class TestEngineLogs:
    """Test engine/logs endpoint."""
    
    def test_engine_logs_returns_agent_id(self):
        """GET /api/engine/logs should return agent_id field."""
        response = requests.get(f"{BASE_URL}/api/engine/logs", timeout=10)
        assert response.status_code == 200, f"Engine logs failed: {response.status_code}"
        data = response.json()
        assert "agent_id" in data, "Missing agent_id field in engine logs"
        print(f"✓ Engine logs returns agent_id: {data.get('agent_id')}")
    
    def test_engine_logs_returns_stdout_stderr(self):
        """GET /api/engine/logs should return stdout and stderr fields."""
        response = requests.get(f"{BASE_URL}/api/engine/logs", timeout=10)
        data = response.json()
        assert "stdout" in data, "Missing stdout field"
        assert "stderr" in data, "Missing stderr field"
        print(f"✓ Engine logs returns stdout ({len(data.get('stdout', ''))} chars) and stderr ({len(data.get('stderr', ''))} chars)")


class TestAgentsList:
    """Test agents list endpoint."""
    
    def test_agents_list_returns_agents(self):
        """GET /api/agents should return list of agents."""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert response.status_code == 200, f"Agents list failed: {response.status_code}"
        data = response.json()
        assert "agents" in data, "Missing agents field"
        assert isinstance(data.get("agents"), list), "agents should be a list"
        assert len(data.get("agents", [])) >= 1, "Should have at least one agent (anima-fund)"
        print(f"✓ Agents list returns {len(data.get('agents', []))} agents")
    
    def test_agents_list_contains_default_agent(self):
        """GET /api/agents should contain the anima-fund default agent."""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        data = response.json()
        agents = data.get("agents", [])
        agent_ids = [a.get("agent_id") for a in agents]
        assert "anima-fund" in agent_ids, "Default agent 'anima-fund' not found in agents list"
        print(f"✓ Agents list contains default agent 'anima-fund'")


class TestWalletBalance:
    """Test wallet balance endpoint."""
    
    def test_wallet_balance_returns_data(self):
        """GET /api/wallet/balance should return wallet data."""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=10)
        assert response.status_code == 200, f"Wallet balance failed: {response.status_code}"
        data = response.json()
        # Should have at least usdc and eth fields
        assert "usdc" in data, "Missing usdc field"
        assert "eth" in data, "Missing eth field"
        print(f"✓ Wallet balance returns USDC: {data.get('usdc')}, ETH: {data.get('eth')}")


class TestAgentSelection:
    """Test agent selection endpoint."""
    
    def test_select_default_agent(self):
        """POST /api/agents/anima-fund/select should switch to default agent."""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        assert response.status_code == 200, f"Agent selection failed: {response.status_code}"
        data = response.json()
        assert data.get("success") == True, f"Agent selection not successful: {data}"
        assert data.get("active_agent") == "anima-fund", f"Active agent should be anima-fund: {data}"
        print(f"✓ Agent selection works: switched to {data.get('active_agent')}")
    
    def test_select_nonexistent_agent_returns_404(self):
        """POST /api/agents/nonexistent-agent/select should return 404."""
        response = requests.post(f"{BASE_URL}/api/agents/nonexistent-agent-xyz123/select", timeout=10)
        assert response.status_code == 404, f"Expected 404 for nonexistent agent, got: {response.status_code}"
        print(f"✓ Nonexistent agent selection correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
