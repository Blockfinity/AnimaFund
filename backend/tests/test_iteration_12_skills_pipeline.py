"""
Test iteration 12: Skills provisioning pipeline rewrite and genesis prompt security hardening

Tests:
1. Backend: GET /api/health returns 200
2. Backend: POST /api/provision/load-skills without sandbox returns success=false with 'No sandbox' error
3. Backend: GET /api/provision/status returns valid response with skills_loaded field
4. Backend: POST /api/provision/domain-search still works (regression check)
5. Backend: GET /api/provision/domain-pricing still works (regression check)
6. Backend: GET /api/agents returns agents list
7. Backend: GET /api/skills/available returns skills with domain_check etc.
8. Backend: POST /api/provision/nudge works
9. Backend: POST /api/provision/verify-sandbox without sandbox returns error
10. Backend: POST /api/provision/deploy-agent without sandbox returns error
11. Content: genesis-prompt.md contains SKILL DISCOVERY section
12. Content: genesis-prompt.md contains 'npx clawhub' commands
13. Content: genesis-prompt.md contains 'openclaw skills list' command
14. Content: genesis-prompt.md contains ClawHavoc security warning
15. Content: genesis-prompt.md SECURITY section says 'NEVER attempt to connect to localhost'
16. Content: genesis-prompt.md contains skill-vetter recommendation
17. Content: genesis-prompt.md does NOT contain 'localhost' or '127.0.0.1' outside security warnings
18. Code: agent_setup.py uses ~/.openclaw/skills/ path (not ~/.anima/skills/)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Path to genesis-prompt.md and agent_setup.py for content validation
GENESIS_PROMPT_PATH = "/app/automaton/genesis-prompt.md"
AGENT_SETUP_PATH = "/app/backend/routers/agent_setup.py"


class TestHealthAndBasicEndpoints:
    """Test basic API health and core endpoints"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got {data}"
        print(f"✓ Health check passed: {data}")
    
    def test_provision_status(self):
        """GET /api/provision/status returns valid response with skills_loaded field"""
        response = requests.get(f"{BASE_URL}/api/provision/status")
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        data = response.json()
        # Must have skills_loaded field
        assert "skills_loaded" in data, f"Missing skills_loaded field: {data.keys()}"
        # Must have agent_id
        assert "agent_id" in data, f"Missing agent_id field: {data.keys()}"
        print(f"✓ Provision status passed: agent_id={data.get('agent_id')}, skills_loaded={data.get('skills_loaded')}")
    
    def test_agents_list(self):
        """GET /api/agents returns agents list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200, f"Agents endpoint failed: {response.text}"
        data = response.json()
        # Should be a list or have agents key
        assert isinstance(data, list) or "agents" in data, f"Invalid agents response: {type(data)}"
        print(f"✓ Agents endpoint passed: {len(data) if isinstance(data, list) else len(data.get('agents', []))} agents")
    
    def test_skills_available(self):
        """GET /api/skills/available returns skills with domain_check etc."""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200, f"Skills endpoint failed: {response.text}"
        data = response.json()
        # Check for domain tools in skills list
        skills = data if isinstance(data, list) else data.get("skills", [])
        skill_names = [s.get("name", s.get("id", str(s))) for s in skills] if skills else []
        # At minimum check that domain_check is in the skill list somewhere
        skill_str = str(data).lower()
        assert "domain" in skill_str, f"No domain skills found in response"
        print(f"✓ Skills available passed: {len(skills)} skills, includes domain tools")
    
    def test_nudge_endpoint(self):
        """POST /api/provision/nudge works"""
        response = requests.post(f"{BASE_URL}/api/provision/nudge")
        assert response.status_code == 200, f"Nudge endpoint failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, f"Nudge failed: {data}"
        print(f"✓ Nudge endpoint passed: {data}")


class TestSandboxRequiredEndpoints:
    """Test endpoints that require sandbox - should fail gracefully without one"""
    
    def test_load_skills_without_sandbox(self):
        """POST /api/provision/load-skills without sandbox returns success=false with 'No sandbox' error"""
        response = requests.post(f"{BASE_URL}/api/provision/load-skills")
        assert response.status_code == 200, f"load-skills endpoint HTTP failed: {response.status_code}"
        data = response.json()
        # Without sandbox, should return success=false
        assert data.get("success") == False, f"Expected success=false without sandbox, got: {data}"
        # Error should mention sandbox
        error_msg = str(data.get("error", "")).lower()
        assert "sandbox" in error_msg or "no sandbox" in error_msg, f"Error should mention sandbox: {data}"
        print(f"✓ load-skills without sandbox correctly returns error: {data.get('error')}")
    
    def test_verify_sandbox_without_sandbox(self):
        """POST /api/provision/verify-sandbox without sandbox returns error"""
        response = requests.post(f"{BASE_URL}/api/provision/verify-sandbox")
        assert response.status_code == 200, f"verify-sandbox endpoint HTTP failed: {response.status_code}"
        data = response.json()
        # Without sandbox, should return success=false
        assert data.get("success") == False, f"Expected success=false without sandbox, got: {data}"
        error_msg = str(data.get("error", "")).lower()
        assert "sandbox" in error_msg, f"Error should mention sandbox: {data}"
        print(f"✓ verify-sandbox without sandbox correctly returns error: {data.get('error')}")
    
    def test_deploy_agent_without_sandbox(self):
        """POST /api/provision/deploy-agent without sandbox returns error"""
        response = requests.post(f"{BASE_URL}/api/provision/deploy-agent")
        assert response.status_code == 200, f"deploy-agent endpoint HTTP failed: {response.status_code}"
        data = response.json()
        # Without sandbox, should return success=false
        assert data.get("success") == False, f"Expected success=false without sandbox, got: {data}"
        error_msg = str(data.get("error", "")).lower()
        assert "sandbox" in error_msg, f"Error should mention sandbox: {data}"
        print(f"✓ deploy-agent without sandbox correctly returns error: {data.get('error')}")


class TestRegressionDomainEndpoints:
    """Regression tests for domain endpoints that should still work"""
    
    def test_domain_search(self):
        """POST /api/provision/domain-search still works"""
        response = requests.post(
            f"{BASE_URL}/api/provision/domain-search",
            json={"query": "animatest", "tlds": "com,ai"}
        )
        assert response.status_code == 200, f"domain-search failed: {response.text}"
        data = response.json()
        # Should return success=true (public endpoint)
        assert data.get("success") == True, f"domain-search should succeed: {data}"
        assert "results" in data or "query" in data, f"Invalid domain-search response: {data}"
        print(f"✓ domain-search regression passed: {data.get('source', 'unknown')} source")
    
    def test_domain_pricing(self):
        """GET /api/provision/domain-pricing still works"""
        response = requests.get(f"{BASE_URL}/api/provision/domain-pricing?tlds=com,ai")
        assert response.status_code == 200, f"domain-pricing failed: {response.text}"
        data = response.json()
        # Should return success=true (public endpoint)
        assert data.get("success") == True, f"domain-pricing should succeed: {data}"
        assert "pricing" in data, f"Missing pricing in response: {data.keys()}"
        print(f"✓ domain-pricing regression passed: {len(data.get('pricing', []))} TLDs")


class TestGenesisPromptContent:
    """Test genesis-prompt.md contains required content"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Load genesis prompt content"""
        with open(GENESIS_PROMPT_PATH, "r") as f:
            self.content = f.read()
    
    def test_skill_discovery_section(self):
        """genesis-prompt.md contains SKILL DISCOVERY section"""
        assert "SKILL DISCOVERY" in self.content, "Missing 'SKILL DISCOVERY' section"
        print("✓ genesis-prompt.md contains SKILL DISCOVERY section")
    
    def test_npx_clawhub_commands(self):
        """genesis-prompt.md contains 'npx clawhub' commands"""
        assert "npx clawhub" in self.content, "Missing 'npx clawhub' commands"
        # Check for specific commands
        assert "npx clawhub search" in self.content, "Missing 'npx clawhub search' command"
        assert "npx clawhub@latest install" in self.content, "Missing 'npx clawhub@latest install' command"
        print("✓ genesis-prompt.md contains npx clawhub commands (search, install)")
    
    def test_openclaw_skills_list_command(self):
        """genesis-prompt.md contains 'openclaw skills list' command"""
        assert "openclaw skills list" in self.content, "Missing 'openclaw skills list' command"
        print("✓ genesis-prompt.md contains 'openclaw skills list' command")
    
    def test_clawhavoc_warning(self):
        """genesis-prompt.md contains ClawHavoc security warning"""
        assert "ClawHavoc" in self.content, "Missing 'ClawHavoc' security warning"
        print("✓ genesis-prompt.md contains ClawHavoc security warning")
    
    def test_localhost_security_warning(self):
        """genesis-prompt.md SECURITY section says 'NEVER attempt to connect to localhost'"""
        assert "NEVER attempt to connect to localhost" in self.content, "Missing localhost security warning"
        print("✓ genesis-prompt.md contains 'NEVER attempt to connect to localhost' warning")
    
    def test_skill_vetter_recommendation(self):
        """genesis-prompt.md contains skill-vetter recommendation"""
        assert "skill-vetter" in self.content, "Missing 'skill-vetter' recommendation"
        print("✓ genesis-prompt.md contains skill-vetter recommendation")
    
    def test_no_localhost_outside_warnings(self):
        """genesis-prompt.md does NOT contain 'localhost' or '127.0.0.1' outside security warnings"""
        # Split content into lines and check each
        lines = self.content.split('\n')
        problematic_lines = []
        for i, line in enumerate(lines, 1):
            # Skip lines that are security warnings
            if "NEVER" in line.upper() or "WARNING" in line.upper() or "DON'T" in line.upper() or "DO NOT" in line.upper():
                continue
            # Check for localhost references in non-warning context
            if "localhost" in line.lower() and "never" not in line.lower():
                problematic_lines.append((i, line.strip()))
            if "127.0.0.1" in line:
                problematic_lines.append((i, line.strip()))
        
        # Allow localhost in the security warning line itself (line 346)
        problematic_lines = [l for l in problematic_lines if "never attempt to connect" not in l[1].lower()]
        
        assert len(problematic_lines) == 0, f"Found localhost/127.0.0.1 outside security warnings: {problematic_lines}"
        print("✓ genesis-prompt.md does NOT contain localhost/127.0.0.1 outside security warnings")


class TestAgentSetupCodePath:
    """Test agent_setup.py uses correct skill paths"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Load agent_setup.py content"""
        with open(AGENT_SETUP_PATH, "r") as f:
            self.content = f.read()
    
    def test_uses_openclaw_skills_path(self):
        """agent_setup.py uses ~/.openclaw/skills/ path"""
        assert "~/.openclaw/skills" in self.content or ".openclaw/skills" in self.content, \
            "agent_setup.py should use ~/.openclaw/skills/ path"
        print("✓ agent_setup.py uses ~/.openclaw/skills/ path")
    
    def test_no_anima_skills_path(self):
        """agent_setup.py does NOT use ~/.anima/skills/ path"""
        # Check that .anima/skills is NOT used (should be .openclaw/skills now)
        assert ".anima/skills" not in self.content, \
            "agent_setup.py should NOT use ~/.anima/skills/ path anymore (should be ~/.openclaw/skills/)"
        print("✓ agent_setup.py correctly does NOT use ~/.anima/skills/ path")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
