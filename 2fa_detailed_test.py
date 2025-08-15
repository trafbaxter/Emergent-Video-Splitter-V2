#!/usr/bin/env python3
"""
2FA Detailed Test - More thorough testing of 2FA functionality
"""

import requests
import json
import pyotp
import time

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def detailed_2fa_test():
    # Login first
    login_data = {
        "email": "admin@videosplitter.com",
        "password": "AdminPass123!"
    }
    
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json=login_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    token = data.get('access_token')
    
    print("🔐 Login successful")
    print()
    
    # Test 2FA setup
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Testing 2FA Setup...")
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
            print(f"TOTP Secret: {totp_secret}")
            
            # Generate TOTP code
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
            print(f"Generated TOTP code: {totp_code}")
            
            # Test 2FA verification
            print("\n🔍 Testing 2FA Verification...")
            verify_data = {
                "totp_code": totp_code
            }
            
            verify_response = requests.post(
                f"{API_BASE}/api/user/2fa/verify",
                json=verify_data,
                headers=headers,
                timeout=10
            )
            
            print(f"2FA Verify status: {verify_response.status_code}")
            print(f"2FA Verify response: {json.dumps(verify_response.json(), indent=2)}")
            
            # Check profile after verification
            print("\n🔍 Testing Profile after 2FA verification...")
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
                print(f"TOTP Enabled in profile: {totp_enabled}")
            
            # Test login with 2FA
            print("\n🔍 Testing Login with 2FA...")
            
            # Generate new TOTP code for login
            time.sleep(1)  # Wait a second to ensure different code
            new_totp_code = totp.now()
            
            login_2fa_data = {
                "email": "admin@videosplitter.com",
                "password": "AdminPass123!",
                "totp_code": new_totp_code
            }
            
            login_2fa_response = requests.post(
                f"{API_BASE}/api/auth/login",
                json=login_2fa_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"Login with 2FA status: {login_2fa_response.status_code}")
            print(f"Login with 2FA response: {json.dumps(login_2fa_response.json(), indent=2)}")
    
    # Test password reset endpoints
    print("\n🔍 Testing Password Reset Endpoints...")
    
    reset_endpoints = [
        "/api/auth/forgot-password",
        "/api/auth/password-reset",
        "/api/user/forgot-password",
        "/api/user/password-reset"
    ]
    
    for endpoint in reset_endpoints:
        reset_data = {"email": "admin@videosplitter.com"}
        
        try:
            reset_response = requests.post(
                f"{API_BASE}{endpoint}",
                json=reset_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"{endpoint}: {reset_response.status_code}")
            if reset_response.status_code != 404:
                try:
                    print(f"  Response: {json.dumps(reset_response.json(), indent=2)}")
                except:
                    print(f"  Response: {reset_response.text}")
        except Exception as e:
            print(f"{endpoint}: Error - {str(e)}")

if __name__ == "__main__":
    detailed_2fa_test()