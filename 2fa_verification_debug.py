#!/usr/bin/env python3
"""
2FA Verification Debug - Test different formats for TOTP verification
"""

import requests
import json
import pyotp
import time

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def debug_2fa_verification():
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
    
    # Get 2FA setup
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    setup_response = requests.get(
        f"{API_BASE}/api/user/2fa/setup",
        headers=headers,
        timeout=10
    )
    
    if setup_response.status_code != 200:
        print(f"2FA Setup failed: {setup_response.status_code}")
        return
    
    setup_data = setup_response.json()
    totp_secret = setup_data.get('totp_secret')
    
    if not totp_secret:
        print("No TOTP secret received")
        return
    
    print(f"TOTP Secret: {totp_secret}")
    
    # Generate TOTP code
    totp = pyotp.TOTP(totp_secret)
    totp_code = totp.now()
    print(f"Generated TOTP code: {totp_code}")
    
    # Try different verification formats
    verification_formats = [
        {"totp_code": totp_code},
        {"code": totp_code},
        {"token": totp_code},
        {"otp": totp_code},
        {"totp": totp_code},
        {"verification_code": totp_code},
        {"twofa_code": totp_code}
    ]
    
    for i, verify_data in enumerate(verification_formats):
        print(f"\n🔍 Testing format {i+1}: {verify_data}")
        
        verify_response = requests.post(
            f"{API_BASE}/api/user/2fa/verify",
            json=verify_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {verify_response.status_code}")
        try:
            response_data = verify_response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response: {verify_response.text}")
        
        if verify_response.status_code == 200:
            print("✅ SUCCESS! This format worked.")
            break
    
    # Also try with empty body to see what error we get
    print(f"\n🔍 Testing with empty body:")
    empty_response = requests.post(
        f"{API_BASE}/api/user/2fa/verify",
        json={},
        headers=headers,
        timeout=10
    )
    
    print(f"Empty body status: {empty_response.status_code}")
    try:
        print(f"Empty body response: {json.dumps(empty_response.json(), indent=2)}")
    except:
        print(f"Empty body response: {empty_response.text}")

if __name__ == "__main__":
    debug_2fa_verification()