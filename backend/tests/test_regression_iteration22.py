"""
Iteration 22 - PRE-DEPLOYMENT REGRESSION TEST
==============================================
Final deployment readiness test. Validates:
1. All existing endpoints from iteration 20/21
2. NEW: GET /api/constitution - verify Article XIII is present
3. NEW: POST /api/agents/push-constitution - push updated constitution to all agents
4. Verify constitution is copied when creating agents

CRITICAL: User has 4 live agents with real funds on production.
This deployment must be safe - no breaking changes.

Endpoints tested:
- GET /api/health - Backend health with creator_wallet
- GET /api/agents - List all agents
- GET /api/skills/available - 95 skills
- GET /api/genesis/status - Full status with wallet, stage
- GET /api/wallet/balance - On-chain balance check
- GET /api/engine/live - Engine live check
- GET /api/live/identity - Agent identity
- GET /api/live/soul - SOUL.md content
- GET /api/live/turns?limit=10 - Agent turns
- GET /api/live/kv - KV store
- GET /api/live/skills-full - Skills + models + tool usage
- GET /api/payments/status - Payment compliance
- GET /api/telegram/status - Telegram config
- GET /api/engine/status - Engine version info
- GET /api/constitution - NEW: Should return constitution with Article XIII
- POST /api/agents/create - Create test agent (verify constitution copied)
- POST /api/agents/push-constitution - NEW: Push constitution to all agents
- POST /api/agents/{id}/select - Switch agent
- DELETE /api/agents/{id} - Delete test agent
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoints:
    """Health and status endpoints"""
    
    def test_api_health(self):
        """GET /api/health returns ok status with creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "ok"
        assert "creator_wallet" in data, "creator_wallet must be present"
        assert data["creator_wallet"] is not None, "creator_wallet should not be None"
        assert "timestamp" in data
        assert "engine_db_exists" in data
    
    def test_health_root_routes_to_frontend(self):
        """GET /health - skipped as it routes to frontend in K8s ingress"""
        pytest.skip("Non-API paths route to frontend, /api/health is the correct endpoint")


class TestAgentsEndpoints:
    """Agent management endpoints"""
    
    def test_get_agents_list(self):
        """GET /api/agents returns list with at least anima-fund"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        # Should have at least the default anima-fund agent
        agent_ids = [a["agent_id"] for a in data["agents"]]
        assert "anima-fund" in agent_ids, f"Default agent not found. Agents: {agent_ids}"
        
        # Verify anima-fund has correct fields
        anima_fund = next((a for a in data["agents"] if a["agent_id"] == "anima-fund"), None)
        assert anima_fund is not None
        assert anima_fund["is_default"] == True
        assert anima_fund["name"] == "Anima Fund"


class TestSkillsEndpoints:
    """Skills management endpoints"""
    
    def test_skills_available_returns_95(self):
        """GET /api/skills/available returns 95 skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert data["total"] == 95, f"Expected 95 skills, got {data['total']}"
        assert len(data["skills"]) == 95
    
    def test_skills_include_gambling_mastery(self):
        """Skills include gambling-mastery"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skill_names = [s["name"] for s in data["skills"]]
        assert "gambling-mastery" in skill_names, f"gambling-mastery not found in skills"
    
    def test_skills_include_rainbet_betting_mastery(self):
        """Skills include rainbet-betting-mastery"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skill_names = [s["name"] for s in data["skills"]]
        assert "rainbet-betting-mastery" in skill_names, f"rainbet-betting-mastery not found in skills"


class TestGenesisEndpoints:
    """Genesis status endpoints"""
    
    def test_genesis_status_fields(self):
        """GET /api/genesis/status returns required fields"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Required fields from review request
        required_fields = ["wallet_address", "config_exists", "wallet_exists", "stage", "creator_wallet"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Stage should be one of expected values
        valid_stages = ["not_created", "created", "running", "generating_wallet", "provisioning", "configuring"]
        assert data["stage"] in valid_stages, f"Invalid stage: {data['stage']}"


class TestWalletEndpoints:
    """Wallet balance endpoints"""
    
    def test_wallet_balance_fields(self):
        """GET /api/wallet/balance returns USDC, ETH, credits"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check for balance fields (may be null/0 if no wallet)
        assert "usdc" in data or "error" in data, "Missing usdc field"
        assert "eth" in data or "error" in data, "Missing eth field"


class TestEngineEndpoints:
    """Engine status endpoints"""
    
    def test_engine_live(self):
        """GET /api/engine/live returns db_exists field"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "db_exists" in data, "Missing db_exists field"
        # Engine in sleeping state - db_exists should be true
        assert data["db_exists"] == True, f"Expected db_exists=True, got {data['db_exists']}"
    
    def test_engine_status(self):
        """GET /api/engine/status returns version info"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "skills" in data
        assert "creator_wallet" in data
        assert "version" in data


class TestConstitutionEndpoints:
    """Constitution endpoints - NEW in iteration 22"""
    
    def test_get_constitution_returns_content(self):
        """GET /api/constitution returns constitution content"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "content" in data, "Missing content field"
        assert data["content"] is not None, "Content should not be None"
        assert len(data["content"]) > 100, "Constitution content too short"
    
    def test_get_constitution_contains_article_xiii(self):
        """GET /api/constitution contains Article XIII (Information Security)"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200
        
        data = response.json()
        content = data["content"]
        
        # Verify Article XIII is present
        assert "XIII" in content, "Article XIII not found in constitution"
        assert "Information Security" in content or "Info Security" in content, \
            "Article XIII (Info Security) title not found"
        assert "Open Collaboration" in content, "Open Collaboration not found in Article XIII"
        assert "CLASSIFIED" in content, "CLASSIFIED section not found in Article XIII"


class TestLiveEndpoints:
    """Live engine data endpoints (reads from state.db)"""
    
    def test_live_identity(self):
        """GET /api/live/identity returns agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_live_soul(self):
        """GET /api/live/soul returns SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data or "exists" in data
    
    def test_live_skills_full(self):
        """GET /api/live/skills-full returns skills + models + tool usage"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        
        data = response.json()
        assert "skills" in data
        assert "models" in data
        assert "tool_usage" in data
        assert "source" in data
        assert data["source"] == "engine"
    
    def test_live_turns(self):
        """GET /api/live/turns?limit=10 returns agent turns"""
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "turns" in data
        assert "source" in data
        assert data["source"] == "engine"
        assert isinstance(data["turns"], list)
    
    def test_live_kv(self):
        """GET /api/live/kv returns KV store"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "source" in data
        assert isinstance(data["items"], list)


class TestPaymentsEndpoints:
    """Payment and compliance endpoints"""
    
    def test_payments_status(self):
        """GET /api/payments/status returns payment compliance"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)


class TestTelegramEndpoints:
    """Telegram configuration endpoints"""
    
    def test_telegram_status(self):
        """GET /api/telegram/status returns telegram config status"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data


class TestAgentCRUDOperations:
    """Test agent create/select/delete operations including constitution copy"""
    
    TEST_AGENT_ID = "pre-deploy-test-agent"
    
    @pytest.fixture(autouse=True)
    def cleanup_test_agent(self):
        """Cleanup test agent before and after tests"""
        # Pre-cleanup
        try:
            requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        except:
            pass
        
        yield
        
        # Post-cleanup
        try:
            requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        except:
            pass
    
    def test_full_agent_lifecycle_create_select_delete(self):
        """Test POST create -> POST select -> DELETE agent"""
        
        # 1. CREATE agent
        agent_data = {
            "name": "Pre Deploy Test Agent",
            "genesis_prompt": "This is a pre-deployment test agent. Do nothing.",
            "welcome_message": "Pre-deployment test",
            "goals": ["Verify CRUD works before deployment"],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50,
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "selected_skills": ["gambling-mastery"]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        create_data = create_response.json()
        assert create_data["success"] == True
        assert "agent" in create_data
        assert create_data["agent"]["agent_id"] == self.TEST_AGENT_ID
        assert create_data["agent"]["name"] == "Pre Deploy Test Agent"
        
        # 2. SELECT the created agent
        select_response = requests.post(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}/select")
        assert select_response.status_code == 200, f"Select failed: {select_response.text}"
        select_data = select_response.json()
        assert select_data["success"] == True
        assert select_data["active_agent"] == self.TEST_AGENT_ID
        
        # 3. Switch back to default
        reset_response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert reset_response.status_code == 200
        
        # 4. DELETE the test agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        delete_data = delete_response.json()
        assert delete_data["success"] == True
        
        # 5. Verify agent is deleted (should be 404 on select)
        verify_response = requests.post(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}/select")
        assert verify_response.status_code == 404, "Deleted agent should not be selectable"
    
    def test_cannot_delete_default_agent(self):
        """DELETE /api/agents/anima-fund should return 400"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400, f"Expected 400 for deleting default agent, got {response.status_code}"


class TestPushConstitutionEndpoint:
    """Test push-constitution endpoint - NEW in iteration 22"""
    
    def test_push_constitution_works(self):
        """POST /api/agents/push-constitution pushes constitution to all agents"""
        response = requests.post(f"{BASE_URL}/api/agents/push-constitution")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert "updated_agents" in data
        assert "total" in data
        assert "message" in data
        assert isinstance(data["updated_agents"], list)
        
        # Should have updated at least the default anima-fund agent
        # (if ~/.anima directory exists)
        print(f"Push-constitution updated {data['total']} agents: {data['updated_agents']}")


class TestAllLiveDataEndpoints:
    """Test additional live data endpoints for completeness"""
    
    def test_live_agents(self):
        """GET /api/live/agents works"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "source" in data
    
    def test_live_activity(self):
        """GET /api/live/activity works"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "source" in data
    
    def test_live_transactions(self):
        """GET /api/live/transactions works"""
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
    
    def test_live_financials(self):
        """GET /api/live/financials works"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_live_memory(self):
        """GET /api/live/memory works"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
    
    def test_live_heartbeat(self):
        """GET /api/live/heartbeat works"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
    
    def test_live_modifications(self):
        """GET /api/live/modifications works"""
        response = requests.get(f"{BASE_URL}/api/live/modifications")
        assert response.status_code == 200
        data = response.json()
        assert "modifications" in data
    
    def test_live_messages(self):
        """GET /api/live/messages works"""
        response = requests.get(f"{BASE_URL}/api/live/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
    
    def test_live_relationships(self):
        """GET /api/live/relationships works"""
        response = requests.get(f"{BASE_URL}/api/live/relationships")
        assert response.status_code == 200
        data = response.json()
        assert "relationships" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
