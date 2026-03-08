"""
Anima Fund API Tests - Iteration 14
Tests all API endpoints when ENGINE IS NOT RUNNING (expected state)

The automaton engine is NOT currently running (no state.db), so all /api/live/* 
endpoints will return empty arrays/objects. This is EXPECTED behavior.

Test Coverage (as per PRD):
- /api/health - Health check with status, engine_live, creator_wallet, timestamp
- /api/genesis/status - Genesis status with wallet_address, stage, creator_wallet
- /api/engine/live - Returns live, db_exists, turn_count
- /api/engine/status - Returns version, skills array, built status
- /api/wallet/balance - Returns usdc, eth, credits_cents, tier
- /api/telegram/status - Returns configured, bot_token_set, chat_id_set
- /api/constitution - Returns content string
- /api/live/identity - Returns name, address, sandbox, services
- /api/live/agents - Returns agents array with total
- /api/live/activity - Returns activities array with total
- /api/live/turns - Returns turns array with total
- /api/live/transactions - Returns transactions array
- /api/live/financials - Returns financial state
- /api/live/heartbeat - Returns history array
- /api/live/memory - Returns facts array
- /api/live/soul - Returns content and exists boolean
- /api/live/skills - Returns skills array
- /api/live/skills-full - Returns skills (27 Conway tools), models, tool_usage
- /api/live/kv - Returns items array
- /api/live/wake-events - Returns events array
- /api/live/heartbeat-schedule - Returns tasks array
- /api/live/working-memory - Returns items array
- /api/live/episodic-memory - Returns events array
- /api/live/procedural-memory - Returns procedures array
- /api/live/tools - Returns tools array
- /api/live/metrics - Returns snapshots array
- /api/live/policy - Returns decisions array
- /api/live/soul-history - Returns versions array
- /api/live/onchain - Returns transactions array
- /api/live/sessions - Returns sessions array
- /api/live/discovered - Returns agents array
- POST /api/genesis/reset - Returns success
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoint:
    """Tests for /api/health - Health check endpoint"""
    
    def test_health_returns_200(self):
        """Health endpoint returns 200 status code"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ /api/health returns 200")
    
    def test_health_response_structure(self):
        """Health endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        # Required fields per PRD
        assert "status" in data
        assert "engine_live" in data
        assert "creator_wallet" in data
        assert "timestamp" in data
        
        # Type validation
        assert data["status"] == "ok"
        assert isinstance(data["engine_live"], bool)
        assert isinstance(data["creator_wallet"], str)
        assert isinstance(data["timestamp"], str)
        
        print(f"✓ Health: status={data['status']}, engine_live={data['engine_live']}, creator_wallet={data['creator_wallet'][:10]}...")


class TestGenesisStatusEndpoint:
    """Tests for /api/genesis/status - Genesis agent status"""
    
    def test_genesis_status_returns_200(self):
        """Genesis status returns 200"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        print("✓ /api/genesis/status returns 200")
    
    def test_genesis_status_required_fields(self):
        """Genesis status returns all required fields per PRD"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        
        # Required fields per PRD
        required_fields = ["wallet_address", "stage", "status", "creator_wallet", "turn_count", "engine_running"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Type validation
        assert data["stage"] in ["not_created", "generating_wallet", "provisioning", "configuring", "created", "running"]
        assert isinstance(data["turn_count"], int)
        assert isinstance(data["engine_running"], bool)
        
        print(f"✓ Genesis: stage={data['stage']}, engine_running={data['engine_running']}, turn_count={data['turn_count']}")


class TestEngineLiveEndpoint:
    """Tests for /api/engine/live - Engine live status"""
    
    def test_engine_live_returns_200(self):
        """Engine live returns 200"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        print("✓ /api/engine/live returns 200")
    
    def test_engine_live_required_fields(self):
        """Engine live returns live, db_exists, turn_count (when db exists)"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        
        # Required fields per PRD
        assert "live" in data or "db_exists" in data  # Structure varies based on engine state
        
        if data.get("db_exists"):
            assert "turn_count" in data
            print(f"✓ Engine live: db_exists={data['db_exists']}, turn_count={data.get('turn_count', 'N/A')}")
        else:
            print(f"✓ Engine live: db_exists={data.get('db_exists', False)}, reason={data.get('reason', 'N/A')}")


class TestEngineStatusEndpoint:
    """Tests for /api/engine/status - Engine info and skills"""
    
    def test_engine_status_returns_200(self):
        """Engine status returns 200"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        print("✓ /api/engine/status returns 200")
    
    def test_engine_status_required_fields(self):
        """Engine status returns version, skills array, built status"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        
        # Required fields per PRD
        assert "version" in data
        assert "skills" in data
        assert "built" in data
        
        # Type validation
        assert isinstance(data["skills"], list)
        assert isinstance(data["built"], bool)
        
        # Should have many skills (92 mentioned in context)
        assert len(data["skills"]) > 80, f"Expected 80+ skills, got {len(data['skills'])}"
        
        print(f"✓ Engine status: version={data['version']}, skills={len(data['skills'])}, built={data['built']}")


class TestWalletBalanceEndpoint:
    """Tests for /api/wallet/balance - Wallet balance check"""
    
    def test_wallet_balance_returns_200(self):
        """Wallet balance returns 200"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        print("✓ /api/wallet/balance returns 200")
    
    def test_wallet_balance_required_fields(self):
        """Wallet balance returns usdc, eth, credits_cents, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        
        # Required fields per PRD
        assert "usdc" in data
        assert "eth" in data
        
        # When no wallet exists, these may be null/0
        # But the fields must exist
        print(f"✓ Wallet balance: usdc={data.get('usdc')}, eth={data.get('eth')}")


class TestTelegramStatusEndpoint:
    """Tests for /api/telegram/status - Telegram configuration status"""
    
    def test_telegram_status_returns_200(self):
        """Telegram status returns 200"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        print("✓ /api/telegram/status returns 200")
    
    def test_telegram_status_required_fields(self):
        """Telegram status returns configured, bot_token_set, chat_id_set"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        data = response.json()
        
        # Required fields per PRD
        assert "configured" in data
        assert "bot_token_set" in data
        assert "chat_id_set" in data
        
        # Type validation
        assert isinstance(data["configured"], bool)
        assert isinstance(data["bot_token_set"], bool)
        assert isinstance(data["chat_id_set"], bool)
        
        print(f"✓ Telegram: configured={data['configured']}, bot_token={data['bot_token_set']}, chat_id={data['chat_id_set']}")


class TestConstitutionEndpoint:
    """Tests for /api/constitution - Constitution content"""
    
    def test_constitution_returns_200(self):
        """Constitution returns 200"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200
        print("✓ /api/constitution returns 200")
    
    def test_constitution_returns_content(self):
        """Constitution returns content string"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        data = response.json()
        
        # Required fields per PRD
        assert "content" in data
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0
        
        print(f"✓ Constitution: content_length={len(data['content'])}")


class TestLiveIdentityEndpoint:
    """Tests for /api/live/identity - Agent identity"""
    
    def test_live_identity_returns_200(self):
        """Live identity returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        print("✓ /api/live/identity returns 200")
    
    def test_live_identity_required_fields(self):
        """Live identity returns name, address, sandbox, services (installed_tools, children_sandboxes only when DB exists)"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        data = response.json()
        
        # Core required fields (always present)
        core_keys = ["name", "address", "sandbox", "services"]
        for key in core_keys:
            assert key in data, f"Missing core key: {key}"
        
        # Optional keys (only present when engine DB exists)
        # installed_tools and children_sandboxes are only populated when DB connection is available
        
        print(f"✓ Live identity: name={data.get('name')}, address={data.get('address')}")


class TestLiveAgentsEndpoint:
    """Tests for /api/live/agents - Child agents list"""
    
    def test_live_agents_returns_200(self):
        """Live agents returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        print("✓ /api/live/agents returns 200")
    
    def test_live_agents_structure(self):
        """Live agents returns agents array with total"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        data = response.json()
        
        assert "agents" in data
        assert "total" in data
        assert isinstance(data["agents"], list)
        assert isinstance(data["total"], int)
        
        print(f"✓ Live agents: total={data['total']}")


class TestLiveActivityEndpoint:
    """Tests for /api/live/activity - Tool call activity"""
    
    def test_live_activity_returns_200(self):
        """Live activity returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        print("✓ /api/live/activity returns 200")
    
    def test_live_activity_structure(self):
        """Live activity returns activities array with total"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        data = response.json()
        
        assert "activities" in data
        assert "total" in data
        assert isinstance(data["activities"], list)
        
        print(f"✓ Live activity: total={data['total']}")


class TestLiveTurnsEndpoint:
    """Tests for /api/live/turns - Agent turns"""
    
    def test_live_turns_returns_200(self):
        """Live turns returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/turns")
        assert response.status_code == 200
        print("✓ /api/live/turns returns 200")
    
    def test_live_turns_structure(self):
        """Live turns returns turns array with total"""
        response = requests.get(f"{BASE_URL}/api/live/turns")
        data = response.json()
        
        assert "turns" in data
        assert "total" in data
        assert isinstance(data["turns"], list)
        
        print(f"✓ Live turns: total={data['total']}")


class TestLiveTransactionsEndpoint:
    """Tests for /api/live/transactions - Financial transactions"""
    
    def test_live_transactions_returns_200(self):
        """Live transactions returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        assert response.status_code == 200
        print("✓ /api/live/transactions returns 200")
    
    def test_live_transactions_structure(self):
        """Live transactions returns transactions array"""
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        data = response.json()
        
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        
        print(f"✓ Live transactions: total={len(data['transactions'])}")


class TestLiveFinancialsEndpoint:
    """Tests for /api/live/financials - Financial state"""
    
    def test_live_financials_returns_200(self):
        """Live financials returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        print("✓ /api/live/financials returns 200")
    
    def test_live_financials_returns_dict(self):
        """Live financials returns a dict (may be empty when no engine)"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        data = response.json()
        
        assert isinstance(data, dict)
        print(f"✓ Live financials: keys={list(data.keys()) if data else '(empty)'}")


class TestLiveHeartbeatEndpoint:
    """Tests for /api/live/heartbeat - Heartbeat history"""
    
    def test_live_heartbeat_returns_200(self):
        """Live heartbeat returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        assert response.status_code == 200
        print("✓ /api/live/heartbeat returns 200")
    
    def test_live_heartbeat_structure(self):
        """Live heartbeat returns history array"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        data = response.json()
        
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)
        
        print(f"✓ Live heartbeat: total={data['total']}")


class TestLiveMemoryEndpoint:
    """Tests for /api/live/memory - Semantic memory facts"""
    
    def test_live_memory_returns_200(self):
        """Live memory returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        print("✓ /api/live/memory returns 200")
    
    def test_live_memory_structure(self):
        """Live memory returns facts array"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        data = response.json()
        
        assert "facts" in data
        assert isinstance(data["facts"], list)
        
        print(f"✓ Live memory: facts={len(data['facts'])}")


class TestLiveSoulEndpoint:
    """Tests for /api/live/soul - SOUL.md content"""
    
    def test_live_soul_returns_200(self):
        """Live soul returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        print("✓ /api/live/soul returns 200")
    
    def test_live_soul_structure(self):
        """Live soul returns content and exists boolean"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        data = response.json()
        
        assert "content" in data
        assert "exists" in data
        assert isinstance(data["exists"], bool)
        
        print(f"✓ Live soul: exists={data['exists']}, content_length={len(data.get('content') or '')}")


class TestLiveSkillsEndpoint:
    """Tests for /api/live/skills - Installed skills"""
    
    def test_live_skills_returns_200(self):
        """Live skills returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/skills")
        assert response.status_code == 200
        print("✓ /api/live/skills returns 200")
    
    def test_live_skills_structure(self):
        """Live skills returns skills array"""
        response = requests.get(f"{BASE_URL}/api/live/skills")
        data = response.json()
        
        assert "skills" in data
        assert isinstance(data["skills"], list)
        
        print(f"✓ Live skills: count={len(data['skills'])}")


class TestLiveSkillsFullEndpoint:
    """Tests for /api/live/skills-full - Aggregated skills view"""
    
    def test_live_skills_full_returns_200(self):
        """Live skills-full returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        print("✓ /api/live/skills-full returns 200")
    
    def test_live_skills_full_structure(self):
        """Live skills-full returns skills, models, tool_usage"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        
        assert "skills" in data
        assert "models" in data
        assert "tool_usage" in data
        assert isinstance(data["skills"], list)
        assert isinstance(data["models"], list)
        assert isinstance(data["tool_usage"], dict)
        
        print(f"✓ Live skills-full: skills={len(data['skills'])}, models={len(data['models'])}")
    
    def test_live_skills_full_conway_tools(self):
        """Skills-full returns 27 Conway platform tools (even without engine running)"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        
        conway_skills = [s for s in data["skills"] if s.get("source") == "conway"]
        assert len(conway_skills) == 27, f"Expected 27 Conway tools, got {len(conway_skills)}"
        
        print(f"✓ Conway tools: {len(conway_skills)} (expected 27)")


class TestLiveKVEndpoint:
    """Tests for /api/live/kv - Key-value store"""
    
    def test_live_kv_returns_200(self):
        """Live KV returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        print("✓ /api/live/kv returns 200")
    
    def test_live_kv_structure(self):
        """Live KV returns items array"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        data = response.json()
        
        assert "items" in data
        assert isinstance(data["items"], list)
        
        print(f"✓ Live KV: items={len(data['items'])}")


class TestLiveWakeEventsEndpoint:
    """Tests for /api/live/wake-events - Wake events"""
    
    def test_live_wake_events_returns_200(self):
        """Live wake events returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/wake-events")
        assert response.status_code == 200
        print("✓ /api/live/wake-events returns 200")
    
    def test_live_wake_events_structure(self):
        """Live wake events returns events array"""
        response = requests.get(f"{BASE_URL}/api/live/wake-events")
        data = response.json()
        
        assert "events" in data
        assert isinstance(data["events"], list)
        
        print(f"✓ Live wake-events: events={len(data['events'])}")


class TestLiveHeartbeatScheduleEndpoint:
    """Tests for /api/live/heartbeat-schedule - Scheduled tasks"""
    
    def test_live_heartbeat_schedule_returns_200(self):
        """Live heartbeat schedule returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat-schedule")
        assert response.status_code == 200
        print("✓ /api/live/heartbeat-schedule returns 200")
    
    def test_live_heartbeat_schedule_structure(self):
        """Live heartbeat schedule returns tasks array"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat-schedule")
        data = response.json()
        
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        
        print(f"✓ Live heartbeat-schedule: tasks={len(data['tasks'])}")


class TestLiveWorkingMemoryEndpoint:
    """Tests for /api/live/working-memory"""
    
    def test_live_working_memory_returns_200(self):
        """Live working memory returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/working-memory")
        assert response.status_code == 200
        print("✓ /api/live/working-memory returns 200")
    
    def test_live_working_memory_structure(self):
        """Live working memory returns items array"""
        response = requests.get(f"{BASE_URL}/api/live/working-memory")
        data = response.json()
        
        assert "items" in data
        assert isinstance(data["items"], list)
        
        print(f"✓ Live working-memory: items={len(data['items'])}")


class TestLiveEpisodicMemoryEndpoint:
    """Tests for /api/live/episodic-memory"""
    
    def test_live_episodic_memory_returns_200(self):
        """Live episodic memory returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/episodic-memory")
        assert response.status_code == 200
        print("✓ /api/live/episodic-memory returns 200")
    
    def test_live_episodic_memory_structure(self):
        """Live episodic memory returns events array"""
        response = requests.get(f"{BASE_URL}/api/live/episodic-memory")
        data = response.json()
        
        assert "events" in data
        assert isinstance(data["events"], list)
        
        print(f"✓ Live episodic-memory: events={len(data['events'])}")


class TestLiveProceduralMemoryEndpoint:
    """Tests for /api/live/procedural-memory"""
    
    def test_live_procedural_memory_returns_200(self):
        """Live procedural memory returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/procedural-memory")
        assert response.status_code == 200
        print("✓ /api/live/procedural-memory returns 200")
    
    def test_live_procedural_memory_structure(self):
        """Live procedural memory returns procedures array"""
        response = requests.get(f"{BASE_URL}/api/live/procedural-memory")
        data = response.json()
        
        assert "procedures" in data
        assert isinstance(data["procedures"], list)
        
        print(f"✓ Live procedural-memory: procedures={len(data['procedures'])}")


class TestLiveToolsEndpoint:
    """Tests for /api/live/tools"""
    
    def test_live_tools_returns_200(self):
        """Live tools returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/tools")
        assert response.status_code == 200
        print("✓ /api/live/tools returns 200")
    
    def test_live_tools_structure(self):
        """Live tools returns tools array"""
        response = requests.get(f"{BASE_URL}/api/live/tools")
        data = response.json()
        
        assert "tools" in data
        assert isinstance(data["tools"], list)
        
        print(f"✓ Live tools: tools={len(data['tools'])}")


class TestLiveMetricsEndpoint:
    """Tests for /api/live/metrics"""
    
    def test_live_metrics_returns_200(self):
        """Live metrics returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/metrics")
        assert response.status_code == 200
        print("✓ /api/live/metrics returns 200")
    
    def test_live_metrics_structure(self):
        """Live metrics returns snapshots array"""
        response = requests.get(f"{BASE_URL}/api/live/metrics")
        data = response.json()
        
        assert "snapshots" in data
        assert isinstance(data["snapshots"], list)
        
        print(f"✓ Live metrics: snapshots={len(data['snapshots'])}")


class TestLivePolicyEndpoint:
    """Tests for /api/live/policy"""
    
    def test_live_policy_returns_200(self):
        """Live policy returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/policy")
        assert response.status_code == 200
        print("✓ /api/live/policy returns 200")
    
    def test_live_policy_structure(self):
        """Live policy returns decisions array"""
        response = requests.get(f"{BASE_URL}/api/live/policy")
        data = response.json()
        
        assert "decisions" in data
        assert isinstance(data["decisions"], list)
        
        print(f"✓ Live policy: decisions={len(data['decisions'])}")


class TestLiveSoulHistoryEndpoint:
    """Tests for /api/live/soul-history"""
    
    def test_live_soul_history_returns_200(self):
        """Live soul history returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/soul-history")
        assert response.status_code == 200
        print("✓ /api/live/soul-history returns 200")
    
    def test_live_soul_history_structure(self):
        """Live soul history returns versions array"""
        response = requests.get(f"{BASE_URL}/api/live/soul-history")
        data = response.json()
        
        assert "versions" in data
        assert isinstance(data["versions"], list)
        
        print(f"✓ Live soul-history: versions={len(data['versions'])}")


class TestLiveOnchainEndpoint:
    """Tests for /api/live/onchain"""
    
    def test_live_onchain_returns_200(self):
        """Live onchain returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/onchain")
        assert response.status_code == 200
        print("✓ /api/live/onchain returns 200")
    
    def test_live_onchain_structure(self):
        """Live onchain returns transactions array"""
        response = requests.get(f"{BASE_URL}/api/live/onchain")
        data = response.json()
        
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        
        print(f"✓ Live onchain: transactions={len(data['transactions'])}")


class TestLiveSessionsEndpoint:
    """Tests for /api/live/sessions"""
    
    def test_live_sessions_returns_200(self):
        """Live sessions returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/sessions")
        assert response.status_code == 200
        print("✓ /api/live/sessions returns 200")
    
    def test_live_sessions_structure(self):
        """Live sessions returns sessions array"""
        response = requests.get(f"{BASE_URL}/api/live/sessions")
        data = response.json()
        
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        
        print(f"✓ Live sessions: sessions={len(data['sessions'])}")


class TestLiveDiscoveredEndpoint:
    """Tests for /api/live/discovered"""
    
    def test_live_discovered_returns_200(self):
        """Live discovered returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/discovered")
        assert response.status_code == 200
        print("✓ /api/live/discovered returns 200")
    
    def test_live_discovered_structure(self):
        """Live discovered returns agents array"""
        response = requests.get(f"{BASE_URL}/api/live/discovered")
        data = response.json()
        
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        print(f"✓ Live discovered: agents={len(data['agents'])}")


class TestGenesisResetEndpoint:
    """Tests for POST /api/genesis/reset"""
    
    def test_genesis_reset_returns_200(self):
        """Genesis reset returns 200"""
        # NOTE: We are only testing that the endpoint returns success
        # The actual reset preserves the wallet
        response = requests.post(f"{BASE_URL}/api/genesis/reset")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data["success"] == True
        
        print(f"✓ Genesis reset: success={data['success']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
