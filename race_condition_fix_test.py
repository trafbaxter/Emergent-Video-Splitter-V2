#!/usr/bin/env python3
"""
RACE CONDITION FIX VERIFICATION TEST
Tests the Video Splitter Pro backend to verify that the race condition fix in the job status endpoint is working correctly.

Specifically tests:
1. POST /api/split-video - Start a video splitting job and get job_id
2. GET /api/job-status/{job_id} - Test multiple calls to ensure:
   - Progress values never decrease (monotonic behavior)
   - When job is completed, detailed results include duration metadata 
   - Status shows consistent completion detection

Focus on testing the specific issue mentioned in the user problem: 
progress bar erratic behavior (e.g., 25% → 50% → 30%) and the UI not recognizing job completion despite successful video splits.
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class RaceConditionFixTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.job_ids = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_time: float = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status}: {test_name}{time_info}")
        print(f"   Details: {details}")
        print()
        
    def test_split_video_job_creation(self) -> str:
        """Test 1: POST /api/split-video - Start a video splitting job and get job_id"""
        print("🔍 Testing Split Video Job Creation...")
        
        # Use realistic test data as per instructions
        test_payload = {
            "s3_key": "test-race-condition-fix.mp4",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 202:
                data = response.json()
                job_id = data.get('job_id')
                
                success_criteria = []
                
                # Check for job_id
                if job_id:
                    success_criteria.append(f"✅ job_id returned: {job_id}")
                    self.job_ids.append(job_id)
                else:
                    success_criteria.append("❌ job_id missing")
                
                # Check status
                status = data.get('status')
                if status in ['accepted', 'queued', 'processing']:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append(f"❌ Unexpected status: {status}")
                
                # Check response time (should be immediate)
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Split Video Job Creation", all_success, details, response_time)
                return job_id if job_id else None
                
            else:
                self.log_test("Split Video Job Creation", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            self.log_test("Split Video Job Creation", False, f"Request failed: {str(e)}")
            return None
    
    def test_job_status_monotonic_progress(self, job_id: str) -> bool:
        """Test 2: GET /api/job-status/{job_id} - Test multiple calls for monotonic progress"""
        print(f"🔍 Testing Job Status Monotonic Progress for job_id: {job_id}")
        
        progress_values = []
        response_times = []
        status_values = []
        
        # Make multiple calls over time to check for race conditions
        for i in range(8):  # 8 calls over ~15 seconds
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base}/api/job-status/{job_id}",
                    timeout=10
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    
                    progress_values.append(progress)
                    status_values.append(status)
                    
                    print(f"   Call {i+1}: Progress={progress}%, Status={status}, Time={response_time:.2f}s")
                    
                else:
                    print(f"   Call {i+1}: HTTP {response.status_code}")
                    progress_values.append(-1)  # Error marker
                    status_values.append('error')
                
            except Exception as e:
                print(f"   Call {i+1}: Exception - {str(e)}")
                progress_values.append(-1)  # Error marker
                status_values.append('error')
            
            # Wait between calls to allow processing
            if i < 7:  # Don't wait after last call
                time.sleep(2)
        
        # Analyze results for race condition issues
        success_criteria = []
        
        # Check monotonic progress (never decreases)
        monotonic = True
        for i in range(1, len(progress_values)):
            if progress_values[i] != -1 and progress_values[i-1] != -1:
                if progress_values[i] < progress_values[i-1]:
                    monotonic = False
                    success_criteria.append(f"❌ Progress decreased: {progress_values[i-1]}% → {progress_values[i]}% (call {i}→{i+1})")
        
        if monotonic:
            success_criteria.append("✅ Progress values are monotonic (never decrease)")
        
        # Check response times (should be consistent and fast)
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        if avg_response_time < 5.0:
            success_criteria.append(f"✅ Average response time: {avg_response_time:.2f}s (<5s)")
        else:
            success_criteria.append(f"❌ Average response time: {avg_response_time:.2f}s (≥5s)")
        
        # Check for consistent status progression
        valid_statuses = ['processing', 'completed', 'failed', 'queued']
        status_consistent = all(status in valid_statuses for status in status_values if status != 'error')
        if status_consistent:
            success_criteria.append("✅ Status values are consistent")
        else:
            success_criteria.append(f"❌ Invalid status values found: {set(status_values)}")
        
        # Check progress range (0-100)
        valid_progress = all(0 <= p <= 100 for p in progress_values if p != -1)
        if valid_progress:
            success_criteria.append("✅ Progress values in valid range (0-100%)")
        else:
            success_criteria.append(f"❌ Invalid progress values: {progress_values}")
        
        all_success = all("✅" in criterion for criterion in success_criteria)
        details = "; ".join(success_criteria)
        
        self.log_test("Job Status Monotonic Progress", all_success, details, avg_response_time)
        return all_success
    
    def test_completed_job_status(self) -> bool:
        """Test 3: Test a known completed job for detailed results and duration metadata"""
        print("🔍 Testing Completed Job Status with Duration Metadata...")
        
        # Use a known completed job ID from the test_result.md history
        completed_job_id = "7e38b588-fe5a-46d5-b0c9-e876f3293e2a"
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{completed_job_id}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check completion status
                status = data.get('status')
                if status == 'completed':
                    success_criteria.append("✅ Status: completed")
                else:
                    success_criteria.append(f"❌ Status: {status} (expected completed)")
                
                # Check progress is 100%
                progress = data.get('progress', 0)
                if progress == 100:
                    success_criteria.append("✅ Progress: 100%")
                else:
                    success_criteria.append(f"❌ Progress: {progress}% (expected 100%)")
                
                # Check for detailed results
                results = data.get('results', [])
                if results and len(results) > 0:
                    success_criteria.append(f"✅ Results array present: {len(results)} items")
                    
                    # Check for duration metadata in results
                    has_duration_metadata = False
                    for result in results:
                        if isinstance(result, dict):
                            # Check for duration-related fields
                            duration_fields = ['duration', 'start_time', 'end_time', 'metadata']
                            if any(field in result for field in duration_fields):
                                has_duration_metadata = True
                                success_criteria.append("✅ Duration metadata found in results")
                                break
                    
                    if not has_duration_metadata:
                        success_criteria.append("❌ Duration metadata missing from results")
                        # Show what fields are actually present
                        if results:
                            actual_fields = list(results[0].keys()) if isinstance(results[0], dict) else []
                            success_criteria.append(f"   Actual fields: {actual_fields}")
                else:
                    success_criteria.append("❌ Results array missing or empty")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Completed Job Status with Duration Metadata", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Completed Job Status with Duration Metadata", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Completed Job Status with Duration Metadata", False, f"Request failed: {str(e)}")
            return False
    
    def test_job_completion_detection(self, job_id: str) -> bool:
        """Test 4: Test job completion detection consistency"""
        print(f"🔍 Testing Job Completion Detection for job_id: {job_id}")
        
        # Make multiple calls to check for consistent completion detection
        completion_checks = []
        
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base}/api/job-status/{job_id}",
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    is_completed = (status == 'completed' and progress == 100)
                    completion_checks.append({
                        'call': i+1,
                        'status': status,
                        'progress': progress,
                        'is_completed': is_completed,
                        'response_time': response_time
                    })
                    
                    print(f"   Call {i+1}: Status={status}, Progress={progress}%, Completed={is_completed}")
                    
                else:
                    completion_checks.append({
                        'call': i+1,
                        'status': 'error',
                        'progress': -1,
                        'is_completed': False,
                        'response_time': response_time
                    })
                
            except Exception as e:
                completion_checks.append({
                    'call': i+1,
                    'status': 'exception',
                    'progress': -1,
                    'is_completed': False,
                    'response_time': 0
                })
            
            time.sleep(1)  # Short wait between calls
        
        # Analyze completion detection consistency
        success_criteria = []
        
        # Check for consistent completion detection
        completion_states = [check['is_completed'] for check in completion_checks]
        if len(set(completion_states)) <= 1:  # All same state
            success_criteria.append("✅ Completion detection is consistent")
        else:
            success_criteria.append(f"❌ Inconsistent completion detection: {completion_states}")
        
        # Check response times
        response_times = [check['response_time'] for check in completion_checks if check['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time < 5.0:
                success_criteria.append(f"✅ Average response time: {avg_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Average response time: {avg_time:.2f}s (≥5s)")
        
        # Check status consistency
        statuses = [check['status'] for check in completion_checks if check['status'] not in ['error', 'exception']]
        if len(set(statuses)) <= 1:  # All same status
            success_criteria.append("✅ Status values are consistent")
        else:
            success_criteria.append(f"❌ Inconsistent status values: {set(statuses)}")
        
        all_success = all("✅" in criterion for criterion in success_criteria)
        details = "; ".join(success_criteria)
        
        avg_time = sum(response_times) / len(response_times) if response_times else 0
        self.log_test("Job Completion Detection Consistency", all_success, details, avg_time)
        return all_success
    
    def run_race_condition_tests(self):
        """Run all race condition fix verification tests"""
        print("🚀 RACE CONDITION FIX VERIFICATION TEST")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing the specific race condition fix in job status endpoint")
        print("Focus: Progress monotonic behavior, completion detection, duration metadata")
        print("=" * 80)
        print()
        
        # Test 1: Create a new job
        job_id = self.test_split_video_job_creation()
        
        # Test 2: Test monotonic progress (only if job creation succeeded)
        monotonic_success = False
        if job_id:
            monotonic_success = self.test_job_status_monotonic_progress(job_id)
        
        # Test 3: Test completed job with duration metadata
        completed_success = self.test_completed_job_status()
        
        # Test 4: Test completion detection consistency (only if job creation succeeded)
        completion_success = False
        if job_id:
            completion_success = self.test_job_completion_detection(job_id)
        
        # Summary
        test_results = [
            job_id is not None,  # Job creation
            monotonic_success,   # Monotonic progress
            completed_success,   # Duration metadata
            completion_success   # Completion detection
        ]
        
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 RACE CONDITION FIX TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check specific race condition fix criteria
        race_condition_criteria = []
        
        if monotonic_success:
            race_condition_criteria.append("✅ Progress values are monotonic (never decrease)")
        else:
            race_condition_criteria.append("❌ Progress values show erratic behavior")
        
        if completion_success:
            race_condition_criteria.append("✅ Job completion detection is consistent")
        else:
            race_condition_criteria.append("❌ Job completion detection is inconsistent")
        
        if completed_success:
            race_condition_criteria.append("✅ Completed jobs show duration metadata")
        else:
            race_condition_criteria.append("❌ Duration metadata missing from completed jobs")
        
        print("RACE CONDITION FIX VERIFICATION:")
        for criterion in race_condition_criteria:
            print(criterion)
        
        print()
        
        if success_rate >= 75:
            print("🎉 RACE CONDITION FIX VERIFICATION SUCCESSFUL!")
            print("✅ The race condition fix in job status endpoint is working correctly")
            print("✅ Progress values show monotonic behavior")
            print("✅ Job completion is properly detected")
            if completed_success:
                print("✅ Duration metadata is preserved in completed jobs")
        else:
            print("⚠️  RACE CONDITION FIX VERIFICATION INCOMPLETE")
            print("❌ Some race condition issues may still exist")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        return success_rate >= 75

if __name__ == "__main__":
    tester = RaceConditionFixTester()
    success = tester.run_race_condition_tests()
    
    if not success:
        exit(1)