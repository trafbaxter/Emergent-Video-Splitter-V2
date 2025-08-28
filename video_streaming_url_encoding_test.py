#!/usr/bin/env python3
"""
VIDEO STREAMING URL ENCODING TEST for Video Splitter Pro
Testing the updated video streaming architecture with proper URL encoding fixes.

CRITICAL TEST FOCUS:
Test the video streaming endpoint with both S3 keys and proper URL encoding handling 
to resolve the double encoding issue identified in console logs.

SPECIFIC TESTS:
1. S3 Key Video Streaming Test with actual MKV file S3 key
2. URL Encoding Handling Test 
3. Job ID Support Test

EXPECTED RESULTS:
- S3 keys work with proper single URL encoding
- Generated presigned URLs don't have double encoding (%20 not %2520)
- Job IDs return helpful error message
- All responses have proper CORS headers
- Response time under 5 seconds
"""

import requests
import json
import time
import urllib.parse
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 10  # 10 second timeout for fast response requirement

# Test S3 key from review request
TEST_S3_KEY = "uploads/3edba1d9-b854-45b0-a7d4-54a88940f38b/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"

class VideoStreamingTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.access_token = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Dict = None, response_time: float = None):
        """Log test results with response time"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data,
            'response_time': response_time
        })
        print()

    def register_test_user(self):
        """Register a test user for authentication"""
        print("🔐 Setting up test user authentication...")
        
        # Generate unique test user
        test_id = str(int(time.time()))
        test_user = {
            "email": f"videotest{test_id}@example.com",
            "password": "TestPass123!",
            "name": "Video Test User"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user,
                headers={'Content-Type': 'application/json'}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.log_test(
                        "User Registration for Testing", 
                        True, 
                        f"User registered successfully with email: {test_user['email']}", 
                        response_time=response_time
                    )
                    return True
                else:
                    self.log_test("User Registration for Testing", False, "No access token in response", data, response_time)
            else:
                self.log_test("User Registration for Testing", False, f"HTTP {response.status_code}", response.json() if response.content else {}, response_time)
                
        except Exception as e:
            self.log_test("User Registration for Testing", False, f"Exception: {str(e)}")
            
        return False

    def test_s3_key_video_streaming(self):
        """Test 1: S3 Key Video Streaming Test with actual MKV file S3 key"""
        print("🎥 Testing S3 Key Video Streaming...")
        
        if not self.access_token:
            self.log_test("S3 Key Video Streaming", False, "No access token available")
            return
            
        try:
            # Test with the actual S3 key from review request
            s3_key = TEST_S3_KEY
            
            # URL encode the S3 key for the path parameter
            encoded_key = urllib.parse.quote(s3_key, safe='')
            
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/video-stream/{encoded_key}",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['stream_url', 's3_key', 'expires_in']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check for double encoding issue in stream_url
                    stream_url = data.get('stream_url', '')
                    has_double_encoding = '%2520' in stream_url  # Double encoded space
                    
                    # Check CORS headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin', '')
                    has_cors = cors_header in ['*', 'https://working.tads-video-splitter.com']
                    
                    # Check response time requirement (under 5 seconds)
                    fast_response = response_time < 5.0
                    
                    success = not has_double_encoding and has_cors and fast_response
                    
                    details = f"Response format complete. CORS: {cors_header}. "
                    if has_double_encoding:
                        details += "❌ DOUBLE ENCODING DETECTED (%2520 found in URL). "
                    else:
                        details += "✅ Single URL encoding (no %2520). "
                    
                    if not fast_response:
                        details += f"❌ Slow response ({response_time:.2f}s > 5s). "
                    else:
                        details += f"✅ Fast response ({response_time:.2f}s < 5s). "
                        
                    self.log_test(
                        "S3 Key Video Streaming", 
                        success, 
                        details,
                        response_time=response_time
                    )
                    
                    # Additional test: Check if the generated S3 URL is accessible
                    if 'stream_url' in data:
                        self.test_s3_url_accessibility(data['stream_url'])
                        
                else:
                    self.log_test(
                        "S3 Key Video Streaming", 
                        False, 
                        f"Missing required fields: {missing_fields}",
                        data,
                        response_time
                    )
            else:
                self.log_test(
                    "S3 Key Video Streaming", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.json() if response.content else {},
                    response_time
                )
                
        except Exception as e:
            self.log_test("S3 Key Video Streaming", False, f"Exception: {str(e)}")

    def test_url_encoding_handling(self):
        """Test 2: URL Encoding Handling Test"""
        print("🔗 Testing URL Encoding Handling...")
        
        if not self.access_token:
            self.log_test("URL Encoding Handling", False, "No access token available")
            return
            
        try:
            # Test with URL-encoded S3 key (as it would come from frontend)
            s3_key = TEST_S3_KEY
            
            # Double encode to simulate frontend URL encoding
            double_encoded_key = urllib.parse.quote(urllib.parse.quote(s3_key, safe=''), safe='')
            
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/video-stream/{double_encoded_key}",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if backend properly handled URL decoding
                returned_s3_key = data.get('s3_key', '')
                properly_decoded = returned_s3_key == s3_key
                
                # Check for double encoding in generated URL
                stream_url = data.get('stream_url', '')
                no_double_encoding = '%2520' not in stream_url
                
                success = properly_decoded and no_double_encoding
                
                details = f"Backend URL decoding: {'✅ Correct' if properly_decoded else '❌ Failed'}. "
                details += f"Generated URL encoding: {'✅ Single' if no_double_encoding else '❌ Double'}. "
                
                self.log_test(
                    "URL Encoding Handling", 
                    success, 
                    details,
                    response_time=response_time
                )
            else:
                self.log_test(
                    "URL Encoding Handling", 
                    False, 
                    f"HTTP {response.status_code}",
                    response.json() if response.content else {},
                    response_time
                )
                
        except Exception as e:
            self.log_test("URL Encoding Handling", False, f"Exception: {str(e)}")

    def test_job_id_support(self):
        """Test 3: Job ID Support Test"""
        print("🆔 Testing Job ID Support...")
        
        if not self.access_token:
            self.log_test("Job ID Support", False, "No access token available")
            return
            
        try:
            # Test with a job ID format
            job_id = "job-test-123"
            
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/video-stream/{job_id}",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                }
            )
            response_time = time.time() - start_time
            
            # Should return helpful error message for job IDs
            if response.status_code in [400, 404, 501]:
                data = response.json() if response.content else {}
                
                # Check for helpful error message
                error_message = data.get('message', '').lower()
                helpful_message = any(keyword in error_message for keyword in ['job', 'mapping', 'not implemented', 'not found'])
                
                # Check CORS headers are present even on error
                cors_header = response.headers.get('Access-Control-Allow-Origin', '')
                has_cors = cors_header in ['*', 'https://working.tads-video-splitter.com']
                
                success = helpful_message and has_cors
                
                details = f"Error message: {'✅ Helpful' if helpful_message else '❌ Generic'}. "
                details += f"CORS headers: {'✅ Present' if has_cors else '❌ Missing'}. "
                details += f"Message: '{data.get('message', 'No message')}'"
                
                self.log_test(
                    "Job ID Support", 
                    success, 
                    details,
                    response_time=response_time
                )
            else:
                self.log_test(
                    "Job ID Support", 
                    False, 
                    f"Unexpected HTTP {response.status_code} (expected 400/404/501)",
                    response.json() if response.content else {},
                    response_time
                )
                
        except Exception as e:
            self.log_test("Job ID Support", False, f"Exception: {str(e)}")

    def test_s3_url_accessibility(self, s3_url: str):
        """Test S3 URL accessibility (separate from main tests)"""
        print("🔗 Testing S3 URL Accessibility...")
        
        try:
            # Test direct access to S3 URL
            start_time = time.time()
            response = self.session.head(s3_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check CORS headers from S3
                cors_header = response.headers.get('Access-Control-Allow-Origin', 'None')
                content_type = response.headers.get('Content-Type', 'unknown')
                
                details = f"S3 CORS: {cors_header}, Content-Type: {content_type}"
                
                self.log_test(
                    "S3 URL Direct Access", 
                    True, 
                    details,
                    response_time=response_time
                )
            elif response.status_code == 403:
                self.log_test(
                    "S3 URL Direct Access", 
                    False, 
                    "HTTP 403 Forbidden - S3 permissions or CORS issue",
                    response_time=response_time
                )
            elif response.status_code == 404:
                self.log_test(
                    "S3 URL Direct Access", 
                    False, 
                    "HTTP 404 Not Found - File doesn't exist in S3",
                    response_time=response_time
                )
            else:
                self.log_test(
                    "S3 URL Direct Access", 
                    False, 
                    f"HTTP {response.status_code}",
                    response_time=response_time
                )
                
        except Exception as e:
            self.log_test("S3 URL Direct Access", False, f"Exception: {str(e)}")

    def test_cors_preflight(self):
        """Test CORS preflight requests"""
        print("🌐 Testing CORS Preflight...")
        
        try:
            start_time = time.time()
            response = self.session.options(
                f"{self.base_url}/api/video-stream/test",
                headers={
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Authorization'
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
                cors_methods = response.headers.get('Access-Control-Allow-Methods', '')
                cors_headers = response.headers.get('Access-Control-Allow-Headers', '')
                
                has_origin = cors_origin in ['*', 'https://working.tads-video-splitter.com']
                has_methods = 'GET' in cors_methods
                has_headers = 'Authorization' in cors_headers or 'authorization' in cors_headers.lower()
                
                success = has_origin and has_methods and has_headers
                
                details = f"Origin: {cors_origin}, Methods: {cors_methods}, Headers: {cors_headers}"
                
                self.log_test(
                    "CORS Preflight", 
                    success, 
                    details,
                    response_time=response_time
                )
            else:
                self.log_test(
                    "CORS Preflight", 
                    False, 
                    f"HTTP {response.status_code}",
                    response_time=response_time
                )
                
        except Exception as e:
            self.log_test("CORS Preflight", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all video streaming URL encoding tests"""
        print("🚀 Starting Video Streaming URL Encoding Tests")
        print("=" * 60)
        
        # Setup authentication
        if not self.register_test_user():
            print("❌ Cannot proceed without authentication")
            return
            
        print("🎯 Running Core Video Streaming Tests...")
        print("-" * 40)
        
        # Core tests from review request
        self.test_s3_key_video_streaming()
        self.test_url_encoding_handling() 
        self.test_job_id_support()
        
        # Additional supporting tests
        self.test_cors_preflight()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        # Critical issues
        critical_failures = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['test'] for keyword in ['S3 Key Video Streaming', 'URL Encoding Handling']):
                critical_failures.append(result['test'])
                
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   - {failure}")
        
        # Performance summary
        fast_responses = sum(1 for result in self.test_results if result.get('response_time', 0) < 5.0 and result.get('response_time', 0) > 0)
        timed_tests = sum(1 for result in self.test_results if result.get('response_time', 0) > 0)
        
        if timed_tests > 0:
            print(f"\n⚡ PERFORMANCE: {fast_responses}/{timed_tests} responses under 5s")
            
        # URL encoding specific results
        encoding_issues = []
        for result in self.test_results:
            if 'double encoding' in result.get('details', '').lower() or '%2520' in result.get('details', ''):
                encoding_issues.append(result['test'])
                
        if encoding_issues:
            print(f"\n🔗 URL ENCODING ISSUES DETECTED:")
            for issue in encoding_issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ URL ENCODING: No double encoding issues detected")

if __name__ == "__main__":
    tester = VideoStreamingTester()
    tester.run_all_tests()