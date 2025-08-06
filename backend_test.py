#!/usr/bin/env python3
"""
URGENT: Test split-video CORS and timeout fix

CRITICAL OBJECTIVE:
Verify that the split-video endpoint now returns HTTP 202 immediately with proper CORS headers 
instead of timing out with 504 and CORS errors.

SPECIFIC TEST:
1. Test POST /api/split-video with exact payload from review request
2. MUST return HTTP 202 in under 5 seconds (not 504 timeout)
3. MUST include CORS headers (Access-Control-Allow-Origin)
4. Should include job_id, status: "accepted", and other fields

SUCCESS CRITERIA:
✅ HTTP 202 status (not 504)
✅ Response time < 5 seconds (not 29+ seconds)  
✅ CORS headers present (Access-Control-Allow-Origin)
✅ Response includes job_id and status fields
✅ No "Failed to fetch" errors from browser
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration - Using the backend URL from AuthContext.js
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30  # 30 second timeout for testing immediate response

class SplitVideoTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Dict = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data
        })
        print()

    def test_cors_preflight(self):
        """Test CORS preflight request for split-video endpoint"""
        print("🔍 Testing CORS Preflight for split-video endpoint...")
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            start_time = time.time()
            response = self.session.options(f"{self.base_url}/api/split-video", headers=headers)
            response_time = time.time() - start_time
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            cors_headers = response.headers.get('Access-Control-Allow-Headers')
            
            if response.status_code == 200 and cors_origin:
                self.log_test(
                    "CORS Preflight for split-video",
                    True,
                    f"✅ CORS preflight working! Origin: {cors_origin}, Methods: {cors_methods}, Response time: {response_time:.2f}s"
                )
                return True
            else:
                self.log_test(
                    "CORS Preflight for split-video",
                    False,
                    f"CORS preflight failed. Status: {response.status_code}, Origin header: {cors_origin}"
                )
                return False
                
        except Exception as e:
            self.log_test("CORS Preflight for split-video", False, f"Error: {str(e)}")
            return False

    def test_split_video_immediate_response(self):
        """Test the critical split-video immediate response fix"""
        print("🚨 CRITICAL TEST: Split-video immediate response...")
        
        # Exact payload from review request
        split_data = {
            "s3_key": "uploads/test/sample-video.mkv", 
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            print(f"   🎯 Testing with exact review request payload...")
            print(f"   📋 Payload: {json.dumps(split_data, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            # SUCCESS CRITERIA CHECK
            success_criteria = {
                'http_202': response.status_code == 202,
                'under_5_seconds': response_time < 5.0,
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 202 status: {'PASS' if success_criteria['http_202'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Response < 5s: {'PASS' if success_criteria['under_5_seconds'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            if response.status_code == 202:
                # Parse response for job_id and status
                try:
                    data = response.json()
                    job_id = data.get('job_id')
                    status = data.get('status')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    
                    if job_id and status:
                        success_criteria['response_fields'] = True
                        print(f"      ✅ Response fields: PASS")
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing job_id or status)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
                    data = {}
            else:
                success_criteria['response_fields'] = False
                try:
                    data = response.json() if response.content else {}
                except:
                    data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    "🎉 SPLIT-VIDEO IMMEDIATE RESPONSE FIX SUCCESS",
                    True,
                    f"✅ ALL SUCCESS CRITERIA MET! HTTP 202 in {response_time:.2f}s with CORS headers and proper response fields. The timeout and CORS issues are COMPLETELY RESOLVED!"
                )
            elif response.status_code == 504:
                self.log_test(
                    "❌ SPLIT-VIDEO TIMEOUT STILL PRESENT",
                    False,
                    f"🚨 CRITICAL: Still getting HTTP 504 Gateway Timeout after {response_time:.2f}s. The timeout fix has NOT resolved the issue. CORS: {cors_origin}"
                )
            elif response_time >= 5.0:
                self.log_test(
                    "❌ SPLIT-VIDEO SLOW RESPONSE",
                    False,
                    f"Response time {response_time:.2f}s exceeds 5s threshold. Status: {response.status_code}, CORS: {cors_origin}"
                )
            elif not cors_origin:
                self.log_test(
                    "❌ SPLIT-VIDEO CORS MISSING",
                    False,
                    f"Missing CORS headers. Status: {response.status_code}, Response time: {response_time:.2f}s"
                )
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    "❌ SPLIT-VIDEO PARTIAL SUCCESS",
                    False,
                    f"Some criteria failed: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s, CORS: {cors_origin}",
                    data
                )
                
            return all_criteria_met
            
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ SPLIT-VIDEO CLIENT TIMEOUT",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - endpoint is not responding fast enough"
            )
            return False
        except Exception as e:
            self.log_test(
                "❌ SPLIT-VIDEO ERROR",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_basic_connectivity(self):
        """Quick connectivity test"""
        print("🔍 Testing Basic Connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Basic API Connectivity", 
                    True, 
                    f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
                )
                return True
            else:
                self.log_test("Basic API Connectivity", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}")
            return False

    def run_split_video_test(self):
        """Run the focused split-video test as requested in review"""
        print("=" * 80)
        print("🚨 URGENT: SPLIT-VIDEO CORS AND TIMEOUT FIX TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 CRITICAL OBJECTIVE:")
        print("   Verify split-video endpoint returns HTTP 202 immediately with CORS headers")
        print("   instead of timing out with 504 and CORS errors")
        print()
        print("📋 SUCCESS CRITERIA:")
        print("   ✅ HTTP 202 status (not 504)")
        print("   ✅ Response time < 5 seconds (not 29+ seconds)")
        print("   ✅ CORS headers present (Access-Control-Allow-Origin)")
        print("   ✅ Response includes job_id and status fields")
        print("   ✅ No 'Failed to fetch' errors from browser")
        print()
        
        # Run tests in order
        connectivity_ok = self.test_basic_connectivity()
        cors_ok = self.test_cors_preflight()
        split_video_ok = self.test_split_video_immediate_response()
        
        # Summary
        print("=" * 80)
        print("📊 SPLIT-VIDEO TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical assessment
        print("💡 CRITICAL ASSESSMENT:")
        
        if split_video_ok:
            print("   🎉 SPLIT-VIDEO FIX COMPLETELY SUCCESSFUL!")
            print("   • User will no longer see 'CORS error' in browser console")
            print("   • Split request returns immediately instead of timing out")
            print("   • Browser can successfully receive the response")
            print("   • All timeout and CORS issues are RESOLVED")
        else:
            print("   ❌ SPLIT-VIDEO FIX INCOMPLETE OR FAILED")
            
            # Analyze specific failures
            timeout_issues = []
            cors_issues = []
            other_issues = []
            
            for result in self.test_results:
                if not result['success']:
                    if '504' in result['details'] or 'timeout' in result['details'].lower():
                        timeout_issues.append(result['test'])
                    elif 'cors' in result['details'].lower():
                        cors_issues.append(result['test'])
                    else:
                        other_issues.append(result['test'])
            
            if timeout_issues:
                print("   🚨 TIMEOUT ISSUES STILL PRESENT:")
                for issue in timeout_issues:
                    print(f"      • {issue}")
                print("   • The 29-second timeout problem is NOT resolved")
                print("   • Users will still experience 'Gateway Timeout' errors")
            
            if cors_issues:
                print("   🚨 CORS ISSUES STILL PRESENT:")
                for issue in cors_issues:
                    print(f"      • {issue}")
                print("   • Users will still see 'CORS error' in browser console")
                print("   • Browser requests will be blocked by CORS policy")
            
            if other_issues:
                print("   ⚠️  OTHER ISSUES:")
                for issue in other_issues:
                    print(f"      • {issue}")
        
        print()
        print("🔍 USER IMPACT:")
        if split_video_ok:
            print("   ✅ User can successfully initiate video splitting")
            print("   ✅ No more 'Failed to fetch' errors")
            print("   ✅ No more CORS policy violations")
            print("   ✅ No more 29-second timeouts")
        else:
            print("   ❌ User will still experience the reported issues")
            print("   ❌ Video splitting functionality remains broken")
            print("   ❌ Browser console will show errors")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = SplitVideoTester()
    passed, failed = tester.run_split_video_test()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)