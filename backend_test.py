import requests
import sys
from datetime import datetime
import json

class AnimaFundAPITester:
    def __init__(self, base_url="https://115fbed8-6e46-49d1-b4f7-8c45a000c04a.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status=200, expected_fields=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
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
                print(f"❌ Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                print(f"   Warning: Response not JSON")

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
                if response_data:
                    print(f"   Response keys: {list(response_data.keys())}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            self.failed_tests.append(f"{name}: Network Error - {str(e)}")
            return False, {}

    def test_health(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            expected_fields=["status", "fund", "timestamp"]
        )
        return success

    def test_fund_overview(self):
        """Test fund overview endpoint"""
        success, response = self.run_test(
            "Fund Overview",
            "GET",
            "/api/fund/overview",
            expected_fields=["fund_name", "current_aum", "total_agents", "alive_agents", "total_deals", "portfolio_companies"]
        )
        if success and response:
            print(f"   Fund: {response.get('fund_name')}, AUM: ${response.get('current_aum', 0)/1000000:.1f}M")
        return success

    def test_agents(self):
        """Test agents endpoint"""
        success, response = self.run_test(
            "Agents List", 
            "GET",
            "/api/agents",
            expected_fields=["agents", "total"]
        )
        if success and response:
            print(f"   Total agents: {response.get('total', 0)}")
        return success

    def test_deals(self):
        """Test deals endpoint"""
        success, response = self.run_test(
            "Deals List",
            "GET", 
            "/api/deals",
            expected_fields=["deals", "total"]
        )
        if success and response:
            print(f"   Total deals: {response.get('total', 0)}")
        return success

    def test_portfolio(self):
        """Test portfolio endpoint"""
        success, response = self.run_test(
            "Portfolio Companies",
            "GET",
            "/api/portfolio", 
            expected_fields=["companies", "total"]
        )
        if success and response:
            print(f"   Portfolio companies: {response.get('total', 0)}")
        return success

    def test_financials_history(self):
        """Test financial history endpoint"""
        success, response = self.run_test(
            "Financial History",
            "GET",
            "/api/financials/history",
            expected_fields=["history"]
        )
        if success and response:
            history = response.get('history', [])
            print(f"   Financial records: {len(history)}")
        return success

    def test_activity(self):
        """Test activity endpoint"""
        success, response = self.run_test(
            "Activity Feed",
            "GET",
            "/api/activity",
            expected_fields=["activities", "total"]
        )
        if success and response:
            print(f"   Activity entries: {response.get('total', 0)}")
        return success

    def test_constitution(self):
        """Test constitution endpoint"""
        success, response = self.run_test(
            "Constitution",
            "GET",
            "/api/constitution",
            expected_fields=["content", "source"]
        )
        if success and response:
            content_length = len(response.get('content', ''))
            print(f"   Constitution length: {content_length} characters")
        return success

    def test_engine_status(self):
        """Test engine status endpoint"""
        success, response = self.run_test(
            "Engine Status",
            "GET", 
            "/api/engine/status",
            expected_fields=["engine", "repo_present", "version"]
        )
        if success and response:
            print(f"   Engine: {response.get('engine')}, Repo present: {response.get('repo_present')}")
            if not response.get('repo_present'):
                print("   ⚠️  Warning: repo_present should be true according to requirements")
        return success

    def test_additional_endpoints(self):
        """Test additional endpoints mentioned in the code"""
        success_count = 0
        
        # Test agent hierarchy  
        success, _ = self.run_test("Agent Hierarchy", "GET", "/api/agents/hierarchy/tree")
        if success: success_count += 1

        # Test deal pipeline
        success, _ = self.run_test("Deal Pipeline", "GET", "/api/deals/pipeline")
        if success: success_count += 1

        # Test financial summary
        success, _ = self.run_test("Financial Summary", "GET", "/api/financials/summary")
        if success: success_count += 1

        # Test config
        success, _ = self.run_test("Fund Config", "GET", "/api/config")
        if success: success_count += 1

        # Test departments
        success, _ = self.run_test("Departments", "GET", "/api/departments")
        if success: success_count += 1

        return success_count

def main():
    # Setup
    tester = AnimaFundAPITester()
    print(f"🚀 Starting Anima Fund API Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Base URL: {tester.base_url}")

    # Run core API tests
    test_results = []
    test_results.append(tester.test_health())
    test_results.append(tester.test_fund_overview())
    test_results.append(tester.test_agents())
    test_results.append(tester.test_deals())
    test_results.append(tester.test_portfolio())
    test_results.append(tester.test_financials_history())
    test_results.append(tester.test_activity())
    test_results.append(tester.test_constitution())
    test_results.append(tester.test_engine_status())

    # Additional endpoint tests
    additional_passed = tester.test_additional_endpoints()

    # Print results
    core_passed = sum(test_results)
    total_passed = tester.tests_passed
    total_tests = tester.tests_run

    print(f"\n📊 Test Results:")
    print(f"   Core APIs: {core_passed}/9 passed")
    print(f"   Additional APIs: {additional_passed}/5 passed") 
    print(f"   Total: {total_passed}/{total_tests} tests passed")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in tester.failed_tests:
            print(f"   - {failure}")

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())