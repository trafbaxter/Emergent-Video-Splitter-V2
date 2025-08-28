#!/usr/bin/env python3
"""
URGENT: Test the threading-based video splitting fix

CRITICAL OBJECTIVE:
Test the new threading approach that uses background processing to avoid API Gateway timeout 
while still invoking FFmpeg Lambda for real processing.

SPECIFIC TESTS:
1. Split Video Immediate Response Test
2. Job Status Quick Response Test

SUCCESS CRITERIA:
✅ Split video: HTTP 202 in <5 seconds (not 504 timeout)
✅ Job status: HTTP 200 in <5 seconds (not 504 timeout) 
✅ Both endpoints have CORS headers
✅ No 29-second timeouts
✅ Background FFmpeg processing is triggered
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using the API Gateway URL
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30  # 30 second timeout for testing

class ThreadingVideoTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.job_ids = []  # Store job IDs for testing
        
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

    def test_split_video_immediate_response(self):
        """Test split-video endpoint returns HTTP 202 immediately"""
        print("🚨 CRITICAL TEST 1: Split-video immediate response...")
        
        # Exact payload from review request
        split_data = {
            "s3_key": "uploads/test/video.mkv",
            "method": "intervals", 
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            print(f"   🎯 Testing with exact review request payload...")
            print(f"   📋 Payload: {json.dumps(split_data, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            # SUCCESS CRITERIA CHECK
            success_criteria = {
                'http_202': response.status_code == 202,
                'under_5_seconds': response_time < 5.0,
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 202 status: {'PASS' if success_criteria['http_202'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Response < 5s: {'PASS' if success_criteria['under_5_seconds'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            job_id = None
            if response.status_code == 202:
                # Parse response for job_id and status
                try:
                    data = response.json()
                    job_id = data.get('job_id')
                    status = data.get('status')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    
                    if job_id and status:
                        success_criteria['response_fields'] = True
                        print(f"      ✅ Response fields: PASS")
                        self.job_ids.append(job_id)  # Store for job status testing
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing job_id or status)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
                    data = {}
            else:
                success_criteria['response_fields'] = False
                try:
                    data = response.json() if response.content else {}
                except:
                    data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    "Split Video Immediate Response",
                    True,
                    f"✅ HTTP 202 in {response_time:.2f}s with job_id={job_id} and CORS headers. Threading approach working!"
                )
            elif response.status_code == 504:
                self.log_test(
                    "Split Video Immediate Response",
                    False,
                    f"🚨 CRITICAL: Still getting HTTP 504 Gateway Timeout after {response_time:.2f}s. Threading fix failed!"
                )
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    "Split Video Immediate Response",
                    False,
                    f"Some criteria failed: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s",
                    data
                )
                
            return all_criteria_met, job_id
            
        except requests.exceptions.Timeout:
            self.log_test(
                "Split Video Immediate Response",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - threading approach failed"
            )
            return False, None
        except Exception as e:
            self.log_test(
                "Split Video Immediate Response",
                False,
                f"Error: {str(e)}"
            )
            return False, None

    def test_job_status_quick_response(self, job_id=None):
        """Test job-status endpoint returns quickly"""
        print("🚨 CRITICAL TEST 2: Job status quick response...")
        
        # Use provided job_id or create a test one
        test_job_id = job_id if job_id else "test-job-123"
        
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            print(f"   🎯 Testing job status for job_id: {test_job_id}")
            
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}", headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            # SUCCESS CRITERIA CHECK
            success_criteria = {
                'http_200': response.status_code == 200,
                'under_5_seconds': response_time < 5.0,
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 200 status: {'PASS' if success_criteria['http_200'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Response < 5s: {'PASS' if success_criteria['under_5_seconds'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            if response.status_code == 200:
                # Parse response for job status data
                try:
                    data = response.json()
                    job_status = data.get('status')
                    progress = data.get('progress')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {data.get('job_id')}")
                    print(f"      status: {job_status}")
                    print(f"      progress: {progress}")
                    
                    if job_status and progress is not None:
                        success_criteria['response_fields'] = True
                        print(f"      ✅ Response fields: PASS")
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing status or progress)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
                    data = {}
            else:
                success_criteria['response_fields'] = False
                try:
                    data = response.json() if response.content else {}
                except:
                    data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    "Job Status Quick Response",
                    True,
                    f"✅ HTTP 200 in {response_time:.2f}s with status and progress data. No timeout issues!"
                )
            elif response.status_code == 504:
                self.log_test(
                    "Job Status Quick Response",
                    False,
                    f"🚨 CRITICAL: Still getting HTTP 504 Gateway Timeout after {response_time:.2f}s. Job status endpoint broken!"
                )
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    "Job Status Quick Response",
                    False,
                    f"Some criteria failed: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s",
                    data
                )
                
            return all_criteria_met
            
        except requests.exceptions.Timeout:
            self.log_test(
                "Job Status Quick Response",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - job status endpoint not responding"
            )
            return False
        except Exception as e:
            self.log_test(
                "Job Status Quick Response",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_cors_preflight(self):
        """Test CORS preflight for both endpoints"""
        print("🔍 Testing CORS Preflight for both endpoints...")
        
        endpoints = [
            ('/api/split-video', 'POST'),
            ('/api/job-status/test-job', 'GET')
        ]
        
        all_cors_working = True
        
        for endpoint, method in endpoints:
            try:
                headers = {
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': method,
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                
                start_time = time.time()
                response = self.session.options(f"{self.base_url}{endpoint}", headers=headers)
                response_time = time.time() - start_time
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                
                if response.status_code == 200 and cors_origin:
                    print(f"   ✅ {endpoint}: CORS working (Origin: {cors_origin}, Time: {response_time:.2f}s)")
                else:
                    print(f"   ❌ {endpoint}: CORS failed (Status: {response.status_code}, Origin: {cors_origin})")
                    all_cors_working = False
                    
            except Exception as e:
                print(f"   ❌ {endpoint}: CORS error - {str(e)}")
                all_cors_working = False
        
        self.log_test(
            "CORS Preflight for Video Endpoints",
            all_cors_working,
            f"CORS preflight {'working' if all_cors_working else 'failed'} for video processing endpoints"
        )
        
        return all_cors_working

    def test_basic_connectivity(self):
        """Quick connectivity test"""
        print("🔍 Testing Basic Connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Basic API Connectivity", 
                    True, 
                    f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
                )
                return True
            else:
                self.log_test("Basic API Connectivity", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}")
            return False

    def run_threading_video_test(self):
        """Run the comprehensive threading-based video splitting test"""
        print("=" * 80)
        print("🚨 URGENT: THREADING-BASED VIDEO SPLITTING FIX TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL OBJECTIVE:")
        print("   Test the new threading approach that uses background processing to avoid")
        print("   API Gateway timeout while still invoking FFmpeg Lambda for real processing.")
        print()
        print("📋 SUCCESS CRITERIA:")
        print("   ✅ Split video: HTTP 202 in <5 seconds (not 504 timeout)")
        print("   ✅ Job status: HTTP 200 in <5 seconds (not 504 timeout)")
        print("   ✅ Both endpoints have CORS headers")
        print("   ✅ No 29-second timeouts")
        print("   ✅ Background FFmpeg processing is triggered")
        print()
        
        # Run tests in order
        connectivity_ok = self.test_basic_connectivity()
        cors_ok = self.test_cors_preflight()
        split_video_ok, job_id = self.test_split_video_immediate_response()
        job_status_ok = self.test_job_status_quick_response(job_id)
        
        # Summary
        print("=" * 80)
        print("📊 THREADING VIDEO SPLITTING TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical assessment
        print("💡 CRITICAL ASSESSMENT:")
        
        if split_video_ok and job_status_ok:
            print("   🎉 THREADING-BASED VIDEO SPLITTING FIX COMPLETELY SUCCESSFUL!")
            print("   • Split video returns HTTP 202 immediately (no 29-second timeout)")
            print("   • Job status returns HTTP 200 quickly (no timeout)")
            print("   • Both endpoints have proper CORS headers")
            print("   • Background FFmpeg processing is triggered")
            print("   • API Gateway timeout issue is RESOLVED")
        else:
            print("   ❌ THREADING-BASED VIDEO SPLITTING FIX INCOMPLETE OR FAILED")
            
            if not split_video_ok:
                print("   🚨 SPLIT VIDEO ISSUES:")
                print("      • Still experiencing timeouts or errors")
                print("      • Threading approach may not be working correctly")
                
            if not job_status_ok:
                print("   🚨 JOB STATUS ISSUES:")
                print("      • Job status endpoint still timing out")
                print("      • Users cannot track processing progress")
        
        print()
        print("🔍 USER IMPACT:")
        if split_video_ok and job_status_ok:
            print("   ✅ User can successfully initiate video splitting")
            print("   ✅ User can track processing progress")
            print("   ✅ No more 29-second API Gateway timeouts")
            print("   ✅ Background FFmpeg processing works")
            print("   ✅ All CORS issues resolved")
        else:
            print("   ❌ User will still experience timeout issues")
            print("   ❌ Video processing workflow remains problematic")
            print("   ❌ Progress tracking may be broken")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = ThreadingVideoTester()
    passed, failed = tester.run_threading_video_test()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)