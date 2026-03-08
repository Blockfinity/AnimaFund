"""
Iteration 15 Backend Tests — Verify real data enforcement (no mocks/fakes)

Testing:
1. /api/payments/status — new payment compliance endpoint
2. /api/live/skills-full — must return only real skills (no 'conway' source)
3. /api/health — must return creator_wallet
4. /api/engine/live — engine status
5. Genesis prompt validation — ETH address and $10K threshold
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPaymentStatusEndpoint:
    """Tests for the new /api/payments/status endpoint — 50% creator payout tracking"""

    def test_payments_status_returns_200(self):
        """Payment status endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ /api/payments/status returns 200")

    def test_payments_status_has_engine_running_field(self):
        """Payment status must have engine_running field"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "engine_running" in data, "Missing engine_running field"
        print(f"✓ engine_running: {data['engine_running']}")

    def test_payments_status_has_revenue_fields(self):
        """Payment status must have total_revenue field"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "total_revenue" in data, "Missing total_revenue field"
        assert "total_sustainability_cost" in data, "Missing total_sustainability_cost"
        print(f"✓ total_revenue: {data['total_revenue']}, sustainability_cost: {data['total_sustainability_cost']}")

    def test_payments_status_has_net_after_sustainability(self):
        """Payment status must have net_after_sustainability"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "net_after_sustainability" in data, "Missing net_after_sustainability"
        print(f"✓ net_after_sustainability: {data['net_after_sustainability']}")

    def test_payments_status_has_creator_payouts(self):
        """Payment status must have creator payout fields"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "total_creator_payouts" in data, "Missing total_creator_payouts"
        assert "owed_to_creator" in data, "Missing owed_to_creator"
        print(f"✓ creator_payouts: {data['total_creator_payouts']}, owed: {data['owed_to_creator']}")

    def test_payments_status_has_payout_compliant(self):
        """Payment status must have payout_compliant boolean"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "payout_compliant" in data, "Missing payout_compliant"
        assert isinstance(data["payout_compliant"], bool), "payout_compliant should be boolean"
        print(f"✓ payout_compliant: {data['payout_compliant']}")

    def test_payments_status_has_fund_launch_fields(self):
        """Payment status must have fund launch threshold fields"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "fund_launch_ready" in data, "Missing fund_launch_ready"
        assert "fund_launch_threshold" in data, "Missing fund_launch_threshold"
        assert data["fund_launch_threshold"] == 10000, f"Expected $10K threshold, got {data['fund_launch_threshold']}"
        print(f"✓ fund_launch_ready: {data['fund_launch_ready']}, threshold: ${data['fund_launch_threshold']}")

    def test_payments_status_has_capital_raised(self):
        """Payment status must have capital_raised field"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "capital_raised" in data, "Missing capital_raised"
        print(f"✓ capital_raised: {data['capital_raised']}")

    def test_payments_status_has_creator_wallets(self):
        """Payment status must have both SOL and ETH creator wallets"""
        response = requests.get(f"{BASE_URL}/api/payments/status")
        data = response.json()
        assert "creator_wallets" in data, "Missing creator_wallets"
        wallets = data["creator_wallets"]
        assert "solana" in wallets, "Missing solana wallet"
        assert "ethereum" in wallets, "Missing ethereum wallet"
        assert wallets["solana"].startswith("xtm"), f"Wrong SOL wallet: {wallets['solana']}"
        assert wallets["ethereum"].startswith("0x"), f"Wrong ETH wallet: {wallets['ethereum']}"
        assert wallets["ethereum"] == "0xec2340CD6a14229debe7B7841B8cB618dfD085b6", "ETH address mismatch"
        print(f"✓ creator_wallets: SOL={wallets['solana'][:10]}..., ETH={wallets['ethereum'][:12]}...")


class TestSkillsNoFakes:
    """Tests for /api/live/skills-full — must return ONLY real skills, NO conway fakes"""

    def test_skills_full_returns_200(self):
        """Skills-full endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        assert response.status_code == 200
        print("✓ /api/live/skills-full returns 200")

    def test_skills_full_has_skills_list(self):
        """Skills-full must return skills array"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "skills" in data, "Missing skills field"
        assert isinstance(data["skills"], list), "skills should be a list"
        print(f"✓ Skills returned: {len(data['skills'])}")

    def test_skills_full_no_conway_source(self):
        """CRITICAL: No skills should have source='conway' — this was removed"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        skills = data.get("skills", [])
        conway_skills = [s for s in skills if s.get("source") == "conway"]
        assert len(conway_skills) == 0, f"Found {len(conway_skills)} conway skills - these should be removed!"
        print("✓ No 'conway' source skills found (correctly removed)")

    def test_skills_full_all_anima_source(self):
        """All skills should have source 'anima' or similar real sources"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        skills = data.get("skills", [])
        # Valid sources: anima, mcp, openclaw, installed, builtin
        invalid_sources = [s for s in skills if s.get("source") in ["conway", "fake", "hardcoded"]]
        assert len(invalid_sources) == 0, f"Found skills with invalid sources: {[s['name'] for s in invalid_sources[:5]]}"
        print("✓ All skills have valid real sources")

    def test_skills_count_approximately_95(self):
        """Should return approximately 95 skills (from real DB, not 27 fake conway tools)"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        skills = data.get("skills", [])
        # The old code had 122 (95 real + 27 conway fakes), now should be ~95
        # Allow some range in case engine added/removed skills
        assert len(skills) >= 80, f"Expected ~95 skills, got only {len(skills)}"
        assert len(skills) <= 120, f"Too many skills ({len(skills)}) - might include fakes"
        print(f"✓ Skills count: {len(skills)} (expected ~95 real skills)")

    def test_skills_full_has_models(self):
        """Skills-full must return models array"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "models" in data, "Missing models field"
        assert isinstance(data["models"], list), "models should be a list"
        print(f"✓ Models returned: {len(data['models'])}")

    def test_skills_full_has_tool_usage(self):
        """Skills-full must return tool_usage dict"""
        response = requests.get(f"{BASE_URL}/api/live/skills-full")
        data = response.json()
        assert "tool_usage" in data, "Missing tool_usage field"
        assert isinstance(data["tool_usage"], dict), "tool_usage should be a dict"
        print(f"✓ Tool usage stats: {len(data['tool_usage'])} entries")


class TestHealthEndpoint:
    """Tests for /api/health"""

    def test_health_returns_200(self):
        """Health check should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ /api/health returns 200")

    def test_health_has_status_ok(self):
        """Health check must have status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got {data.get('status')}"
        print("✓ Health status: ok")

    def test_health_has_creator_wallet(self):
        """Health check must return creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "creator_wallet" in data, "Missing creator_wallet in health response"
        assert data["creator_wallet"].startswith("xtm"), f"Invalid creator wallet: {data['creator_wallet']}"
        print(f"✓ Creator wallet: {data['creator_wallet'][:12]}...")


class TestEngineLive:
    """Tests for /api/engine/live"""

    def test_engine_live_returns_200(self):
        """Engine live check should return 200"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        print("✓ /api/engine/live returns 200")

    def test_engine_live_has_status_fields(self):
        """Engine live must have live, db_exists fields"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        assert "live" in data, "Missing live field"
        assert "db_exists" in data, "Missing db_exists field"
        print(f"✓ Engine live: {data['live']}, db_exists: {data['db_exists']}")

    def test_engine_live_has_turn_count(self):
        """Engine live should have turn_count if db exists"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        if data.get("db_exists"):
            assert "turn_count" in data, "Missing turn_count when db_exists is True"
            print(f"✓ Turn count: {data['turn_count']}")
        else:
            print("✓ DB doesn't exist yet, turn_count not expected")

    def test_engine_live_has_agent_state(self):
        """Engine live should have agent_state if db exists"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        data = response.json()
        if data.get("db_exists"):
            assert "agent_state" in data, "Missing agent_state when db_exists is True"
            print(f"✓ Agent state: {data['agent_state']}")
        else:
            print("✓ DB doesn't exist yet, agent_state not expected")


class TestGenesisPromptContent:
    """Tests to verify genesis-prompt.md has correct content"""

    def test_genesis_prompt_exists(self):
        """Genesis prompt file must exist"""
        import os
        genesis_path = "/app/automaton/genesis-prompt.md"
        assert os.path.exists(genesis_path), f"Genesis prompt not found at {genesis_path}"
        print("✓ Genesis prompt file exists")

    def test_genesis_prompt_has_eth_address(self):
        """Genesis prompt must contain ETH address 0xec2340CD6a14229debe7B7841B8cB618dfD085b6"""
        with open("/app/automaton/genesis-prompt.md", "r") as f:
            content = f.read()
        eth_address = "0xec2340CD6a14229debe7B7841B8cB618dfD085b6"
        assert eth_address in content, f"ETH address {eth_address} not found in genesis prompt"
        # Count occurrences - should appear multiple times
        count = content.count(eth_address)
        print(f"✓ ETH address found {count} times in genesis prompt")

    def test_genesis_prompt_has_10k_threshold(self):
        """Genesis prompt must mention $10K/$10,000 fund launch threshold"""
        with open("/app/automaton/genesis-prompt.md", "r") as f:
            content = f.read()
        # Check for various representations
        has_10k = "$10K" in content or "$10,000" in content or "$10000" in content or "10000" in content
        assert has_10k, "$10K threshold not found in genesis prompt"
        print("✓ $10K threshold mentioned in genesis prompt")

    def test_genesis_prompt_has_sol_address(self):
        """Genesis prompt must contain SOL creator wallet"""
        with open("/app/automaton/genesis-prompt.md", "r") as f:
            content = f.read()
        sol_address = "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"
        assert sol_address in content, f"SOL address {sol_address} not found in genesis prompt"
        print(f"✓ SOL address found in genesis prompt")


class TestOtherEndpoints:
    """Additional endpoint tests"""

    def test_genesis_status(self):
        """Genesis status endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        assert "creator_wallet" in data
        print(f"✓ Genesis status: stage={data.get('stage')}, status={data.get('status')}")

    def test_live_identity(self):
        """Live identity endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Live identity: name={data.get('name')}, address={data.get('address')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
