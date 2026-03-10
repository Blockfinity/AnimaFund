"""
Iteration 11 - Conway Domains API Integration Tests

Testing the Conway Domains API alignment changes:
1. Public endpoints (domain-search, domain-check, domain-pricing) - should return real data from api.conway.domains
2. Authenticated endpoints (domain-list, domain-register, domain-renew, domain-dns-*, domain-privacy, domain-nameservers, domain-info, domain-transactions) - should return sandbox required error
3. Skills endpoint should include new domain tools
4. Genesis-prompt.md should have updated model names (gpt-5.2, gpt-5-nano)
"""

import pytest
import requests
import os

# Use REACT_APP_BACKEND_URL from environment - no default fallback
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health and existing endpoints should still work"""
    
    def test_health_returns_200(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Health check passed: {data}")

    def test_provision_status_returns_agent_id(self):
        """GET /api/provision/status returns agent_id"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        print(f"✓ Provision status passed: agent_id={data.get('agent_id')}")

    def test_agents_endpoint_works(self):
        """GET /api/agents returns agents list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        print(f"✓ Agents endpoint passed: {len(data['agents'])} agents")

    def test_nudge_endpoint_works(self):
        """POST /api/provision/nudge still works"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Nudge endpoint passed")


class TestPublicDomainEndpoints:
    """
    Public Conway Domain endpoints - no auth required
    These should return real data from api.conway.domains
    """

    def test_domain_search_returns_success_with_results(self):
        """POST /api/provision/domain-search returns success=true with results array and source=api.conway.domains"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-search",
            json={"query": "test", "tlds": "com,ai"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got: {data}"
        assert "results" in data, f"Expected 'results' key in response: {data}"
        assert isinstance(data["results"], list), f"Expected results to be a list: {data}"
        assert data.get("source") == "api.conway.domains", f"Expected source=api.conway.domains, got: {data.get('source')}"
        print(f"✓ Domain search passed: {len(data['results'])} results from {data.get('source')}")

    def test_domain_check_returns_success_with_domains(self):
        """POST /api/provision/domain-check returns success=true with domains array and source=api.conway.domains"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-check",
            json={"domains": "test.com,test.ai"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got: {data}"
        assert "domains" in data, f"Expected 'domains' key in response: {data}"
        assert isinstance(data["domains"], list), f"Expected domains to be a list: {data}"
        assert data.get("source") == "api.conway.domains", f"Expected source=api.conway.domains, got: {data.get('source')}"
        print(f"✓ Domain check passed: {len(data['domains'])} domains from {data.get('source')}")

    def test_domain_pricing_returns_success_with_pricing(self):
        """GET /api/provision/domain-pricing returns success=true with pricing array and source=api.conway.domains"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-pricing?tlds=com,ai,io,xyz")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got: {data}"
        assert "pricing" in data, f"Expected 'pricing' key in response: {data}"
        assert isinstance(data["pricing"], list), f"Expected pricing to be a list: {data}"
        assert data.get("source") == "api.conway.domains", f"Expected source=api.conway.domains, got: {data.get('source')}"
        print(f"✓ Domain pricing passed: {len(data['pricing'])} TLD prices from {data.get('source')}")


class TestAuthenticatedDomainEndpoints:
    """
    Authenticated Conway Domain endpoints - require sandbox with Conway Terminal
    These should return success=false with error mentioning 'sandbox' (no sandbox provisioned)
    """

    def test_domain_list_requires_sandbox(self):
        """GET /api/provision/domain-list returns success=false with error mentioning 'sandbox'"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-list")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain list correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_register_requires_sandbox(self):
        """POST /api/provision/domain-register returns success=false with error mentioning 'sandbox'"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-register",
            json={"domain": "test.io"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain register correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_renew_requires_sandbox(self):
        """POST /api/provision/domain-renew returns success=false with error mentioning 'sandbox'"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-renew",
            json={"domain": "test.io"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain renew correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_dns_list_requires_sandbox(self):
        """GET /api/provision/domain-dns-list requires sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-dns-list?domain=test.io")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain DNS list correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_dns_add_requires_sandbox(self):
        """POST /api/provision/domain-dns-add requires sandbox"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-dns-add",
            json={
                "domain": "test.io",
                "record_type": "A",
                "host": "@",
                "value": "1.2.3.4"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain DNS add correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_privacy_requires_sandbox(self):
        """PUT /api/provision/domain-privacy requires sandbox"""
        response = requests.put(
            f"{BASE_URL}/api/provision/domain-privacy",
            json={"domain": "test.io", "enabled": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain privacy correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_nameservers_requires_sandbox(self):
        """PUT /api/provision/domain-nameservers requires sandbox"""
        response = requests.put(
            f"{BASE_URL}/api/provision/domain-nameservers",
            json={"domain": "test.io", "nameservers": ["ns1.test.com", "ns2.test.com"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain nameservers correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_info_requires_sandbox(self):
        """GET /api/provision/domain-info requires sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-info?domain=test.io")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain info correctly requires sandbox: {data.get('error')[:100]}")

    def test_domain_transactions_requires_sandbox(self):
        """GET /api/provision/domain-transactions requires sandbox"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-transactions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False, f"Expected success=false, got: {data}"
        error_msg = data.get("error", "").lower()
        assert "sandbox" in error_msg, f"Expected error to mention 'sandbox', got: {data.get('error')}"
        print(f"✓ Domain transactions correctly requires sandbox: {data.get('error')[:100]}")


class TestSkillsWithDomainTools:
    """
    Skills endpoint should include the new domain tools
    """

    def test_skills_include_domain_tools(self):
        """GET /api/skills/available returns skills with domain_check, domain_pricing, domain_renew, domain_dns_list, domain_dns_update, domain_dns_delete, domain_privacy, domain_nameservers tools"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data, f"Expected 'skills' key in response: {data}"
        
        skill_names = [s.get("name", "") for s in data["skills"]]
        
        # Check for required domain tools
        required_tools = [
            "domain_check",
            "domain_pricing", 
            "domain_renew",
            "domain_dns_list",
            "domain_dns_add",  # Note: in agents.py it's domain_dns_add/update/delete
            "domain_dns_update",
            "domain_dns_delete",
            "domain_privacy",
            "domain_nameservers"
        ]
        
        missing_tools = []
        for tool in required_tools:
            if tool not in skill_names:
                missing_tools.append(tool)
        
        assert len(missing_tools) == 0, f"Missing domain tools in skills: {missing_tools}. Available skills: {skill_names[:20]}..."
        print(f"✓ Skills include all domain tools: {required_tools}")


class TestGenesisPromptModelNames:
    """
    Genesis prompt should have updated model names (gpt-5.2, gpt-5-nano)
    """

    def test_genesis_prompt_line_204_has_gpt52_models(self):
        """Content: genesis-prompt.md line 204 contains gpt-5.2 and gpt-5-nano (not GPT-4o or o3-mini)"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            lines = f.readlines()
        
        # Line 204 (0-indexed: line 203)
        line_204 = lines[203] if len(lines) > 203 else ""
        
        # Check for correct model names
        assert "gpt-5.2" in line_204, f"Line 204 should contain 'gpt-5.2', got: {line_204}"
        assert "gpt-5-nano" in line_204, f"Line 204 should contain 'gpt-5-nano', got: {line_204}"
        
        # Check that outdated model names are NOT present
        assert "GPT-4o" not in line_204, f"Line 204 should NOT contain 'GPT-4o', got: {line_204}"
        assert "o3-mini" not in line_204, f"Line 204 should NOT contain 'o3-mini', got: {line_204}"
        
        print(f"✓ Genesis prompt line 204 has correct model names: {line_204[:100].strip()}")

    def test_genesis_prompt_phase_0_test_uses_gpt5_nano(self):
        """Content: genesis-prompt.md Phase 0 tool test #10 uses gpt-5-nano model (not gpt-4o-mini)"""
        genesis_path = "/app/automaton/genesis-prompt.md"
        with open(genesis_path, "r") as f:
            content = f.read()
        
        # Find Phase 0 tool test #10
        # Looking for the line around line 55: "10. COMPUTE: Run chat_completions (model: "gpt-5-nano"..."
        assert 'model: "gpt-5-nano"' in content or "model: 'gpt-5-nano'" in content, \
            f"Phase 0 tool test #10 should use 'gpt-5-nano' model"
        
        # Check that outdated model names are NOT in Phase 0 test
        assert 'model: "gpt-4o-mini"' not in content, \
            "Phase 0 tool test should NOT use 'gpt-4o-mini' model"
        
        print(f"✓ Genesis prompt Phase 0 test #10 uses correct model: gpt-5-nano")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
