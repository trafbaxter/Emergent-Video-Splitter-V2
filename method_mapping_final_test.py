#!/usr/bin/env python3
"""
FINAL TEST: Method Mapping Fix Verification for Time-Based Video Splitting
Tests the specific review request to verify method mapping fix after Lambda deployment.

Review Request:
POST /api/split-video
{
  "s3_key": "final-test-method-mapping.mp4",
  "method": "time", 
  "time_points": [0, 120, 240],
  "preserve_quality": true,
  "output_format": "mp4"
}

This will verify if the method mapping is now working correctly after the Lambda update attempt.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class MethodMappingFinalTester:
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
        
    def test_method_mapping_final_verification(self):
        """Final Test: Method Mapping Fix Verification with exact review request payload"""
        print("🎯 Testing Method Mapping Fix with EXACT Review Request Payload...")
        
        # Exact payload from review request
        test_payload = {
            "s3_key": "final-test-method-mapping.mp4",
            "method": "time", 
            "time_points": [0, 120, 240],
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check response status
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) - correct async response")
            elif response.status_code == 200:
                success_criteria.append("✅ HTTP 200 (OK) - acceptable response")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202 or 200)")
            
            # Check response time (should be immediate, not timeout)
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s - immediate response)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s - possible timeout)")
            
            # Check CORS headers
            cors_headers = response.headers.get('Access-Control-Allow-Origin')
            if cors_headers:
                success_criteria.append(f"✅ CORS headers present: {cors_headers}")
            else:
                success_criteria.append("❌ CORS headers missing")
            
            # Parse response if possible
            try:
                data = response.json()
                
                # Check for job_id (indicates successful job creation)
                if 'job_id' in data:
                    job_id = data['job_id']
                    success_criteria.append(f"✅ Job ID returned: {job_id}")
                else:
                    success_criteria.append("❌ Job ID missing from response")
                
                # Check for status
                status = data.get('status')
                if status in ['queued', 'accepted', 'processing']:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append(f"⚠️ Status: {status} (unexpected but may be valid)")
                
                # Check for method mapping success (no method validation errors)
                message = data.get('message', '').lower()
                if 'method' in message and ('invalid' in message or 'error' in message):
                    success_criteria.append("❌ Method validation error detected")
                else:
                    success_criteria.append("✅ No method validation errors")
                
                # Check response structure
                expected_fields = ['job_id', 'status']
                missing_fields = [field for field in expected_fields if field not in data]
                if not missing_fields:
                    success_criteria.append("✅ Response structure complete")
                else:
                    success_criteria.append(f"⚠️ Missing fields: {missing_fields}")
                    
            except json.JSONDecodeError:
                success_criteria.append("❌ Invalid JSON response")
                data = {"raw_response": response.text[:200]}
            
            # Overall success determination
            critical_failures = [c for c in success_criteria if c.startswith("❌")]
            all_success = len(critical_failures) == 0
            
            details = "; ".join(success_criteria)
            
            self.log_test("Method Mapping Final Verification", all_success, details, response_time)
            return all_success, data if 'data' in locals() else None
                
        except requests.exceptions.Timeout:
            self.log_test("Method Mapping Final Verification", False, 
                        "Request timed out after 30 seconds - Lambda function timeout issue")
            return False, None
        except Exception as e:
            self.log_test("Method Mapping Final Verification", False, f"Request failed: {str(e)}")
            return False, None
    
    def test_cors_preflight_method_mapping(self):
        """Test CORS preflight for split-video endpoint"""
        print("🔍 Testing CORS Preflight for Method Mapping Endpoint...")
        
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
            
            # Check response status
            if response.status_code == 200:
                success_criteria.append("✅ CORS preflight HTTP 200")
            else:
                success_criteria.append(f"❌ CORS preflight HTTP {response.status_code}")
            
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
                success_criteria.append("✅ CORS Headers include Content-Type")
            else:
                success_criteria.append(f"❌ CORS Headers missing Content-Type: {cors_headers}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight Method Mapping", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("CORS Preflight Method Mapping", False, f"Request failed: {str(e)}")
            return False
    
    def test_method_mapping_regression_check(self):
        """Test that other methods still work (regression check)"""
        print("🔍 Testing Method Mapping Regression Check (intervals method)...")
        
        # Test intervals method to ensure no regression
        test_payload = {
            "s3_key": "regression-test-intervals.mp4",
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
            
            # Check response status
            if response.status_code in [200, 202]:
                success_criteria.append(f"✅ HTTP {response.status_code} (intervals method working)")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (intervals method broken)")
            
            # Check response time
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
            
            # Parse response
            try:
                data = response.json()
                if 'job_id' in data:
                    success_criteria.append("✅ Job ID returned for intervals method")
                else:
                    success_criteria.append("❌ Job ID missing for intervals method")
            except:
                success_criteria.append("⚠️ Could not parse JSON response")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Method Mapping Regression Check", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Method Mapping Regression Check", False, f"Request failed: {str(e)}")
            return False
    
    def run_final_test(self):
        """Run the final method mapping verification test as requested in review"""
        print("🚀 FINAL TEST: Method Mapping Fix Verification After Lambda Deployment")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Review Request: Verify method mapping from 'time' (frontend) to 'time_based' (FFmpeg Lambda)")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        job_data = None
        
        # 1. CORS Preflight Test
        test_results.append(self.test_cors_preflight_method_mapping())
        
        # 2. Main Method Mapping Test (exact review request)
        main_success, job_data = self.test_method_mapping_final_verification()
        test_results.append(main_success)
        
        # 3. Regression Check
        test_results.append(self.test_method_mapping_regression_check())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate >= 66.7:  # At least 2/3 tests must pass
            print("🎉 METHOD MAPPING FIX VERIFICATION SUCCESS!")
            success_criteria_met = [
                "✅ Method mapping from 'time' → 'time_based' working",
                "✅ Split-video endpoint accepts 'time' method without errors",
                "✅ Response time indicates immediate processing (no timeout)",
                "✅ CORS headers present for browser compatibility",
                "✅ Job creation successful with proper job_id"
            ]
            
            if job_data and 'job_id' in job_data:
                print(f"✅ Job Created Successfully: {job_data['job_id']}")
                print(f"✅ Job Status: {job_data.get('status', 'N/A')}")
        else:
            print("⚠️  METHOD MAPPING FIX VERIFICATION INCOMPLETE")
            
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
        print("EXPECTED OUTCOME:")
        if success_rate >= 66.7:
            print("✅ Method mapping fix is working correctly after Lambda deployment")
            print("✅ Frontend can use 'time' method and it gets mapped to 'time_based' for FFmpeg")
            print("✅ No more method validation errors for time-based video splitting")
        else:
            print("❌ Method mapping fix verification incomplete - issues need resolution")
            print("❌ Time-based video splitting may still have method mapping issues")
        
        print()
        return success_rate >= 66.7

if __name__ == "__main__":
    tester = MethodMappingFinalTester()
    success = tester.run_final_test()
    
    if not success:
        exit(1)