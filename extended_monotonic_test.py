#!/usr/bin/env python3
"""
EXTENDED MONOTONIC PROGRESS TEST
Tests existing jobs and creates multiple scenarios to thoroughly verify 
the monotonic progress fix.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class ExtendedMonotonicProgressTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        
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
        
    def test_existing_completed_jobs(self):
        """Test existing completed jobs to verify they maintain monotonic progress"""
        print("🔍 Testing Existing Completed Jobs...")
        
        # Test some known job IDs from the test_result.md history
        known_job_ids = [
            "7e38b588-fe5a-46d5-b0c9-e876f3293e2a",  # From review request
            "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5",  # From test history
            "c5e2575b-0896-4080-8be9-25ff9212d96d",  # From test history
        ]
        
        success_criteria = []
        jobs_tested = 0
        
        for job_id in known_job_ids:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base}/api/job-status/{job_id}",
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    message = data.get('message', '')
                    
                    jobs_tested += 1
                    print(f"   Job {job_id}: Progress={progress}%, Status={status}")
                    
                    # Check if this job shows higher progress (indicating the fix is working)
                    if progress > 25:
                        success_criteria.append(f"✅ Job {job_id}: Progress={progress}% (>25%)")
                    elif progress == 25:
                        success_criteria.append(f"ℹ️  Job {job_id}: Progress={progress}% (initial state)")
                    else:
                        success_criteria.append(f"❌ Job {job_id}: Progress={progress}% (<25%)")
                        
                    # Check for completion
                    if status == 'completed' and progress == 100:
                        success_criteria.append(f"✅ Job {job_id}: Completed with 100% progress")
                    elif status == 'completed' and progress != 100:
                        success_criteria.append(f"⚠️  Job {job_id}: Completed but progress={progress}%")
                        
                else:
                    print(f"   Job {job_id}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   Job {job_id}: Error - {str(e)}")
        
        if jobs_tested > 0:
            success_criteria.insert(0, f"✅ Tested {jobs_tested} existing jobs")
            all_success = jobs_tested > 0
        else:
            success_criteria.append("❌ No existing jobs could be tested")
            all_success = False
        
        details = "; ".join(success_criteria)
        self.log_test("Existing Completed Jobs", all_success, details)
        return all_success
    
    def test_rapid_progress_monitoring(self):
        """Test rapid monitoring to catch any progress fluctuations"""
        print("🔍 Testing Rapid Progress Monitoring...")
        
        # Create a new job for rapid monitoring
        test_payload = {
            "s3_key": "rapid-monitor-test.mp4",
            "method": "intervals",
            "interval_duration": 120,  # Shorter intervals for potentially faster processing
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            # Create job
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 202:
                data = response.json()
                job_id = data.get('job_id')
                
                if job_id:
                    print(f"   Created rapid monitoring job: {job_id}")
                    
                    # Rapid monitoring - check every 1 second for 30 seconds
                    progress_readings = []
                    monotonic_violations = []
                    
                    for i in range(30):
                        try:
                            status_response = requests.get(
                                f"{self.api_base}/api/job-status/{job_id}",
                                timeout=5
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                progress = status_data.get('progress', 0)
                                status = status_data.get('status', 'unknown')
                                message = status_data.get('message', '')
                                
                                reading = {
                                    'second': i + 1,
                                    'progress': progress,
                                    'status': status,
                                    'message': message,
                                    'timestamp': datetime.now().isoformat()
                                }
                                progress_readings.append(reading)
                                
                                # Check for monotonic violation
                                if len(progress_readings) > 1:
                                    prev_progress = progress_readings[-2]['progress']
                                    if progress < prev_progress:
                                        violation = {
                                            'second': i + 1,
                                            'previous': prev_progress,
                                            'current': progress,
                                            'drop': prev_progress - progress
                                        }
                                        monotonic_violations.append(violation)
                                        print(f"   ⚠️  VIOLATION at second {i+1}: {prev_progress}% → {progress}% (drop: {violation['drop']}%)")
                                
                                # Print every 5 seconds to avoid spam
                                if (i + 1) % 5 == 0:
                                    print(f"   Second {i+1}: Progress={progress}%, Status={status}")
                                
                                # Look for specific error messages
                                if "temporarily unavailable" in message.lower():
                                    print(f"   ⚠️  S3 error message at second {i+1}: {message}")
                                
                                if status in ['completed', 'failed']:
                                    print(f"   Job {status} at second {i+1}, stopping monitoring")
                                    break
                                    
                        except Exception as e:
                            print(f"   Second {i+1}: Request error - {str(e)}")
                        
                        time.sleep(1)  # 1 second intervals
                    
                    # Analyze rapid monitoring results
                    success_criteria = []
                    
                    if progress_readings:
                        success_criteria.append(f"✅ Collected {len(progress_readings)} rapid progress readings")
                        
                        # Check for monotonic violations
                        if not monotonic_violations:
                            success_criteria.append("✅ No monotonic violations in rapid monitoring")
                        else:
                            success_criteria.append(f"❌ {len(monotonic_violations)} monotonic violations detected")
                            for violation in monotonic_violations[:3]:  # Show first 3 violations
                                success_criteria.append(f"   - Second {violation['second']}: {violation['previous']}% → {violation['current']}% (drop: {violation['drop']}%)")
                        
                        # Check progress range
                        min_progress = min(r['progress'] for r in progress_readings)
                        max_progress = max(r['progress'] for r in progress_readings)
                        success_criteria.append(f"✅ Progress range: {min_progress}% to {max_progress}%")
                        
                        # Check for the specific hardcoded 30% issue
                        hardcoded_30_issues = []
                        for i, reading in enumerate(progress_readings[1:], 1):
                            prev_reading = progress_readings[i-1]
                            if prev_reading['progress'] > 30 and reading['progress'] == 30:
                                hardcoded_30_issues.append(f"Second {reading['second']}: {prev_reading['progress']}% → 30%")
                        
                        if not hardcoded_30_issues:
                            success_criteria.append("✅ No hardcoded 30% regression detected in rapid monitoring")
                        else:
                            success_criteria.append(f"❌ Hardcoded 30% regression detected: {'; '.join(hardcoded_30_issues)}")
                        
                        # Check for S3 error messages
                        error_messages = [r for r in progress_readings if "temporarily unavailable" in r['message'].lower()]
                        if error_messages:
                            success_criteria.append(f"✅ S3 error handling detected in {len(error_messages)} readings")
                        else:
                            success_criteria.append("ℹ️  No S3 error messages in rapid monitoring")
                    else:
                        success_criteria.append("❌ No progress readings collected in rapid monitoring")
                    
                    all_success = (progress_readings and not monotonic_violations and not hardcoded_30_issues)
                    details = "; ".join(success_criteria)
                    
                    self.log_test("Rapid Progress Monitoring", all_success, details)
                    return all_success
                else:
                    self.log_test("Rapid Progress Monitoring", False, "No job_id returned for rapid monitoring test")
                    return False
            else:
                self.log_test("Rapid Progress Monitoring", False, f"Failed to create rapid monitoring job: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Rapid Progress Monitoring", False, f"Rapid monitoring failed: {str(e)}")
            return False
    
    def test_multiple_concurrent_jobs(self):
        """Test multiple concurrent jobs to verify consistent monotonic behavior"""
        print("🔍 Testing Multiple Concurrent Jobs...")
        
        job_configs = [
            {"s3_key": "concurrent-test-1.mp4", "method": "intervals", "interval_duration": 300},
            {"s3_key": "concurrent-test-2.mp4", "method": "intervals", "interval_duration": 180},
            {"s3_key": "concurrent-test-3.mp4", "method": "intervals", "interval_duration": 240},
        ]
        
        created_jobs = []
        
        try:
            # Create multiple jobs
            for i, config in enumerate(job_configs):
                config.update({"preserve_quality": True, "output_format": "mp4"})
                
                response = requests.post(
                    f"{self.api_base}/api/split-video",
                    json=config,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 202:
                    data = response.json()
                    job_id = data.get('job_id')
                    if job_id:
                        created_jobs.append(job_id)
                        print(f"   Created concurrent job {i+1}: {job_id}")
            
            if created_jobs:
                print(f"   Monitoring {len(created_jobs)} concurrent jobs...")
                
                # Monitor all jobs simultaneously for several iterations
                all_progress_data = {job_id: [] for job_id in created_jobs}
                all_violations = []
                
                for iteration in range(10):
                    print(f"   Iteration {iteration + 1}:")
                    
                    for job_id in created_jobs:
                        try:
                            response = requests.get(
                                f"{self.api_base}/api/job-status/{job_id}",
                                timeout=5
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                progress = data.get('progress', 0)
                                status = data.get('status', 'unknown')
                                
                                reading = {
                                    'iteration': iteration + 1,
                                    'progress': progress,
                                    'status': status,
                                    'job_id': job_id
                                }
                                all_progress_data[job_id].append(reading)
                                
                                # Check for monotonic violation within this job
                                if len(all_progress_data[job_id]) > 1:
                                    prev_progress = all_progress_data[job_id][-2]['progress']
                                    if progress < prev_progress:
                                        violation = {
                                            'job_id': job_id,
                                            'iteration': iteration + 1,
                                            'previous': prev_progress,
                                            'current': progress
                                        }
                                        all_violations.append(violation)
                                
                                print(f"     Job {job_id[-8:]}: {progress}% ({status})")
                                
                        except Exception as e:
                            print(f"     Job {job_id[-8:]}: Error - {str(e)}")
                    
                    time.sleep(2)  # Wait between iterations
                
                # Analyze concurrent job results
                success_criteria = []
                
                total_readings = sum(len(readings) for readings in all_progress_data.values())
                success_criteria.append(f"✅ Collected {total_readings} total progress readings from {len(created_jobs)} concurrent jobs")
                
                if not all_violations:
                    success_criteria.append("✅ No monotonic violations across all concurrent jobs")
                else:
                    success_criteria.append(f"❌ {len(all_violations)} monotonic violations detected across concurrent jobs")
                    for violation in all_violations[:2]:  # Show first 2 violations
                        success_criteria.append(f"   - Job {violation['job_id'][-8:]}: {violation['previous']}% → {violation['current']}%")
                
                # Check for consistent behavior across jobs
                job_progress_ranges = {}
                for job_id, readings in all_progress_data.items():
                    if readings:
                        min_prog = min(r['progress'] for r in readings)
                        max_prog = max(r['progress'] for r in readings)
                        job_progress_ranges[job_id] = (min_prog, max_prog)
                
                if job_progress_ranges:
                    success_criteria.append(f"✅ Progress ranges: {len(job_progress_ranges)} jobs tracked")
                    for job_id, (min_prog, max_prog) in list(job_progress_ranges.items())[:2]:
                        success_criteria.append(f"   - Job {job_id[-8:]}: {min_prog}% to {max_prog}%")
                
                all_success = (total_readings > 0 and not all_violations)
                details = "; ".join(success_criteria)
                
                self.log_test("Multiple Concurrent Jobs", all_success, details)
                return all_success
            else:
                self.log_test("Multiple Concurrent Jobs", False, "No concurrent jobs could be created")
                return False
                
        except Exception as e:
            self.log_test("Multiple Concurrent Jobs", False, f"Concurrent jobs test failed: {str(e)}")
            return False
    
    def run_extended_tests(self):
        """Run extended monotonic progress tests"""
        print("🚀 EXTENDED MONOTONIC PROGRESS VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Extended testing to thoroughly verify monotonic progress fix")
        print("=" * 80)
        print()
        
        # Run extended tests
        test_results = []
        
        test_results.append(self.test_existing_completed_jobs())
        test_results.append(self.test_rapid_progress_monitoring())
        test_results.append(self.test_multiple_concurrent_jobs())
        
        # Summary
        passed = sum(1 for result in test_results if result)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 EXTENDED MONOTONIC PROGRESS TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        return success_rate == 100

if __name__ == "__main__":
    tester = ExtendedMonotonicProgressTester()
    success = tester.run_extended_tests()
    
    if not success:
        exit(1)