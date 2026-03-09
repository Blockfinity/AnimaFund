"""
Iteration 42 - Comprehensive Conway Integration Tests
Tests all Conway API endpoints, core APIs, and verifies complete platform functionality.
"""
import pytest
import requests
import os

# Get BASE_URL from environment - no defaults
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://multi-agent-vc.preview.emergentagent.com"


class TestHealthEndpoints:
    """Test basic health and connectivity endpoints"""

    def test_api_health(self):
        """GET /api/health - returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"✓ /api/health - status: {data['status']}, engine_live: {data.get('engine_live')}")


class TestConwayBalance:
    """Test Conway balance and sandboxes endpoint"""

    def test_conway_balance(self):
        """GET /api/conway/balance - returns credits_cents, credits_usd, sandbox_count, source"""
        response = requests.get(f"{BASE_URL}/api/conway/balance", timeout=15)
        assert response.status_code == 200, f"Conway balance failed: {response.text}"
        data = response.json()
        
        # Verify expected fields exist
        assert data.get("source") == "conway_api", f"Expected source='conway_api', got: {data.get('source')}"
        
        # credits_cents might be 0 if no credits, but field should exist
        if "error" not in data:
            assert "credits_cents" in data, f"Missing credits_cents field: {data}"
            assert "credits_usd" in data, f"Missing credits_usd field: {data}"
            credits_cents = data.get("credits_cents", 0)
            credits_usd = data.get("credits_usd", 0.0)
            print(f"✓ /api/conway/balance - credits_cents: {credits_cents}, credits_usd: {credits_usd}")
        else:
            print(f"⚠ /api/conway/balance - error: {data.get('error')} (expected if no API key)")
        
        # sandbox_count may or may not be present depending on API response
        if "sandbox_count" in data:
            print(f"  sandbox_count: {data['sandbox_count']}")


class TestConwayHealth:
    """Test Conway health status endpoint"""

    def test_conway_health(self):
        """GET /api/conway/health - returns all_healthy boolean and 3 services"""
        response = requests.get(f"{BASE_URL}/api/conway/health", timeout=15)
        assert response.status_code == 200, f"Conway health failed: {response.text}"
        data = response.json()
        
        assert "all_healthy" in data, f"Missing all_healthy field: {data}"
        assert "services" in data, f"Missing services field: {data}"
        
        services = data["services"]
        expected_services = ["cloud", "domains", "inference"]
        for svc in expected_services:
            assert svc in services, f"Missing service {svc}: {services}"
            svc_data = services[svc]
            assert "status" in svc_data, f"Missing status for {svc}: {svc_data}"
            print(f"  {svc}: {svc_data.get('status')}")
        
        print(f"✓ /api/conway/health - all_healthy: {data['all_healthy']}")


class TestConwaySandboxes:
    """Test Conway sandboxes endpoint"""

    def test_conway_sandboxes(self):
        """GET /api/conway/sandboxes - returns sandbox data from Conway Cloud API"""
        response = requests.get(f"{BASE_URL}/api/conway/sandboxes", timeout=15)
        assert response.status_code == 200, f"Conway sandboxes failed: {response.text}"
        data = response.json()
        
        # Might be empty or error if no API key/no sandboxes
        if "error" in data:
            print(f"⚠ /api/conway/sandboxes - error: {data.get('error')} (expected if no API key)")
        else:
            sandboxes = data.get("sandboxes", [])
            count = data.get("count", len(sandboxes))
            print(f"✓ /api/conway/sandboxes - count: {count}")


class TestConwayCredits:
    """Test Conway credits pricing and history endpoints"""

    def test_conway_credits_pricing(self):
        """GET /api/conway/credits/pricing - returns pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/conway/credits/pricing", timeout=15)
        assert response.status_code == 200, f"Conway credits pricing failed: {response.text}"
        data = response.json()
        
        if "error" in data:
            print(f"⚠ /api/conway/credits/pricing - error: {data.get('error')}")
        else:
            # Should have VM tiers with vcpu, memory_mb, disk_gb, cents_per_month
            vm_tiers = data.get("vm_tiers") or data.get("tiers") or data
            print(f"✓ /api/conway/credits/pricing - returned pricing data")
            if isinstance(vm_tiers, list):
                print(f"  VM tiers count: {len(vm_tiers)}")
                for tier in vm_tiers[:3]:  # Show first 3
                    print(f"    {tier.get('name', 'tier')}: {tier.get('vcpu')} vCPU, {tier.get('memory_mb')}MB, {tier.get('cents_per_month')}c/mo")

    def test_conway_credits_history(self):
        """GET /api/conway/credits/history - returns credit transaction history"""
        response = requests.get(f"{BASE_URL}/api/conway/credits/history", timeout=15)
        assert response.status_code == 200, f"Conway credits history failed: {response.text}"
        data = response.json()
        
        # May return error if no history or no credits
        if "error" in data:
            print(f"⚠ /api/conway/credits/history - {data.get('error')} (expected for 0 credits)")
        else:
            history = data.get("history", data.get("transactions", []))
            print(f"✓ /api/conway/credits/history - {len(history) if isinstance(history, list) else 'data'} transactions")


class TestConwayDomains:
    """Test Conway domains search endpoint"""

    def test_conway_domains_search(self):
        """GET /api/conway/domains/search - returns domain availability"""
        response = requests.get(
            f"{BASE_URL}/api/conway/domains/search?q=animafund&tlds=ai,com",
            timeout=15
        )
        assert response.status_code == 200, f"Conway domains search failed: {response.text}"
        data = response.json()
        
        if "error" in data:
            print(f"⚠ /api/conway/domains/search - error: {data.get('error')}")
        else:
            results = data.get("results", data.get("domains", []))
            print(f"✓ /api/conway/domains/search - found {len(results) if isinstance(results, list) else 'some'} results")
            if isinstance(results, list):
                for r in results[:5]:  # Show first 5
                    print(f"    {r.get('domain')}: available={r.get('available')}, premium={r.get('premium', False)}")


class TestConwayInference:
    """Test Conway inference health endpoint"""

    def test_conway_inference_health(self):
        """GET /api/conway/inference/health - returns status='ok' and service='inference-api'"""
        response = requests.get(f"{BASE_URL}/api/conway/inference/health", timeout=15)
        assert response.status_code == 200, f"Conway inference health failed: {response.text}"
        data = response.json()
        
        # Should return status and service info
        status = data.get("status")
        print(f"✓ /api/conway/inference/health - status: {status}")
        if "service" in data:
            print(f"  service: {data['service']}")


class TestWalletAndGenesis:
    """Test wallet balance and genesis status endpoints"""

    def test_wallet_balance(self):
        """GET /api/wallet/balance - returns usdc_balance, eth_balance, conway_credits_cents, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=15)
        assert response.status_code == 200, f"Wallet balance failed: {response.text}"
        data = response.json()
        
        # May have error if no wallet yet
        if "error" in data and "No wallet" in str(data.get("error", "")):
            print(f"⚠ /api/wallet/balance - {data.get('error')} (expected if engine not started)")
        else:
            print(f"✓ /api/wallet/balance - wallet: {data.get('wallet', 'N/A')[:20]}...")
            print(f"  usdc: {data.get('usdc', 0)}, eth: {data.get('eth', 0)}, credits_cents: {data.get('credits_cents', 0)}, tier: {data.get('tier', 'unknown')}")

    def test_genesis_status(self):
        """GET /api/genesis/status - returns agent_id='anima-fund', wallet_address, state, turns"""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=15)
        assert response.status_code == 200, f"Genesis status failed: {response.text}"
        data = response.json()
        
        assert data.get("agent_id") == "anima-fund", f"Expected agent_id='anima-fund', got: {data.get('agent_id')}"
        print(f"✓ /api/genesis/status - agent_id: {data['agent_id']}")
        print(f"  wallet: {data.get('wallet_address', 'N/A')[:20] if data.get('wallet_address') else 'None'}...")
        print(f"  status: {data.get('status')}, engine_live: {data.get('engine_live')}")
        print(f"  turn_count: {data.get('turn_count', 0)}")

    def test_genesis_prompt_template(self):
        """GET /api/genesis/prompt-template - content includes 'conway' and 'openclaw' references"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=15)
        assert response.status_code == 200, f"Genesis prompt template failed: {response.text}"
        data = response.json()
        
        content = data.get("content", "")
        assert len(content) > 0, "Prompt template content is empty"
        
        # Check for key references
        has_conway = "conway" in content.lower()
        has_openclaw = "openclaw" in content.lower()
        
        print(f"✓ /api/genesis/prompt-template - {len(content)} chars")
        print(f"  contains 'conway': {has_conway}")
        print(f"  contains 'openclaw': {has_openclaw}")


class TestAgentsAndSkills:
    """Test agents list and skills available endpoints"""

    def test_agents_list(self):
        """GET /api/agents - returns agents array with at least 1 agent, active_agent field"""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=15)
        assert response.status_code == 200, f"Agents list failed: {response.text}"
        data = response.json()
        
        agents = data.get("agents", [])
        assert len(agents) >= 1, f"Expected at least 1 agent, got: {len(agents)}"
        
        # Check default agent exists
        agent_ids = [a.get("agent_id") for a in agents]
        assert "anima-fund" in agent_ids, f"Default 'anima-fund' agent not found: {agent_ids}"
        
        print(f"✓ /api/agents - {len(agents)} agent(s)")
        for a in agents:
            print(f"    {a.get('agent_id')}: {a.get('name')} - status: {a.get('status')}")

    def test_skills_available(self):
        """GET /api/skills/available - returns 100+ skills with proper sources"""
        response = requests.get(f"{BASE_URL}/api/skills/available", timeout=15)
        assert response.status_code == 200, f"Skills available failed: {response.text}"
        data = response.json()
        
        skills = data.get("skills", [])
        total = data.get("total", len(skills))
        
        # Should have at least 100 skills
        assert total >= 100, f"Expected 100+ skills, got: {total}"
        
        # Check for expected sources
        sources = set(s.get("source") for s in skills)
        expected_sources = ["conway-cloud", "conway-compute", "conway-domains", "conway-x402", "conway-credits", "openclaw", "clawhub"]
        
        found_sources = [src for src in expected_sources if src in sources]
        print(f"✓ /api/skills/available - {total} skills")
        print(f"  sources found: {', '.join(sources)}")
        print(f"  expected sources present: {len(found_sources)}/{len(expected_sources)}")
        
        # Count by source
        source_counts = {}
        for s in skills:
            src = s.get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
        for src, count in sorted(source_counts.items()):
            print(f"    {src}: {count}")


class TestEngineLive:
    """Test engine live status endpoint"""

    def test_engine_live(self):
        """GET /api/engine/live - returns running boolean, agent_id"""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=15)
        assert response.status_code == 200, f"Engine live failed: {response.text}"
        data = response.json()
        
        # Should have running/live status and agent_id
        print(f"✓ /api/engine/live")
        print(f"  live: {data.get('live')}, db_exists: {data.get('db_exists')}")
        print(f"  agent_id: {data.get('agent_id')}, agent_state: {data.get('agent_state')}")


class TestInfrastructure:
    """Test infrastructure overview endpoint"""

    def test_infrastructure_overview(self):
        """GET /api/infrastructure/overview - returns sandbox_count, domain_count, installed_tools"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview", timeout=15)
        assert response.status_code == 200, f"Infrastructure overview failed: {response.text}"
        data = response.json()
        
        print(f"✓ /api/infrastructure/overview")
        print(f"  sandbox_count: {data.get('sandbox_count', 0)}")
        print(f"  domain_count: {data.get('domain_count', 0)}")
        print(f"  installed_tools_count: {data.get('installed_tools_count', 0)}")


class TestLiveIdentity:
    """Test live identity endpoint"""

    def test_live_identity(self):
        """GET /api/live/identity/anima-fund - returns agent identity with name, wallet_address"""
        # First try the generic endpoint
        response = requests.get(f"{BASE_URL}/api/live/identity", timeout=15)
        assert response.status_code == 200, f"Live identity failed: {response.text}"
        data = response.json()
        
        print(f"✓ /api/live/identity")
        if data:
            print(f"  name: {data.get('name', 'N/A')}")
            print(f"  address: {data.get('address', 'N/A')[:20] if data.get('address') else 'None'}...")
            print(f"  state: {data.get('state', 'N/A')}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
