"""
Iteration 23 - CRITICAL BUG FIX VALIDATION TEST
================================================
User reported CRITICAL production issues:
1) Two different wallets (engine generated new wallet, USDC on old wallet)
2) Dashboard glitching during rapid state cycling (sleeping→waking→running→critical→sleeping loop)
3) Lost agents/funds during deployment

Fixes applied by main agent:
1) wallet_mismatch detection in /api/wallet/balance
2) wallet_mismatch + engine_wallet fields in /api/genesis/status
3) Wallet preservation in genesis/create endpoint
4) Adaptive polling in frontend AgentMind component
5) Wallet mismatch UI warning in frontend

Endpoints tested (NEW FIELDS highlighted):
- GET /api/health - Backend health
- GET /api/agents - List all agents
- GET /api/skills/available - 96 skills (includes NEW negotiation-mastery)
- GET /api/genesis/status - NEW: engine_wallet, wallet_mismatch fields
- GET /api/wallet/balance - NEW: wallet_mismatch field
- GET /api/live/identity - Returns identity with address
- GET /api/live/kv - KV store
- GET /api/live/soul - SOUL.md content
- GET /api/payments/status - Payment compliance
- GET /api/telegram/status - Telegram config
- POST /api/agents/create - Create test agent with constitution
- POST /api/agents/push-constitution - Push constitution to all
- DELETE /api/agents/{id} - Cleanup test agent

Context: User has 4 live agents with real funds. Config wallet: 0x700e6b8f...
In dev environment both wallets match so wallet_mismatch=false, but field MUST be present.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


# ============================================================================
# CRITICAL NEW FIELDS TESTS (Bug Fix Validation)
# ============================================================================

class TestWalletMismatchDetection:
    """CRITICAL: Validate wallet_mismatch field in /api/wallet/balance
    This was the PRIMARY bug - user had USDC on old wallet, engine using new wallet."""
    
    def test_wallet_balance_has_wallet_mismatch_field(self):
        """GET /api/wallet/balance MUST return wallet_mismatch field (boolean)"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # CRITICAL: wallet_mismatch field MUST be present
        assert "wallet_mismatch" in data, "CRITICAL BUG: wallet_mismatch field missing from /api/wallet/balance"
        assert isinstance(data["wallet_mismatch"], bool), f"wallet_mismatch must be boolean, got {type(data['wallet_mismatch'])}"
        
        # In dev environment, wallets should match
        assert data["wallet_mismatch"] == False, "In dev env, wallet_mismatch should be False (wallets match)"
        
        print(f"wallet_mismatch = {data['wallet_mismatch']} - Field present and correct")
    
    def test_wallet_balance_returns_all_balance_fields(self):
        """GET /api/wallet/balance returns USDC, ETH, credits, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        
        data = response.json()
        
        # Standard balance fields
        assert "wallet" in data, "wallet field missing"
        assert "usdc" in data, "usdc field missing"
        assert "eth" in data, "eth field missing"
        assert "credits_cents" in data, "credits_cents field missing"
        assert "tier" in data, "tier field missing"
        
        print(f"Balance: wallet={data['wallet'][:10]}..., usdc={data['usdc']}, eth={data['eth']}, tier={data['tier']}")


class TestGenesisStatusWalletFields:
    """CRITICAL: Validate engine_wallet and wallet_mismatch fields in /api/genesis/status
    These fields are essential for detecting wallet mismatch after re-genesis."""
    
    def test_genesis_status_has_engine_wallet_field(self):
        """GET /api/genesis/status MUST return engine_wallet field"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # CRITICAL: engine_wallet field MUST be present
        assert "engine_wallet" in data, "CRITICAL BUG: engine_wallet field missing from /api/genesis/status"
        
        # engine_wallet should be the same as wallet_address in dev env
        wallet_address = data.get("wallet_address")
        engine_wallet = data.get("engine_wallet")
        
        print(f"wallet_address = {wallet_address}")
        print(f"engine_wallet = {engine_wallet}")
        
        # In dev env where engine has state.db, both should exist
        if wallet_address and engine_wallet:
            print(f"Both wallets detected: config={wallet_address[:10]}..., engine={engine_wallet[:10]}...")
    
    def test_genesis_status_has_wallet_mismatch_field(self):
        """GET /api/genesis/status MUST return wallet_mismatch field (boolean)"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # CRITICAL: wallet_mismatch field MUST be present
        assert "wallet_mismatch" in data, "CRITICAL BUG: wallet_mismatch field missing from /api/genesis/status"
        assert isinstance(data["wallet_mismatch"], bool), f"wallet_mismatch must be boolean, got {type(data['wallet_mismatch'])}"
        
        # In dev environment, wallets should match
        assert data["wallet_mismatch"] == False, "In dev env, wallet_mismatch should be False"
        
        print(f"genesis/status wallet_mismatch = {data['wallet_mismatch']}")
    
    def test_genesis_status_all_required_fields(self):
        """GET /api/genesis/status returns all required fields from previous iterations"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        
        data = response.json()
        
        required_fields = [
            "wallet_address", "engine_wallet", "wallet_mismatch",  # NEW in iteration 23
            "config_exists", "wallet_exists", "stage", "creator_wallet",  # Previous fields
            "qr_code", "api_key_exists", "genesis_staged", "engine_live",
            "engine_running", "engine_state", "fund_name", "turn_count", "status"
        ]
        
        missing = [f for f in required_fields if f not in data]
        assert not missing, f"Missing fields in genesis/status: {missing}"
        
        print(f"All {len(required_fields)} required fields present")


# ============================================================================
# NEW SKILL TEST (negotiation-mastery)
# ============================================================================

class TestSkillsUpdate:
    """Validate 96 skills including new negotiation-mastery"""
    
    def test_skills_available_returns_96(self):
        """GET /api/skills/available returns 96 skills (was 95 in iteration 22)"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        assert "skills" in data
        assert "total" in data
        
        # Updated from 95 to 96 with new negotiation-mastery skill
        assert data["total"] == 96, f"Expected 96 skills (was 95), got {data['total']}"
        assert len(data["skills"]) == 96
        
        print(f"Skills count: {data['total']} (correct - was 95, now 96)")
    
    def test_skills_include_negotiation_mastery(self):
        """NEW: negotiation-mastery skill should exist"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        
        data = response.json()
        skill_names = [s["name"] for s in data["skills"]]
        
        assert "negotiation-mastery" in skill_names, "NEW negotiation-mastery skill not found"
        
        # Get the skill details
        negotiation_skill = next((s for s in data["skills"] if s["name"] == "negotiation-mastery"), None)
        assert negotiation_skill is not None
        assert "description" in negotiation_skill
        assert len(negotiation_skill["description"]) > 0, "negotiation-mastery should have a description"
        
        print(f"negotiation-mastery skill found: {negotiation_skill['description'][:50]}...")


# ============================================================================
# REGRESSION TESTS (Existing Endpoints)
# ============================================================================

class TestHealthEndpoints:
    """Health and status endpoints - regression tests"""
    
    def test_api_health(self):
        """GET /api/health returns ok status with creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "creator_wallet" in data
        assert data["creator_wallet"] is not None
        assert "timestamp" in data
        assert "engine_db_exists" in data


class TestAgentsEndpoints:
    """Agent management endpoints - regression tests"""
    
    def test_get_agents_list(self):
        """GET /api/agents returns list with at least anima-fund"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        agent_ids = [a["agent_id"] for a in data["agents"]]
        assert "anima-fund" in agent_ids


class TestLiveEndpoints:
    """Live engine data endpoints - regression tests"""
    
    def test_live_identity_returns_address(self):
        """GET /api/live/identity returns identity with address"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "address" in data, "identity should have address field"
        
        print(f"Live identity address: {data.get('address', 'N/A')}")
    
    def test_live_kv(self):
        """GET /api/live/kv returns KV store"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "source" in data
        assert isinstance(data["items"], list)
    
    def test_live_soul(self):
        """GET /api/live/soul returns SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data or "exists" in data


class TestPaymentsEndpoints:
    """Payment compliance endpoints - regression tests"""
    
    def test_payments_status(self):
        """GET /api/payments/status returns payment compliance"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)


class TestTelegramEndpoints:
    """Telegram configuration endpoints - regression tests"""
    
    def test_telegram_status(self):
        """GET /api/telegram/status returns telegram config status"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data


class TestEngineEndpoints:
    """Engine status endpoints - regression tests"""
    
    def test_engine_live(self):
        """GET /api/engine/live returns db_exists field"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "db_exists" in data


class TestConstitutionEndpoints:
    """Constitution endpoints - regression tests"""
    
    def test_get_constitution(self):
        """GET /api/constitution returns constitution content"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data
        assert data["content"] is not None


# ============================================================================
# AGENT CRUD TESTS (with cleanup)
# ============================================================================

class TestAgentCRUDWithCleanup:
    """Test agent create/select/delete operations - includes cleanup"""
    
    TEST_AGENT_ID = "test-wallet-fix-agent"
    
    @pytest.fixture(autouse=True)
    def cleanup_test_agent(self):
        """Cleanup test agent before and after tests"""
        try:
            requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        except:
            pass
        
        yield
        
        try:
            requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        except:
            pass
    
    def test_full_agent_lifecycle(self):
        """Test POST create -> POST select -> DELETE agent"""
        
        # 1. CREATE agent
        agent_data = {
            "name": "Test Wallet Fix Agent",
            "genesis_prompt": "Test agent for wallet mismatch fix validation.",
            "welcome_message": "Testing wallet fix",
            "goals": ["Verify wallet mismatch detection works"],
            "creator_sol_wallet": "",
            "creator_eth_wallet": "",
            "revenue_share_percent": 50,
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "selected_skills": ["negotiation-mastery"]  # Use new skill
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/agents/create",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        create_data = create_response.json()
        assert create_data["success"] == True
        assert create_data["agent"]["agent_id"] == self.TEST_AGENT_ID
        
        print(f"Created agent: {self.TEST_AGENT_ID}")
        
        # 2. SELECT the created agent
        select_response = requests.post(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}/select")
        assert select_response.status_code == 200
        
        # 3. Switch back to default
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        
        # 4. DELETE the test agent
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}")
        assert delete_response.status_code == 200
        
        # 5. Verify deleted
        verify_response = requests.post(f"{BASE_URL}/api/agents/{self.TEST_AGENT_ID}/select")
        assert verify_response.status_code == 404
        
        print("Agent lifecycle test passed - created, selected, deleted")
    
    def test_push_constitution_works(self):
        """POST /api/agents/push-constitution pushes constitution to all agents"""
        response = requests.post(f"{BASE_URL}/api/agents/push-constitution")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "updated_agents" in data
        assert "total" in data
        
        print(f"Push constitution updated {data['total']} agents")


class TestCannotDeleteDefaultAgent:
    """Cannot delete the default anima-fund agent"""
    
    def test_cannot_delete_anima_fund(self):
        """DELETE /api/agents/anima-fund should return 400"""
        response = requests.delete(f"{BASE_URL}/api/agents/anima-fund")
        assert response.status_code == 400


# ============================================================================
# ADDITIONAL LIVE DATA ENDPOINTS
# ============================================================================

class TestAllLiveDataEndpoints:
    """Test additional live data endpoints for completeness"""
    
    def test_live_agents(self):
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
    
    def test_live_activity(self):
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
    
    def test_live_transactions(self):
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
    
    def test_live_financials(self):
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
    
    def test_live_memory(self):
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
    
    def test_live_turns(self):
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
    
    def test_live_skills_full(self):
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
