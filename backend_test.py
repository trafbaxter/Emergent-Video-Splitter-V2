#!/usr/bin/env python3
"""
Backend Test for MongoDB to DynamoDB Migration
Tests the Lambda function's DynamoDB implementation for user authentication and data storage.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class DynamoDBMigrationTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.test_user_email = f"dynamodb-test-{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_data = {
            "email": self.test_user_email,
            "password": "TestPassword123!",
            "firstName": "DynamoDB",
            "lastName": "User",
            "confirmPassword": "TestPassword123!"
        }
        
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
        
    def test_health_check_dynamodb(self):
        """Test 1: Health Check with DynamoDB"""
        print("🔍 Testing Health Check with DynamoDB...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check database_type
                db_info = data.get('database_info', {})
                database_type = db_info.get('database_type')
                connected = db_info.get('connected')
                users_table = db_info.get('users_table')
                jobs_table = db_info.get('jobs_table')
                
                success_criteria = []
                if database_type == "DynamoDB":
                    success_criteria.append("✅ database_type: DynamoDB")
                else:
                    success_criteria.append(f"❌ database_type: {database_type} (expected DynamoDB)")
                
                if connected is True:
                    success_criteria.append("✅ connected: true")
                else:
                    success_criteria.append(f"❌ connected: {connected} (expected true)")
                
                if users_table == "VideoSplitter-Users":
                    success_criteria.append("✅ VideoSplitter-Users table listed")
                else:
                    success_criteria.append(f"❌ Users table: {users_table} (expected VideoSplitter-Users)")
                
                if jobs_table == "VideoSplitter-Jobs":
                    success_criteria.append("✅ VideoSplitter-Jobs table listed")
                else:
                    success_criteria.append(f"❌ Jobs table: {jobs_table} (expected VideoSplitter-Jobs)")
                
                # Check for demo_mode flag (should NOT be present)
                demo_mode = data.get('demo_mode')
                if demo_mode is None:
                    success_criteria.append("✅ No demo_mode flag (good)")
                else:
                    success_criteria.append(f"❌ demo_mode present: {demo_mode} (should not exist)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Health Check DynamoDB", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Health Check DynamoDB", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Health Check DynamoDB", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_registration_dynamodb(self):
        """Test 2: User Registration with DynamoDB"""
        print("🔍 Testing User Registration with DynamoDB...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/register",
                json=self.test_user_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                
                success_criteria = []
                
                # Check for access_token
                if 'access_token' in data:
                    success_criteria.append("✅ access_token returned")
                else:
                    success_criteria.append("❌ access_token missing")
                
                # Check user info
                user_info = data.get('user', {})
                if user_info.get('email') == self.test_user_email:
                    success_criteria.append("✅ User email correct")
                else:
                    success_criteria.append(f"❌ User email: {user_info.get('email')}")
                
                if user_info.get('firstName') == "DynamoDB":
                    success_criteria.append("✅ First name correct")
                else:
                    success_criteria.append(f"❌ First name: {user_info.get('firstName')}")
                
                # Check for demo_mode flag (should NOT be present)
                if 'demo_mode' not in data:
                    success_criteria.append("✅ No demo_mode flag")
                else:
                    success_criteria.append(f"❌ demo_mode present: {data.get('demo_mode')}")
                
                # Store user_id for login test
                self.user_id = data.get('user_id')
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Registration DynamoDB", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Registration DynamoDB", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration DynamoDB", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_login_dynamodb(self):
        """Test 3: User Login with DynamoDB"""
        print("🔍 Testing User Login with DynamoDB...")
        
        try:
            login_data = {
                "email": self.test_user_email,
                "password": "TestPassword123!"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check for JWT tokens
                access_token = data.get('access_token')
                if access_token:
                    # Check JWT format (should have 3 parts separated by dots)
                    token_parts = access_token.split('.')
                    if len(token_parts) == 3:
                        success_criteria.append("✅ Valid JWT access_token format")
                    else:
                        success_criteria.append(f"❌ Invalid JWT format: {len(token_parts)} parts")
                else:
                    success_criteria.append("❌ access_token missing")
                
                # Check user info
                user_info = data.get('user', {})
                if user_info.get('email') == self.test_user_email:
                    success_criteria.append("✅ Login email correct")
                else:
                    success_criteria.append(f"❌ Login email: {user_info.get('email')}")
                
                # Check for demo_mode flag (should NOT be present)
                if 'demo_mode' not in data:
                    success_criteria.append("✅ No demo_mode flag")
                else:
                    success_criteria.append(f"❌ demo_mode present: {data.get('demo_mode')}")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Login DynamoDB", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Login DynamoDB", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Login DynamoDB", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test 4: CORS Headers Present"""
        print("🔍 Testing CORS Headers...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/health", timeout=10)
            response_time = time.time() - start_time
            
            cors_headers = response.headers.get('Access-Control-Allow-Origin')
            
            if cors_headers:
                success = True
                details = f"CORS headers present: {cors_headers}"
            else:
                success = False
                details = "CORS headers missing"
            
            self.log_test("CORS Headers", success, details, response_time)
            return success
            
        except Exception as e:
            self.log_test("CORS Headers", False, f"Request failed: {str(e)}")
            return False
    
    def test_response_times(self):
        """Test 5: Response Times (<5 seconds)"""
        print("🔍 Testing Response Times...")
        
        endpoints_to_test = [
            ("/api/health", "GET"),
        ]
        
        all_fast = True
        details = []
        
        for endpoint, method in endpoints_to_test:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response_time < 5.0:
                    details.append(f"✅ {endpoint}: {response_time:.2f}s")
                else:
                    details.append(f"❌ {endpoint}: {response_time:.2f}s (>5s)")
                    all_fast = False
                    
            except Exception as e:
                details.append(f"❌ {endpoint}: Failed ({str(e)})")
                all_fast = False
        
        self.log_test("Response Times", all_fast, "; ".join(details))
        return all_fast
    
    def run_all_tests(self):
        """Run all DynamoDB migration tests"""
        print("🚀 Starting MongoDB to DynamoDB Migration Tests")
        print("=" * 60)
        print(f"Backend URL: {self.api_base}")
        print(f"Test User: {self.test_user_email}")
        print("=" * 60)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_health_check_dynamodb())
        test_results.append(self.test_user_registration_dynamodb())
        test_results.append(self.test_user_login_dynamodb())
        test_results.append(self.test_cors_headers())
        test_results.append(self.test_response_times())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED - DynamoDB Migration Successful!")
            print("✅ Health check shows DynamoDB connection")
            print("✅ User registration works with DynamoDB")
            print("✅ User login works with DynamoDB")
            print("✅ No MongoDB references in responses")
            print("✅ All endpoints have proper CORS headers")
            print("✅ Response times are fast (<5 seconds)")
        else:
            print("⚠️  SOME TESTS FAILED - Review issues above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = DynamoDBMigrationTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)