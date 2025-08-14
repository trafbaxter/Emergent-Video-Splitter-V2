#!/usr/bin/env python3
"""
Video Splitter Pro - Review Backend Testing
Testing authentication system and video streaming functionality as requested.

FOCUS AREAS:
1. Authentication Testing - Test user registration with videotest@example.com
2. Video Streaming Endpoint Testing - Test GET /api/video-stream/{key}
3. Video Metadata Endpoint Testing - Test POST /api/get-video-info
4. Split Video Endpoint Testing - Test POST /api/split-video for CORS errors

Based on test_result.md analysis:
- Most endpoints are working but video processing has timeout issues
- FFmpeg Lambda consistently times out after ~29s
- CORS configuration is working properly
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using AWS Lambda API Gateway URL from existing test
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 60  # Reasonable timeout for testing

class VideoSplitterReviewTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.access_token = None
        self.user_id = None
        
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

    def test_authentication_system(self):
        """Test 1: Authentication system with specific test user"""
        print("🔍 Testing Authentication System...")
        
        # Test user registration with requested email
        test_email = "videotest@example.com"
        test_password = "videotest123"
        
        try:
            # Test registration endpoint
            register_data = {
                "email": test_email,
                "password": test_password,
                "firstName": "Video",
                "lastName": "Tester"
            }
            
            print(f"   🎯 Testing registration with {test_email}")
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Registration response time: {response_time:.2f}s")
            
            if response.status_code == 201:
                data = response.json()
                if 'access_token' in data and 'user_id' in data:
                    self.access_token = data['access_token']
                    self.user_id = data['user_id']
                    demo_mode = data.get('demo_mode', False)
                    
                    self.log_test(
                        "User Registration (videotest@example.com)",
                        True,
                        f"✅ Registration successful! Demo mode: {demo_mode}, User ID: {self.user_id[:8]}..., Response time: {response_time:.2f}s"
                    )
                    
                    # Verify JWT token format
                    if '.' in self.access_token and len(self.access_token.split('.')) == 3:
                        self.log_test(
                            "JWT Token Format Validation",
                            True,
                            f"✅ Valid JWT token format returned (3 parts separated by dots)"
                        )
                    else:
                        self.log_test(
                            "JWT Token Format Validation",
                            False,
                            f"❌ Invalid JWT token format: {self.access_token[:50]}..."
                        )
                        
                else:
                    self.log_test("User Registration (videotest@example.com)", False, "Missing access_token or user_id in response", data)
                    
            elif response.status_code == 409:
                # User already exists - try login instead
                self.log_test(
                    "User Registration (videotest@example.com)",
                    True,
                    f"✅ User already exists (409) - this is expected for repeated tests. Response time: {response_time:.2f}s"
                )
                
            elif response.status_code == 503:
                # MongoDB connection failure - expected based on test history
                self.log_test(
                    "User Registration (videotest@example.com)",
                    False,
                    f"❌ MongoDB connection failure (503) - known issue from test history. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
            else:
                self.log_test(
                    "User Registration (videotest@example.com)", 
                    False, 
                    f"HTTP {response.status_code}, Response time: {response_time:.2f}s", 
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test("User Registration (videotest@example.com)", False, f"Error: {str(e)}")

        # Test login with the same user
        try:
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            print(f"   🎯 Testing login with {test_email}")
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Login response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.log_test(
                        "User Login (videotest@example.com)",
                        True,
                        f"✅ Login successful! Response time: {response_time:.2f}s"
                    )
                    
                    # Verify JWT token is returned properly
                    if '.' in self.access_token and len(self.access_token.split('.')) == 3:
                        self.log_test(
                            "JWT Token Returned on Login",
                            True,
                            f"✅ Valid JWT token returned on login"
                        )
                    else:
                        self.log_test(
                            "JWT Token Returned on Login",
                            False,
                            f"❌ Invalid JWT token format on login"
                        )
                else:
                    self.log_test("User Login (videotest@example.com)", False, "Missing access_token in response", data)
            elif response.status_code == 503:
                self.log_test(
                    "User Login (videotest@example.com)", 
                    False, 
                    f"❌ MongoDB connection failure (503). Response time: {response_time:.2f}s", 
                    response.json() if response.content else {}
                )
            elif response.status_code == 401:
                self.log_test(
                    "User Login (videotest@example.com)", 
                    False, 
                    f"❌ Authentication failed (401) - user may not exist. Response time: {response_time:.2f}s", 
                    response.json() if response.content else {}
                )
            else:
                self.log_test(
                    "User Login (videotest@example.com)", 
                    False, 
                    f"HTTP {response.status_code}, Response time: {response_time:.2f}s", 
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test("User Login (videotest@example.com)", False, f"Error: {str(e)}")

    def test_video_streaming_endpoint(self):
        """Test 2: Video streaming endpoint with sample keys"""
        print("🔍 Testing Video Streaming Endpoint...")
        
        # Test with various sample keys
        test_keys = [
            "uploads/sample-video.mp4",
            "test/demo-video.mkv", 
            "videos/test-file.mp4"
        ]
        
        for test_key in test_keys:
            try:
                print(f"   🎯 Testing video streaming with key: {test_key}")
                start_time = time.time()
                
                response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                
                # Check if response time is under 5 seconds as requested
                under_5s = response_time < 5.0
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['stream_url', 's3_key', 'expires_in']
                    
                    if all(field in data for field in expected_fields):
                        stream_url = data['stream_url']
                        
                        # Verify it returns presigned S3 URL
                        if 'amazonaws.com' in stream_url and 'Signature' in stream_url:
                            self.log_test(
                                f"Video Streaming - {test_key.split('/')[-1]}",
                                True,
                                f"✅ Valid presigned S3 URL returned! Response time: {response_time:.2f}s ({'✅ Under 5s' if under_5s else '⚠️ Over 5s'})"
                            )
                            
                            # Check CORS headers
                            cors_origin = response.headers.get('Access-Control-Allow-Origin')
                            if cors_origin:
                                self.log_test(
                                    f"CORS Headers - Video Streaming ({test_key.split('/')[-1]})",
                                    True,
                                    f"✅ CORS headers present: Access-Control-Allow-Origin: {cors_origin}"
                                )
                            else:
                                self.log_test(
                                    f"CORS Headers - Video Streaming ({test_key.split('/')[-1]})",
                                    False,
                                    f"❌ Missing CORS headers in response"
                                )
                        else:
                            self.log_test(
                                f"Video Streaming - {test_key.split('/')[-1]}",
                                False,
                                f"❌ Invalid presigned URL format. Response time: {response_time:.2f}s"
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Streaming - {test_key.split('/')[-1]}",
                            False,
                            f"❌ Missing expected fields: {missing_fields}. Response time: {response_time:.2f}s",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent files - endpoint is working
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        True,
                        f"✅ Endpoint working (404 for non-existent file is expected). Response time: {response_time:.2f}s ({'✅ Under 5s' if under_5s else '⚠️ Over 5s'})"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        False,
                        f"❌ Gateway timeout (504) after {response_time:.2f}s - Lambda function timeout issue"
                    )
                    
                else:
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        False,
                        f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Streaming - {test_key.split('/')[-1]}",
                    False,
                    f"❌ Request timeout after {TIMEOUT}s"
                )
            except Exception as e:
                self.log_test(
                    f"Video Streaming - {test_key.split('/')[-1]}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_video_metadata_endpoint(self):
        """Test 3: Video metadata endpoint"""
        print("🔍 Testing Video Metadata Endpoint...")
        
        # Test with sample S3 keys
        test_cases = [
            {
                "s3_key": "uploads/test-video.mp4",
                "description": "Standard MP4 video file"
            },
            {
                "s3_key": "uploads/sample-mkv-file.mkv", 
                "description": "MKV file (should detect subtitles)"
            }
        ]
        
        for test_case in test_cases:
            try:
                metadata_data = {
                    "s3_key": test_case["s3_key"]
                }
                
                print(f"   🎯 Testing metadata extraction: {test_case['description']}")
                start_time = time.time()
                
                response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_data)
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['duration', 'format', 'video_streams', 'audio_streams', 'subtitle_streams']
                    
                    if all(field in data for field in expected_fields):
                        duration = data.get('duration', 0)
                        subtitle_count = data.get('subtitle_streams', 0)
                        format_info = data.get('format', 'unknown')
                        
                        self.log_test(
                            f"Video Metadata - {test_case['description']}",
                            True,
                            f"✅ Metadata retrieved! Duration={duration}s, Format={format_info}, Subtitles={subtitle_count}, Response time={response_time:.2f}s"
                        )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Metadata - {test_case['description']}",
                            False,
                            f"❌ Missing expected fields: {missing_fields}. Response time={response_time:.2f}s",
                            data
                        )
                        
                elif response.status_code == 404:
                    # File not found - endpoint is working
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        True,
                        f"✅ Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    # Gateway timeout - known issue from test_result.md
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        False,
                        f"❌ TIMEOUT: HTTP 504 after {response_time:.2f}s - FFmpeg Lambda timeout issue (known from test history)"
                    )
                    
                elif response.status_code == 400:
                    # Bad request - check if it's proper validation
                    data = response.json() if response.content else {}
                    if 'error' in data:
                        self.log_test(
                            f"Video Metadata - {test_case['description']}",
                            True,
                            f"✅ Proper validation (400) - endpoint working. Error: {data.get('error', 'N/A')}"
                        )
                    else:
                        self.log_test(
                            f"Video Metadata - {test_case['description']}",
                            False,
                            f"❌ HTTP 400 without proper error message. Response time={response_time:.2f}s",
                            data
                        )
                        
                else:
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        False,
                        f"❌ HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Metadata - {test_case['description']}",
                    False,
                    f"❌ Request timeout after {TIMEOUT}s - endpoint timing out"
                )
            except Exception as e:
                self.log_test(
                    f"Video Metadata - {test_case['description']}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_split_video_endpoint_cors(self):
        """Test 4: Split video endpoint specifically for CORS errors"""
        print("🔍 Testing Split Video Endpoint (CORS Focus)...")
        
        # Test CORS preflight first
        try:
            print("   🎯 Testing CORS preflight (OPTIONS request)")
            
            headers = {
                'Origin': 'https://working.tads-video-splitter.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.base_url}/api/split-video", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if cors_headers['Access-Control-Allow-Origin']:
                self.log_test(
                    "Split Video CORS Preflight",
                    True,
                    f"✅ CORS preflight successful! Origin: {cors_headers['Access-Control-Allow-Origin']}, Methods: {cors_headers['Access-Control-Allow-Methods']}"
                )
            else:
                self.log_test(
                    "Split Video CORS Preflight",
                    False,
                    f"❌ Missing CORS headers in preflight response"
                )
                
        except Exception as e:
            self.log_test("Split Video CORS Preflight", False, f"❌ Error: {str(e)}")

        # Test actual POST request
        try:
            split_data = {
                "s3_key": "uploads/test-video.mp4",
                "segments": [
                    {
                        "start_time": "00:00:00",
                        "end_time": "00:00:30", 
                        "output_name": "segment_1.mp4"
                    }
                ]
            }
            
            headers = {
                'Origin': 'https://working.tads-video-splitter.com',
                'Content-Type': 'application/json'
            }
            
            print("   🎯 Testing POST /api/split-video with CORS headers")
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            # Check for CORS headers in response
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            
            if response.status_code == 202:
                # Processing started successfully
                data = response.json()
                if 'job_id' in data:
                    self.log_test(
                        "Split Video Endpoint",
                        True,
                        f"✅ Processing started! Job ID: {data['job_id']}, Response time: {response_time:.2f}s"
                    )
                else:
                    self.log_test(
                        "Split Video Endpoint",
                        False,
                        f"❌ 202 response but missing job_id. Response time: {response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 404:
                # File not found - endpoint is working
                self.log_test(
                    "Split Video Endpoint",
                    True,
                    f"✅ Endpoint working (404 for non-existent file is expected). Response time: {response_time:.2f}s"
                )
                
            elif response.status_code == 504:
                # Gateway timeout - known issue
                self.log_test(
                    "Split Video Endpoint",
                    False,
                    f"❌ TIMEOUT: HTTP 504 after {response_time:.2f}s - FFmpeg Lambda timeout issue (known from test history)"
                )
                
            else:
                self.log_test(
                    "Split Video Endpoint",
                    False,
                    f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
            
            # Check CORS headers regardless of status code
            if cors_origin:
                self.log_test(
                    "Split Video CORS Headers",
                    True,
                    f"✅ CORS headers present in response: Access-Control-Allow-Origin: {cors_origin}"
                )
            else:
                self.log_test(
                    "Split Video CORS Headers",
                    False,
                    f"❌ Missing CORS headers in POST response - this could cause CORS errors in browser"
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Split Video Endpoint",
                False,
                f"❌ Request timeout after {TIMEOUT}s - endpoint timing out"
            )
        except Exception as e:
            self.log_test(
                "Split Video Endpoint",
                False,
                f"❌ Error: {str(e)}"
            )

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("🔍 Testing Basic API Connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Basic API Connectivity",
                    True,
                    f"✅ API Gateway accessible. Version: {data.get('version', 'N/A')}, Message: {data.get('message', 'N/A')}"
                )
            else:
                self.log_test(
                    "Basic API Connectivity",
                    False,
                    f"❌ HTTP {response.status_code}",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"❌ Error: {str(e)}")

    def run_review_tests(self):
        """Run the focused review tests"""
        print("=" * 80)
        print("🎯 VIDEO SPLITTER PRO - REVIEW BACKEND TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("📋 REVIEW FOCUS AREAS:")
        print("   1. Authentication Testing - videotest@example.com user")
        print("   2. Video Streaming Endpoint - GET /api/video-stream/{key}")
        print("   3. Video Metadata Endpoint - POST /api/get-video-info")
        print("   4. Split Video Endpoint - POST /api/split-video (CORS focus)")
        print()
        
        # Run tests in order
        self.test_basic_connectivity()
        self.test_authentication_system()
        self.test_video_streaming_endpoint()
        self.test_video_metadata_endpoint()
        self.test_split_video_endpoint_cors()
        
        # Summary
        print("=" * 80)
        print("📊 REVIEW TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Categorize results
        auth_tests = [r for r in self.test_results if 'auth' in r['test'].lower() or 'login' in r['test'].lower() or 'registration' in r['test'].lower() or 'jwt' in r['test'].lower()]
        streaming_tests = [r for r in self.test_results if 'streaming' in r['test'].lower()]
        metadata_tests = [r for r in self.test_results if 'metadata' in r['test'].lower()]
        split_tests = [r for r in self.test_results if 'split' in r['test'].lower()]
        cors_tests = [r for r in self.test_results if 'cors' in r['test'].lower()]
        
        print("🔍 RESULTS BY CATEGORY:")
        print(f"   🔐 Authentication: {sum(1 for r in auth_tests if r['success'])}/{len(auth_tests)} passed")
        print(f"   📺 Video Streaming: {sum(1 for r in streaming_tests if r['success'])}/{len(streaming_tests)} passed")
        print(f"   📋 Video Metadata: {sum(1 for r in metadata_tests if r['success'])}/{len(metadata_tests)} passed")
        print(f"   ✂️  Video Splitting: {sum(1 for r in split_tests if r['success'])}/{len(split_tests)} passed")
        print(f"   🌐 CORS: {sum(1 for r in cors_tests if r['success'])}/{len(cors_tests)} passed")
        print()
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print("❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("💡 KEY FINDINGS:")
        
        # Check for timeout issues
        timeout_issues = [r for r in failed_results if '504' in r['details'] or 'timeout' in r['details'].lower()]
        if timeout_issues:
            print(f"   🚨 TIMEOUT ISSUES: {len(timeout_issues)} endpoints timing out (FFmpeg Lambda issue)")
            
        # Check for CORS issues
        cors_issues = [r for r in failed_results if 'cors' in r['details'].lower()]
        if cors_issues:
            print(f"   🌐 CORS ISSUES: {len(cors_issues)} CORS-related failures")
        else:
            print("   ✅ CORS: No CORS errors detected")
            
        # Check authentication status
        auth_working = any(r['success'] for r in auth_tests)
        if auth_working:
            print("   ✅ AUTHENTICATION: Working properly")
        else:
            print("   ❌ AUTHENTICATION: Issues detected")
            
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoSplitterReviewTester()
    passed, failed = tester.run_review_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)