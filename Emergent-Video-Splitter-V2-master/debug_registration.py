#!/usr/bin/env python3
"""
Debug Registration Response
"""

import requests
import json
import time

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def debug_registration():
    test_user_data = {
        "email": f"debug-user-{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "firstName": "Debug",
        "lastName": "User",
        "confirmPassword": "TestPassword123!"
    }
    
    print(f"Creating user: {test_user_data['email']}")
    
    response = requests.post(
        f"{API_BASE}/api/auth/register",
        json=test_user_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Registration status: {response.status_code}")
    try:
        data = response.json()
        print(f"Registration response: {json.dumps(data, indent=2)}")
    except:
        print(f"Registration response: {response.text}")

if __name__ == "__main__":
    debug_registration()