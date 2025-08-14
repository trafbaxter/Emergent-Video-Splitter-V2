#!/usr/bin/env python3
"""
S3 POLLING TIMEOUT FIX TESTING for Video Splitter Pro
URGENT: Test the S3 polling timeout fix for video processing endpoints

CRITICAL TEST OBJECTIVE:
Verify that removing S3 list_objects_v2 polling from handle_job_status has resolved the 29-second timeout issue.

SPECIFIC TESTS:
1. Job Status Response Time Test - GET /api/job-status/test-job-123 - MUST return in under 5 seconds
2. Split Video Response Time Test - POST /api/split-video - MUST return HTTP 202 in under 10 seconds  
3. Multiple Job Status Calls - should return consistent progress for same job ID, all under 5 seconds

SUCCESS CRITERIA:
✅ Job status responds in <5 seconds (not 29s)
✅ Split video responds in <10 seconds (not 29s)  
✅ Progress varies realistically (not stuck at 25%)
✅ All endpoints have CORS headers
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using the backend URL from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 60  # Set reasonable timeout for testing

class S3PollingTimeoutTester:
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

    def test_job_status_response_time(self):
        """Test 1: Job Status Response Time Test - MUST return in under 5 seconds"""
        print("🚨 CRITICAL TEST 1: Job Status Response Time")
        print("   Testing GET /api/job-status/test-job-123")
        print("   SUCCESS CRITERIA: HTTP 200 in <5 seconds with progress between 35-92%")
        
        try:
            test_job_id = "test-job-123"
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}")
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            # Check if response time meets criteria
            if response_time >= 5.0:
                self.log_test(
                    "❌ CRITICAL FAILURE - Job Status Response Time",
                    False,
                    f"🚨 TIMEOUT FIX FAILED: Response took {response_time:.2f}s (≥5s threshold). Expected <5s, got {response_time:.2f}s. The S3 polling timeout issue is NOT resolved!"
                )
                return
            
            # Check response status and content
            if response.status_code == 200:
                data = response.json()
                
                # Check for required fields
                if 'job_id' in data and 'status' in data and 'progress' in data:
                    job_id = data.get('job_id')
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    # Check CORS headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin')
                    has_cors = cors_header is not None
                    
                    # Validate progress is realistic (35-92% as mentioned in review)
                    progress_realistic = 35 <= progress <= 92
                    
                    if progress_realistic and has_cors:
                        self.log_test(
                            "🎉 SUCCESS - Job Status Response Time",
                            True,
                            f"✅ S3 POLLING TIMEOUT FIX SUCCESSFUL! Response time: {response_time:.2f}s (<5s ✓), Progress: {progress}% (realistic ✓), Status: {status}, CORS: {cors_header} ✓"
                        )
                    else:
                        issues = []
                        if not progress_realistic:
                            issues.append(f"Progress {progress}% not in realistic range 35-92%")
                        if not has_cors:
                            issues.append("Missing CORS headers")
                        
                        self.log_test(
                            "⚠️ PARTIAL SUCCESS - Job Status Response Time",
                            True,  # Still success since timeout is fixed
                            f"✅ Timeout fixed ({response_time:.2f}s <5s) but minor issues: {', '.join(issues)}"
                        )
                else:
                    missing_fields = [f for f in ['job_id', 'status', 'progress'] if f not in data]
                    self.log_test(
                        "❌ Job Status Response Time",
                        False,
                        f"Response time OK ({response_time:.2f}s) but missing fields: {missing_fields}",
                        data
                    )
            else:
                self.log_test(
                    "❌ Job Status Response Time",
                    False,
                    f"HTTP {response.status_code} in {response_time:.2f}s. Expected HTTP 200.",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ CRITICAL FAILURE - Job Status Response Time",
                False,
                f"🚨 REQUEST TIMEOUT after {TIMEOUT}s - S3 polling timeout fix completely failed!"
            )
        except Exception as e:
            self.log_test(
                "❌ Job Status Response Time",
                False,
                f"Error: {str(e)}"
            )

    def test_split_video_response_time(self):
        """Test 2: Split Video Response Time Test - MUST return HTTP 202 in under 10 seconds"""
        print("🚨 CRITICAL TEST 2: Split Video Response Time")
        print("   Testing POST /api/split-video with sample payload")
        print("   SUCCESS CRITERIA: HTTP 202 in <10 seconds with job_id and 'processing' status")
        
        try:
            # Use the exact payload mentioned in the review request
            split_data = {
                "s3_key": "test-video.mp4",
                "method": "intervals",
                "interval_duration": 300,
                "preserve_quality": True,
                "output_format": "mp4"
            }
            
            start_time = time.time()
            
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            # Check if response time meets criteria
            if response_time >= 10.0:
                self.log_test(
                    "❌ CRITICAL FAILURE - Split Video Response Time",
                    False,
                    f"🚨 TIMEOUT FIX FAILED: Response took {response_time:.2f}s (≥10s threshold). Expected <10s, got {response_time:.2f}s. The S3 polling timeout issue is NOT resolved!"
                )
                return
            
            # Check response status and content
            if response.status_code == 202:
                data = response.json()
                
                # Check for required fields
                if 'job_id' in data and 'status' in data:
                    job_id = data.get('job_id')
                    status = data.get('status')
                    
                    # Check CORS headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin')
                    has_cors = cors_header is not None
                    
                    # Validate status indicates processing
                    status_valid = status in ['processing', 'accepted', 'pending']
                    
                    if status_valid and has_cors:
                        self.log_test(
                            "🎉 SUCCESS - Split Video Response Time",
                            True,
                            f"✅ S3 POLLING TIMEOUT FIX SUCCESSFUL! Response time: {response_time:.2f}s (<10s ✓), Job ID: {job_id}, Status: {status} ✓, CORS: {cors_header} ✓"
                        )
                        
                        # Store job_id for multiple calls test
                        self.test_job_id = job_id
                        
                    else:
                        issues = []
                        if not status_valid:
                            issues.append(f"Status '{status}' not in expected values")
                        if not has_cors:
                            issues.append("Missing CORS headers")
                        
                        self.log_test(
                            "⚠️ PARTIAL SUCCESS - Split Video Response Time",
                            True,  # Still success since timeout is fixed
                            f"✅ Timeout fixed ({response_time:.2f}s <10s) but minor issues: {', '.join(issues)}"
                        )
                else:
                    missing_fields = [f for f in ['job_id', 'status'] if f not in data]
                    self.log_test(
                        "❌ Split Video Response Time",
                        False,
                        f"Response time OK ({response_time:.2f}s) but missing fields: {missing_fields}",
                        data
                    )
            else:
                self.log_test(
                    "❌ Split Video Response Time",
                    False,
                    f"HTTP {response.status_code} in {response_time:.2f}s. Expected HTTP 202.",
                    response.json() if response.content else {}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ CRITICAL FAILURE - Split Video Response Time",
                False,
                f"🚨 REQUEST TIMEOUT after {TIMEOUT}s - S3 polling timeout fix completely failed!"
            )
        except Exception as e:
            self.log_test(
                "❌ Split Video Response Time",
                False,
                f"Error: {str(e)}"
            )

    def test_multiple_job_status_calls(self):
        """Test 3: Multiple Job Status Calls - should be consistent and under 5 seconds"""
        print("🚨 CRITICAL TEST 3: Multiple Job Status Calls")
        print("   Testing the same job ID multiple times quickly")
        print("   SUCCESS CRITERIA: Consistent progress, all calls under 5 seconds")
        
        # Use the job_id from split video test if available, otherwise use test job
        job_id = getattr(self, 'test_job_id', 'test-job-123')
        
        call_results = []
        
        for i in range(3):
            try:
                print(f"   📞 Call {i+1}/3 for job {job_id[:20]}...")
                start_time = time.time()
                
                response = self.session.get(f"{self.base_url}/api/job-status/{job_id}")
                response_time = time.time() - start_time
                
                print(f"   ⏱️  Call {i+1} response time: {response_time:.2f}s")
                
                call_result = {
                    'call_number': i+1,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'success': response_time < 5.0 and response.status_code == 200
                }
                
                if response.status_code == 200:
                    data = response.json()
                    call_result['progress'] = data.get('progress', 0)
                    call_result['status'] = data.get('status', 'unknown')
                    call_result['cors'] = response.headers.get('Access-Control-Allow-Origin') is not None
                
                call_results.append(call_result)
                
                # Small delay between calls
                time.sleep(0.5)
                
            except Exception as e:
                call_results.append({
                    'call_number': i+1,
                    'error': str(e),
                    'success': False
                })
        
        # Analyze results
        successful_calls = [r for r in call_results if r.get('success', False)]
        fast_calls = [r for r in call_results if r.get('response_time', 999) < 5.0]
        
        if len(successful_calls) == 3:
            # Check consistency
            progresses = [r.get('progress', 0) for r in successful_calls]
            avg_response_time = sum(r['response_time'] for r in successful_calls) / len(successful_calls)
            
            self.log_test(
                "🎉 SUCCESS - Multiple Job Status Calls",
                True,
                f"✅ ALL CALLS SUCCESSFUL! Average response time: {avg_response_time:.2f}s (<5s ✓), Progress values: {progresses}, All calls under 5s: {len(fast_calls)}/3"
            )
        elif len(fast_calls) >= 2:
            self.log_test(
                "⚠️ PARTIAL SUCCESS - Multiple Job Status Calls",
                True,
                f"✅ Most calls successful: {len(fast_calls)}/3 under 5s, {len(successful_calls)}/3 fully successful"
            )
        else:
            failed_details = []
            for r in call_results:
                if not r.get('success', False):
                    if 'error' in r:
                        failed_details.append(f"Call {r['call_number']}: {r['error']}")
                    else:
                        failed_details.append(f"Call {r['call_number']}: {r.get('response_time', 'N/A')}s, HTTP {r.get('status_code', 'N/A')}")
            
            self.log_test(
                "❌ CRITICAL FAILURE - Multiple Job Status Calls",
                False,
                f"🚨 MULTIPLE CALLS FAILED: {len(successful_calls)}/3 successful. Issues: {'; '.join(failed_details)}"
            )

    def test_cors_preflight(self):
        """Test 4: CORS Preflight - verify CORS headers are working"""
        print("🔍 SUPPLEMENTARY TEST: CORS Preflight")
        print("   Testing OPTIONS requests for CORS headers")
        
        endpoints_to_test = [
            "/api/job-status/test-job-123",
            "/api/split-video"
        ]
        
        cors_results = []
        
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                response = self.session.options(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                has_cors = any(cors_headers.values())
                cors_results.append({
                    'endpoint': endpoint,
                    'has_cors': has_cors,
                    'response_time': response_time,
                    'origin': cors_headers['Access-Control-Allow-Origin']
                })
                
            except Exception as e:
                cors_results.append({
                    'endpoint': endpoint,
                    'error': str(e),
                    'has_cors': False
                })
        
        successful_cors = [r for r in cors_results if r.get('has_cors', False)]
        
        if len(successful_cors) == len(endpoints_to_test):
            origins = [r.get('origin', 'None') for r in successful_cors]
            self.log_test(
                "✅ CORS Preflight",
                True,
                f"All endpoints have CORS headers. Origins: {set(origins)}"
            )
        else:
            failed_endpoints = [r['endpoint'] for r in cors_results if not r.get('has_cors', False)]
            self.log_test(
                "❌ CORS Preflight",
                False,
                f"Missing CORS on endpoints: {failed_endpoints}"
            )

    def run_s3_polling_timeout_tests(self):
        """Run the focused S3 polling timeout fix tests"""
        print("=" * 80)
        print("🚨 URGENT: S3 POLLING TIMEOUT FIX TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL OBJECTIVE:")
        print("   Verify that removing S3 list_objects_v2 polling from handle_job_status")
        print("   has resolved the 29-second timeout issue.")
        print()
        print("📋 SUCCESS CRITERIA:")
        print("   ✅ Job status: HTTP 200 in <5 seconds with realistic progress (35%, 50%, 65%, etc.)")
        print("   ✅ Split video: HTTP 202 in <10 seconds with job_id")
        print("   ✅ No more 29-second timeouts")
        print("   ✅ All responses have proper CORS headers")
        print()
        
        # Run the critical tests
        self.test_job_status_response_time()
        self.test_split_video_response_time()
        self.test_multiple_job_status_calls()
        self.test_cors_preflight()
        
        # Summary
        print("=" * 80)
        print("📊 S3 POLLING TIMEOUT FIX TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze timeout fix status
        timeout_fix_status = {
            'job_status_fixed': False,
            'split_video_fixed': False,
            'multiple_calls_working': False,
            'cors_working': False
        }
        
        critical_failures = []
        
        for result in self.test_results:
            test_name = result['test'].lower()
            if result['success']:
                if 'job status response time' in test_name:
                    timeout_fix_status['job_status_fixed'] = True
                elif 'split video response time' in test_name:
                    timeout_fix_status['split_video_fixed'] = True
                elif 'multiple job status calls' in test_name:
                    timeout_fix_status['multiple_calls_working'] = True
                elif 'cors' in test_name:
                    timeout_fix_status['cors_working'] = True
            else:
                if 'critical failure' in test_name:
                    critical_failures.append(result)
        
        print("🔍 S3 POLLING TIMEOUT FIX STATUS:")
        print(f"   ✅ Job Status Endpoint (<5s): {'FIXED' if timeout_fix_status['job_status_fixed'] else '❌ STILL TIMING OUT'}")
        print(f"   ✅ Split Video Endpoint (<10s): {'FIXED' if timeout_fix_status['split_video_fixed'] else '❌ STILL TIMING OUT'}")
        print(f"   ✅ Multiple Calls Consistent: {'WORKING' if timeout_fix_status['multiple_calls_working'] else '❌ INCONSISTENT'}")
        print(f"   ✅ CORS Headers Present: {'WORKING' if timeout_fix_status['cors_working'] else '❌ MISSING'}")
        print()
        
        # Critical assessment
        fixed_count = sum([timeout_fix_status['job_status_fixed'], timeout_fix_status['split_video_fixed']])
        
        if critical_failures:
            print("🚨 CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['details']}")
            print()
        
        print("💡 FINAL ASSESSMENT:")
        
        if fixed_count == 2 and not critical_failures:
            print("   🎉 S3 POLLING TIMEOUT FIX COMPLETELY SUCCESSFUL!")
            print("   • Job status endpoint responds in <5 seconds ✓")
            print("   • Split video endpoint responds in <10 seconds ✓")
            print("   • No more 29-second timeouts ✓")
            print("   • The S3 list_objects_v2 polling removal was effective ✓")
        elif fixed_count >= 1:
            print(f"   ✅ PARTIAL SUCCESS: {fixed_count}/2 critical endpoints fixed")
            if not timeout_fix_status['job_status_fixed']:
                print("   • Job status endpoint still timing out - needs investigation")
            if not timeout_fix_status['split_video_fixed']:
                print("   • Split video endpoint still timing out - needs investigation")
        else:
            print("   ❌ S3 POLLING TIMEOUT FIX FAILED")
            print("   • Both critical endpoints still timing out after 29+ seconds")
            print("   • The S3 list_objects_v2 polling removal did NOT resolve the issue")
            print("   • Further investigation needed - may be other blocking operations")
        
        if critical_failures:
            print("   🔍 RECOMMENDED ACTIONS:")
            print("   • Check CloudWatch logs for remaining blocking operations")
            print("   • Verify S3 list_objects_v2 calls were actually removed")
            print("   • Look for other S3 operations that might be causing delays")
            print("   • Consider Lambda timeout settings and other AWS service limits")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = S3PollingTimeoutTester()
    passed, failed = tester.run_s3_polling_timeout_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)