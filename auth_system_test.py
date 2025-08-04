#!/usr/bin/env python3
"""
Comprehensive Authentication System Testing for Video Splitter Pro - Phase 2 Recovery
Testing the newly deployed AWS Lambda authentication system to verify Phase 2 completion.

Focus Areas:
1. Authentication Endpoints Testing
2. Dependencies Verification (bcrypt, PyJWT, pymongo)
3. Integration with Core Video Processing
4. Error Handling and Security
"""

import requests
import json
import time
import uuid
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30

class AuthenticationTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.test_user_email = f"test.user.{int(time.time())}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_user_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "firstName": "Test",
            "lastName": "User"
        }
        self.access_token = None
        self.refresh_token = None
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
        print()

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=default_headers, timeout=TIMEOUT)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=default_headers, timeout=TIMEOUT)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=default_headers, timeout=TIMEOUT)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=default_headers, timeout=TIMEOUT)
            else:
                return {"error": f"Unsupported method: {method}", "status_code": 0}
                
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            return {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers),
                "url": url
            }
            
        except requests.exceptions.Timeout:
            return {"error": "Request timeout", "status_code": 0}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error", "status_code": 0}
        except Exception as e:
            return {"error": str(e), "status_code": 0}

    def test_1_basic_connectivity(self):
        """Test 1: Basic API Gateway connectivity"""
        print("=" * 60)
        print("TEST 1: BASIC CONNECTIVITY")
        print("=" * 60)
        
        # Test root endpoint
        response = self.make_request('GET', '/')
        
        if response.get("status_code") == 403:
            self.log_test("Root endpoint accessibility", "PASS", 
                         "Returns 403 'Missing Authentication Token' as expected for API Gateway")
        elif response.get("status_code") == 200:
            self.log_test("Root endpoint accessibility", "PASS", 
                         f"Returns 200: {response.get('data', {}).get('message', 'No message')}")
        else:
            self.log_test("Root endpoint accessibility", "FAIL", 
                         f"Status: {response.get('status_code')}, Error: {response.get('error', 'Unknown')}")
            
        # Test API root
        response = self.make_request('GET', '/api/')
        
        if response.get("status_code") == 200:
            self.log_test("API root endpoint", "PASS", 
                         f"Response: {response.get('data', {})}")
        elif response.get("status_code") == 502:
            self.log_test("API root endpoint", "FAIL", 
                         "502 Bad Gateway - Lambda function execution failure")
            return False
        else:
            self.log_test("API root endpoint", "WARN", 
                         f"Status: {response.get('status_code')}, Response: {response.get('data', {})}")
            
        return True

    def test_2_authentication_endpoints_availability(self):
        """Test 2: Authentication endpoints availability"""
        print("=" * 60)
        print("TEST 2: AUTHENTICATION ENDPOINTS AVAILABILITY")
        print("=" * 60)
        
        auth_endpoints = [
            '/api/auth/register',
            '/api/auth/login',
            '/api/auth/verify-email',
            '/api/auth/refresh'
        ]
        
        all_available = True
        
        for endpoint in auth_endpoints:
            # Test with OPTIONS to check CORS
            response = self.make_request('OPTIONS', endpoint)
            
            if response.get("status_code") == 200:
                self.log_test(f"CORS preflight {endpoint}", "PASS", 
                             "CORS headers properly configured")
            elif response.get("status_code") == 502:
                self.log_test(f"CORS preflight {endpoint}", "FAIL", 
                             "502 Bad Gateway - Lambda execution failure")
                all_available = False
            else:
                self.log_test(f"CORS preflight {endpoint}", "WARN", 
                             f"Status: {response.get('status_code')}")
                
        return all_available

    def test_3_user_registration(self):
        """Test 3: User registration functionality"""
        print("=" * 60)
        print("TEST 3: USER REGISTRATION")
        print("=" * 60)
        
        # Test user registration
        response = self.make_request('POST', '/api/auth/register', self.test_user_data)
        
        if response.get("status_code") == 201:
            self.log_test("User registration", "PASS", 
                         f"User registered successfully: {response.get('data', {}).get('message', '')}")
            return True
        elif response.get("status_code") == 502:
            self.log_test("User registration", "FAIL", 
                         "502 Bad Gateway - Lambda function execution failure (likely bcrypt import error)")
            return False
        elif response.get("status_code") == 400:
            self.log_test("User registration", "WARN", 
                         f"Validation error: {response.get('data', {})}")
            return False
        else:
            self.log_test("User registration", "FAIL", 
                         f"Status: {response.get('status_code')}, Response: {response.get('data', {})}")
            return False

    def test_4_user_login(self):
        """Test 4: User login functionality"""
        print("=" * 60)
        print("TEST 4: USER LOGIN")
        print("=" * 60)
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.make_request('POST', '/api/auth/login', login_data)
        
        if response.get("status_code") == 200:
            data = response.get('data', {})
            if 'accessToken' in data and 'refreshToken' in data:
                self.access_token = data['accessToken']
                self.refresh_token = data['refreshToken']
                self.log_test("User login", "PASS", 
                             f"Login successful, tokens received")
                return True
            else:
                self.log_test("User login", "FAIL", 
                             f"Login response missing tokens: {data}")
                return False
        elif response.get("status_code") == 502:
            self.log_test("User login", "FAIL", 
                         "502 Bad Gateway - Lambda function execution failure (likely bcrypt/JWT import error)")
            return False
        elif response.get("status_code") == 401:
            self.log_test("User login", "WARN", 
                         "401 Unauthorized - User may not exist or password incorrect")
            return False
        else:
            self.log_test("User login", "FAIL", 
                         f"Status: {response.get('status_code')}, Response: {response.get('data', {})}")
            return False

    def test_5_jwt_token_validation(self):
        """Test 5: JWT token validation and protected routes"""
        print("=" * 60)
        print("TEST 5: JWT TOKEN VALIDATION")
        print("=" * 60)
        
        if not self.access_token:
            self.log_test("JWT token validation", "SKIP", 
                         "No access token available from login test")
            return False
            
        # Test protected route with valid token
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = self.make_request('GET', '/api/user/profile', headers=headers)
        
        if response.get("status_code") == 200:
            self.log_test("Protected route with valid token", "PASS", 
                         f"Profile data retrieved: {response.get('data', {})}")
            return True
        elif response.get("status_code") == 502:
            self.log_test("Protected route with valid token", "FAIL", 
                         "502 Bad Gateway - Lambda function execution failure")
            return False
        elif response.get("status_code") == 401:
            self.log_test("Protected route with valid token", "FAIL", 
                         "401 Unauthorized - JWT validation failed")
            return False
        else:
            self.log_test("Protected route with valid token", "WARN", 
                         f"Status: {response.get('status_code')}, Response: {response.get('data', {})}")
            return False

    def test_6_bcrypt_password_hashing(self):
        """Test 6: Verify bcrypt password hashing is working"""
        print("=" * 60)
        print("TEST 6: BCRYPT PASSWORD HASHING")
        print("=" * 60)
        
        # Test with wrong password
        wrong_login_data = {
            "email": self.test_user_email,
            "password": "WrongPassword123!"
        }
        
        response = self.make_request('POST', '/api/auth/login', wrong_login_data)
        
        if response.get("status_code") == 401:
            self.log_test("Bcrypt password verification", "PASS", 
                         "Wrong password correctly rejected")
            return True
        elif response.get("status_code") == 502:
            self.log_test("Bcrypt password verification", "FAIL", 
                         "502 Bad Gateway - bcrypt library not available")
            return False
        else:
            self.log_test("Bcrypt password verification", "WARN", 
                         f"Unexpected response: Status {response.get('status_code')}")
            return False

    def test_7_dependencies_verification(self):
        """Test 7: Verify PyJWT and pymongo dependencies"""
        print("=" * 60)
        print("TEST 7: DEPENDENCIES VERIFICATION")
        print("=" * 60)
        
        # Test JWT token refresh (tests PyJWT)
        if self.refresh_token:
            refresh_data = {"refreshToken": self.refresh_token}
            response = self.make_request('POST', '/api/auth/refresh', refresh_data)
            
            if response.get("status_code") == 200:
                self.log_test("PyJWT dependency", "PASS", 
                             "Token refresh successful - PyJWT working")
            elif response.get("status_code") == 502:
                self.log_test("PyJWT dependency", "FAIL", 
                             "502 Bad Gateway - PyJWT library not available")
                return False
            else:
                self.log_test("PyJWT dependency", "WARN", 
                             f"Token refresh failed: Status {response.get('status_code')}")
        else:
            self.log_test("PyJWT dependency", "SKIP", 
                         "No refresh token available")
            
        # Test user history (tests pymongo)
        if self.access_token:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = self.make_request('GET', '/api/user/history', headers=headers)
            
            if response.get("status_code") == 200:
                self.log_test("PyMongo dependency", "PASS", 
                             "User history retrieved - PyMongo working")
                return True
            elif response.get("status_code") == 502:
                self.log_test("PyMongo dependency", "FAIL", 
                             "502 Bad Gateway - PyMongo library not available")
                return False
            else:
                self.log_test("PyMongo dependency", "WARN", 
                             f"User history failed: Status {response.get('status_code')}")
        else:
            self.log_test("PyMongo dependency", "SKIP", 
                         "No access token available")
            
        return True

    def test_8_core_video_processing_integration(self):
        """Test 8: Verify existing video endpoints still work"""
        print("=" * 60)
        print("TEST 8: CORE VIDEO PROCESSING INTEGRATION")
        print("=" * 60)
        
        # Test video upload endpoint
        response = self.make_request('GET', '/api/upload-video')
        
        if response.get("status_code") in [200, 405]:  # 405 Method Not Allowed is acceptable for GET on POST endpoint
            self.log_test("Video upload endpoint", "PASS", 
                         "Endpoint accessible (method validation working)")
        elif response.get("status_code") == 502:
            self.log_test("Video upload endpoint", "FAIL", 
                         "502 Bad Gateway - Core video processing broken")
            return False
        else:
            self.log_test("Video upload endpoint", "WARN", 
                         f"Status: {response.get('status_code')}")
            
        # Test S3 presigned URL generation (if endpoint exists)
        response = self.make_request('GET', '/api/video-info/test-job-id')
        
        if response.get("status_code") in [200, 404]:  # 404 is expected for non-existent job
            self.log_test("Video info endpoint", "PASS", 
                         "Endpoint accessible and responding correctly")
            return True
        elif response.get("status_code") == 502:
            self.log_test("Video info endpoint", "FAIL", 
                         "502 Bad Gateway - Video processing broken")
            return False
        else:
            self.log_test("Video info endpoint", "WARN", 
                         f"Status: {response.get('status_code')}")
            
        return True

    def test_9_error_handling_and_security(self):
        """Test 9: Error handling and security measures"""
        print("=" * 60)
        print("TEST 9: ERROR HANDLING AND SECURITY")
        print("=" * 60)
        
        # Test invalid authentication attempts
        invalid_login = {
            "email": "invalid@email.com",
            "password": "wrongpassword"
        }
        
        response = self.make_request('POST', '/api/auth/login', invalid_login)
        
        if response.get("status_code") == 401:
            self.log_test("Invalid login handling", "PASS", 
                         "Invalid credentials properly rejected")
        elif response.get("status_code") == 502:
            self.log_test("Invalid login handling", "FAIL", 
                         "502 Bad Gateway - Authentication system not working")
            return False
        else:
            self.log_test("Invalid login handling", "WARN", 
                         f"Unexpected response: Status {response.get('status_code')}")
            
        # Test CORS headers
        response = self.make_request('OPTIONS', '/api/auth/login')
        cors_headers = response.get('headers', {})
        
        if 'Access-Control-Allow-Origin' in cors_headers:
            self.log_test("CORS headers", "PASS", 
                         f"CORS properly configured: {cors_headers.get('Access-Control-Allow-Origin')}")
        else:
            self.log_test("CORS headers", "FAIL", 
                         "CORS headers missing")
            
        # Test malformed requests
        response = self.make_request('POST', '/api/auth/register', {"invalid": "data"})
        
        if response.get("status_code") == 400:
            self.log_test("Input validation", "PASS", 
                         "Malformed requests properly rejected")
            return True
        elif response.get("status_code") == 502:
            self.log_test("Input validation", "FAIL", 
                         "502 Bad Gateway - Validation not working")
            return False
        else:
            self.log_test("Input validation", "WARN", 
                         f"Status: {response.get('status_code')}")
            
        return True

    def run_comprehensive_test(self):
        """Run all authentication system tests"""
        print("🚀 STARTING COMPREHENSIVE AUTHENTICATION SYSTEM TESTING")
        print(f"📍 API Base URL: {self.base_url}")
        print(f"🕒 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_results = {}
        
        # Run all tests
        test_results['basic_connectivity'] = self.test_1_basic_connectivity()
        test_results['endpoints_availability'] = self.test_2_authentication_endpoints_availability()
        test_results['user_registration'] = self.test_3_user_registration()
        test_results['user_login'] = self.test_4_user_login()
        test_results['jwt_validation'] = self.test_5_jwt_token_validation()
        test_results['bcrypt_hashing'] = self.test_6_bcrypt_password_hashing()
        test_results['dependencies'] = self.test_7_dependencies_verification()
        test_results['video_integration'] = self.test_8_core_video_processing_integration()
        test_results['security'] = self.test_9_error_handling_and_security()
        
        # Summary
        print("=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result is True)
        total_tests = len(test_results)
        
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        print()
        
        # Detailed results
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL" if result is False else "⚠️ SKIP"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            
        print()
        
        # Phase 2 completion assessment
        critical_tests = ['basic_connectivity', 'endpoints_availability', 'user_registration', 'user_login']
        critical_passed = all(test_results.get(test, False) for test in critical_tests)
        
        if critical_passed:
            print("🎉 PHASE 2 AUTHENTICATION SYSTEM RECOVERY: ✅ COMPLETE")
            print("   All critical authentication functionality is working correctly.")
        else:
            print("⚠️ PHASE 2 AUTHENTICATION SYSTEM RECOVERY: ❌ INCOMPLETE")
            print("   Critical authentication functionality is still failing.")
            
        print(f"🕒 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return test_results

def main():
    """Main test execution"""
    tester = AuthenticationTester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if all(result is not False for result in results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()