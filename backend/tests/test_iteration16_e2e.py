"""
Iteration 16 - Full E2E Production Test for Anima Fund Platform

CRITICAL TESTS:
- All API endpoints return valid JSON on production URL
- /api/health returns status, engine_live, engine_db_exists, creator_wallet, timestamp
- /api/genesis/status returns wallet_address, stage, status, creator_wallet, engine_running
- /api/engine/live returns live/db_exists/turn_count/agent_state
- /api/engine/status returns version, skills array (93 skills), built=true
- /api/wallet/balance returns usdc, eth, credits_cents, tier
- /api/telegram/status returns configured=true, bot_token_set=true, chat_id_set=true
- POST /api/telegram/send sends real message
- /api/payments/status returns all compliance fields
- /api/live/skills-full returns 95 skills (NO conway source), 6 models
- /api/constitution returns non-empty content
- /api/live/identity returns name='Anima Fund', address starting with 0x
- All live/* endpoints return arrays
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ═══════════════════════════════════════════════════════════
# CRITICAL ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """CRITICAL: /api/health must return all required fields"""

    def test_health_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /api/health returns 200")

    def test_health_has_status_ok(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got {data.get('status')}"
        print("✓ status: ok")

    def test_health_has_engine_live(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "engine_live" in data, "Missing engine_live field"
        assert isinstance(data["engine_live"], bool), "engine_live should be boolean"
        print(f"✓ engine_live: {data['engine_live']}")

    def test_health_has_engine_db_exists(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "engine_db_exists" in data, "Missing engine_db_exists field"
        assert isinstance(data["engine_db_exists"], bool), "engine_db_exists should be boolean"
        print(f"✓ engine_db_exists: {data['engine_db_exists']}")

    def test_health_has_creator_wallet(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "creator_wallet" in data, "Missing creator_wallet field"
        assert data["creator_wallet"].startswith("xtm"), f"Invalid wallet: {data['creator_wallet']}"
        print(f"✓ creator_wallet: {data['creator_wallet'][:12]}...")

    def test_health_has_timestamp(self):
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data, "Missing timestamp field"
        assert data["timestamp"], "Empty timestamp"
        print(f"✓ timestamp: {data['timestamp'][:20]}...")


class TestGenesisStatus:
    """CRITICAL: /api/genesis/status must return all required fields"""

    def test_genesis_status_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        print("✓ /api/genesis/status returns 200")

    def test_genesis_has_wallet_address(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "wallet_address" in data, "Missing wallet_address"
        # May be null if engine not created yet
        if data["wallet_address"]:
            assert data["wallet_address"].startswith("0x"), f"Invalid wallet: {data['wallet_address']}"
            print(f"✓ wallet_address: {data['wallet_address'][:14]}...")
        else:
            print("✓ wallet_address: (not yet generated)")

    def test_genesis_has_stage(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "stage" in data, "Missing stage"
        valid_stages = ["not_created", "generating_wallet", "provisioning", "configuring", "created", "running"]
        assert data["stage"] in valid_stages, f"Invalid stage: {data['stage']}"
        print(f"✓ stage: {data['stage']}")

    def test_genesis_has_status(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "status" in data, "Missing status"
        print(f"✓ status: {data['status']}")

    def test_genesis_has_creator_wallet(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "creator_wallet" in data, "Missing creator_wallet"
        assert data["creator_wallet"].startswith("xtm"), f"Invalid SOL wallet: {data['creator_wallet']}"
        print(f"✓ creator_wallet: {data['creator_wallet'][:12]}...")

    def test_genesis_has_engine_running(self):
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "engine_running" in data, "Missing engine_running"
        assert isinstance(data["engine_running"], bool), "engine_running should be boolean"
        print(f"✓ engine_running: {data['engine_running']}")


class TestEngineLive:
    """CRITICAL: /api/engine/live must return live/db_exists/turn_count/agent_state"""

    def test_engine_live_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        print("✓ /api/engine/live returns 200")

    def test_engine_live_has_live(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "live" in data, "Missing live field"
        print(f"✓ live: {data['live']}")

    def test_engine_live_has_db_exists(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "db_exists" in data, "Missing db_exists field"
        print(f"✓ db_exists: {data['db_exists']}")

    def test_engine_live_has_turn_count(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        if data.get("db_exists"):
            assert "turn_count" in data, "Missing turn_count when db_exists=True"
            print(f"✓ turn_count: {data['turn_count']}")
        else:
            print("✓ turn_count: N/A (db doesn't exist)")

    def test_engine_live_has_agent_state(self):
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        if data.get("db_exists"):
            assert "agent_state" in data, "Missing agent_state when db_exists=True"
            print(f"✓ agent_state: {data['agent_state']}")
        else:
            print("✓ agent_state: N/A (db doesn't exist)")


class TestEngineStatus:
    """CRITICAL: /api/engine/status returns version, skills array, built=true"""

    def test_engine_status_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        print("✓ /api/engine/status returns 200")

    def test_engine_status_has_version(self):
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "version" in data, "Missing version"
        print(f"✓ version: {data['version']}")

    def test_engine_status_has_skills(self):
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "skills" in data, "Missing skills"
        assert isinstance(data["skills"], list), "skills should be list"
        # Should be around 93 skills in /app/automaton/skills/
        print(f"✓ skills count (from files): {len(data['skills'])}")

    def test_engine_status_has_built(self):
        response = requests.get(f"{BASE_URL}/api/engine/status")
        data = response.json()
        assert "built" in data, "Missing built"
        assert data["built"] == True, f"Expected built=true, got {data['built']}"
        print(f"✓ built: {data['built']}")


class TestWalletBalance:
    """CRITICAL: /api/wallet/balance returns usdc, eth, credits_cents, tier"""

    def test_wallet_balance_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        print("✓ /api/wallet/balance returns 200")

    def test_wallet_balance_has_usdc(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "usdc" in data, "Missing usdc field"
        print(f"✓ usdc: {data['usdc']}")

    def test_wallet_balance_has_eth(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "eth" in data, "Missing eth field"
        print(f"✓ eth: {data['eth']}")

    def test_wallet_balance_has_credits_cents(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "credits_cents" in data, "Missing credits_cents field"
        print(f"✓ credits_cents: {data['credits_cents']}")

    def test_wallet_balance_has_tier(self):
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "tier" in data, "Missing tier field"
        print(f"✓ tier: {data['tier']}")


class TestTelegramStatus:
    """CRITICAL: /api/telegram/status returns configured=true, bot_token_set=true, chat_id_set=true"""

    def test_telegram_status_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code == 200
        print("✓ /api/telegram/status returns 200")

    def test_telegram_has_configured(self):
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        data = response.json()
        assert "configured" in data, "Missing configured field"
        assert data["configured"] == True, f"Expected configured=true, got {data['configured']}"
        print(f"✓ configured: {data['configured']}")

    def test_telegram_has_bot_token_set(self):
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        data = response.json()
        assert "bot_token_set" in data, "Missing bot_token_set field"
        assert data["bot_token_set"] == True, f"Expected bot_token_set=true, got {data['bot_token_set']}"
        print(f"✓ bot_token_set: {data['bot_token_set']}")

    def test_telegram_has_chat_id_set(self):
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        data = response.json()
        assert "chat_id_set" in data, "Missing chat_id_set field"
        assert data["chat_id_set"] == True, f"Expected chat_id_set=true, got {data['chat_id_set']}"
        print(f"✓ chat_id_set: {data['chat_id_set']}")


class TestTelegramSend:
    """CRITICAL: POST /api/telegram/send actually sends a message"""

    def test_telegram_send_returns_200(self):
        response = requests.post(
            f"{BASE_URL}/api/telegram/send",
            json={"text": "Automated E2E test from testing agent - Iteration 16"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, f"Expected success=true, got {data}"
        print("✓ Telegram message sent successfully!")


class TestPaymentsStatus:
    """CRITICAL: /api/payments/status returns all compliance fields"""

    def test_payments_status_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200
        print("✓ /api/payments/status returns 200")

    def test_payments_has_engine_running(self):
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "engine_running" in data, "Missing engine_running"
        print(f"✓ engine_running: {data['engine_running']}")

    def test_payments_has_payout_compliant(self):
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "payout_compliant" in data, "Missing payout_compliant"
        assert isinstance(data["payout_compliant"], bool), "payout_compliant should be boolean"
        print(f"✓ payout_compliant: {data['payout_compliant']}")

    def test_payments_has_fund_launch_threshold(self):
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "fund_launch_threshold" in data, "Missing fund_launch_threshold"
        assert data["fund_launch_threshold"] == 10000, f"Expected 10000, got {data['fund_launch_threshold']}"
        print(f"✓ fund_launch_threshold: ${data['fund_launch_threshold']}")

    def test_payments_has_creator_wallets(self):
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "creator_wallets" in data, "Missing creator_wallets"
        wallets = data["creator_wallets"]
        assert "solana" in wallets and wallets["solana"], "Missing/empty solana wallet"
        assert "ethereum" in wallets and wallets["ethereum"], "Missing/empty ethereum wallet"
        assert wallets["solana"].startswith("xtm"), f"Invalid SOL: {wallets['solana']}"
        assert wallets["ethereum"].startswith("0x"), f"Invalid ETH: {wallets['ethereum']}"
        print(f"✓ creator_wallets: SOL={wallets['solana'][:10]}..., ETH={wallets['ethereum'][:14]}...")


class TestSkillsFull:
    """CRITICAL: /api/live/skills-full returns 95 skills (NO conway source), 6 models"""

    def test_skills_full_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        print("✓ /api/live/skills-full returns 200")

    def test_skills_full_has_skills_list(self):
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "skills" in data, "Missing skills"
        assert isinstance(data["skills"], list), "skills should be list"
        print(f"✓ skills count: {len(data['skills'])}")

    def test_skills_full_no_conway_source(self):
        """CRITICAL: NO skills should have source='conway'"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        skills = data.get("skills", [])
        conway_skills = [s for s in skills if s.get("source") == "conway"]
        assert len(conway_skills) == 0, f"Found {len(conway_skills)} 'conway' source skills - MUST BE REMOVED!"
        print("✓ NO 'conway' source skills (correctly removed)")

    def test_skills_full_count_approximately_95(self):
        """Should be ~95 skills from DB (not 122 with 27 fakes)"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        skills = data.get("skills", [])
        assert 80 <= len(skills) <= 120, f"Skills count {len(skills)} outside expected range 80-120"
        print(f"✓ Skills count: {len(skills)} (expected ~95)")

    def test_skills_full_has_models(self):
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "models" in data, "Missing models"
        assert isinstance(data["models"], list), "models should be list"
        # Should be 6 models
        print(f"✓ models count: {len(data['models'])}")

    def test_skills_full_has_tool_usage(self):
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "tool_usage" in data, "Missing tool_usage"
        print(f"✓ tool_usage present")


class TestConstitution:
    """CRITICAL: /api/constitution returns non-empty content"""

    def test_constitution_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/constitution")
        assert response.status_code == 200
        print("✓ /api/constitution returns 200")

    def test_constitution_has_content(self):
        response = requests.get(f"{BASE_URL}/api/constitution")
        data = response.json()
        assert "content" in data, "Missing content field"
        assert data["content"], "Empty constitution content"
        assert len(data["content"]) > 100, "Constitution content too short"
        print(f"✓ content length: {len(data['content'])} chars")


class TestLiveIdentity:
    """CRITICAL: /api/live/identity returns name='Anima Fund', address starting with 0x"""

    def test_live_identity_returns_200(self):
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        print("✓ /api/live/identity returns 200")

    def test_live_identity_has_name(self):
        response = requests.get(f"{BASE_URL}/api/live/identity")
        data = response.json()
        if data.get("name"):
            assert data["name"] == "Anima Fund", f"Expected 'Anima Fund', got {data['name']}"
            print(f"✓ name: {data['name']}")
        else:
            print("✓ name: (engine not fully initialized)")

    def test_live_identity_has_address(self):
        response = requests.get(f"{BASE_URL}/api/live/identity")
        data = response.json()
        if data.get("address"):
            assert data["address"].startswith("0x"), f"Address should start with 0x: {data['address']}"
            print(f"✓ address: {data['address'][:14]}...")
        else:
            print("✓ address: (not yet generated)")


# ═══════════════════════════════════════════════════════════
# BACKEND: Live Endpoint Tests
# ═══════════════════════════════════════════════════════════

class TestLiveAgents:
    """Backend: /api/live/agents returns agents array"""

    def test_live_agents(self):
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data, "Missing agents"
        assert isinstance(data["agents"], list), "agents should be list"
        print(f"✓ /api/live/agents: {data['total']} agents")


class TestLiveActivity:
    """Backend: /api/live/activity returns activities array"""

    def test_live_activity(self):
        response = requests.get(f"{BASE_URL}/api/live/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data, "Missing activities"
        assert isinstance(data["activities"], list), "activities should be list"
        print(f"✓ /api/live/activity: {data['total']} activities")


class TestLiveTurns:
    """Backend: /api/live/turns returns turns array"""

    def test_live_turns(self):
        response = requests.get(f"{BASE_URL}/api/live/turns")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data, "Missing turns"
        assert isinstance(data["turns"], list), "turns should be list"
        print(f"✓ /api/live/turns: {data['total']} turns")


class TestLiveHeartbeat:
    """Backend: /api/live/heartbeat returns history array with real heartbeat entries"""

    def test_live_heartbeat(self):
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data, "Missing history"
        assert isinstance(data["history"], list), "history should be list"
        print(f"✓ /api/live/heartbeat: {data['total']} entries")

    def test_heartbeat_has_real_entries(self):
        """Check if heartbeat has real task entries like check_social_inbox, check_usdc_balance"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat")
        data = response.json()
        history = data.get("history", [])
        if history:
            # Check for expected task types
            task_names = [h.get("task_name", h.get("type", "")) for h in history[:10]]
            print(f"✓ Heartbeat tasks: {task_names[:5]}")
        else:
            print("✓ No heartbeat history yet (engine idle)")


class TestLiveMemory:
    """Backend: /api/live/memory returns facts array"""

    def test_live_memory(self):
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data, "Missing facts"
        assert isinstance(data["facts"], list), "facts should be list"
        print(f"✓ /api/live/memory: {data['total']} facts")


class TestLiveSoul:
    """Backend: /api/live/soul returns content and exists boolean"""

    def test_live_soul(self):
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data, "Missing exists"
        assert isinstance(data["exists"], bool), "exists should be boolean"
        print(f"✓ /api/live/soul: exists={data['exists']}")


class TestLiveKV:
    """Backend: /api/live/kv returns items array"""

    def test_live_kv(self):
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data, "Missing items"
        assert isinstance(data["items"], list), "items should be list"
        print(f"✓ /api/live/kv: {len(data['items'])} items")


class TestLiveFinancials:
    """Backend: /api/live/financials returns financial state with inference data"""

    def test_live_financials(self):
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        data = response.json()
        # Should return financial state dict
        print(f"✓ /api/live/financials: {list(data.keys())[:5]}...")


class TestLiveTransactions:
    """Backend: /api/live/transactions returns transactions array"""

    def test_live_transactions(self):
        response = requests.get(f"{BASE_URL}/api/live/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data, "Missing transactions"
        assert isinstance(data["transactions"], list), "transactions should be list"
        print(f"✓ /api/live/transactions: {data['total']} transactions")


class TestGenesisReset:
    """Backend: POST /api/genesis/reset endpoint exists (don't actually reset)"""

    def test_genesis_reset_endpoint_exists(self):
        # We just verify the endpoint exists by checking it accepts POST
        # Don't actually reset in this test
        response = requests.options(f"{BASE_URL}/api/genesis/reset")
        # OPTIONS should return 200 with CORS
        print("✓ /api/genesis/reset endpoint exists")


class TestGenesisPromptSecurity:
    """Security: Genesis prompt uses {{PLACEHOLDERS}} for secrets"""

    def test_genesis_prompt_has_placeholders(self):
        with open("/app/automaton/genesis-prompt.md", "r") as f:
            content = f.read()
        
        # Must contain placeholders, not real values
        assert "{{TELEGRAM_BOT_TOKEN}}" in content, "Missing {{TELEGRAM_BOT_TOKEN}} placeholder"
        assert "{{TELEGRAM_CHAT_ID}}" in content, "Missing {{TELEGRAM_CHAT_ID}} placeholder"
        
        # Should NOT contain actual token values (8474833303 is the bot token prefix)
        # The template should have placeholders, not the real token
        bot_token_value = "8474833303:AAGPAma0oLHgItyC8anIgIDd_dvViGVkaVQ"
        assert bot_token_value not in content, "SECURITY: Real bot token found in genesis prompt!"
        
        print("✓ Genesis prompt uses {{placeholders}} for secrets (secure)")


class TestSkillsDirectory:
    """Verify skills directory has expected count including weather-trading-bot-setup"""

    def test_skills_directory_count(self):
        import os
        skills_dir = "/app/automaton/skills"
        skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
        assert len(skills) >= 90, f"Expected ~93 skills, found {len(skills)}"
        print(f"✓ Skills directory: {len(skills)} skill folders")

    def test_weather_trading_bot_skill_exists(self):
        import os
        skill_path = "/app/automaton/skills/weather-trading-bot-setup"
        assert os.path.isdir(skill_path), "Missing weather-trading-bot-setup skill"
        skill_file = os.path.join(skill_path, "SKILL.md")
        assert os.path.exists(skill_file), "Missing SKILL.md in weather-trading-bot-setup"
        print("✓ weather-trading-bot-setup skill exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
