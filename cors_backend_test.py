#!/usr/bin/env python3
"""
CORS-Focused AWS Lambda Backend Testing for Video Splitter Pro
Tests the updated Lambda function with enhanced CORS support for authentication system.
Focus on testing authentication endpoints with different origins and verifying CORS headers.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-uploads"
TIMEOUT = 30

# CORS Test Origins - matching the allowed origins in fix_cors_lambda.py
TEST_ORIGINS = [
    'https://develop.tads-video-splitter.com',
    'https://main.tads-video-splitter.com', 
    'https://working.tads-video-splitter.com',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000'
]

class VideoSplitterCORSTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.access_token = None
        self.user_id = None
        
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

    def test_cors_preflight_requests(self):
        """Test 1: CORS preflight (OPTIONS) requests with different origins"""
        print("🔍 Testing CORS Preflight Requests...")
        
        for origin in TEST_ORIGINS:
            try:
                headers = {
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type,Authorization'
                }
                
                response = self.session.options(f"{self.base_url}/api/auth/register", headers=headers)
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                # Check if origin is properly handled
                origin_match = cors_headers['Access-Control-Allow-Origin'] == origin or cors_headers['Access-Control-Allow-Origin'] == '*'
                has_required_methods = 'POST' in (cors_headers['Access-Control-Allow-Methods'] or '')
                has_required_headers = 'Content-Type' in (cors_headers['Access-Control-Allow-Headers'] or '')
                
                success = response.status_code == 200 and origin_match and has_required_methods and has_required_headers
                
                self.log_test(
                    f"CORS Preflight - {origin}",
                    success,
                    f"Status: {response.status_code}, Origin: {cors_headers['Access-Control-Allow-Origin']}, Methods: {cors_headers['Access-Control-Allow-Methods']}"
                )
                
            except Exception as e:
                self.log_test(f"CORS Preflight - {origin}", False, f"Error: {str(e)}")

    def test_health_check_cors(self):
        """Test 2: Health check endpoint with CORS information"""
        print("🔍 Testing Health Check Endpoint CORS...")
        
        for origin in TEST_ORIGINS[:3]:  # Test with first 3 origins
            try:
                headers = {'Origin': origin}
                response = self.session.get(f"{self.base_url}/api/", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    cors_info = data.get('cors', {})
                    
                    # Check if CORS configuration is exposed in health check
                    has_cors_config = 'allowed_origins' in cors_info
                    has_current_origin = 'current_origin' in cors_info
                    correct_origin = cors_info.get('current_origin') == origin
                    
                    # Check response headers
                    cors_header = response.headers.get('Access-Control-Allow-Origin')
                    header_correct = cors_header == origin or cors_header == '*'
                    
                    success = has_cors_config and has_current_origin and header_correct
                    
                    self.log_test(
                        f"Health Check CORS - {origin}",
                        success,
                        f"CORS config exposed: {has_cors_config}, Origin tracked: {correct_origin}, Header: {cors_header}"
                    )
                    
                    # Log allowed origins from the first successful response
                    if origin == TEST_ORIGINS[0] and has_cors_config:
                        allowed_origins = cors_info.get('allowed_origins', [])
                        self.log_test(
                            "CORS Configuration Check",
                            len(allowed_origins) >= 6,  # Should have at least 6 allowed origins
                            f"Allowed origins count: {len(allowed_origins)}, Origins: {allowed_origins}"
                        )
                else:
                    self.log_test(f"Health Check CORS - {origin}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Health Check CORS - {origin}", False, f"Error: {str(e)}")

    def test_authentication_endpoints_cors(self):
        """Test 3: Authentication endpoints with different origins"""
        print("🔍 Testing Authentication Endpoints with CORS...")
        
        # Generate unique test user data
        test_password = "CORSTest123!"
        
        for i, origin in enumerate(TEST_ORIGINS[:4]):  # Test with first 4 origins
            try:
                # Test Registration with CORS
                register_data = {
                    "email": f"corstest_{i}_{uuid.uuid4().hex[:6]}@example.com",
                    "password": test_password,
                    "firstName": "CORS",
                    "lastName": f"Test{i}"
                }
                
                headers = {
                    'Origin': origin,
                    'Content-Type': 'application/json'
                }
                
                response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data, headers=headers)
                
                # Check CORS headers in response
                cors_header = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                
                if response.status_code == 201:
                    data = response.json()
                    has_token = 'access_token' in data
                    has_user_id = 'user_id' in data
                    cors_correct = cors_header == origin or cors_header == '*'
                    
                    success = has_token and has_user_id and cors_correct
                    
                    self.log_test(
                        f"Registration CORS - {origin}",
                        success,
                        f"Token: {has_token}, User ID: {has_user_id}, CORS Header: {cors_header}"
                    )
                    
                    # Test Login with the same origin
                    if success:
                        login_data = {
                            "email": register_data["email"],
                            "password": test_password
                        }
                        
                        login_response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data, headers=headers)
                        login_cors_header = login_response.headers.get('Access-Control-Allow-Origin')
                        
                        if login_response.status_code == 200:
                            login_data_resp = login_response.json()
                            login_has_token = 'access_token' in login_data_resp
                            login_cors_correct = login_cors_header == origin or login_cors_header == '*'
                            
                            self.log_test(
                                f"Login CORS - {origin}",
                                login_has_token and login_cors_correct,
                                f"Token: {login_has_token}, CORS Header: {login_cors_header}"
                            )
                        else:
                            self.log_test(f"Login CORS - {origin}", False, f"HTTP {login_response.status_code}")
                            
                elif response.status_code == 503:
                    # MongoDB connection issue - but CORS should still work
                    cors_correct = cors_header == origin or cors_header == '*'
                    self.log_test(
                        f"Registration CORS - {origin}",
                        cors_correct,
                        f"MongoDB unavailable (503) but CORS working: {cors_correct}, Header: {cors_header}"
                    )
                else:
                    cors_correct = cors_header == origin or cors_header == '*'
                    self.log_test(
                        f"Registration CORS - {origin}",
                        cors_correct,
                        f"HTTP {response.status_code} but CORS: {cors_correct}, Header: {cors_header}"
                    )
                    
            except Exception as e:
                self.log_test(f"Authentication CORS - {origin}", False, f"Error: {str(e)}")

    def test_user_profile_cors(self):
        """Test 4: User profile endpoint with CORS (if we have a token)"""
        print("🔍 Testing User Profile Endpoint CORS...")
        
        # First, try to get a token by registering a user
        test_email = f"profiletest_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "ProfileTest123!"
        
        register_data = {
            "email": test_email,
            "password": test_password,
            "firstName": "Profile",
            "lastName": "Test"
        }
        
        try:
            # Register user to get token
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                access_token = data.get('access_token')
                
                if access_token:
                    # Test profile endpoint with different origins
                    for origin in TEST_ORIGINS[:3]:
                        try:
                            headers = {
                                'Origin': origin,
                                'Authorization': f'Bearer {access_token}',
                                'Content-Type': 'application/json'
                            }
                            
                            profile_response = self.session.get(f"{self.base_url}/api/user/profile", headers=headers)
                            cors_header = profile_response.headers.get('Access-Control-Allow-Origin')
                            
                            if profile_response.status_code == 200:
                                profile_data = profile_response.json()
                                has_user_data = 'user' in profile_data
                                cors_correct = cors_header == origin or cors_header == '*'
                                
                                self.log_test(
                                    f"Profile CORS - {origin}",
                                    has_user_data and cors_correct,
                                    f"User data: {has_user_data}, CORS Header: {cors_header}"
                                )
                            else:
                                cors_correct = cors_header == origin or cors_header == '*'
                                self.log_test(
                                    f"Profile CORS - {origin}",
                                    cors_correct,
                                    f"HTTP {profile_response.status_code} but CORS: {cors_correct}"
                                )
                                
                        except Exception as e:
                            self.log_test(f"Profile CORS - {origin}", False, f"Error: {str(e)}")
                else:
                    self.log_test("Profile CORS Test Setup", False, "No access token received from registration")
            else:
                self.log_test("Profile CORS Test Setup", False, f"Registration failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Profile CORS Test Setup", False, f"Setup error: {str(e)}")

    def test_end_to_end_user_registration(self):
        """Test 5: End-to-end user registration with realistic data"""
        print("🔍 Testing End-to-End User Registration...")
        
        # Use realistic test data
        realistic_users = [
            {
                "email": f"sarah.johnson_{uuid.uuid4().hex[:6]}@gmail.com",
                "password": "SecurePass2024!",
                "firstName": "Sarah",
                "lastName": "Johnson"
            },
            {
                "email": f"mike.chen_{uuid.uuid4().hex[:6]}@company.com",
                "password": "MyPassword123$",
                "firstName": "Mike",
                "lastName": "Chen"
            }
        ]
        
        for i, user_data in enumerate(realistic_users):
            origin = TEST_ORIGINS[i % len(TEST_ORIGINS)]
            
            try:
                headers = {
                    'Origin': origin,
                    'Content-Type': 'application/json'
                }
                
                # Step 1: Register user
                response = self.session.post(f"{self.base_url}/api/auth/register", json=user_data, headers=headers)
                
                if response.status_code == 201:
                    data = response.json()
                    access_token = data.get('access_token')
                    user_id = data.get('user_id')
                    user_info = data.get('user', {})
                    demo_mode = data.get('demo_mode', False)
                    
                    # Verify registration response
                    registration_success = all([
                        access_token,
                        user_id,
                        user_info.get('email') == user_data['email'],
                        user_info.get('firstName') == user_data['firstName']
                    ])
                    
                    self.log_test(
                        f"E2E Registration - {user_data['firstName']}",
                        registration_success,
                        f"Demo mode: {demo_mode}, User ID: {user_id[:8] if user_id else 'None'}..., Email: {user_info.get('email')}"
                    )
                    
                    if registration_success:
                        # Step 2: Test login with registered user
                        login_data = {
                            "email": user_data['email'],
                            "password": user_data['password']
                        }
                        
                        login_response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data, headers=headers)
                        
                        if login_response.status_code == 200:
                            login_data_resp = login_response.json()
                            login_token = login_data_resp.get('access_token')
                            login_user = login_data_resp.get('user', {})
                            
                            login_success = all([
                                login_token,
                                login_user.get('email') == user_data['email'],
                                login_user.get('firstName') == user_data['firstName']
                            ])
                            
                            self.log_test(
                                f"E2E Login - {user_data['firstName']}",
                                login_success,
                                f"Token received: {bool(login_token)}, User data correct: {login_user.get('email') == user_data['email']}"
                            )
                            
                            # Step 3: Test profile access
                            if login_token:
                                profile_headers = {
                                    'Origin': origin,
                                    'Authorization': f'Bearer {login_token}',
                                    'Content-Type': 'application/json'
                                }
                                
                                profile_response = self.session.get(f"{self.base_url}/api/user/profile", headers=profile_headers)
                                
                                if profile_response.status_code == 200:
                                    profile_data = profile_response.json()
                                    profile_user = profile_data.get('user', {})
                                    
                                    profile_success = all([
                                        profile_user.get('email') == user_data['email'],
                                        profile_user.get('firstName') == user_data['firstName'],
                                        profile_user.get('userId') == user_id
                                    ])
                                    
                                    self.log_test(
                                        f"E2E Profile Access - {user_data['firstName']}",
                                        profile_success,
                                        f"Profile data complete: {profile_success}, User ID match: {profile_user.get('userId') == user_id}"
                                    )
                                else:
                                    self.log_test(f"E2E Profile Access - {user_data['firstName']}", False, f"HTTP {profile_response.status_code}")
                        else:
                            self.log_test(f"E2E Login - {user_data['firstName']}", False, f"HTTP {login_response.status_code}")
                            
                elif response.status_code == 503:
                    self.log_test(
                        f"E2E Registration - {user_data['firstName']}",
                        False,
                        "MongoDB connection failure (503) - authentication system unavailable"
                    )
                else:
                    self.log_test(f"E2E Registration - {user_data['firstName']}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"E2E Test - {user_data['firstName']}", False, f"Error: {str(e)}")

    def test_cors_error_resolution(self):
        """Test 6: Verify CORS errors are resolved"""
        print("🔍 Testing CORS Error Resolution...")
        
        # Test with a browser-like request that would typically cause CORS issues
        problematic_origins = [
            'https://different-domain.com',  # Not in allowed list
            'http://localhost:8080',         # Different localhost port
            'https://unauthorized-site.com'  # Completely different domain
        ]
        
        for origin in problematic_origins:
            try:
                headers = {
                    'Origin': origin,
                    'Content-Type': 'application/json'
                }
                
                response = self.session.get(f"{self.base_url}/api/", headers=headers)
                cors_header = response.headers.get('Access-Control-Allow-Origin')
                
                # For unauthorized origins, should get '*' or no specific origin
                cors_handled = cors_header is not None
                
                self.log_test(
                    f"CORS Error Resolution - {origin}",
                    cors_handled,
                    f"CORS header present: {cors_handled}, Header value: {cors_header}"
                )
                
            except Exception as e:
                self.log_test(f"CORS Error Resolution - {origin}", False, f"Error: {str(e)}")
        
        # Test with allowed origins to ensure they still work
        for origin in TEST_ORIGINS[:2]:
            try:
                headers = {
                    'Origin': origin,
                    'Content-Type': 'application/json'
                }
                
                response = self.session.get(f"{self.base_url}/api/", headers=headers)
                cors_header = response.headers.get('Access-Control-Allow-Origin')
                
                # Should get the specific origin back or '*'
                cors_correct = cors_header == origin or cors_header == '*'
                
                self.log_test(
                    f"CORS Allowed Origin - {origin}",
                    cors_correct,
                    f"Correct CORS header: {cors_correct}, Header: {cors_header}"
                )
                
            except Exception as e:
                self.log_test(f"CORS Allowed Origin - {origin}", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all CORS-focused tests and provide summary"""
        print("=" * 80)
        print("🚀 AWS LAMBDA CORS AUTHENTICATION TESTING")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Testing Origins: {TEST_ORIGINS}")
        print()
        
        # Run all CORS-focused tests
        self.test_cors_preflight_requests()
        self.test_health_check_cors()
        self.test_authentication_endpoints_cors()
        self.test_user_profile_cors()
        self.test_end_to_end_user_registration()
        self.test_cors_error_resolution()
        
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
        
        # CORS-specific analysis
        cors_tests = [r for r in self.test_results if 'cors' in r['test'].lower()]
        cors_passed = sum(1 for r in cors_tests if r['success'])
        
        print(f"🌐 CORS Tests: {len(cors_tests)} total, {cors_passed} passed")
        
        # Authentication tests analysis
        auth_tests = [r for r in self.test_results if any(keyword in r['test'].lower() for keyword in ['registration', 'login', 'profile', 'e2e'])]
        auth_passed = sum(1 for r in auth_tests if r['success'])
        
        print(f"🔐 Authentication Tests: {len(auth_tests)} total, {auth_passed} passed")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # CORS-specific recommendations
        print("💡 CORS ANALYSIS:")
        
        if cors_passed >= len(cors_tests) * 0.8:
            print("   ✅ CORS configuration appears to be working correctly")
            print("   ✅ Multiple origins are properly supported")
        else:
            print("   ❌ CORS configuration has issues that need attention")
        
        if auth_passed >= len(auth_tests) * 0.7:
            print("   ✅ Authentication system is functional with CORS")
        else:
            print("   ❌ Authentication system has issues (may be MongoDB related)")
        
        # Check for MongoDB issues
        mongodb_issues = sum(1 for r in self.test_results if not r['success'] and '503' in r['details'])
        if mongodb_issues > 0:
            print(f"   ⚠️  {mongodb_issues} tests failed due to MongoDB connectivity (expected)")
            print("   ℹ️  CORS functionality can still be verified despite database issues")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoSplitterCORSTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)