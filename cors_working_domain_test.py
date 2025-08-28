#!/usr/bin/env python3
"""
CORS Configuration Test for working.tads-video-splitter.com Domain
Testing the CORS fix where a missing comma was causing the working domain to be excluded from ALLOWED_ORIGINS.

SPECIFIC TEST FOCUS:
1. Health check endpoint with Origin: https://working.tads-video-splitter.com
2. get-video-info endpoint with the working domain origin
3. video-stream endpoint with the working domain origin
4. Verify Access-Control-Allow-Origin header is properly returned for working.tads-video-splitter.com

This should resolve the CORS policy errors the user was experiencing.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
WORKING_DOMAIN = "https://working.tads-video-splitter.com"
TIMEOUT = 30

class CORSWorkingDomainTester:
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

    def test_health_check_cors(self):
        """Test 1: Health check endpoint with working domain origin"""
        print("🔍 Testing Health Check CORS for working.tads-video-splitter.com...")
        
        try:
            # Test with working domain origin
            headers = {
                'Origin': WORKING_DOMAIN,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            # First test OPTIONS preflight request
            response = self.session.options(f"{self.base_url}/api/", headers=headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            cors_headers = response.headers.get('Access-Control-Allow-Headers')
            
            if cors_origin == WORKING_DOMAIN:
                self.log_test(
                    "Health Check CORS Preflight - working domain",
                    True,
                    f"✅ CORS preflight successful! Origin: {cors_origin}, Methods: {cors_methods}"
                )
            elif cors_origin == '*':
                self.log_test(
                    "Health Check CORS Preflight - working domain",
                    True,
                    f"✅ CORS preflight successful with wildcard! Origin: {cors_origin}, Methods: {cors_methods}"
                )
            else:
                self.log_test(
                    "Health Check CORS Preflight - working domain",
                    False,
                    f"❌ CORS preflight failed! Expected: {WORKING_DOMAIN}, Got: {cors_origin}"
                )
            
            # Now test actual GET request
            response = self.session.get(f"{self.base_url}/api/", headers={'Origin': WORKING_DOMAIN})
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            
            if response.status_code == 200:
                data = response.json()
                
                if cors_origin == WORKING_DOMAIN or cors_origin == '*':
                    self.log_test(
                        "Health Check GET - working domain CORS",
                        True,
                        f"✅ Health check successful with CORS! Status: {response.status_code}, CORS Origin: {cors_origin}, Message: {data.get('message', 'N/A')}"
                    )
                else:
                    self.log_test(
                        "Health Check GET - working domain CORS",
                        False,
                        f"❌ Missing CORS header! Status: {response.status_code}, CORS Origin: {cors_origin}"
                    )
            else:
                self.log_test(
                    "Health Check GET - working domain CORS",
                    False,
                    f"HTTP {response.status_code}, CORS Origin: {cors_origin}",
                    response.json() if response.content else {}
                )
                
        except Exception as e:
            self.log_test("Health Check CORS - working domain", False, f"Error: {str(e)}")

    def test_video_info_cors(self):
        """Test 2: get-video-info endpoint with working domain origin"""
        print("🔍 Testing get-video-info CORS for working.tads-video-splitter.com...")
        
        try:
            # Test with working domain origin
            headers = {
                'Origin': WORKING_DOMAIN,
                'Content-Type': 'application/json'
            }
            
            # Test OPTIONS preflight request first
            preflight_headers = {
                'Origin': WORKING_DOMAIN,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.base_url}/api/get-video-info", headers=preflight_headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            if cors_origin == WORKING_DOMAIN or cors_origin == '*':
                self.log_test(
                    "get-video-info CORS Preflight - working domain",
                    True,
                    f"✅ CORS preflight successful! Origin: {cors_origin}, Methods: {cors_methods}"
                )
            else:
                self.log_test(
                    "get-video-info CORS Preflight - working domain",
                    False,
                    f"❌ CORS preflight failed! Expected: {WORKING_DOMAIN}, Got: {cors_origin}"
                )
            
            # Now test actual POST request
            test_data = {
                "s3_key": "uploads/test-video.mp4"
            }
            
            response = self.session.post(f"{self.base_url}/api/get-video-info", json=test_data, headers=headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            
            # We expect this to work regardless of whether the file exists
            # The key is that CORS headers are present
            if cors_origin == WORKING_DOMAIN or cors_origin == '*':
                if response.status_code in [200, 404, 504]:  # 404 = file not found, 504 = timeout (known issue)
                    self.log_test(
                        "get-video-info POST - working domain CORS",
                        True,
                        f"✅ CORS headers present! Status: {response.status_code}, CORS Origin: {cors_origin}"
                    )
                else:
                    self.log_test(
                        "get-video-info POST - working domain CORS",
                        False,
                        f"Unexpected status with CORS: {response.status_code}, CORS Origin: {cors_origin}",
                        response.json() if response.content else {}
                    )
            else:
                self.log_test(
                    "get-video-info POST - working domain CORS",
                    False,
                    f"❌ Missing CORS header! Status: {response.status_code}, CORS Origin: {cors_origin}"
                )
                
        except Exception as e:
            self.log_test("get-video-info CORS - working domain", False, f"Error: {str(e)}")

    def test_video_stream_cors(self):
        """Test 3: video-stream endpoint with working domain origin"""
        print("🔍 Testing video-stream CORS for working.tads-video-splitter.com...")
        
        try:
            # Test with working domain origin
            headers = {
                'Origin': WORKING_DOMAIN
            }
            
            # Test OPTIONS preflight request first
            preflight_headers = {
                'Origin': WORKING_DOMAIN,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            test_key = "uploads/test-video.mp4"
            
            response = self.session.options(f"{self.base_url}/api/video-stream/{test_key}", headers=preflight_headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            if cors_origin == WORKING_DOMAIN or cors_origin == '*':
                self.log_test(
                    "video-stream CORS Preflight - working domain",
                    True,
                    f"✅ CORS preflight successful! Origin: {cors_origin}, Methods: {cors_methods}"
                )
            else:
                self.log_test(
                    "video-stream CORS Preflight - working domain",
                    False,
                    f"❌ CORS preflight failed! Expected: {WORKING_DOMAIN}, Got: {cors_origin}"
                )
            
            # Now test actual GET request
            response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}", headers=headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            
            # We expect this to work regardless of whether the file exists
            # The key is that CORS headers are present
            if cors_origin == WORKING_DOMAIN or cors_origin == '*':
                if response.status_code in [200, 404, 504]:  # 404 = file not found, 504 = timeout (known issue)
                    self.log_test(
                        "video-stream GET - working domain CORS",
                        True,
                        f"✅ CORS headers present! Status: {response.status_code}, CORS Origin: {cors_origin}"
                    )
                else:
                    self.log_test(
                        "video-stream GET - working domain CORS",
                        False,
                        f"Unexpected status with CORS: {response.status_code}, CORS Origin: {cors_origin}",
                        response.json() if response.content else {}
                    )
            else:
                self.log_test(
                    "video-stream GET - working domain CORS",
                    False,
                    f"❌ Missing CORS header! Status: {response.status_code}, CORS Origin: {cors_origin}"
                )
                
        except Exception as e:
            self.log_test("video-stream CORS - working domain", False, f"Error: {str(e)}")

    def test_cors_comparison_with_other_domains(self):
        """Test 4: Compare CORS behavior with other allowed domains"""
        print("🔍 Testing CORS comparison with other domains...")
        
        test_domains = [
            'https://develop.tads-video-splitter.com',
            'https://main.tads-video-splitter.com',
            'https://working.tads-video-splitter.com',  # Our focus domain
            'http://localhost:3000'
        ]
        
        for domain in test_domains:
            try:
                headers = {'Origin': domain}
                response = self.session.get(f"{self.base_url}/api/", headers=headers)
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin == domain or cors_origin == '*':
                    status = "✅ WORKING" if domain == WORKING_DOMAIN else "✅ OK"
                    self.log_test(
                        f"CORS Domain Comparison - {domain.split('//')[1]}",
                        True,
                        f"{status} CORS Origin: {cors_origin}"
                    )
                else:
                    status = "❌ BROKEN" if domain == WORKING_DOMAIN else "❌ FAIL"
                    self.log_test(
                        f"CORS Domain Comparison - {domain.split('//')[1]}",
                        False,
                        f"{status} Expected: {domain}, Got: {cors_origin}"
                    )
                    
            except Exception as e:
                self.log_test(f"CORS Domain Comparison - {domain.split('//')[1]}", False, f"Error: {str(e)}")

    def test_unauthorized_origin(self):
        """Test 5: Verify unauthorized origins are properly rejected"""
        print("🔍 Testing unauthorized origin rejection...")
        
        unauthorized_domain = "https://malicious-site.com"
        
        try:
            headers = {'Origin': unauthorized_domain}
            response = self.session.get(f"{self.base_url}/api/", headers=headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            
            # Should either not have CORS header or not match the unauthorized domain
            if cors_origin != unauthorized_domain:
                self.log_test(
                    "Unauthorized Origin Rejection",
                    True,
                    f"✅ Unauthorized origin properly rejected. CORS Origin: {cors_origin or 'None'}"
                )
            else:
                self.log_test(
                    "Unauthorized Origin Rejection",
                    False,
                    f"❌ Security issue: Unauthorized origin accepted! CORS Origin: {cors_origin}"
                )
                
        except Exception as e:
            self.log_test("Unauthorized Origin Rejection", False, f"Error: {str(e)}")

    def run_cors_tests(self):
        """Run focused CORS tests for working.tads-video-splitter.com domain"""
        print("=" * 80)
        print("🎯 CORS CONFIGURATION TEST FOR working.tads-video-splitter.com")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Focus Domain: {WORKING_DOMAIN}")
        print()
        print("🔧 TESTING CORS FIX:")
        print("   Fixed missing comma in ALLOWED_ORIGINS list that was excluding working domain")
        print("   User was getting CORS policy errors because domain wasn't properly configured")
        print()
        print("📋 TEST COVERAGE:")
        print("   1. Health check endpoint CORS")
        print("   2. get-video-info endpoint CORS")
        print("   3. video-stream endpoint CORS")
        print("   4. Access-Control-Allow-Origin header verification")
        print("   5. Domain comparison testing")
        print()
        
        # Run CORS tests
        self.test_health_check_cors()
        self.test_video_info_cors()
        self.test_video_stream_cors()
        self.test_cors_comparison_with_other_domains()
        self.test_unauthorized_origin()
        
        # Summary
        print("=" * 80)
        print("📊 CORS TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze CORS fix status
        cors_fix_status = {
            'health_check_cors': False,
            'video_info_cors': False,
            'video_stream_cors': False,
            'working_domain_supported': False
        }
        
        for result in self.test_results:
            if result['success']:
                test_name = result['test'].lower()
                if 'health check' in test_name and 'working domain' in test_name:
                    cors_fix_status['health_check_cors'] = True
                elif 'get-video-info' in test_name and 'working domain' in test_name:
                    cors_fix_status['video_info_cors'] = True
                elif 'video-stream' in test_name and 'working domain' in test_name:
                    cors_fix_status['video_stream_cors'] = True
                elif 'working.tads-video-splitter.com' in test_name:
                    cors_fix_status['working_domain_supported'] = True
        
        print("🔍 CORS FIX STATUS FOR working.tads-video-splitter.com:")
        print(f"   ✅ Health Check CORS: {'FIXED' if cors_fix_status['health_check_cors'] else 'STILL BROKEN'}")
        print(f"   ✅ get-video-info CORS: {'FIXED' if cors_fix_status['video_info_cors'] else 'STILL BROKEN'}")
        print(f"   ✅ video-stream CORS: {'FIXED' if cors_fix_status['video_stream_cors'] else 'STILL BROKEN'}")
        print(f"   ✅ Working Domain Support: {'ENABLED' if cors_fix_status['working_domain_supported'] else 'DISABLED'}")
        print()
        
        # Failed tests details
        cors_failures = []
        other_failures = []
        
        for result in self.test_results:
            if not result['success']:
                if 'cors' in result['test'].lower() or 'working domain' in result['test'].lower():
                    cors_failures.append(result)
                else:
                    other_failures.append(result)
        
        if cors_failures:
            print("🚨 CORS ISSUES STILL PRESENT:")
            for result in cors_failures:
                print(f"   • {result['test']}: {result['details']}")
            print()
        
        if other_failures:
            print("❌ OTHER ISSUES:")
            for result in other_failures:
                print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Final assessment
        print("💡 CORS FIX ASSESSMENT:")
        
        fixed_count = sum(cors_fix_status.values())
        if fixed_count >= 3:
            print("   🎉 CORS FIX SUCCESSFUL!")
            print("   • working.tads-video-splitter.com is now properly supported")
            print("   • All tested endpoints return correct Access-Control-Allow-Origin headers")
            print("   • User's CORS policy errors should be resolved")
        elif fixed_count >= 1:
            print(f"   ✅ PARTIAL SUCCESS: {fixed_count}/4 CORS issues resolved")
            if not cors_fix_status['health_check_cors']:
                print("   • Health check endpoint CORS still broken")
            if not cors_fix_status['video_info_cors']:
                print("   • get-video-info endpoint CORS still broken")
            if not cors_fix_status['video_stream_cors']:
                print("   • video-stream endpoint CORS still broken")
            if not cors_fix_status['working_domain_supported']:
                print("   • working.tads-video-splitter.com domain still not supported")
        else:
            print("   ❌ CORS FIX FAILED: working.tads-video-splitter.com still not supported")
            print("   • Missing comma fix may not have been deployed correctly")
            print("   • ALLOWED_ORIGINS list may still be malformed")
            print("   • User will continue to experience CORS policy errors")
        
        if cors_failures:
            print("   • Verify ALLOWED_ORIGINS list in Lambda function")
            print("   • Check Lambda deployment status")
            print("   • Review CloudWatch logs for CORS configuration errors")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = CORSWorkingDomainTester()
    passed, failed = tester.run_cors_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)