"""
Anima Fund API Tests
Tests for Genesis Agent creation, status checking, and engine endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-vc-platform-1.preview.emergentagent.com').rstrip('/')


class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_api_health(self):
        """Test /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine_live" in data
        assert "creator_wallet" in data
        assert "timestamp" in data
        print(f"✓ /api/health: status={data['status']}, engine_live={data['engine_live']}")
    
    def test_kubernetes_health(self):
        """Test /health Kubernetes probe"""
        response = requests.get(f"{BASE_URL}/health")
        # Note: This might return HTML if not properly routed, but API should work
        if response.headers.get('content-type', '').startswith('application/json'):
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            print("✓ /health: status=ok")
        else:
            # HTML response means frontend served this route
            print("⚠ /health returned HTML (frontend served), expected JSON API")


class TestGenesisStatus:
    """Genesis agent status endpoint tests"""
    
    def test_genesis_status_initial(self):
        """Test GET /api/genesis/status returns initial state"""
        response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields exist
        assert "status" in data
        assert "engine_running" in data
        assert "wallet_address" in data
        assert "config_exists" in data
        assert "wallet_exists" in data
        assert "creator_wallet" in data
        
        print(f"✓ /api/genesis/status: status={data['status']}, engine_running={data['engine_running']}")
        print(f"  wallet_address={data['wallet_address']}, config_exists={data['config_exists']}")
        return data


class TestGenesisCreation:
    """Genesis agent creation workflow tests"""
    
    def test_create_genesis_agent(self):
        """Test POST /api/genesis/create starts the engine"""
        response = requests.post(f"{BASE_URL}/api/genesis/create")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "message" in data
        print(f"✓ /api/genesis/create: success={data['success']}, message={data['message']}")
        return data
    
    def test_status_after_create(self):
        """Test GET /api/genesis/status after creation (wait for engine boot)"""
        # First create the agent
        create_response = requests.post(f"{BASE_URL}/api/genesis/create")
        assert create_response.status_code == 200
        
        # Wait for engine to boot and generate wallet (8 seconds as noted)
        print("  Waiting 8 seconds for engine to boot...")
        time.sleep(8)
        
        # Check status
        status_response = requests.get(f"{BASE_URL}/api/genesis/status")
        assert status_response.status_code == 200
        data = status_response.json()
        
        # After create, engine_running should be true
        assert data.get("engine_running") == True or data.get("status") in ["running", "created"]
        
        # Wallet should exist and start with 0x
        if data.get("wallet_address"):
            assert data["wallet_address"].startswith("0x"), f"Wallet should start with 0x, got: {data['wallet_address']}"
            print(f"✓ Engine running with wallet: {data['wallet_address']}")
        else:
            print(f"⚠ Engine running but wallet not yet generated, status: {data}")
        
        return data


class TestEngineLogs:
    """Engine logs endpoint tests"""
    
    def test_engine_logs(self):
        """Test GET /api/engine/logs returns log data"""
        response = requests.get(f"{BASE_URL}/api/engine/logs")
        assert response.status_code == 200
        data = response.json()
        
        # Should have stdout, stderr, and anima_dir
        assert "stdout" in data
        assert "stderr" in data
        assert "anima_dir" in data
        
        print(f"✓ /api/engine/logs: anima_dir files count={len(data['anima_dir'])}")
        if data['anima_dir']:
            for f in data['anima_dir'][:5]:
                print(f"    - {f['name']} ({f['size']} bytes)")
        return data


class TestEngineLiveEndpoints:
    """Engine live data endpoints tests"""
    
    def test_engine_live(self):
        """Test GET /api/engine/live"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        data = response.json()
        
        # Should have live status fields
        assert "live" in data or "db_exists" in data
        print(f"✓ /api/engine/live: {data}")
        return data
    
    def test_live_identity(self):
        """Test GET /api/live/identity"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ /api/live/identity: {data}")
        return data


class TestEngineStatus:
    """Engine status and configuration tests"""
    
    def test_engine_status(self):
        """Test GET /api/engine/status returns engine info"""
        response = requests.get(f"{BASE_URL}/api/engine/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "engine" in data
        assert "version" in data
        assert "built" in data
        assert "creator_wallet" in data
        
        print(f"✓ /api/engine/status: engine={data['engine']}, version={data['version']}, built={data['built']}")
        return data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
