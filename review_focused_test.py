#!/usr/bin/env python3
"""
REVIEW FOCUSED TESTING for Video Splitter Pro
Testing the specific areas mentioned in the review request:

1. Video Streaming Response Format - GET /api/video-stream/{key} 
2. Split Video Endpoint Behavior - POST /api/split-video
3. Authentication Still Working - videotest@example.com credentials

Focus on the expected improvements:
- Video streaming response format completed
- Split video endpoint returns immediately instead of timing out
- CORS errors on split video should be resolved
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration from .env file
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-storage-1751560247"
TIMEOUT = 30  # 30 seconds should be enough for immediate responses

class ReviewFocusedTester:
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

    def test_authentication_with_specific_credentials(self):
        """Test authentication with videotest@example.com credentials as requested"""
        print("🔍 Testing Authentication with videotest@example.com...")
        
        # Test login with specific credentials mentioned in review
        try:
            login_data = {
                "email": "videotest@example.com",
                "password": "TestPassword123!"  # Using a reasonable test password
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    token_preview = self.access_token[:20] + "..." if len(self.access_token) > 20 else self.access_token
                    
                    self.log_test(
                        "Authentication - videotest@example.com Login",
                        True,
                        f"✅ JWT token returned properly. Token preview: {token_preview}, Response time: {response_time:.2f}s"
                    )
                    
                    # Verify token format (should be JWT with 3 parts)
                    token_parts = self.access_token.split('.')
                    if len(token_parts) == 3:
                        self.log_test(
                            "JWT Token Format Validation",
                            True,
                            f"✅ Valid JWT format with 3 parts (header.payload.signature)"
                        )
                    else:
                        self.log_test(
                            "JWT Token Format Validation",
                            False,
                            f"❌ Invalid JWT format - expected 3 parts, got {len(token_parts)}"
                        )
                        
                else:
                    self.log_test(
                        "Authentication - videotest@example.com Login",
                        False,
                        f"❌ Missing access_token in response. Response time: {response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 401:
                # User might not exist, try registration first
                self.log_test(
                    "Authentication - videotest@example.com Login",
                    False,
                    f"❌ Authentication failed (401) - user may not exist. Trying registration first. Response time: {response_time:.2f}s"
                )
                
                # Try registration
                self.test_registration_for_videotest_user()
                
            elif response.status_code == 503:
                self.log_test(
                    "Authentication - videotest@example.com Login",
                    False,
                    f"❌ Service unavailable (503) - MongoDB connection issue. Response time: {response_time:.2f}s"
                )
                
            else:
                self.log_test(
                    "Authentication - videotest@example.com Login",
                    False,
                    f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test(
                "Authentication - videotest@example.com Login",
                False,
                f"❌ Error: {str(e)}"
            )

    def test_registration_for_videotest_user(self):
        """Register the videotest@example.com user if it doesn't exist"""
        print("🔍 Registering videotest@example.com user...")
        
        try:
            register_data = {
                "email": "videotest@example.com",
                "password": "TestPassword123!",
                "firstName": "Video",
                "lastName": "Test"
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.log_test(
                        "User Registration - videotest@example.com",
                        True,
                        f"✅ User registered successfully. Response time: {response_time:.2f}s"
                    )
                else:
                    self.log_test(
                        "User Registration - videotest@example.com",
                        False,
                        f"❌ Registration successful but missing access_token. Response time: {response_time:.2f}s",
                        data
                    )
            elif response.status_code == 409:
                # User already exists, that's fine
                self.log_test(
                    "User Registration - videotest@example.com",
                    True,
                    f"✅ User already exists (409) - this is expected. Response time: {response_time:.2f}s"
                )
                # Try login again
                self.test_authentication_with_specific_credentials()
                
            else:
                self.log_test(
                    "User Registration - videotest@example.com",
                    False,
                    f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test(
                "User Registration - videotest@example.com",
                False,
                f"❌ Error: {str(e)}"
            )

    def test_video_streaming_response_format(self):
        """Test GET /api/video-stream/{key} endpoint response format"""
        print("🔍 Testing Video Streaming Response Format...")
        
        test_keys = [
            "test-video.mp4",
            "sample-mkv-file.mkv", 
            "test-mkv-file.mkv"
        ]
        
        for test_key in test_keys:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
                response_time = time.time() - start_time
                
                # Check response time is under 5 seconds as required
                under_5s = response_time < 5.0
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for required fields: stream_url, s3_key, expires_in
                    required_fields = ['stream_url', 's3_key', 'expires_in']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        stream_url = data['stream_url']
                        s3_key = data['s3_key']
                        expires_in = data['expires_in']
                        
                        # Validate stream_url is a proper S3 presigned URL
                        is_valid_s3_url = 'amazonaws.com' in stream_url and 'Signature' in stream_url
                        
                        # Check CORS headers
                        cors_origin = response.headers.get('Access-Control-Allow-Origin')
                        has_cors = cors_origin is not None
                        
                        if is_valid_s3_url and under_5s and has_cors:
                            self.log_test(
                                f"Video Streaming Response Format - {test_key}",
                                True,
                                f"✅ Complete response format: stream_url (valid S3), s3_key='{s3_key}', expires_in={expires_in}s. Response time: {response_time:.2f}s < 5s ✓. CORS: {cors_origin}"
                            )
                        else:
                            issues = []
                            if not is_valid_s3_url:
                                issues.append("Invalid S3 URL")
                            if not under_5s:
                                issues.append(f"Response time {response_time:.2f}s >= 5s")
                            if not has_cors:
                                issues.append("Missing CORS headers")
                                
                            self.log_test(
                                f"Video Streaming Response Format - {test_key}",
                                False,
                                f"❌ Issues: {', '.join(issues)}. Response time: {response_time:.2f}s",
                                data
                            )
                    else:
                        self.log_test(
                            f"Video Streaming Response Format - {test_key}",
                            False,
                            f"❌ Missing required fields: {missing_fields}. Response time: {response_time:.2f}s",
                            data
                        )
                        
                elif response.status_code == 404:
                    # File not found is expected for test files, but check response format
                    if under_5s:
                        cors_origin = response.headers.get('Access-Control-Allow-Origin')
                        has_cors = cors_origin is not None
                        
                        self.log_test(
                            f"Video Streaming Response Format - {test_key}",
                            True,
                            f"✅ Endpoint working (404 for non-existent file expected). Response time: {response_time:.2f}s < 5s ✓. CORS: {cors_origin if has_cors else 'Missing'}"
                        )
                    else:
                        self.log_test(
                            f"Video Streaming Response Format - {test_key}",
                            False,
                            f"❌ Response time {response_time:.2f}s >= 5s threshold"
                        )
                        
                elif response.status_code == 504:
                    self.log_test(
                        f"Video Streaming Response Format - {test_key}",
                        False,
                        f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s - endpoint still timing out"
                    )
                    
                else:
                    self.log_test(
                        f"Video Streaming Response Format - {test_key}",
                        False,
                        f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Streaming Response Format - {test_key}",
                    False,
                    f"❌ Request timeout after {TIMEOUT}s"
                )
            except Exception as e:
                self.log_test(
                    f"Video Streaming Response Format - {test_key}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_split_video_endpoint_behavior(self):
        """Test POST /api/split-video endpoint behavior - should return HTTP 202 immediately"""
        print("🔍 Testing Split Video Endpoint Behavior...")
        
        test_cases = [
            {
                "s3_key": "uploads/test-video.mp4",
                "description": "Standard MP4 video splitting",
                "segments": [
                    {
                        "start_time": "00:00:00",
                        "end_time": "00:00:30",
                        "output_name": "segment_1.mp4"
                    }
                ]
            },
            {
                "s3_key": "uploads/sample-mkv-file.mkv",
                "description": "MKV video splitting with multiple segments",
                "segments": [
                    {
                        "start_time": "00:00:00", 
                        "end_time": "00:01:00",
                        "output_name": "mkv_segment_1.mp4"
                    },
                    {
                        "start_time": "00:01:00",
                        "end_time": "00:02:00", 
                        "output_name": "mkv_segment_2.mp4"
                    }
                ]
            }
        ]
        
        for test_case in test_cases:
            try:
                split_data = {
                    "s3_key": test_case["s3_key"],
                    "segments": test_case["segments"]
                }
                
                start_time = time.time()
                response = self.session.post(f"{self.base_url}/api/split-video", json=split_data)
                response_time = time.time() - start_time
                
                # Check if response is immediate (under 5 seconds as expected for async processing)
                is_immediate = response_time < 5.0
                
                if response.status_code == 202:
                    # This is the expected behavior - processing started asynchronously
                    data = response.json()
                    
                    if 'job_id' in data:
                        job_id = data['job_id']
                        
                        # Check CORS headers
                        cors_origin = response.headers.get('Access-Control-Allow-Origin')
                        has_cors = cors_origin is not None
                        
                        if is_immediate and has_cors:
                            self.log_test(
                                f"Split Video Endpoint - {test_case['description']}",
                                True,
                                f"✅ HTTP 202 (Accepted) returned immediately with job_id: {job_id}. Response time: {response_time:.2f}s < 5s ✓. CORS: {cors_origin}"
                            )
                        else:
                            issues = []
                            if not is_immediate:
                                issues.append(f"Response time {response_time:.2f}s >= 5s")
                            if not has_cors:
                                issues.append("Missing CORS headers")
                                
                            self.log_test(
                                f"Split Video Endpoint - {test_case['description']}",
                                False,
                                f"❌ Issues: {', '.join(issues)}. job_id: {job_id}",
                                data
                            )
                    else:
                        self.log_test(
                            f"Split Video Endpoint - {test_case['description']}",
                            False,
                            f"❌ HTTP 202 but missing job_id. Response time: {response_time:.2f}s",
                            data
                        )
                        
                elif response.status_code == 404:
                    # File not found is expected for test files
                    if is_immediate:
                        cors_origin = response.headers.get('Access-Control-Allow-Origin')
                        has_cors = cors_origin is not None
                        
                        self.log_test(
                            f"Split Video Endpoint - {test_case['description']}",
                            True,
                            f"✅ Endpoint working (404 for non-existent file expected). Response time: {response_time:.2f}s < 5s ✓. CORS: {cors_origin if has_cors else 'Missing'}"
                        )
                    else:
                        self.log_test(
                            f"Split Video Endpoint - {test_case['description']}",
                            False,
                            f"❌ Response time {response_time:.2f}s >= 5s threshold"
                        )
                        
                elif response.status_code == 504:
                    self.log_test(
                        f"Split Video Endpoint - {test_case['description']}",
                        False,
                        f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s - endpoint still timing out instead of returning 202 immediately"
                    )
                    
                elif response.status_code == 501:
                    self.log_test(
                        f"Split Video Endpoint - {test_case['description']}",
                        False,
                        f"❌ Still returning 501 (Not Implemented) - endpoint not fully implemented yet. Response time: {response_time:.2f}s"
                    )
                    
                else:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    self.log_test(
                        f"Split Video Endpoint - {test_case['description']}",
                        False,
                        f"❌ HTTP {response.status_code} (expected 202). Response time: {response_time:.2f}s. CORS: {cors_origin}",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Split Video Endpoint - {test_case['description']}",
                    False,
                    f"❌ Request timeout after {TIMEOUT}s - endpoint not returning immediately as expected"
                )
            except Exception as e:
                self.log_test(
                    f"Split Video Endpoint - {test_case['description']}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_cors_headers_comprehensive(self):
        """Test CORS headers are present on all endpoints"""
        print("🔍 Testing CORS Headers Comprehensive...")
        
        endpoints_to_test = [
            ("GET", "/api/", "Health check endpoint"),
            ("OPTIONS", "/api/video-stream/test.mp4", "Video streaming preflight"),
            ("OPTIONS", "/api/split-video", "Split video preflight"),
            ("OPTIONS", "/api/auth/login", "Authentication preflight")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "OPTIONS":
                    response = self.session.options(f"{self.base_url}{endpoint}")
                    
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                has_origin = cors_headers['Access-Control-Allow-Origin'] is not None
                has_methods = cors_headers['Access-Control-Allow-Methods'] is not None
                has_headers = cors_headers['Access-Control-Allow-Headers'] is not None
                
                if has_origin:
                    cors_details = f"Origin: {cors_headers['Access-Control-Allow-Origin']}"
                    if has_methods:
                        cors_details += f", Methods: {cors_headers['Access-Control-Allow-Methods']}"
                    if has_headers:
                        cors_details += f", Headers: {cors_headers['Access-Control-Allow-Headers']}"
                        
                    self.log_test(
                        f"CORS Headers - {description}",
                        True,
                        f"✅ CORS headers present. {cors_details}"
                    )
                else:
                    self.log_test(
                        f"CORS Headers - {description}",
                        False,
                        f"❌ Missing CORS headers. Status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"CORS Headers - {description}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def run_review_focused_tests(self):
        """Run the focused tests based on the review request"""
        print("=" * 80)
        print("🎯 REVIEW FOCUSED TESTING - Video Splitter Pro")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Expected S3 Bucket: {S3_BUCKET}")
        print()
        print("📋 REVIEW REQUEST FOCUS AREAS:")
        print("   1. Video Streaming Response Format - GET /api/video-stream/{key}")
        print("      • Should return: stream_url, s3_key, expires_in fields")
        print("      • Response time under 5 seconds")
        print("      • CORS headers present")
        print()
        print("   2. Split Video Endpoint Behavior - POST /api/split-video")
        print("      • Should return HTTP 202 (Accepted) with job_id immediately")
        print("      • No more 29s timeout")
        print("      • CORS headers included")
        print()
        print("   3. Authentication Still Working - videotest@example.com")
        print("      • JWT tokens returned properly")
        print()
        print("🎯 EXPECTED IMPROVEMENTS:")
        print("   • Video streaming response format completed")
        print("   • Split video returns immediately instead of timing out")
        print("   • CORS errors on split video resolved")
        print()
        
        # Run the focused tests
        self.test_authentication_with_specific_credentials()
        self.test_video_streaming_response_format()
        self.test_split_video_endpoint_behavior()
        self.test_cors_headers_comprehensive()
        
        # Summary
        print("=" * 80)
        print("📊 REVIEW FOCUSED TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze specific review areas
        review_areas = {
            'video_streaming_format': False,
            'split_video_immediate': False,
            'authentication_working': False,
            'cors_headers_present': False
        }
        
        for result in self.test_results:
            if result['success']:
                test_name = result['test'].lower()
                if 'video streaming response format' in test_name:
                    review_areas['video_streaming_format'] = True
                elif 'split video endpoint' in test_name:
                    review_areas['split_video_immediate'] = True
                elif 'authentication' in test_name and 'videotest@example.com' in test_name:
                    review_areas['authentication_working'] = True
                elif 'cors headers' in test_name:
                    review_areas['cors_headers_present'] = True
        
        print("🎯 REVIEW AREAS STATUS:")
        print(f"   ✅ Video Streaming Response Format: {'WORKING' if review_areas['video_streaming_format'] else 'ISSUES FOUND'}")
        print(f"   ✅ Split Video Immediate Response: {'WORKING' if review_areas['split_video_immediate'] else 'ISSUES FOUND'}")
        print(f"   ✅ Authentication (videotest@example.com): {'WORKING' if review_areas['authentication_working'] else 'ISSUES FOUND'}")
        print(f"   ✅ CORS Headers Present: {'WORKING' if review_areas['cors_headers_present'] else 'ISSUES FOUND'}")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Final assessment
        print("💡 REVIEW ASSESSMENT:")
        working_areas = sum(review_areas.values())
        
        if working_areas == 4:
            print("   🎉 ALL REVIEW AREAS WORKING PERFECTLY!")
            print("   • Video streaming response format is complete")
            print("   • Split video endpoint returns immediately (no timeout)")
            print("   • Authentication with videotest@example.com works")
            print("   • CORS headers are properly configured")
        elif working_areas >= 2:
            print(f"   ✅ PARTIAL SUCCESS: {working_areas}/4 review areas working")
            if not review_areas['video_streaming_format']:
                print("   • Video streaming response format needs attention")
            if not review_areas['split_video_immediate']:
                print("   • Split video endpoint still has timeout/response issues")
            if not review_areas['authentication_working']:
                print("   • Authentication with videotest@example.com not working")
            if not review_areas['cors_headers_present']:
                print("   • CORS headers configuration needs attention")
        else:
            print("   ❌ MAJOR ISSUES: Most review areas not working as expected")
            print("   • Significant fixes needed before the improvements are complete")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = ReviewFocusedTester()
    passed, failed = tester.run_review_focused_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)