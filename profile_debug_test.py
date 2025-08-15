#!/usr/bin/env python3
"""
Profile Endpoint Debug Test
Debug the profile endpoint to understand the response structure
"""

import requests
import json

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

def debug_profile_endpoint():
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
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        
        print("🔐 Login successful, testing profile endpoint...")
        print(f"Login response: {json.dumps(data, indent=2)}")
        print()
        
        # Test profile endpoint
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        profile_response = requests.get(
            f"{API_BASE}/api/user/profile",
            headers=headers,
            timeout=10
        )
        
        print(f"Profile endpoint status: {profile_response.status_code}")
        print(f"Profile response: {json.dumps(profile_response.json(), indent=2)}")
        
    else:
        print(f"Login failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_profile_endpoint()