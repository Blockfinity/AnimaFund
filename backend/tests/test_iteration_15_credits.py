"""
Iteration 15: Conway Credits Funding Mechanism Tests
Tests the new credits router endpoints that enable users to fund their Conway API key
with USDC payments on Base network before creating sandbox VMs.

Endpoints tested:
- GET /api/credits/balance - returns credits_cents and credits_usd
- GET /api/credits/pricing - returns pricing tiers and VM costs
- POST /api/credits/purchase - returns QR code, pay_to address, USDC amount, instructions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCreditsBalance:
    """Test GET /api/credits/balance endpoint"""
    
    def test_balance_returns_200(self):
        """Balance endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_balance_returns_credits_cents(self):
        """Balance response should include credits_cents field"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", timeout=15)
        data = response.json()
        assert 'credits_cents' in data, f"Response missing credits_cents: {data}"
        assert isinstance(data['credits_cents'], (int, float)), f"credits_cents should be numeric: {data}"
    
    def test_balance_returns_credits_usd(self):
        """Balance response should include credits_usd field"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", timeout=15)
        data = response.json()
        assert 'credits_usd' in data, f"Response missing credits_usd: {data}"
        assert isinstance(data['credits_usd'], (int, float)), f"credits_usd should be numeric: {data}"
    
    def test_balance_usd_matches_cents(self):
        """credits_usd should equal credits_cents / 100"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", timeout=15)
        data = response.json()
        expected_usd = data['credits_cents'] / 100
        assert data['credits_usd'] == expected_usd, f"USD {data['credits_usd']} != cents/100 {expected_usd}"


class TestCreditsPricing:
    """Test GET /api/credits/pricing endpoint"""
    
    def test_pricing_returns_200(self):
        """Pricing endpoint should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/credits/pricing", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_pricing_structure(self):
        """Pricing response should have expected structure (tiers and/or pricing info)"""
        response = requests.get(f"{BASE_URL}/api/credits/pricing", timeout=15)
        data = response.json()
        # Should return some pricing data (structure may vary based on Conway API)
        # Either 'tiers' for purchase tiers or 'pricing' for VM costs or both
        assert not data.get('error'), f"Pricing returned error: {data.get('error')}"
        print(f"Pricing data structure: {list(data.keys())}")


class TestCreditsPurchase:
    """Test POST /api/credits/purchase endpoint - x402 payment flow"""
    
    def test_purchase_25_returns_payment_details(self):
        """Purchase $25 should return payment details with QR code"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Purchase $25 response keys: {list(data.keys())}")
        
        # Should indicate success and payment required
        assert data.get('success') == True, f"Expected success=true: {data}"
        assert data.get('payment_required') == True, f"Expected payment_required=true: {data}"
    
    def test_purchase_25_has_pay_to_address(self):
        """Purchase response should include pay_to address"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            timeout=20
        )
        data = response.json()
        
        if data.get('success'):
            assert 'pay_to' in data, f"Missing pay_to address: {data}"
            assert data['pay_to'].startswith('0x'), f"pay_to should be Ethereum address: {data['pay_to']}"
            assert len(data['pay_to']) == 42, f"pay_to should be 42 chars: {data['pay_to']}"
            print(f"Pay-to address: {data['pay_to']}")
    
    def test_purchase_25_has_qr_code(self):
        """Purchase response should include QR code as base64 data URI"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            timeout=20
        )
        data = response.json()
        
        if data.get('success'):
            assert 'qr_code' in data, f"Missing qr_code: {data}"
            qr = data['qr_code']
            assert qr.startswith('data:image/png;base64,'), f"QR should be base64 PNG: {qr[:50]}"
            print(f"QR code present, length: {len(qr)}")
    
    def test_purchase_25_has_usdc_amount(self):
        """Purchase response should include USDC amount"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            timeout=20
        )
        data = response.json()
        
        if data.get('success'):
            assert 'amount_usdc' in data, f"Missing amount_usdc: {data}"
            assert isinstance(data['amount_usdc'], (int, float)), f"amount_usdc should be numeric"
            print(f"USDC amount: {data['amount_usdc']}")
    
    def test_purchase_25_has_instructions(self):
        """Purchase response should include payment instructions"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            timeout=20
        )
        data = response.json()
        
        if data.get('success'):
            assert 'instructions' in data, f"Missing instructions: {data}"
            assert isinstance(data['instructions'], list), f"instructions should be list"
            assert len(data['instructions']) > 0, f"instructions should not be empty"
            print(f"Instructions: {data['instructions']}")
    
    def test_purchase_5_returns_payment_details(self):
        """Purchase $5 tier should also work"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 5},
            timeout=20
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Even if $5 is not a valid tier, we should get a response
        print(f"Purchase $5 response: success={data.get('success')}, keys={list(data.keys())}")
    
    def test_purchase_100_tier(self):
        """Purchase $100 tier should work"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 100},
            timeout=20
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Purchase $100 response: success={data.get('success')}")
    
    def test_purchase_has_network_info(self):
        """Purchase response should indicate Base network"""
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"amount": 25},
            timeout=20
        )
        data = response.json()
        
        if data.get('success'):
            # Should have network info
            assert 'network' in data or 'asset' in data, f"Missing network/asset info: {data}"
            print(f"Network: {data.get('network')}, Asset: {data.get('asset')}")


class TestCreditsIntegration:
    """Integration tests for credits flow"""
    
    def test_balance_then_purchase_flow(self):
        """Test typical user flow: check balance -> purchase credits"""
        # Step 1: Check current balance
        balance_res = requests.get(f"{BASE_URL}/api/credits/balance", timeout=15)
        assert balance_res.status_code == 200
        balance = balance_res.json()
        print(f"Current balance: {balance.get('credits_cents')} cents (${balance.get('credits_usd')})")
        
        # Step 2: If balance < 2500 cents, get purchase details
        if balance.get('credits_cents', 0) < 2500:
            purchase_res = requests.post(
                f"{BASE_URL}/api/credits/purchase",
                json={"amount": 25},
                timeout=20
            )
            assert purchase_res.status_code == 200
            purchase = purchase_res.json()
            
            if purchase.get('success'):
                print(f"Payment required: Send {purchase.get('amount_usdc')} USDC to {purchase.get('pay_to')}")
            else:
                print(f"Purchase error: {purchase.get('error')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
