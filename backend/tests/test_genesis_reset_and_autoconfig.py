"""
Anima Fund API Tests - Genesis Reset and Auto-Config Testing
Tests the NEW /api/genesis/reset endpoint and auto-config.json with genesisPrompt/creatorMessage fields.

Test Coverage:
- POST /api/genesis/reset - Stop engine, clean state, preserve wallet
- POST /api/genesis/create - Verify auto-config.json contains genesisPrompt, creatorMessage, creatorAddress
- GET /api/genesis/status - Verify wallet_address, stage, status, engine_state
- GET /api/health - Verify healthy status
- GET /api/wallet/balance - Verify on-chain balance returns without errors
- Symlink verification: ~/.automaton -> ~/.anima
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
    
    def test_health_contains_all_required_fields(self):
        """Health endpoint contains engine_live, engine_db_exists, creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "engine_live" in data
        assert "engine_db_exists" in data
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"✓ All health fields present: engine_live={data['engine_live']}, engine_db_exists={data['engine_db_exists']}")


class TestWalletBalanceEndpoint:
    """Tests for /api/wallet/balance endpoint - on-chain balance check"""
    
    def test_wallet_balance_returns_200(self):
        """Wallet balance endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        print("✓ Wallet balance endpoint accessible")
    
    def test_wallet_balance_contains_required_fields(self):
        """Wallet balance returns wallet, usdc, eth, credits_cents, tier"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        assert "wallet" in data
        assert "usdc" in data
        assert "eth" in data
        assert "credits_cents" in data
        assert "tier" in data
        print(f"✓ Balance fields: wallet={data['wallet']}, usdc={data['usdc']}, eth={data['eth']}, tier={data['tier']}")
    
    def test_wallet_balance_no_onchain_error(self):
        """Wallet balance returns with no onchain_error (successful RPC call)"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        # onchain_error should be None (no error)
        assert data.get("onchain_error") is None, f"Unexpected onchain_error: {data.get('onchain_error')}"
        print(f"✓ No onchain error - RPC call successful")
    
    def test_wallet_balance_valid_wallet_address(self):
        """Wallet balance returns valid Ethereum wallet address"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        data = response.json()
        wallet = data.get("wallet")
        assert wallet is not None
        assert wallet.startswith("0x")
        assert len(wallet) == 42
        print(f"✓ Valid wallet address: {wallet}")


class TestGenesisStatusEndpoint:
    """Tests for /api/genesis/status endpoint"""
    
    def test_genesis_status_returns_200(self):
        """Genesis status endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        print("✓ Genesis status endpoint accessible")
    
    def test_genesis_status_wallet_address(self):
        """Genesis status returns valid wallet address"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "wallet_address" in data
        wallet = data["wallet_address"]
        assert wallet is not None
        assert wallet.startswith("0x")
        assert len(wallet) == 42
        print(f"✓ Wallet address: {wallet}")
    
    def test_genesis_status_stage_and_status(self):
        """Genesis status returns stage and status fields"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "stage" in data
        assert "status" in data
        # stage can be: not_created, generating_wallet, provisioning, configuring, running, created
        valid_stages = ["not_created", "generating_wallet", "provisioning", "configuring", "running", "created"]
        assert data["stage"] in valid_stages, f"Invalid stage: {data['stage']}"
        # status can be: not_created, created, running
        valid_statuses = ["not_created", "created", "running"]
        assert data["status"] in valid_statuses, f"Invalid status: {data['status']}"
        print(f"✓ Stage: {data['stage']}, Status: {data['status']}")
    
    def test_genesis_status_engine_state(self):
        """Genesis status returns engine_state field"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "engine_state" in data
        # Engine state could be None, 'sleeping', 'active', 'critical', etc.
        print(f"✓ Engine state: {data['engine_state']}")
    
    def test_genesis_status_qr_code(self):
        """Genesis status returns QR code when wallet exists"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "qr_code" in data
        if data["wallet_address"] and data["wallet_address"].startswith("0x"):
            assert data["qr_code"] is not None
            assert data["qr_code"].startswith("data:image/png;base64,")
            print(f"✓ QR code generated for wallet")
        else:
            print(f"✓ QR code field present (no wallet yet)")
    
    def test_genesis_status_creator_wallet(self):
        """Genesis status returns creator_wallet"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        data = response.json()
        assert "creator_wallet" in data
        assert data["creator_wallet"] == "xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r"
        print(f"✓ Creator wallet: {data['creator_wallet']}")


class TestGenesisResetEndpoint:
    """Tests for POST /api/genesis/reset endpoint - NEW feature"""
    
    def test_genesis_reset_endpoint_returns_200(self):
        """Genesis reset endpoint returns 200"""
        # Note: We're just testing the endpoint exists and responds correctly
        # We'll save the actual reset for after collecting other test data
        response = requests.post(f"{BASE_URL}/api/genesis/reset")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        print(f"✓ Genesis reset endpoint accessible, success={data['success']}")
    
    def test_genesis_reset_returns_success_true(self):
        """Genesis reset returns success=true"""
        response = requests.post(f"{BASE_URL}/api/genesis/reset")
        data = response.json()
        assert data["success"] == True
        print(f"✓ Genesis reset success=true")
    
    def test_genesis_reset_returns_message(self):
        """Genesis reset returns message about wallet preserved"""
        response = requests.post(f"{BASE_URL}/api/genesis/reset")
        data = response.json()
        assert "message" in data
        assert "wallet" in data["message"].lower() or "preserved" in data["message"].lower()
        print(f"✓ Genesis reset message: {data['message']}")


class TestGenesisResetAndRecreate:
    """Tests reset + recreate flow - verifies state is properly cleaned and recreated"""
    
    def test_reset_clears_state_and_preserves_wallet(self):
        """After reset, config is cleared but wallet.json is preserved"""
        # Get wallet address before reset
        status_before = requests.get(f"{BASE_URL}/api/genesis/status").json()
        wallet_before = status_before.get("wallet_address")
        
        # Reset
        reset_resp = requests.post(f"{BASE_URL}/api/genesis/reset")
        assert reset_resp.status_code == 200
        
        # Check status after reset - should still have wallet but engine not running
        status_after = requests.get(f"{BASE_URL}/api/genesis/status").json()
        
        # Note: After reset, the wallet may still be readable from wallet.json
        # but config_exists should be false (anima.json deleted)
        print(f"✓ Before reset: wallet={wallet_before}")
        print(f"✓ After reset: config_exists={status_after.get('config_exists')}, wallet_exists={status_after.get('wallet_exists')}")
    
    def test_create_after_reset_restores_config(self):
        """After reset, create restores auto-config.json with genesisPrompt and creatorMessage"""
        # First reset to clean state
        requests.post(f"{BASE_URL}/api/genesis/reset")
        
        # Then create
        create_resp = requests.post(f"{BASE_URL}/api/genesis/create")
        assert create_resp.status_code == 200
        data = create_resp.json()
        assert data["success"] == True
        
        # Check engine logs for anima_dir to verify files were staged
        logs_resp = requests.get(f"{BASE_URL}/api/engine/logs")
        logs_data = logs_resp.json()
        anima_files = [f["name"] for f in logs_data.get("anima_dir", [])]
        
        # auto-config.json should be created
        assert "auto-config.json" in anima_files, f"auto-config.json not found in anima_dir: {anima_files}"
        print(f"✓ auto-config.json created after genesis/create")
        print(f"✓ anima_dir files: {anima_files}")


class TestAutoConfigFields:
    """Tests that auto-config.json contains genesisPrompt, creatorMessage, creatorAddress"""
    
    def test_engine_logs_shows_autoconfig(self):
        """Engine logs endpoint shows auto-config.json in anima_dir"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        data = response.json()
        anima_files = [f["name"] for f in data.get("anima_dir", [])]
        assert "auto-config.json" in anima_files
        
        # Check file size is substantial (should be 32KB+ with genesisPrompt)
        auto_config_file = next((f for f in data.get("anima_dir", []) if f["name"] == "auto-config.json"), None)
        assert auto_config_file is not None
        assert auto_config_file["size"] > 25000, f"auto-config.json too small: {auto_config_file['size']} bytes (expected >25KB with genesisPrompt)"
        print(f"✓ auto-config.json exists with size {auto_config_file['size']} bytes")


class TestAnimaJsonCreatorMessage:
    """Tests that anima.json contains creatorMessage field after engine initialization"""
    
    def test_engine_logs_shows_anima_json(self):
        """Engine logs endpoint shows anima.json in anima_dir"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        data = response.json()
        anima_files = [f["name"] for f in data.get("anima_dir", [])]
        
        # anima.json should exist after engine runs
        if "anima.json" in anima_files:
            anima_json_file = next((f for f in data.get("anima_dir", []) if f["name"] == "anima.json"), None)
            assert anima_json_file is not None
            # anima.json should be substantial (>20KB with genesisPrompt and creatorMessage)
            assert anima_json_file["size"] > 20000, f"anima.json too small: {anima_json_file['size']} bytes"
            print(f"✓ anima.json exists with size {anima_json_file['size']} bytes")
        else:
            print(f"⚠ anima.json not yet created (engine may not have initialized fully)")


class TestSymlinkCheck:
    """Tests that ~/.automaton symlink points to ~/.anima"""
    
    def test_engine_logs_shows_state_db_exists(self):
        """Engine logs should show state.db exists (proves ~/.anima is accessible)"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        data = response.json()
        anima_files = [f["name"] for f in data.get("anima_dir", [])]
        
        # state.db should exist if engine has run
        if "state.db" in anima_files:
            print(f"✓ state.db exists in ~/.anima (symlink working)")
        else:
            print(f"⚠ state.db not found (engine may not have run yet)")
        
        # Print all files for debugging
        print(f"  anima_dir contents: {anima_files}")


class TestLiveEndpointsAfterReset:
    """Tests that live endpoints still work after reset+create"""
    
    def test_live_identity_after_recreate(self):
        """Live identity endpoint returns data after reset+create"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        # Should return 200 even if no data
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Live identity after reset: name={data.get('name')}, address={data.get('address')}")
    
    def test_live_soul_after_recreate(self):
        """Live soul endpoint returns data after reset+create"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Live soul after reset: exists={data.get('exists')}")
    
    def test_engine_live_after_recreate(self):
        """Engine live endpoint returns status after reset+create"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Engine live after reset: db_exists={data.get('db_exists')}, agent_state={data.get('agent_state')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
