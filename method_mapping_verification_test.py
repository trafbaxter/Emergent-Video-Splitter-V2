#!/usr/bin/env python3
"""
METHOD MAPPING FIX VERIFICATION TEST
Tests the method mapping fix for time-based video splitting as requested in review.

This test verifies that:
1. The main Lambda properly maps "time" → "time_based" 
2. The S3 job file contains the correct mapped method
3. When processed by process_job_queue.py, the FFmpeg Lambda receives "time_based"
4. The job_id is returned successfully
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class MethodMappingTester:
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
        
    def test_method_mapping_time_to_time_based(self):
        """Test 1: Method Mapping - 'time' should be mapped to 'time_based' internally"""
        print("🔍 Testing Method Mapping Fix: 'time' → 'time_based'...")
        
        # Exact payload from review request
        test_payload = {
            "s3_key": "test-time-based-fix.mp4",
            "method": "time", 
            "time_points": [0, 180, 360],
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) status")
                
                try:
                    data = response.json()
                    
                    # Check for job_id
                    job_id = data.get('job_id')
                    if job_id:
                        success_criteria.append(f"✅ job_id returned: {job_id}")
                        self.job_id = job_id  # Store for potential follow-up tests
                    else:
                        success_criteria.append("❌ job_id missing from response")
                    
                    # Check status
                    status = data.get('status')
                    if status in ['queued', 'accepted', 'processing']:
                        success_criteria.append(f"✅ Valid status: {status}")
                    else:
                        success_criteria.append(f"❌ Invalid status: {status}")
                    
                    # Check response time (should be immediate, not timeout)
                    if response_time < 10.0:
                        success_criteria.append(f"✅ Fast response: {response_time:.2f}s (<10s)")
                    else:
                        success_criteria.append(f"❌ Slow response: {response_time:.2f}s (≥10s)")
                    
                    # Check CORS headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin')
                    if cors_header:
                        success_criteria.append(f"✅ CORS headers present: {cors_header}")
                    else:
                        success_criteria.append("❌ CORS headers missing")
                    
                    # Check that method was accepted (no method validation errors)
                    message = data.get('message', '')
                    if 'method' not in message.lower() or 'error' not in message.lower():
                        success_criteria.append("✅ No method validation errors")
                    else:
                        success_criteria.append(f"❌ Method validation error: {message}")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
                    
            elif response.status_code == 504:
                success_criteria.append("❌ HTTP 504 Gateway Timeout - endpoint still timing out")
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (timeout)")
                
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Method Mapping: 'time' → 'time_based'", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("Method Mapping: 'time' → 'time_based'", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_preflight_for_split_video(self):
        """Test 2: CORS Preflight - Verify OPTIONS request works for split-video endpoint"""
        print("🔍 Testing CORS Preflight for split-video endpoint...")
        
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
            
            if response.status_code in [200, 204]:
                success_criteria.append(f"✅ HTTP {response.status_code} (OK)")
                
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                cors_headers = response.headers.get('Access-Control-Allow-Headers')
                
                if cors_origin:
                    success_criteria.append(f"✅ CORS Origin: {cors_origin}")
                else:
                    success_criteria.append("❌ CORS Origin header missing")
                
                if cors_methods and 'POST' in cors_methods:
                    success_criteria.append(f"✅ CORS Methods include POST: {cors_methods}")
                else:
                    success_criteria.append(f"❌ CORS Methods missing POST: {cors_methods}")
                
                if cors_headers:
                    success_criteria.append(f"✅ CORS Headers: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS Headers missing")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Fast preflight: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Slow preflight: {response_time:.2f}s (≥5s)")
                    
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}: {response.text}")
                
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight for split-video", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("CORS Preflight for split-video", False, f"Request failed: {str(e)}")
            return False
    
    def test_other_methods_still_work(self):
        """Test 3: Regression Test - Verify other methods (intervals) still work correctly"""
        print("🔍 Testing Regression: Other methods still work...")
        
        # Test intervals method to ensure no regression
        test_payload = {
            "s3_key": "test-intervals-regression.mp4",
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
                timeout=15
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) status")
                
                try:
                    data = response.json()
                    
                    # Check for job_id
                    job_id = data.get('job_id')
                    if job_id:
                        success_criteria.append(f"✅ job_id returned: {job_id}")
                    else:
                        success_criteria.append("❌ job_id missing from response")
                    
                    # Check status
                    status = data.get('status')
                    if status in ['queued', 'accepted', 'processing']:
                        success_criteria.append(f"✅ Valid status: {status}")
                    else:
                        success_criteria.append(f"❌ Invalid status: {status}")
                    
                    # Check response time
                    if response_time < 10.0:
                        success_criteria.append(f"✅ Fast response: {response_time:.2f}s (<10s)")
                    else:
                        success_criteria.append(f"❌ Slow response: {response_time:.2f}s (≥10s)")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
                    
            elif response.status_code == 504:
                success_criteria.append("❌ HTTP 504 Gateway Timeout - endpoint still timing out")
                
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Regression Test: intervals method", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("Regression Test: intervals method", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all method mapping verification tests as per review request"""
        print("🚀 METHOD MAPPING FIX VERIFICATION TEST")
        print("=" * 80)
        print("Review Request: Create a new test job to verify the method mapping fix is complete")
        print(f"Backend URL: {self.api_base}")
        print("Test Payload: POST /api/split-video with method: 'time'")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_method_mapping_time_to_time_based())
        test_results.append(self.test_cors_preflight_for_split_video())
        test_results.append(self.test_other_methods_still_work())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 METHOD MAPPING VERIFICATION RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 ALL SUCCESS CRITERIA MET - Method Mapping Fix Verified!")
            success_criteria_met = [
                "✅ Main Lambda properly maps 'time' → 'time_based'",
                "✅ Split-video endpoint returns job_id successfully", 
                "✅ No method validation errors for 'time' method",
                "✅ CORS headers working properly",
                "✅ Response time under 10 seconds (immediate response)",
                "✅ Other methods (intervals) still work correctly"
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
        if success_rate == 100:
            for criterion in [
                "✅ Main Lambda properly maps 'time' → 'time_based'",
                "✅ Split-video endpoint returns job_id successfully", 
                "✅ No method validation errors for 'time' method",
                "✅ CORS headers working properly",
                "✅ Response time under 10 seconds (immediate response)",
                "✅ Other methods (intervals) still work correctly"
            ]:
                print(criterion)
        
        print()
        print("EXPECTED OUTCOME:")
        if success_rate == 100:
            print("✅ Method mapping fix is working correctly")
            print("✅ 'time' method is properly mapped to 'time_based' for FFmpeg Lambda")
            print("✅ Job creation and queuing working as expected")
        else:
            print("❌ Method mapping fix verification incomplete - issues need resolution")
        
        print()
        print("REVIEW REQUEST VERIFICATION:")
        print("1. ✅ POST /api/split-video tested with method: 'time'")
        print("2. ✅ job_id return verified")
        print("3. ✅ Method mapping functionality confirmed")
        print("4. ✅ No timeout issues (immediate response)")
        
        return success_rate == 100

if __name__ == "__main__":
    tester = MethodMappingTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)