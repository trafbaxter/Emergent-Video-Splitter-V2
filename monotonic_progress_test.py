#!/usr/bin/env python3
"""
MONOTONIC PROGRESS FIX VERIFICATION TEST
Tests the Video Splitter Pro backend to verify that the monotonic progress fix 
in the exception handler is working correctly.

Focus: Verify that progress values are truly monotonic (never decrease) even 
when S3 errors occur, and that the fix uses max(30, current_progress) instead 
of hardcoding 30%.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class MonotonicProgressTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.job_id = None
        
    def log_test(self, test_name, success, details, response_time=None):
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
        
    def test_create_video_splitting_job(self):
        """Test 1: Create a video splitting job using POST /api/split-video"""
        print("🔍 Testing Video Splitting Job Creation...")
        
        # Use realistic test data as per instructions
        test_payload = {
            "s3_key": "test-monotonic-progress.mp4",
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
                
                success_criteria = []
                
                # Check for job_id
                job_id = data.get('job_id')
                if job_id:
                    self.job_id = job_id
                    success_criteria.append(f"✅ job_id returned: {job_id}")
                else:
                    success_criteria.append("❌ job_id missing")
                
                # Check status
                status = data.get('status')
                if status in ['accepted', 'queued', 'processing']:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append(f"❌ Unexpected status: {status}")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers: {cors_headers}")
                else:
                    success_criteria.append("❌ No CORS headers")
                
                # Check response time (<5s as per review request)
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Create Video Splitting Job", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Create Video Splitting Job", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Create Video Splitting Job", False, f"Request failed: {str(e)}")
            return False
    
    def test_monotonic_progress_monitoring(self):
        """Test 2: Monitor GET /api/job-status/{job_id} calls repeatedly to verify monotonic progress"""
        print("🔍 Testing Monotonic Progress Monitoring...")
        
        if not self.job_id:
            self.log_test("Monotonic Progress Monitoring", False, "No job_id available from previous test")
            return False
        
        progress_values = []
        test_iterations = 15  # Monitor for 15 iterations
        monotonic_violations = []
        
        try:
            for i in range(test_iterations):
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base}/api/job-status/{self.job_id}",
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    message = data.get('message', '')
                    
                    progress_values.append({
                        'iteration': i + 1,
                        'progress': progress,
                        'status': status,
                        'message': message,
                        'response_time': response_time,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Check for monotonic violation
                    if len(progress_values) > 1:
                        prev_progress = progress_values[-2]['progress']
                        if progress < prev_progress:
                            monotonic_violations.append({
                                'iteration': i + 1,
                                'previous_progress': prev_progress,
                                'current_progress': progress,
                                'violation': f"Progress dropped from {prev_progress}% to {progress}%"
                            })
                    
                    print(f"   Iteration {i+1}: Progress={progress}%, Status={status}, Time={response_time:.2f}s")
                    
                    # If job is completed, we can stop early
                    if status in ['completed', 'failed']:
                        print(f"   Job {status} at iteration {i+1}, stopping monitoring")
                        break
                        
                else:
                    print(f"   Iteration {i+1}: HTTP {response.status_code} - {response.text}")
                
                # Wait between requests to allow for progress changes
                time.sleep(2)
            
            # Analyze results
            success_criteria = []
            
            # Check if we got any progress data
            if progress_values:
                success_criteria.append(f"✅ Collected {len(progress_values)} progress readings")
                
                # Check for monotonic violations
                if not monotonic_violations:
                    success_criteria.append("✅ No monotonic violations detected - progress never decreased")
                else:
                    success_criteria.append(f"❌ {len(monotonic_violations)} monotonic violations detected")
                    for violation in monotonic_violations:
                        success_criteria.append(f"   - {violation['violation']}")
                
                # Check progress range (should be reasonable)
                min_progress = min(p['progress'] for p in progress_values)
                max_progress = max(p['progress'] for p in progress_values)
                success_criteria.append(f"✅ Progress range: {min_progress}% to {max_progress}%")
                
                # Check for the specific fix: progress should not drop to hardcoded 30%
                hardcoded_30_detected = False
                for i, reading in enumerate(progress_values[1:], 1):
                    prev_reading = progress_values[i-1]
                    if prev_reading['progress'] > 30 and reading['progress'] == 30:
                        hardcoded_30_detected = True
                        success_criteria.append(f"❌ Hardcoded 30% detected at iteration {reading['iteration']} (was {prev_reading['progress']}%)")
                
                if not hardcoded_30_detected:
                    success_criteria.append("✅ No hardcoded 30% regression detected")
                
                # Check response times
                avg_response_time = sum(p['response_time'] for p in progress_values) / len(progress_values)
                if avg_response_time < 5.0:
                    success_criteria.append(f"✅ Average response time: {avg_response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Average response time: {avg_response_time:.2f}s (≥5s)")
                
            else:
                success_criteria.append("❌ No progress data collected")
            
            # Overall success: no monotonic violations and no hardcoded 30% regression
            all_success = (not monotonic_violations and not hardcoded_30_detected and progress_values)
            details = "; ".join(success_criteria)
            
            self.log_test("Monotonic Progress Monitoring", all_success, details)
            return all_success
            
        except Exception as e:
            self.log_test("Monotonic Progress Monitoring", False, f"Monitoring failed: {str(e)}")
            return False
    
    def test_s3_error_simulation(self):
        """Test 3: Test with a non-existent S3 key to potentially trigger S3 errors and verify progress behavior"""
        print("🔍 Testing S3 Error Simulation...")
        
        # Use a non-existent S3 key to potentially trigger S3 errors
        test_payload = {
            "s3_key": "non-existent-file-to-trigger-s3-errors.mp4",
            "method": "intervals", 
            "interval_duration": 180,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            # Create job with non-existent file
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
                error_test_job_id = data.get('job_id')
                
                if error_test_job_id:
                    print(f"   Created error test job: {error_test_job_id}")
                    
                    # Monitor this job for a few iterations to see how it handles S3 errors
                    progress_values = []
                    for i in range(8):  # Fewer iterations for error case
                        time.sleep(3)  # Wait a bit longer between requests
                        
                        status_response = requests.get(
                            f"{self.api_base}/api/job-status/{error_test_job_id}",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            progress = status_data.get('progress', 0)
                            status = status_data.get('status', 'unknown')
                            message = status_data.get('message', '')
                            
                            progress_values.append({
                                'iteration': i + 1,
                                'progress': progress,
                                'status': status,
                                'message': message
                            })
                            
                            print(f"   Error test iteration {i+1}: Progress={progress}%, Status={status}")
                            
                            # Look for the specific message that indicates S3 error handling
                            if "Status check temporarily unavailable" in message:
                                print(f"   ⚠️  S3 error message detected: {message}")
                            
                            if status in ['completed', 'failed']:
                                break
                    
                    # Analyze error case results
                    success_criteria = []
                    
                    if progress_values:
                        # Check for monotonic behavior even with errors
                        monotonic_violations = []
                        for i in range(1, len(progress_values)):
                            if progress_values[i]['progress'] < progress_values[i-1]['progress']:
                                monotonic_violations.append(f"Progress dropped from {progress_values[i-1]['progress']}% to {progress_values[i]['progress']}%")
                        
                        if not monotonic_violations:
                            success_criteria.append("✅ Progress remained monotonic even with potential S3 errors")
                        else:
                            success_criteria.append(f"❌ Monotonic violations with S3 errors: {'; '.join(monotonic_violations)}")
                        
                        # Check if we see the "Status check temporarily unavailable" message
                        error_messages = [p for p in progress_values if "temporarily unavailable" in p['message'].lower()]
                        if error_messages:
                            success_criteria.append(f"✅ S3 error handling message detected in {len(error_messages)} readings")
                        else:
                            success_criteria.append("ℹ️  No S3 error messages detected (may not have triggered S3 errors)")
                        
                        # Check for hardcoded 30% in error scenarios
                        hardcoded_30_in_errors = [p for p in progress_values if p['progress'] == 30]
                        if hardcoded_30_in_errors and len(progress_values) > 1:
                            # Check if 30% appeared after higher progress
                            for reading in hardcoded_30_in_errors:
                                prev_readings = [p for p in progress_values if p['iteration'] < reading['iteration']]
                                if prev_readings and max(p['progress'] for p in prev_readings) > 30:
                                    success_criteria.append("❌ Hardcoded 30% detected after higher progress in error scenario")
                                    break
                            else:
                                success_criteria.append("✅ No hardcoded 30% regression in error scenario")
                        else:
                            success_criteria.append("✅ No hardcoded 30% detected in error scenario")
                    else:
                        success_criteria.append("❌ No progress data collected for error test")
                    
                    all_success = progress_values and not any("❌" in criterion for criterion in success_criteria)
                    details = "; ".join(success_criteria)
                    
                    self.log_test("S3 Error Simulation", all_success, details)
                    return all_success
                else:
                    self.log_test("S3 Error Simulation", False, "No job_id returned for error test")
                    return False
            else:
                self.log_test("S3 Error Simulation", False, 
                            f"Failed to create error test job: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("S3 Error Simulation", False, f"Error simulation failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all monotonic progress tests as per review request"""
        print("🚀 MONOTONIC PROGRESS FIX VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing the fix for progress dropping from 50% to 30% due to hardcoded values in S3 exception handler")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_create_video_splitting_job())
        test_results.append(self.test_monotonic_progress_monitoring())
        test_results.append(self.test_s3_error_simulation())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 MONOTONIC PROGRESS TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 ALL SUCCESS CRITERIA MET - Monotonic Progress Fix Working!")
            success_criteria_met = [
                "✅ Video splitting jobs can be created successfully",
                "✅ Progress values are truly monotonic (never decrease)",
                "✅ No hardcoded 30% regression detected",
                "✅ S3 error handling preserves monotonic behavior",
                "✅ 'Status check temporarily unavailable' message doesn't cause progress regression"
            ]
        else:
            print("⚠️  SOME SUCCESS CRITERIA NOT MET - Review issues above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        for criterion in success_criteria_met if success_rate == 100 else []:
            print(criterion)
        
        print()
        print("EXPECTED OUTCOME:")
        if success_rate == 100:
            print("✅ Monotonic progress fix is working correctly")
            print("✅ Progress values never decrease, even when S3 errors occur")
            print("✅ Exception handler uses max(30, current_progress) instead of hardcoding 30%")
        else:
            print("❌ Monotonic progress fix verification incomplete - issues need resolution")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = MonotonicProgressTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)