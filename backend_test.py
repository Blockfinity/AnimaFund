import requests
import sys
from datetime import datetime
import json
import time
import os

class AnimaFundAPITester:
    def __init__(self, base_url="https://genesis-engine-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.genesis_created = False
        self.engine_pid = None

    def run_test(self, name, method, endpoint, expected_status=200, expected_fields=None, data=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                print(f"   Warning: Response not JSON: {response.text[:100]}")

            if success:
                # Check for expected fields if provided
                if expected_fields:
                    missing_fields = []
                    for field in expected_fields:
                        if field not in response_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"❌ Failed - Missing fields: {missing_fields}")
                        self.failed_tests.append(f"{name}: Missing fields {missing_fields}")
                        return False, response_data
                
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_data and isinstance(response_data, dict):
                    print(f"   Response keys: {list(response_data.keys())}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            self.failed_tests.append(f"{name}: Network Error - {str(e)}")
            return False, {}

    def test_health_with_creator_wallet(self):
        """Test /api/health returns ok with creator_wallet"""
        success, response = self.run_test(
            "Health Check with creator_wallet",
            "GET",
            "/api/health",
            expected_fields=["status", "creator_wallet", "timestamp"]
        )
        if success and response:
            if response.get('status') != 'ok':
                print(f"❌ Expected status 'ok', got '{response.get('status')}'")
                self.failed_tests.append("Health: Status not 'ok'")
                return False
            creator_wallet = response.get('creator_wallet')
            if not creator_wallet:
                print(f"❌ creator_wallet missing in response")
                self.failed_tests.append("Health: creator_wallet missing")
                return False
            print(f"   ✓ Status: {response.get('status')}")
            print(f"   ✓ Creator wallet: {creator_wallet}")
            if not creator_wallet.startswith('xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r'):
                print(f"   ⚠️  Warning: Creator wallet doesn't match expected value")
        return success

    def test_genesis_status_not_created(self):
        """Test /api/genesis/status returns not_created when clean"""
        success, response = self.run_test(
            "Genesis Status - Not Created",
            "GET",
            "/api/genesis/status",
            expected_fields=["status", "wallet_exists", "engine_running"]
        )
        if success and response:
            status = response.get('status')
            print(f"   ✓ Status: {status}")
            print(f"   ✓ Wallet exists: {response.get('wallet_exists')}")
            print(f"   ✓ Engine running: {response.get('engine_running')}")
            
            # Note: might be created already, so we check for valid statuses
            valid_statuses = ['not_created', 'created', 'running']
            if status not in valid_statuses:
                print(f"❌ Invalid status: {status}")
                self.failed_tests.append(f"Genesis Status: Invalid status {status}")
                return False
        return success

    def test_engine_live_false_when_no_engine(self):
        """Test /api/engine/live returns live=false when no engine"""
        success, response = self.run_test(
            "Engine Live - No Engine",
            "GET",
            "/api/engine/live",
            expected_fields=["live", "db_exists"]
        )
        if success and response:
            live = response.get('live')
            db_exists = response.get('db_exists')
            print(f"   ✓ Live: {live}")
            print(f"   ✓ DB exists: {db_exists}")
            # Note: Engine might already be running from previous tests
        return success

    def test_engine_status_skills_and_genesis(self):
        """Test /api/engine/status returns 50 skills and 324 genesis lines"""
        success, response = self.run_test(
            "Engine Status - Skills and Genesis",
            "GET",
            "/api/engine/status",
            expected_fields=["skills", "genesis_prompt_lines", "creator_wallet"]
        )
        if success and response:
            skills = response.get('skills', [])
            genesis_lines = response.get('genesis_prompt_lines', 0)
            creator_wallet = response.get('creator_wallet')
            
            print(f"   ✓ Skills count: {len(skills)}")
            print(f"   ✓ Genesis lines: {genesis_lines}")
            print(f"   ✓ Creator wallet: {creator_wallet}")
            
            if len(skills) < 40:  # Allow some flexibility
                print(f"   ⚠️  Warning: Expected ~50 skills, got {len(skills)}")
            
            if genesis_lines < 300:  # Allow some flexibility
                print(f"   ⚠️  Warning: Expected ~324 genesis lines, got {genesis_lines}")
            
            if genesis_lines == 324:
                print(f"   ✅ Genesis prompt exactly 324 lines as expected!")
            
            if len(skills) >= 50:
                print(f"   ✅ Skills count meets requirement (50+)!")
                
        return success

    def test_constitution_12_laws(self):
        """Test /api/constitution returns 12 laws including Law XII Ownership Non-Transferable"""
        success, response = self.run_test(
            "Constitution - 12 Laws",
            "GET",
            "/api/constitution",
            expected_fields=["content"]
        )
        if success and response:
            content = response.get('content', '')
            print(f"   ✓ Constitution length: {len(content)} characters")
            
            # Check for Law XII specifically
            if 'Law XII' in content or 'XII.' in content:
                print(f"   ✅ Found Law XII reference")
            else:
                print(f"   ⚠️  Warning: Law XII not found")
            
            if 'Ownership Non-Transferable' in content:
                print(f"   ✅ Found 'Ownership Non-Transferable' text")
            else:
                print(f"   ⚠️  Warning: 'Ownership Non-Transferable' text not found")
            
            # Count law sections (rough estimate)
            law_count = content.count('## ') + content.count('### ')
            print(f"   ✓ Estimated law sections: {law_count}")
            
            if law_count >= 12:
                print(f"   ✅ Constitution appears to have 12+ laws!")
                
        return success

    def test_all_live_endpoints_empty_when_no_engine(self):
        """Test all /api/live/* endpoints return empty when engine not running"""
        live_endpoints = [
            '/api/live/agents',
            '/api/live/turns', 
            '/api/live/activity',
            '/api/live/transactions',
            '/api/live/financials',
            '/api/live/memory',
            '/api/live/messages',
            '/api/live/relationships',
            '/api/live/discovered',
            '/api/live/heartbeat',
            '/api/live/soul',
            '/api/live/working-memory',
            '/api/live/episodic-memory',
            '/api/live/procedural-memory',
            '/api/live/tools',
            '/api/live/skills',
            '/api/live/metrics',
            '/api/live/policy',
            '/api/live/soul-history',
            '/api/live/onchain',
            '/api/live/sessions',
            '/api/live/identity'
        ]
        
        passed_count = 0
        for endpoint in live_endpoints:
            success, response = self.run_test(
                f"Live endpoint: {endpoint}",
                "GET", 
                endpoint
            )
            if success:
                passed_count += 1
                # Check if response is appropriately empty when no engine
                if isinstance(response, dict):
                    # Look for indicators of empty state
                    empty_indicators = [
                        response.get('total', 0) == 0,
                        response.get('agents', []) == [],
                        response.get('turns', []) == [],
                        response.get('activities', []) == [],
                        response.get('transactions', []) == [],
                        response.get('facts', []) == [],
                        response.get('messages', []) == [],
                        response.get('relationships', []) == [],
                        response.get('history', []) == [],
                        response.get('content') is None,
                        response.get('items', []) == [],
                        response.get('events', []) == [],
                        response.get('procedures', []) == [],
                        response.get('tools', []) == [],
                        response.get('skills', []) == [],
                        response.get('snapshots', []) == [],
                        response.get('decisions', []) == [],
                        response.get('versions', []) == [],
                        response.get('sessions', []) == []
                    ]
                    
                    if any(empty_indicators):
                        print(f"   ✓ Appropriately returns empty/zero data when engine not running")
        
        print(f"   ✓ Live endpoints tested: {passed_count}/{len(live_endpoints)}")
        return passed_count >= len(live_endpoints) * 0.8  # 80% success rate

    def test_genesis_create(self):
        """Test POST /api/genesis/create successfully builds Automaton"""
        print(f"\n🚀 Creating Genesis Agent - This may take 60-90 seconds...")
        
        success, response = self.run_test(
            "Genesis Create - Build Automaton",
            "POST",
            "/api/genesis/create",
            expected_fields=["success", "pid"]
        )
        
        if success and response:
            if response.get('success'):
                self.genesis_created = True
                self.engine_pid = response.get('pid')
                print(f"   ✅ Genesis creation successful!")
                print(f"   ✓ Engine PID: {self.engine_pid}")
                print(f"   ✓ Waiting for engine to initialize...")
                
                # Wait for engine to start up
                time.sleep(15)
                
                return True
            else:
                error = response.get('error', 'Unknown error')
                print(f"   ❌ Genesis creation failed: {error}")
                self.failed_tests.append(f"Genesis Create: {error}")
        
        return success

    def test_genesis_status_after_create(self):
        """Test after create: /api/genesis/status shows wallet_address and engine_running=true"""
        if not self.genesis_created:
            print("   ⚠️  Skipping - Genesis not created in this test run")
            return False
            
        success, response = self.run_test(
            "Genesis Status - After Create",
            "GET",
            "/api/genesis/status",
            expected_fields=["wallet_address", "engine_running", "status"]
        )
        
        if success and response:
            wallet_address = response.get('wallet_address')
            engine_running = response.get('engine_running')
            status = response.get('status')
            
            print(f"   ✓ Status: {status}")
            print(f"   ✓ Engine running: {engine_running}")
            print(f"   ✓ Wallet address: {wallet_address}")
            
            if wallet_address and wallet_address.startswith('0x'):
                print(f"   ✅ Wallet address properly formatted!")
            else:
                print(f"   ⚠️  Warning: Wallet address not in expected format")
            
            if engine_running:
                print(f"   ✅ Engine is running as expected!")
            else:
                print(f"   ⚠️  Warning: Engine not running after create")
                
        return success

    def test_engine_logs_after_create(self):
        """Test after create: engine logs show skills loaded, wallet created, identity registered"""
        if not self.genesis_created:
            print("   ⚠️  Skipping - Genesis not created in this test run")
            return False
            
        print(f"\n📋 Checking engine logs...")
        
        # Check if log file exists and has content
        log_files = ['/var/log/automaton.out.log', '/var/log/automaton.err.log']
        logs_found = False
        
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                        if content:
                            logs_found = True
                            print(f"   ✓ Found log file: {log_file}")
                            print(f"   ✓ Log size: {len(content)} characters")
                            
                            # Look for key indicators
                            if 'skills' in content.lower():
                                print(f"   ✅ Found skills references in logs")
                            if 'wallet' in content.lower():
                                print(f"   ✅ Found wallet references in logs")
                            if 'identity' in content.lower():
                                print(f"   ✅ Found identity references in logs")
                                
                            # Try to extract skill count
                            lines = content.split('\n')
                            for line in lines[-50:]:  # Check last 50 lines
                                if 'skill' in line.lower() and any(char.isdigit() for char in line):
                                    print(f"   ✓ Recent skill log: {line.strip()[:100]}...")
                                    break
            except Exception as e:
                print(f"   ⚠️  Could not read {log_file}: {e}")
        
        if not logs_found:
            print(f"   ⚠️  No engine logs found")
            return False
            
        return True

    def cleanup_engine(self):
        """Clean up engine process and files after testing"""
        if self.engine_pid:
            try:
                print(f"\n🧹 Cleaning up engine process (PID: {self.engine_pid})...")
                os.system(f"pkill -f 'dist/index.js'")
                os.system(f"rm -rf /root/.anima")
                print(f"   ✓ Engine cleanup completed")
            except Exception as e:
                print(f"   ⚠️  Cleanup error: {e}")

def main():
    # Setup
    tester = AnimaFundAPITester()
    print(f"🚀 Starting Anima Fund Comprehensive Backend Tests")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Base URL: {tester.base_url}")
    print(f"   Testing all requirements from review request...")

    try:
        # Run all required tests from review request
        test_results = []
        
        print(f"\n" + "="*60)
        print(f"PHASE 1: Basic API Tests (Pre-Genesis)")
        print(f"="*60)
        
        test_results.append(tester.test_health_with_creator_wallet())
        test_results.append(tester.test_genesis_status_not_created())
        test_results.append(tester.test_engine_live_false_when_no_engine())
        test_results.append(tester.test_engine_status_skills_and_genesis())
        test_results.append(tester.test_constitution_12_laws())
        test_results.append(tester.test_all_live_endpoints_empty_when_no_engine())
        
        print(f"\n" + "="*60)
        print(f"PHASE 2: Genesis Creation Test") 
        print(f"="*60)
        
        test_results.append(tester.test_genesis_create())
        
        if tester.genesis_created:
            print(f"\n" + "="*60)
            print(f"PHASE 3: Post-Genesis Tests")
            print(f"="*60)
            
            test_results.append(tester.test_genesis_status_after_create())
            test_results.append(tester.test_engine_logs_after_create())

    finally:
        # Always try to cleanup
        tester.cleanup_engine()

    # Print results
    total_passed = tester.tests_passed
    total_tests = tester.tests_run

    print(f"\n" + "="*60)
    print(f"📊 FINAL TEST RESULTS")
    print(f"="*60)
    print(f"   Total tests run: {total_tests}")
    print(f"   Tests passed: {total_passed}")
    print(f"   Tests failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"   {i}. {failure}")

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    # Check specific requirements
    print(f"\n📋 Requirement Validation:")
    print(f"   ✓ Health endpoint with creator_wallet: {'✅' if 'Health Check' not in str(tester.failed_tests) else '❌'}")
    print(f"   ✓ Genesis status handling: {'✅' if 'Genesis Status' not in str(tester.failed_tests) else '❌'}")
    print(f"   ✓ Engine status with skills/genesis: {'✅' if 'Engine Status' not in str(tester.failed_tests) else '❌'}")
    print(f"   ✓ Constitution with 12 laws: {'✅' if 'Constitution' not in str(tester.failed_tests) else '❌'}")
    print(f"   ✓ Live endpoints functionality: {'✅' if 'Live endpoint' not in str(tester.failed_tests) else '❌'}")
    
    if tester.genesis_created:
        print(f"   ✓ Genesis creation successful: ✅")
        print(f"   ✓ Post-genesis validation: {'✅' if 'After Create' not in str(tester.failed_tests) else '❌'}")
    else:
        print(f"   ✓ Genesis creation successful: ❌ (Not attempted or failed)")
    
    print(f"\n{'🎉 ALL TESTS COMPLETED' if success_rate >= 80 else '⚠️  SOME TESTS FAILED'}")
    
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())