#!/usr/bin/env python3
"""
Simple Authentication Test to diagnose Lambda function issues
"""

import requests
import json

# Configuration
BACKEND_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"

def test_basic_connectivity():
    """Test basic Lambda connectivity"""
    print("🔍 Testing basic Lambda connectivity...")
    
    # Test different endpoints to see what works
    endpoints_to_test = [
        "",
        "/",
        "/api",
        "/api/",
        "/api/auth/register",
        "/api/auth/login",
        "/api/video-info/test",
        "/api/upload"
    ]
    
    for endpoint in endpoints_to_test:
        url = f"{BACKEND_URL}{endpoint}"
        try:
            print(f"\n📡 Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

def test_auth_endpoints():
    """Test authentication endpoints specifically"""
    print("\n🔍 Testing authentication endpoints...")
    
    # Test POST to auth endpoints
    auth_endpoints = [
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh"
    ]
    
    test_data = {
        "email": "test@example.com",
        "password": "TestPass123!",
        "firstName": "Test",
        "lastName": "User"
    }
    
    for endpoint in auth_endpoints:
        url = f"{BACKEND_URL}{endpoint}"
        try:
            print(f"\n📡 POST {url}")
            response = requests.post(url, json=test_data, timeout=10)
            print(f"   Status: {response.status_code}")
            
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

def test_options_requests():
    """Test CORS preflight requests"""
    print("\n🔍 Testing CORS preflight requests...")
    
    endpoints = ["/api/auth/register", "/api/auth/login"]
    
    for endpoint in endpoints:
        url = f"{BACKEND_URL}{endpoint}"
        try:
            print(f"\n📡 OPTIONS {url}")
            response = requests.options(url, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
        except Exception as e:
            print(f"   Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Simple Authentication Test")
    print(f"Backend URL: {BACKEND_URL}")
    
    test_basic_connectivity()
    test_auth_endpoints()
    test_options_requests()
    
    print("\n✅ Test completed!")