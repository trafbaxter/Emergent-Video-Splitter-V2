#!/usr/bin/env python3
"""
WILDCARD CORS FIX TESTING for Video Splitter Pro
Testing the temporary wildcard CORS fix where Access-Control-Allow-Origin is set to '*'

URGENT TEST FOCUS:
1. Health check endpoint - should return Access-Control-Allow-Origin: *
2. get-video-info endpoint - should work from any origin now
3. video-stream endpoint - should work from any origin now
4. Confirm no CORS errors from working.tads-video-splitter.com domain

This should resolve all CORS issues immediately with the wildcard approach.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-storage-1751560247"
TIMEOUT = 30

# Test Origins - including working.tads-video-splitter.com and random origins
TEST_ORIGINS = [
    'https://working.tads-video-splitter.com',  # Primary focus
    'https://develop.tads-video-splitter.com',
    'https://main.tads-video-splitter.com', 
    'http://localhost:3000',
    'https://random-domain.com',  # Should work with wildcard
    'https://example.org',  # Should work with wildcard
    'https://test.invalid'  # Should work with wildcard
]

class WildcardCORSTester:
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

    def test_wildcard_cors_health_check(self):
        """Test 1: Health check endpoint should return Access-Control-Allow-Origin: *"""
        print("🔍 Testing Wildcard CORS on Health Check Endpoint...")
        
        for origin in TEST_ORIGINS:
            try:
                headers = {'Origin': origin}
                response = self.session.get(f"{self.base_url}/api/", headers=headers)
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin == '*':
                    self.log_test(
                        f"Health Check Wildcard CORS - {origin}",
                        True,
                        f"✅ WILDCARD WORKING! Access-Control-Allow-Origin: {cors_origin}"
                    )
                else:
                    self.log_test(
                        f"Health Check Wildcard CORS - {origin}",
                        False,
                        f"❌ Expected '*' but got: {cors_origin}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Health Check Wildcard CORS - {origin}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_wildcard_cors_preflight(self):
        """Test 2: OPTIONS preflight requests should return Access-Control-Allow-Origin: *"""
        print("🔍 Testing Wildcard CORS Preflight (OPTIONS) Requests...")
        
        test_endpoints = [
            '/api/',
            '/api/get-video-info',
            '/api/video-stream/test.mp4',
            '/api/auth/register'
        ]
        
        for endpoint in test_endpoints:
            for origin in TEST_ORIGINS[:3]:  # Test with first 3 origins
                try:
                    headers = {
                        'Origin': origin,
                        'Access-Control-Request-Method': 'POST',
                        'Access-Control-Request-Headers': 'Content-Type'
                    }
                    
                    response = self.session.options(f"{self.base_url}{endpoint}", headers=headers)
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = response.headers.get('Access-Control-Allow-Methods')
                    
                    if cors_origin == '*' and cors_methods:
                        self.log_test(
                            f"Preflight Wildcard CORS - {endpoint} from {origin.split('//')[1]}",
                            True,
                            f"✅ WILDCARD WORKING! Origin: {cors_origin}, Methods: {cors_methods}"
                        )
                    else:
                        self.log_test(
                            f"Preflight Wildcard CORS - {endpoint} from {origin.split('//')[1]}",
                            False,
                            f"❌ Origin: {cors_origin}, Methods: {cors_methods}"
                        )
                        
                except Exception as e:
                    self.log_test(
                        f"Preflight Wildcard CORS - {endpoint} from {origin.split('//')[1]}",
                        False,
                        f"Error: {str(e)}"
                    )

    def test_wildcard_cors_get_video_info(self):
        """Test 3: get-video-info endpoint should work from any origin with wildcard CORS"""
        print("🔍 Testing Wildcard CORS on get-video-info Endpoint...")
        
        test_data = {
            "s3_key": "uploads/test-video.mp4"
        }
        
        for origin in TEST_ORIGINS:
            try:
                headers = {
                    'Origin': origin,
                    'Content-Type': 'application/json'
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/get-video-info", 
                    json=test_data,
                    headers=headers
                )
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                # Check if CORS header is wildcard (regardless of endpoint functionality)
                if cors_origin == '*':
                    # Additional check: endpoint should respond (not CORS blocked)
                    if response.status_code in [200, 202, 404, 500]:  # Any valid HTTP response
                        self.log_test(
                            f"get-video-info Wildcard CORS - {origin.split('//')[1]}",
                            True,
                            f"✅ WILDCARD WORKING! CORS: {cors_origin}, HTTP: {response.status_code}"
                        )
                    else:
                        self.log_test(
                            f"get-video-info Wildcard CORS - {origin.split('//')[1]}",
                            False,
                            f"CORS OK but unexpected HTTP: {response.status_code}"
                        )
                else:
                    self.log_test(
                        f"get-video-info Wildcard CORS - {origin.split('//')[1]}",
                        False,
                        f"❌ Expected '*' but got: {cors_origin}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"get-video-info Wildcard CORS - {origin.split('//')[1]}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_wildcard_cors_video_stream(self):
        """Test 4: video-stream endpoint should work from any origin with wildcard CORS"""
        print("🔍 Testing Wildcard CORS on video-stream Endpoint...")
        
        test_keys = [
            "uploads/test-video.mp4",
            "test/sample.mkv"
        ]
        
        for test_key in test_keys:
            for origin in TEST_ORIGINS[:4]:  # Test with first 4 origins
                try:
                    headers = {'Origin': origin}
                    
                    response = self.session.get(
                        f"{self.base_url}/api/video-stream/{test_key}",
                        headers=headers
                    )
                    
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    # Check if CORS header is wildcard (regardless of endpoint functionality)
                    if cors_origin == '*':
                        # Additional check: endpoint should respond (not CORS blocked)
                        if response.status_code in [200, 404, 500]:  # Any valid HTTP response
                            self.log_test(
                                f"video-stream Wildcard CORS - {test_key} from {origin.split('//')[1]}",
                                True,
                                f"✅ WILDCARD WORKING! CORS: {cors_origin}, HTTP: {response.status_code}"
                            )
                        else:
                            self.log_test(
                                f"video-stream Wildcard CORS - {test_key} from {origin.split('//')[1]}",
                                False,
                                f"CORS OK but unexpected HTTP: {response.status_code}"
                            )
                    else:
                        self.log_test(
                            f"video-stream Wildcard CORS - {test_key} from {origin.split('//')[1]}",
                            False,
                            f"❌ Expected '*' but got: {cors_origin}"
                        )
                        
                except Exception as e:
                    self.log_test(
                        f"video-stream Wildcard CORS - {test_key} from {origin.split('//')[1]}",
                        False,
                        f"Error: {str(e)}"
                    )

    def test_working_domain_specific(self):
        """Test 5: Focused test on working.tads-video-splitter.com domain"""
        print("🔍 Testing working.tads-video-splitter.com Domain Specifically...")
        
        working_origin = 'https://working.tads-video-splitter.com'
        
        test_endpoints = [
            {'method': 'GET', 'path': '/api/', 'name': 'Health Check'},
            {'method': 'POST', 'path': '/api/get-video-info', 'name': 'Video Info', 'data': {'s3_key': 'test.mp4'}},
            {'method': 'GET', 'path': '/api/video-stream/test.mp4', 'name': 'Video Stream'},
            {'method': 'POST', 'path': '/api/auth/register', 'name': 'Auth Register', 'data': {'email': 'test@example.com', 'password': 'test123'}}
        ]
        
        for endpoint in test_endpoints:
            try:
                headers = {
                    'Origin': working_origin,
                    'Content-Type': 'application/json'
                }
                
                if endpoint['method'] == 'GET':
                    response = self.session.get(
                        f"{self.base_url}{endpoint['path']}",
                        headers=headers
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint['path']}",
                        json=endpoint.get('data', {}),
                        headers=headers
                    )
                
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin == '*':
                    self.log_test(
                        f"working.tads-video-splitter.com - {endpoint['name']}",
                        True,
                        f"✅ WILDCARD CORS WORKING! Origin: {cors_origin}, HTTP: {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"working.tads-video-splitter.com - {endpoint['name']}",
                        False,
                        f"❌ Expected '*' but got: {cors_origin}, HTTP: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"working.tads-video-splitter.com - {endpoint['name']}",
                    False,
                    f"Error: {str(e)}"
                )

    def test_cors_credentials_setting(self):
        """Test 6: Verify Access-Control-Allow-Credentials is set to 'false' with wildcard"""
        print("🔍 Testing CORS Credentials Setting with Wildcard...")
        
        try:
            headers = {'Origin': 'https://working.tads-video-splitter.com'}
            response = self.session.get(f"{self.base_url}/api/", headers=headers)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
            
            if cors_origin == '*' and cors_credentials == 'false':
                self.log_test(
                    "CORS Credentials Configuration",
                    True,
                    f"✅ CORRECT! Origin: {cors_origin}, Credentials: {cors_credentials}"
                )
            else:
                self.log_test(
                    "CORS Credentials Configuration",
                    False,
                    f"❌ Origin: {cors_origin}, Credentials: {cors_credentials} (should be 'false' with wildcard)"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Credentials Configuration",
                False,
                f"Error: {str(e)}"
            )

    def run_wildcard_cors_tests(self):
        """Run focused tests on the wildcard CORS fix"""
        print("=" * 80)
        print("🚨 URGENT: WILDCARD CORS FIX TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 WILDCARD CORS FIX TESTING:")
        print("   Access-Control-Allow-Origin temporarily set to '*'")
        print("   This should resolve ALL CORS issues immediately")
        print()
        print("📋 TESTING FOCUS:")
        print("   1. Health check endpoint - should return Access-Control-Allow-Origin: *")
        print("   2. get-video-info endpoint - should work from any origin")
        print("   3. video-stream endpoint - should work from any origin")
        print("   4. working.tads-video-splitter.com domain - should work perfectly")
        print()
        
        # Run wildcard CORS tests
        self.test_wildcard_cors_health_check()
        self.test_wildcard_cors_preflight()
        self.test_wildcard_cors_get_video_info()
        self.test_wildcard_cors_video_stream()
        self.test_working_domain_specific()
        self.test_cors_credentials_setting()
        
        # Summary
        print("=" * 80)
        print("📊 WILDCARD CORS FIX TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze wildcard CORS status
        wildcard_working = True
        working_domain_ok = True
        
        for result in self.test_results:
            if not result['success']:
                if 'wildcard' in result['test'].lower() or 'cors' in result['test'].lower():
                    wildcard_working = False
                if 'working.tads-video-splitter.com' in result['test']:
                    working_domain_ok = False
        
        print("🔍 WILDCARD CORS FIX STATUS:")
        print(f"   ✅ Wildcard CORS Working: {'YES' if wildcard_working else 'NO'}")
        print(f"   ✅ working.tads-video-splitter.com OK: {'YES' if working_domain_ok else 'NO'}")
        
        if wildcard_working and working_domain_ok:
            print("\n🎉 SUCCESS: Wildcard CORS fix is working perfectly!")
            print("   All origins should now work without CORS errors")
        else:
            print("\n🚨 ISSUE: Wildcard CORS fix needs attention")
            print("   Some origins may still experience CORS errors")
        
        return wildcard_working and working_domain_ok

if __name__ == "__main__":
    tester = WildcardCORSTester()
    success = tester.run_wildcard_cors_tests()
    
    if success:
        print("\n✅ WILDCARD CORS FIX VERIFIED - Ready for production!")
        sys.exit(0)
    else:
        print("\n❌ WILDCARD CORS FIX NEEDS ATTENTION")
        sys.exit(1)