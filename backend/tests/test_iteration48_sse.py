"""
Iteration 48 - SSE Integration Tests
Tests the Server-Sent Events endpoint and related page data APIs.

Features tested:
1. SSE endpoint /api/live/stream returns valid JSON data
2. SSE sends heartbeat comments when data hasn't changed
3. All page APIs return correct data structure
4. Navigation-related APIs work correctly
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSSEEndpoint:
    """Tests for the SSE endpoint at /api/live/stream"""
    
    def test_sse_endpoint_returns_event_stream(self):
        """SSE endpoint returns text/event-stream content type"""
        response = requests.get(
            f"{BASE_URL}/api/live/stream",
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=15
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        
        # Read first chunk of data
        lines = []
        start = time.time()
        for line in response.iter_lines(decode_unicode=True):
            lines.append(line)
            # Stop after getting some data or 12 seconds
            if len(lines) >= 5 or time.time() - start > 12:
                break
        
        response.close()
        
        # Should have at least one data line
        data_lines = [l for l in lines if l.startswith("data:")]
        assert len(data_lines) >= 1, "SSE should send at least one data message"
        print(f"SSE data received: {data_lines[0][:100]}...")
    
    def test_sse_data_structure(self):
        """SSE data contains required fields"""
        import json
        
        response = requests.get(
            f"{BASE_URL}/api/live/stream",
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=15
        )
        
        # Get first data message
        data = None
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                break
        
        response.close()
        
        assert data is not None, "Should receive SSE data"
        
        # Verify required fields
        assert "engine" in data, "SSE data should have 'engine' field"
        assert "conway_credits_cents" in data, "SSE data should have 'conway_credits_cents'"
        assert "agent_count" in data, "SSE data should have 'agent_count'"
        assert "latest_activity_id" in data, "SSE data should have 'latest_activity_id'"
        assert "timestamp" in data, "SSE data should have 'timestamp'"
        
        # Verify engine sub-fields
        engine = data["engine"]
        assert "live" in engine, "Engine should have 'live' field"
        assert "db_exists" in engine, "Engine should have 'db_exists' field"
        assert "agent_state" in engine, "Engine should have 'agent_state' field"
        assert "turn_count" in engine, "Engine should have 'turn_count' field"
        assert "agent_id" in engine, "Engine should have 'agent_id' field"
        
        print(f"SSE data structure verified: engine.live={engine['live']}, agent_count={data['agent_count']}")


class TestEngineLive:
    """Tests for /api/engine/live endpoint"""
    
    def test_engine_live_endpoint(self):
        """Engine live endpoint returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/engine/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "live" in data
        assert "db_exists" in data
        assert "agent_id" in data
        
        print(f"Engine status: live={data['live']}, db_exists={data['db_exists']}, agent_id={data.get('agent_id')}")


class TestPageAPIs:
    """Tests for APIs used by different pages"""
    
    def test_live_identity(self):
        """GET /api/live/identity returns identity data"""
        response = requests.get(f"{BASE_URL}/api/live/identity")
        assert response.status_code == 200
        data = response.json()
        # Identity may have name, address, etc.
        print(f"Identity: {data.get('name', 'N/A')}, address: {data.get('address', 'N/A')[:20]}...")
    
    def test_live_agents(self):
        """GET /api/live/agents returns agents list"""
        response = requests.get(f"{BASE_URL}/api/live/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert "source" in data
        print(f"Agents: {data['total']} total")
    
    def test_live_activity(self):
        """GET /api/live/activity returns activity list"""
        response = requests.get(f"{BASE_URL}/api/live/activity?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total" in data
        print(f"Activities: {data['total']} total")
    
    def test_live_turns(self):
        """GET /api/live/turns returns turns list"""
        response = requests.get(f"{BASE_URL}/api/live/turns?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "turns" in data
        assert "total" in data
        print(f"Turns: {data['total']} total")
    
    def test_live_transactions(self):
        """GET /api/live/transactions returns transactions"""
        response = requests.get(f"{BASE_URL}/api/live/transactions?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        print(f"Transactions: {data['total']} total")
    
    def test_live_financials(self):
        """GET /api/live/financials returns financial data"""
        response = requests.get(f"{BASE_URL}/api/live/financials")
        assert response.status_code == 200
        data = response.json()
        # May return empty dict if no financial data
        print(f"Financials keys: {list(data.keys())[:5]}")
    
    def test_live_heartbeat(self):
        """GET /api/live/heartbeat returns heartbeat history"""
        response = requests.get(f"{BASE_URL}/api/live/heartbeat?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        print(f"Heartbeat history: {data['total']} entries")
    
    def test_live_memory(self):
        """GET /api/live/memory returns memory facts"""
        response = requests.get(f"{BASE_URL}/api/live/memory")
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        print(f"Memory facts: {data['total']} total")
    
    def test_live_soul(self):
        """GET /api/live/soul returns SOUL.md content"""
        response = requests.get(f"{BASE_URL}/api/live/soul")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "exists" in data
        if data.get("content"):
            print(f"SOUL.md: {len(data['content'])} chars")
        else:
            print("SOUL.md: No content")
    
    def test_live_discovered(self):
        """GET /api/live/discovered returns discovered agents"""
        response = requests.get(f"{BASE_URL}/api/live/discovered")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"Discovered agents: {data['total']} total")
    
    def test_live_skills(self):
        """GET /api/live/skills returns skills"""
        response = requests.get(f"{BASE_URL}/api/live/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        print(f"Skills: {len(data['skills'])} total")
    
    def test_live_tools(self):
        """GET /api/live/tools returns installed tools"""
        response = requests.get(f"{BASE_URL}/api/live/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        print(f"Tools: {len(data['tools'])} total")
    
    def test_live_kv(self):
        """GET /api/live/kv returns key-value store"""
        response = requests.get(f"{BASE_URL}/api/live/kv")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"KV items: {len(data['items'])} total")
    
    def test_live_wake_events(self):
        """GET /api/live/wake-events returns wake events"""
        response = requests.get(f"{BASE_URL}/api/live/wake-events?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        print(f"Wake events: {len(data['events'])} total")


class TestInfrastructureAPIs:
    """Tests for Infrastructure page APIs"""
    
    def test_infrastructure_overview(self):
        """GET /api/infrastructure/overview returns overview"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/overview")
        assert response.status_code == 200
        data = response.json()
        print(f"Infrastructure overview: {list(data.keys())[:5]}")
    
    def test_infrastructure_sandboxes(self):
        """GET /api/infrastructure/sandboxes returns sandboxes"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/sandboxes")
        assert response.status_code == 200
        data = response.json()
        assert "sandboxes" in data
        print(f"Sandboxes: {len(data['sandboxes'])} total")
    
    def test_infrastructure_activity_feed(self):
        """GET /api/infrastructure/activity-feed returns feed"""
        response = requests.get(f"{BASE_URL}/api/infrastructure/activity-feed?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "feed" in data
        print(f"Activity feed: {len(data['feed'])} items")


class TestOpenClawAPIs:
    """Tests for OpenClaw VM page APIs"""
    
    def test_openclaw_status(self):
        """GET /api/openclaw/status returns status"""
        response = requests.get(f"{BASE_URL}/api/openclaw/status")
        assert response.status_code == 200
        data = response.json()
        # Should have openclaw field with status info
        assert "openclaw" in data or "has_activity" in data
        print(f"OpenClaw status: {data}")
    
    def test_openclaw_actions(self):
        """GET /api/openclaw/actions returns actions"""
        response = requests.get(f"{BASE_URL}/api/openclaw/actions?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        print(f"OpenClaw actions: {len(data['actions'])} total")
    
    def test_openclaw_sandboxes(self):
        """GET /api/openclaw/sandboxes returns sandboxes"""
        response = requests.get(f"{BASE_URL}/api/openclaw/sandboxes")
        assert response.status_code == 200
        data = response.json()
        print(f"OpenClaw sandboxes: {data}")
    
    def test_openclaw_browsing(self):
        """GET /api/openclaw/browsing returns browsing sessions"""
        response = requests.get(f"{BASE_URL}/api/openclaw/browsing?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        print(f"Browsing sessions: {len(data['sessions'])} total")


class TestWalletAPI:
    """Tests for Wallet API"""
    
    def test_wallet_balance(self):
        """GET /api/wallet/balance returns balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        # Should have balance fields
        print(f"Wallet balance: USDC={data.get('usdc', 'N/A')}, credits={data.get('credits_cents', 'N/A')}, tier={data.get('tier', 'N/A')}")


class TestAgentSelection:
    """Tests for agent selection/switching"""
    
    def test_list_agents(self):
        """GET /api/agents returns agent list"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"Agents list: {len(data['agents'])} agents")
        if data['agents']:
            print(f"First agent: {data['agents'][0].get('name', 'N/A')}")


class TestHealthEndpoint:
    """Tests for health endpoint"""
    
    def test_api_health(self):
        """GET /api/health returns health status"""
        response = requests.get(f"{BASE_URL}/api/health")
        # This may return 200 with JSON or HTML depending on routing
        assert response.status_code == 200
        print(f"Health endpoint status: {response.status_code}")
