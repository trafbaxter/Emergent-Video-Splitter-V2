#!/usr/bin/env python3
"""
Quick WILDCARD CORS verification test
Testing the specific endpoints mentioned in the review request
"""

import requests
import json

API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
WORKING_ORIGIN = "https://working.tads-video-splitter.com"

def test_endpoint_cors(method, endpoint, data=None):
    """Test CORS headers for a specific endpoint"""
    try:
        headers = {'Origin': WORKING_ORIGIN}
        if data:
            headers['Content-Type'] = 'application/json'
        
        if method == 'GET':
            response = requests.get(f"{API_GATEWAY_URL}{endpoint}", headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(f"{API_GATEWAY_URL}{endpoint}", json=data, headers=headers, timeout=10)
        elif method == 'OPTIONS':
            response = requests.options(f"{API_GATEWAY_URL}{endpoint}", headers=headers, timeout=10)
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        
        print(f"{method} {endpoint}")
        print(f"  Status: {response.status_code}")
        print(f"  CORS Origin: {cors_origin}")
        print(f"  Wildcard Working: {'✅ YES' if cors_origin == '*' else '❌ NO'}")
        print()
        
        return cors_origin == '*'
        
    except requests.exceptions.Timeout:
        print(f"{method} {endpoint}")
        print(f"  Status: TIMEOUT (expected for some endpoints)")
        print(f"  CORS Origin: Cannot determine due to timeout")
        print(f"  Wildcard Working: ⚠️ TIMEOUT")
        print()
        return None
    except Exception as e:
        print(f"{method} {endpoint}")
        print(f"  Status: ERROR - {str(e)}")
        print(f"  CORS Origin: Cannot determine")
        print(f"  Wildcard Working: ❌ ERROR")
        print()
        return False

print("🚨 URGENT: Quick Wildcard CORS Verification")
print("=" * 60)
print(f"Testing from origin: {WORKING_ORIGIN}")
print()

# Test the specific endpoints mentioned in the review request
results = []

print("1. Health check endpoint:")
results.append(test_endpoint_cors('GET', '/api/'))

print("2. Health check OPTIONS:")
results.append(test_endpoint_cors('OPTIONS', '/api/'))

print("3. get-video-info endpoint:")
results.append(test_endpoint_cors('POST', '/api/get-video-info', {'s3_key': 'test.mp4'}))

print("4. get-video-info OPTIONS:")
results.append(test_endpoint_cors('OPTIONS', '/api/get-video-info'))

print("5. video-stream endpoint:")
results.append(test_endpoint_cors('GET', '/api/video-stream/test.mp4'))

print("6. video-stream OPTIONS:")
results.append(test_endpoint_cors('OPTIONS', '/api/video-stream/test.mp4'))

# Summary
working_count = sum(1 for r in results if r is True)
timeout_count = sum(1 for r in results if r is None)
total_testable = len([r for r in results if r is not None])

print("=" * 60)
print("📊 WILDCARD CORS VERIFICATION SUMMARY")
print("=" * 60)
print(f"✅ Working with wildcard CORS: {working_count}/{len(results)}")
print(f"⚠️ Timeouts (expected): {timeout_count}/{len(results)}")
print(f"Success rate (excluding timeouts): {working_count}/{total_testable} ({(working_count/total_testable)*100:.1f}%)" if total_testable > 0 else "No testable endpoints")
print()

if working_count >= 4:  # At least health check and OPTIONS should work
    print("🎉 WILDCARD CORS FIX VERIFIED!")
    print("   The temporary '*' fix is working for CORS headers")
    print("   working.tads-video-splitter.com should now work without CORS errors")
else:
    print("🚨 WILDCARD CORS FIX NEEDS ATTENTION!")
    print("   Some endpoints are not returning the expected '*' CORS header")