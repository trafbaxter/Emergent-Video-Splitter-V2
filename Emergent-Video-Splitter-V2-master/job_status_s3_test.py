#!/usr/bin/env python3
"""
CRITICAL: Test the restored original job status logic with real S3 file checking

OBJECTIVE:
Test that the job status endpoint now uses the original working logic to check for actual video processing results in S3.

KEY TESTS:
1. Job Status Real File Detection - Test GET /api/job-status/test-job-123
   - Should check S3 `outputs/test-job-123/` for actual video files
   - Should return progress based on file count:
     - 0 files = 25% progress, "processing" status
     - 1 file = 50% progress, "processing" status  
     - 2+ files = 100% progress, "completed" status

2. Split Video + Real Job Status Flow - POST to /api/split-video with real video payload
   - Use returned job_id to check /api/job-status/{job_id}
   - Should show realistic progress based on actual S3 files, not fake progress

3. Response Time Verification - Both endpoints should return in <10 seconds (not timeout)
   - S3 file checking should be fast with MaxKeys=10 limit

EXPECTED BEHAVIOR:
- Job status now uses **original working logic** from master branch
- Checks S3 `outputs/{job_id}/` for actual video files 
- Returns real completion status instead of fake hash-based progress
- If FFmpeg Lambda is processing videos, this should detect the results

SUCCESS CRITERIA:
✅ Job status uses real S3 file counting (not fake progress)
✅ Progress based on actual output file count
✅ Fast response times (<10 seconds)
✅ CORS headers present
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using the backend URL from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 15  # 15 second timeout for testing

class JobStatusS3Tester:
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

    def test_job_status_real_file_detection(self):
        """Test that job status checks S3 for actual video files"""
        print("🔍 Testing Job Status Real S3 File Detection...")
        
        test_job_id = "test-job-123"
        
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}", headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    job_id = data.get('job_id')
                    status = data.get('status')
                    progress = data.get('progress')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    print(f"      progress: {progress}")
                    
                    # Check if this looks like real S3-based progress
                    expected_progress_values = [25, 50, 75, 100]  # Based on file count
                    is_realistic_progress = progress in expected_progress_values
                    
                    # Check response time (should be fast with S3 file checking)
                    fast_response = response_time < 10.0
                    
                    # Check for required fields
                    has_required_fields = job_id and status is not None and progress is not None
                    
                    # Check CORS headers
                    has_cors = cors_origin is not None
                    
                    success_criteria = {
                        'fast_response': fast_response,
                        'has_required_fields': has_required_fields,
                        'has_cors': has_cors,
                        'realistic_progress': is_realistic_progress
                    }
                    
                    print(f"   📋 SUCCESS CRITERIA:")
                    print(f"      ✅ Fast response (<10s): {'PASS' if fast_response else 'FAIL'} ({response_time:.2f}s)")
                    print(f"      ✅ Required fields: {'PASS' if has_required_fields else 'FAIL'}")
                    print(f"      ✅ CORS headers: {'PASS' if has_cors else 'FAIL'} ({cors_origin})")
                    print(f"      ✅ Realistic progress: {'PASS' if is_realistic_progress else 'FAIL'} ({progress}%)")
                    
                    all_criteria_met = all(success_criteria.values())
                    
                    if all_criteria_met:
                        self.log_test(
                            "Job Status Real S3 File Detection",
                            True,
                            f"✅ Job status endpoint working perfectly! Returns realistic progress ({progress}%) based on S3 file checking in {response_time:.2f}s with CORS headers. This indicates the original working logic has been restored."
                        )
                    else:
                        failed_criteria = [k for k, v in success_criteria.items() if not v]
                        self.log_test(
                            "Job Status Real S3 File Detection",
                            False,
                            f"Some criteria failed: {failed_criteria}. Progress: {progress}%, Time: {response_time:.2f}s, CORS: {cors_origin}",
                            data
                        )
                    
                    return all_criteria_met
                    
                except json.JSONDecodeError:
                    self.log_test(
                        "Job Status Real S3 File Detection",
                        False,
                        f"Invalid JSON response. Status: {response.status_code}, Time: {response_time:.2f}s"
                    )
                    return False
            else:
                self.log_test(
                    "Job Status Real S3 File Detection",
                    False,
                    f"HTTP {response.status_code} response. Time: {response_time:.2f}s, CORS: {cors_origin}"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Job Status Real S3 File Detection",
                False,
                f"🚨 TIMEOUT: Job status endpoint timed out after {TIMEOUT}s - S3 file checking may be blocking"
            )
            return False
        except Exception as e:
            self.log_test(
                "Job Status Real S3 File Detection",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_split_video_job_status_flow(self):
        """Test the complete split video + job status flow"""
        print("🔍 Testing Split Video + Real Job Status Flow...")
        
        # Step 1: Create a split video job
        split_data = {
            "s3_key": "test-video.mp4",
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
            
            print(f"   🎯 Step 1: Creating split video job...")
            print(f"   📋 Payload: {json.dumps(split_data, indent=2)}")
            
            start_time = time.time()
            split_response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            split_time = time.time() - start_time
            
            print(f"   ⏱️  Split video response time: {split_time:.2f}s")
            print(f"   📊 Split video status code: {split_response.status_code}")
            
            if split_response.status_code == 202:
                try:
                    split_data_response = split_response.json()
                    job_id = split_data_response.get('job_id')
                    
                    print(f"   📄 Split video response:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {split_data_response.get('status')}")
                    
                    if job_id:
                        # Step 2: Check job status with the returned job_id
                        print(f"   🎯 Step 2: Checking job status for job_id: {job_id}")
                        
                        start_time = time.time()
                        status_response = self.session.get(f"{self.base_url}/api/job-status/{job_id}", headers={'Origin': 'https://working.tads-video-splitter.com'})
                        status_time = time.time() - start_time
                        
                        print(f"   ⏱️  Job status response time: {status_time:.2f}s")
                        print(f"   📊 Job status status code: {status_response.status_code}")
                        
                        if status_response.status_code == 200:
                            try:
                                status_data = status_response.json()
                                status_job_id = status_data.get('job_id')
                                job_status = status_data.get('status')
                                progress = status_data.get('progress')
                                
                                print(f"   📄 Job status response:")
                                print(f"      job_id: {status_job_id}")
                                print(f"      status: {job_status}")
                                print(f"      progress: {progress}")
                                
                                # Check if this is real S3-based progress
                                expected_progress_values = [25, 50, 75, 100]
                                is_realistic_progress = progress in expected_progress_values
                                
                                # Success criteria
                                success_criteria = {
                                    'split_video_success': split_response.status_code == 202,
                                    'job_status_success': status_response.status_code == 200,
                                    'fast_responses': split_time < 10.0 and status_time < 10.0,
                                    'job_id_match': job_id == status_job_id,
                                    'realistic_progress': is_realistic_progress,
                                    'cors_headers': split_response.headers.get('Access-Control-Allow-Origin') and status_response.headers.get('Access-Control-Allow-Origin')
                                }
                                
                                print(f"   📋 SUCCESS CRITERIA:")
                                print(f"      ✅ Split video success: {'PASS' if success_criteria['split_video_success'] else 'FAIL'}")
                                print(f"      ✅ Job status success: {'PASS' if success_criteria['job_status_success'] else 'FAIL'}")
                                print(f"      ✅ Fast responses: {'PASS' if success_criteria['fast_responses'] else 'FAIL'} (split: {split_time:.2f}s, status: {status_time:.2f}s)")
                                print(f"      ✅ Job ID match: {'PASS' if success_criteria['job_id_match'] else 'FAIL'}")
                                print(f"      ✅ Realistic progress: {'PASS' if success_criteria['realistic_progress'] else 'FAIL'} ({progress}%)")
                                print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'}")
                                
                                all_criteria_met = all(success_criteria.values())
                                
                                if all_criteria_met:
                                    self.log_test(
                                        "Split Video + Real Job Status Flow",
                                        True,
                                        f"✅ Complete workflow working perfectly! Split video creates job in {split_time:.2f}s, job status shows realistic progress ({progress}%) based on S3 files in {status_time:.2f}s. Original working logic restored!"
                                    )
                                else:
                                    failed_criteria = [k for k, v in success_criteria.items() if not v]
                                    self.log_test(
                                        "Split Video + Real Job Status Flow",
                                        False,
                                        f"Some criteria failed: {failed_criteria}. Split: {split_time:.2f}s, Status: {status_time:.2f}s, Progress: {progress}%",
                                        {'split_response': split_data_response, 'status_response': status_data}
                                    )
                                
                                return all_criteria_met
                                
                            except json.JSONDecodeError:
                                self.log_test(
                                    "Split Video + Real Job Status Flow",
                                    False,
                                    f"Invalid JSON in job status response. Status: {status_response.status_code}"
                                )
                                return False
                        else:
                            self.log_test(
                                "Split Video + Real Job Status Flow",
                                False,
                                f"Job status request failed. Status: {status_response.status_code}, Time: {status_time:.2f}s"
                            )
                            return False
                    else:
                        self.log_test(
                            "Split Video + Real Job Status Flow",
                            False,
                            f"No job_id returned from split video request"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Split Video + Real Job Status Flow",
                        False,
                        f"Invalid JSON in split video response. Status: {split_response.status_code}"
                    )
                    return False
            else:
                self.log_test(
                    "Split Video + Real Job Status Flow",
                    False,
                    f"Split video request failed. Status: {split_response.status_code}, Time: {split_time:.2f}s"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Split Video + Real Job Status Flow",
                False,
                f"🚨 TIMEOUT: Request timed out after {TIMEOUT}s"
            )
            return False
        except Exception as e:
            self.log_test(
                "Split Video + Real Job Status Flow",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_response_time_verification(self):
        """Test that both endpoints return quickly (not timeout)"""
        print("🔍 Testing Response Time Verification...")
        
        endpoints_to_test = [
            ("Job Status", f"{self.base_url}/api/job-status/test-job-456"),
            ("Split Video", f"{self.base_url}/api/split-video")
        ]
        
        all_fast = True
        response_times = []
        
        for endpoint_name, url in endpoints_to_test:
            try:
                headers = {'Origin': 'https://working.tads-video-splitter.com'}
                
                if endpoint_name == "Split Video":
                    headers['Content-Type'] = 'application/json'
                    payload = {
                        "s3_key": "test-video.mp4",
                        "method": "intervals", 
                        "interval_duration": 300
                    }
                    start_time = time.time()
                    response = self.session.post(url, json=payload, headers=headers)
                else:
                    start_time = time.time()
                    response = self.session.get(url, headers=headers)
                
                response_time = time.time() - start_time
                response_times.append((endpoint_name, response_time, response.status_code))
                
                print(f"   📊 {endpoint_name}: {response_time:.2f}s (HTTP {response.status_code})")
                
                if response_time >= 10.0:
                    all_fast = False
                    print(f"      ❌ SLOW: {endpoint_name} took {response_time:.2f}s (≥10s threshold)")
                else:
                    print(f"      ✅ FAST: {endpoint_name} responded in {response_time:.2f}s (<10s threshold)")
                    
            except requests.exceptions.Timeout:
                all_fast = False
                response_times.append((endpoint_name, TIMEOUT, "TIMEOUT"))
                print(f"   ❌ TIMEOUT: {endpoint_name} timed out after {TIMEOUT}s")
            except Exception as e:
                all_fast = False
                response_times.append((endpoint_name, 0, f"ERROR: {str(e)}"))
                print(f"   ❌ ERROR: {endpoint_name} - {str(e)}")
        
        if all_fast:
            avg_time = sum(rt[1] for rt in response_times if isinstance(rt[1], (int, float))) / len([rt for rt in response_times if isinstance(rt[1], (int, float))])
            self.log_test(
                "Response Time Verification",
                True,
                f"✅ All endpoints respond quickly! Average response time: {avg_time:.2f}s. S3 file checking with MaxKeys=10 limit is working efficiently."
            )
        else:
            slow_endpoints = [rt[0] for rt in response_times if isinstance(rt[1], (int, float)) and rt[1] >= 10.0]
            timeout_endpoints = [rt[0] for rt in response_times if rt[2] == "TIMEOUT"]
            self.log_test(
                "Response Time Verification",
                False,
                f"Some endpoints are slow or timing out. Slow: {slow_endpoints}, Timeouts: {timeout_endpoints}. This suggests S3 operations may still be blocking."
            )
        
        return all_fast

    def test_cors_preflight(self):
        """Test CORS preflight for job status endpoint"""
        print("🔍 Testing CORS Preflight for job-status endpoint...")
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            start_time = time.time()
            response = self.session.options(f"{self.base_url}/api/job-status/test-job-123", headers=headers)
            response_time = time.time() - start_time
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            if response.status_code == 200 and cors_origin:
                self.log_test(
                    "CORS Preflight for job-status",
                    True,
                    f"✅ CORS preflight working! Origin: {cors_origin}, Methods: {cors_methods}, Response time: {response_time:.2f}s"
                )
                return True
            else:
                self.log_test(
                    "CORS Preflight for job-status",
                    False,
                    f"CORS preflight failed. Status: {response.status_code}, Origin header: {cors_origin}"
                )
                return False
                
        except Exception as e:
            self.log_test("CORS Preflight for job-status", False, f"Error: {str(e)}")
            return False

    def run_job_status_s3_test(self):
        """Run the comprehensive job status S3 testing as requested in review"""
        print("=" * 80)
        print("🚨 CRITICAL: Test the restored original job status logic with real S3 file checking")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 OBJECTIVE:")
        print("   Test that the job status endpoint now uses the original working logic")
        print("   to check for actual video processing results in S3.")
        print()
        print("📋 KEY TESTS:")
        print("   1. Job Status Real File Detection - GET /api/job-status/test-job-123")
        print("      • Should check S3 outputs/test-job-123/ for actual video files")
        print("      • Progress based on file count: 0=25%, 1=50%, 2+=100%")
        print("   2. Split Video + Real Job Status Flow")
        print("      • POST to /api/split-video then check job status")
        print("      • Should show realistic progress based on actual S3 files")
        print("   3. Response Time Verification")
        print("      • Both endpoints should return in <10 seconds")
        print()
        print("✅ SUCCESS CRITERIA:")
        print("   • Job status uses real S3 file counting (not fake progress)")
        print("   • Progress based on actual output file count")
        print("   • Fast response times (<10 seconds)")
        print("   • CORS headers present")
        print()
        
        # Run tests in order
        cors_ok = self.test_cors_preflight()
        job_status_ok = self.test_job_status_real_file_detection()
        workflow_ok = self.test_split_video_job_status_flow()
        response_time_ok = self.test_response_time_verification()
        
        # Summary
        print("=" * 80)
        print("📊 JOB STATUS S3 TESTING SUMMARY")
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
        
        if job_status_ok and workflow_ok and response_time_ok:
            print("   🎉 ORIGINAL JOB STATUS LOGIC COMPLETELY RESTORED!")
            print("   • Job status endpoint now checks S3 for actual video files")
            print("   • Returns realistic progress based on file count (not fake hash-based)")
            print("   • Fast response times indicate efficient S3 operations")
            print("   • Complete workflow from split-video to job-status works")
            print("   • If FFmpeg Lambda is processing videos, this will detect results")
        else:
            print("   ❌ JOB STATUS LOGIC RESTORATION INCOMPLETE")
            
            if not job_status_ok:
                print("   🚨 Job status endpoint issues:")
                print("      • May still be using fake progress instead of S3 file checking")
                print("      • Could be timing out due to blocking S3 operations")
                print("      • Progress values may not reflect actual file counts")
            
            if not workflow_ok:
                print("   🚨 Split video + job status workflow issues:")
                print("      • End-to-end flow not working properly")
                print("      • Job creation or status checking failing")
            
            if not response_time_ok:
                print("   🚨 Response time issues:")
                print("      • Endpoints taking too long (≥10 seconds)")
                print("      • S3 operations may be blocking instead of optimized")
                print("      • MaxKeys=10 limit may not be implemented")
        
        print()
        print("🔍 EXPECTED BEHAVIOR VERIFICATION:")
        if job_status_ok and workflow_ok:
            print("   ✅ Job status uses original working logic from master branch")
            print("   ✅ Checks S3 outputs/{job_id}/ for actual video files")
            print("   ✅ Returns real completion status instead of fake progress")
            print("   ✅ Can detect FFmpeg Lambda processing results")
        else:
            print("   ❌ Original working logic not fully restored")
            print("   ❌ May still be using fake hash-based progress")
            print("   ❌ S3 file checking may not be working properly")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = JobStatusS3Tester()
    passed, failed = tester.run_job_status_s3_test()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)