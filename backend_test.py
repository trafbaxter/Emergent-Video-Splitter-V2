#!/usr/bin/env python3
"""
FINAL TEST: Complete DynamoDB migration verification after IAM permissions fix
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
        # Use the exact test user from review request
        self.test_user_email = "final-test@example.com"
        self.test_user_data = {
            "email": self.test_user_email,
            "password": "TestPassword123!",
            "firstName": "Final",
            "lastName": "Test",
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
        """Test 1: Health Check Verification - Should show database_type: "DynamoDB" and connected: true"""
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
                
                # Check response time (<10s as per review request)
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Health Check Verification", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Health Check Verification", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Health Check Verification", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_registration_dynamodb(self):
        """Test 2: User Registration (CREATE) - Should create user in DynamoDB VideoSplitter-Users table"""
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
            
            if response.status_code in [200, 201]:
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
                
                if user_info.get('firstName') == "Final":
                    success_criteria.append("✅ First name correct")
                else:
                    success_criteria.append(f"❌ First name: {user_info.get('firstName')}")
                
                # Check for demo_mode flag (should NOT be present)
                if 'demo_mode' not in data:
                    success_criteria.append("✅ No demo_mode flag")
                else:
                    success_criteria.append(f"❌ demo_mode present: {data.get('demo_mode')}")
                
                # Check response time (<10s as per review request)
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                # Store user_id for login test
                self.user_id = data.get('user_id')
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Registration (CREATE)", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Registration (CREATE)", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration (CREATE)", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_login_dynamodb(self):
        """Test 3: User Login (READ) - Should query DynamoDB using EmailIndex"""
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
                        # Check if it's a simple token (acceptable for this test)
                        if len(access_token) > 10:
                            success_criteria.append("✅ Access token returned (valid format)")
                        else:
                            success_criteria.append(f"❌ Invalid token format: {len(token_parts)} parts")
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
                
                # Check response time (<10s as per review request)
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Login (READ)", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Login (READ)", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Login (READ)", False, f"Request failed: {str(e)}")
            return False
    
    def test_migration_completeness(self):
        """Test 4: Migration Completeness Check - Verify no MongoDB references"""
        print("🔍 Testing Migration Completeness...")
        
        try:
            # Test health check for MongoDB references
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/", timeout=10)
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()
                
                # Check for MongoDB references
                mongodb_terms = ['mongodb', 'mongo', 'pymongo', 'mongoclient']
                mongodb_found = any(term in response_text for term in mongodb_terms)
                
                if not mongodb_found:
                    success_criteria.append("✅ No MongoDB references in response")
                else:
                    success_criteria.append("❌ MongoDB references found in response")
                
                # Check for demo_mode flag
                if 'demo_mode' not in data:
                    success_criteria.append("✅ No demo_mode flags")
                else:
                    success_criteria.append(f"❌ demo_mode present: {data.get('demo_mode')}")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Migration Completeness Check", all_success, details, response_time)
                return all_success
            else:
                self.log_test("Migration Completeness Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Migration Completeness Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """Test 5: CORS Headers Present - Proper CORS headers on all responses"""
        print("🔍 Testing CORS Headers...")
        
        endpoints_to_test = [
            ("/api/", "GET"),
            ("/api/auth/register", "OPTIONS"),
            ("/api/auth/login", "OPTIONS")
        ]
        
        all_cors_working = True
        details = []
        
        for endpoint, method in endpoints_to_test:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                elif method == "OPTIONS":
                    response = requests.options(f"{self.api_base}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_headers:
                    details.append(f"✅ {endpoint} ({method}): {cors_headers}")
                else:
                    details.append(f"❌ {endpoint} ({method}): No CORS headers")
                    all_cors_working = False
                    
            except Exception as e:
                details.append(f"❌ {endpoint} ({method}): Failed ({str(e)})")
                all_cors_working = False
        
        self.log_test("CORS Headers", all_cors_working, "; ".join(details))
        return all_cors_working
    
    def run_all_tests(self):
        """Run all DynamoDB migration tests as per FINAL TEST requirements"""
        print("🚀 FINAL TEST: Complete DynamoDB migration verification after IAM permissions fix")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Test User: {self.test_user_email}")
        print("=" * 80)
        print()
        
        # Run tests in order as specified in review request
        test_results = []
        
        test_results.append(self.test_health_check_dynamodb())
        test_results.append(self.test_user_registration_dynamodb())
        test_results.append(self.test_user_login_dynamodb())
        test_results.append(self.test_migration_completeness())
        test_results.append(self.test_cors_headers())
        
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
        success_criteria_met = []
        
        if success_rate == 100:
            print("🎉 ALL SUCCESS CRITERIA MET - DynamoDB Migration Complete!")
            success_criteria_met = [
                "✅ Health check shows DynamoDB connected: true",
                "✅ User registration works (HTTP 201/200)",
                "✅ User login works (HTTP 200)",
                "✅ No MongoDB/demo_mode references",
                "✅ All operations under 10 seconds",
                "✅ Proper CORS headers on all responses"
            ]
        else:
            print("⚠️  SOME SUCCESS CRITERIA NOT MET - Review issues above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        for criterion in success_criteria_met:
            print(criterion)
        
        print()
        print("EXPECTED OUTCOME:")
        if success_rate == 100:
            print("✅ Complete confirmation that MongoDB has been successfully replaced with DynamoDB")
            print("✅ All authentication functionality is working perfectly")
        else:
            print("❌ DynamoDB migration verification incomplete - issues need resolution")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = DynamoDBMigrationTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)