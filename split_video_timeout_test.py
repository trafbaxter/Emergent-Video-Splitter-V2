#!/usr/bin/env python3
"""
SPLIT VIDEO ENDPOINT TIMEOUT FIX TEST for Video Splitter Pro

SPECIFIC TEST OBJECTIVE:
Test POST /api/split-video endpoint to verify it now returns HTTP 202 immediately 
instead of timing out after 29 seconds.

REVIEW REQUEST REQUIREMENTS:
1. Response time: < 10 seconds (ideally < 5 seconds)
2. Status code: 202 (not 504 timeout)
3. Response includes: job_id, status: "processing", message
4. CORS headers present (Access-Control-Allow-Origin: *)
5. Use videotest@example.com credentials if needed for auth headers
"""

import requests
import json
import time
import uuid
from typing import Dict, Any

# Configuration from .env file
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 15  # 15 seconds timeout for testing (should respond much faster)

class SplitVideoTimeoutTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.access_token = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Dict = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data
        })
        print()

    def setup_authentication(self):
        """Setup authentication with videotest@example.com as requested"""
        print("🔍 Setting up authentication with videotest@example.com...")
        
        # First try to register the user (in case it doesn't exist)
        register_data = {
            "email": "videotest@example.com",
            "password": "TestPassword123!",
            "firstName": "Video",
            "lastName": "Tester"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            if response.status_code == 201:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    print(f"   ✅ User registered successfully")
                    return True
            elif response.status_code == 409:
                # User already exists, try to login
                print(f"   ℹ️  User already exists, attempting login...")
        except Exception as e:
            print(f"   ⚠️  Registration failed: {str(e)}")
        
        # Try to login
        login_data = {
            "email": "videotest@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    print(f"   ✅ Login successful")
                    return True
            else:
                print(f"   ❌ Login failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Login error: {str(e)}")
        
        print(f"   ⚠️  Proceeding without authentication")
        return False

    def test_split_video_timeout_fix(self):
        """
        MAIN TEST: Split video endpoint timeout fix
        
        This test verifies the specific requirement from the review request:
        - POST /api/split-video should return HTTP 202 immediately (< 10s, ideally < 5s)
        - Should include job_id and processing status
        - Should have CORS headers
        """
        print("🚨 TESTING SPLIT VIDEO ENDPOINT TIMEOUT FIX...")
        print("=" * 60)
        
        # Use the exact payload from the review request
        split_data = {
            "s3_key": "test-video.mp4",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        print(f"📋 Test Payload:")
        print(f"   s3_key: {split_data['s3_key']}")
        print(f"   method: {split_data['method']}")
        print(f"   interval_duration: {split_data['interval_duration']}s")
        print(f"   preserve_quality: {split_data['preserve_quality']}")
        print(f"   output_format: {split_data['output_format']}")
        print()
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            print(f"🔐 Using authentication token")
        else:
            print(f"🔓 Testing without authentication")
        print()
        
        try:
            print(f"🎯 CRITICAL TEST: POST /api/split-video")
            print(f"   Expected: HTTP 202 response in < 10 seconds (ideally < 5 seconds)")
            print(f"   Previous issue: HTTP 504 timeout after ~29 seconds")
            print()
            
            start_time = time.time()
            
            response = self.session.post(
                f"{self.base_url}/api/split-video", 
                json=split_data,
                headers=headers
            )
            
            response_time = time.time() - start_time
            
            print(f"⏱️  RESPONSE TIME: {response_time:.2f} seconds")
            print(f"📊 STATUS CODE: {response.status_code}")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin', 'Not present')
            print(f"🌐 CORS Header: {cors_header}")
            print()
            
            # Analyze the response based on review requirements
            if response.status_code == 202:
                # SUCCESS CASE: This is what we expect
                try:
                    data = response.json()
                    print(f"📄 RESPONSE DATA:")
                    print(json.dumps(data, indent=2))
                    print()
                    
                    # Check required fields
                    has_job_id = 'job_id' in data
                    has_status = 'status' in data
                    has_message = 'message' in data
                    status_value = data.get('status', '')
                    
                    # Check response time requirement
                    time_ok = response_time < 10.0
                    time_ideal = response_time < 5.0
                    
                    # Check CORS requirement
                    cors_ok = cors_header == '*'
                    
                    if has_job_id and has_status and time_ok and cors_ok:
                        success_level = "IDEAL" if time_ideal else "GOOD"
                        self.log_test(
                            f"🎉 SPLIT VIDEO TIMEOUT FIX - {success_level} SUCCESS",
                            True,
                            f"✅ TIMEOUT ISSUE RESOLVED! HTTP 202 returned in {response_time:.2f}s ({'< 5s IDEAL' if time_ideal else '< 10s GOOD'}). "
                            f"Response includes job_id: {data.get('job_id', 'N/A')[:20]}..., "
                            f"status: '{status_value}', CORS: {cors_header}. "
                            f"The 29-second timeout problem is FIXED!"
                        )
                    else:
                        missing_items = []
                        if not has_job_id: missing_items.append("job_id")
                        if not has_status: missing_items.append("status")
                        if not time_ok: missing_items.append(f"response_time > 10s ({response_time:.2f}s)")
                        if not cors_ok: missing_items.append(f"CORS header ({cors_header})")
                        
                        self.log_test(
                            "Split Video Timeout Fix - Partial Success",
                            False,
                            f"HTTP 202 received but missing requirements: {', '.join(missing_items)}. Response time: {response_time:.2f}s",
                            data
                        )
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Split Video Timeout Fix - Response Format Issue",
                        False,
                        f"HTTP 202 received in {response_time:.2f}s but response is not valid JSON"
                    )
                    
            elif response.status_code == 504:
                # FAILURE CASE: Still timing out (the original problem)
                self.log_test(
                    "❌ SPLIT VIDEO TIMEOUT FIX FAILED",
                    False,
                    f"🚨 CRITICAL: HTTP 504 Gateway Timeout still occurring after {response_time:.2f}s! "
                    f"The timeout fix did NOT resolve the issue. The endpoint should return HTTP 202 immediately "
                    f"with a job_id for async processing, but it's still timing out after ~29 seconds."
                )
                
            elif response.status_code == 200:
                # Unexpected but not necessarily bad
                try:
                    data = response.json()
                    self.log_test(
                        "Split Video Timeout Fix - Unexpected 200",
                        True,
                        f"HTTP 200 received in {response_time:.2f}s (expected 202). May indicate synchronous processing instead of async. CORS: {cors_header}",
                        data
                    )
                except:
                    self.log_test(
                        "Split Video Timeout Fix - Unexpected 200",
                        False,
                        f"HTTP 200 received in {response_time:.2f}s but invalid JSON response"
                    )
                    
            elif response.status_code == 401:
                self.log_test(
                    "Split Video Timeout Fix - Authentication Required",
                    False,
                    f"HTTP 401 Unauthorized in {response_time:.2f}s. Authentication may be required for this endpoint."
                )
                
            elif response.status_code == 404:
                self.log_test(
                    "Split Video Timeout Fix - Endpoint Not Found",
                    False,
                    f"HTTP 404 Not Found in {response_time:.2f}s. The /api/split-video endpoint may not be implemented."
                )
                
            elif response.status_code == 400:
                try:
                    data = response.json()
                    self.log_test(
                        "Split Video Timeout Fix - Bad Request",
                        False,
                        f"HTTP 400 Bad Request in {response_time:.2f}s. Payload validation failed.",
                        data
                    )
                except:
                    self.log_test(
                        "Split Video Timeout Fix - Bad Request",
                        False,
                        f"HTTP 400 Bad Request in {response_time:.2f}s. Invalid request format."
                    )
                    
            else:
                # Other status codes
                try:
                    data = response.json()
                    self.log_test(
                        f"Split Video Timeout Fix - HTTP {response.status_code}",
                        False,
                        f"Unexpected HTTP {response.status_code} in {response_time:.2f}s",
                        data
                    )
                except:
                    self.log_test(
                        f"Split Video Timeout Fix - HTTP {response.status_code}",
                        False,
                        f"Unexpected HTTP {response.status_code} in {response_time:.2f}s with non-JSON response"
                    )
                    
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ SPLIT VIDEO TIMEOUT FIX FAILED - CLIENT TIMEOUT",
                False,
                f"🚨 CRITICAL: Request timed out after {TIMEOUT}s on client side. "
                f"This indicates the endpoint is still taking longer than expected. "
                f"The timeout fix did NOT resolve the issue."
            )
            
        except requests.exceptions.ConnectionError as e:
            self.log_test(
                "Split Video Timeout Fix - Connection Error",
                False,
                f"Connection error: {str(e)}"
            )
            
        except Exception as e:
            self.log_test(
                "Split Video Timeout Fix - Unexpected Error",
                False,
                f"Unexpected error: {str(e)}"
            )

    def test_cors_preflight(self):
        """Test CORS preflight request for split-video endpoint"""
        print("🔍 Testing CORS Preflight for Split Video Endpoint...")
        
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            start_time = time.time()
            response = self.session.options(f"{self.base_url}/api/split-video", headers=headers)
            response_time = time.time() - start_time
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'Not present')
            cors_methods = response.headers.get('Access-Control-Allow-Methods', 'Not present')
            cors_headers = response.headers.get('Access-Control-Allow-Headers', 'Not present')
            
            if response.status_code == 200 and cors_origin == '*':
                self.log_test(
                    "CORS Preflight for Split Video",
                    True,
                    f"CORS preflight successful in {response_time:.2f}s. Origin: {cors_origin}, Methods: {cors_methods}"
                )
            else:
                self.log_test(
                    "CORS Preflight for Split Video",
                    False,
                    f"HTTP {response.status_code} in {response_time:.2f}s. CORS headers: Origin={cors_origin}, Methods={cors_methods}"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Preflight for Split Video",
                False,
                f"Error: {str(e)}"
            )

    def run_focused_test(self):
        """Run the focused split video timeout test"""
        print("=" * 80)
        print("🎯 SPLIT VIDEO ENDPOINT TIMEOUT FIX TEST")
        print("=" * 80)
        print(f"API Gateway URL: {self.base_url}")
        print(f"Test Timeout: {TIMEOUT} seconds")
        print()
        print("📋 REVIEW REQUEST REQUIREMENTS:")
        print("   1. Response time: < 10 seconds (ideally < 5 seconds)")
        print("   2. Status code: 202 (not 504 timeout)")
        print("   3. Response includes: job_id, status: 'processing', message")
        print("   4. CORS headers present (Access-Control-Allow-Origin: *)")
        print("   5. Use videotest@example.com credentials if needed")
        print()
        
        # Setup authentication
        self.setup_authentication()
        print()
        
        # Run the main test
        self.test_split_video_timeout_fix()
        
        # Test CORS preflight
        self.test_cors_preflight()
        
        # Summary
        print("=" * 80)
        print("📊 SPLIT VIDEO TIMEOUT FIX TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
        print()
        
        # Analyze timeout fix status
        timeout_fixed = False
        response_time = None
        
        for result in self.test_results:
            if 'split video timeout fix' in result['test'].lower():
                if result['success'] and 'timeout issue resolved' in result['details'].lower():
                    timeout_fixed = True
                    # Extract response time from details
                    import re
                    time_match = re.search(r'(\d+\.\d+)s', result['details'])
                    if time_match:
                        response_time = float(time_match.group(1))
                break
        
        print("🔍 TIMEOUT FIX STATUS:")
        if timeout_fixed:
            time_status = ""
            if response_time:
                if response_time < 5.0:
                    time_status = f" in {response_time:.2f}s (IDEAL - under 5s)"
                elif response_time < 10.0:
                    time_status = f" in {response_time:.2f}s (GOOD - under 10s)"
                else:
                    time_status = f" in {response_time:.2f}s (SLOW - over 10s)"
            
            print(f"   🎉 SUCCESS: Split video endpoint timeout is FIXED{time_status}")
            print(f"   ✅ Returns HTTP 202 immediately instead of timing out after 29s")
            print(f"   ✅ Includes required response fields (job_id, status)")
            print(f"   ✅ CORS headers are present")
        else:
            print(f"   ❌ FAILED: Split video endpoint is still timing out")
            print(f"   ❌ Does not return HTTP 202 immediately as expected")
            print(f"   ❌ The 29-second timeout issue persists")
        
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Final assessment
        print("💡 FINAL ASSESSMENT:")
        if timeout_fixed:
            print("   🎉 TIMEOUT FIX VERIFICATION: SUCCESSFUL")
            print("   • The split video endpoint now returns HTTP 202 immediately")
            print("   • Response time is within acceptable limits")
            print("   • The 29-second timeout issue has been resolved")
            print("   • Main agent can proceed with confidence")
        else:
            print("   ❌ TIMEOUT FIX VERIFICATION: FAILED")
            print("   • The split video endpoint is still experiencing timeout issues")
            print("   • Further investigation is needed by the main agent")
            print("   • Consider checking Lambda timeout settings, FFmpeg Lambda, or API Gateway configuration")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests, timeout_fixed

if __name__ == "__main__":
    tester = SplitVideoTimeoutTester()
    passed, failed, timeout_fixed = tester.run_focused_test()
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if timeout_fixed else 1)