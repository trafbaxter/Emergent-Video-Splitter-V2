#!/usr/bin/env python3
"""
Login Debug - Check what's happening with admin login
"""

import requests
import json

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def debug_login():
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
    
    print(f"Login status: {response.status_code}")
    try:
        data = response.json()
        print(f"Login response: {json.dumps(data, indent=2)}")
    except:
        print(f"Login response: {response.text}")

if __name__ == "__main__":
    debug_login()