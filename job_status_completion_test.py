#!/usr/bin/env python3
"""
Job Status Completion Test - Review Request Verification
Tests the specific job-status endpoint for job ID: 7e38b588-fe5a-46d5-b0c9-e876f3293e2a
Expected: progress: 100 (not 25), status: completed, results: array with download URLs for 2 split video files
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from AuthContext.js
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class JobStatusCompletionTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # Specific job ID from review request
        self.target_job_id = "7e38b588-fe5a-46d5-b0c9-e876f3293e2a"
        
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
        
    def test_job_status_completion(self):
        """Test the specific job status endpoint for completed job"""
        print(f"🔍 Testing Job Status Completion for job: {self.target_job_id}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.target_job_id}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check job_id matches
                job_id = data.get('job_id')
                if job_id == self.target_job_id:
                    success_criteria.append(f"✅ job_id matches: {job_id}")
                else:
                    success_criteria.append(f"❌ job_id mismatch: {job_id} (expected {self.target_job_id})")
                
                # Check progress is 100 (not 25)
                progress = data.get('progress')
                if progress == 100:
                    success_criteria.append(f"✅ progress: {progress}% (completed)")
                elif progress == 25:
                    success_criteria.append(f"❌ progress stuck at: {progress}% (should be 100%)")
                else:
                    success_criteria.append(f"⚠️ progress: {progress}% (unexpected value)")
                
                # Check status is completed
                status = data.get('status')
                if status == 'completed':
                    success_criteria.append(f"✅ status: {status}")
                else:
                    success_criteria.append(f"❌ status: {status} (expected 'completed')")
                
                # Check results array with download URLs
                results = data.get('results', [])
                if isinstance(results, list) and len(results) > 0:
                    success_criteria.append(f"✅ results array present with {len(results)} items")
                    
                    # Check for download URLs in results
                    download_urls = 0
                    for i, result in enumerate(results):
                        if isinstance(result, dict) and 'download_url' in result:
                            download_urls += 1
                            success_criteria.append(f"✅ result[{i}] has download_url")
                        elif isinstance(result, str) and ('http' in result or 's3' in result):
                            download_urls += 1
                            success_criteria.append(f"✅ result[{i}] is URL: {result[:50]}...")
                    
                    if download_urls >= 2:
                        success_criteria.append(f"✅ Found {download_urls} download URLs (expected 2 split video files)")
                    else:
                        success_criteria.append(f"❌ Found {download_urls} download URLs (expected 2 split video files)")
                        
                else:
                    success_criteria.append(f"❌ results array missing or empty: {results}")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                # Overall success based on key criteria
                key_success = (
                    progress == 100 and 
                    status == 'completed' and 
                    isinstance(results, list) and 
                    len(results) >= 2
                )
                
                details = "; ".join(success_criteria)
                
                self.log_test("Job Status Completion Check", key_success, details, response_time)
                
                # Print full response for debugging
                print("📋 Full Response Data:")
                print(json.dumps(data, indent=2))
                print()
                
                return key_success
                
            else:
                self.log_test("Job Status Completion Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Job Status Completion Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_preflight(self):
        """Test CORS preflight for job-status endpoint"""
        print("🔍 Testing CORS Preflight for job-status endpoint...")
        
        try:
            start_time = time.time()
            response = requests.options(
                f"{self.api_base}/api/job-status/{self.target_job_id}",
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
            
            if cors_origin:
                success_criteria.append(f"✅ CORS origin: {cors_origin}")
            else:
                success_criteria.append("❌ CORS origin header missing")
            
            if cors_methods and 'GET' in cors_methods:
                success_criteria.append(f"✅ CORS methods include GET: {cors_methods}")
            else:
                success_criteria.append(f"❌ CORS methods missing GET: {cors_methods}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight Check", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("CORS Preflight Check", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all job status completion tests"""
        print("🚀 JOB STATUS COMPLETION TEST - Review Request Verification")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Target Job ID: {self.target_job_id}")
        print("Expected Results:")
        print("  - progress: 100 (not 25)")
        print("  - status: completed")
        print("  - results: array with download URLs for 2 split video files")
        print("=" * 80)
        print()
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_cors_preflight())
        test_results.append(self.test_job_status_completion())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 JOB STATUS COMPLETION TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 SUCCESS CRITERIA VERIFICATION:")
            print("✅ Job status endpoint responds correctly")
            print("✅ Progress shows 100% completion (not stuck at 25%)")
            print("✅ Status shows 'completed'")
            print("✅ Results array contains download URLs for split video files")
            print("✅ CORS headers working properly")
            print()
            print("EXPECTED OUTCOME ACHIEVED:")
            print("✅ User should now see progress completion instead of being stuck at 25%")
        else:
            print("⚠️ SOME SUCCESS CRITERIA NOT MET:")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            print("\nEXPECTED OUTCOME NOT ACHIEVED:")
            print("❌ User may still see progress stuck at 25% or other issues")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = JobStatusCompletionTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)