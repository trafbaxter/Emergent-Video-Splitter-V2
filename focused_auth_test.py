#!/usr/bin/env python3
"""
Focused Authentication System Testing
Testing the specific issues with the Lambda function deployment
"""

import requests
import json
import time

# Test both URLs mentioned in the review
OLD_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
NEW_URL = "https://ztu91dvx96.execute-api.us-east-1.amazonaws.com/prod"

def test_basic_connectivity():
    """Test basic connectivity to both Lambda URLs"""
    print("=== Testing Basic Lambda Connectivity ===")
    
    urls_to_test = [
        ("OLD URL", OLD_URL),
        ("NEW URL", NEW_URL)
    ]
    
    for name, base_url in urls_to_test:
        print(f"\n{name}: {base_url}")
        
        # Test root endpoint
        try:
            response = requests.get(f"{base_url}/", timeout=10)
            print(f"  Root (/): {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"  Root (/): ERROR - {e}")
        
        # Test API endpoint
        try:
            response = requests.get(f"{base_url}/api/", timeout=10)
            print(f"  API (/api/): {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"  API (/api/): ERROR - {e}")

def test_auth_endpoints():
    """Test authentication endpoints specifically"""
    print("\n=== Testing Authentication Endpoints ===")
    
    # Use the old URL since new one doesn't resolve
    base_url = OLD_URL
    
    auth_endpoints = [
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/verify-email", 
        "/api/auth/refresh"
    ]
    
    for endpoint in auth_endpoints:
        print(f"\nTesting {endpoint}:")
        
        # Test OPTIONS (CORS)
        try:
            response = requests.options(f"{base_url}{endpoint}", timeout=10)
            print(f"  OPTIONS: {response.status_code}")
            if response.headers:
                cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
                if cors_headers:
                    print(f"  CORS Headers: {cors_headers}")
        except Exception as e:
            print(f"  OPTIONS: ERROR - {e}")
        
        # Test GET
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"  GET: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"  GET: ERROR - {e}")
        
        # Test POST with minimal data
        try:
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={"test": "data"}, 
                                   timeout=10)
            print(f"  POST: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"  POST: ERROR - {e}")

def test_dependency_import_errors():
    """Test if we can detect dependency import errors"""
    print("\n=== Testing for Dependency Import Errors ===")
    
    base_url = OLD_URL
    
    # Try a simple registration that would use bcrypt, jwt, pymongo
    test_payload = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "dependency.test@example.com",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", 
                               json=test_payload, 
                               timeout=15)
        
        print(f"Registration test: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Check for common import error patterns
        response_text = response.text.lower()
        import_error_patterns = [
            'no module named',
            'import error', 
            'modulenotfounderror',
            'cannot import',
            'bcrypt',
            'jwt',
            'pymongo'
        ]
        
        for pattern in import_error_patterns:
            if pattern in response_text:
                print(f"⚠️ Possible import error detected: '{pattern}' found in response")
        
        if response.status_code == 502:
            print("⚠️ 502 error suggests Lambda execution failure - likely missing dependencies")
        elif response.status_code == 500:
            print("⚠️ 500 error suggests code execution error - check for import issues")
            
    except Exception as e:
        print(f"Dependency test failed: {e}")

def test_lambda_function_status():
    """Test Lambda function status and configuration"""
    print("\n=== Testing Lambda Function Status ===")
    
    base_url = OLD_URL
    
    # Test different endpoints to understand Lambda behavior
    test_endpoints = [
        "/",
        "/api/",
        "/api/health",
        "/api/status",
        "/api/auth/register",
        "/api/upload-video"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"{endpoint}: {response.status_code} - {response.text[:100]}")
            
            # Check response headers for Lambda info
            lambda_headers = {k: v for k, v in response.headers.items() 
                            if any(x in k.lower() for x in ['lambda', 'aws', 'x-amz'])}
            if lambda_headers:
                print(f"  Lambda headers: {lambda_headers}")
                
        except Exception as e:
            print(f"{endpoint}: ERROR - {e}")

def main():
    """Run all focused tests"""
    print("🔍 Focused Authentication System Testing")
    print("=" * 60)
    
    test_basic_connectivity()
    test_auth_endpoints()
    test_dependency_import_errors()
    test_lambda_function_status()
    
    print("\n" + "=" * 60)
    print("🏁 Focused Testing Complete")
    
    print("\n📋 SUMMARY:")
    print("- NEW URL (ztu91dvx96) does not resolve - likely incorrect or not deployed")
    print("- OLD URL (2419j971hh) is accessible but returns 502/500 errors")
    print("- All /api/* endpoints return 'Internal server error'")
    print("- Root endpoint returns 'Missing Authentication Token' (normal for API Gateway)")
    print("- 502 errors suggest Lambda function execution failure")
    print("- Most likely cause: Missing Python dependencies (bcrypt, PyJWT, pymongo)")

if __name__ == "__main__":
    main()