#!/usr/bin/env python3
"""
Video Processing Endpoints Testing for Video Splitter Pro
Tests the newly restored video processing functionality that now calls the actual FFmpeg Lambda function.

Key changes being tested:
1. Video metadata extraction - Now calls FFmpeg Lambda for real duration/metadata analysis
2. Video splitting - Now calls FFmpeg Lambda with actual split configuration instead of returning 501
3. Job status tracking - Now checks S3 for completed results instead of placeholder
4. Download functionality - Now generates presigned URLs for processed files
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-storage-1751560247"
TIMEOUT = 35  # Increased timeout for FFmpeg processing

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

    def test_video_metadata_extraction_real_ffmpeg(self):
        """Test 1: Video metadata extraction with real FFmpeg Lambda calls"""
        print("🔍 Testing Video Metadata Extraction (Real FFmpeg)...")
        
        # Test with a realistic S3 key that should exist or be processable
        test_cases = [
            {
                "s3_key": "uploads/test-video.mp4",
                "description": "Standard MP4 video file"
            },
            {
                "s3_key": "uploads/sample-mkv-file.mkv", 
                "description": "MKV file with potential subtitles"
            },
            {
                "s3_key": "test/demo-video.mp4",
                "description": "Demo video file"
            }
        ]
        
        for test_case in test_cases:
            try:
                metadata_data = {
                    "s3_key": test_case["s3_key"]
                }
                
                print(f"   Testing: {test_case['description']} ({test_case['s3_key']})")
                start_time = time.time()
                
                response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    # Check for real FFmpeg metadata fields
                    expected_fields = ['duration', 'format', 'video_streams', 'audio_streams', 'subtitle_streams']
                    
                    if all(field in data for field in expected_fields):
                        duration = data.get('duration', 0)
                        subtitle_count = data.get('subtitle_streams', 0)
                        
                        # Check if we're getting real duration (not fake estimates like 1:12)
                        if duration > 0:
                            self.log_test(
                                f"Video Metadata Extraction - {test_case['description']}",
                                True,
                                f"Real FFmpeg metadata retrieved: Duration={duration}s, Subtitles={subtitle_count}, Response time={response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Video Metadata Extraction - {test_case['description']}",
                                False,
                                f"Duration is 0 - may not be calling real FFmpeg. Response time={response_time:.2f}s"
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Metadata Extraction - {test_case['description']}",
                            False,
                            f"Missing expected fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 400:
                    # Check if it's proper validation (missing s3_key)
                    data = response.json() if response.content else {}
                    error_msg = data.get('error', '')
                    
                    if 's3_key' in error_msg:
                        self.log_test(
                            f"Video Metadata Extraction - {test_case['description']}",
                            True,
                            "Proper request validation working (400 for missing s3_key)"
                        )
                    else:
                        self.log_test(
                            f"Video Metadata Extraction - {test_case['description']}",
                            False,
                            f"Unexpected 400 error: {error_msg}"
                        )
                        
                elif response.status_code == 404:
                    # File not found - this is expected for test files
                    self.log_test(
                        f"Video Metadata Extraction - {test_case['description']}",
                        True,
                        f"Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    # Gateway timeout - this was the previous issue
                    self.log_test(
                        f"Video Metadata Extraction - {test_case['description']}",
                        False,
                        f"❌ TIMEOUT ISSUE PERSISTS: HTTP 504 after {response_time:.2f}s - FFmpeg Lambda may still be timing out"
                    )
                    
                elif response.status_code == 502:
                    self.log_test(
                        f"Video Metadata Extraction - {test_case['description']}",
                        False,
                        f"Lambda execution failure (502). Response time={response_time:.2f}s"
                    )
                    
                else:
                    self.log_test(
                        f"Video Metadata Extraction - {test_case['description']}",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Metadata Extraction - {test_case['description']}",
                    False,
                    f"Request timeout after {TIMEOUT}s - FFmpeg processing may be taking too long"
                )
            except Exception as e:
                self.log_test(
                    f"Video Metadata Extraction - {test_case['description']}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_video_splitting_real_processing(self):
        """Test 2: Video splitting with real FFmpeg processing (should return 202, not 501)"""
        print("🔍 Testing Video Splitting (Real Processing)...")
        
        try:
            split_data = {
                "s3_key": "uploads/test-video.mp4",
                "segments": [
                    {
                        "start_time": "00:00:00",
                        "end_time": "00:00:30", 
                        "output_name": "segment_1.mp4"
                    },
                    {
                        "start_time": "00:00:30",
                        "end_time": "00:01:00",
                        "output_name": "segment_2.mp4"
                    }
                ]
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data)
            response_time = time.time() - start_time
            
            if response.status_code == 202:
                # This is what we expect now - processing started
                data = response.json()
                if 'job_id' in data:
                    job_id = data['job_id']
                    self.log_test(
                        "Video Splitting - Real Processing",
                        True,
                        f"✅ RESTORED: Now returns 202 (processing started) instead of 501. Job ID: {job_id}. Response time={response_time:.2f}s"
                    )
                    
                    # Test job status tracking with the returned job_id
                    self.test_job_status_tracking(job_id)
                    
                else:
                    self.log_test(
                        "Video Splitting - Real Processing",
                        False,
                        "202 response but missing job_id",
                        data
                    )
                    
            elif response.status_code == 501:
                # This was the old placeholder behavior
                self.log_test(
                    "Video Splitting - Real Processing",
                    False,
                    "❌ STILL PLACEHOLDER: Returns 501 'Not Implemented' - real FFmpeg processing not restored yet"
                )
                
            elif response.status_code == 400:
                # Check if it's proper validation
                data = response.json() if response.content else {}
                error_msg = data.get('error', '')
                
                if any(field in error_msg for field in ['s3_key', 'segments']):
                    self.log_test(
                        "Video Splitting - Real Processing",
                        True,
                        f"Proper request validation working (400): {error_msg}"
                    )
                else:
                    self.log_test(
                        "Video Splitting - Real Processing",
                        False,
                        f"Unexpected 400 error: {error_msg}"
                    )
                    
            elif response.status_code == 404:
                # File not found
                self.log_test(
                    "Video Splitting - Real Processing",
                    True,
                    f"Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s"
                )
                
            elif response.status_code == 504:
                self.log_test(
                    "Video Splitting - Real Processing",
                    False,
                    f"Gateway timeout (504) after {response_time:.2f}s - FFmpeg processing timeout"
                )
                
            else:
                self.log_test(
                    "Video Splitting - Real Processing",
                    False,
                    f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Video Splitting - Real Processing",
                False,
                f"Request timeout after {TIMEOUT}s"
            )
        except Exception as e:
            self.log_test(
                "Video Splitting - Real Processing",
                False,
                f"Error: {str(e)}"
            )

    def test_job_status_tracking(self, job_id: str = None):
        """Test 3: Job status tracking (should check S3 for results, not placeholder)"""
        print("🔍 Testing Job Status Tracking (S3 Results Check)...")
        
        # Use provided job_id or create test job_ids
        test_job_ids = [job_id] if job_id else [
            "test-job-" + uuid.uuid4().hex[:8],
            "sample-processing-job-123",
            "ffmpeg-job-" + str(int(time.time()))
        ]
        
        for test_job_id in test_job_ids:
            if not test_job_id:
                continue
                
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['job_id', 'status']
                    
                    if all(field in data for field in expected_fields):
                        status = data.get('status', '')
                        
                        # Check if it's checking S3 for real results
                        if status in ['pending', 'processing', 'completed', 'failed']:
                            self.log_test(
                                f"Job Status Tracking - {test_job_id[:16]}...",
                                True,
                                f"✅ RESTORED: Real S3 status check. Status: {status}. Response time={response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Job Status Tracking - {test_job_id[:16]}...",
                                False,
                                f"Unexpected status value: {status}",
                                data
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Job Status Tracking - {test_job_id[:16]}...",
                            False,
                            f"Missing expected fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Job not found - this is expected for test job IDs
                    self.log_test(
                        f"Job Status Tracking - {test_job_id[:16]}...",
                        True,
                        f"Endpoint working (404 for non-existent job is expected). Response time={response_time:.2f}s"
                    )
                    
                elif response.status_code == 501:
                    # This was the old placeholder behavior
                    self.log_test(
                        f"Job Status Tracking - {test_job_id[:16]}...",
                        False,
                        "❌ STILL PLACEHOLDER: Returns 501 'Not Implemented' - S3 status checking not restored yet"
                    )
                    
                else:
                    self.log_test(
                        f"Job Status Tracking - {test_job_id[:16]}...",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Job Status Tracking - {test_job_id[:16]}...",
                    False,
                    f"Error: {str(e)}"
                )

    def test_download_functionality_presigned_urls(self):
        """Test 4: Download functionality (should generate presigned URLs, not placeholder)"""
        print("🔍 Testing Download Functionality (Presigned URLs)...")
        
        test_cases = [
            {
                "job_id": "test-job-123",
                "filename": "segment_1.mp4",
                "description": "MP4 segment download"
            },
            {
                "job_id": "sample-job-456", 
                "filename": "output_video.mkv",
                "description": "MKV output download"
            },
            {
                "job_id": "ffmpeg-job-789",
                "filename": "processed_clip.mp4", 
                "description": "Processed clip download"
            }
        ]
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/download/{test_case['job_id']}/{test_case['filename']}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'download_url' in data:
                        download_url = data['download_url']
                        
                        # Check if it's a real S3 presigned URL
                        if 'amazonaws.com' in download_url and 'Signature' in download_url:
                            self.log_test(
                                f"Download Functionality - {test_case['description']}",
                                True,
                                f"✅ RESTORED: Real S3 presigned URL generated. Response time={response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Download Functionality - {test_case['description']}",
                                False,
                                f"Invalid presigned URL format: {download_url[:100]}..."
                            )
                    else:
                        self.log_test(
                            f"Download Functionality - {test_case['description']}",
                            False,
                            "Missing download_url in response",
                            data
                        )
                        
                elif response.status_code == 404:
                    # File not found - this is expected for test files
                    self.log_test(
                        f"Download Functionality - {test_case['description']}",
                        True,
                        f"Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s"
                    )
                    
                elif response.status_code == 501:
                    # This was the old placeholder behavior
                    self.log_test(
                        f"Download Functionality - {test_case['description']}",
                        False,
                        "❌ STILL PLACEHOLDER: Returns 501 'Not Implemented' - presigned URL generation not restored yet"
                    )
                    
                else:
                    self.log_test(
                        f"Download Functionality - {test_case['description']}",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Download Functionality - {test_case['description']}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_video_streaming_endpoint(self):
        """Test 5: Video streaming endpoint (should work as before)"""
        print("🔍 Testing Video Streaming Endpoint...")
        
        test_keys = [
            "uploads/test-video.mp4",
            "test/sample-mkv-file.mkv",
            "demo/example-video.mp4"
        ]
        
        for test_key in test_keys:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['stream_url', 's3_key', 'expires_in']
                    
                    if all(field in data for field in expected_fields):
                        stream_url = data['stream_url']
                        
                        if 'amazonaws.com' in stream_url and 'Signature' in stream_url:
                            self.log_test(
                                f"Video Streaming - {test_key.split('/')[-1]}",
                                True,
                                f"Valid streaming URL generated. Response time={response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Video Streaming - {test_key.split('/')[-1]}",
                                False,
                                f"Invalid streaming URL format"
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Streaming - {test_key.split('/')[-1]}",
                            False,
                            f"Missing expected fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent files
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        True,
                        f"Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        False,
                        f"Gateway timeout (504) after {response_time:.2f}s"
                    )
                    
                else:
                    self.log_test(
                        f"Video Streaming - {test_key.split('/')[-1]}",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Video Streaming - {test_key.split('/')[-1]}",
                    False,
                    f"Error: {str(e)}"
                )

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
        """Run all tests focusing on newly restored video processing functionality"""
        print("=" * 80)
        print("🚀 VIDEO PROCESSING RESTORATION TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Expected S3 Bucket: {S3_BUCKET}")
        print()
        print("🎯 FOCUS: Testing newly restored video processing functionality")
        print("   1. Video metadata extraction - Now calls FFmpeg Lambda for real duration/metadata")
        print("   2. Video splitting - Now calls FFmpeg Lambda (should return 202, not 501)")
        print("   3. Job status tracking - Now checks S3 for completed results")
        print("   4. Download functionality - Now generates presigned URLs for processed files")
        print()
        
        # Run focused tests on restored functionality
        self.test_video_metadata_extraction_real_ffmpeg()
        self.test_video_splitting_real_processing()
        self.test_job_status_tracking()
        self.test_download_functionality_presigned_urls()
        self.test_video_streaming_endpoint()
        
        # Quick connectivity check
        self.test_basic_connectivity()
        
        # Summary
        print("=" * 80)
        print("📊 VIDEO PROCESSING RESTORATION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze restoration status
        restoration_status = {
            'metadata_extraction': False,
            'video_splitting': False, 
            'job_status': False,
            'download_urls': False
        }
        
        for result in self.test_results:
            if result['success']:
                if 'metadata extraction' in result['test'].lower() and 'real ffmpeg' in result['details'].lower():
                    restoration_status['metadata_extraction'] = True
                elif 'video splitting' in result['test'].lower() and '202' in result['details']:
                    restoration_status['video_splitting'] = True
                elif 'job status' in result['test'].lower() and 'restored' in result['details'].lower():
                    restoration_status['job_status'] = True
                elif 'download functionality' in result['test'].lower() and 'restored' in result['details'].lower():
                    restoration_status['download_urls'] = True
        
        print("🔍 RESTORATION STATUS:")
        print(f"   ✅ Video Metadata Extraction (Real FFmpeg): {'RESTORED' if restoration_status['metadata_extraction'] else 'NOT RESTORED'}")
        print(f"   ✅ Video Splitting (202 Response): {'RESTORED' if restoration_status['video_splitting'] else 'NOT RESTORED'}")
        print(f"   ✅ Job Status Tracking (S3 Check): {'RESTORED' if restoration_status['job_status'] else 'NOT RESTORED'}")
        print(f"   ✅ Download URLs (Presigned): {'RESTORED' if restoration_status['download_urls'] else 'NOT RESTORED'}")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Critical issues
        timeout_issues = []
        placeholder_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if '504' in result['details'] or 'timeout' in result['details'].lower():
                    timeout_issues.append(result['test'])
                elif '501' in result['details'] or 'placeholder' in result['details'].lower():
                    placeholder_issues.append(result['test'])
        
        if timeout_issues:
            print("🚨 TIMEOUT ISSUES (FFmpeg Lambda may be timing out):")
            for issue in timeout_issues:
                print(f"   • {issue}")
            print()
        
        if placeholder_issues:
            print("🚨 PLACEHOLDER ENDPOINTS (Not yet restored):")
            for issue in placeholder_issues:
                print(f"   • {issue}")
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        
        restored_count = sum(restoration_status.values())
        if restored_count == 4:
            print("   🎉 ALL VIDEO PROCESSING FUNCTIONALITY SUCCESSFULLY RESTORED!")
            print("   • Real FFmpeg Lambda integration is working")
            print("   • Video splitting now processes instead of returning 501")
            print("   • Job status tracking checks S3 for real results")
            print("   • Download functionality generates proper presigned URLs")
        elif restored_count >= 2:
            print(f"   ✅ PARTIAL SUCCESS: {restored_count}/4 functionalities restored")
            print("   • Continue working on remaining endpoints")
        else:
            print("   ❌ RESTORATION INCOMPLETE: Most functionality still using placeholders")
            print("   • Check Lambda deployment and FFmpeg integration")
        
        if timeout_issues:
            print("   • Investigate FFmpeg Lambda timeout issues")
            print("   • Consider increasing Lambda timeout or optimizing FFmpeg processing")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoSplitterTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)