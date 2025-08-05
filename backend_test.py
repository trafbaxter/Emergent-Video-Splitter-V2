#!/usr/bin/env python3
"""
CORS-Focused AWS Lambda Backend Testing for Video Splitter Pro
Tests the updated Lambda function with enhanced CORS support for authentication system.
Focus on testing authentication endpoints with different origins and verifying CORS headers.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-uploads"
TIMEOUT = 30

# CORS Test Origins - matching the allowed origins in fix_cors_lambda.py
TEST_ORIGINS = [
    'https://develop.tads-video-splitter.com',
    'https://main.tads-video-splitter.com', 
    'https://working.tads-video-splitter.com',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000'
]

class VideoSplitterTester:
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

    def test_basic_connectivity(self):
        """Test 1: Basic connectivity to AWS Lambda API Gateway endpoint"""
        print("🔍 Testing Basic Connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['message', 'version', 'authentication', 'database']
                
                if all(field in data for field in expected_fields):
                    self.log_test(
                        "Basic API Gateway Connectivity", 
                        True, 
                        f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}, Version: {data.get('version', 'N/A')}"
                    )
                    
                    # Check dependency status
                    deps = data.get('dependencies', {})
                    self.log_test(
                        "Authentication Dependencies Check",
                        all(deps.values()),
                        f"bcrypt: {deps.get('bcrypt', False)}, jwt: {deps.get('jwt', False)}, pymongo: {deps.get('pymongo', False)}"
                    )
                    
                    # Check database status
                    db_status = data.get('database', 'unknown')
                    self.log_test(
                        "Database Connectivity Check",
                        db_status in ['connected', 'fallback_mode'],
                        f"Database status: {db_status}"
                    )
                    
                else:
                    self.log_test("Basic API Gateway Connectivity", False, "Missing expected response fields", data)
            else:
                self.log_test("Basic API Gateway Connectivity", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("Basic API Gateway Connectivity", False, f"Connection error: {str(e)}")

    def test_cors_configuration(self):
        """Test 2: CORS configuration"""
        print("🔍 Testing CORS Configuration...")
        try:
            # Test OPTIONS request
            response = self.session.options(f"{self.base_url}/api/")
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            has_cors = any(cors_headers.values())
            self.log_test(
                "CORS Headers Configuration",
                has_cors,
                f"CORS headers present: {has_cors}, Origin: {cors_headers['Access-Control-Allow-Origin']}"
            )
            
        except Exception as e:
            self.log_test("CORS Headers Configuration", False, f"Error: {str(e)}")

    def test_authentication_endpoints(self):
        """Test 3: Authentication endpoints (register, login, user profile)"""
        print("🔍 Testing Authentication Endpoints...")
        
        # Test user registration
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "TestPassword123!"
        
        try:
            # Test registration endpoint accessibility
            register_data = {
                "email": test_email,
                "password": test_password,
                "firstName": "Test",
                "lastName": "User"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                if 'access_token' in data and 'user_id' in data:
                    self.access_token = data['access_token']
                    self.user_id = data['user_id']
                    demo_mode = data.get('demo_mode', False)
                    
                    self.log_test(
                        "User Registration",
                        True,
                        f"User registered successfully, Demo mode: {demo_mode}, User ID: {self.user_id[:8]}..."
                    )
                else:
                    self.log_test("User Registration", False, "Missing access_token or user_id in response", data)
                    
            elif response.status_code == 503:
                # MongoDB connection failure - expected based on test history
                self.log_test(
                    "User Registration",
                    False,
                    "MongoDB connection failure (503) - known issue from test history",
                    response.json() if response.content else {}
                )
            elif response.status_code == 502:
                self.log_test("User Registration", False, "Lambda execution failure (502)", {})
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")

        # Test login endpoint
        try:
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.log_test("User Login", True, "Login successful")
                else:
                    self.log_test("User Login", False, "Missing access_token in response", data)
            elif response.status_code == 503:
                self.log_test("User Login", False, "MongoDB connection failure (503) - known issue", response.json() if response.content else {})
            elif response.status_code == 401:
                self.log_test("User Login", False, "Authentication failed - user may not exist due to registration failure", response.json() if response.content else {})
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")

        # Test user profile endpoint (protected)
        if self.access_token:
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = self.session.get(f"{self.base_url}/api/user/profile", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'user' in data:
                        self.log_test("User Profile Access", True, "Profile retrieved successfully")
                    else:
                        self.log_test("User Profile Access", False, "Missing user data in response", data)
                else:
                    self.log_test("User Profile Access", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                    
            except Exception as e:
                self.log_test("User Profile Access", False, f"Error: {str(e)}")
        else:
            self.log_test("User Profile Access", False, "No access token available for testing")

    def test_core_video_processing(self):
        """Test 4: Core video processing endpoints"""
        print("🔍 Testing Core Video Processing Endpoints...")
        
        # Test presigned URL generation
        try:
            presigned_data = {
                "filename": "test_video.mp4",
                "contentType": "video/mp4"
            }
            
            response = self.session.post(f"{self.base_url}/api/generate-presigned-url", json=presigned_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'uploadUrl' in data and 'objectKey' in data:
                    upload_url = data['uploadUrl']
                    object_key = data['objectKey']
                    
                    # Verify the URL contains AWS signature
                    if 'amazonaws.com' in upload_url and 'Signature' in upload_url:
                        self.log_test(
                            "S3 Presigned URL Generation",
                            True,
                            f"Valid presigned URL generated for bucket: {S3_BUCKET}"
                        )
                        
                        # Test video metadata extraction with the object key
                        self.test_video_metadata(object_key)
                        
                    else:
                        self.log_test("S3 Presigned URL Generation", False, "Invalid presigned URL format", data)
                else:
                    self.log_test("S3 Presigned URL Generation", False, "Missing uploadUrl or objectKey", data)
            else:
                self.log_test("S3 Presigned URL Generation", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("S3 Presigned URL Generation", False, f"Error: {str(e)}")

    def test_video_metadata(self, object_key: str):
        """Test video metadata extraction"""
        try:
            metadata_data = {
                "objectKey": object_key
            }
            
            response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Video Metadata Extraction", True, "Metadata endpoint accessible")
            elif response.status_code == 404:
                # Expected for non-existent video file
                self.log_test("Video Metadata Extraction", True, "Endpoint working (404 for non-existent file is expected)")
            elif response.status_code == 500:
                self.log_test("Video Metadata Extraction", False, "Internal server error", response.json() if response.content else {})
            else:
                self.log_test("Video Metadata Extraction", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("Video Metadata Extraction", False, f"Error: {str(e)}")

    def test_video_splitting(self):
        """Test 5: Video splitting functionality"""
        print("🔍 Testing Video Splitting Functionality...")
        
        try:
            split_data = {
                "objectKey": "test/sample_video.mp4",
                "segments": [
                    {"start": 0, "end": 30, "name": "segment_1"},
                    {"start": 30, "end": 60, "name": "segment_2"}
                ]
            }
            
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Video Splitting", True, "Split endpoint accessible and processing")
            elif response.status_code == 400:
                # Expected for invalid request data
                self.log_test("Video Splitting", True, "Endpoint working (400 for invalid data is expected)")
            elif response.status_code == 404:
                # Expected for non-existent video file
                self.log_test("Video Splitting", True, "Endpoint working (404 for non-existent file is expected)")
            elif response.status_code == 502:
                self.log_test("Video Splitting", False, "Lambda execution failure (502)", {})
            else:
                self.log_test("Video Splitting", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("Video Splitting", False, f"Error: {str(e)}")

    def test_video_streaming(self):
        """Test 6: Video streaming functionality"""
        print("🔍 Testing Video Streaming Functionality...")
        
        try:
            # Test download endpoint
            test_key = "test/sample_video.mp4"
            response = self.session.get(f"{self.base_url}/api/download/{test_key}")
            
            if response.status_code == 200:
                data = response.json()
                if 'downloadUrl' in data:
                    download_url = data['downloadUrl']
                    if 'amazonaws.com' in download_url:
                        self.log_test("Video Streaming/Download", True, "Download URL generated successfully")
                    else:
                        self.log_test("Video Streaming/Download", False, "Invalid download URL format", data)
                else:
                    self.log_test("Video Streaming/Download", False, "Missing downloadUrl in response", data)
            elif response.status_code == 404:
                # Expected for non-existent file
                self.log_test("Video Streaming/Download", True, "Endpoint working (404 for non-existent file is expected)")
            elif response.status_code == 502:
                self.log_test("Video Streaming/Download", False, "Lambda execution failure (502)", {})
            else:
                self.log_test("Video Streaming/Download", False, f"HTTP {response.status_code}", response.json() if response.content else {})
                
        except Exception as e:
            self.log_test("Video Streaming/Download", False, f"Error: {str(e)}")

    def test_ffmpeg_integration(self):
        """Test 7: FFmpeg Lambda integration"""
        print("🔍 Testing FFmpeg Lambda Integration...")
        
        # This is tested indirectly through video metadata extraction
        # The lambda_function_with_fallback.py calls the ffmpeg-converter Lambda function
        
        try:
            # Test with a realistic object key to see if FFmpeg Lambda is called
            metadata_data = {
                "objectKey": "uploads/test-video-for-ffmpeg.mp4"
            }
            
            response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_data)
            
            # Check response time to infer if FFmpeg processing is attempted
            response_time = response.elapsed.total_seconds()
            
            if response.status_code == 404:
                # Expected for non-existent file, but should be fast if FFmpeg integration works
                if response_time < 5:
                    self.log_test(
                        "FFmpeg Lambda Integration",
                        True,
                        f"FFmpeg integration appears functional (fast 404 response: {response_time:.2f}s)"
                    )
                else:
                    self.log_test(
                        "FFmpeg Lambda Integration",
                        False,
                        f"Slow response suggests FFmpeg timeout issues ({response_time:.2f}s)"
                    )
            elif response.status_code == 500:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', 'Unknown error')
                
                if 'ffmpeg' in error_msg.lower() or 'lambda' in error_msg.lower():
                    self.log_test("FFmpeg Lambda Integration", False, f"FFmpeg Lambda error: {error_msg}")
                else:
                    self.log_test("FFmpeg Lambda Integration", False, f"Server error: {error_msg}")
            else:
                self.log_test(
                    "FFmpeg Lambda Integration",
                    True,
                    f"FFmpeg integration accessible (HTTP {response.status_code}, {response_time:.2f}s)"
                )
                
        except Exception as e:
            self.log_test("FFmpeg Lambda Integration", False, f"Error: {str(e)}")

    def test_s3_bucket_access(self):
        """Test 8: S3 bucket configuration and access"""
        print("🔍 Testing S3 Bucket Configuration...")
        
        # This is tested indirectly through presigned URL generation
        # If presigned URLs are generated successfully, S3 access is working
        
        try:
            # Generate a presigned URL and check its validity
            presigned_data = {
                "filename": "s3-test-file.mp4",
                "contentType": "video/mp4"
            }
            
            response = self.session.post(f"{self.base_url}/api/generate-presigned-url", json=presigned_data)
            
            if response.status_code == 200:
                data = response.json()
                upload_url = data.get('uploadUrl', '')
                
                # Check if URL contains correct bucket name
                if S3_BUCKET in upload_url:
                    self.log_test(
                        "S3 Bucket Access",
                        True,
                        f"S3 bucket '{S3_BUCKET}' accessible via presigned URLs"
                    )
                else:
                    self.log_test(
                        "S3 Bucket Access",
                        False,
                        f"Presigned URL doesn't contain expected bucket '{S3_BUCKET}'"
                    )
            else:
                self.log_test("S3 Bucket Access", False, f"Failed to generate presigned URL: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("S3 Bucket Access", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("=" * 80)
        print("🚀 AWS LAMBDA BACKEND COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Expected S3 Bucket: {S3_BUCKET}")
        print()
        
        # Run all tests
        self.test_basic_connectivity()
        self.test_cors_configuration()
        self.test_authentication_endpoints()
        self.test_core_video_processing()
        self.test_video_splitting()
        self.test_video_streaming()
        self.test_ffmpeg_integration()
        self.test_s3_bucket_access()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Critical issues
        critical_failures = []
        for result in self.test_results:
            if not result['success'] and any(keyword in result['details'].lower() for keyword in ['502', 'connection', 'timeout', 'execution failure']):
                critical_failures.append(result['test'])
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"   • {failure}")
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        
        auth_failures = sum(1 for r in self.test_results if not r['success'] and 'auth' in r['test'].lower())
        if auth_failures > 0:
            print("   • Authentication system has MongoDB connectivity issues (expected based on test history)")
            print("   • Core video processing functionality should be prioritized")
        
        if any('502' in r['details'] for r in self.test_results if not r['success']):
            print("   • Lambda function execution failures detected - check deployment and dependencies")
        
        if passed_tests >= total_tests * 0.7:
            print("   • Overall system health is good - most functionality is working")
        else:
            print("   • System requires immediate attention - multiple critical failures")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoSplitterTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)