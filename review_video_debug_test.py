#!/usr/bin/env python3
"""
URGENT VIDEO DEBUG TEST - Review Request Focus
Testing the specific video preview and processing issues reported by user:

CRITICAL ISSUES TO INVESTIGATE:
1. Video Preview CORS Errors - black screen despite correct metadata
2. Video Processing Stuck at 0% - not progressing
3. S3 CORS Configuration - presigned URLs might not have proper CORS headers

SPECIFIC TESTS NEEDED:
1. Test GET /api/video-stream/{key} and verify S3 URL accessibility
2. Test /api/job-status/{job_id} with sample job_id
3. Check S3 bucket CORS configuration for video streaming
4. Verify Content-Type headers for MKV files
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30

class VideoDebugTester:
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

    def test_video_stream_endpoint_accessibility(self):
        """Test 1: Video streaming endpoint and S3 URL accessibility"""
        print("🔍 Testing Video Streaming Endpoint Accessibility...")
        
        test_keys = [
            "test-video.mp4",
            "sample-mkv-file.mkv", 
            "uploads/test-video.mp4",
            "demo/sample.mkv"
        ]
        
        for test_key in test_keys:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
                response_time = time.time() - start_time
                
                print(f"   🎯 Testing: {test_key}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📊 Status code: {response.status_code}")
                
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                print(f"   🌐 CORS Origin: {cors_origin}")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['stream_url', 's3_key', 'expires_in']
                    
                    if all(field in data for field in expected_fields):
                        stream_url = data['stream_url']
                        s3_key = data['s3_key']
                        expires_in = data['expires_in']
                        
                        print(f"   📁 S3 Key: {s3_key}")
                        print(f"   ⏰ Expires in: {expires_in}s")
                        print(f"   🔗 Stream URL: {stream_url[:100]}...")
                        
                        # Test if S3 URL is accessible from browser perspective
                        if 'amazonaws.com' in stream_url and 'Signature' in stream_url:
                            # Try to access the S3 URL directly
                            try:
                                s3_response = requests.head(stream_url, timeout=10)
                                s3_cors = s3_response.headers.get('Access-Control-Allow-Origin')
                                content_type = s3_response.headers.get('Content-Type')
                                
                                print(f"   🎬 S3 Direct Access: {s3_response.status_code}")
                                print(f"   🌐 S3 CORS: {s3_cors}")
                                print(f"   📄 Content-Type: {content_type}")
                                
                                if s3_response.status_code == 200:
                                    self.log_test(
                                        f"Video Stream Access - {test_key}",
                                        True,
                                        f"✅ S3 URL accessible! Status: {s3_response.status_code}, CORS: {s3_cors}, Content-Type: {content_type}, Response time: {response_time:.2f}s"
                                    )
                                else:
                                    self.log_test(
                                        f"Video Stream Access - {test_key}",
                                        False,
                                        f"❌ S3 URL not accessible: {s3_response.status_code}. This could cause black screen in video preview."
                                    )
                                    
                            except Exception as s3_error:
                                self.log_test(
                                    f"Video Stream Access - {test_key}",
                                    False,
                                    f"❌ S3 URL access failed: {str(s3_error)}. This could cause black screen in video preview."
                                )
                        else:
                            self.log_test(
                                f"Video Stream Access - {test_key}",
                                False,
                                f"❌ Invalid S3 URL format: {stream_url[:100]}..."
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Stream Access - {test_key}",
                            False,
                            f"❌ Missing fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent files, but endpoint is working
                    self.log_test(
                        f"Video Stream Access - {test_key}",
                        True,
                        f"✅ Endpoint working (404 for non-existent file is expected). Response time: {response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Video Stream Access - {test_key}",
                        False,
                        f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s. This explains user's 504 errors!"
                    )
                    
                else:
                    self.log_test(
                        f"Video Stream Access - {test_key}",
                        False,
                        f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Stream Access - {test_key}",
                    False,
                    f"❌ CRITICAL: Request timeout after {TIMEOUT}s. This explains user's timeout issues!"
                )
            except Exception as e:
                self.log_test(
                    f"Video Stream Access - {test_key}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_job_status_endpoint(self):
        """Test 2: Job status endpoint for video processing"""
        print("🔍 Testing Job Status Endpoint...")
        
        # Test with various job IDs to see if endpoint is working
        test_job_ids = [
            "test-job-123",
            "sample-job-456",
            str(uuid.uuid4()),  # Random UUID
            "processing-job-789"
        ]
        
        for job_id in test_job_ids:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/api/job-status/{job_id}")
                response_time = time.time() - start_time
                
                print(f"   🎯 Testing job ID: {job_id[:20]}...")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📊 Status code: {response.status_code}")
                
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                print(f"   🌐 CORS Origin: {cors_origin}")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['job_id', 'status']
                    
                    if all(field in data for field in expected_fields):
                        status = data.get('status', '')
                        progress = data.get('progress', 'N/A')
                        
                        print(f"   📊 Job Status: {status}")
                        print(f"   📈 Progress: {progress}")
                        
                        # Check if it's returning real status or placeholder
                        if status in ['pending', 'processing', 'completed', 'failed', 'accepted']:
                            self.log_test(
                                f"Job Status Check - {job_id[:12]}...",
                                True,
                                f"✅ Real job status returned: {status}, Progress: {progress}, Response time: {response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Job Status Check - {job_id[:12]}...",
                                False,
                                f"❌ Unexpected status: {status}. May be placeholder logic.",
                                data
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Job Status Check - {job_id[:12]}...",
                            False,
                            f"❌ Missing fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent jobs, but endpoint is working
                    self.log_test(
                        f"Job Status Check - {job_id[:12]}...",
                        True,
                        f"✅ Endpoint working (404 for non-existent job is expected). Response time: {response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Job Status Check - {job_id[:12]}...",
                        False,
                        f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s. This explains user's processing stuck at 0%!"
                    )
                    
                else:
                    self.log_test(
                        f"Job Status Check - {job_id[:12]}...",
                        False,
                        f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Job Status Check - {job_id[:12]}...",
                    False,
                    f"❌ CRITICAL: Request timeout after {TIMEOUT}s. This explains user's processing stuck at 0%!"
                )
            except Exception as e:
                self.log_test(
                    f"Job Status Check - {job_id[:12]}...",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_video_processing_split_endpoint(self):
        """Test 3: Video processing split endpoint"""
        print("🔍 Testing Video Processing Split Endpoint...")
        
        # Test with the exact payload format from user's scenario
        test_payload = {
            "s3_key": "test-video.mp4",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            print(f"   🎯 Testing split-video with payload: {json.dumps(test_payload, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=test_payload)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin: {cors_origin}")
            
            if response.status_code == 202:
                # This is what we expect for async processing
                data = response.json()
                if 'job_id' in data:
                    job_id = data['job_id']
                    status = data.get('status', 'unknown')
                    
                    print(f"   🆔 Job ID: {job_id}")
                    print(f"   📊 Status: {status}")
                    
                    self.log_test(
                        "Video Processing Split",
                        True,
                        f"✅ Processing started successfully! Job ID: {job_id}, Status: {status}, Response time: {response_time:.2f}s"
                    )
                    
                    # Test the job status with the returned job_id
                    self.test_specific_job_status(job_id)
                    
                else:
                    self.log_test(
                        "Video Processing Split",
                        False,
                        f"❌ 202 response but missing job_id. Response time: {response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 404:
                # File not found - endpoint is working
                self.log_test(
                    "Video Processing Split",
                    True,
                    f"✅ Endpoint working (404 for non-existent file is expected). Response time: {response_time:.2f}s"
                )
                
            elif response.status_code == 504:
                self.log_test(
                    "Video Processing Split",
                    False,
                    f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s. This explains user's processing stuck at 0%!"
                )
                
            else:
                self.log_test(
                    "Video Processing Split",
                    False,
                    f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Video Processing Split",
                False,
                f"❌ CRITICAL: Request timeout after {TIMEOUT}s. This explains user's processing stuck at 0%!"
            )
        except Exception as e:
            self.log_test(
                "Video Processing Split",
                False,
                f"❌ Error: {str(e)}"
            )

    def test_specific_job_status(self, job_id: str):
        """Test job status for a specific job ID returned from split-video"""
        print(f"   🔍 Testing specific job status: {job_id}")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/job-status/{job_id}")
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 'N/A')
                
                print(f"   📊 Job Status: {status}")
                print(f"   📈 Progress: {progress}")
                
                if status == 'processing' and progress == '0%':
                    self.log_test(
                        f"Specific Job Status - {job_id[:12]}...",
                        False,
                        f"❌ CRITICAL: Job stuck at 0% progress! This matches user's reported issue. Status: {status}, Progress: {progress}"
                    )
                else:
                    self.log_test(
                        f"Specific Job Status - {job_id[:12]}...",
                        True,
                        f"✅ Job status working: {status}, Progress: {progress}, Response time: {response_time:.2f}s"
                    )
            else:
                print(f"   ❌ Job status check failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Job status check error: {str(e)}")

    def test_cors_preflight_requests(self):
        """Test 4: CORS preflight requests for video endpoints"""
        print("🔍 Testing CORS Preflight Requests...")
        
        endpoints = [
            "/api/video-stream/test.mp4",
            "/api/job-status/test-job",
            "/api/split-video",
            "/api/get-video-info"
        ]
        
        for endpoint in endpoints:
            try:
                # Test OPTIONS request (CORS preflight)
                response = self.session.options(f"{self.base_url}{endpoint}")
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                print(f"   🎯 Testing: {endpoint}")
                print(f"   📊 Status: {response.status_code}")
                print(f"   🌐 CORS Headers: {cors_headers}")
                
                has_cors = any(cors_headers.values())
                origin_wildcard = cors_headers['Access-Control-Allow-Origin'] == '*'
                
                if has_cors and origin_wildcard:
                    self.log_test(
                        f"CORS Preflight - {endpoint.split('/')[-1]}",
                        True,
                        f"✅ CORS headers present with wildcard origin. Status: {response.status_code}"
                    )
                elif has_cors:
                    self.log_test(
                        f"CORS Preflight - {endpoint.split('/')[-1]}",
                        True,
                        f"✅ CORS headers present. Origin: {cors_headers['Access-Control-Allow-Origin']}"
                    )
                else:
                    self.log_test(
                        f"CORS Preflight - {endpoint.split('/')[-1]}",
                        False,
                        f"❌ Missing CORS headers. This could cause CORS policy errors in browser!"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"CORS Preflight - {endpoint.split('/')[-1]}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def test_video_metadata_endpoint(self):
        """Test 5: Video metadata endpoint for MKV files"""
        print("🔍 Testing Video Metadata Endpoint...")
        
        test_cases = [
            {
                "s3_key": "test-video.mp4",
                "description": "MP4 file metadata"
            },
            {
                "s3_key": "sample-mkv-file.mkv",
                "description": "MKV file metadata (should show subtitles)"
            }
        ]
        
        for test_case in test_cases:
            try:
                metadata_payload = {
                    "s3_key": test_case["s3_key"]
                }
                
                print(f"   🎯 Testing: {test_case['description']} ({test_case['s3_key']})")
                
                start_time = time.time()
                response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_payload)
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📊 Status code: {response.status_code}")
                
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                print(f"   🌐 CORS Origin: {cors_origin}")
                
                if response.status_code == 200:
                    data = response.json()
                    expected_fields = ['duration', 'format', 'video_streams', 'audio_streams', 'subtitle_streams']
                    
                    if all(field in data for field in expected_fields):
                        duration = data.get('duration', 0)
                        format_info = data.get('format', 'unknown')
                        subtitle_count = data.get('subtitle_streams', 0)
                        
                        print(f"   ⏱️  Duration: {duration}s")
                        print(f"   📄 Format: {format_info}")
                        print(f"   📝 Subtitles: {subtitle_count}")
                        
                        # Check if MKV files show correct subtitle count
                        if test_case['s3_key'].endswith('.mkv') and subtitle_count > 0:
                            self.log_test(
                                f"Video Metadata - {test_case['description']}",
                                True,
                                f"✅ MKV subtitle detection working! Duration: {duration}s, Format: {format_info}, Subtitles: {subtitle_count}, Response time: {response_time:.2f}s"
                            )
                        elif test_case['s3_key'].endswith('.mp4'):
                            self.log_test(
                                f"Video Metadata - {test_case['description']}",
                                True,
                                f"✅ MP4 metadata working! Duration: {duration}s, Format: {format_info}, Response time: {response_time:.2f}s"
                            )
                        else:
                            self.log_test(
                                f"Video Metadata - {test_case['description']}",
                                False,
                                f"❌ Metadata incomplete or incorrect. Duration: {duration}s, Subtitles: {subtitle_count}"
                            )
                    else:
                        missing_fields = [f for f in expected_fields if f not in data]
                        self.log_test(
                            f"Video Metadata - {test_case['description']}",
                            False,
                            f"❌ Missing fields: {missing_fields}",
                            data
                        )
                        
                elif response.status_code == 404:
                    # Expected for non-existent files
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        True,
                        f"✅ Endpoint working (404 for non-existent file is expected). Response time: {response_time:.2f}s"
                    )
                    
                elif response.status_code == 504:
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        False,
                        f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s. This could affect video preview metadata!"
                    )
                    
                else:
                    self.log_test(
                        f"Video Metadata - {test_case['description']}",
                        False,
                        f"❌ HTTP {response.status_code}. Response time: {response_time:.2f}s",
                        response.json() if response.content else {}
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Video Metadata - {test_case['description']}",
                    False,
                    f"❌ CRITICAL: Request timeout after {TIMEOUT}s. This could affect video preview!"
                )
            except Exception as e:
                self.log_test(
                    f"Video Metadata - {test_case['description']}",
                    False,
                    f"❌ Error: {str(e)}"
                )

    def run_review_debug_tests(self):
        """Run focused tests based on user's review request"""
        print("=" * 80)
        print("🚨 URGENT: VIDEO DEBUG TESTING - Review Request Focus")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 USER REPORTED ISSUES:")
        print("   1. Video preview shows black screen despite correct metadata")
        print("   2. Console shows CORS policy errors for fetch requests")
        print("   3. 504 Gateway Timeout errors are occurring")
        print("   4. Video processing stuck at 0% and not progressing")
        print("   5. S3 streaming URLs from /api/video-stream endpoint issues")
        print()
        print("📋 TESTING FOCUS:")
        print("   1. GET /api/video-stream/{key} - S3 URL accessibility")
        print("   2. GET /api/job-status/{job_id} - Job status tracking")
        print("   3. POST /api/split-video - Video processing initiation")
        print("   4. CORS configuration for video streaming")
        print("   5. Content-Type headers for MKV files")
        print()
        
        # Run focused debug tests
        self.test_video_stream_endpoint_accessibility()
        self.test_job_status_endpoint()
        self.test_video_processing_split_endpoint()
        self.test_cors_preflight_requests()
        self.test_video_metadata_endpoint()
        
        # Summary
        print("=" * 80)
        print("📊 VIDEO DEBUG TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze specific issues
        critical_issues = []
        timeout_issues = []
        cors_issues = []
        s3_access_issues = []
        
        for result in self.test_results:
            if not result['success']:
                details = result['details'].lower()
                if '504' in details or 'timeout' in details:
                    timeout_issues.append(result)
                if 'cors' in details:
                    cors_issues.append(result)
                if 's3' in details and 'not accessible' in details:
                    s3_access_issues.append(result)
                if 'critical' in details:
                    critical_issues.append(result)
        
        print("🔍 ISSUE ANALYSIS:")
        
        if timeout_issues:
            print(f"   🚨 TIMEOUT ISSUES ({len(timeout_issues)} found):")
            for issue in timeout_issues:
                print(f"      • {issue['test']}: {issue['details']}")
            print()
        
        if cors_issues:
            print(f"   🌐 CORS ISSUES ({len(cors_issues)} found):")
            for issue in cors_issues:
                print(f"      • {issue['test']}: {issue['details']}")
            print()
        
        if s3_access_issues:
            print(f"   📁 S3 ACCESS ISSUES ({len(s3_access_issues)} found):")
            for issue in s3_access_issues:
                print(f"      • {issue['test']}: {issue['details']}")
            print()
        
        # Root cause analysis
        print("💡 ROOT CAUSE ANALYSIS:")
        
        if timeout_issues:
            print("   🚨 TIMEOUT PROBLEMS DETECTED:")
            print("      - Video streaming endpoints timing out (504 Gateway Timeout)")
            print("      - This explains user's black screen in video preview")
            print("      - Video processing stuck at 0% due to timeout issues")
            print("      - Recommendation: Check Lambda function timeout settings")
            print()
        
        if s3_access_issues:
            print("   📁 S3 ACCESS PROBLEMS DETECTED:")
            print("      - S3 presigned URLs not accessible from browser")
            print("      - This explains user's black screen in video preview")
            print("      - Recommendation: Check S3 bucket CORS configuration")
            print()
        
        if cors_issues:
            print("   🌐 CORS PROBLEMS DETECTED:")
            print("      - Missing or incorrect CORS headers")
            print("      - This explains user's CORS policy errors in console")
            print("      - Recommendation: Fix CORS configuration in Lambda function")
            print()
        
        # Final assessment
        print("🎯 FINAL ASSESSMENT:")
        
        if failed_tests == 0:
            print("   ✅ ALL TESTS PASSED - Video functionality appears to be working correctly")
            print("   • User's issues may be browser-specific or network-related")
            print("   • Recommend checking browser console for specific error messages")
        elif timeout_issues:
            print("   ❌ CRITICAL TIMEOUT ISSUES CONFIRMED")
            print("   • Video streaming endpoints are timing out")
            print("   • This directly explains user's reported issues:")
            print("     - Black screen in video preview (S3 URLs not accessible)")
            print("     - Video processing stuck at 0% (endpoints timing out)")
            print("     - 504 Gateway Timeout errors in console")
        elif s3_access_issues:
            print("   ❌ S3 ACCESS ISSUES CONFIRMED")
            print("   • S3 presigned URLs are not accessible from browser")
            print("   • This explains user's black screen in video preview")
            print("   • Recommendation: Fix S3 bucket CORS configuration")
        else:
            print(f"   ⚠️  PARTIAL ISSUES DETECTED ({failed_tests}/{total_tests} failures)")
            print("   • Some video functionality is working, but issues remain")
            print("   • Review individual test failures for specific problems")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoDebugTester()
    passed, failed = tester.run_review_debug_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)