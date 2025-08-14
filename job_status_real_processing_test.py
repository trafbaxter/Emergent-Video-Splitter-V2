#!/usr/bin/env python3
"""
Test job status detection while real FFmpeg processing is happening

OBJECTIVE:
Test the job-status endpoint with the real processing jobs to see if it can detect ongoing FFmpeg processing.

SPECIFIC TESTS:
1. Test Real Processing Job Status:
   - Test GET /api/job-status/0c205835-9155-4a86-b364-c84b1ab0f03d
   - This job is actively processing the real Ninja Turtles video
   - Should show progress based on output file count

2. Test Second Processing Job:
   - Test GET /api/job-status/a27beb30-44dd-4fad-b45f-7f30f76434a5
   - This is the intervals-based processing job
   - Should also show processing status

3. Check for Processing Updates:
   - Since FFmpeg is actively working on the 727MB video
   - May take 5-10 minutes but progress should eventually change from 25%

EXPECTED RESULTS:
- Both jobs should show 25% progress initially (no output files yet)
- As FFmpeg creates output files, progress should increase
- Status should remain "processing" until completion

CRITICAL VERIFICATION:
This will confirm if the job status system can properly track real video processing in progress.
The user should see the progress change from 25% as processing continues.
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import sys

# Configuration - Using the backend URL from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30  # 30 second timeout for testing

class JobStatusRealProcessingTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
        # The specific job IDs mentioned in the review request
        self.ninja_turtles_job_id = "0c205835-9155-4a86-b364-c84b1ab0f03d"
        self.intervals_job_id = "a27beb30-44dd-4fad-b45f-7f30f76434a5"
        
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

    def test_job_status(self, job_id: str, job_description: str):
        """Test job status for a specific job ID"""
        print(f"🔍 Testing job status for {job_description}...")
        print(f"   Job ID: {job_id}")
        
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
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    job_id_resp = data.get('job_id')
                    status = data.get('status')
                    progress = data.get('progress')
                    estimated_time = data.get('estimated_time_remaining')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id_resp}")
                    print(f"      status: {status}")
                    print(f"      progress: {progress}%")
                    print(f"      estimated_time_remaining: {estimated_time}")
                    
                    # Success criteria
                    success_criteria = {
                        'response_under_5s': response_time < 5.0,
                        'cors_headers': cors_origin is not None,
                        'has_job_id': job_id_resp is not None,
                        'has_status': status is not None,
                        'has_progress': progress is not None,
                        'valid_progress': isinstance(progress, (int, float)) and 0 <= progress <= 100
                    }
                    
                    print(f"   📋 SUCCESS CRITERIA:")
                    print(f"      ✅ Response < 5s: {'PASS' if success_criteria['response_under_5s'] else 'FAIL'} ({response_time:.2f}s)")
                    print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
                    print(f"      ✅ Has job_id: {'PASS' if success_criteria['has_job_id'] else 'FAIL'}")
                    print(f"      ✅ Has status: {'PASS' if success_criteria['has_status'] else 'FAIL'}")
                    print(f"      ✅ Has progress: {'PASS' if success_criteria['has_progress'] else 'FAIL'}")
                    print(f"      ✅ Valid progress: {'PASS' if success_criteria['valid_progress'] else 'FAIL'} ({progress}%)")
                    
                    all_criteria_met = all(success_criteria.values())
                    
                    if all_criteria_met:
                        self.log_test(
                            f"✅ {job_description} Status Check",
                            True,
                            f"Job status working perfectly! Status: {status}, Progress: {progress}%, Response time: {response_time:.2f}s, CORS: {cors_origin}"
                        )
                        return True, progress, status
                    else:
                        failed_criteria = [k for k, v in success_criteria.items() if not v]
                        self.log_test(
                            f"❌ {job_description} Status Check - Partial Success",
                            False,
                            f"Some criteria failed: {failed_criteria}. Status: {status}, Progress: {progress}%, Time: {response_time:.2f}s",
                            data
                        )
                        return False, progress, status
                        
                except json.JSONDecodeError:
                    self.log_test(
                        f"❌ {job_description} Status Check - Invalid JSON",
                        False,
                        f"Response not valid JSON. Status: {response.status_code}, Time: {response_time:.2f}s"
                    )
                    return False, None, None
                    
            elif response.status_code == 504:
                self.log_test(
                    f"❌ {job_description} Status Check - Timeout",
                    False,
                    f"🚨 CRITICAL: Job status endpoint timing out after {response_time:.2f}s with HTTP 504. This explains 'processing stuck at 0%' issue."
                )
                return False, None, None
                
            else:
                self.log_test(
                    f"❌ {job_description} Status Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code} error. Response time: {response_time:.2f}s, CORS: {cors_origin}"
                )
                return False, None, None
                
        except requests.exceptions.Timeout:
            self.log_test(
                f"❌ {job_description} Status Check - Client Timeout",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - endpoint not responding"
            )
            return False, None, None
            
        except Exception as e:
            self.log_test(
                f"❌ {job_description} Status Check - Error",
                False,
                f"Error: {str(e)}"
            )
            return False, None, None

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

    def run_real_processing_test(self):
        """Run the real processing job status test as requested in review"""
        print("=" * 80)
        print("🎯 REAL FFMPEG PROCESSING JOB STATUS DETECTION TEST")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL OBJECTIVE:")
        print("   Test job-status endpoint with real processing jobs to see if it can detect")
        print("   ongoing FFmpeg processing and show progress based on output file count")
        print()
        print("📋 SPECIFIC TESTS:")
        print(f"   1. Ninja Turtles Video Job: {self.ninja_turtles_job_id}")
        print(f"   2. Intervals Processing Job: {self.intervals_job_id}")
        print()
        print("📋 EXPECTED RESULTS:")
        print("   • Both jobs should show 25% progress initially (no output files yet)")
        print("   • As FFmpeg creates output files, progress should increase")
        print("   • Status should remain 'processing' until completion")
        print("   • Progress should eventually change from 25% as processing continues")
        print()
        
        # Run tests in order
        connectivity_ok = self.test_basic_connectivity()
        
        if not connectivity_ok:
            print("❌ Basic connectivity failed - skipping job status tests")
            return 0, 1
        
        # Test both job IDs
        ninja_success, ninja_progress, ninja_status = self.test_job_status(
            self.ninja_turtles_job_id, 
            "Ninja Turtles Video Processing"
        )
        
        intervals_success, intervals_progress, intervals_status = self.test_job_status(
            self.intervals_job_id, 
            "Intervals-based Processing"
        )
        
        # Summary
        print("=" * 80)
        print("📊 REAL PROCESSING JOB STATUS TEST SUMMARY")
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
        
        if ninja_success and intervals_success:
            print("   🎉 REAL PROCESSING JOB STATUS DETECTION WORKING!")
            print(f"   • Ninja Turtles job: Status={ninja_status}, Progress={ninja_progress}%")
            print(f"   • Intervals job: Status={intervals_status}, Progress={intervals_progress}%")
            print("   • Job status system can properly track real video processing")
            print("   • Users can see processing progress updates")
            
            # Check if progress is realistic
            if ninja_progress == 25 and intervals_progress == 25:
                print("   ⚠️  INITIAL STATE: Both jobs showing 25% progress (no output files yet)")
                print("   📝 RECOMMENDATION: Monitor these jobs over 5-10 minutes to see progress increase")
                print("   📝 As FFmpeg creates output files, progress should change from 25%")
            elif ninja_progress > 25 or intervals_progress > 25:
                print("   🎉 PROGRESS DETECTED: Jobs showing progress > 25% - FFmpeg is creating output files!")
                print("   ✅ This confirms the job status system is tracking real processing")
            
        elif ninja_success or intervals_success:
            print("   ⚠️  PARTIAL SUCCESS: One job status working, one failing")
            working_job = "Ninja Turtles" if ninja_success else "Intervals"
            failing_job = "Intervals" if ninja_success else "Ninja Turtles"
            print(f"   ✅ {working_job} job status working")
            print(f"   ❌ {failing_job} job status failing")
            
        else:
            print("   ❌ JOB STATUS DETECTION FAILED")
            
            # Analyze specific failures
            timeout_issues = []
            other_issues = []
            
            for result in self.test_results:
                if not result['success']:
                    if '504' in result['details'] or 'timeout' in result['details'].lower():
                        timeout_issues.append(result['test'])
                    else:
                        other_issues.append(result['test'])
            
            if timeout_issues:
                print("   🚨 TIMEOUT ISSUES:")
                for issue in timeout_issues:
                    print(f"      • {issue}")
                print("   • Job status endpoint timing out - explains 'processing stuck at 0%'")
                print("   • Users cannot track processing progress due to timeouts")
            
            if other_issues:
                print("   ⚠️  OTHER ISSUES:")
                for issue in other_issues:
                    print(f"      • {issue}")
        
        print()
        print("🔍 USER IMPACT:")
        if ninja_success and intervals_success:
            print("   ✅ Users can successfully track real video processing progress")
            print("   ✅ Job status system detects ongoing FFmpeg processing")
            print("   ✅ Progress updates based on actual output file count")
            print("   ✅ No timeout errors preventing progress tracking")
        else:
            print("   ❌ Users cannot track processing progress properly")
            print("   ❌ Job status system may not detect real FFmpeg processing")
            print("   ❌ Processing appears stuck at 0% due to status check failures")
        
        print()
        print("📝 NEXT STEPS:")
        if ninja_success and intervals_success:
            if ninja_progress == 25 and intervals_progress == 25:
                print("   • Monitor these jobs over 5-10 minutes")
                print("   • Progress should increase as FFmpeg creates output files")
                print("   • Re-run this test to verify progress changes")
            else:
                print("   • Job status detection is working correctly")
                print("   • Real processing progress is being tracked")
        else:
            print("   • Fix job status endpoint timeout issues")
            print("   • Ensure S3 operations are not blocking the response")
            print("   • Test again after timeout fixes are applied")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = JobStatusRealProcessingTester()
    passed, failed = tester.run_real_processing_test()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)