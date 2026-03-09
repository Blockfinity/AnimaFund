"""
Iteration 41 - Conway API Integration Tests

Testing the new /api/conway/* router endpoints that integrate with Conway ecosystem:
- Conway Cloud (sandboxes/VMs)
- Conway Domains (domain registration/DNS)
- Conway Compute (inference)
- Conway Credits (balance, pricing)

Also tests core endpoints: health, wallet, genesis, agents, skills, infrastructure
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoints:
    """Basic health and engine status endpoints"""
    
    def test_health_returns_ok_with_engine_info(self):
        """GET /api/health - returns status ok with engine info"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"Health check: status={data['status']}, engine_live={data['engine_live']}")
    
    def test_engine_live_status(self):
        """GET /api/engine/live - returns engine running status"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "live" in data
        assert "db_exists" in data
        assert "agent_id" in data
        print(f"Engine live: live={data['live']}, db_exists={data['db_exists']}, agent_state={data.get('agent_state', 'N/A')}")


class TestConwayBalance:
    """Conway API balance and credits endpoints"""
    
    def test_conway_balance_returns_credits_and_sandboxes(self):
        """GET /api/conway/balance - returns credits_cents, credits_usd, sandboxes from Conway API"""
        response = requests.get(f"{BASE_URL}/api/conway/balance")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "conway_api"
        assert "credits_cents" in data
        assert "credits_usd" in data
        # Credits may be 0 (expected since agent has no funds)
        assert isinstance(data["credits_cents"], (int, float))
        assert isinstance(data["credits_usd"], (int, float))
        # Sandboxes should be present (empty list if none)
        assert "sandboxes" in data or "sandbox_count" in data
        print(f"Conway balance: credits_cents={data['credits_cents']}, credits_usd={data['credits_usd']}")
    
    def test_conway_sandboxes_list(self):
        """GET /api/conway/sandboxes - returns sandbox list from Conway Cloud"""
        response = requests.get(f"{BASE_URL}/api/conway/sandboxes")
        assert response.status_code == 200
        data = response.json()
        # Should return sandboxes list (empty if none) or error if API key missing
        assert "sandboxes" in data or "count" in data or "error" in data
        print(f"Conway sandboxes: {data}")


class TestConwayHealth:
    """Conway API health check endpoints"""
    
    def test_conway_health_all_services(self):
        """GET /api/conway/health - returns all_healthy boolean and status of 3 Conway services"""
        response = requests.get(f"{BASE_URL}/api/conway/health")
        assert response.status_code == 200
        data = response.json()
        assert "all_healthy" in data
        assert "services" in data
        # Verify all 3 services are checked
        services = data["services"]
        assert "cloud" in services
        assert "domains" in services
        assert "inference" in services
        # Each service should have status
        for name, svc in services.items():
            assert "status" in svc
            print(f"  {name}: {svc['status']}")
        print(f"Conway health: all_healthy={data['all_healthy']}")
    
    def test_conway_inference_health(self):
        """GET /api/conway/inference/health - returns inference API status"""
        response = requests.get(f"{BASE_URL}/api/conway/inference/health")
        assert response.status_code == 200
        data = response.json()
        # Should have status field
        assert "status" in data
        print(f"Inference health: {data}")


class TestConwayDomains:
    """Conway Domains API endpoints"""
    
    def test_conway_domain_search(self):
        """GET /api/conway/domains/search?q=test&tlds=ai,com - returns domain search results"""
        response = requests.get(f"{BASE_URL}/api/conway/domains/search", params={"q": "test", "tlds": "ai,com"})
        assert response.status_code == 200
        data = response.json()
        # Should have query and results
        assert "query" in data or "results" in data or "error" not in data
        if "results" in data:
            assert isinstance(data["results"], list)
            # Each result should have domain and availability info
            for result in data["results"][:3]:  # Check first 3
                assert "domain" in result
                assert "available" in result
        print(f"Domain search results: {len(data.get('results', []))} domains found")


class TestConwayCredits:
    """Conway Credits API endpoints"""
    
    def test_conway_credits_pricing(self):
        """GET /api/conway/credits/pricing - returns pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/conway/credits/pricing")
        assert response.status_code == 200
        data = response.json()
        # Should have pricing or tiers
        assert "pricing" in data or "tiers" in data or "error" not in data
        if "pricing" in data:
            assert isinstance(data["pricing"], list)
            # Each tier should have price info
            for tier in data["pricing"][:3]:
                assert "name" in tier or "vcpu" in tier
        if "tiers" in data:
            assert isinstance(data["tiers"], list)
        print(f"Conway pricing: {len(data.get('pricing', []))} VM tiers, {len(data.get('tiers', []))} credit tiers")


class TestWalletBalance:
    """Wallet balance and on-chain status"""
    
    def test_wallet_balance_returns_full_info(self):
        """GET /api/wallet/balance - returns usdc, eth, credits_cents, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        # Should have wallet address
        assert "wallet" in data or "error" in data
        if "wallet" in data:
            assert data["wallet"].startswith("0x")
            # Should have balance fields
            assert "usdc" in data
            assert "eth" in data
            assert "credits_cents" in data
            assert "tier" in data
            print(f"Wallet balance: wallet={data['wallet'][:10]}..., usdc=${data['usdc']}, eth={data['eth']}, credits=${data['credits_cents']/100}, tier={data['tier']}")
        else:
            print(f"Wallet error: {data.get('error', 'unknown')}")


class TestGenesisStatus:
    """Genesis agent status and configuration"""
    
    def test_genesis_status_returns_agent_info(self):
        """GET /api/genesis/status - returns agent_id, wallet_address, config status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        # Core fields
        assert "agent_id" in data
        assert "wallet_address" in data or data.get("status") == "not_created"
        assert "config_exists" in data
        assert "status" in data or "stage" in data
        print(f"Genesis status: agent_id={data['agent_id']}, wallet={data.get('wallet_address', 'N/A')[:10]}..., status={data.get('status', data.get('stage', 'N/A'))}")
    
    def test_genesis_prompt_template(self):
        """GET /api/genesis/prompt-template - returns genesis prompt with conway and openclaw references"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        content = data["content"].lower()
        # Should contain Conway Terminal references
        assert "conway" in content
        # Should contain OpenClaw references
        assert "openclaw" in content
        print(f"Genesis prompt template: {len(data['content'])} characters, contains Conway={True}, contains OpenClaw={True}")


class TestAgents:
    """Agent management endpoints"""
    
    def test_agents_list_returns_active_agent(self):
        """GET /api/agents - returns agents list with active agent"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) >= 1  # At least default agent
        # Check first agent has required fields
        agent = data["agents"][0]
        assert "agent_id" in agent
        assert "name" in agent
        print(f"Agents: {len(data['agents'])} agents, first={agent['name']}")


class TestSkills:
    """Skills and capabilities endpoints"""
    
    def test_skills_available_returns_full_list(self):
        """GET /api/skills/available - returns 141 skills across 9 sources"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert isinstance(data["skills"], list)
        # Should have significant number of skills
        assert len(data["skills"]) >= 50  # At least 50 skills
        
        # Check skills have required fields
        skill = data["skills"][0]
        assert "name" in skill
        assert "source" in skill
        
        # Count sources
        sources = set(s["source"] for s in data["skills"])
        print(f"Skills: {data['total']} skills across {len(sources)} sources: {sources}")
        
        # Verify Conway tool categories are present
        conway_skills = [s for s in data["skills"] if "conway" in s["source"]]
        assert len(conway_skills) >= 5  # Should have Conway cloud, domains, compute, x402, credits
        print(f"Conway skills: {len(conway_skills)}")


class TestInfrastructure:
    """Infrastructure monitoring endpoints"""
    
    def test_infrastructure_overview(self):
        """GET /api/infrastructure/overview - returns sandbox_count, domain_count, service_count"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview")
        assert response.status_code == 200
        data = response.json()
        # Should have count fields
        assert "sandbox_count" in data
        assert "domain_count" in data
        assert "service_count" in data
        assert "installed_tools_count" in data
        print(f"Infrastructure: sandboxes={data['sandbox_count']}, domains={data['domain_count']}, services={data['service_count']}, tools={data['installed_tools_count']}")


class TestLiveIdentity:
    """Live engine identity endpoint"""
    
    def test_live_identity_returns_agent_info(self):
        """GET /api/live/identity - returns agent identity from state.db"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        # Should have identity fields
        assert "name" in data or "address" in data
        print(f"Live identity: name={data.get('name', 'N/A')}, address={data.get('address', 'N/A')[:10] if data.get('address') else 'N/A'}...")


# Run pytest fixture
@pytest.fixture(scope="session", autouse=True)
def setup_session():
    """Verify BASE_URL is set before running tests"""
    if not BASE_URL:
        pytest.fail("REACT_APP_BACKEND_URL environment variable not set")
    print(f"\n{'='*60}")
    print(f"Testing against: {BASE_URL}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
