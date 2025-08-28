#!/usr/bin/env python3
"""
FINAL TEST: Verify both split-video and job-status endpoints work without timeouts

CRITICAL OBJECTIVE:
Final verification that both endpoints now return immediately without 29-second timeouts 
after removing all blocking S3 operations.

TESTS:
1. Split Video Endpoint:
   - POST /api/split-video with real video payload
   - Must return HTTP 202 in <5 seconds
   - Must include CORS headers and job_id

2. Job Status Endpoint:
   - GET /api/job-status/test-job-123
   - Must return HTTP 200 in <5 seconds  
   - Must include CORS headers and progress

3. Both Endpoints Together:
   - Test complete workflow: split → get job_id → check status
   - Both should be fast (<5 seconds each)

SUCCESS CRITERIA:
✅ Split video: HTTP 202 in <5s with CORS headers
✅ Job status: HTTP 200 in <5s with CORS headers  
✅ No 29-second timeouts on either endpoint
✅ Complete workflow functional

EXPECTED RESULT:
Both endpoints should now work immediately, resolving the user's issue completely.
The user should be able to start video splitting AND track progress without any timeout errors.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 35  # 35 second timeout for testing
MAX_RESPONSE_TIME = 5.0  # Maximum acceptable response time

class FinalTimeoutTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.job_id_from_split = None
        
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

    def test_split_video_endpoint(self):
        """Test POST /api/split-video endpoint for immediate response"""
        print("🎯 TESTING SPLIT VIDEO ENDPOINT...")
        
        # Real video payload as specified in review request
        split_data = {
            "s3_key": "uploads/test/sample-video.mkv", 
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
                'under_5_seconds': response_time < MAX_RESPONSE_TIME,
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 202 status: {'PASS' if success_criteria['http_202'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Response < 5s: {'PASS' if success_criteria['under_5_seconds'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            response_data = {}
            if response.status_code == 202:
                try:
                    response_data = response.json()
                    job_id = response_data.get('job_id')
                    status = response_data.get('status')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    
                    if job_id and status:
                        success_criteria['response_fields'] = True
                        self.job_id_from_split = job_id  # Store for later use
                        print(f"      ✅ Response fields: PASS")
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing job_id or status)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
            else:
                success_criteria['response_fields'] = False
                try:
                    response_data = response.json() if response.content else {}
                except:
                    response_data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    "Split Video Endpoint",
                    True,
                    f"✅ ALL SUCCESS CRITERIA MET! HTTP 202 in {response_time:.2f}s with CORS headers and job_id. No timeout issues!"
                )
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    "Split Video Endpoint",
                    False,
                    f"Failed criteria: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s, CORS: {cors_origin}",
                    response_data
                )
                
            return all_criteria_met
            
        except requests.exceptions.Timeout:
            self.log_test(
                "Split Video Endpoint",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - endpoint still not responding fast enough"
            )
            return False
        except Exception as e:
            self.log_test(
                "Split Video Endpoint",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_job_status_endpoint(self, job_id: str = "test-job-123"):
        """Test GET /api/job-status/{job_id} endpoint for immediate response"""
        print(f"🎯 TESTING JOB STATUS ENDPOINT (job_id: {job_id})...")
        
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/job-status/{job_id}", headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            # SUCCESS CRITERIA CHECK
            success_criteria = {
                'http_200': response.status_code == 200,
                'under_5_seconds': response_time < MAX_RESPONSE_TIME,
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 200 status: {'PASS' if success_criteria['http_200'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Response < 5s: {'PASS' if success_criteria['under_5_seconds'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            response_data = {}
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    job_id_resp = response_data.get('job_id')
                    status = response_data.get('status')
                    progress = response_data.get('progress')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id_resp}")
                    print(f"      status: {status}")
                    print(f"      progress: {progress}")
                    
                    if job_id_resp and status is not None:
                        success_criteria['response_fields'] = True
                        print(f"      ✅ Response fields: PASS")
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing job_id or status)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
            else:
                success_criteria['response_fields'] = False
                try:
                    response_data = response.json() if response.content else {}
                except:
                    response_data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    f"Job Status Endpoint ({job_id})",
                    True,
                    f"✅ ALL SUCCESS CRITERIA MET! HTTP 200 in {response_time:.2f}s with CORS headers and progress data. No timeout issues!"
                )
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    f"Job Status Endpoint ({job_id})",
                    False,
                    f"Failed criteria: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s, CORS: {cors_origin}",
                    response_data
                )
                
            return all_criteria_met
            
        except requests.exceptions.Timeout:
            self.log_test(
                f"Job Status Endpoint ({job_id})",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - endpoint still not responding fast enough"
            )
            return False
        except Exception as e:
            self.log_test(
                f"Job Status Endpoint ({job_id})",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_cors_preflight(self, endpoint: str, method: str = "GET"):
        """Test CORS preflight request"""
        print(f"🔍 Testing CORS Preflight for {endpoint}...")
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
                self.log_test(
                    f"CORS Preflight {endpoint}",
                    True,
                    f"✅ CORS preflight working! Origin: {cors_origin}, Methods: {cors_methods}, Response time: {response_time:.2f}s"
                )
                return True
            else:
                self.log_test(
                    f"CORS Preflight {endpoint}",
                    False,
                    f"CORS preflight failed. Status: {response.status_code}, Origin header: {cors_origin}"
                )
                return False
                
        except Exception as e:
            self.log_test(f"CORS Preflight {endpoint}", False, f"Error: {str(e)}")
            return False

    def test_complete_workflow(self):
        """Test the complete workflow: split video → check status"""
        print("🔄 TESTING COMPLETE WORKFLOW...")
        
        # Step 1: Split video
        print("   Step 1: Initiating video split...")
        split_success = self.test_split_video_endpoint()
        
        if not split_success:
            self.log_test(
                "Complete Workflow",
                False,
                "❌ Workflow failed at step 1 (split video)"
            )
            return False
        
        # Step 2: Check status with job_id from split (if available)
        print("   Step 2: Checking job status...")
        if self.job_id_from_split:
            print(f"   Using job_id from split: {self.job_id_from_split}")
            status_success = self.test_job_status_endpoint(self.job_id_from_split)
        else:
            print("   Using test job_id: test-job-123")
            status_success = self.test_job_status_endpoint("test-job-123")
        
        if not status_success:
            self.log_test(
                "Complete Workflow",
                False,
                "❌ Workflow failed at step 2 (job status)"
            )
            return False
        
        # Both steps successful
        self.log_test(
            "Complete Workflow",
            True,
            "✅ Complete workflow successful! User can split videos AND track progress without timeouts."
        )
        return True

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

    def run_final_verification(self):
        """Run the complete final verification test"""
        print("=" * 80)
        print("🎯 FINAL VERIFICATION: BOTH ENDPOINTS WITHOUT TIMEOUTS")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL OBJECTIVE:")
        print("   Final verification that both endpoints now return immediately without")
        print("   29-second timeouts after removing all blocking S3 operations.")
        print()
        print("📋 SUCCESS CRITERIA:")
        print("   ✅ Split video: HTTP 202 in <5s with CORS headers")
        print("   ✅ Job status: HTTP 200 in <5s with CORS headers")
        print("   ✅ No 29-second timeouts on either endpoint")
        print("   ✅ Complete workflow functional")
        print()
        print("🎯 EXPECTED RESULT:")
        print("   Both endpoints should now work immediately, resolving the user's issue completely.")
        print("   The user should be able to start video splitting AND track progress without any timeout errors.")
        print()
        
        # Run tests in order
        connectivity_ok = self.test_basic_connectivity()
        
        # Test CORS preflight for both endpoints
        cors_split_ok = self.test_cors_preflight("/api/split-video", "POST")
        cors_status_ok = self.test_cors_preflight("/api/job-status/test-job-123", "GET")
        
        # Test individual endpoints
        split_ok = self.test_split_video_endpoint()
        status_ok = self.test_job_status_endpoint("test-job-123")
        
        # Test complete workflow
        workflow_ok = self.test_complete_workflow()
        
        # Summary
        print("=" * 80)
        print("📊 FINAL VERIFICATION SUMMARY")
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
        
        if split_ok and status_ok:
            print("   🎉 BOTH ENDPOINTS WORKING PERFECTLY!")
            print("   ✅ Split video endpoint: Returns HTTP 202 immediately")
            print("   ✅ Job status endpoint: Returns HTTP 200 immediately")
            print("   ✅ No 29-second timeouts on either endpoint")
            print("   ✅ CORS headers present on both endpoints")
            print("   ✅ Complete workflow functional")
            print()
            print("   🎯 USER IMPACT:")
            print("   ✅ User can successfully start video splitting")
            print("   ✅ User can track processing progress")
            print("   ✅ No more timeout errors")
            print("   ✅ No more CORS policy violations")
            print("   ✅ Complete resolution of reported issues")
        else:
            print("   ❌ ENDPOINTS STILL HAVE ISSUES")
            
            if not split_ok:
                print("   🚨 SPLIT VIDEO ENDPOINT ISSUES:")
                print("      • Still experiencing timeouts or other problems")
                print("      • User cannot start video splitting")
            
            if not status_ok:
                print("   🚨 JOB STATUS ENDPOINT ISSUES:")
                print("      • Still experiencing timeouts or other problems")
                print("      • User cannot track processing progress")
                print("      • This explains 'processing stuck at 0%' issue")
            
            print()
            print("   🎯 USER IMPACT:")
            print("   ❌ User will still experience the reported issues")
            print("   ❌ Video processing functionality remains problematic")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = FinalTimeoutTester()
    passed, failed = tester.run_final_verification()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)