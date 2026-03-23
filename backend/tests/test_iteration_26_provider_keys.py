"""
Iteration 26: Provider Key Management Tests
Tests the BYOI (Bring Your Own Infrastructure) endpoints for Fly.io and Conway providers.
Critical bug fix: 'It fails when adding a new fly api key for a new agent'

Endpoints tested:
- GET /api/provision/provider-key-status?provider=fly
- GET /api/provision/provider-key-status?provider=conway
- POST /api/provision/set-provider-key (fly, conway, empty key validation)
- POST /api/provision/health-check
- POST /api/provision/reset-sandbox
- POST /api/provision/delete-sandbox
- Per-agent key isolation
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://anima-runtime.preview.emergentagent.com')

# Test credentials from review request
TEST_TELEGRAM_TOKEN = "8474833303:AAHAhnRoHSIZTEruDu4ic-tPvdzrnTadnrw"
TEST_TELEGRAM_CHAT_ID = "8613975358"


class TestProviderKeyStatus:
    """Tests for GET /api/provision/provider-key-status endpoint"""
    
    def test_fly_key_status_returns_configured(self):
        """GET /api/provision/provider-key-status?provider=fly returns configured status"""
        # First ensure anima-fund is selected (has fly key)
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        
        res = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
        assert res.status_code == 200
        data = res.json()
        
        assert "configured" in data
        assert "provider" in data
        assert data["provider"] == "fly"
        assert "app_name" in data
        assert "key_prefix" in data
        
        # anima-fund should have fly key configured
        assert data["configured"] == True
        assert data["key_prefix"].startswith("fm2_")
        print(f"Fly key status: configured={data['configured']}, app_name={data['app_name']}, prefix={data['key_prefix']}")
    
    def test_conway_key_status_returns_configured(self):
        """GET /api/provision/provider-key-status?provider=conway returns configured status"""
        # Ensure anima-fund is selected
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        
        res = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=conway", timeout=10)
        assert res.status_code == 200
        data = res.json()
        
        assert "configured" in data
        assert "provider" in data
        assert data["provider"] == "conway"
        assert "key_prefix" in data
        
        # anima-fund should have conway key configured
        assert data["configured"] == True
        assert data["key_prefix"].startswith("cnwy_k_")
        print(f"Conway key status: configured={data['configured']}, prefix={data['key_prefix']}")
    
    def test_unknown_provider_returns_not_configured(self):
        """GET /api/provision/provider-key-status?provider=unknown returns configured=false"""
        res = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=unknown", timeout=10)
        assert res.status_code == 200
        data = res.json()
        
        assert data["configured"] == False
        assert data["provider"] == "unknown"
        print(f"Unknown provider status: {data}")


class TestSetProviderKey:
    """Tests for POST /api/provision/set-provider-key endpoint"""
    
    def test_set_fly_key_empty_returns_400(self):
        """POST /api/provision/set-provider-key with empty key returns 400"""
        res = requests.post(
            f"{BASE_URL}/api/provision/set-provider-key",
            json={"provider": "fly", "api_key": ""},
            timeout=10
        )
        assert res.status_code == 400
        data = res.json()
        assert "detail" in data or "error" in data
        error_msg = data.get("detail") or data.get("error")
        assert "empty" in error_msg.lower()
        print(f"Empty key validation: {error_msg}")
    
    def test_set_fly_key_whitespace_only_returns_400(self):
        """POST /api/provision/set-provider-key with whitespace-only key returns 400"""
        res = requests.post(
            f"{BASE_URL}/api/provision/set-provider-key",
            json={"provider": "fly", "api_key": "   "},
            timeout=10
        )
        assert res.status_code == 400
        data = res.json()
        error_msg = data.get("detail") or data.get("error")
        assert "empty" in error_msg.lower()
        print(f"Whitespace key validation: {error_msg}")
    
    def test_set_fly_key_strips_flyv1_prefix(self):
        """POST /api/provision/set-provider-key strips 'FlyV1 ' prefix from key"""
        # Create a test agent first
        test_agent_id = f"TEST_fly_prefix_test_{int(time.time())}"
        create_res = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": test_agent_id.replace("_", " ").title(),
                "genesis_prompt": "Test agent for Fly prefix stripping",
                "telegram_bot_token": TEST_TELEGRAM_TOKEN,
                "telegram_chat_id": TEST_TELEGRAM_CHAT_ID,
            },
            timeout=10
        )
        
        if create_res.status_code != 200:
            pytest.skip(f"Could not create test agent: {create_res.text}")
        
        created_agent = create_res.json().get("agent", {})
        agent_id = created_agent.get("agent_id")
        
        try:
            # Select the test agent
            requests.post(f"{BASE_URL}/api/agents/{agent_id}/select", timeout=10)
            
            # Set a key with FlyV1 prefix
            test_key = "FlyV1 fm2_test_key_12345"
            res = requests.post(
                f"{BASE_URL}/api/provision/set-provider-key",
                json={"provider": "fly", "api_key": test_key},
                timeout=10
            )
            assert res.status_code == 200
            data = res.json()
            assert data.get("success") == True
            print(f"Set key with FlyV1 prefix: {data}")
            
            # Verify the prefix was stripped by checking key status
            status_res = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
            status_data = status_res.json()
            
            # The key_prefix should start with fm2_, not FlyV1
            assert status_data["configured"] == True
            assert status_data["key_prefix"].startswith("fm2_")
            assert not status_data["key_prefix"].startswith("FlyV1")
            print(f"Verified prefix stripped: {status_data['key_prefix']}")
            
        finally:
            # Cleanup: delete test agent and switch back to anima-fund
            requests.delete(f"{BASE_URL}/api/agents/{agent_id}", timeout=10)
            requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
    
    def test_set_conway_key_success(self):
        """POST /api/provision/set-provider-key with provider=conway stores key"""
        # Create a test agent
        test_agent_id = f"TEST_conway_key_test_{int(time.time())}"
        create_res = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": test_agent_id.replace("_", " ").title(),
                "genesis_prompt": "Test agent for Conway key",
                "telegram_bot_token": TEST_TELEGRAM_TOKEN,
                "telegram_chat_id": TEST_TELEGRAM_CHAT_ID,
            },
            timeout=10
        )
        
        if create_res.status_code != 200:
            pytest.skip(f"Could not create test agent: {create_res.text}")
        
        created_agent = create_res.json().get("agent", {})
        agent_id = created_agent.get("agent_id")
        
        try:
            # Select the test agent
            requests.post(f"{BASE_URL}/api/agents/{agent_id}/select", timeout=10)
            
            # Set Conway key
            test_key = "cnwy_k_test_key_12345"
            res = requests.post(
                f"{BASE_URL}/api/provision/set-provider-key",
                json={"provider": "conway", "api_key": test_key},
                timeout=10
            )
            assert res.status_code == 200
            data = res.json()
            assert data.get("success") == True
            print(f"Set Conway key: {data}")
            
            # Verify key was stored
            status_res = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=conway", timeout=10)
            status_data = status_res.json()
            assert status_data["configured"] == True
            assert status_data["key_prefix"].startswith("cnwy_k_test")
            print(f"Verified Conway key stored: {status_data['key_prefix']}")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/agents/{agent_id}", timeout=10)
            requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
    
    def test_set_unknown_provider_returns_400(self):
        """POST /api/provision/set-provider-key with unknown provider returns 400"""
        res = requests.post(
            f"{BASE_URL}/api/provision/set-provider-key",
            json={"provider": "unknown_provider", "api_key": "some_key"},
            timeout=10
        )
        assert res.status_code == 400
        data = res.json()
        error_msg = data.get("detail") or data.get("error")
        assert "unknown" in error_msg.lower() or "provider" in error_msg.lower()
        print(f"Unknown provider error: {error_msg}")


class TestSandboxManagement:
    """Tests for sandbox management endpoints"""
    
    def test_health_check_no_sandbox(self):
        """POST /api/provision/health-check returns error when no sandbox"""
        # Ensure anima-fund is selected (may not have active sandbox)
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)
        
        res = requests.post(f"{BASE_URL}/api/provision/health-check", timeout=30)
        assert res.status_code == 200
        data = res.json()
        
        # Should return success=false if no sandbox, or success=true with health info
        assert "success" in data
        if not data["success"]:
            assert "error" in data
            print(f"Health check (no sandbox): {data['error']}")
        else:
            print(f"Health check (sandbox active): engine_running={data.get('engine_running')}")
    
    def test_reset_sandbox_no_sandbox(self):
        """POST /api/provision/reset-sandbox returns error when no sandbox"""
        res = requests.post(f"{BASE_URL}/api/provision/reset-sandbox", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Should return success=false if no sandbox
        if not data.get("success"):
            assert "error" in data
            assert "no" in data["error"].lower() and "sandbox" in data["error"].lower()
            print(f"Reset sandbox (no sandbox): {data['error']}")
        else:
            print(f"Reset sandbox: {data.get('message')}")
    
    def test_delete_sandbox_no_sandbox(self):
        """POST /api/provision/delete-sandbox returns error when no sandbox"""
        res = requests.post(f"{BASE_URL}/api/provision/delete-sandbox", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Should return success=false if no sandbox
        if not data.get("success"):
            assert "error" in data
            assert "no" in data["error"].lower() and "sandbox" in data["error"].lower()
            print(f"Delete sandbox (no sandbox): {data['error']}")
        else:
            print(f"Delete sandbox: {data.get('message')}")


class TestPerAgentKeyIsolation:
    """Tests for per-agent key isolation"""
    
    def test_agent_a_key_not_visible_to_agent_b(self):
        """Agent A's Fly key should not leak to Agent B"""
        # Create two test agents
        agent_a_id = f"TEST_agent_a_{int(time.time())}"
        agent_b_id = f"TEST_agent_b_{int(time.time())}"
        
        # Create agent A
        create_a = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": agent_a_id.replace("_", " ").title(),
                "genesis_prompt": "Test agent A",
                "telegram_bot_token": TEST_TELEGRAM_TOKEN,
                "telegram_chat_id": TEST_TELEGRAM_CHAT_ID,
            },
            timeout=30
        )
        if create_a.status_code != 200:
            pytest.skip(f"Could not create agent A: {create_a.text}")
        agent_a = create_a.json().get("agent", {}).get("agent_id")
        
        # Create agent B
        create_b = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": agent_b_id.replace("_", " ").title(),
                "genesis_prompt": "Test agent B",
                "telegram_bot_token": TEST_TELEGRAM_TOKEN,
                "telegram_chat_id": TEST_TELEGRAM_CHAT_ID,
            },
            timeout=10
        )
        if create_b.status_code != 200:
            requests.delete(f"{BASE_URL}/api/agents/{agent_a}", timeout=10)
            pytest.skip(f"Could not create agent B: {create_b.text}")
        agent_b = create_b.json().get("agent", {}).get("agent_id")
        
        try:
            # Select agent A and set a unique Fly key
            requests.post(f"{BASE_URL}/api/agents/{agent_a}/select", timeout=10)
            unique_key_a = "fm2_unique_key_for_agent_a_12345"
            requests.post(
                f"{BASE_URL}/api/provision/set-provider-key",
                json={"provider": "fly", "api_key": unique_key_a},
                timeout=10
            )
            
            # Verify agent A has the key
            status_a = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
            assert status_a.json()["configured"] == True
            # Key prefix is truncated to first 12 chars + "...", so check for fm2_unique
            assert status_a.json()["key_prefix"].startswith("fm2_unique")
            print(f"Agent A key: {status_a.json()['key_prefix']}")
            
            # Switch to agent B
            requests.post(f"{BASE_URL}/api/agents/{agent_b}/select", timeout=10)
            
            # Check agent B's key status - should NOT have agent A's key
            status_b = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
            status_b_data = status_b.json()
            
            # Agent B should either have no key or a different key (from env fallback)
            if status_b_data["configured"]:
                # If configured, it should NOT be agent A's unique key (starts with fm2_unique)
                assert not status_b_data.get("key_prefix", "").startswith("fm2_unique")
                print(f"Agent B key (from env fallback): {status_b_data['key_prefix']}")
            else:
                print(f"Agent B has no Fly key configured (expected)")
            
            print("Per-agent key isolation verified: Agent A's key not visible to Agent B")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/agents/{agent_a}", timeout=10)
            requests.delete(f"{BASE_URL}/api/agents/{agent_b}", timeout=10)
            requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)


class TestFullWorkflow:
    """Full workflow test: Create agent -> Add Fly key -> Verify -> Cleanup"""
    
    def test_full_fly_key_workflow(self):
        """Full workflow: Create new agent -> Select it -> Add Fly key -> Verify key status -> Clean up"""
        test_agent_name = f"TEST Fly Workflow {int(time.time())}"
        
        # Step 1: Create new agent
        create_res = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": test_agent_name,
                "genesis_prompt": "Test agent for Fly.io workflow",
                "telegram_bot_token": TEST_TELEGRAM_TOKEN,
                "telegram_chat_id": TEST_TELEGRAM_CHAT_ID,
            },
            timeout=10
        )
        assert create_res.status_code == 200, f"Failed to create agent: {create_res.text}"
        agent_data = create_res.json()
        assert agent_data.get("success") == True
        agent_id = agent_data.get("agent", {}).get("agent_id")
        assert agent_id is not None
        print(f"Step 1: Created agent '{agent_id}'")
        
        try:
            # Step 2: Select the new agent
            select_res = requests.post(f"{BASE_URL}/api/agents/{agent_id}/select", timeout=10)
            assert select_res.status_code == 200
            assert select_res.json().get("success") == True
            print(f"Step 2: Selected agent '{agent_id}'")
            
            # Step 3: Verify no Fly key initially (should fall back to env or be unconfigured)
            initial_status = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
            assert initial_status.status_code == 200
            initial_data = initial_status.json()
            print(f"Step 3: Initial Fly key status: configured={initial_data['configured']}")
            
            # Step 4: Add Fly key
            test_fly_key = "fm2_workflow_test_key_67890"
            set_key_res = requests.post(
                f"{BASE_URL}/api/provision/set-provider-key",
                json={"provider": "fly", "api_key": test_fly_key},
                timeout=10
            )
            assert set_key_res.status_code == 200
            set_key_data = set_key_res.json()
            assert set_key_data.get("success") == True
            print(f"Step 4: Set Fly key: {set_key_data.get('message')}")
            
            # Step 5: Verify key status shows configured
            final_status = requests.get(f"{BASE_URL}/api/provision/provider-key-status?provider=fly", timeout=10)
            assert final_status.status_code == 200
            final_data = final_status.json()
            assert final_data["configured"] == True
            assert final_data["key_prefix"].startswith("fm2_workflow")
            print(f"Step 5: Verified Fly key configured: {final_data['key_prefix']}")
            
            print("Full workflow completed successfully!")
            
        finally:
            # Step 6: Cleanup - delete test agent
            delete_res = requests.delete(f"{BASE_URL}/api/agents/{agent_id}", timeout=10)
            if delete_res.status_code == 200:
                print(f"Step 6: Cleaned up agent '{agent_id}'")
            else:
                print(f"Step 6: Warning - could not delete agent: {delete_res.text}")
            
            # Switch back to anima-fund
            requests.post(f"{BASE_URL}/api/agents/anima-fund/select", timeout=10)


class TestAgentCRUD:
    """Tests for agent CRUD operations related to provider keys"""
    
    def test_create_agent_requires_telegram(self):
        """POST /api/agents/create requires telegram credentials"""
        res = requests.post(
            f"{BASE_URL}/api/agents/create",
            json={
                "name": "Test No Telegram",
                "genesis_prompt": "Test",
            },
            timeout=10
        )
        assert res.status_code == 400
        data = res.json()
        error_msg = data.get("detail") or data.get("error")
        assert "telegram" in error_msg.lower()
        print(f"Telegram required validation: {error_msg}")
    
    def test_select_nonexistent_agent_returns_404(self):
        """POST /api/agents/nonexistent/select returns 404"""
        res = requests.post(f"{BASE_URL}/api/agents/nonexistent-agent-12345/select", timeout=10)
        assert res.status_code == 404
        print("Nonexistent agent selection returns 404")
    
    def test_delete_default_agent_returns_400(self):
        """DELETE /api/agents/anima-fund returns 400 (cannot delete default)"""
        res = requests.delete(f"{BASE_URL}/api/agents/anima-fund", timeout=10)
        assert res.status_code == 400
        data = res.json()
        error_msg = data.get("detail") or data.get("error")
        assert "default" in error_msg.lower() or "cannot" in error_msg.lower()
        print(f"Cannot delete default agent: {error_msg}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
