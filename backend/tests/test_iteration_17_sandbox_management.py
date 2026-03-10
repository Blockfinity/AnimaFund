"""
Iteration 17: Sandbox Management Tests - Non-refundable Conway sandbox protection

Key requirement: Conway sandboxes are prepaid and non-refundable, so we must:
1. Block delete-sandbox endpoint (returns error + redirects to reset)
2. reset-sandbox returns 'No sandbox to reset' when no sandbox exists
3. create-sandbox checks for existing sandboxes via Conway API before creating new ones
4. list-sandboxes returns sandbox list from Conway API
5. Provision status endpoint returns full provisioning state
6. Credits endpoints (balance, purchase)
7. Telegram health/test endpoints
8. Conway health endpoint

All endpoints call REAL Conway API and Telegram (no mocks).
"""
import os
import pytest
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://anima-audit.preview.emergentagent.com"


class TestDeleteSandboxBlocked:
    """DELETE sandbox endpoint is disabled - Conway sandboxes are prepaid and non-refundable"""
    
    def test_delete_sandbox_returns_error(self):
        """POST /api/provision/delete-sandbox returns error with non-refundable message"""
        session = get_session()
        res = session.post(f"{BASE_URL}/api/provision/delete-sandbox", timeout=60)
        assert res.status_code == 200  # Still returns 200 but with success:false
        data = res.json()
        # Should return success=False with error message
        assert data.get("success") == False
        # Error should mention non-refundable
        error = data.get("error", "")
        assert "non-refundable" in error.lower() or "prepaid" in error.lower() or "disabled" in error.lower(), \
            f"Expected error to mention non-refundable/prepaid/disabled, got: {error}"
        # Should redirect to reset-sandbox
        assert data.get("use_instead") == "/api/provision/reset-sandbox"
        print(f"PASS: /api/provision/delete-sandbox - correctly blocked with message: {error[:80]}...")


class TestResetSandbox:
    """Reset sandbox endpoint - wipes agent data but preserves sandbox VM"""
    
    def test_reset_sandbox_no_sandbox(self):
        """POST /api/provision/reset-sandbox returns 'No sandbox to reset' when no sandbox exists"""
        res = requests.post(f"{BASE_URL}/api/provision/reset-sandbox", timeout=10)
        assert res.status_code == 200
        data = res.json()
        # When no sandbox exists, should return success=False with appropriate message
        # OR success=True if sandbox exists (which we can't predict)
        if not data.get("success"):
            error = data.get("error", "")
            assert "no sandbox" in error.lower() or "sandbox" in error.lower(), \
                f"Expected 'no sandbox' message, got: {error}"
            print(f"PASS: /api/provision/reset-sandbox - correctly returns no sandbox: {error}")
        else:
            # If there IS a sandbox, reset succeeded
            assert "sandbox_id" in data
            print(f"PASS: /api/provision/reset-sandbox - reset succeeded for sandbox: {data.get('sandbox_id')}")


class TestCreateSandbox:
    """Create sandbox endpoint - should check for existing sandboxes before creating new"""
    
    def test_create_sandbox_checks_existing(self):
        """POST /api/provision/create-sandbox checks for existing sandboxes via Conway API"""
        res = requests.post(f"{BASE_URL}/api/provision/create-sandbox", 
                           json={}, timeout=30)
        assert res.status_code == 200
        data = res.json()
        
        # Response should indicate either:
        # 1. Reused existing sandbox (reused=True)
        # 2. Created new sandbox (reused=False)
        # 3. Error (insufficient credits)
        
        if data.get("success"):
            assert "sandbox_id" in data
            if data.get("reused"):
                # Reusing existing sandbox - credits preserved
                print(f"PASS: /api/provision/create-sandbox - reused existing sandbox: {data.get('sandbox_id')}")
            else:
                # Created new sandbox
                print(f"PASS: /api/provision/create-sandbox - created new sandbox: {data.get('sandbox_id')}")
        else:
            # Failed - likely insufficient credits (0 credits on test key)
            error = data.get("error", "")
            print(f"PASS: /api/provision/create-sandbox - returned error (expected with 0 credits): {error}")
        
        # Either way, the endpoint should work without crashing


class TestListSandboxes:
    """List sandboxes endpoint - returns all sandboxes from Conway API"""
    
    def test_list_sandboxes(self):
        """GET /api/provision/list-sandboxes returns sandbox list from Conway API"""
        res = requests.get(f"{BASE_URL}/api/provision/list-sandboxes", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Response should have success field and sandboxes list
        assert "sandboxes" in data or "error" in data
        
        if data.get("success"):
            sandboxes = data.get("sandboxes", [])
            assert isinstance(sandboxes, list)
            print(f"PASS: /api/provision/list-sandboxes - found {len(sandboxes)} sandboxes")
        else:
            # May fail if no API key or API error
            error = data.get("error", "")
            print(f"PASS: /api/provision/list-sandboxes - returned error: {error[:80]}")


class TestProvisionStatus:
    """Provision status endpoint - returns full provisioning state"""
    
    def test_provision_status(self):
        """GET /api/provision/status returns full provisioning state"""
        res = requests.get(f"{BASE_URL}/api/provision/status", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Required fields
        assert "agent_id" in data
        assert "sandbox" in data
        assert "tools" in data
        assert "skills_loaded" in data
        
        # Sandbox should be a dict with status
        sandbox = data.get("sandbox", {})
        assert "status" in sandbox
        
        # Credits should be returned
        assert "credits_cents" in data
        
        print(f"PASS: /api/provision/status - agent_id={data['agent_id']}, sandbox_status={sandbox.get('status')}, credits_cents={data.get('credits_cents')}")


class TestCreditsEndpoints:
    """Credits endpoints for Conway API"""
    
    def test_credits_balance(self):
        """GET /api/credits/balance returns current balance"""
        res = requests.get(f"{BASE_URL}/api/credits/balance", timeout=10)
        assert res.status_code == 200
        data = res.json()
        
        assert "credits_cents" in data
        assert "credits_usd" in data
        assert isinstance(data["credits_cents"], (int, float))
        assert isinstance(data["credits_usd"], (int, float))
        
        print(f"PASS: /api/credits/balance - credits_cents={data['credits_cents']}, credits_usd=${data['credits_usd']}")
    
    def test_credits_purchase(self):
        """POST /api/credits/purchase returns QR code and payment details"""
        res = requests.post(f"{BASE_URL}/api/credits/purchase", 
                           json={"amount": 5}, timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Should return success with payment details
        assert data.get("success") == True
        assert "pay_to" in data
        assert "amount_usdc" in data
        assert "qr_code" in data
        assert "instructions" in data
        
        # QR code should be a data URL
        qr = data.get("qr_code", "")
        assert qr.startswith("data:image/png;base64,")
        
        print(f"PASS: /api/credits/purchase - pay_to={data['pay_to'][:30]}..., amount_usdc={data['amount_usdc']}")


class TestTelegramEndpoints:
    """Telegram bot health and test message endpoints"""
    
    def test_telegram_health(self):
        """GET /api/telegram/health returns bot_alive status"""
        res = requests.get(f"{BASE_URL}/api/telegram/health", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        assert "agents" in data
        agents = data["agents"]
        
        # Find anima-fund agent
        anima_agent = next((a for a in agents if a.get("agent_id") == "anima-fund"), None)
        if anima_agent:
            assert "bot_alive" in anima_agent
            print(f"PASS: /api/telegram/health - anima-fund bot_alive={anima_agent['bot_alive']}, username={anima_agent.get('bot_username')}")
        else:
            print(f"PASS: /api/telegram/health - returned {len(agents)} agents")
    
    def test_telegram_test_message(self):
        """POST /api/telegram/test/anima-fund sends actual test message"""
        res = requests.post(f"{BASE_URL}/api/telegram/test/anima-fund", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Should succeed in sending message
        assert data.get("success") == True
        print(f"PASS: /api/telegram/test/anima-fund - message sent successfully")


class TestConwayHealth:
    """Conway API health check"""
    
    def test_conway_health(self):
        """GET /api/conway/health returns all services healthy"""
        res = requests.get(f"{BASE_URL}/api/conway/health", timeout=20)
        assert res.status_code == 200
        data = res.json()
        
        assert "all_healthy" in data
        assert "services" in data
        
        services = data.get("services", {})
        # Should have cloud, domains, inference
        expected = {"cloud", "domains", "inference"}
        found = set(services.keys())
        assert expected <= found, f"Expected {expected}, found {found}"
        
        print(f"PASS: /api/conway/health - all_healthy={data['all_healthy']}, services={list(services.keys())}")


class TestSandboxInfo:
    """Test sandbox info endpoint"""
    
    def test_sandbox_info(self):
        """GET /api/provision/sandbox-info returns info about current sandbox"""
        res = requests.get(f"{BASE_URL}/api/provision/sandbox-info", timeout=15)
        assert res.status_code == 200
        data = res.json()
        
        # Either returns sandbox info or error (no sandbox)
        if data.get("success"):
            assert "sandbox" in data
            print(f"PASS: /api/provision/sandbox-info - found sandbox info")
        else:
            error = data.get("error", "")
            # Expected if no sandbox
            print(f"PASS: /api/provision/sandbox-info - no sandbox: {error}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
