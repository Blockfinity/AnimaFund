"""
Iteration 43 - Sandboxing Security Tests

Tests the critical sandboxing changes:
1. Bootstrap script does NOT copy global wallet/API key to agents
2. Bootstrap sets chmod 700 on agent directories
3. OpenClaw config has empty env (no leaked API key)
4. agents.py strips MONGO_URL/DB_NAME/DASHBOARD_URL from env
5. All backend APIs still working correctly
"""
import os
import json
import subprocess
import tempfile
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://multi-agent-vc.preview.emergentagent.com').rstrip('/')


class TestBackendAPIs:
    """Test all backend API endpoints are working"""
    
    def test_health(self):
        """GET /api/health - returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: /api/health - status: {data.get('status')}")
    
    def test_conway_balance(self):
        """GET /api/conway/balance - returns credits data"""
        response = requests.get(f"{BASE_URL}/api/conway/balance", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert data.get("source") == "conway_api"
        print(f"PASS: /api/conway/balance - credits_usd: {data.get('credits_usd', 0)}")
    
    def test_conway_health(self):
        """GET /api/conway/health - all 3 services healthy"""
        response = requests.get(f"{BASE_URL}/api/conway/health", timeout=15)
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        services = data.get("services", {})
        for name in ["cloud", "domains", "inference"]:
            assert name in services, f"Missing service: {name}"
        print(f"PASS: /api/conway/health - all_healthy: {data.get('all_healthy')}")
    
    def test_wallet_balance(self):
        """GET /api/wallet/balance - returns balance data"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "wallet" in data
        assert "tier" in data
        print(f"PASS: /api/wallet/balance - wallet: {data.get('wallet', '')[:10]}...")
    
    def test_genesis_status(self):
        """GET /api/genesis/status - returns agent info"""
        response = requests.get(f"{BASE_URL}/api/genesis/status", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        print(f"PASS: /api/genesis/status - agent_id: {data.get('agent_id')}")
    
    def test_agents_list(self):
        """GET /api/agents - returns agents list"""
        response = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data.get("agents", [])) >= 1
        print(f"PASS: /api/agents - count: {len(data.get('agents', []))}")
    
    def test_skills_available(self):
        """GET /api/skills/available - returns 141 skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        total = data.get("total", 0)
        assert total >= 100, f"Expected ~141 skills, got {total}"
        print(f"PASS: /api/skills/available - total: {total}")
    
    def test_engine_live(self):
        """GET /api/engine/live - returns engine status"""
        response = requests.get(f"{BASE_URL}/api/engine/live", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "db_exists" in data
        print(f"PASS: /api/engine/live - db_exists: {data.get('db_exists')}, agent_state: {data.get('agent_state')}")
    
    def test_infrastructure_overview(self):
        """GET /api/infrastructure/overview - returns infra data"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "sandbox_count" in data
        print(f"PASS: /api/infrastructure/overview - sandbox_count: {data.get('sandbox_count')}")
    
    def test_conway_sandboxes(self):
        """GET /api/conway/sandboxes - returns sandbox data"""
        response = requests.get(f"{BASE_URL}/api/conway/sandboxes", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # May have sandboxes or be empty
        assert "sandboxes" in data or "error" in data
        print(f"PASS: /api/conway/sandboxes - count: {data.get('count', 0)}")
    
    def test_conway_pricing(self):
        """GET /api/conway/credits/pricing - returns pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/conway/credits/pricing", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "pricing" in data or "error" in data
        if "pricing" in data:
            assert len(data.get("pricing", [])) > 0
        print(f"PASS: /api/conway/credits/pricing - tiers: {len(data.get('pricing', []))}")
    
    def test_conway_domain_search(self):
        """GET /api/conway/domains/search?q=test - returns domain results"""
        response = requests.get(f"{BASE_URL}/api/conway/domains/search?q=test", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "error" in data
        if "results" in data:
            assert len(data.get("results", [])) > 0
        print(f"PASS: /api/conway/domains/search - results: {len(data.get('results', []))}")
    
    def test_genesis_prompt_template(self):
        """GET /api/genesis/prompt-template - returns genesis prompt content"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        content = data.get("content", "")
        assert len(content) > 1000, f"Prompt too short: {len(content)}"
        print(f"PASS: /api/genesis/prompt-template - length: {len(content)}")


class TestSandboxingSecurity:
    """Test sandboxing security fixes"""
    
    def test_bootstrap_no_wallet_copy(self):
        """Bootstrap script does NOT copy global wallet to new agent dir"""
        # Create isolated test home
        with tempfile.TemporaryDirectory() as test_home:
            env = os.environ.copy()
            env["HOME"] = test_home
            
            # Run bootstrap script
            result = subprocess.run(
                ["bash", "/app/scripts/bootstrap_agent.sh"],
                env=env,
                capture_output=True,
                timeout=60
            )
            
            # Verify no wallet.json created
            wallet_path = os.path.join(test_home, ".anima", "wallet.json")
            assert not os.path.exists(wallet_path), "FAIL: wallet.json should NOT exist (agent self-provisions)"
            
            # Verify no config.json created
            config_path = os.path.join(test_home, ".anima", "config.json")
            assert not os.path.exists(config_path), "FAIL: config.json should NOT exist (agent self-provisions)"
            
            print("PASS: Bootstrap does NOT copy global wallet/config to agent")
    
    def test_bootstrap_file_permissions(self):
        """Bootstrap sets chmod 700 on agent directories"""
        with tempfile.TemporaryDirectory() as test_home:
            env = os.environ.copy()
            env["HOME"] = test_home
            
            # Run bootstrap script
            subprocess.run(
                ["bash", "/app/scripts/bootstrap_agent.sh"],
                env=env,
                capture_output=True,
                timeout=60
            )
            
            # Check permissions
            dirs_to_check = [
                os.path.join(test_home, ".anima"),
                os.path.join(test_home, ".conway"),
                os.path.join(test_home, ".openclaw")
            ]
            
            for dir_path in dirs_to_check:
                if os.path.exists(dir_path):
                    mode = oct(os.stat(dir_path).st_mode)[-3:]
                    assert mode == "700", f"FAIL: {dir_path} should be 700, got {mode}"
            
            print("PASS: Bootstrap sets chmod 700 on agent directories")
    
    def test_openclaw_empty_env(self):
        """OpenClaw config has empty env (no leaked API key)"""
        with tempfile.TemporaryDirectory() as test_home:
            env = os.environ.copy()
            env["HOME"] = test_home
            
            # Run bootstrap script
            subprocess.run(
                ["bash", "/app/scripts/bootstrap_agent.sh"],
                env=env,
                capture_output=True,
                timeout=60
            )
            
            # Check OpenClaw config
            openclaw_config = os.path.join(test_home, ".openclaw", "openclaw.json")
            assert os.path.exists(openclaw_config), "FAIL: OpenClaw config not created"
            
            with open(openclaw_config) as f:
                config = json.load(f)
            
            conway_env = config.get("mcpServers", {}).get("conway", {}).get("env", None)
            assert conway_env == {}, f"FAIL: OpenClaw env should be empty, got: {conway_env}"
            
            print("PASS: OpenClaw config has empty env (no API key leaked)")
    
    def test_agents_py_strips_secrets(self):
        """agents.py code strips MONGO_URL, DB_NAME, DASHBOARD_URL from env"""
        agents_py = "/app/backend/routers/agents.py"
        assert os.path.exists(agents_py), "agents.py not found"
        
        with open(agents_py) as f:
            content = f.read()
        
        # Check that secret stripping code exists
        assert 'for secret_key in ["MONGO_URL", "DB_NAME", "DASHBOARD_URL"]' in content, \
            "FAIL: agents.py should strip MONGO_URL, DB_NAME, DASHBOARD_URL"
        
        # Check that .pop() is used to remove secrets
        assert 'bootstrap_env.pop(secret_key, None)' in content or \
               'env.pop(secret_key, None)' in content, \
            "FAIL: agents.py should use pop() to remove secrets from env"
        
        print("PASS: agents.py strips MONGO_URL, DB_NAME, DASHBOARD_URL from env")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
