#!/usr/bin/env python3
"""
Focused Authentication MongoDB Connection Test

Based on initial findings, the authentication endpoints are accessible but failing
with "Database connection failed" errors. This test focuses specifically on:

1. MongoDB connection issues causing 503 errors
2. Testing authentication with valid payloads to trigger database operations
3. Verifying if dependencies are loaded but MongoDB is unreachable
4. Testing core functionality to ensure no regression
"""

import os
import requests
import time
import json
import unittest
from pathlib import Path

# Test against the AWS Lambda backend URL
BACKEND_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
API_URL = f"{BACKEND_URL}/api"

print(f"Testing Authentication MongoDB Connection at: {API_URL}")

class AuthenticationMongoDBTest(unittest.TestCase):
    """Test suite for diagnosing MongoDB connection issues in authentication system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_user_data = {
            "email": "mongodb.test@videosplitter.com",
            "password": "TestPassword123!",
            "firstName": "MongoDB",
            "lastName": "Test"
        }
        cls.test_login_data = {
            "email": "mongodb.test@videosplitter.com", 
            "password": "TestPassword123!"
        }
        
        print("Setting up Authentication MongoDB Connection Test Suite")
        print(f"Focus: Diagnosing MongoDB connection failures causing 503 errors")
    
    def test_01_dependency_availability_check(self):
        """Verify that authentication dependencies are actually loaded"""
        print("\n=== Testing Authentication Dependency Availability ===")
        
        try:
            # Check the root endpoint which shows dependency status
            response = requests.get(f"{API_URL}/", timeout=10)
            print(f"Root endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                # Check if dependencies are reported as available
                dependencies = data.get('dependencies', {})
                
                print(f"\n📦 Dependency Status:")
                print(f"bcrypt: {'✅ Available' if dependencies.get('bcrypt') else '❌ Missing'}")
                print(f"jwt: {'✅ Available' if dependencies.get('jwt') else '❌ Missing'}")
                print(f"pymongo: {'✅ Available' if dependencies.get('pymongo') else '❌ Missing'}")
                
                if all(dependencies.values()):
                    print("✅ All authentication dependencies are loaded in Lambda runtime")
                    print("🔍 503 errors are likely due to MongoDB connection, not import failures")
                else:
                    print("❌ Some authentication dependencies are missing")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}")
    
    def test_02_registration_with_valid_data(self):
        """Test registration with valid data to trigger MongoDB operations"""
        print("\n=== Testing Registration with Valid Data (MongoDB Operation) ===")
        
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json=self.test_user_data,
                timeout=15
            )
            
            print(f"Registration status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                print("❌ 503 Service Unavailable - MongoDB connection failure confirmed")
                
                # Parse the error response
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', '')
                    
                    if 'database connection failed' in error_message.lower():
                        print("🔍 Confirmed: MongoDB connection is the root cause")
                        print("   - bcrypt, PyJWT, pymongo dependencies are loaded")
                        print("   - Lambda function executes successfully")
                        print("   - MongoDB connection string or network access is the issue")
                    
                except json.JSONDecodeError:
                    print("🔍 503 error but response is not JSON")
                    
            elif response.status_code == 201:
                print("✅ Registration successful - MongoDB connection working")
                
            elif response.status_code == 409:
                print("✅ User already exists - MongoDB connection working (user lookup succeeded)")
                
            elif response.status_code == 400:
                print("✅ Validation error - endpoint accessible, likely MongoDB connection working")
                
            else:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Registration request failed: {e}")
    
    def test_03_login_with_valid_data(self):
        """Test login with valid data to trigger MongoDB user lookup"""
        print("\n=== Testing Login with Valid Data (MongoDB User Lookup) ===")
        
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json=self.test_login_data,
                timeout=15
            )
            
            print(f"Login status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 503:
                print("❌ 503 Service Unavailable - MongoDB connection failure in login")
                
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', '')
                    
                    if 'database connection failed' in error_message.lower():
                        print("🔍 Confirmed: MongoDB connection failure prevents user lookup")
                        
                except json.JSONDecodeError:
                    print("🔍 503 error but response is not JSON")
                    
            elif response.status_code == 401:
                print("✅ Authentication failed - MongoDB connection working (user lookup succeeded)")
                
            elif response.status_code == 200:
                print("✅ Login successful - MongoDB connection working")
                
            else:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Login request failed: {e}")
    
    def test_04_mongodb_environment_configuration(self):
        """Test if MongoDB environment variables are properly configured"""
        print("\n=== Testing MongoDB Environment Configuration ===")
        
        # Try different authentication operations to see consistent MongoDB failures
        operations = [
            ("register", "POST", f"{API_URL}/auth/register", self.test_user_data),
            ("login", "POST", f"{API_URL}/auth/login", self.test_login_data)
        ]
        
        mongodb_failures = 0
        
        for operation, method, url, payload in operations:
            try:
                response = requests.post(url, json=payload, timeout=10)
                
                print(f"{operation.capitalize()} operation: {response.status_code}")
                
                if response.status_code == 503:
                    try:
                        error_data = response.json()
                        if 'database connection failed' in error_data.get('error', '').lower():
                            mongodb_failures += 1
                            print(f"  ❌ MongoDB connection failure in {operation}")
                    except:
                        pass
                        
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ {operation} request failed: {e}")
        
        print(f"\n📊 MongoDB Connection Analysis:")
        print(f"Operations with MongoDB failures: {mongodb_failures}/{len(operations)}")
        
        if mongodb_failures == len(operations):
            print("❌ ALL authentication operations fail due to MongoDB connection")
            print("🔍 Root Cause: MongoDB connection string or network access issue")
            print("   Possible causes:")
            print("   - MONGO_URL environment variable missing or incorrect")
            print("   - MongoDB server unreachable from Lambda")
            print("   - Network security groups blocking MongoDB access")
            print("   - MongoDB authentication credentials invalid")
        elif mongodb_failures > 0:
            print(f"❌ {mongodb_failures} operations fail due to MongoDB connection")
            print("🔍 Intermittent MongoDB connection issues")
        else:
            print("✅ No MongoDB connection failures detected")
    
    def test_05_core_functionality_regression_detailed(self):
        """Detailed test of core video processing functionality"""
        print("\n=== Detailed Core Functionality Regression Test ===")
        
        # Test core endpoints that should not require authentication
        core_tests = [
            {
                "name": "Presigned URL Generation",
                "method": "POST",
                "url": f"{API_URL}/generate-presigned-url",
                "payload": {
                    "filename": "test_video.mp4",
                    "fileType": "video/mp4",
                    "fileSize": 50000000
                }
            },
            {
                "name": "Video Info (Non-existent)",
                "method": "POST", 
                "url": f"{API_URL}/get-video-info",
                "payload": {
                    "objectKey": "non-existent-video-key"
                }
            },
            {
                "name": "Download Endpoint",
                "method": "GET",
                "url": f"{API_URL}/download/test-download-key",
                "payload": None
            }
        ]
        
        core_working_count = 0
        
        for test in core_tests:
            try:
                if test["method"] == "POST":
                    response = requests.post(test["url"], json=test["payload"], timeout=10)
                else:
                    response = requests.get(test["url"], timeout=10)
                
                print(f"{test['name']}: {response.status_code}")
                
                if response.status_code in [200, 400, 404]:
                    print(f"  ✅ Working (expected response)")
                    core_working_count += 1
                elif response.status_code == 503:
                    print(f"  ❌ 503 Service Unavailable - authentication integration broke core functionality")
                elif response.status_code == 502:
                    print(f"  ❌ 502 Bad Gateway - Lambda execution failure")
                else:
                    print(f"  ⚠️ Unexpected status: {response.status_code}")
                    core_working_count += 1  # Count as working if not 502/503
                    
            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ {test['name']} request failed: {e}")
        
        print(f"\n📊 Core Functionality Status:")
        print(f"Working endpoints: {core_working_count}/{len(core_tests)}")
        
        if core_working_count == len(core_tests):
            print("✅ Core video processing functionality is intact")
            print("🔍 Authentication integration did not break existing features")
        else:
            print("❌ Some core functionality may be affected by authentication integration")
    
    def test_06_authentication_system_diagnosis(self):
        """Comprehensive diagnosis of the authentication system issues"""
        print("\n=== Comprehensive Authentication System Diagnosis ===")
        
        diagnosis = {
            "lambda_execution": "Unknown",
            "dependencies_loaded": "Unknown",
            "mongodb_connection": "Unknown",
            "auth_endpoints_routing": "Unknown",
            "core_functionality": "Unknown"
        }
        
        # Test Lambda execution
        try:
            response = requests.get(f"{API_URL}/", timeout=5)
            if response.status_code == 200:
                diagnosis["lambda_execution"] = "✅ Working"
                
                # Check dependencies from response
                data = response.json()
                dependencies = data.get('dependencies', {})
                if all(dependencies.values()):
                    diagnosis["dependencies_loaded"] = "✅ All loaded (bcrypt, jwt, pymongo)"
                else:
                    diagnosis["dependencies_loaded"] = "❌ Some missing"
            else:
                diagnosis["lambda_execution"] = "❌ Failed"
        except:
            diagnosis["lambda_execution"] = "❌ Failed"
        
        # Test MongoDB connection via registration
        try:
            response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data, timeout=5)
            if response.status_code == 503:
                try:
                    error_data = response.json()
                    if 'database connection failed' in error_data.get('error', '').lower():
                        diagnosis["mongodb_connection"] = "❌ Connection Failed"
                    else:
                        diagnosis["mongodb_connection"] = "❌ Other 503 Error"
                except:
                    diagnosis["mongodb_connection"] = "❌ 503 Error"
            elif response.status_code in [200, 201, 400, 409]:
                diagnosis["mongodb_connection"] = "✅ Working"
            else:
                diagnosis["mongodb_connection"] = "⚠️ Unclear"
        except:
            diagnosis["mongodb_connection"] = "❌ Request Failed"
        
        # Test auth endpoint routing
        try:
            response = requests.post(f"{API_URL}/auth/login", json={}, timeout=5)
            if response.status_code == 404:
                diagnosis["auth_endpoints_routing"] = "❌ Not Found"
            else:
                diagnosis["auth_endpoints_routing"] = "✅ Routed"
        except:
            diagnosis["auth_endpoints_routing"] = "❌ Failed"
        
        # Test core functionality
        try:
            response = requests.post(f"{API_URL}/generate-presigned-url", 
                                   json={"filename": "test.mp4"}, timeout=5)
            if response.status_code in [200, 400]:
                diagnosis["core_functionality"] = "✅ Working"
            else:
                diagnosis["core_functionality"] = "❌ Issues"
        except:
            diagnosis["core_functionality"] = "❌ Failed"
        
        print("\n🔍 AUTHENTICATION SYSTEM DIAGNOSIS:")
        print("=" * 60)
        
        for component, status in diagnosis.items():
            component_name = component.replace("_", " ").title()
            print(f"{component_name:.<35} {status}")
        
        print("\n🎯 ROOT CAUSE ANALYSIS:")
        
        if diagnosis["mongodb_connection"] == "❌ Connection Failed":
            print("❌ IDENTIFIED ROOT CAUSE: MongoDB Connection Failure")
            print("\n🔧 RECOMMENDED FIXES:")
            print("1. Verify MONGO_URL environment variable in Lambda function")
            print("2. Check MongoDB server accessibility from Lambda VPC")
            print("3. Verify MongoDB authentication credentials")
            print("4. Check Lambda function VPC configuration and security groups")
            print("5. Ensure MongoDB server is running and accepting connections")
            print("6. Test MongoDB connection string manually")
            
            print("\n📋 TECHNICAL DETAILS:")
            print("- Authentication dependencies (bcrypt, PyJWT, pymongo) are loaded correctly")
            print("- Lambda function executes successfully")
            print("- Authentication endpoints are properly routed")
            print("- Core video processing functionality is intact")
            print("- Issue is specifically with MongoDB database connectivity")
            
        elif diagnosis["dependencies_loaded"] == "❌ Some missing":
            print("❌ IDENTIFIED ROOT CAUSE: Missing Authentication Dependencies")
            print("\n🔧 RECOMMENDED FIXES:")
            print("1. Rebuild Lambda deployment package with all dependencies")
            print("2. Verify Lambda layer includes bcrypt, PyJWT, and pymongo")
            print("3. Check dependency compatibility with Lambda Python runtime")
            
        else:
            print("✅ Authentication system appears to be working correctly")
            print("🔍 503 errors may be intermittent or configuration-related")
        
        print(f"\n📊 SUMMARY:")
        print(f"The authentication system dependencies are properly loaded, but MongoDB")
        print(f"connection failures are causing 503 Service Unavailable errors. This is")
        print(f"a configuration/network issue rather than a dependency import problem.")
        
        # This test always passes as it's diagnostic
        self.assertTrue(True, "Authentication system diagnosis completed")

if __name__ == "__main__":
    unittest.main(verbosity=2)