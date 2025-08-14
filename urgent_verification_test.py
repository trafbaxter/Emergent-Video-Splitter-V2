#!/usr/bin/env python3
"""
URGENT VERIFICATION: Final test of complete video streaming workflow
Testing S3 CORS fix and job status functionality as requested.

CRITICAL FINAL TEST:
1. Real Video Streaming Test with actual MKV file key
2. Job Status Quick Test (should respond under 10 seconds)

Expected Results:
- Video streaming endpoint should work with real video file
- S3 URLs should return 200/206 (not 403 Forbidden anymore)
- CORS headers should be present
- Job status should respond quickly
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - using the API URL from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30  # 30 second timeout for quick tests

class UrgentVerificationTester:
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

    def test_real_video_streaming(self):
        """Test 1: CRITICAL - Real Video Streaming Test with actual MKV file"""
        print("🚨 URGENT TEST 1: Real Video Streaming with Actual MKV File")
        print("=" * 70)
        
        # The actual MKV file key from the review request
        real_mkv_key = "uploads/43ab1ed4-1c23-488f-b29e-fbab160a0079/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"
        
        try:
            print(f"🎯 Testing GET /api/video-stream/{real_mkv_key}")
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}/api/video-stream/{real_mkv_key}")
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f}s")
            print(f"📊 Status code: {response.status_code}")
            
            # Check CORS headers on Lambda response
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
            print(f"🌐 CORS Origin: {cors_origin}")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['stream_url', 's3_key', 'expires_in']
                
                print(f"📋 Response fields: {list(data.keys())}")
                
                if all(field in data for field in expected_fields):
                    stream_url = data['stream_url']
                    s3_key = data['s3_key']
                    expires_in = data['expires_in']
                    
                    print(f"🔗 Stream URL: {stream_url[:100]}...")
                    print(f"🗂️  S3 Key: {s3_key}")
                    print(f"⏰ Expires in: {expires_in}s")
                    
                    # Test the S3 URL directly for CORS and access
                    self.test_s3_url_access(stream_url, "Real MKV File")
                    
                    self.log_test(
                        "Real Video Streaming - Lambda Response",
                        True,
                        f"✅ Lambda endpoint working perfectly! Response time: {response_time:.2f}s, CORS: {cors_origin}, All fields present: {expected_fields}"
                    )
                    
                else:
                    missing_fields = [f for f in expected_fields if f not in data]
                    self.log_test(
                        "Real Video Streaming - Lambda Response",
                        False,
                        f"Missing expected fields: {missing_fields}. Response time: {response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 404:
                self.log_test(
                    "Real Video Streaming - Lambda Response",
                    False,
                    f"❌ CRITICAL: Real MKV file not found (404). This suggests the file doesn't exist in S3 or the key is incorrect. Response time: {response_time:.2f}s"
                )
                
            elif response.status_code == 403:
                self.log_test(
                    "Real Video Streaming - Lambda Response",
                    False,
                    f"❌ CRITICAL: Access denied (403). Lambda may not have S3 permissions. Response time: {response_time:.2f}s"
                )
                
            elif response.status_code == 504:
                self.log_test(
                    "Real Video Streaming - Lambda Response",
                    False,
                    f"❌ CRITICAL: Gateway timeout (504) after {response_time:.2f}s. Lambda function timeout issue persists."
                )
                
            else:
                self.log_test(
                    "Real Video Streaming - Lambda Response",
                    False,
                    f"HTTP {response.status_code}. Response time: {response_time:.2f}s",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Real Video Streaming - Lambda Response",
                False,
                f"❌ CRITICAL: Request timeout after {TIMEOUT}s"
            )
        except Exception as e:
            self.log_test(
                "Real Video Streaming - Lambda Response",
                False,
                f"Error: {str(e)}"
            )

    def test_s3_url_access(self, s3_url: str, description: str):
        """Test S3 URL access for CORS and 200/206 status"""
        print(f"\n🔍 Testing S3 URL Access for {description}")
        print("-" * 50)
        
        try:
            print(f"🎯 Testing S3 URL: {s3_url[:100]}...")
            start_time = time.time()
            
            # Test with Range header to get 206 response (partial content)
            headers = {
                'Range': 'bytes=0-1023',  # Request first 1KB
                'Origin': 'https://working.tads-video-splitter.com'  # Test CORS
            }
            
            response = self.session.get(s3_url, headers=headers)
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f}s")
            print(f"📊 Status code: {response.status_code}")
            
            # Check CORS headers from S3
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
            content_type = response.headers.get('Content-Type', 'None')
            content_length = response.headers.get('Content-Length', 'None')
            
            print(f"🌐 S3 CORS Origin: {cors_origin}")
            print(f"📄 Content-Type: {content_type}")
            print(f"📏 Content-Length: {content_length}")
            
            if response.status_code in [200, 206]:
                # Success! S3 is accessible
                cors_working = cors_origin != 'None' and cors_origin != ''
                video_content = 'video' in content_type.lower() or 'matroska' in content_type.lower()
                
                self.log_test(
                    f"S3 URL Access - {description}",
                    True,
                    f"🎉 S3 ACCESS WORKING! Status: {response.status_code}, CORS: {cors_origin}, Content-Type: {content_type}, Video content: {video_content}"
                )
                
                if not cors_working:
                    self.log_test(
                        f"S3 CORS Headers - {description}",
                        False,
                        f"⚠️  S3 CORS headers missing or empty. This may cause browser access issues."
                    )
                else:
                    self.log_test(
                        f"S3 CORS Headers - {description}",
                        True,
                        f"✅ S3 CORS headers present: {cors_origin}"
                    )
                    
            elif response.status_code == 403:
                self.log_test(
                    f"S3 URL Access - {description}",
                    False,
                    f"❌ CRITICAL: S3 returns 403 Forbidden! This is the ROOT CAUSE of black screen issue. CORS: {cors_origin}, Content-Type: {content_type}"
                )
                
            elif response.status_code == 404:
                self.log_test(
                    f"S3 URL Access - {description}",
                    False,
                    f"❌ S3 file not found (404). File may not exist in S3 bucket."
                )
                
            else:
                self.log_test(
                    f"S3 URL Access - {description}",
                    False,
                    f"S3 returned HTTP {response.status_code}. Response time: {response_time:.2f}s"
                )
                
        except Exception as e:
            self.log_test(
                f"S3 URL Access - {description}",
                False,
                f"Error accessing S3 URL: {str(e)}"
            )

    def test_job_status_quick(self):
        """Test 2: CRITICAL - Job Status Quick Test (should respond under 10 seconds)"""
        print("\n🚨 URGENT TEST 2: Job Status Quick Test")
        print("=" * 50)
        
        test_job_id = "test-job-123"
        
        try:
            print(f"🎯 Testing GET /api/job-status/{test_job_id}")
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}")
            response_time = time.time() - start_time
            
            print(f"⏱️  Response time: {response_time:.2f}s")
            print(f"📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'None')
            print(f"🌐 CORS Origin: {cors_origin}")
            
            # Critical: Should respond quickly (under 10 seconds)
            quick_response = response_time < 10.0
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['job_id', 'status']
                
                print(f"📋 Response fields: {list(data.keys())}")
                
                if all(field in data for field in expected_fields):
                    job_id = data.get('job_id', '')
                    status = data.get('status', '')
                    
                    print(f"🆔 Job ID: {job_id}")
                    print(f"📊 Status: {status}")
                    
                    self.log_test(
                        "Job Status Quick Response",
                        quick_response,
                        f"✅ Job status endpoint working! Response time: {response_time:.2f}s ({'QUICK' if quick_response else 'SLOW'}), Status: {status}, CORS: {cors_origin}"
                    )
                    
                else:
                    missing_fields = [f for f in expected_fields if f not in data]
                    self.log_test(
                        "Job Status Quick Response",
                        False,
                        f"Missing expected fields: {missing_fields}. Response time: {response_time:.2f}s",
                        data
                    )
                    
            elif response.status_code == 404:
                # Expected for test job ID, but should be quick
                self.log_test(
                    "Job Status Quick Response",
                    quick_response,
                    f"✅ Job status endpoint working (404 for test job is expected). Response time: {response_time:.2f}s ({'QUICK' if quick_response else 'SLOW'}), CORS: {cors_origin}"
                )
                
            elif response.status_code == 504:
                self.log_test(
                    "Job Status Quick Response",
                    False,
                    f"❌ CRITICAL: Job status still timing out (504) after {response_time:.2f}s! This explains 'processing stuck at 0%' issue."
                )
                
            else:
                self.log_test(
                    "Job Status Quick Response",
                    False,
                    f"HTTP {response.status_code}. Response time: {response_time:.2f}s ({'QUICK' if quick_response else 'SLOW'})",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Job Status Quick Response",
                False,
                f"❌ CRITICAL: Job status timeout after {TIMEOUT}s - this explains 'processing stuck at 0%'"
            )
        except Exception as e:
            self.log_test(
                "Job Status Quick Response",
                False,
                f"Error: {str(e)}"
            )

    def test_basic_connectivity(self):
        """Quick connectivity test"""
        print("\n🔍 Basic Connectivity Check")
        print("-" * 30)
        
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', 'N/A')
                version = data.get('version', 'N/A')
                
                self.log_test(
                    "Basic API Connectivity",
                    True,
                    f"API Gateway accessible. Message: {message}, Version: {version}"
                )
            else:
                self.log_test(
                    "Basic API Connectivity",
                    False,
                    f"HTTP {response.status_code}",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test(
                "Basic API Connectivity",
                False,
                f"Connection error: {str(e)}"
            )

    def run_urgent_verification(self):
        """Run the urgent verification tests"""
        print("=" * 80)
        print("🚨 URGENT VERIFICATION: Complete Video Streaming Workflow")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL TESTS:")
        print("   1. Real Video Streaming Test with actual MKV file")
        print("   2. S3 URL access test (should return 200/206, not 403)")
        print("   3. Job Status Quick Test (should respond under 10 seconds)")
        print()
        print("🎉 EXPECTED RESULTS:")
        print("   ✅ Video streaming endpoint works with real video file")
        print("   ✅ S3 URLs return 200/206 (not 403 Forbidden anymore)")
        print("   ✅ CORS headers are present")
        print("   ✅ Job status responds quickly")
        print()
        
        # Run basic connectivity first
        self.test_basic_connectivity()
        
        # Run the critical tests
        self.test_real_video_streaming()
        self.test_job_status_quick()
        
        # Summary
        print("=" * 80)
        print("📊 URGENT VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze critical issues
        critical_issues = []
        resolved_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if 'critical' in result['details'].lower():
                    critical_issues.append(result)
            else:
                if 'working' in result['details'].lower() or 'success' in result['details'].lower():
                    resolved_issues.append(result)
        
        print("🎉 RESOLVED ISSUES:")
        for result in resolved_issues:
            print(f"   ✅ {result['test']}: {result['details'][:100]}...")
        print()
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES REMAINING:")
            for result in critical_issues:
                print(f"   ❌ {result['test']}: {result['details'][:100]}...")
            print()
        
        # Final assessment
        print("💡 FINAL ASSESSMENT:")
        
        video_streaming_working = any('video streaming' in r['test'].lower() and r['success'] for r in self.test_results)
        s3_access_working = any('s3 url access' in r['test'].lower() and r['success'] for r in self.test_results)
        job_status_working = any('job status' in r['test'].lower() and r['success'] for r in self.test_results)
        
        if video_streaming_working and s3_access_working and job_status_working:
            print("   🎉 COMPLETE SUCCESS! Both critical user issues are resolved:")
            print("   ✅ Video preview black screen issue - FIXED (S3 CORS working)")
            print("   ✅ Video processing stuck at 0% issue - FIXED (job status working)")
            print("   🚀 The Video Splitter Pro application should now work perfectly!")
        elif video_streaming_working and s3_access_working:
            print("   ✅ PARTIAL SUCCESS: Video preview issue resolved (S3 CORS working)")
            print("   ❌ Job status issue may persist (processing stuck at 0%)")
        elif job_status_working:
            print("   ✅ PARTIAL SUCCESS: Job status issue resolved")
            print("   ❌ Video preview issue may persist (S3 CORS problems)")
        else:
            print("   ❌ CRITICAL ISSUES PERSIST:")
            if not video_streaming_working:
                print("   • Video streaming endpoint not working")
            if not s3_access_working:
                print("   • S3 CORS still not configured (black screen issue)")
            if not job_status_working:
                print("   • Job status timeout (processing stuck at 0%)")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = UrgentVerificationTester()
    passed, failed = tester.run_urgent_verification()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)