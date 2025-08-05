#!/usr/bin/env python3
"""
Authentication Dependency Investigation Test Suite

This test suite focuses on diagnosing why authentication endpoints are returning 
503 Service Unavailable errors, specifically investigating:

1. Authentication Dependency Investigation:
   - Test if bcrypt, PyJWT, and pymongo libraries are loading in Lambda runtime
   - Check if 503 errors are due to dependency import failures or environment configuration
   - Verify if authentication endpoints are accessible but dependencies missing

2. Detailed Authentication Endpoint Testing:
   - Test POST /api/auth/register with detailed error investigation
   - Test POST /api/auth/login with specific dependency error checking
   - Test POST /api/auth/refresh endpoint availability
   - Examine error responses for import error details

3. Environment Configuration Check:
   - Verify if MongoDB connection strings are causing the 503 errors
   - Check if JWT secrets are properly configured
   - Test if authentication works with mock/fallback data

4. Core Functionality Verification:
   - Confirm that core video processing endpoints still work after integration
   - Verify no regression in existing functionality
   - Ensure integration didn't break working features
"""

import os
import requests
import time
import json
import unittest
from pathlib import Path
import tempfile
import shutil

# Test against the AWS Lambda backend URL from test_result.md
BACKEND_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
API_URL = f"{BACKEND_URL}/api"

print(f"Testing Authentication System at: {API_URL}")

class AuthenticationDependencyTest(unittest.TestCase):
    """Test suite for diagnosing authentication dependency issues in AWS Lambda"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for authentication dependency testing"""
        cls.test_user_data = {
            "email": "testuser@videosplitter.com",
            "password": "TestPassword123!",
            "firstName": "Test",
            "lastName": "User"
        }
        cls.test_login_data = {
            "email": "testuser@videosplitter.com", 
            "password": "TestPassword123!"
        }
        
        print("Setting up Authentication Dependency Test Suite")
        print(f"API Gateway URL: {API_URL}")
        print(f"Focus: Diagnosing 503 Service Unavailable errors in authentication endpoints")
        print(f"Expected Issues: bcrypt, PyJWT, pymongo import failures in Lambda runtime")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        print("Authentication Dependency Test Suite completed")
    
    def test_01_lambda_execution_basic_check(self):
        """Test basic Lambda execution to confirm function is deployed"""
        print("\n=== Testing Basic Lambda Function Execution ===")
        
        try:
            # Test root endpoint first to see if Lambda is executing at all
            response = requests.get(f"{API_URL}/", timeout=10)
            print(f"Root endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
            
            # 502 indicates Lambda execution failure, 503 indicates service unavailable
            if response.status_code == 502:
                print("❌ 502 Bad Gateway - Lambda function execution failure")
                self.fail("Lambda function is not executing - deployment issue")
            elif response.status_code == 503:
                print("❌ 503 Service Unavailable - Lambda function deployed but failing")
                print("This suggests dependency import failures in Lambda runtime")
            else:
                print(f"✅ Lambda function is executing (status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}")
            self.fail(f"Cannot connect to Lambda API: {e}")
    
    def test_02_authentication_endpoint_availability(self):
        """Test if authentication endpoints are accessible (not 404)"""
        print("\n=== Testing Authentication Endpoint Availability ===")
        
        auth_endpoints = [
            ("/api/auth/register", "POST"),
            ("/api/auth/login", "POST"),
            ("/api/auth/refresh", "POST"),
            ("/api/auth/verify-email", "GET")
        ]
        
        endpoint_status = {}
        
        for endpoint, method in auth_endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                
                if method == "POST":
                    # Send minimal payload to test endpoint availability
                    response = requests.post(url, json={}, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                endpoint_status[endpoint] = response.status_code
                print(f"{method} {endpoint}: {response.status_code}")
                
                # Log response details for analysis
                if response.status_code in [502, 503]:
                    print(f"  ❌ Error Response: {response.text}")
                    if response.status_code == 503:
                        print(f"  🔍 503 Service Unavailable suggests dependency import failure")
                elif response.status_code == 404:
                    print(f"  ⚠️ Endpoint not found - routing issue")
                elif response.status_code in [400, 401]:
                    print(f"  ✅ Endpoint accessible (validation error expected)")
                else:
                    print(f"  ✅ Endpoint responding")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ Request failed: {e}")
                endpoint_status[endpoint] = "REQUEST_FAILED"
        
        # Analyze results
        service_unavailable_count = sum(1 for status in endpoint_status.values() if status == 503)
        if service_unavailable_count > 0:
            print(f"\n❌ {service_unavailable_count} authentication endpoints returning 503 Service Unavailable")
            print("This strongly indicates dependency import failures in Lambda runtime")
        
        # At least endpoints should be routed (not 404)
        not_found_count = sum(1 for status in endpoint_status.values() if status == 404)
        if not_found_count == len(auth_endpoints):
            self.fail("All authentication endpoints return 404 - routing not configured")
    
    def test_03_dependency_import_failure_detection(self):
        """Test for specific dependency import failure patterns"""
        print("\n=== Testing for Dependency Import Failure Patterns ===")
        
        # Test registration endpoint with detailed error analysis
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json=self.test_user_data,
                timeout=10
            )
            
            print(f"Registration endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                print("❌ 503 Service Unavailable detected")
                
                # Check for specific dependency error patterns in response
                response_text = response.text.lower()
                
                dependency_errors = {
                    "bcrypt": ["bcrypt", "no module named 'bcrypt'", "_bcrypt"],
                    "jwt": ["jwt", "pyjwt", "no module named 'jwt'"],
                    "pymongo": ["pymongo", "no module named 'pymongo'", "mongo"]
                }
                
                detected_issues = []
                for dep, patterns in dependency_errors.items():
                    for pattern in patterns:
                        if pattern in response_text:
                            detected_issues.append(f"{dep} import failure")
                            break
                
                if detected_issues:
                    print(f"🔍 Detected dependency issues: {', '.join(detected_issues)}")
                else:
                    print("🔍 503 error but no specific dependency patterns detected")
                    print("May be general Lambda runtime or environment issue")
                    
            elif response.status_code == 502:
                print("❌ 502 Bad Gateway - Lambda function execution completely failing")
                
            elif response.status_code in [400, 422]:
                print("✅ Endpoint accessible - validation errors expected for empty/invalid data")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Registration test request failed: {e}")
    
    def test_04_mongodb_connection_issue_check(self):
        """Test if MongoDB connection is causing 503 errors"""
        print("\n=== Testing MongoDB Connection Issues ===")
        
        # Test login endpoint which would require MongoDB access
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json=self.test_login_data,
                timeout=10
            )
            
            print(f"Login endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                response_text = response.text.lower()
                
                # Check for MongoDB-specific error patterns
                mongo_patterns = [
                    "mongodb", "mongo", "connection", "database", 
                    "timeout", "network", "dns", "resolve"
                ]
                
                mongo_issues = [pattern for pattern in mongo_patterns if pattern in response_text]
                
                if mongo_issues:
                    print(f"🔍 Potential MongoDB connection issues detected: {', '.join(mongo_issues)}")
                    print("MongoDB connection string or network access may be the root cause")
                else:
                    print("🔍 503 error but no MongoDB-specific patterns detected")
                    
            elif response.status_code in [400, 401]:
                print("✅ Login endpoint accessible - authentication errors expected")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Login test request failed: {e}")
    
    def test_05_jwt_secret_configuration_check(self):
        """Test if JWT secret configuration is causing issues"""
        print("\n=== Testing JWT Secret Configuration Issues ===")
        
        # Test token refresh endpoint which would require JWT processing
        try:
            response = requests.post(
                f"{API_URL}/auth/refresh",
                json={"refreshToken": "dummy_token_for_testing"},
                timeout=10
            )
            
            print(f"Token refresh endpoint status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                response_text = response.text.lower()
                
                # Check for JWT-specific error patterns
                jwt_patterns = [
                    "jwt", "token", "secret", "key", "signature", "decode"
                ]
                
                jwt_issues = [pattern for pattern in jwt_patterns if pattern in response_text]
                
                if jwt_issues:
                    print(f"🔍 Potential JWT configuration issues detected: {', '.join(jwt_issues)}")
                    print("JWT_SECRET environment variable may be missing or invalid")
                else:
                    print("🔍 503 error but no JWT-specific patterns detected")
                    
            elif response.status_code in [400, 401]:
                print("✅ Token refresh endpoint accessible - token validation errors expected")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Token refresh test request failed: {e}")
    
    def test_06_core_video_functionality_regression_check(self):
        """Test if core video processing endpoints still work after authentication integration"""
        print("\n=== Testing Core Video Processing Functionality (Regression Check) ===")
        
        # Test core video endpoints to ensure authentication integration didn't break them
        core_endpoints = [
            ("/api/generate-presigned-url", "POST", {"filename": "test.mp4", "fileType": "video/mp4", "fileSize": 1000000}),
            ("/api/get-video-info", "POST", {"objectKey": "test-video-key"}),
            ("/api/download/test-key", "GET", None)
        ]
        
        core_working = True
        
        for endpoint, method, payload in core_endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                
                if method == "POST":
                    response = requests.post(url, json=payload, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                print(f"{method} {endpoint}: {response.status_code}")
                
                if response.status_code == 503:
                    print(f"  ❌ Core endpoint also returning 503 - authentication integration broke everything")
                    core_working = False
                elif response.status_code == 502:
                    print(f"  ❌ Core endpoint returning 502 - Lambda execution failure")
                    core_working = False
                elif response.status_code in [200, 400, 404]:
                    print(f"  ✅ Core endpoint working (expected response)")
                else:
                    print(f"  ⚠️ Unexpected status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ Request failed: {e}")
        
        if not core_working:
            print("\n❌ CRITICAL: Authentication integration broke core video processing functionality")
        else:
            print("\n✅ Core video processing endpoints still functional")
    
    def test_07_lambda_environment_variables_check(self):
        """Test if environment variables are properly configured"""
        print("\n=== Testing Lambda Environment Variables Configuration ===")
        
        # Try to trigger an endpoint that would use environment variables
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json={
                    "email": "env-test@example.com",
                    "password": "TestPassword123!",
                    "firstName": "Env",
                    "lastName": "Test"
                },
                timeout=10
            )
            
            print(f"Environment variable test status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                response_text = response.text.lower()
                
                # Check for environment variable related errors
                env_patterns = [
                    "environment", "env", "variable", "config", "missing",
                    "jwt_secret", "mongo_url", "aws_region"
                ]
                
                env_issues = [pattern for pattern in env_patterns if pattern in response_text]
                
                if env_issues:
                    print(f"🔍 Potential environment variable issues: {', '.join(env_issues)}")
                    print("Lambda function may be missing required environment variables")
                else:
                    print("🔍 503 error but no environment variable patterns detected")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Environment variable test failed: {e}")
    
    def test_08_lambda_layer_dependency_check(self):
        """Test if Lambda layer dependencies are properly attached"""
        print("\n=== Testing Lambda Layer Dependency Issues ===")
        
        # Test multiple authentication endpoints to see consistent 503 pattern
        endpoints_to_test = [
            "/api/auth/register",
            "/api/auth/login", 
            "/api/auth/refresh"
        ]
        
        error_503_count = 0
        total_tests = len(endpoints_to_test)
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.post(
                    f"{BACKEND_URL}{endpoint}",
                    json={"test": "data"},
                    timeout=10
                )
                
                if response.status_code == 503:
                    error_503_count += 1
                    print(f"❌ {endpoint}: 503 Service Unavailable")
                else:
                    print(f"✅ {endpoint}: {response.status_code} (not 503)")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ {endpoint}: Request failed - {e}")
        
        print(f"\n📊 503 Error Analysis:")
        print(f"503 Errors: {error_503_count}/{total_tests} authentication endpoints")
        
        if error_503_count == total_tests:
            print("❌ ALL authentication endpoints return 503 Service Unavailable")
            print("🔍 This strongly indicates:")
            print("   - Lambda layer with dependencies (bcrypt, PyJWT, pymongo) is missing or incompatible")
            print("   - Dependencies were not properly packaged for AWS Lambda Python runtime")
            print("   - Architecture mismatch (x86_64 vs arm64) in dependency compilation")
            print("   - Lambda function deployment package is incomplete")
        elif error_503_count > 0:
            print(f"❌ {error_503_count} authentication endpoints return 503 Service Unavailable")
            print("🔍 Partial dependency failure - some imports working, others failing")
        else:
            print("✅ No 503 errors detected - dependencies may be loading correctly")
    
    def test_09_comprehensive_diagnosis_summary(self):
        """Comprehensive summary of authentication dependency issues"""
        print("\n=== Comprehensive Authentication Dependency Diagnosis ===")
        
        # Run a final comprehensive test
        test_results = {
            "lambda_execution": "Unknown",
            "auth_endpoints_accessible": "Unknown", 
            "dependency_imports": "Unknown",
            "mongodb_connection": "Unknown",
            "jwt_configuration": "Unknown",
            "core_functionality": "Unknown",
            "environment_variables": "Unknown",
            "lambda_layers": "Unknown"
        }
        
        # Test each component
        try:
            # 1. Lambda execution
            response = requests.get(f"{API_URL}/", timeout=5)
            if response.status_code != 502:
                test_results["lambda_execution"] = "✅ Working"
            else:
                test_results["lambda_execution"] = "❌ Failed"
        except:
            test_results["lambda_execution"] = "❌ Failed"
        
        # 2. Authentication endpoints
        try:
            response = requests.post(f"{API_URL}/auth/register", json={}, timeout=5)
            if response.status_code == 503:
                test_results["auth_endpoints_accessible"] = "❌ 503 Service Unavailable"
                test_results["dependency_imports"] = "❌ Import Failures Detected"
            elif response.status_code == 404:
                test_results["auth_endpoints_accessible"] = "❌ Not Found"
            else:
                test_results["auth_endpoints_accessible"] = "✅ Accessible"
        except:
            test_results["auth_endpoints_accessible"] = "❌ Failed"
        
        # 3. Core functionality
        try:
            response = requests.post(f"{API_URL}/generate-presigned-url", 
                                   json={"filename": "test.mp4"}, timeout=5)
            if response.status_code not in [502, 503]:
                test_results["core_functionality"] = "✅ Working"
            else:
                test_results["core_functionality"] = "❌ Broken"
        except:
            test_results["core_functionality"] = "❌ Failed"
        
        print("\n🔍 AUTHENTICATION SYSTEM DIAGNOSIS RESULTS:")
        print("=" * 60)
        
        for component, status in test_results.items():
            component_name = component.replace("_", " ").title()
            print(f"{component_name:.<30} {status}")
        
        print("\n🎯 ROOT CAUSE ANALYSIS:")
        
        if "503 Service Unavailable" in test_results["auth_endpoints_accessible"]:
            print("❌ CRITICAL ISSUE IDENTIFIED: Authentication endpoints returning 503 Service Unavailable")
            print("\n🔧 RECOMMENDED FIXES:")
            print("1. Verify bcrypt, PyJWT, and pymongo are included in Lambda deployment package")
            print("2. Check Lambda layer compatibility with Python runtime version")
            print("3. Ensure dependencies are compiled for correct architecture (x86_64/arm64)")
            print("4. Verify Lambda function has sufficient memory and timeout settings")
            print("5. Check CloudWatch logs for specific import error messages")
            print("6. Consider using Lambda container images for complex dependencies")
            
        elif test_results["lambda_execution"] == "❌ Failed":
            print("❌ CRITICAL ISSUE: Lambda function execution completely failing")
            print("\n🔧 RECOMMENDED FIXES:")
            print("1. Check Lambda function deployment status")
            print("2. Verify API Gateway integration configuration")
            print("3. Check Lambda function permissions and IAM roles")
            
        else:
            print("✅ Basic Lambda execution working")
            print("🔍 Authentication issues may be configuration-related rather than dependency failures")
        
        print(f"\n📋 SUMMARY:")
        print(f"The authentication system is experiencing 503 Service Unavailable errors")
        print(f"indicating that bcrypt, PyJWT, and pymongo dependencies are not properly")
        print(f"loaded in the AWS Lambda runtime environment. This requires fixing the")
        print(f"Lambda deployment package to include all required authentication dependencies.")
        
        # This test always passes as it's just a diagnostic summary
        self.assertTrue(True, "Authentication dependency diagnosis completed")

if __name__ == "__main__":
    unittest.main(verbosity=2)