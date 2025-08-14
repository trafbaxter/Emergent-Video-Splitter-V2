#!/usr/bin/env python3
"""
FFprobe Fix Job Status Testing
Tests the specific job IDs mentioned in the review request to verify if the ffprobe fix is working.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from .env configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class FFprobeFixJobStatusTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        
        # Specific job IDs from review request
        self.job_ids = [
            "c5e2575b-0896-4080-8be9-25ff9212d96d",  # User's original job
            "7cd38811-46a3-42a5-acf1-44b5aad9ecd7",  # Newest job that was just processed
            "446b9ce0-1c24-46d7-81c3-0efae25a5e15"   # One more recent job
        ]
        
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
        
    def test_job_status(self, job_id, job_description):
        """Test job status endpoint for a specific job ID"""
        print(f"🔍 Testing Job Status for {job_description} ({job_id})...")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check response format
                    job_id_response = data.get('job_id')
                    status = data.get('status')
                    progress = data.get('progress')
                    message = data.get('message', '')
                    
                    if job_id_response == job_id:
                        success_criteria.append(f"✅ Job ID matches: {job_id}")
                    else:
                        success_criteria.append(f"❌ Job ID mismatch: got {job_id_response}, expected {job_id}")
                    
                    if status:
                        success_criteria.append(f"✅ Status: {status}")
                    else:
                        success_criteria.append("❌ Status missing")
                    
                    if progress is not None:
                        if progress > 25:
                            success_criteria.append(f"🎉 Progress > 25%: {progress}% (FFmpeg working!)")
                        elif progress == 25:
                            success_criteria.append(f"⚠️ Progress stuck at 25%: {progress}% (may indicate issue)")
                        else:
                            success_criteria.append(f"✅ Progress: {progress}%")
                    else:
                        success_criteria.append("❌ Progress missing")
                    
                    if message:
                        success_criteria.append(f"✅ Message: {message}")
                    
                    # Check CORS headers
                    cors_headers = response.headers.get('Access-Control-Allow-Origin')
                    if cors_headers:
                        success_criteria.append(f"✅ CORS headers: {cors_headers}")
                    else:
                        success_criteria.append("❌ CORS headers missing")
                    
                    # Check response time (should be under 5s for good performance)
                    if response_time < 5.0:
                        success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                    elif response_time < 30.0:
                        success_criteria.append(f"⚠️ Response time: {response_time:.2f}s (acceptable but slow)")
                    else:
                        success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥30s)")
                    
                    # Overall success if we got a valid response
                    all_success = response.status_code == 200 and job_id_response == job_id and progress is not None
                    details = "; ".join(success_criteria)
                    
                    self.log_test(f"Job Status - {job_description}", all_success, details, response_time)
                    return all_success, progress, status
                    
                except json.JSONDecodeError:
                    self.log_test(f"Job Status - {job_description}", False, 
                                f"HTTP 200 but invalid JSON: {response.text[:200]}", response_time)
                    return False, None, None
                    
            elif response.status_code == 404:
                self.log_test(f"Job Status - {job_description}", False, 
                            f"Job not found (HTTP 404) - job may not exist or may have been cleaned up", response_time)
                return False, None, "not_found"
                
            elif response.status_code == 504:
                self.log_test(f"Job Status - {job_description}", False, 
                            f"Gateway timeout (HTTP 504) - endpoint timing out after {response_time:.2f}s", response_time)
                return False, None, "timeout"
                
            else:
                self.log_test(f"Job Status - {job_description}", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                return False, None, f"error_{response.status_code}"
                
        except requests.exceptions.Timeout:
            self.log_test(f"Job Status - {job_description}", False, 
                        "Request timeout (30s) - endpoint not responding")
            return False, None, "timeout"
        except Exception as e:
            self.log_test(f"Job Status - {job_description}", False, f"Request failed: {str(e)}")
            return False, None, "error"
    
    def run_ffprobe_fix_verification(self):
        """Run FFprobe fix verification tests for specific job IDs"""
        print("🚀 FFprobe Fix Job Status Testing")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing specific job IDs to verify if ffprobe fix is working")
        print("Looking for progress > 25% which would indicate FFmpeg is now working")
        print("=" * 80)
        print()
        
        job_descriptions = [
            "User's Original Job",
            "Newest Processed Job", 
            "Recent Job"
        ]
        
        test_results = []
        progress_results = []
        
        for i, job_id in enumerate(self.job_ids):
            success, progress, status = self.test_job_status(job_id, job_descriptions[i])
            test_results.append(success)
            progress_results.append({
                'job_id': job_id,
                'description': job_descriptions[i],
                'progress': progress,
                'status': status,
                'success': success
            })
        
        # Summary Analysis
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 FFPROBE FIX VERIFICATION RESULTS")
        print("=" * 80)
        print(f"Jobs Tested: {total}")
        print(f"Successful Responses: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Analyze progress values
        working_jobs = [r for r in progress_results if r['progress'] is not None and r['progress'] > 25]
        stuck_jobs = [r for r in progress_results if r['progress'] == 25]
        failed_jobs = [r for r in progress_results if not r['success']]
        
        print("📊 PROGRESS ANALYSIS:")
        print(f"Jobs with progress > 25% (FFmpeg working): {len(working_jobs)}")
        print(f"Jobs stuck at 25% (potential issue): {len(stuck_jobs)}")
        print(f"Jobs that failed to respond: {len(failed_jobs)}")
        print()
        
        if working_jobs:
            print("🎉 JOBS WITH PROGRESS > 25% (FFmpeg appears to be working):")
            for job in working_jobs:
                print(f"   - {job['description']}: {job['progress']}% (Status: {job['status']})")
            print()
        
        if stuck_jobs:
            print("⚠️ JOBS STUCK AT 25% (may indicate ffprobe/FFmpeg issues):")
            for job in stuck_jobs:
                print(f"   - {job['description']}: {job['progress']}% (Status: {job['status']})")
            print()
        
        if failed_jobs:
            print("❌ JOBS THAT FAILED TO RESPOND:")
            for job in failed_jobs:
                print(f"   - {job['description']} ({job['job_id']}): {job['status']}")
            print()
        
        # Final Assessment
        print("🔍 FFPROBE FIX ASSESSMENT:")
        if len(working_jobs) > 0:
            print("✅ SUCCESS: At least one job shows progress > 25%, indicating FFmpeg/ffprobe is working!")
            print("✅ The ffprobe lambda layer fix appears to be successful.")
        elif len(stuck_jobs) > 0:
            print("⚠️ MIXED RESULTS: Jobs are responding but stuck at 25% progress.")
            print("⚠️ This may indicate ffprobe is working but FFmpeg processing has other issues.")
        else:
            print("❌ INCONCLUSIVE: No jobs could be tested successfully.")
            print("❌ Unable to determine if ffprobe fix is working due to job access issues.")
        
        print()
        print("EXPECTED OUTCOME:")
        if len(working_jobs) > 0:
            print("✅ FFprobe lambda layer fix is working - jobs are progressing beyond 25%")
        elif len(stuck_jobs) > 0:
            print("⚠️ Jobs are accessible but may have other processing issues beyond ffprobe")
        else:
            print("❌ Unable to verify ffprobe fix due to job access/response issues")
        
        print()
        return len(working_jobs) > 0

if __name__ == "__main__":
    tester = FFprobeFixJobStatusTester()
    success = tester.run_ffprobe_fix_verification()
    
    if not success:
        print("⚠️ No conclusive evidence of ffprobe fix working, but this may be due to job lifecycle or other factors.")