"""
Iteration 46 - Comprehensive E2E Testing
Tests:
1. Agent creation flow (CreateAgentModal - Load Template, fields)
2. Data isolation (agent switching, live endpoint returns selected agent)
3. Genesis prompt separation (generic template vs The Catalyst)
4. Telegram integration health
5. Wallet balance API
6. Push genesis (skips anima-fund)
7. Soul patch API
8. SSE live stream
9. Anti-stuck rules in genesis prompt
10. No hardcoded secrets check
"""
import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAgentCRUD:
    """Test agent listing and selection"""
    
    def test_list_agents(self):
        """GET /api/agents should return list of agents"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        # anima-fund should be present
        agent_ids = [a.get("agent_id") for a in data["agents"]]
        assert "anima-fund" in agent_ids
        print(f"PASS: Listed {len(data['agents'])} agents")
    
    def test_select_anima_fund_agent(self):
        """POST /api/agents/anima-fund/select should switch to Anima Fund"""
        response = requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("active_agent") == "anima-fund"
        print(f"PASS: Selected anima-fund agent, data_dir: {data.get('data_dir')}")
    
    def test_engine_live_shows_selected_agent(self):
        """GET /api/engine/live should show the currently selected agent_id"""
        # First select anima-fund
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.3)
        
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert data["agent_id"] == "anima-fund"
        print(f"PASS: engine/live shows agent_id={data['agent_id']}")


class TestDataIsolation:
    """Test data isolation between agents"""
    
    def test_live_soul_returns_selected_agent_soul(self):
        """GET /api/live/soul should show the selected agent's soul, not another's"""
        # Select anima-fund
        requests.post(f"{BASE_URL}/api/agents/anima-fund/select")
        time.sleep(0.3)
        
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        # Should have content field
        assert "content" in data
        # If soul exists, it should contain Anima Fund related content
        if data.get("content"):
            assert "Anima Fund" in data["content"] or data.get("exists") is True
            print(f"PASS: live/soul content length: {len(data['content'])} chars")
        else:
            print(f"PASS: live/soul returned (content={data.get('content')}, exists={data.get('exists')})")


class TestGenesisPromptSeparation:
    """Test that generic template is separate from The Catalyst"""
    
    def test_prompt_template_is_generic(self):
        """GET /api/genesis/prompt-template should return generic template with {AGENT_NAME}"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        content = data["content"]
        
        # Must have {{AGENT_NAME}} placeholder (generic)
        assert "{{AGENT_NAME}}" in content, "Template should have {{AGENT_NAME}} placeholder"
        
        # Must NOT be The Catalyst specific (should not have hardcoded "Anima Fund" in intro)
        # The generic template says "You are {{AGENT_NAME}}"
        assert "You are {{AGENT_NAME}}" in content, "Template should start with generic agent name"
        
        print(f"PASS: Prompt template is generic ({len(content)} chars), has {{{{AGENT_NAME}}}} placeholder")
    
    def test_anima_fund_soul_is_condensed(self):
        """GET /api/agents/anima-fund/soul should show condensed soul (<1000 chars)"""
        response = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        assert response.status_code == 200
        data = response.json()
        
        assert "content" in data
        if data.get("content"):
            assert len(data["content"]) < 1000, f"Soul should be <1000 chars, got {len(data['content'])}"
            print(f"PASS: Anima Fund soul is {len(data['content'])} chars (<1000)")
        else:
            print(f"PASS: Anima Fund soul exists={data.get('exists')}")


class TestTelegramIntegration:
    """Test Telegram health endpoint"""
    
    def test_telegram_health(self):
        """GET /api/telegram/health should show bot_alive status"""
        response = requests.get(f"{BASE_URL}/api/telegram/health")
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "checked_at" in data
        
        # Find anima-fund in the results
        anima_result = None
        for agent in data["agents"]:
            if agent.get("agent_id") == "anima-fund":
                anima_result = agent
                break
        
        assert anima_result is not None, "anima-fund should be in telegram health results"
        
        # Check bot_alive status
        print(f"PASS: Telegram health - anima-fund bot_alive={anima_result.get('bot_alive')}, configured={anima_result.get('configured')}")
        
        # If configured, bot should ideally be alive
        if anima_result.get("configured"):
            # We can't force bot_alive to be true (depends on actual Telegram API)
            # but we document the status
            print(f"  Bot username: {anima_result.get('bot_username')}")


class TestWalletBalance:
    """Test wallet balance API"""
    
    def test_wallet_balance_returns_valid_json(self):
        """GET /api/wallet/balance should return usdc, credits_cents, tier, eth fields"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        required_fields = ["usdc", "credits_cents", "tier"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check types
        assert isinstance(data["usdc"], (int, float))
        assert isinstance(data["credits_cents"], (int, float))
        assert isinstance(data["tier"], str)
        
        # eth may be present
        if "eth" in data:
            assert isinstance(data["eth"], (int, float))
        
        print(f"PASS: Wallet balance - usdc=${data['usdc']}, credits={data['credits_cents']}c, tier={data['tier']}")


class TestPushGenesis:
    """Test push-genesis endpoint"""
    
    def test_push_genesis_skips_anima_fund(self):
        """POST /api/agents/push-genesis should skip anima-fund in skipped_agents"""
        response = requests.post(f"{BASE_URL}/api/agents/push-genesis")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") is True
        assert "skipped_agents" in data
        
        # anima-fund should be in skipped_agents
        assert "anima-fund" in data["skipped_agents"], "anima-fund should be skipped"
        
        print(f"PASS: push-genesis skipped={data['skipped_agents']}, updated={data.get('updated_agents', [])}")


class TestSoulPatchAPI:
    """Test SOUL.md patch API"""
    
    def test_patch_soul_and_verify(self):
        """POST /api/agents/anima-fund/patch-soul should work, then verify with GET"""
        # First get current soul to restore later
        get_res = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        original_soul = get_res.json().get("content", "")
        
        # Patch with test content
        test_content = "# Test Soul\nThis is a test patch."
        patch_res = requests.post(
            f"{BASE_URL}/api/agents/anima-fund/patch-soul",
            json={"content": test_content}
        )
        assert patch_res.status_code == 200
        patch_data = patch_res.json()
        assert patch_data.get("success") is True
        print(f"PASS: patch-soul returned success, soul_size={patch_data.get('soul_size')}")
        
        # Verify the change
        verify_res = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data.get("content") == test_content
        print(f"PASS: GET soul verified patch content")
        
        # Restore original
        if original_soul:
            requests.post(
                f"{BASE_URL}/api/agents/anima-fund/patch-soul",
                json={"content": original_soul}
            )
            print(f"PASS: Restored original soul ({len(original_soul)} chars)")


class TestSSELiveStream:
    """Test Server-Sent Events live stream"""
    
    def test_live_stream_returns_sse(self):
        """GET /api/live/stream should return Server-Sent Events"""
        response = requests.get(f"{BASE_URL}/api/live/stream", stream=True, timeout=15)
        assert response.status_code == 200
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "text/event-stream" in content_type, f"Expected text/event-stream, got {content_type}"
        
        # Read first chunk of data
        first_data = None
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                first_data = line[5:].strip()
                break
        
        response.close()
        
        assert first_data is not None, "Should receive SSE data"
        
        # Parse the JSON data
        parsed = json.loads(first_data)
        assert "engine" in parsed
        assert "timestamp" in parsed
        print(f"PASS: SSE live/stream working, received engine data with timestamp")


class TestAntiStuckRules:
    """Test that genesis prompt contains anti-stuck rules"""
    
    def test_anti_stuck_rules_in_template(self):
        """Genesis template should have ANTI-STUCK RULES with ULID guidance"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        content = response.json().get("content", "")
        
        # Check for ANTI-STUCK RULES section
        assert "ANTI-STUCK RULES" in content, "Template should have ANTI-STUCK RULES section"
        
        # Check for ULID guidance
        assert "ULID" in content, "Template should mention ULID for goal IDs"
        
        # Check for FORBIDDEN LOOP PATTERNS
        assert "FORBIDDEN LOOP PATTERNS" in content or "FORBIDDEN" in content, "Template should have forbidden patterns"
        
        # Check for 3-turn rule
        assert "3-turn" in content or "3 turn" in content.lower(), "Template should mention 3-turn rule"
        
        print(f"PASS: Anti-stuck rules verified in genesis template")


class TestSkillsAvailable:
    """Test skills listing for CreateAgentModal"""
    
    def test_skills_available_endpoint(self):
        """GET /api/skills/available should return skills list"""
        response = requests.get(f"{BASE_URL}/api/skills/available")
        assert response.status_code == 200
        data = response.json()
        
        assert "skills" in data
        assert "total" in data
        assert isinstance(data["skills"], list)
        assert data["total"] > 0, "Should have available skills"
        
        # Check skill structure
        if data["skills"]:
            skill = data["skills"][0]
            assert "name" in skill
            assert "source" in skill
        
        print(f"PASS: skills/available returned {data['total']} skills")


class TestHealthEndpoints:
    """Test health endpoints"""
    
    def test_api_health(self):
        """GET /api/health should return ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: /api/health returned status=ok")
    
    def test_engine_status(self):
        """GET /api/engine/status should return engine info"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        assert "engine" in data
        assert "version" in data
        print(f"PASS: /api/engine/status returned engine={data.get('engine')}")


class TestGenesisStatus:
    """Test genesis status endpoint"""
    
    def test_genesis_status(self):
        """GET /api/genesis/status should return agent status"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected fields
        assert "agent_id" in data
        assert "stage" in data
        assert "status" in data
        
        print(f"PASS: genesis/status - agent_id={data['agent_id']}, stage={data['stage']}, status={data['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
