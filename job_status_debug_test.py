#!/usr/bin/env python3
"""
JOB STATUS ENDPOINT DEBUG TEST
Tests the job-status endpoint behavior with realistic scenario as requested in review.

Review Request:
1. Create a test job by calling split-video
2. Check job status using returned job_id
3. Call job-status multiple times to see if progress changes from 25%

Focus: Understanding why progress stays at 25% - backend issue or frontend polling issue?
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class JobStatusDebugTester:
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
        
    def test_split_video_job_creation(self):
        """Step 1: Create a test job by calling split-video endpoint"""
        print("🎬 Step 1: Creating test job with split-video endpoint...")
        
        # Use realistic payload as specified in review request
        payload = {
            "s3_key": "test-key.mp4",
            "method": "intervals", 
            "interval_duration": 300
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 202:
                data = response.json()
                job_id = data.get('job_id')
                
                if job_id:
                    self.job_id = job_id
                    success_details = f"Job created successfully with job_id: {job_id}, status: {data.get('status')}"
                    self.log_test("Split Video Job Creation", True, success_details, response_time)
                    return True
                else:
                    self.log_test("Split Video Job Creation", False, 
                                f"HTTP 202 but no job_id in response: {data}", response_time)
                    return False
                    
            else:
                self.log_test("Split Video Job Creation", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Split Video Job Creation", False, f"Request failed: {str(e)}")
            return False
    
    def test_initial_job_status(self):
        """Step 2: Check initial job status using returned job_id"""
        print("📊 Step 2: Checking initial job status...")
        
        if not hasattr(self, 'job_id'):
            self.log_test("Initial Job Status Check", False, "No job_id available from previous test")
            return False
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract key information
                job_id = data.get('job_id')
                status = data.get('status')
                progress = data.get('progress')
                
                success_criteria = []
                
                if job_id == self.job_id:
                    success_criteria.append(f"✅ Job ID matches: {job_id}")
                else:
                    success_criteria.append(f"❌ Job ID mismatch: got {job_id}, expected {self.job_id}")
                
                if status:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append("❌ No status in response")
                
                if progress is not None:
                    success_criteria.append(f"✅ Progress: {progress}%")
                    self.initial_progress = progress
                else:
                    success_criteria.append("❌ No progress in response")
                    self.initial_progress = None
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"⚠️ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Initial Job Status Check", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Initial Job Status Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Initial Job Status Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_multiple_job_status_calls(self):
        """Step 3: Call job-status multiple times (3-5 times) with 2-3 second intervals"""
        print("🔄 Step 3: Testing multiple job status calls to check progress changes...")
        
        if not hasattr(self, 'job_id'):
            self.log_test("Multiple Job Status Calls", False, "No job_id available from previous test")
            return False
        
        progress_values = []
        call_results = []
        
        # Make 5 calls with 2-3 second intervals
        for i in range(1, 6):
            print(f"   📞 Call {i}/5...")
            
            try:
                start_time = time.time()
                response = requests.get(
                    f"{self.api_base}/api/job-status/{self.job_id}",
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress')
                    status = data.get('status')
                    
                    progress_values.append(progress)
                    call_results.append({
                        'call': i,
                        'progress': progress,
                        'status': status,
                        'response_time': response_time,
                        'success': True
                    })
                    
                    print(f"      ✅ Call {i}: Progress={progress}%, Status={status}, Time={response_time:.2f}s")
                    
                else:
                    call_results.append({
                        'call': i,
                        'progress': None,
                        'status': f"HTTP {response.status_code}",
                        'response_time': response_time,
                        'success': False
                    })
                    
                    print(f"      ❌ Call {i}: HTTP {response.status_code}, Time={response_time:.2f}s")
                
                # Wait 2-3 seconds before next call (except for last call)
                if i < 5:
                    time.sleep(2.5)
                    
            except Exception as e:
                call_results.append({
                    'call': i,
                    'progress': None,
                    'status': f"Error: {str(e)}",
                    'response_time': None,
                    'success': False
                })
                
                print(f"      ❌ Call {i}: Failed - {str(e)}")
        
        # Analyze results
        successful_calls = [r for r in call_results if r['success']]
        valid_progress_values = [p for p in progress_values if p is not None]
        
        analysis = []
        
        # Check if all calls succeeded
        if len(successful_calls) == 5:
            analysis.append("✅ All 5 calls successful")
        else:
            analysis.append(f"❌ Only {len(successful_calls)}/5 calls successful")
        
        # Check progress variation
        if len(valid_progress_values) >= 2:
            unique_progress = set(valid_progress_values)
            if len(unique_progress) == 1:
                analysis.append(f"🔍 CRITICAL: Progress stuck at {valid_progress_values[0]}% (no change)")
            else:
                analysis.append(f"✅ Progress varies: {sorted(unique_progress)}")
        else:
            analysis.append("❌ Insufficient progress data to analyze")
        
        # Check if stuck at 25%
        if valid_progress_values and all(p == 25 for p in valid_progress_values):
            analysis.append("🚨 ISSUE CONFIRMED: All progress values are 25% (stuck at default/placeholder)")
        elif valid_progress_values and 25 in valid_progress_values:
            analysis.append("⚠️ Some progress values are 25% (may indicate placeholder behavior)")
        
        # Check response times
        response_times = [r['response_time'] for r in successful_calls if r['response_time']]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time < 5.0:
                analysis.append(f"✅ Average response time: {avg_time:.2f}s (<5s)")
            else:
                analysis.append(f"⚠️ Average response time: {avg_time:.2f}s (≥5s)")
        
        # Overall success determination
        all_calls_successful = len(successful_calls) == 5
        progress_changing = len(set(valid_progress_values)) > 1 if len(valid_progress_values) >= 2 else False
        
        overall_success = all_calls_successful and len(valid_progress_values) >= 3
        
        details = "; ".join(analysis)
        self.log_test("Multiple Job Status Calls", overall_success, details)
        
        # Store results for final analysis
        self.progress_values = valid_progress_values
        self.call_results = call_results
        
        return overall_success
    
    def analyze_progress_behavior(self):
        """Final Analysis: Determine if progress is stuck at 25% and why"""
        print("🔍 Final Analysis: Progress Behavior Investigation...")
        
        if not hasattr(self, 'progress_values') or not self.progress_values:
            self.log_test("Progress Behavior Analysis", False, "No progress data available for analysis")
            return False
        
        analysis_findings = []
        
        # Check if progress is stuck at 25%
        stuck_at_25 = all(p == 25 for p in self.progress_values)
        if stuck_at_25:
            analysis_findings.append("🚨 CONFIRMED: Progress stuck at 25% across all calls")
        else:
            analysis_findings.append(f"✅ Progress varies: {sorted(set(self.progress_values))}")
        
        # Check if initial progress was 25%
        if hasattr(self, 'initial_progress') and self.initial_progress == 25:
            analysis_findings.append("🔍 Initial progress was 25% (likely default/placeholder)")
        
        # Determine likely cause
        if stuck_at_25:
            analysis_findings.append("💡 LIKELY CAUSE: Backend returning default/placeholder 25% instead of real progress")
            analysis_findings.append("🎯 RECOMMENDATION: Check backend progress calculation logic")
        else:
            analysis_findings.append("✅ Progress calculation appears to be working correctly")
        
        # Check if this is a backend or frontend issue
        if len(self.call_results) >= 3 and all(r['success'] for r in self.call_results):
            analysis_findings.append("✅ Backend job-status endpoint is responsive (not a frontend polling issue)")
        else:
            analysis_findings.append("⚠️ Backend job-status endpoint has reliability issues")
        
        # Final determination
        is_backend_issue = stuck_at_25 and len(self.call_results) >= 3
        
        details = "; ".join(analysis_findings)
        self.log_test("Progress Behavior Analysis", not is_backend_issue, details)
        
        return not is_backend_issue
    
    def run_debug_test(self):
        """Run the complete job status debug test as requested in review"""
        print("🚀 JOB STATUS ENDPOINT DEBUG TEST")
        print("=" * 80)
        print("Review Request: Debug job-status endpoint behavior")
        print("Focus: Understanding why progress stays at 25%")
        print(f"Backend URL: {self.api_base}")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        test_results = []
        
        # Step 1: Create job
        step1_success = self.test_split_video_job_creation()
        test_results.append(step1_success)
        
        if step1_success:
            # Step 2: Check initial status
            step2_success = self.test_initial_job_status()
            test_results.append(step2_success)
            
            # Step 3: Multiple status calls
            step3_success = self.test_multiple_job_status_calls()
            test_results.append(step3_success)
            
            # Step 4: Analyze behavior
            step4_success = self.analyze_progress_behavior()
            test_results.append(step4_success)
        else:
            print("❌ Cannot proceed with job status testing - job creation failed")
            test_results.extend([False, False, False])
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 DEBUG TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        if hasattr(self, 'progress_values') and self.progress_values:
            unique_progress = set(self.progress_values)
            if len(unique_progress) == 1 and 25 in unique_progress:
                print("🚨 CRITICAL ISSUE CONFIRMED:")
                print("   - Progress is stuck at 25% across all calls")
                print("   - This indicates backend is returning default/placeholder value")
                print("   - NOT a frontend polling issue - backend job-status endpoint responds correctly")
                print("   - RECOMMENDATION: Check backend progress calculation logic")
            elif len(unique_progress) > 1:
                print("✅ PROGRESS WORKING CORRECTLY:")
                print(f"   - Progress values vary: {sorted(unique_progress)}")
                print("   - Backend is calculating real progress based on job processing")
            else:
                print("⚠️ INSUFFICIENT DATA:")
                print("   - Unable to determine progress behavior pattern")
        else:
            print("❌ NO PROGRESS DATA:")
            print("   - Job status endpoint not responding or job creation failed")
        
        print()
        print("ANSWER TO REVIEW QUESTIONS:")
        
        if hasattr(self, 'call_results') and len([r for r in self.call_results if r['success']]) >= 3:
            print("✅ Does job-status endpoint return different progress values over time?")
            if hasattr(self, 'progress_values') and len(set(self.progress_values)) > 1:
                print("   YES - Progress values change over time")
            else:
                print("   NO - Progress stays constant (likely stuck at 25%)")
        else:
            print("❌ Cannot determine - job-status endpoint not responding reliably")
        
        if hasattr(self, 'progress_values') and all(p == 25 for p in self.progress_values):
            print("🚨 Is it stuck at 25% because that's a default/placeholder value?")
            print("   YES - All calls return exactly 25%, indicating placeholder/default behavior")
        else:
            print("✅ Progress appears to be calculated dynamically")
        
        if hasattr(self, 'job_id'):
            print("✅ Are job files actually being processed or just queued?")
            print("   Job was created successfully - processing status needs backend investigation")
        else:
            print("❌ Cannot determine - job creation failed")
        
        print()
        return success_rate >= 75

if __name__ == "__main__":
    tester = JobStatusDebugTester()
    success = tester.run_debug_test()
    
    if not success:
        exit(1)