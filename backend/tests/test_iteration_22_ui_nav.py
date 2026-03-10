"""
Iteration 22: UI/Navigation Changes Backend Tests
Tests for:
1. /api/credits/key-status - Returns correct key status
2. /api/credits/set-key - Accepts and validates new key
3. /api/agents/anima-fund/select - Switches agent correctly
4. /api/agents - Agent list endpoint
5. /api/health - Health check
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Health check tests"""
    
    def test_health_returns_ok(self):
        """Test that /api/health returns 200 with status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        print(f"Health check passed: {data}")


class TestCreditsKeyStatus:
    """Tests for /api/credits/key-status endpoint"""
    
    def test_key_status_returns_configured(self):
        """Test that key-status returns configured state when key exists"""
        response = requests.get(f"{BASE_URL}/api/credits/key-status")
        assert response.status_code == 200
        data = response.json()
        
        # Key should be configured (we have a key in .env)
        assert "configured" in data
        print(f"Key status response: {data}")
        
        if data["configured"]:
            assert "key_prefix" in data
            assert data["key_prefix"].startswith("cnwy_k_")
            print(f"Key is configured with prefix: {data['key_prefix']}")


class TestCreditsSetKey:
    """Tests for /api/credits/set-key endpoint"""
    
    def test_set_key_rejects_invalid_format(self):
        """Test that set-key rejects keys that don't start with cnwy_"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": "invalid_key_format"}
        )
        assert response.status_code == 200  # Returns 200 with success: false
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        print(f"Invalid format rejection: {data['error']}")
    
    def test_set_key_rejects_invalid_conway_key(self):
        """Test that set-key validates against Conway API"""
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": "cnwy_k_invalid_test_key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        print(f"Invalid Conway key rejection: {data['error']}")
    
    def test_set_key_accepts_valid_key(self):
        """Test that set-key accepts valid Conway key"""
        # Use the real key from environment
        valid_key = "cnwy_k_HUFTefVvBakA_QMFbzeb9ps8rKXYIaGe"
        response = requests.post(
            f"{BASE_URL}/api/credits/set-key",
            json={"api_key": valid_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "credits_cents" in data
        assert "key_prefix" in data
        print(f"Valid key accepted: prefix={data['key_prefix']}, credits={data['credits_cents']}")


class TestAgentSelection:
    """Tests for /api/agents/{id}/select endpoint"""
    
    def test_select_anima_fund_agent(self):
        """Test switching to anima-fund agent"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["active_agent"] == "anima-fund"
        print(f"Agent selection successful: {data}")
    
    def test_select_nonexistent_agent_returns_404(self):
        """Test that selecting non-existent agent returns 404"""
        response = requests.post(f"{BASE_URL}/api/agents/nonexistent-agent-123/select")
        assert response.status_code == 404
        print(f"Non-existent agent correctly returned 404")


class TestAgentList:
    """Tests for /api/agents endpoint"""
    
    def test_agents_returns_list(self):
        """Test that /api/agents returns agent list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        # Should have at least anima-fund
        agent_ids = [a["agent_id"] for a in data["agents"]]
        assert "anima-fund" in agent_ids
        print(f"Found {len(data['agents'])} agents: {agent_ids}")
    
    def test_anima_fund_agent_has_required_fields(self):
        """Test that anima-fund agent has all required fields"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        
        anima = next((a for a in data["agents"] if a["agent_id"] == "anima-fund"), None)
        assert anima is not None
        
        # Required fields
        assert "agent_id" in anima
        assert "name" in anima
        assert "status" in anima
        assert anima["name"] == "Anima Fund"
        print(f"Anima Fund agent data: {anima}")


class TestCreditsBalance:
    """Tests for /api/credits/balance endpoint"""
    
    def test_balance_returns_credits(self):
        """Test that balance endpoint returns credit info"""
        response = requests.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200
        data = response.json()
        assert "credits_cents" in data
        print(f"Credit balance: {data['credits_cents']} cents")


class TestCreditsVerify:
    """Tests for /api/credits/verify endpoint"""
    
    def test_verify_returns_verified(self):
        """Test that verify endpoint returns verification status"""
        response = requests.post(f"{BASE_URL}/api/credits/verify")
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        print(f"Verify response: verified={data['verified']}")


# Fixtures
@pytest.fixture(scope="module", autouse=True)
def setup_agent():
    """Ensure anima-fund is selected before tests"""
    requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
    yield


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
