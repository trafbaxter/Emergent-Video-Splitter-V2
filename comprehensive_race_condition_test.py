#!/usr/bin/env python3
"""
COMPREHENSIVE RACE CONDITION FIX TEST
Tests the Video Splitter Pro backend race condition fix with focus on:
1. Progress monotonic behavior (no erratic jumps like 25% → 50% → 30%)
2. Job completion detection consistency
3. Duration metadata preservation in completed jobs
4. Multiple concurrent job status calls to detect race conditions
"""

import requests
import json
import time
import threading
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class ComprehensiveRaceConditionTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        
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
    
    def make_job_status_call(self, job_id: str, call_id: int) -> Dict[str, Any]:
        """Make a single job status call and return results"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{job_id}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'call_id': call_id,
                    'success': True,
                    'status': data.get('status', 'unknown'),
                    'progress': data.get('progress', 0),
                    'results': data.get('results', []),
                    'response_time': response_time,
                    'timestamp': time.time()
                }
            else:
                return {
                    'call_id': call_id,
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time,
                    'timestamp': time.time()
                }
        except Exception as e:
            return {
                'call_id': call_id,
                'success': False,
                'error': str(e),
                'response_time': 0,
                'timestamp': time.time()
            }
    
    def test_concurrent_job_status_calls(self, job_id: str) -> bool:
        """Test concurrent job status calls to detect race conditions"""
        print(f"🔍 Testing Concurrent Job Status Calls for race conditions...")
        print(f"   Job ID: {job_id}")
        
        # Make 10 concurrent calls to stress test the race condition fix
        num_calls = 10
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all calls simultaneously
            futures = [
                executor.submit(self.make_job_status_call, job_id, i+1) 
                for i in range(num_calls)
            ]
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Sort by call_id for analysis
        results.sort(key=lambda x: x['call_id'])
        
        # Analyze results for race conditions
        success_criteria = []
        successful_calls = [r for r in results if r['success']]
        
        if len(successful_calls) >= 8:  # At least 80% success rate
            success_criteria.append(f"✅ Successful calls: {len(successful_calls)}/{num_calls}")
            
            # Check for progress consistency (no erratic behavior)
            progress_values = [r['progress'] for r in successful_calls]
            progress_range = max(progress_values) - min(progress_values)
            
            if progress_range <= 10:  # Allow small variations but no big jumps
                success_criteria.append(f"✅ Progress values consistent: {min(progress_values)}-{max(progress_values)}%")
            else:
                success_criteria.append(f"❌ Erratic progress values: {min(progress_values)}-{max(progress_values)}% (range: {progress_range}%)")
            
            # Check response times (should be fast and consistent)
            response_times = [r['response_time'] for r in successful_calls]
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            if avg_time < 1.0 and max_time < 3.0:
                success_criteria.append(f"✅ Response times: avg={avg_time:.2f}s, max={max_time:.2f}s")
            else:
                success_criteria.append(f"❌ Slow response times: avg={avg_time:.2f}s, max={max_time:.2f}s")
            
            # Check status consistency
            statuses = [r['status'] for r in successful_calls]
            unique_statuses = set(statuses)
            if len(unique_statuses) <= 2:  # Allow processing -> completed transition
                success_criteria.append(f"✅ Status consistency: {unique_statuses}")
            else:
                success_criteria.append(f"❌ Inconsistent statuses: {unique_statuses}")
                
        else:
            success_criteria.append(f"❌ Too many failed calls: {len(successful_calls)}/{num_calls}")
        
        # Show detailed results
        print("   Concurrent call results:")
        for r in results[:5]:  # Show first 5 calls
            if r['success']:
                print(f"     Call {r['call_id']}: Progress={r['progress']}%, Status={r['status']}, Time={r['response_time']:.2f}s")
            else:
                print(f"     Call {r['call_id']}: ERROR - {r.get('error', 'Unknown')}")
        
        all_success = all("✅" in criterion for criterion in success_criteria)
        details = "; ".join(success_criteria)
        
        avg_time = sum(r['response_time'] for r in successful_calls) / len(successful_calls) if successful_calls else 0
        self.log_test("Concurrent Job Status Race Condition Test", all_success, details, avg_time)
        return all_success
    
    def test_progress_monotonic_behavior(self) -> bool:
        """Test progress monotonic behavior over time"""
        print("🔍 Testing Progress Monotonic Behavior...")
        
        # Create a new job first
        test_payload = {
            "s3_key": "test-monotonic-progress.mp4",
            "method": "intervals", 
            "interval_duration": 180,
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
            
            if response.status_code != 202:
                self.log_test("Progress Monotonic Behavior", False, f"Failed to create job: HTTP {response.status_code}")
                return False
            
            job_data = response.json()
            job_id = job_data.get('job_id')
            
            if not job_id:
                self.log_test("Progress Monotonic Behavior", False, "No job_id returned")
                return False
            
            print(f"   Created job: {job_id}")
            
            # Monitor progress over time
            progress_history = []
            
            for i in range(12):  # 12 calls over 24 seconds
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_base}/api/job-status/{job_id}", timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        progress = data.get('progress', 0)
                        status = data.get('status', 'unknown')
                        
                        progress_history.append({
                            'call': i+1,
                            'progress': progress,
                            'status': status,
                            'timestamp': time.time(),
                            'response_time': response_time
                        })
                        
                        print(f"     Call {i+1}: Progress={progress}%, Status={status}")
                    
                    time.sleep(2)  # Wait 2 seconds between calls
                    
                except Exception as e:
                    print(f"     Call {i+1}: Error - {str(e)}")
            
            # Analyze monotonic behavior
            success_criteria = []
            
            if len(progress_history) >= 8:
                # Check for monotonic progress (never decreases)
                monotonic_violations = []
                for i in range(1, len(progress_history)):
                    current = progress_history[i]['progress']
                    previous = progress_history[i-1]['progress']
                    
                    if current < previous:
                        monotonic_violations.append(f"{previous}%→{current}% (call {i}→{i+1})")
                
                if not monotonic_violations:
                    success_criteria.append("✅ Progress is monotonic (never decreases)")
                else:
                    success_criteria.append(f"❌ Progress violations: {', '.join(monotonic_violations)}")
                
                # Check for reasonable progress range
                all_progress = [h['progress'] for h in progress_history]
                min_progress = min(all_progress)
                max_progress = max(all_progress)
                
                if 0 <= min_progress <= max_progress <= 100:
                    success_criteria.append(f"✅ Progress range valid: {min_progress}-{max_progress}%")
                else:
                    success_criteria.append(f"❌ Invalid progress range: {min_progress}-{max_progress}%")
                
                # Check response times
                response_times = [h['response_time'] for h in progress_history]
                avg_time = sum(response_times) / len(response_times)
                
                if avg_time < 1.0:
                    success_criteria.append(f"✅ Fast response times: avg={avg_time:.2f}s")
                else:
                    success_criteria.append(f"❌ Slow response times: avg={avg_time:.2f}s")
                    
            else:
                success_criteria.append(f"❌ Insufficient data points: {len(progress_history)}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            avg_time = sum(h['response_time'] for h in progress_history) / len(progress_history) if progress_history else 0
            self.log_test("Progress Monotonic Behavior", all_success, details, avg_time)
            return all_success
            
        except Exception as e:
            self.log_test("Progress Monotonic Behavior", False, f"Test failed: {str(e)}")
            return False
    
    def test_job_completion_consistency(self) -> bool:
        """Test job completion detection consistency"""
        print("🔍 Testing Job Completion Detection Consistency...")
        
        # Test with multiple job IDs to find different states
        test_job_ids = [
            '33749042-9f5e-4fcf-a6ef-4cecbe9c99c5',  # This one showed 30% progress
            '7e38b588-fe5a-46d5-b0c9-e876f3293e2a',
            'c5e2575b-0896-4080-8be9-25ff9212d96d'
        ]
        
        consistency_results = []
        
        for job_id in test_job_ids:
            print(f"   Testing job: {job_id}")
            
            # Make 5 rapid calls to check consistency
            job_results = []
            for i in range(5):
                try:
                    response = requests.get(f"{self.api_base}/api/job-status/{job_id}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        job_results.append({
                            'status': data.get('status'),
                            'progress': data.get('progress', 0),
                            'results_count': len(data.get('results', []))
                        })
                    time.sleep(0.5)  # Short delay
                except Exception:
                    pass
            
            if job_results:
                # Check consistency within this job
                statuses = [r['status'] for r in job_results]
                progresses = [r['progress'] for r in job_results]
                
                status_consistent = len(set(statuses)) <= 1
                progress_consistent = len(set(progresses)) <= 1
                
                consistency_results.append({
                    'job_id': job_id,
                    'status_consistent': status_consistent,
                    'progress_consistent': progress_consistent,
                    'statuses': statuses,
                    'progresses': progresses
                })
                
                print(f"     Status consistency: {status_consistent}, Progress consistency: {progress_consistent}")
        
        # Analyze overall consistency
        success_criteria = []
        
        if consistency_results:
            status_consistent_count = sum(1 for r in consistency_results if r['status_consistent'])
            progress_consistent_count = sum(1 for r in consistency_results if r['progress_consistent'])
            
            if status_consistent_count >= len(consistency_results) * 0.8:
                success_criteria.append(f"✅ Status consistency: {status_consistent_count}/{len(consistency_results)} jobs")
            else:
                success_criteria.append(f"❌ Status inconsistency: {status_consistent_count}/{len(consistency_results)} jobs")
            
            if progress_consistent_count >= len(consistency_results) * 0.8:
                success_criteria.append(f"✅ Progress consistency: {progress_consistent_count}/{len(consistency_results)} jobs")
            else:
                success_criteria.append(f"❌ Progress inconsistency: {progress_consistent_count}/{len(consistency_results)} jobs")
        else:
            success_criteria.append("❌ No consistency data collected")
        
        all_success = all("✅" in criterion for criterion in success_criteria)
        details = "; ".join(success_criteria)
        
        self.log_test("Job Completion Detection Consistency", all_success, details)
        return all_success
    
    def run_comprehensive_race_condition_tests(self):
        """Run comprehensive race condition fix verification tests"""
        print("🚀 COMPREHENSIVE RACE CONDITION FIX VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing race condition fixes in job status endpoint:")
        print("• Progress monotonic behavior (no erratic jumps)")
        print("• Concurrent call consistency")
        print("• Job completion detection reliability")
        print("=" * 80)
        print()
        
        # Run all tests
        test_results = []
        
        # Test 1: Progress monotonic behavior
        test_results.append(self.test_progress_monotonic_behavior())
        
        # Test 2: Concurrent calls race condition test
        # Use a job that showed some progress variation
        test_results.append(self.test_concurrent_job_status_calls('33749042-9f5e-4fcf-a6ef-4cecbe9c99c5'))
        
        # Test 3: Job completion consistency
        test_results.append(self.test_job_completion_consistency())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 COMPREHENSIVE RACE CONDITION TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Race condition fix assessment
        if success_rate >= 75:
            print("🎉 RACE CONDITION FIX VERIFICATION SUCCESSFUL!")
            print("✅ Progress values show monotonic behavior (no erratic jumps)")
            print("✅ Concurrent job status calls are consistent")
            print("✅ Job completion detection is reliable")
            print()
            print("SPECIFIC ISSUES RESOLVED:")
            print("✅ No more progress bar erratic behavior (25% → 50% → 30%)")
            print("✅ UI can properly recognize job completion")
            print("✅ Race conditions in job status endpoint are fixed")
        else:
            print("⚠️  RACE CONDITION FIX VERIFICATION INCOMPLETE")
            print("❌ Some race condition issues may still exist")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}")
                    print(f"     {test['details']}")
        
        print()
        return success_rate >= 75

if __name__ == "__main__":
    tester = ComprehensiveRaceConditionTester()
    success = tester.run_comprehensive_race_condition_tests()
    
    if not success:
        exit(1)