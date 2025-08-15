#!/usr/bin/env python3
"""
Debug 2FA Login
"""

import requests
import json
import pyotp

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def debug_2fa_login():
    totp_secret = "DRBRJPJWOTA3JXXLJGOJHJWUGCNVURGP"
    
    # Generate TOTP code
    totp = pyotp.TOTP(totp_secret)
    totp_code = totp.now()
    
    print(f"Generated TOTP code: {totp_code}")
    
    login_data = {
        "email": "admin@videosplitter.com",
        "password": "AdminPass123!",
        "code": totp_code
    }
    
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json=login_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Login status: {response.status_code}")
    try:
        data = response.json()
        print(f"Login response: {json.dumps(data, indent=2)}")
    except:
        print(f"Login response: {response.text}")

if __name__ == "__main__":
    debug_2fa_login()