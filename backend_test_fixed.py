#!/usr/bin/env python3
"""
Anima Fund Backend API Test Suite
Tests all backend endpoints when engine is NOT running
"""
import requests
import sys
import json
from datetime import datetime


class AnimaFundAPITester:
    def __init__(self, base_url="https://ai-bootstrap-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, expected_data_checks=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if not success:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.text[:200]}...")
                except:
                    pass
                self.failed_tests.append(f"{name}: Status {response.status_code} != {expected_status}")
                return False

            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
            except Exception as e:
                print(f"❌ Failed - Invalid JSON response: {e}")
                self.failed_tests.append(f"{name}: Invalid JSON response")
                return False

            # Check expected data structure
            if expected_data_checks:
                for check_name, check_func in expected_data_checks.items():
                    try:
                        if not check_func(data):
                            print(f"❌ Failed - Data check '{check_name}' failed")
                            print(f"   Data: {json.dumps(data, indent=2)[:300]}...")
                            self.failed_tests.append(f"{name}: Data check '{check_name}' failed")
                            return False
                        else:
                            print(f"   ✓ {check_name}")
                    except Exception as e:
                        print(f"❌ Failed - Data check '{check_name}' error: {e}")
                        self.failed_tests.append(f"{name}: Data check '{check_name}' error: {e}")
                        return False

            self.tests_passed += 1
            print(f"✅ Passed")
            return True

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            return False


def main():
    """Run all backend API tests"""
    print("=" * 80)
    print("🚀 ANIMA FUND BACKEND API TEST SUITE")
    print("=" * 80)
    print(f"Testing against: https://ai-bootstrap-1.preview.emergentagent.com")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    tester = AnimaFundAPITester()
    
    # Test 1: Health endpoint
    print("\n📡 CORE API ENDPOINTS")
    print("-" * 40)
    
    tester.run_test(
        "Health Check",
        "GET", 
        "api/health",
        200,
        {
            "has_status_ok": lambda d: d.get('status') == 'ok',
            "has_creator_wallet": lambda d: d.get('creator_wallet') == 'xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r',
            "has_timestamp": lambda d: 'timestamp' in d,
            "has_engine_live": lambda d: 'engine_live' in d
        }
    )

    # Test 2: Genesis status - should be not_created
    tester.run_test(
        "Genesis Status",
        "GET",
        "api/genesis/status", 
        200,
        {
            "status_not_created": lambda d: d.get('status') == 'not_created',
            "has_creator_wallet": lambda d: d.get('creator_wallet') == 'xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r',
            "engine_not_running": lambda d: d.get('engine_running') == False,
            "engine_not_live": lambda d: d.get('engine_live') == False
        }
    )

    # Test 3: Engine live check
    tester.run_test(
        "Engine Live Check",
        "GET",
        "api/engine/live",
        200,
        {
            "live_false": lambda d: d.get('live') == False,
            "has_db_exists": lambda d: 'db_exists' in d
        }
    )

    # Test 4: Engine status info
    tester.run_test(
        "Engine Status",
        "GET",
        "api/engine/status",
        200,
        {
            "has_genesis_lines": lambda d: d.get('genesis_prompt_lines') == 324,
            "has_skills": lambda d: isinstance(d.get('skills'), list) and len(d.get('skills')) == 6,
            "has_creator_wallet": lambda d: d.get('creator_wallet') == 'xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r',
            "has_engine_name": lambda d: d.get('engine') == 'Anima Fund Runtime'
        }
    )

    # Test 5: Constitution content
    tester.run_test(
        "Constitution",
        "GET",
        "api/constitution",
        200,
        {
            "has_content": lambda d: 'content' in d and len(d.get('content', '')) > 100,
            "has_path": lambda d: 'path' in d
        }
    )

    # Test all live endpoints - should return empty when engine not running
    print("\n🔄 LIVE ENDPOINTS (Engine Not Running)")
    print("-" * 40)
    
    live_endpoints = [
        ("Live Agents", "api/live/agents", 
         {"empty_agents": lambda d: d.get('agents') == [] and d.get('total') == 0}),
        ("Live Turns", "api/live/turns", 
         {"empty_turns": lambda d: d.get('turns') == [] and d.get('total') == 0}), 
        ("Live Activity", "api/live/activity", 
         {"empty_activities": lambda d: d.get('activities') == [] and d.get('total') == 0}),
        ("Live Transactions", "api/live/transactions", 
         {"empty_transactions": lambda d: d.get('transactions') == [] and d.get('total') == 0}),
        ("Live Financials", "api/live/financials", 
         {"empty_financials": lambda d: d == {} or len(d) == 0}),
        ("Live Memory", "api/live/memory", 
         {"empty_memory": lambda d: d.get('facts') == [] and d.get('total') == 0}),
        ("Live Messages", "api/live/messages", 
         {"empty_messages": lambda d: d.get('messages') == [] and d.get('total') == 0}),
        ("Live Relationships", "api/live/relationships", 
         {"empty_relationships": lambda d: d.get('relationships') == [] and d.get('total') == 0}),
        ("Live Discovered", "api/live/discovered", 
         {"empty_discovered": lambda d: d.get('agents') == [] and d.get('total') == 0}),
        ("Live Identity", "api/live/identity", 
         {"identity_null": lambda d: d.get('name') is None}),
    ]
    
    for name, endpoint, checks in live_endpoints:
        tester.run_test(name, "GET", endpoint, 200, checks)

    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for failure in tester.failed_tests:
            print(f"  • {failure}")
    else:
        print("\n✅ ALL TESTS PASSED!")
    
    print("=" * 80)
    
    return 0 if tester.tests_passed == tester.tests_run else 1


if __name__ == "__main__":
    sys.exit(main())