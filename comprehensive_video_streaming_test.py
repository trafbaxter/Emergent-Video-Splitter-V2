#!/usr/bin/env python3
"""
COMPREHENSIVE VIDEO STREAMING ARCHITECTURE TEST
Final comprehensive test of the video streaming endpoint with URL encoding fixes.

This test validates all requirements from the review request:
1. S3 Key Video Streaming Test with actual MKV file S3 key
2. URL Encoding Handling Test 
3. Job ID Support Test
4. Response format validation
5. CORS headers validation
6. Performance validation (under 5 seconds)
"""

import requests
import json
import time
import urllib.parse
from typing import Dict, Any

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TEST_S3_KEY = "uploads/3edba1d9-b854-45b0-a7d4-54a88940f38b/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"

class ComprehensiveVideoStreamingTest:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.access_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str, response_time: float = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time
        })
        print()

    def setup_authentication(self):
        """Setup test user authentication"""
        print("🔐 Setting up authentication...")
        
        test_id = str(int(time.time()))
        test_user = {
            "email": f"streamtest{test_id}@example.com",
            "password": "TestPass123!",
            "name": "Stream Test User"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=test_user,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get('access_token')
                self.log_result(
                    "Authentication Setup", 
                    True, 
                    f"User registered: {test_user['email']}", 
                    response_time
                )
                return True
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Exception: {str(e)}")
            return False

    def test_s3_key_streaming_proper_encoding(self):
        """Test S3 key streaming with proper URL encoding (CRITICAL TEST)"""
        print("🎥 Testing S3 Key Video Streaming with Proper URL Encoding...")
        
        # Use proper single URL encoding as identified in debug test
        encoded_key = urllib.parse.quote(TEST_S3_KEY, safe='')
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/video-stream/{encoded_key}",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response format
                required_fields = ['stream_url', 's3_key', 'expires_in']
                has_all_fields = all(field in data for field in required_fields)
                
                # Check URL encoding (no double encoding)
                stream_url = data.get('stream_url', '')
                no_double_encoding = '%2520' not in stream_url
                
                # Check CORS headers
                cors_header = response.headers.get('Access-Control-Allow-Origin', '')
                has_cors = cors_header == '*'
                
                # Check response time
                fast_response = response_time < 5.0
                
                # Check S3 key decoding
                returned_key = data.get('s3_key', '')
                correct_decoding = returned_key == TEST_S3_KEY
                
                success = has_all_fields and no_double_encoding and has_cors and fast_response and correct_decoding
                
                details = []
                details.append(f"Response format: {'✅ Complete' if has_all_fields else '❌ Missing fields'}")
                details.append(f"URL encoding: {'✅ Single' if no_double_encoding else '❌ Double (%2520 found)'}")
                details.append(f"CORS headers: {'✅ Present (*)' if has_cors else f'❌ Missing/Wrong ({cors_header})'}")
                details.append(f"Response time: {'✅ Fast' if fast_response else '❌ Slow'} ({response_time:.2f}s)")
                details.append(f"S3 key decoding: {'✅ Correct' if correct_decoding else '❌ Failed'}")
                
                self.log_result(
                    "S3 Key Video Streaming (Proper Encoding)", 
                    success, 
                    " | ".join(details), 
                    response_time
                )
                
                return success, data
                
            else:
                self.log_result(
                    "S3 Key Video Streaming (Proper Encoding)", 
                    False, 
                    f"HTTP {response.status_code}: {response.text[:100]}", 
                    response_time
                )
                return False, None
                
        except Exception as e:
            self.log_result("S3 Key Video Streaming (Proper Encoding)", False, f"Exception: {str(e)}")
            return False, None

    def test_job_id_error_handling(self):
        """Test job ID error handling"""
        print("🆔 Testing Job ID Error Handling...")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/video-stream/job-test-123",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            # Should return helpful error
            if response.status_code in [400, 404, 501]:
                data = response.json() if response.content else {}
                
                # Check error message
                error_message = data.get('message', '').lower()
                helpful_message = any(keyword in error_message for keyword in ['job', 'mapping', 'not implemented'])
                
                # Check CORS
                cors_header = response.headers.get('Access-Control-Allow-Origin', '')
                has_cors = cors_header == '*'
                
                success = helpful_message and has_cors
                
                details = f"Error message: {'✅ Helpful' if helpful_message else '❌ Generic'} | CORS: {'✅ Present' if has_cors else '❌ Missing'} | Message: '{data.get('message', 'None')}'"
                
                self.log_result("Job ID Error Handling", success, details, response_time)
                return success
                
            else:
                self.log_result(
                    "Job ID Error Handling", 
                    False, 
                    f"Unexpected HTTP {response.status_code} (expected 400/404/501)", 
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result("Job ID Error Handling", False, f"Exception: {str(e)}")
            return False

    def test_cors_preflight(self):
        """Test CORS preflight requests"""
        print("🌐 Testing CORS Preflight...")
        
        try:
            start_time = time.time()
            response = requests.options(
                f"{self.base_url}/api/video-stream/test-key",
                headers={
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Authorization'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 204]:
                cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
                cors_methods = response.headers.get('Access-Control-Allow-Methods', '')
                cors_headers = response.headers.get('Access-Control-Allow-Headers', '')
                
                has_origin = cors_origin == '*'
                has_methods = 'GET' in cors_methods.upper()
                has_auth_header = 'authorization' in cors_headers.lower()
                
                success = has_origin and has_methods and has_auth_header
                
                details = f"Origin: {'✅ *' if has_origin else f'❌ {cors_origin}'} | Methods: {'✅ GET' if has_methods else f'❌ {cors_methods}'} | Headers: {'✅ Auth' if has_auth_header else f'❌ {cors_headers}'}"
                
                self.log_result("CORS Preflight", success, details, response_time)
                return success
                
            else:
                self.log_result("CORS Preflight", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("CORS Preflight", False, f"Exception: {str(e)}")
            return False

    def test_s3_url_direct_access(self, stream_url: str):
        """Test direct S3 URL access"""
        print("🔗 Testing S3 URL Direct Access...")
        
        try:
            start_time = time.time()
            response = requests.head(stream_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                cors_header = response.headers.get('Access-Control-Allow-Origin', 'None')
                content_type = response.headers.get('Content-Type', 'unknown')
                
                # S3 CORS should allow the origin
                has_s3_cors = cors_header != 'None'
                
                details = f"S3 CORS: {'✅ Present' if has_s3_cors else '❌ Missing'} ({cors_header}) | Content-Type: {content_type}"
                
                self.log_result("S3 URL Direct Access", has_s3_cors, details, response_time)
                return has_s3_cors
                
            elif response.status_code == 403:
                self.log_result("S3 URL Direct Access", False, "HTTP 403 Forbidden - S3 permissions issue", response_time)
                return False
            elif response.status_code == 404:
                self.log_result("S3 URL Direct Access", False, "HTTP 404 Not Found - File doesn't exist", response_time)
                return False
            else:
                self.log_result("S3 URL Direct Access", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_result("S3 URL Direct Access", False, f"Exception: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 COMPREHENSIVE VIDEO STREAMING ARCHITECTURE TEST")
        print("=" * 70)
        print("Testing updated video streaming architecture with URL encoding fixes")
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
            
        print("🎯 CORE FUNCTIONALITY TESTS")
        print("-" * 40)
        
        # Core tests
        streaming_success, stream_data = self.test_s3_key_streaming_proper_encoding()
        job_id_success = self.test_job_id_error_handling()
        cors_success = self.test_cors_preflight()
        
        # S3 direct access test (if we got stream data)
        s3_success = False
        if stream_data and 'stream_url' in stream_data:
            s3_success = self.test_s3_url_direct_access(stream_data['stream_url'])
        
        # Summary
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        # Critical requirements check
        print(f"\n🎯 REVIEW REQUIREMENTS STATUS:")
        print(f"   S3 Key Streaming (Proper Encoding): {'✅ PASS' if streaming_success else '❌ FAIL'}")
        print(f"   Job ID Error Handling: {'✅ PASS' if job_id_success else '❌ FAIL'}")
        print(f"   CORS Headers: {'✅ PASS' if cors_success else '❌ FAIL'}")
        print(f"   S3 Direct Access: {'✅ PASS' if s3_success else '❌ FAIL'}")
        
        # Performance check
        fast_responses = sum(1 for result in self.test_results if result.get('response_time', 0) < 5.0 and result.get('response_time', 0) > 0)
        timed_tests = sum(1 for result in self.test_results if result.get('response_time', 0) > 0)
        
        print(f"\n⚡ PERFORMANCE: {fast_responses}/{timed_tests} responses under 5 seconds")
        
        # URL encoding status
        encoding_issues = any('Double' in result.get('details', '') or '%2520' in result.get('details', '') for result in self.test_results)
        print(f"🔗 URL ENCODING: {'❌ Issues detected' if encoding_issues else '✅ No double encoding issues'}")
        
        # Final verdict
        critical_success = streaming_success and job_id_success and cors_success
        print(f"\n🏆 FINAL VERDICT: {'✅ ARCHITECTURE WORKING' if critical_success else '❌ CRITICAL ISSUES REMAIN'}")
        
        if not critical_success:
            print("   Critical issues need resolution before deployment")
        else:
            print("   Video streaming architecture is ready for production")

if __name__ == "__main__":
    tester = ComprehensiveVideoStreamingTest()
    tester.run_comprehensive_test()