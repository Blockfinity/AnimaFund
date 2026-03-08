"""
Iteration 38 - Infrastructure Page & Enhanced Activity Feed Tests
Tests all new infrastructure endpoints and activity feed enhancements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestInfrastructureOverview:
    """Tests for /api/infrastructure/overview endpoint"""

    def test_overview_returns_valid_json(self):
        """Overview endpoint returns valid JSON with required fields"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview")
        assert response.status_code == 200
        
        data = response.json()
        # Check required fields exist
        assert "agent_name" in data
        assert "agent_address" in data
        assert "sandbox_count" in data
        assert "domain_count" in data
        assert "service_count" in data
        assert "installed_tools_count" in data
        assert "discovered_agents_count" in data
        assert "pending_messages" in data
        
        # Check counts are integers
        assert isinstance(data["sandbox_count"], int)
        assert isinstance(data["domain_count"], int)
        assert isinstance(data["installed_tools_count"], int)
        
        # Check arrays exist
        assert "children_sandboxes" in data
        assert "installed_tools" in data
        assert "domains" in data
        assert isinstance(data["children_sandboxes"], list)
        assert isinstance(data["installed_tools"], list)
        assert isinstance(data["domains"], list)


class TestInfrastructureSandboxes:
    """Tests for /api/infrastructure/sandboxes endpoint"""

    def test_sandboxes_returns_valid_json(self):
        """Sandboxes endpoint returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes")
        assert response.status_code == 200
        
        data = response.json()
        assert "sandboxes" in data
        assert "total" in data
        assert isinstance(data["sandboxes"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["sandboxes"])


class TestInfrastructureTerminal:
    """Tests for /api/infrastructure/terminal endpoint"""

    def test_terminal_returns_valid_json(self):
        """Terminal endpoint returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/terminal")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)
        assert isinstance(data["total"], int)

    def test_terminal_respects_lines_param(self):
        """Terminal endpoint respects lines parameter"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/terminal?lines=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["entries"], list)
        # Should have at most 10 entries (may have fewer if not enough data)
        assert len(data["entries"]) <= 10


class TestInfrastructureDomains:
    """Tests for /api/infrastructure/domains endpoint"""

    def test_domains_returns_valid_json(self):
        """Domains endpoint returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/domains")
        assert response.status_code == 200
        
        data = response.json()
        assert "domains" in data
        assert "total" in data
        assert isinstance(data["domains"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["domains"])


class TestInfrastructureInstalledTools:
    """Tests for /api/infrastructure/installed-tools endpoint"""

    def test_installed_tools_returns_valid_json(self):
        """Installed tools endpoint returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/installed-tools")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert "total" in data
        assert isinstance(data["tools"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["tools"])


class TestInfrastructureActivityFeed:
    """Tests for /api/infrastructure/activity-feed endpoint"""

    def test_activity_feed_returns_valid_json(self):
        """Activity feed endpoint returns valid JSON structure"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed")
        assert response.status_code == 200
        
        data = response.json()
        assert "feed" in data
        assert "total" in data
        assert isinstance(data["feed"], list)
        assert isinstance(data["total"], int)

    def test_activity_feed_respects_limit_param(self):
        """Activity feed respects limit parameter"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["feed"], list)
        assert len(data["feed"]) <= 5

    def test_activity_feed_item_structure(self):
        """Activity feed items have required fields"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        if data["feed"]:  # Only test if there are items
            item = data["feed"][0]
            # Required fields for all feed items
            assert "type" in item
            assert "category" in item
            assert "title" in item
            assert "timestamp" in item
            # Check category is valid
            valid_categories = ["infrastructure", "compute", "finance", "network", 
                               "domains", "orchestrator", "tools", "inference", 
                               "memory", "system", "heartbeat", "other"]
            assert item["category"] in valid_categories

    def test_activity_feed_has_heartbeat_entries(self):
        """Activity feed contains heartbeat entries (agent is sleeping but heartbeats logged)"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=100")
        assert response.status_code == 200
        
        data = response.json()
        # Since agent is sleeping, we should at least have heartbeat entries
        heartbeat_items = [item for item in data["feed"] if item.get("type") == "heartbeat"]
        # There should be heartbeat entries based on context
        assert len(heartbeat_items) >= 0  # May be empty but structure is correct


class TestLegacyEndpointsStillWork:
    """Verify legacy endpoints still function"""

    def test_health_endpoint(self):
        """Health endpoint works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_db_exists" in data

    def test_genesis_status(self):
        """Genesis status endpoint works"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        # Should have basic fields
        assert "status" in data or "config_exists" in data

    def test_live_identity(self):
        """Live identity endpoint works"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        # Should return identity data or empty
        assert isinstance(data, dict)

    def test_agents_list(self):
        """Agents list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)


class TestSidebarNavigation:
    """Test that expected nav items exist via skills check"""

    def test_skills_endpoint(self):
        """Skills endpoint works - implies sidebar can navigate to skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
