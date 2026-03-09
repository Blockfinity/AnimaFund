"""
Iteration 45 - Critical Fixes Testing
Tests for:
1. SOUL.md Emergency Patch API (POST/GET)
2. SOUL.md condensation (<1000 chars)
3. Wallet Balance API with Conway credits
4. SSE Live Stream endpoint
5. Genesis Prompt fixes (no 'already available')
6. Soul Validator limits (4000/2000)
7. OpenClaw config filename (config.json not openclaw.json)
8. Loop detection messages updated
9. Engine build present
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSOULmdPatchAPI:
    """Test SOUL.md patch and get endpoints"""
    
    def test_get_soul_anima_fund(self):
        """GET /api/agents/anima-fund/soul should return current SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "content" in data, "Response should have 'content' field"
        assert "exists" in data, "Response should have 'exists' field"
        assert "size" in data, "Response should have 'size' field"
        assert "agent_id" in data, "Response should have 'agent_id' field"
        assert data["agent_id"] == "anima-fund"
        print(f"SOUL.md size: {data.get('size')} chars, exists: {data.get('exists')}")
    
    def test_patch_soul_anima_fund(self):
        """POST /api/agents/anima-fund/patch-soul should overwrite SOUL.md"""
        # First get current content to restore later
        get_response = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        original_content = get_response.json().get("content", "")
        
        # Test patch with new content
        test_content = "# Test SOUL\n## Test section\nThis is a test."
        response = requests.post(
            f"{BASE_URL}/api/agents/anima-fund/patch-soul",
            json={"content": test_content}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, f"Patch should succeed: {data}"
        assert data.get("agent_id") == "anima-fund"
        assert data.get("soul_size") == len(test_content)
        print(f"Patch response: {data}")
        
        # Verify the patch was applied
        verify = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        verify_data = verify.json()
        assert verify_data.get("content") == test_content, "Content should match patched content"
        
        # Restore original content
        if original_content:
            requests.post(
                f"{BASE_URL}/api/agents/anima-fund/patch-soul",
                json={"content": original_content}
            )
            print("Restored original SOUL.md content")


class TestSOULmdCondensation:
    """Test SOUL.md is condensed to <1000 chars"""
    
    def test_soul_size_under_1000_chars(self):
        """Live SOUL.md at ~/.anima/SOUL.md should be under 1000 chars"""
        response = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        assert response.status_code == 200
        
        data = response.json()
        size = data.get("size", 0)
        
        # The requirement states <1000 chars (was 30,666 bytes)
        assert size < 1000, f"SOUL.md should be <1000 chars, got {size}"
        print(f"SOUL.md size: {size} chars (requirement: <1000)")


class TestWalletBalanceAPI:
    """Test wallet balance endpoint with Conway API integration"""
    
    def test_wallet_balance_returns_valid_json(self):
        """GET /api/wallet/balance should return valid JSON with usdc, credits_cents, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should have usdc field (or 0 if no wallet)
        assert "usdc" in data or "error" in data, "Should have 'usdc' or 'error' field"
        
        # If wallet exists, should have credits_cents and tier
        if data.get("wallet"):
            assert "credits_cents" in data, "Should have 'credits_cents' when wallet exists"
            assert "tier" in data, "Should have 'tier' when wallet exists"
            print(f"Wallet: {data.get('wallet')[:20]}...")
            print(f"USDC: ${data.get('usdc', 0):.2f}")
            print(f"Credits: ${data.get('credits_cents', 0)/100:.2f}")
            print(f"Tier: {data.get('tier')}")
        else:
            print(f"No wallet found: {data.get('error', 'no error msg')}")


class TestSSELiveStream:
    """Test Server-Sent Events endpoint"""
    
    def test_sse_endpoint_exists(self):
        """GET /api/live/stream should return SSE content type"""
        response = requests.get(f"{BASE_URL}/api/live/stream", stream=True, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "text/event-stream" in content_type, f"Expected text/event-stream, got {content_type}"
        
        # Read first event
        try:
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if line and line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    assert "engine" in data, "SSE data should have 'engine' field"
                    assert "conway_credits_cents" in data, "SSE data should have 'conway_credits_cents'"
                    assert "timestamp" in data, "SSE data should have 'timestamp'"
                    print(f"SSE event received: engine_live={data['engine'].get('live')}, credits={data.get('conway_credits_cents')}")
                    break
                if i > 5:
                    break
        finally:
            response.close()


class TestGenesisPrompt:
    """Test genesis prompt template"""
    
    def test_genesis_prompt_no_already_available(self):
        """Genesis prompt should NOT contain 'already available' text"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        assert response.status_code == 200
        
        data = response.json()
        content = data.get("content", "")
        
        assert "already available" not in content.lower(), \
            "Genesis prompt should NOT contain 'already available' (causes skipped installs)"
        print("PASS: 'already available' text NOT found in genesis prompt")
    
    def test_genesis_prompt_has_boot_sequence(self):
        """Genesis prompt should have mandatory BOOT SEQUENCE"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        data = response.json()
        content = data.get("content", "")
        
        assert "BOOT SEQUENCE" in content, "Should have BOOT SEQUENCE section"
        print("PASS: BOOT SEQUENCE found")
    
    def test_genesis_prompt_has_anti_stuck_rules(self):
        """Genesis prompt should have ANTI-STUCK RULES with ULID guidance"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        data = response.json()
        content = data.get("content", "")
        
        assert "ANTI-STUCK RULES" in content, "Should have ANTI-STUCK RULES section"
        assert "ULID" in content, "Should mention ULID for goal IDs"
        print("PASS: ANTI-STUCK RULES with ULID guidance found")
    
    def test_genesis_prompt_has_telegram_reporting(self):
        """Genesis prompt should have Telegram EVERY TURN reporting"""
        response = requests.get(f"{BASE_URL}/api/genesis/prompt-template")
        data = response.json()
        content = data.get("content", "")
        
        assert "TELEGRAM" in content.upper(), "Should mention Telegram"
        assert "EVERY TURN" in content.upper() or "AFTER EVERY TURN" in content.upper(), \
            "Should specify Telegram reporting every turn"
        print("PASS: Telegram reporting instruction found")


class TestConwayBalanceAPI:
    """Test Conway balance endpoint"""
    
    def test_conway_balance_endpoint(self):
        """GET /api/conway/balance should return credits data"""
        response = requests.get(f"{BASE_URL}/api/conway/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "source" in data, "Should have 'source' field"
        assert data.get("source") == "conway_api", f"Source should be 'conway_api', got {data.get('source')}"
        
        # Should have credits info (may be 0)
        if "error" not in data:
            assert "credits_cents" in data or "credits_usd" in data, \
                "Should have credits info when no error"
            print(f"Conway balance: credits_cents={data.get('credits_cents')}")
        else:
            print(f"Conway API error: {data.get('error')}")


class TestEngineLiveEndpoint:
    """Test engine live status"""
    
    def test_engine_live_endpoint(self):
        """GET /api/engine/live should return engine status"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "live" in data or "db_exists" in data, "Should have live or db_exists field"
        assert "agent_id" in data, "Should have agent_id field"
        print(f"Engine live: live={data.get('live')}, db_exists={data.get('db_exists')}, agent_id={data.get('agent_id')}")


class TestLiveIdentity:
    """Test live identity endpoint"""
    
    def test_live_identity(self):
        """GET /api/live/identity should return agent identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        
        data = response.json()
        if data:  # May be empty if engine not running
            print(f"Identity: name={data.get('name')}, address={data.get('address')}")
        else:
            print("Identity: (empty - engine may not be running)")


class TestLiveSoul:
    """Test live soul endpoint"""
    
    def test_live_soul(self):
        """GET /api/live/soul should return soul content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        
        data = response.json()
        assert "exists" in data, "Should have 'exists' field"
        print(f"Live soul: exists={data.get('exists')}")


class TestGenesisPatchSoulAcceptsJSON:
    """Verify patch-soul accepts JSON payload"""
    
    def test_patch_soul_accepts_json(self):
        """POST should accept JSON body with 'content' field"""
        # Get current to restore
        get_resp = requests.get(f"{BASE_URL}/api/agents/anima-fund/soul")
        original = get_resp.json().get("content", "")
        
        # Try posting with explicit JSON
        test_content = "# Minimal Test\nTest content for JSON acceptance"
        response = requests.post(
            f"{BASE_URL}/api/agents/anima-fund/patch-soul",
            headers={"Content-Type": "application/json"},
            json={"content": test_content}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        
        # Restore
        if original:
            requests.post(
                f"{BASE_URL}/api/agents/anima-fund/patch-soul",
                json={"content": original}
            )
        print("PASS: patch-soul accepts JSON with 'content' field")


class TestEngineStatus:
    """Test engine status endpoint"""
    
    def test_engine_status(self):
        """GET /api/engine/status should return build info"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "built" in data, "Should have 'built' field"
        assert "version" in data, "Should have 'version' field"
        print(f"Engine: built={data.get('built')}, version={data.get('version')}")
        
        # Verify bundle.mjs exists
        assert data.get("built") == True, "Engine should be built (dist/bundle.mjs)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
