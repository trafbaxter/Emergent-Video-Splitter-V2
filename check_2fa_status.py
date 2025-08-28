#!/usr/bin/env python3
"""
Check 2FA Status - Create a new user to test 2FA functionality
"""

import requests
import json
import pyotp
import time

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def test_2fa_with_new_user():
    # Create a new test user
    test_user_data = {
        "email": f"test-2fa-{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "firstName": "Test",
        "lastName": "User",
        "confirmPassword": "TestPassword123!"
    }
    
    print(f"Creating test user: {test_user_data['email']}")
    
    # Register test user
    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json=test_user_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Registration status: {register_response.status_code}")
    if register_response.status_code not in [200, 201]:
        print(f"Registration failed: {register_response.text}")
        return
    
    register_data = register_response.json()
    token = register_data.get('access_token')
    
    if not token:
        print("No access token received from registration")
        return
    
    print("✅ Test user created successfully")
    
    # Test 2FA setup
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔍 Testing 2FA Setup...")
    setup_response = requests.get(
        f"{API_BASE}/api/user/2fa/setup",
        headers=headers,
        timeout=10
    )
    
    print(f"2FA Setup status: {setup_response.status_code}")
    if setup_response.status_code == 200:
        setup_data = setup_response.json()
        print(f"2FA Setup response: {json.dumps(setup_data, indent=2)}")
        
        totp_secret = setup_data.get('totp_secret')
        if totp_secret:
            print(f"\nTOTP Secret: {totp_secret}")
            
            # Generate and verify TOTP code
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
            print(f"Generated TOTP code: {totp_code}")
            
            # Test 2FA verification
            print("\n🔍 Testing 2FA Verification...")
            verify_data = {"code": totp_code}
            
            verify_response = requests.post(
                f"{API_BASE}/api/user/2fa/verify",
                json=verify_data,
                headers=headers,
                timeout=10
            )
            
            print(f"2FA Verify status: {verify_response.status_code}")
            print(f"2FA Verify response: {json.dumps(verify_response.json(), indent=2)}")
            
            if verify_response.status_code == 200:
                # Test profile endpoint
                print("\n🔍 Testing Profile Endpoint...")
                profile_response = requests.get(
                    f"{API_BASE}/api/user/profile",
                    headers=headers,
                    timeout=10
                )
                
                print(f"Profile status: {profile_response.status_code}")
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"Profile response: {json.dumps(profile_data, indent=2)}")
                    
                    totp_enabled = profile_data.get('user', {}).get('totpEnabled')
                    print(f"\nTOTP Enabled in profile: {totp_enabled}")
                
                # Test login with 2FA
                print("\n🔍 Testing Login with 2FA...")
                
                # Wait a moment and generate new code
                time.sleep(2)
                new_totp_code = totp.now()
                
                login_2fa_data = {
                    "email": test_user_data['email'],
                    "password": test_user_data['password'],
                    "code": new_totp_code
                }
                
                login_2fa_response = requests.post(
                    f"{API_BASE}/api/auth/login",
                    json=login_2fa_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f"Login with 2FA status: {login_2fa_response.status_code}")
                print(f"Login with 2FA response: {json.dumps(login_2fa_response.json(), indent=2)}")

if __name__ == "__main__":
    test_2fa_with_new_user()