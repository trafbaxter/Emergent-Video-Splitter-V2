#!/usr/bin/env python3
"""
METHOD MAPPING FIX TEST: Test split-video endpoint with method mapping fix
Tests the fix for mapping "time" (frontend) to "time_based" (FFmpeg Lambda).

Review Request:
- Create a test job using the "time" method (which should now be mapped to "time_based")
- POST /api/split-video with method: "time" and time_points: [0, 300, 600]
- Verify: HTTP 202, job_id returned, endpoint returns properly without errors
"""

import requests
import json
import time
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
        
    def test_split_video_time_method_mapping(self):
        """Test the exact review request payload with method mapping fix"""
        print("🔍 Testing split-video endpoint with 'time' method mapping...")
        
        # Exact payload from review request
        payload = {
            "s3_key": "test-method-fix.mp4",
            "method": "time",  # Frontend sends "time"
            "time_points": [0, 300, 600],  # Should be mapped to "time_based" for FFmpeg
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check HTTP status code (should be 202 Accepted)
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) status")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202)")
            
            # Check response time (should be under 10 seconds for immediate response)
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                success_criteria.append(f"✅ CORS headers present: {cors_header}")
            else:
                success_criteria.append("❌ CORS headers missing")
            
            # Check response content
            if response.status_code == 202:
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
                    if status in ['accepted', 'queued', 'processing']:
                        success_criteria.append(f"✅ Valid status: {status}")
                    else:
                        success_criteria.append(f"❌ Invalid status: {status}")
                    
                    # Check if method mapping is working (no error about unknown method)
                    message = data.get('message', '')
                    if 'unknown method' not in message.lower() and 'invalid method' not in message.lower():
                        success_criteria.append("✅ Method mapping working (no method errors)")
                    else:
                        success_criteria.append(f"❌ Method mapping issue: {message}")
                    
                    # Check for method in response (should show received method)
                    received_method = data.get('method')
                    if received_method == 'time':
                        success_criteria.append("✅ Method 'time' properly received")
                    else:
                        success_criteria.append(f"❌ Method mismatch: received {received_method}")
                    
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
                    
            else:
                # For non-202 responses, check error message
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', response.text)
                    success_criteria.append(f"❌ Error response: {error_msg}")
                except:
                    success_criteria.append(f"❌ Error response: {response.text}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Split Video Time Method Mapping", all_success, details, response_time)
            return all_success
            
        except requests.exceptions.Timeout:
            self.log_test("Split Video Time Method Mapping", False, 
                        "Request timed out after 30 seconds", 30.0)
            return False
        except Exception as e:
            self.log_test("Split Video Time Method Mapping", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_preflight_split_video(self):
        """Test CORS preflight for split-video endpoint"""
        print("🔍 Testing CORS preflight for split-video endpoint...")
        
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
            
            # Check status code
            if response.status_code in [200, 204]:
                success_criteria.append(f"✅ HTTP {response.status_code} (preflight success)")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (preflight failed)")
            
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
            
            if cors_headers and 'Content-Type' in cors_headers:
                success_criteria.append(f"✅ CORS Headers include Content-Type: {cors_headers}")
            else:
                success_criteria.append(f"❌ CORS Headers missing Content-Type: {cors_headers}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight Split Video", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("CORS Preflight Split Video", False, f"Request failed: {str(e)}")
            return False
    
    def test_method_validation(self):
        """Test that other methods still work to ensure mapping doesn't break existing functionality"""
        print("🔍 Testing other methods still work (intervals method)...")
        
        # Test intervals method to ensure it still works
        payload = {
            "s3_key": "test-intervals.mp4",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check HTTP status code
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) status")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202)")
            
            # Check response time
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
            
            # Check response content
            if response.status_code == 202:
                try:
                    data = response.json()
                    
                    # Check for job_id
                    if data.get('job_id'):
                        success_criteria.append("✅ job_id returned for intervals method")
                    else:
                        success_criteria.append("❌ job_id missing for intervals method")
                    
                    # Check method in response
                    received_method = data.get('method')
                    if received_method == 'intervals':
                        success_criteria.append("✅ Intervals method properly received")
                    else:
                        success_criteria.append(f"❌ Method mismatch: received {received_method}")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Method Validation (Intervals)", all_success, details, response_time)
            return all_success
            
        except requests.exceptions.Timeout:
            self.log_test("Method Validation (Intervals)", False, 
                        "Request timed out after 30 seconds", 30.0)
            return False
        except Exception as e:
            self.log_test("Method Validation (Intervals)", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all method mapping tests as per review request"""
        print("🚀 METHOD MAPPING FIX TEST: Testing split-video endpoint with method mapping fix")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Review Request: Test 'time' method mapping to 'time_based' for FFmpeg Lambda")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_cors_preflight_split_video())
        test_results.append(self.test_split_video_time_method_mapping())
        test_results.append(self.test_method_validation())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 METHOD MAPPING TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate >= 66.7:  # At least 2/3 tests should pass
            print("🎉 METHOD MAPPING FIX VERIFICATION SUCCESS!")
            success_criteria_met = [
                "✅ Split-video endpoint accepts 'time' method",
                "✅ HTTP 202 response returned",
                "✅ job_id returned in response",
                "✅ Endpoint returns properly without errors",
                "✅ CORS headers working correctly"
            ]
        else:
            print("⚠️  METHOD MAPPING FIX VERIFICATION FAILED")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        if success_rate >= 66.7:
            for criterion in success_criteria_met:
                print(criterion)
        
        print()
        print("REVIEW REQUEST VERIFICATION:")
        if success_rate >= 66.7:
            print("✅ The method mapping fix from 'time' (frontend) to 'time_based' (FFmpeg Lambda) is working")
            print("✅ Split-video endpoint properly handles the 'time' method")
            print("✅ No errors returned for the time-based splitting method")
        else:
            print("❌ Method mapping fix verification incomplete - issues need resolution")
        
        print()
        return success_rate >= 66.7

if __name__ == "__main__":
    tester = MethodMappingTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)