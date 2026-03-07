"""
Anima Fund API Tests - Comprehensive Backend Testing
Tests all API endpoints for the Anima Fund autonomous VC platform.

Test Coverage:
- /api/health - Health check with engine status
- /api/genesis/status - Genesis agent status
- /api/engine/live - Engine live status check
- /api/live/identity - Agent identity data
- /api/live/activity - Activity list
- /api/live/soul - SOUL.md content
- /api/engine/logs - Engine stdout/stderr logs
- /api/engine/status - Engine info and skills list
- /api/constitution - Constitution content
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""
    
    def test_health_returns_ok_status(self):
        """Health endpoint returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health status: {data['status']}")
    
    def test_health_contains_engine_live_field(self):
        """Health endpoint contains engine_live boolean"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "engine_live" in data
        assert isinstance(data["engine_live"], bool)
        print(f"✓ Engine live: {data['engine_live']}")
    
    def test_health_contains_engine_db_exists_field(self):
        """Health endpoint contains engine_db_exists boolean"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "engine_db_exists" in data
        assert isinstance(data["engine_db_exists"], bool)
        print(f"✓ Engine DB exists: {data['engine_db_exists']}")
    
    def test_health_contains_creator_wallet(self):
        """Health endpoint contains creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "creator_wallet" in data
        assert isinstance(data["creator_wallet"], str)
        assert len(data["creator_wallet"]) > 0
        print(f"✓ Creator wallet: {data['creator_wallet']}")


class TestGenesisStatusEndpoint:
    """Tests for /api/genesis/status endpoint"""
    
    def test_genesis_status_returns_200(self):
        """Genesis status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        print("✓ Genesis status endpoint accessible")
    
    def test_genesis_status_wallet_address(self):
        """Genesis status returns wallet address"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "wallet_address" in data
        # Wallet should be a valid Ethereum address (0x...)
        if data["wallet_address"]:
            assert data["wallet_address"].startswith("0x")
            assert len(data["wallet_address"]) == 42
        print(f"✓ Wallet address: {data['wallet_address']}")
    
    def test_genesis_status_engine_running(self):
        """Genesis status returns engine_running=true (as per context)"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "engine_running" in data
        assert isinstance(data["engine_running"], bool)
        # Per context note, engine_running should be true
        assert data["engine_running"] == True
        print(f"✓ Engine running: {data['engine_running']}")
    
    def test_genesis_status_stage_running(self):
        """Genesis status returns stage=running (as per context)"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "stage" in data
        assert data["stage"] == "running"
        print(f"✓ Stage: {data['stage']}")
    
    def test_genesis_status_config_fields(self):
        """Genesis status returns config field booleans"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        
        # Config existence fields
        assert "config_exists" in data
        assert "wallet_exists" in data
        assert "api_key_exists" in data
        assert "genesis_staged" in data
        
        # All should be true since engine is running
        assert data["config_exists"] == True
        assert data["wallet_exists"] == True
        print(f"✓ Config exists: {data['config_exists']}, Wallet exists: {data['wallet_exists']}")
    
    def test_genesis_status_creator_wallet(self):
        """Genesis status returns creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "creator_wallet" in data
        assert data["creator_wallet"] == "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"
        print(f"✓ Creator wallet: {data['creator_wallet']}")


class TestEngineLiveEndpoint:
    """Tests for /api/engine/live endpoint"""
    
    def test_engine_live_returns_200(self):
        """Engine live endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        print("✓ Engine live endpoint accessible")
    
    def test_engine_live_db_exists_true(self):
        """Engine live returns db_exists=true (state.db created)"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "db_exists" in data
        # Per context, state.db exists
        assert data["db_exists"] == True
        print(f"✓ DB exists: {data['db_exists']}")
    
    def test_engine_live_contains_state_info(self):
        """Engine live returns agent state and fund name"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        
        # Should have agent_state (sleeping due to no credits)
        if data.get("db_exists"):
            assert "agent_state" in data
            assert "fund_name" in data
            assert "turn_count" in data
            print(f"✓ Agent state: {data.get('agent_state')}, Fund name: {data.get('fund_name')}")


class TestLiveIdentityEndpoint:
    """Tests for /api/live/identity endpoint"""
    
    def test_live_identity_returns_200(self):
        """Live identity endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        print("✓ Live identity endpoint accessible")
    
    def test_live_identity_contains_name(self):
        """Live identity returns agent name"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        data = response.json()
        assert "name" in data
        # Per genesis, name should be "Anima Fund"
        assert data["name"] == "Anima Fund"
        print(f"✓ Agent name: {data['name']}")
    
    def test_live_identity_contains_wallet_address(self):
        """Live identity returns wallet address"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        data = response.json()
        assert "address" in data
        if data["address"]:
            assert data["address"].startswith("0x")
        print(f"✓ Wallet address: {data['address']}")


class TestLiveActivityEndpoint:
    """Tests for /api/live/activity endpoint"""
    
    def test_live_activity_returns_200(self):
        """Live activity endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        print("✓ Live activity endpoint accessible")
    
    def test_live_activity_returns_list(self):
        """Live activity returns activity list structure"""
        response = requests.get(f"{BASE_URL}/api/live/activity")
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
        assert "total" in data
        assert "source" in data
        assert data["source"] == "engine"
        print(f"✓ Activity count: {data['total']}")


class TestLiveSoulEndpoint:
    """Tests for /api/live/soul endpoint"""
    
    def test_live_soul_returns_200(self):
        """Live soul endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        print("✓ Live soul endpoint accessible")
    
    def test_live_soul_contains_content(self):
        """Live soul returns SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        data = response.json()
        assert "content" in data
        assert "exists" in data
        # Should have content since engine has created SOUL.md
        assert data["exists"] == True
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0
        # Check it contains expected content from genesis
        assert "Anima Fund" in data["content"]
        print(f"✓ SOUL.md exists: {data['exists']}, Content length: {len(data['content'])}")


class TestEngineLogsEndpoint:
    """Tests for /api/engine/logs endpoint"""
    
    def test_engine_logs_returns_200(self):
        """Engine logs endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        assert response.status_code == 200
        print("✓ Engine logs endpoint accessible")
    
    def test_engine_logs_structure(self):
        """Engine logs returns stdout, stderr, and anima_dir"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        data = response.json()
        assert "stdout" in data
        assert "stderr" in data
        assert "anima_dir" in data
        assert isinstance(data["anima_dir"], list)
        print(f"✓ Logs structure valid, anima_dir files: {len(data['anima_dir'])}")
    
    def test_engine_logs_anima_dir_files(self):
        """Engine logs returns list of ~/.anima files"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        data = response.json()
        anima_files = data["anima_dir"]
        
        # Should contain key files
        file_names = [f["name"] for f in anima_files]
        assert "state.db" in file_names
        assert "anima.json" in file_names
        assert "wallet.json" in file_names
        print(f"✓ Key files present: state.db, anima.json, wallet.json")
    
    def test_engine_logs_with_lines_param(self):
        """Engine logs accepts lines query parameter"""
        response = requests.get(f"{BASE_URL}/api/engine/logs?lines=20")
        assert response.status_code == 200
        print("✓ Lines parameter accepted")


class TestEngineStatusEndpoint:
    """Tests for /api/engine/status endpoint"""
    
    def test_engine_status_returns_200(self):
        """Engine status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        print("✓ Engine status endpoint accessible")
    
    def test_engine_status_contains_version(self):
        """Engine status returns version info"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "version" in data
        assert "engine" in data
        assert data["engine"] == "Anima Fund Runtime"
        print(f"✓ Engine: {data['engine']}, Version: {data['version']}")
    
    def test_engine_status_contains_skills(self):
        """Engine status returns skills list"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) > 0
        print(f"✓ Skills count: {len(data['skills'])}")
    
    def test_engine_status_built_flag(self):
        """Engine status returns built=true"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "built" in data
        assert data["built"] == True
        print(f"✓ Engine built: {data['built']}")
    
    def test_engine_status_creator_wallet(self):
        """Engine status returns creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "creator_wallet" in data
        assert data["creator_wallet"] == "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"
        print(f"✓ Creator wallet: {data['creator_wallet']}")


class TestConstitutionEndpoint:
    """Tests for /api/constitution endpoint"""
    
    def test_constitution_returns_200(self):
        """Constitution endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200
        print("✓ Constitution endpoint accessible")
    
    def test_constitution_contains_content(self):
        """Constitution returns content and path"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        data = response.json()
        assert "content" in data
        assert "path" in data
        assert isinstance(data["content"], str)
        assert len(data["content"]) > 0
        print(f"✓ Constitution content length: {len(data['content'])}")
    
    def test_constitution_content_valid(self):
        """Constitution content contains expected text"""
        response = requests.get(f"{BASE_URL}/api/constitution")
        data = response.json()
        # Should contain key constitution elements
        assert "Anima Fund" in data["content"]
        assert "Never harm" in data["content"]
        print("✓ Constitution contains expected content")


class TestAdditionalLiveEndpoints:
    """Tests for additional /api/live/* endpoints"""
    
    def test_live_agents_returns_200(self):
        """Live agents endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "source" in data
        print(f"✓ Live agents: {len(data['agents'])} agents")
    
    def test_live_turns_returns_200(self):
        """Live turns endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/turns")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        print(f"✓ Live turns: {len(data['turns'])} turns")
    
    def test_live_transactions_returns_200(self):
        """Live transactions endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        print(f"✓ Live transactions: {len(data['transactions'])} transactions")
    
    def test_live_financials_returns_200(self):
        """Live financials endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        print("✓ Live financials accessible")
    
    def test_live_memory_returns_200(self):
        """Live memory endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        print(f"✓ Live memory: {len(data['facts'])} facts")
    
    def test_live_skills_returns_200(self):
        """Live skills endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/live/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        print(f"✓ Live skills: {len(data['skills'])} skills")


class TestNewLiveEndpoints:
    """Tests for new /api/live/* endpoints added for data display fixes"""
    
    def test_live_heartbeat_returns_200(self):
        """Live heartbeat endpoint returns 200 with history"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total" in data
        assert "source" in data
        assert data["source"] == "engine"
        # Verify we have heartbeat data (per context: ~30+ events)
        assert len(data["history"]) > 0
        print(f"✓ Live heartbeat: {len(data['history'])} events")
    
    def test_live_heartbeat_event_structure(self):
        """Heartbeat events have correct structure"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat?limit=5")
        data = response.json()
        if len(data["history"]) > 0:
            event = data["history"][0]
            assert "id" in event
            assert "task" in event
            assert "started_at" in event
            assert "result" in event
            # result should be success or failure
            assert event["result"] in ["success", "failure", "pending", None]
        print("✓ Heartbeat event structure verified")
    
    def test_live_kv_returns_200(self):
        """Live KV store endpoint returns 200 with items"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "source" in data
        assert data["source"] == "engine"
        # Verify we have KV data (per context: 16 items)
        assert len(data["items"]) > 0
        print(f"✓ Live KV: {len(data['items'])} items")
    
    def test_live_kv_item_structure(self):
        """KV items have correct structure"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        data = response.json()
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "key" in item
            assert "value" in item
            assert "raw" in item
        print("✓ KV item structure verified")
    
    def test_live_wake_events_returns_200(self):
        """Live wake events endpoint returns 200 with events"""
        response = requests.get(f"{BASE_URL}/api/live/wake-events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "source" in data
        assert data["source"] == "engine"
        # Verify we have wake event data (per context: 6 events)
        assert len(data["events"]) > 0
        print(f"✓ Live wake events: {len(data['events'])} events")
    
    def test_live_wake_event_structure(self):
        """Wake events have correct structure"""
        response = requests.get(f"{BASE_URL}/api/live/wake-events?limit=5")
        data = response.json()
        if len(data["events"]) > 0:
            event = data["events"][0]
            assert "id" in event
            assert "source" in event
            assert "reason" in event
            assert "created_at" in event
        print("✓ Wake event structure verified")
    
    def test_live_heartbeat_schedule_returns_200(self):
        """Live heartbeat schedule endpoint returns 200 with tasks"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat-schedule")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "source" in data
        assert data["source"] == "engine"
        # Verify we have schedule data (per context: 6 tasks)
        assert len(data["tasks"]) > 0
        print(f"✓ Live heartbeat schedule: {len(data['tasks'])} tasks")
    
    def test_live_heartbeat_schedule_task_structure(self):
        """Heartbeat schedule tasks have correct structure"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat-schedule")
        data = response.json()
        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            assert "task" in task
            assert "cron" in task
            assert "enabled" in task
            assert "run_count" in task
        print("✓ Heartbeat schedule task structure verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
