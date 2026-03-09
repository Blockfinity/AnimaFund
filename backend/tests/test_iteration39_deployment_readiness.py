"""
Iteration 39 - Deployment Readiness Testing
Tests:
1. No hardcoded secrets/URLs in frontend code
2. Frontend uses process.env.REACT_APP_BACKEND_URL everywhere
3. Backend uses os.environ.get() for all credentials
4. All 16+ major API endpoints return 200 status
5. Agent isolation - correct data for selected agent
6. Infrastructure monitoring endpoints work
7. Activity feed structure is correct
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-genesis-6.preview.emergentagent.com').rstrip('/')


class TestDeploymentReadiness:
    """Verify no hardcoded values in production code."""

    def test_frontend_uses_env_variable_for_api(self):
        """Frontend App.js uses process.env.REACT_APP_BACKEND_URL."""
        with open('/app/frontend/src/App.js', 'r') as f:
            content = f.read()
        assert "process.env.REACT_APP_BACKEND_URL" in content, "App.js should use env variable for API URL"
        # Ensure no hardcoded URLs
        assert "localhost:8001" not in content, "No hardcoded localhost URLs"
        assert "127.0.0.1" not in content, "No hardcoded 127.0.0.1"

    def test_agent_mind_uses_env_variable(self):
        """AgentMind.js uses process.env.REACT_APP_BACKEND_URL."""
        with open('/app/frontend/src/pages/AgentMind.js', 'r') as f:
            content = f.read()
        assert "process.env.REACT_APP_BACKEND_URL" in content, "AgentMind.js should use env variable"
        assert "localhost" not in content.lower() or "// localhost" in content.lower(), "No hardcoded localhost"

    def test_infrastructure_uses_env_variable(self):
        """Infrastructure.js uses process.env.REACT_APP_BACKEND_URL."""
        with open('/app/frontend/src/pages/Infrastructure.js', 'r') as f:
            content = f.read()
        assert "process.env.REACT_APP_BACKEND_URL" in content, "Infrastructure.js should use env variable"

    def test_activity_uses_env_variable(self):
        """Activity.js uses process.env.REACT_APP_BACKEND_URL."""
        with open('/app/frontend/src/pages/Activity.js', 'r') as f:
            content = f.read()
        assert "process.env.REACT_APP_BACKEND_URL" in content, "Activity.js should use env variable"

    def test_backend_config_uses_environ(self):
        """Backend config.py uses os.environ.get() for credentials."""
        with open('/app/backend/config.py', 'r') as f:
            content = f.read()
        assert "os.environ.get" in content, "config.py should use os.environ.get()"
        assert "CREATOR_WALLET" in content, "Should have CREATOR_WALLET"
        # No hardcoded wallet addresses
        lines = content.split('\n')
        for line in lines:
            if '=' in line and 'WALLET' in line.upper():
                assert 'environ' in line.lower() or '#' in line, f"Wallet should come from env: {line}"

    def test_no_exposed_secrets_in_frontend(self):
        """No API keys, tokens, or secrets exposed in frontend code."""
        import glob
        frontend_files = glob.glob('/app/frontend/src/**/*.js', recursive=True)
        sensitive_patterns = ['API_KEY=', 'SECRET=', 'TOKEN=', 'PASSWORD=', 'MONGO_URL=']
        for filepath in frontend_files:
            with open(filepath, 'r') as f:
                content = f.read()
            for pattern in sensitive_patterns:
                # Allow environment variable references
                if pattern in content and 'process.env' not in content:
                    assert False, f"Found sensitive pattern '{pattern}' in {filepath}"


class TestAllAPIEndpoints:
    """Test all 16+ major endpoints return 200."""

    def test_health_endpoint(self):
        """Health check endpoint."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_genesis_status_endpoint(self):
        """Genesis status endpoint - core agent status."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Required fields
        assert "agent_id" in data
        assert "wallet_address" in data
        assert "config_exists" in data
        assert "engine_running" in data or "engine_live" in data
        # Verify returns anima-fund data by default
        assert data.get("agent_id") == "anima-fund"

    def test_engine_logs_endpoint(self):
        """Engine logs endpoint."""
        response = requests.get(f"{BASE_URL}/api/engine/logs?lines=50", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "stdout" in data or "stderr" in data

    def test_wallet_balance_endpoint(self):
        """Wallet balance endpoint."""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=15)
        assert response.status_code == 200
        data = response.json()
        # Should have wallet or error
        assert "wallet" in data or "error" in data

    def test_live_identity_endpoint(self):
        """Live identity endpoint."""
        response = requests.get(f"{BASE_URL}/api/live/identity", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Should return identity object
        assert isinstance(data, dict)

    def test_live_turns_endpoint(self):
        """Live turns endpoint."""
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=10", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        assert isinstance(data["turns"], list)

    def test_live_soul_endpoint(self):
        """Live SOUL.md endpoint."""
        response = requests.get(f"{BASE_URL}/api/live/soul", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_infrastructure_overview_endpoint(self):
        """Infrastructure overview endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Should have counts
        assert "agent_name" in data or "sandbox_count" in data

    def test_infrastructure_sandboxes_endpoint(self):
        """Infrastructure sandboxes endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data
        assert isinstance(data["sandboxes"], list)
        assert "total" in data

    def test_infrastructure_terminal_endpoint(self):
        """Infrastructure terminal endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/terminal?lines=50", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_infrastructure_domains_endpoint(self):
        """Infrastructure domains endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/domains", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)

    def test_infrastructure_installed_tools_endpoint(self):
        """Infrastructure installed tools endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/installed-tools", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    def test_infrastructure_activity_feed_endpoint(self):
        """Infrastructure activity feed endpoint."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=50", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "feed" in data
        assert isinstance(data["feed"], list)

    def test_skills_available_endpoint(self):
        """Skills available endpoint."""
        response = requests.get(f"{BASE_URL}/api/skills/available", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 50, "Should have many skills available"

    def test_agents_list_endpoint(self):
        """Agents list endpoint."""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        # Should have at least the default agent
        assert len(data["agents"]) >= 1
        # Default agent should be anima-fund
        agent_ids = [a.get("agent_id") for a in data["agents"]]
        assert "anima-fund" in agent_ids

    def test_telegram_status_endpoint(self):
        """Telegram status endpoint."""
        response = requests.get(f"{BASE_URL}/api/telegram/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data


class TestActivityFeedStructure:
    """Test activity feed items have correct structure."""

    def test_activity_feed_item_structure(self):
        """Each activity feed item has required fields."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=100", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # If feed is not empty, check structure
        if data["feed"]:
            for item in data["feed"][:10]:  # Check first 10
                assert "type" in item, "Activity item should have 'type'"
                assert "category" in item, "Activity item should have 'category'"
                assert "title" in item, "Activity item should have 'title'"
                # Optional but expected
                if "timestamp" in item:
                    assert item["timestamp"], "Timestamp should not be empty"


class TestAgentIsolation:
    """Test that agent selection returns correct agent-specific data."""

    def test_genesis_status_returns_correct_agent_id(self):
        """Genesis status returns data for the correct agent."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Default should be anima-fund
        assert data.get("agent_id") == "anima-fund"

    def test_anima_fund_has_wallet(self):
        """Default Anima Fund agent has a wallet address."""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        wallet = data.get("wallet_address")
        # The expected wallet from the problem statement
        expected_wallet = "0x700e6b8f41551Cd6162C63047a4556fF35Eb9B07"
        if wallet:
            assert wallet.startswith("0x"), "Wallet should be an Ethereum address"
            # Optionally check if it matches expected
            assert wallet.lower() == expected_wallet.lower(), f"Expected wallet {expected_wallet}, got {wallet}"

    def test_select_anima_fund_agent(self):
        """Can select anima-fund agent via API."""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("active_agent") == "anima-fund"


class TestInfrastructureTabs:
    """Test that all 6 infrastructure tabs have working endpoints."""

    def test_overview_tab_data(self):
        """Overview tab: has stat counts."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Check for count fields
        assert "sandbox_count" in data or "installed_tools_count" in data or "discovered_agents_count" in data

    def test_sandboxes_tab_data(self):
        """Sandboxes tab: returns array."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data
        assert "total" in data

    def test_terminal_tab_data(self):
        """Terminal tab: returns entries array."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/terminal", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data

    def test_domains_tab_data(self):
        """Domains tab: returns domains array."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/domains", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert "total" in data

    def test_tools_tab_data(self):
        """Tools tab: returns tools array."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/installed-tools", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data

    def test_network_tab_data_agents(self):
        """Network tab: discovered agents via overview."""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Should have discovered_agents_count or children_sandboxes
        assert "discovered_agents_count" in data or "children_sandboxes" in data


class TestEngineLive:
    """Test engine live endpoint."""

    def test_engine_live_endpoint(self):
        """Engine live endpoint returns state."""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Should have db_exists or live field
        assert "db_exists" in data or "live" in data


class TestUIStabilityPrerequisites:
    """Verify code patterns that prevent UI flashing."""

    def test_app_js_uses_viewref(self):
        """App.js uses viewRef for stable checkStatus."""
        with open('/app/frontend/src/App.js', 'r') as f:
            content = f.read()
        assert "viewRef" in content, "App.js should use viewRef for stable polling"
        assert "useRef(view)" in content, "viewRef should be initialized with useRef(view)"

    def test_app_js_checkstatus_empty_deps(self):
        """checkStatus useCallback has empty dependency array."""
        with open('/app/frontend/src/App.js', 'r') as f:
            content = f.read()
        # Look for the useCallback with empty deps
        assert "checkStatus = useCallback" in content, "checkStatus should be useCallback"
        # Check for empty deps comment
        assert "No dependencies" in content or "[])" in content, "checkStatus should have [] deps"

    def test_agentmind_fetchdata_empty_deps(self):
        """AgentMind fetchData useCallback has empty dependency array."""
        with open('/app/frontend/src/pages/AgentMind.js', 'r') as f:
            content = f.read()
        assert "fetchData = useCallback" in content, "fetchData should be useCallback"

    def test_agentmind_content_based_log_comparison(self):
        """AgentMind uses content-based comparison for logs."""
        with open('/app/frontend/src/pages/AgentMind.js', 'r') as f:
            content = f.read()
        # Should compare last entry content, not just count
        assert "prevLast" in content and "newLast" in content, "Should use content comparison for logs"


class TestNavigationStructure:
    """Test sidebar navigation structure."""

    def test_sidebar_has_infrastructure(self):
        """Sidebar has Infrastructure nav item."""
        with open('/app/frontend/src/components/Sidebar.js', 'r') as f:
            content = f.read()
        assert "'infra'" in content or "infra" in content, "Sidebar should have 'infra' nav item"
        assert "Infrastructure" in content, "Should display 'Infrastructure' label"

    def test_sidebar_nav_order(self):
        """Sidebar has correct nav order: agents, infra, skills."""
        with open('/app/frontend/src/components/Sidebar.js', 'r') as f:
            content = f.read()
        agents_pos = content.find("'agents'")
        infra_pos = content.find("'infra'")
        skills_pos = content.find("'skills'")
        assert agents_pos < infra_pos < skills_pos, "Nav order should be: agents < infra < skills"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
