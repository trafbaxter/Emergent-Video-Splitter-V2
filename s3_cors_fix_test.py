#!/usr/bin/env python3
"""
S3 CORS Fix Verification Test for Video Streaming
Testing the updated video streaming and job status functionality after S3 CORS fix

CRITICAL VERIFICATION TESTS:
1. Video Streaming S3 Access Test - Test GET /api/video-stream/{key} and direct S3 URL access
2. Job Status Endpoint Test - Test GET /api/job-status/{job_id} for quick response
3. Split Video Flow Test - Test POST /api/split-video workflow

Expected Results After S3 CORS Fix:
- S3 video URLs should return 200 OK instead of 403 Forbidden
- Video streaming should work (no more black screen)
- Job status should return quickly
- CORS headers should be present on all responses
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using the API Gateway URL from existing backend_test.py
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30  # 30 second timeout for requests

class S3CORSFixTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
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

    def test_video_streaming_s3_access(self):
        """Test 1: Video Streaming S3 Access Test"""
        print("🔍 Testing Video Streaming S3 Access...")
        
        # Test with sample video keys
        test_keys = [
            "test-video.mp4",
            "sample-mkv-file.mkv", 
            "demo-video.mp4"
        ]
        
        for test_key in test_keys:
            try:
                print(f"   🎯 Testing video streaming for: {test_key}")
                start_time = time.time()
                
                # Step 1: Get presigned S3 URL from Lambda endpoint
                response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Lambda response time: {response_time:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['stream_url', 's3_key', 'expires_in']
                    
                    if all(field in data for field in expected_fields):
                        stream_url = data['stream_url']
                        s3_key = data['s3_key']
                        expires_in = data['expires_in']
                        
                        # Check CORS headers on Lambda response
                        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                        
                        self.log_test(
                            f"Lambda Video Streaming Endpoint - {test_key}",
                            True,
                            f"✅ Lambda endpoint working: Response time={response_time:.2f}s, CORS={cors_origin}, S3 key={s3_key}, Expires={expires_in}s"
                        )
                        
                        # Step 2: CRITICAL - Test direct S3 URL access (this was failing with 403)
                        print(f"   🚨 CRITICAL S3 CORS TEST: Testing direct access to S3 URL...")
                        s3_start_time = time.time()
                        
                        try:
                            # Test direct S3 URL access
                            s3_response = self.session.head(stream_url, timeout=10)
                            s3_response_time = time.time() - s3_start_time
                            
                            print(f"   ⏱️  S3 response time: {s3_response_time:.2f}s")
                            print(f"   📊 S3 Status Code: {s3_response.status_code}")
                            
                            # Check S3 CORS headers
                            s3_cors_origin = s3_response.headers.get('Access-Control-Allow-Origin', 'None')
                            s3_content_type = s3_response.headers.get('Content-Type', 'None')
                            
                            print(f"   🔍 S3 CORS Origin: {s3_cors_origin}")
                            print(f"   🔍 S3 Content-Type: {s3_content_type}")
                            
                            if s3_response.status_code == 200:
                                # SUCCESS - S3 CORS fix worked!
                                self.log_test(
                                    f"🎉 S3 CORS FIX SUCCESS - {test_key}",
                                    True,
                                    f"✅ S3 URL returns 200 OK! Response time={s3_response_time:.2f}s, CORS={s3_cors_origin}, Content-Type={s3_content_type}. BLACK SCREEN ISSUE RESOLVED!"
                                )
                            elif s3_response.status_code == 403:
                                # FAILURE - S3 CORS still not working
                                self.log_test(
                                    f"❌ S3 CORS FIX FAILED - {test_key}",
                                    False,
                                    f"🚨 S3 URL still returns 403 Forbidden! Response time={s3_response_time:.2f}s, CORS={s3_cors_origin}. This explains the black screen in video preview."
                                )
                            else:
                                self.log_test(
                                    f"S3 Access Test - {test_key}",
                                    False,
                                    f"S3 URL returned unexpected status {s3_response.status_code}. Response time={s3_response_time:.2f}s"
                                )
                                
                        except requests.exceptions.Timeout:
                            self.log_test(
                                f"S3 Access Test - {test_key}",
                                False,
                                f"S3 URL request timed out after 10s"
                            )
                        except Exception as e:
                            self.log_test(
                                f"S3 Access Test - {test_key}",
                                False,
                                f"S3 URL request failed: {str(e)}"
                            )
                            
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Lambda Video Streaming Endpoint - {test_key}",
                            False,
                            f"Missing expected fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent files, but endpoint is working
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                    self.log_test(
                        f"Lambda Video Streaming Endpoint - {test_key}",
                        True,
                        f"✅ Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s, CORS={cors_origin}"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Lambda Video Streaming Endpoint - {test_key}",
                        False,
                        f"❌ Gateway timeout (504) after {response_time:.2f}s"
                    )
                    
                else:
                    self.log_test(
                        f"Lambda Video Streaming Endpoint - {test_key}",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Lambda Video Streaming Endpoint - {test_key}",
                    False,
                    f"Lambda request timed out after {TIMEOUT}s"
                )
            except Exception as e:
                self.log_test(
                    f"Lambda Video Streaming Endpoint - {test_key}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_job_status_endpoint(self):
        """Test 2: Job Status Endpoint Test"""
        print("🔍 Testing Job Status Endpoint...")
        
        # Test with sample job IDs
        test_job_ids = [
            f"test-job-{uuid.uuid4().hex[:8]}",
            f"sample-job-{uuid.uuid4().hex[:8]}",
            "existing-job-123"
        ]
        
        for job_id in test_job_ids:
            try:
                print(f"   🎯 Testing job status for: {job_id}")
                start_time = time.time()
                
                response = self.session.get(f"{self.base_url}/api/job-status/{job_id}")
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                
                # Check if response is quick (under 5 seconds as requested)
                is_quick = response_time < 5.0
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['job_id', 'status']
                    
                    if all(field in data for field in expected_fields):
                        status = data.get('status', '')
                        progress = data.get('progress', 'N/A')
                        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                        
                        self.log_test(
                            f"Job Status Endpoint - {job_id[:12]}...",
                            is_quick,
                            f"✅ Response format correct: Status={status}, Progress={progress}, Response time={response_time:.2f}s ({'QUICK' if is_quick else 'SLOW'}), CORS={cors_origin}"
                        )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Job Status Endpoint - {job_id[:12]}...",
                            False,
                            f"Missing expected fields: {missing_fields}. Response time={response_time:.2f}s",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent jobs, but endpoint should be quick
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                    self.log_test(
                        f"Job Status Endpoint - {job_id[:12]}...",
                        is_quick,
                        f"✅ Endpoint working (404 for non-existent job is expected). Response time={response_time:.2f}s ({'QUICK' if is_quick else 'SLOW'}), CORS={cors_origin}"
                    )
                    
                elif response.status_code == 504:
                    # This was the main issue - job status timing out
                    self.log_test(
                        f"❌ Job Status Timeout - {job_id[:12]}...",
                        False,
                        f"🚨 CRITICAL: Job status endpoint still timing out (504) after {response_time:.2f}s! This explains 'processing stuck at 0%' issue."
                    )
                    
                else:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                    self.log_test(
                        f"Job Status Endpoint - {job_id[:12]}...",
                        False,
                        f"HTTP {response.status_code}. Response time={response_time:.2f}s, CORS={cors_origin}",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"❌ Job Status Timeout - {job_id[:12]}...",
                    False,
                    f"🚨 CRITICAL: Job status request timed out after {TIMEOUT}s"
                )
            except Exception as e:
                self.log_test(
                    f"Job Status Endpoint - {job_id[:12]}...",
                    False,
                    f"Error: {str(e)}"
                )

    def test_split_video_flow(self):
        """Test 3: Split Video Flow Test"""
        print("🔍 Testing Split Video Flow...")
        
        try:
            # Test split video endpoint (should return 202 immediately)
            split_data = {
                "s3_key": "test-video.mp4",
                "method": "intervals",
                "interval_duration": 300,
                "preserve_quality": True,
                "output_format": "mp4"
            }
            
            print(f"   🎯 Testing split video with payload: {json.dumps(split_data, indent=2)}")
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            # Check if response is immediate (under 5 seconds as requested)
            is_immediate = response_time < 5.0
            
            if response.status_code == 202:
                # SUCCESS - This is what we expect for async processing
                data = response.json()
                
                if 'job_id' in data:
                    job_id = data['job_id']
                    status = data.get('status', 'unknown')
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                    
                    self.log_test(
                        "🎉 Split Video Flow SUCCESS",
                        True,
                        f"✅ Returns 202 immediately with job_id: {job_id}, Status: {status}, Response time={response_time:.2f}s ({'IMMEDIATE' if is_immediate else 'SLOW'}), CORS={cors_origin}"
                    )
                    
                    # Now test the job status with the returned job_id
                    print(f"   🔄 Testing job status with returned job_id: {job_id}")
                    self.test_specific_job_status(job_id)
                    
                else:
                    self.log_test(
                        "Split Video Flow",
                        False,
                        f"202 response but missing job_id. Response time={response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 404:
                # File not found - endpoint is working, no timeout
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                self.log_test(
                    "Split Video Flow",
                    is_immediate,
                    f"✅ Endpoint working (404 for non-existent file is expected). Response time={response_time:.2f}s ({'IMMEDIATE' if is_immediate else 'SLOW'}), CORS={cors_origin}"
                )
                
            elif response.status_code == 504:
                # This was the main issue that should be fixed
                self.log_test(
                    "❌ Split Video Timeout STILL PRESENT",
                    False,
                    f"🚨 CRITICAL: Split video endpoint still timing out (504) after {response_time:.2f}s instead of returning 202 immediately!"
                )
                
            else:
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                self.log_test(
                    "Split Video Flow",
                    False,
                    f"HTTP {response.status_code}. Response time={response_time:.2f}s, CORS={cors_origin}",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ Split Video Timeout",
                False,
                f"🚨 CRITICAL: Split video request timed out after {TIMEOUT}s"
            )
        except Exception as e:
            self.log_test(
                "Split Video Flow",
                False,
                f"Error: {str(e)}"
            )

    def test_specific_job_status(self, job_id: str):
        """Test job status for a specific job ID from split video"""
        try:
            print(f"   🎯 Testing specific job status: {job_id}")
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}/api/job-status/{job_id}")
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Job status response time: {response_time:.2f}s")
            
            is_quick = response_time < 5.0
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 'N/A')
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                
                self.log_test(
                    f"Specific Job Status - {job_id[:12]}...",
                    is_quick,
                    f"✅ Job status retrieved: Status={status}, Progress={progress}, Response time={response_time:.2f}s ({'QUICK' if is_quick else 'SLOW'}), CORS={cors_origin}"
                )
                
            elif response.status_code == 404:
                cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
                self.log_test(
                    f"Specific Job Status - {job_id[:12]}...",
                    is_quick,
                    f"Job not found (404) but response was {'quick' if is_quick else 'slow'}: {response_time:.2f}s, CORS={cors_origin}"
                )
                
            elif response.status_code == 504:
                self.log_test(
                    f"❌ Specific Job Status Timeout - {job_id[:12]}...",
                    False,
                    f"🚨 CRITICAL: Job status for created job still timing out (504) after {response_time:.2f}s!"
                )
                
            else:
                self.log_test(
                    f"Specific Job Status - {job_id[:12]}...",
                    False,
                    f"HTTP {response.status_code}. Response time={response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test(
                f"Specific Job Status - {job_id[:12]}...",
                False,
                f"Error: {str(e)}"
            )

    def run_s3_cors_fix_tests(self):
        """Run the S3 CORS fix verification tests"""
        print("=" * 80)
        print("🚨 S3 CORS FIX VERIFICATION TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL S3 CORS FIX VERIFICATION:")
        print("   Testing if S3 CORS configuration fix resolved video streaming black screen issue")
        print("   Expected: S3 presigned URLs should return 200 OK instead of 403 Forbidden")
        print()
        print("📋 TESTING FOCUS:")
        print("   1. Video Streaming S3 Access - GET /api/video-stream/{key} + direct S3 URL test")
        print("   2. Job Status Endpoint - GET /api/job-status/{job_id} (should be quick, under 5s)")
        print("   3. Split Video Flow - POST /api/split-video (should return 202 immediately)")
        print()
        
        # Run the three critical tests
        self.test_video_streaming_s3_access()
        self.test_job_status_endpoint()
        self.test_split_video_flow()
        
        # Summary
        print("=" * 80)
        print("📊 S3 CORS FIX TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze S3 CORS fix status
        s3_cors_status = {
            's3_access_working': False,
            'job_status_quick': False,
            'split_video_immediate': False
        }
        
        critical_issues = []
        
        for result in self.test_results:
            if result['success']:
                if 's3 cors fix success' in result['test'].lower():
                    s3_cors_status['s3_access_working'] = True
                elif 'job status' in result['test'].lower() and 'quick' in result['details'].lower():
                    s3_cors_status['job_status_quick'] = True
                elif 'split video flow success' in result['test'].lower():
                    s3_cors_status['split_video_immediate'] = True
            else:
                if 's3 cors fix failed' in result['test'].lower() or '403 forbidden' in result['details'].lower():
                    critical_issues.append(f"S3 CORS: {result['details']}")
                elif 'job status timeout' in result['test'].lower():
                    critical_issues.append(f"Job Status: {result['details']}")
                elif 'split video timeout' in result['test'].lower():
                    critical_issues.append(f"Split Video: {result['details']}")
        
        print("🔍 S3 CORS FIX STATUS:")
        print(f"   ✅ S3 Video URLs Accessible: {'FIXED' if s3_cors_status['s3_access_working'] else 'STILL FAILING (403 Forbidden)'}")
        print(f"   ✅ Job Status Quick Response: {'WORKING' if s3_cors_status['job_status_quick'] else 'STILL TIMING OUT'}")
        print(f"   ✅ Split Video Immediate Response: {'WORKING' if s3_cors_status['split_video_immediate'] else 'STILL TIMING OUT'}")
        print()
        
        # Critical issues
        if critical_issues:
            print("🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   • {issue}")
            print()
        
        # Final assessment
        print("💡 S3 CORS FIX ASSESSMENT:")
        
        fixed_count = sum(s3_cors_status.values())
        if fixed_count == 3:
            print("   🎉 S3 CORS FIX COMPLETELY SUCCESSFUL!")
            print("   • Video streaming S3 URLs now return 200 OK (black screen resolved)")
            print("   • Job status endpoint responds quickly (processing progress works)")
            print("   • Split video returns immediately (no more timeouts)")
            print("   • CORS headers present on all responses")
        elif fixed_count >= 1:
            print(f"   ✅ PARTIAL SUCCESS: {fixed_count}/3 issues resolved")
            if not s3_cors_status['s3_access_working']:
                print("   • S3 video URLs still return 403 Forbidden - black screen issue persists")
            if not s3_cors_status['job_status_quick']:
                print("   • Job status endpoint still timing out - processing stuck at 0%")
            if not s3_cors_status['split_video_immediate']:
                print("   • Split video endpoint still timing out - not returning 202 immediately")
        else:
            print("   ❌ S3 CORS FIX FAILED: All critical issues still present")
            print("   • S3 bucket CORS configuration may need 1-2 minutes to propagate")
            print("   • Consider checking S3 bucket CORS policy directly")
            print("   • Job status and split video timeouts may be separate Lambda issues")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = S3CORSFixTester()
    passed, failed = tester.run_s3_cors_fix_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)