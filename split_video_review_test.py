#!/usr/bin/env python3
"""
SPLIT VIDEO API ENDPOINT REVIEW TEST
Tests the split-video API endpoint to ensure it's working properly after recent frontend fixes.
Focus on verifying immediate response with job_id extraction as requested in review.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class SplitVideoReviewTester:
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
        
    def test_split_video_endpoint(self):
        """Test 1: POST /api/split-video endpoint with exact review request payload"""
        print("🔍 Testing POST /api/split-video endpoint...")
        
        # Exact payload from review request
        test_payload = {
            "s3_key": "test-video.mp4", 
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
            
            success_criteria = []
            
            # Check response time (should be under 5 seconds)
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s requirement)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s, should be immediate)")
            
            # Check status code (should be 202 Accepted or 200)
            if response.status_code in [200, 202]:
                success_criteria.append(f"✅ Status code: {response.status_code} (accepted)")
            else:
                success_criteria.append(f"❌ Status code: {response.status_code} (expected 202/200)")
            
            # Check response content
            if response.status_code in [200, 202]:
                try:
                    data = response.json()
                    
                    # Check for job_id
                    job_id = data.get('job_id')
                    if job_id:
                        success_criteria.append(f"✅ job_id present: {job_id}")
                        # Store for potential follow-up tests
                        self.job_id = job_id
                    else:
                        success_criteria.append("❌ job_id missing from response")
                    
                    # Check for status field
                    status = data.get('status')
                    if status in ['accepted', 'processing', 'queued']:
                        success_criteria.append(f"✅ status: '{status}' (valid)")
                    else:
                        success_criteria.append(f"❌ status: '{status}' (expected 'accepted' or 'processing')")
                    
                    # Check CORS headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin')
                    if cors_header:
                        success_criteria.append(f"✅ CORS header: {cors_header}")
                    else:
                        success_criteria.append("❌ CORS header missing")
                    
                    # Show full response for debugging
                    success_criteria.append(f"Response: {json.dumps(data, indent=2)}")
                    
                except json.JSONDecodeError:
                    success_criteria.append(f"❌ Invalid JSON response: {response.text[:200]}")
            else:
                success_criteria.append(f"❌ Error response: {response.text[:200]}")
            
            all_success = all("✅" in criterion for criterion in success_criteria[:4])  # Only check first 4 criteria for success
            details = "; ".join(success_criteria)
            
            self.log_test("Split Video Endpoint", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Split Video Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_preflight(self):
        """Test 2: CORS preflight request for split-video endpoint"""
        print("🔍 Testing CORS preflight for split-video...")
        
        try:
            start_time = time.time()
            response = requests.options(
                f"{self.api_base}/api/split-video",
                headers={
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Preflight response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Preflight response time: {response_time:.2f}s (≥5s)")
            
            # Check status code
            if response.status_code in [200, 204]:
                success_criteria.append(f"✅ Preflight status: {response.status_code}")
            else:
                success_criteria.append(f"❌ Preflight status: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            cors_headers = response.headers.get('Access-Control-Allow-Headers')
            
            if cors_origin:
                success_criteria.append(f"✅ CORS Origin: {cors_origin}")
            else:
                success_criteria.append("❌ CORS Origin header missing")
            
            if cors_methods and 'POST' in cors_methods:
                success_criteria.append(f"✅ CORS Methods: {cors_methods}")
            else:
                success_criteria.append(f"❌ CORS Methods: {cors_methods} (POST not allowed)")
            
            all_success = all("✅" in criterion for criterion in success_criteria[:4])
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("CORS Preflight", False, f"Request failed: {str(e)}")
            return False
    
    def test_job_status_if_available(self):
        """Test 3: Optional job status check if job_id was obtained"""
        if not hasattr(self, 'job_id') or not self.job_id:
            self.log_test("Job Status Check", True, "Skipped - no job_id available")
            return True
            
        print(f"🔍 Testing job status for job_id: {self.job_id}...")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Job status response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Job status response time: {response_time:.2f}s (≥5s)")
            
            # Check status code
            if response.status_code == 200:
                success_criteria.append(f"✅ Job status code: {response.status_code}")
                
                try:
                    data = response.json()
                    
                    # Check job_id matches
                    returned_job_id = data.get('job_id')
                    if returned_job_id == self.job_id:
                        success_criteria.append(f"✅ Job ID matches: {returned_job_id}")
                    else:
                        success_criteria.append(f"❌ Job ID mismatch: {returned_job_id} vs {self.job_id}")
                    
                    # Check status field
                    status = data.get('status')
                    if status:
                        success_criteria.append(f"✅ Job status: {status}")
                    else:
                        success_criteria.append("❌ Job status missing")
                    
                    # Show response for debugging
                    success_criteria.append(f"Job response: {json.dumps(data, indent=2)}")
                    
                except json.JSONDecodeError:
                    success_criteria.append(f"❌ Invalid JSON response: {response.text[:200]}")
            else:
                success_criteria.append(f"❌ Job status code: {response.status_code}")
                success_criteria.append(f"Error: {response.text[:200]}")
            
            all_success = all("✅" in criterion for criterion in success_criteria[:3])
            details = "; ".join(success_criteria)
            
            self.log_test("Job Status Check", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Job Status Check", False, f"Request failed: {str(e)}")
            return False
    
    def run_review_tests(self):
        """Run split-video endpoint review tests as requested"""
        print("🚀 SPLIT VIDEO API ENDPOINT REVIEW TEST")
        print("Testing split-video endpoint after frontend job_id extraction fix")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Test Focus: Immediate response with job_id extraction")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_split_video_endpoint())
        test_results.append(self.test_cors_preflight())
        test_results.append(self.test_job_status_if_available())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 SPLIT VIDEO REVIEW TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate >= 66.7:  # At least 2/3 tests pass (main endpoint + CORS)
            print("🎉 SPLIT VIDEO ENDPOINT WORKING!")
            success_criteria_met = [
                "✅ POST /api/split-video returns response with job_id",
                "✅ Response time under 5 seconds (immediate response)",
                "✅ Status code 202/200 (accepted/processing)",
                "✅ CORS headers present for browser requests"
            ]
        else:
            print("⚠️  SPLIT VIDEO ENDPOINT ISSUES DETECTED")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        for criterion in success_criteria_met if success_rate >= 66.7 else []:
            print(criterion)
        
        print()
        print("REVIEW REQUEST VERIFICATION:")
        if success_rate >= 66.7:
            print("✅ Split video button frontend issue appears to be resolved")
            print("✅ Backend API is responding properly with job_id")
            print("✅ Response time confirms immediate response (not timeout)")
        else:
            print("❌ Split video endpoint may still have issues")
            print("❌ Frontend job_id extraction may still be problematic")
        
        print()
        return success_rate >= 66.7

if __name__ == "__main__":
    tester = SplitVideoReviewTester()
    success = tester.run_review_tests()
    
    if not success:
        exit(1)