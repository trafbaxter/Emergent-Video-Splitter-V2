#!/usr/bin/env python3
"""
FOCUSED URL ENCODING DEBUG TEST
Debug the specific URL encoding issue identified in the main test.
"""

import requests
import json
import time
import urllib.parse

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TEST_S3_KEY = "uploads/3edba1d9-b854-45b0-a7d4-54a88940f38b/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"

def register_user():
    """Quick user registration"""
    test_id = str(int(time.time()))
    test_user = {
        "email": f"debugtest{test_id}@example.com",
        "password": "TestPass123!",
        "name": "Debug Test User"
    }
    
    response = requests.post(
        f"{API_GATEWAY_URL}/api/auth/register",
        json=test_user,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code == 201:
        return response.json().get('access_token')
    return None

def test_encoding_scenarios(access_token):
    """Test different encoding scenarios"""
    
    print("🔍 DEBUGGING URL ENCODING SCENARIOS")
    print("=" * 50)
    
    scenarios = [
        ("Original S3 Key", TEST_S3_KEY),
        ("Single URL Encoded", urllib.parse.quote(TEST_S3_KEY, safe='')),
        ("Double URL Encoded", urllib.parse.quote(urllib.parse.quote(TEST_S3_KEY, safe=''), safe='')),
        ("Path Safe Encoded", urllib.parse.quote(TEST_S3_KEY, safe='/')),
    ]
    
    for scenario_name, encoded_key in scenarios:
        print(f"\n📝 Testing: {scenario_name}")
        print(f"   Input Key: {encoded_key[:80]}...")
        
        try:
            response = requests.get(
                f"{API_GATEWAY_URL}/api/video-stream/{encoded_key}",
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                returned_key = data.get('s3_key', '')
                stream_url = data.get('stream_url', '')
                
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📤 Returned S3 Key: {returned_key[:80]}...")
                print(f"   🔗 Stream URL: {stream_url[:100]}...")
                
                # Check for encoding issues
                if '%2520' in stream_url:
                    print(f"   ❌ DOUBLE ENCODING DETECTED in stream URL")
                else:
                    print(f"   ✅ No double encoding in stream URL")
                    
                # Check if returned key matches original
                if returned_key == TEST_S3_KEY:
                    print(f"   ✅ Backend correctly decoded to original key")
                else:
                    print(f"   ❌ Backend decoding issue")
                    print(f"      Expected: {TEST_S3_KEY}")
                    print(f"      Got:      {returned_key}")
                    
            else:
                print(f"   ❌ Status: {response.status_code}")
                if response.content:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('message', 'No message')}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

if __name__ == "__main__":
    access_token = register_user()
    if access_token:
        test_encoding_scenarios(access_token)
    else:
        print("❌ Failed to get access token")