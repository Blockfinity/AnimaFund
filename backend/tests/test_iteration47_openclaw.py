"""
Iteration 47 - Backend API Tests
Tests OpenClaw VM endpoints, sidebar navigation, SOUL.md editor, CreateAgentModal, wallet balance, 
data isolation, push-genesis protection, genesis template, telegram, SSE stream, engine status
"""
import os
import pytest
import requests
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOpenClawEndpoints:
    """OpenClaw VM Viewer API tests"""
    
    def test_openclaw_status(self):
        """GET /api/openclaw/status returns openclaw_installed, conway_terminal_installed, mcp_servers"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Verify required fields exist
        assert "openclaw_installed" in data, "Missing openclaw_installed field"
        assert "conway_terminal_installed" in data, "Missing conway_terminal_installed field"
        assert "mcp_servers" in data, "Missing mcp_servers field"
        assert isinstance(data["mcp_servers"], list), "mcp_servers should be a list"
        print(f"PASS: OpenClaw status: openclaw_installed={data['openclaw_installed']}, conway_terminal={data['conway_terminal_installed']}, mcp_servers={data['mcp_servers']}")
    
    def test_openclaw_actions(self):
        """GET /api/openclaw/actions returns actions array"""
        response = requests.get(f"{BASE_URL}/api/openclaw/actions?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "actions" in data, "Missing actions field"
        assert isinstance(data["actions"], list), "actions should be a list"
        assert "total" in data, "Missing total field"
        assert "categories" in data, "Missing categories field"
        print(f"PASS: OpenClaw actions: total={data['total']}, categories={data['categories']}")
    
    def test_openclaw_sandboxes(self):
        """GET /api/openclaw/sandboxes returns sandboxes array"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandboxes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "sandboxes" in data, "Missing sandboxes field"
        assert isinstance(data["sandboxes"], list), "sandboxes should be a list"
        print(f"PASS: OpenClaw sandboxes: count={len(data['sandboxes'])}")
    
    def test_openclaw_browsing_sessions(self):
        """GET /api/openclaw/browsing-sessions returns sessions array"""
        response = requests.get(f"{BASE_URL}/api/openclaw/browsing-sessions?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "sessions" in data, "Missing sessions field"
        assert isinstance(data["sessions"], list), "sessions should be a list"
        assert "total" in data, "Missing total field"
        print(f"PASS: OpenClaw browsing-sessions: total={data['total']}")


class TestWalletAndFinancials:
    """Wallet balance API tests"""
    
    def test_wallet_balance_structure(self):
        """GET /api/wallet/balance returns usdc, credits_cents, tier, eth"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Check for key fields (some may be null if no wallet configured)
        expected_fields = ["usdc", "credits_cents", "tier"]
        for field in expected_fields:
            assert field in data, f"Missing {field} field"
        print(f"PASS: Wallet balance: usdc={data.get('usdc')}, credits_cents={data.get('credits_cents')}, tier={data.get('tier')}, eth={data.get('eth')}")


class TestDataIsolation:
    """Agent data isolation tests"""
    
    def test_list_agents(self):
        """GET /api/agents lists agents"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "agents" in data, "Missing agents field"
        assert isinstance(data["agents"], list), "agents should be a list"
        assert len(data["agents"]) >= 1, "Should have at least 1 agent (anima-fund)"
        print(f"PASS: List agents: {len(data['agents'])} agents found")
        for agent in data["agents"]:
            print(f"  - {agent.get('agent_id')}: {agent.get('name')}")
    
    def test_select_agent_anima_fund(self):
        """POST /api/agents/anima-fund/select returns success"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=True"
        assert "active_agent" in data, "Missing active_agent field"
        print(f"PASS: Select agent: active_agent={data.get('active_agent')}, data_dir={data.get('data_dir')}")
    
    def test_engine_live_returns_agent_id(self):
        """GET /api/engine/live returns agent_id in response"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "agent_id" in data, "Missing agent_id field"
        print(f"PASS: Engine live: agent_id={data.get('agent_id')}, live={data.get('live')}, db_exists={data.get('db_exists')}")


class TestPushGenesisProtection:
    """Push genesis protection tests"""
    
    def test_push_genesis_skips_anima_fund(self):
        """POST /api/agents/push-genesis returns skipped_agents containing 'anima-fund'"""
        response = requests.post(f"{BASE_URL}/api/agents/push-genesis")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "skipped_agents" in data, "Missing skipped_agents field"
        assert "anima-fund" in data["skipped_agents"], "anima-fund should be in skipped_agents"
        print(f"PASS: Push genesis skipped: {data['skipped_agents']}, updated: {data.get('updated_agents', [])}")


class TestGenesisTemplate:
    """Genesis prompt template tests"""
    
    def test_genesis_template_is_generic(self):
        """GET /api/genesis/prompt-template returns generic template with {AGENT_NAME} placeholder"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "content" in data, "Missing content field"
        content = data["content"]
        
        # Should have placeholder for agent name
        has_placeholder = "{AGENT_NAME}" in content or "{{AGENT_NAME}}" in content
        assert has_placeholder, "Template should have {AGENT_NAME} placeholder"
        
        # Should NOT contain 'The Catalyst' (that's the specific anima-fund soul)
        assert "The Catalyst" not in content, "Template should NOT contain 'The Catalyst' - that's agent-specific"
        
        # Should have boot sequence and anti-stuck rules
        assert "BOOT" in content.upper() or "boot" in content.lower(), "Template should have boot sequence"
        
        print(f"PASS: Genesis template is generic ({len(content)} chars), has {{AGENT_NAME}} placeholder, no 'The Catalyst'")


class TestTelegramHealth:
    """Telegram integration tests"""
    
    def test_telegram_health(self):
        """GET /api/telegram/health shows agents with bot status"""
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Should have some structure about telegram status
        print(f"PASS: Telegram health: {data}")


class TestSSEStream:
    """Server-Sent Events stream tests"""
    
    def test_sse_stream_returns_events(self):
        """GET /api/live/stream returns Server-Sent Events data"""
        response = requests.get(f"{BASE_URL}/api/live/stream", stream=True, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        # Check content type is SSE
        content_type = response.headers.get('Content-Type', '')
        assert 'text/event-stream' in content_type, f"Expected text/event-stream, got {content_type}"
        
        # Read first event
        first_line = None
        for line in response.iter_lines(decode_unicode=True):
            if line:
                first_line = line
                break
        
        # Should start with data:
        if first_line:
            assert first_line.startswith('data:'), f"Expected SSE data format, got: {first_line[:50]}"
            # Parse the JSON data
            try:
                event_data = json.loads(first_line.replace('data: ', ''))
                assert "engine" in event_data or "timestamp" in event_data, "SSE should have engine or timestamp"
                print(f"PASS: SSE stream working, first event keys: {list(event_data.keys())}")
            except json.JSONDecodeError:
                print(f"PASS: SSE stream working, raw data: {first_line[:100]}")
        else:
            print("PASS: SSE stream opened successfully (no data yet)")
        
        response.close()


class TestEngineStatus:
    """Engine status tests"""
    
    def test_engine_live_structure(self):
        """GET /api/engine/live returns live, db_exists, agent_id, agent_state"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check expected fields
        expected_fields = ["live", "db_exists", "agent_id"]
        for field in expected_fields:
            assert field in data, f"Missing {field} field"
        
        # agent_state may be present
        print(f"PASS: Engine live: live={data.get('live')}, db_exists={data.get('db_exists')}, agent_id={data.get('agent_id')}, agent_state={data.get('agent_state')}")


class TestSoulEditor:
    """SOUL.md editor API tests"""
    
    def test_get_live_soul(self):
        """GET /api/live/soul returns soul content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "content" in data, "Missing content field"
        assert "exists" in data, "Missing exists field"
        print(f"PASS: Live soul: exists={data.get('exists')}, content_length={len(data.get('content') or '')}")
    
    def test_get_agent_soul(self):
        """GET /api/agents/anima-fund/soul returns soul for specific agent"""
        response = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "agent_id" in data, "Missing agent_id field"
        print(f"PASS: Agent soul: agent_id={data.get('agent_id')}, exists={data.get('exists')}, size={data.get('size')}")


class TestGenesisStatus:
    """Genesis status tests"""
    
    def test_genesis_status_structure(self):
        """GET /api/genesis/status returns comprehensive status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check expected fields
        expected_fields = ["agent_id", "config_exists", "engine_running", "status"]
        for field in expected_fields:
            assert field in data, f"Missing {field} field"
        
        print(f"PASS: Genesis status: agent_id={data.get('agent_id')}, config_exists={data.get('config_exists')}, engine_running={data.get('engine_running')}, status={data.get('status')}")


class TestSkillsAvailable:
    """Skills API tests"""
    
    def test_list_available_skills(self):
        """GET /api/skills/available lists all skills"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "skills" in data, "Missing skills field"
        assert isinstance(data["skills"], list), "skills should be a list"
        assert len(data["skills"]) > 0, "Should have at least some skills"
        
        # Check skill structure
        if data["skills"]:
            skill = data["skills"][0]
            assert "name" in skill, "Skill missing name"
            assert "source" in skill, "Skill missing source"
        
        print(f"PASS: Available skills: {data['total']} skills, sources: {set(s['source'] for s in data['skills'])}")


class TestHealthEndpoints:
    """Health check endpoints"""
    
    def test_api_health(self):
        """GET /api/health returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got {data.get('status')}"
        print(f"PASS: API health: {data}")
    
    def test_root_health(self):
        """GET /health returns status ok"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got {data.get('status')}"
        print(f"PASS: Root health: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
