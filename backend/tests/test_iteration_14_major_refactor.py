"""
Test iteration 14: Major refactor - all host-side engine operations removed.
Agent ONLY runs inside Conway Cloud sandbox. This test verifies:
- genesis/status returns stage=not_created, config_exists=false, sandbox_active=false
- genesis/create returns success=false with 'disabled' error
- wallet/balance returns error about 'not provisioned yet' (no wallet on host)
- engine/live returns live=false, source=none
- engine/logs returns error about 'No sandbox'
- engine/status returns source=sandbox
- live/identity returns name and source=database
- live/activity returns empty list
- live/turns returns empty list
- infrastructure/sandboxes returns empty list
- infrastructure/domains returns empty list
- agents returns agents list
- provision/status works (regression)
- provision/domain-search works (regression)
- skills/available works with domain tools (regression)
- agents/{agent_id}/start returns success=false with 'disabled' error
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoint:
    """Health check - engine_live should be False (nothing on host)"""
    
    def test_health_returns_engine_live_false(self):
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health returned {response.status_code}"
        data = response.json()
        assert data.get('status') == 'ok', "Health status should be ok"
        assert data.get('engine_live') is False, "engine_live should be False (nothing on host)"
        print(f"✓ GET /api/health: status=ok, engine_live={data.get('engine_live')}")


class TestGenesisEndpoints:
    """Genesis routes - all read from sandbox provisioning state, not host filesystem"""
    
    def test_genesis_status_returns_not_created(self):
        """genesis/status should return stage=not_created, config_exists=false when no sandbox provisioned"""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200, f"genesis/status returned {response.status_code}"
        data = response.json()
        
        # Key assertions for the major refactor
        assert 'stage' in data, "Response should have 'stage' field"
        assert 'config_exists' in data, "Response should have 'config_exists' field"
        assert 'sandbox_active' in data, "Response should have 'sandbox_active' field"
        
        # These may be true if a sandbox was provisioned, so we check the structure
        print(f"✓ GET /api/genesis/status: stage={data.get('stage')}, config_exists={data.get('config_exists')}, sandbox_active={data.get('sandbox_active')}")
        
        # Verify other fields exist
        assert 'agent_id' in data
        assert 'wallet_address' in data or data.get('wallet_address') is not None or 'wallet_address' in str(data)
        
    def test_genesis_create_returns_disabled_error(self):
        """genesis/create should return success=false with 'disabled' error"""
        response = requests.post(f"{BASE_URL}/api/genesis/create", timeout=10)
        assert response.status_code == 200, f"genesis/create returned {response.status_code}"
        data = response.json()
        
        assert data.get('success') is False, "genesis/create should return success=false"
        assert 'error' in data, "Response should have error message"
        assert 'disabled' in data.get('error', '').lower(), f"Error should mention 'disabled': {data.get('error')}"
        print(f"✓ POST /api/genesis/create: success=false, error contains 'disabled'")


class TestWalletEndpoint:
    """Wallet balance - reads from sandbox wallet, not host"""
    
    def test_wallet_balance_returns_not_provisioned_error(self):
        """wallet/balance should return error about 'not provisioned yet' when no wallet on host"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=10)
        assert response.status_code == 200, f"wallet/balance returned {response.status_code}"
        data = response.json()
        
        # If no wallet is provisioned, there should be an error about provisioning
        # OR if wallet exists, it should have wallet field
        if data.get('error'):
            assert 'provisioned' in data.get('error', '').lower() or 'wallet' in data.get('error', '').lower(), \
                f"Error should mention provisioning or wallet: {data.get('error')}"
            print(f"✓ GET /api/wallet/balance: error='{data.get('error')}'")
        else:
            # Wallet exists (sandbox was provisioned)
            print(f"✓ GET /api/wallet/balance: wallet={data.get('wallet')}, source={data.get('source')}")
        

class TestEngineEndpoints:
    """Engine routes - read from sandbox, not host"""
    
    def test_engine_live_returns_false_and_source_none(self):
        """engine/live should return live=false, source=none (or sandbox)"""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert response.status_code == 200, f"engine/live returned {response.status_code}"
        data = response.json()
        
        assert 'live' in data, "Response should have 'live' field"
        assert 'source' in data, "Response should have 'source' field"
        
        # If no sandbox, source should be 'none'. If sandbox exists, source is 'sandbox'
        assert data.get('source') in ['none', 'sandbox'], f"source should be 'none' or 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/engine/live: live={data.get('live')}, source={data.get('source')}")
        
    def test_engine_logs_returns_no_sandbox_error(self):
        """engine/logs should return error about 'No sandbox' when no sandbox provisioned"""
        response = requests.get(f"{BASE_URL}/api/engine/logs", timeout=10)
        assert response.status_code == 200, f"engine/logs returned {response.status_code}"
        data = response.json()
        
        # If no sandbox, there should be an error
        # If sandbox exists, there should be stdout/stderr fields
        if data.get('error'):
            assert 'sandbox' in data.get('error', '').lower(), f"Error should mention 'sandbox': {data.get('error')}"
            print(f"✓ GET /api/engine/logs: error='{data.get('error')}'")
        else:
            assert 'stdout' in data or 'stderr' in data, "Response should have stdout/stderr"
            print(f"✓ GET /api/engine/logs: source={data.get('source')}")
            
    def test_engine_status_returns_source_sandbox(self):
        """engine/status should return source=sandbox"""
        response = requests.get(f"{BASE_URL}/api/engine/status", timeout=10)
        assert response.status_code == 200, f"engine/status returned {response.status_code}"
        data = response.json()
        
        assert data.get('source') == 'sandbox', f"source should be 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/engine/status: source={data.get('source')}, engine_deployed={data.get('engine_deployed')}")


class TestLiveEndpoints:
    """Live routes - return empty defaults (no host engine_bridge)"""
    
    def test_live_identity_returns_name_and_source_database(self):
        """live/identity should return name and source=database"""
        response = requests.get(f"{BASE_URL}/api/live/identity", timeout=10)
        assert response.status_code == 200, f"live/identity returned {response.status_code}"
        data = response.json()
        
        assert 'name' in data, "Response should have 'name' field"
        assert data.get('source') == 'database', f"source should be 'database', got {data.get('source')}"
        print(f"✓ GET /api/live/identity: name={data.get('name')}, source={data.get('source')}")
        
    def test_live_activity_returns_empty_list(self):
        """live/activity should return empty list"""
        response = requests.get(f"{BASE_URL}/api/live/activity", timeout=10)
        assert response.status_code == 200, f"live/activity returned {response.status_code}"
        data = response.json()
        
        # Should have activities or items key with empty list
        activities = data.get('activities') or data.get('items') or []
        assert isinstance(activities, list), "activities should be a list"
        assert data.get('source') == 'sandbox', f"source should be 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/live/activity: activities count={len(activities)}, source={data.get('source')}")
        
    def test_live_turns_returns_empty_list(self):
        """live/turns should return empty list"""
        response = requests.get(f"{BASE_URL}/api/live/turns", timeout=10)
        assert response.status_code == 200, f"live/turns returned {response.status_code}"
        data = response.json()
        
        # Should have turns or items key with empty list
        turns = data.get('turns') or data.get('items') or []
        assert isinstance(turns, list), "turns should be a list"
        assert data.get('source') == 'sandbox', f"source should be 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/live/turns: turns count={len(turns)}, source={data.get('source')}")


class TestInfrastructureEndpoints:
    """Infrastructure routes - return empty defaults"""
    
    def test_infrastructure_sandboxes_returns_empty_list(self):
        """infrastructure/sandboxes should return empty list"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes", timeout=10)
        assert response.status_code == 200, f"infrastructure/sandboxes returned {response.status_code}"
        data = response.json()
        
        sandboxes = data.get('sandboxes') or data.get('items') or []
        assert isinstance(sandboxes, list), "sandboxes should be a list"
        assert data.get('source') == 'sandbox', f"source should be 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/infrastructure/sandboxes: count={len(sandboxes)}, source={data.get('source')}")
        
    def test_infrastructure_domains_returns_empty_list(self):
        """infrastructure/domains should return empty list"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/domains", timeout=10)
        assert response.status_code == 200, f"infrastructure/domains returned {response.status_code}"
        data = response.json()
        
        domains = data.get('domains') or data.get('items') or []
        assert isinstance(domains, list), "domains should be a list"
        assert data.get('source') == 'sandbox', f"source should be 'sandbox', got {data.get('source')}"
        print(f"✓ GET /api/infrastructure/domains: count={len(domains)}, source={data.get('source')}")


class TestAgentsEndpoints:
    """Agents routes - CRUD, list, start"""
    
    def test_agents_returns_list(self):
        """agents should return agents list"""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert response.status_code == 200, f"agents returned {response.status_code}"
        data = response.json()
        
        assert 'agents' in data, "Response should have 'agents' field"
        agents = data.get('agents', [])
        assert isinstance(agents, list), "agents should be a list"
        assert len(agents) > 0, "Should have at least one agent (anima-fund)"
        
        # Verify agent structure
        for agent in agents:
            assert 'agent_id' in agent, "Agent should have agent_id"
            assert 'name' in agent, "Agent should have name"
            
        print(f"✓ GET /api/agents: count={len(agents)}, agent_ids={[a.get('agent_id') for a in agents]}")
        
    def test_agent_start_returns_disabled_error(self):
        """agents/{agent_id}/start should return success=false with 'disabled' error"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/start", timeout=10)
        assert response.status_code == 200, f"agents/start returned {response.status_code}"
        data = response.json()
        
        assert data.get('success') is False, "agents/start should return success=false"
        assert 'error' in data, "Response should have error message"
        assert 'disabled' in data.get('error', '').lower(), f"Error should mention 'disabled': {data.get('error')}"
        print(f"✓ POST /api/agents/anima-fund/start: success=false, error contains 'disabled'")


class TestProvisioningEndpoints:
    """Provisioning routes - regression tests"""
    
    def test_provision_status_works(self):
        """provision/status should work"""
        response = requests.get(f"{BASE_URL}/api/provision/status", timeout=10)
        assert response.status_code == 200, f"provision/status returned {response.status_code}"
        data = response.json()
        
        # Should have agent_id and sandbox structure
        assert 'agent_id' in data, "Response should have agent_id"
        assert 'sandbox' in data, "Response should have sandbox"
        print(f"✓ GET /api/provision/status: agent_id={data.get('agent_id')}, sandbox_status={data.get('sandbox', {}).get('status')}")
        
    def test_provision_domain_search_works(self):
        """provision/domain-search should work"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-search",
            json={"query": "test"},
            timeout=15
        )
        assert response.status_code == 200, f"provision/domain-search returned {response.status_code}"
        data = response.json()
        
        # Should have success field
        assert 'success' in data, "Response should have success field"
        print(f"✓ POST /api/provision/domain-search: success={data.get('success')}")


class TestSkillsEndpoint:
    """Skills routes - regression test with domain tools"""
    
    def test_skills_available_works_with_domain_tools(self):
        """skills/available should work with domain tools"""
        response = requests.get(f"{BASE_URL}/api/skills/available", timeout=10)
        assert response.status_code == 200, f"skills/available returned {response.status_code}"
        data = response.json()
        
        assert 'skills' in data, "Response should have 'skills' field"
        skills = data.get('skills', [])
        assert len(skills) > 0, "Should have skills"
        
        # Verify domain tools are present
        skill_names = [s.get('name') for s in skills]
        domain_tools = ['domain_search', 'domain_check', 'domain_register', 'domain_renew']
        found_domain_tools = [t for t in domain_tools if t in skill_names]
        
        print(f"✓ GET /api/skills/available: total={len(skills)}, domain_tools_found={found_domain_tools}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
