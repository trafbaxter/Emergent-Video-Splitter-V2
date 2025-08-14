#!/usr/bin/env python3
"""
SPECIFIC JOB STATUS TEST: Test the job-status endpoint for the user's specific job
Job ID: c5e2575b-0896-4080-8be9-25ff9212d96d

This job was stuck at 25% and the user just ran the job queue processor 
which successfully invoked the FFmpeg Lambda for this job.

Test Requirements:
1. GET /api/job-status/c5e2575b-0896-4080-8be9-25ff9212d96d
2. Check if the progress has changed from 25% 
3. Look for any status changes (should still be "processing" but progress might be different)
4. Test 2-3 times with a few seconds between calls to see if progress is updating
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class JobStatusSpecificTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # The specific job ID from the review request
        self.job_id = "c5e2575b-0896-4080-8be9-25ff9212d96d"
        
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
        
    def test_job_status_single(self, test_number):
        """Test the specific job status endpoint once"""
        print(f"🔍 Testing Job Status #{test_number} for job: {self.job_id}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check response format
                job_id_response = data.get('job_id')
                status = data.get('status')
                progress = data.get('progress')
                
                if job_id_response == self.job_id:
                    success_criteria.append(f"✅ Job ID matches: {job_id_response}")
                else:
                    success_criteria.append(f"❌ Job ID mismatch: {job_id_response} (expected {self.job_id})")
                
                if status:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append("❌ Status missing")
                
                if progress is not None:
                    success_criteria.append(f"✅ Progress: {progress}%")
                    # Store progress for comparison
                    setattr(self, f'progress_{test_number}', progress)
                else:
                    success_criteria.append("❌ Progress missing")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time (<5s as per review requirements)
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                # Additional fields that might be present
                additional_fields = []
                for field in ['created_at', 'updated_at', 'estimated_time', 'message', 'output_files']:
                    if field in data:
                        additional_fields.append(f"{field}: {data[field]}")
                
                if additional_fields:
                    success_criteria.append(f"✅ Additional fields: {', '.join(additional_fields)}")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test(f"Job Status Test #{test_number}", all_success, details, response_time)
                return all_success, data
                
            elif response.status_code == 404:
                self.log_test(f"Job Status Test #{test_number}", False, 
                            f"Job not found (HTTP 404) - job may not exist or may have been completed/cleaned up", response_time)
                return False, None
                
            elif response.status_code == 504:
                self.log_test(f"Job Status Test #{test_number}", False, 
                            f"Gateway timeout (HTTP 504) - endpoint timing out after {response_time:.2f}s", response_time)
                return False, None
                
            else:
                self.log_test(f"Job Status Test #{test_number}", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False, None
                
        except requests.exceptions.Timeout:
            self.log_test(f"Job Status Test #{test_number}", False, "Request timeout (>30s)")
            return False, None
        except Exception as e:
            self.log_test(f"Job Status Test #{test_number}", False, f"Request failed: {str(e)}")
            return False, None
    
    def test_cors_preflight(self):
        """Test CORS preflight for job status endpoint"""
        print("🔍 Testing CORS Preflight for Job Status Endpoint...")
        
        try:
            start_time = time.time()
            response = requests.options(
                f"{self.api_base}/api/job-status/{self.job_id}",
                headers={
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code
            if response.status_code in [200, 204]:
                success_criteria.append(f"✅ CORS preflight status: {response.status_code}")
            else:
                success_criteria.append(f"❌ CORS preflight status: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            cors_headers = response.headers.get('Access-Control-Allow-Headers')
            
            if cors_origin:
                success_criteria.append(f"✅ CORS Origin: {cors_origin}")
            else:
                success_criteria.append("❌ CORS Origin header missing")
            
            if cors_methods and 'GET' in cors_methods:
                success_criteria.append(f"✅ CORS Methods: {cors_methods}")
            else:
                success_criteria.append(f"❌ CORS Methods: {cors_methods} (GET not allowed)")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight Test", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("CORS Preflight Test", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all job status tests as per review request requirements"""
        print("🚀 SPECIFIC JOB STATUS TEST: Testing job that was stuck at 25%")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Job ID: {self.job_id}")
        print("=" * 80)
        print()
        
        # Test CORS preflight first
        cors_success = self.test_cors_preflight()
        
        # Test job status multiple times with delays as requested
        test_results = []
        job_responses = []
        
        # Test 1: Initial check
        success1, data1 = self.test_job_status_single(1)
        test_results.append(success1)
        if data1:
            job_responses.append(data1)
        
        # Wait 3 seconds
        print("⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
        
        # Test 2: Second check
        success2, data2 = self.test_job_status_single(2)
        test_results.append(success2)
        if data2:
            job_responses.append(data2)
        
        # Wait 5 seconds
        print("⏳ Waiting 5 seconds before final test...")
        time.sleep(5)
        
        # Test 3: Final check
        success3, data3 = self.test_job_status_single(3)
        test_results.append(success3)
        if data3:
            job_responses.append(data3)
        
        # Add CORS result
        test_results.append(cors_success)
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 SPECIFIC JOB STATUS TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Analyze progress changes
        if len(job_responses) >= 2:
            print("📊 PROGRESS ANALYSIS:")
            print("-" * 40)
            
            for i, response in enumerate(job_responses, 1):
                progress = response.get('progress', 'N/A')
                status = response.get('status', 'N/A')
                print(f"Test #{i}: Progress={progress}%, Status={status}")
            
            # Check if progress changed
            progresses = [r.get('progress') for r in job_responses if r.get('progress') is not None]
            if len(progresses) >= 2:
                if progresses[0] != progresses[-1]:
                    print(f"✅ PROGRESS CHANGED: {progresses[0]}% → {progresses[-1]}%")
                    print("🎉 FFmpeg Lambda processing is working!")
                elif progresses[0] == 25:
                    print(f"⚠️  PROGRESS STILL AT 25%: May still be processing or stuck")
                else:
                    print(f"ℹ️  PROGRESS STABLE: {progresses[0]}% (may be normal)")
            
            print()
        
        # Check SUCCESS CRITERIA from review request
        success_criteria_met = []
        
        if any(test_results[:3]):  # At least one job status test passed
            success_criteria_met.append("✅ Job status endpoint is responding")
        else:
            success_criteria_met.append("❌ Job status endpoint not responding")
        
        if cors_success:
            success_criteria_met.append("✅ CORS headers working properly")
        else:
            success_criteria_met.append("❌ CORS headers not working")
        
        if len(job_responses) > 0:
            latest_response = job_responses[-1]
            if latest_response.get('progress') != 25:
                success_criteria_met.append("✅ Progress has changed from 25%")
            else:
                success_criteria_met.append("⚠️  Progress still at 25% (may still be processing)")
            
            if latest_response.get('status') == 'processing':
                success_criteria_met.append("✅ Status is 'processing' as expected")
            else:
                success_criteria_met.append(f"ℹ️  Status: {latest_response.get('status')}")
        
        print("REVIEW REQUEST VERIFICATION:")
        for criterion in success_criteria_met:
            print(criterion)
        
        print()
        print("EXPECTED OUTCOME:")
        if success_rate >= 75:
            print("✅ Job status endpoint is working and can track the specific job")
            if len(job_responses) > 0 and job_responses[-1].get('progress', 25) != 25:
                print("✅ FFmpeg Lambda processing appears to be working - progress has changed")
            else:
                print("ℹ️  Job may still be processing or completed - check progress values above")
        else:
            print("❌ Job status endpoint has issues - see failed tests above")
        
        print()
        return success_rate >= 75

if __name__ == "__main__":
    tester = JobStatusSpecificTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)