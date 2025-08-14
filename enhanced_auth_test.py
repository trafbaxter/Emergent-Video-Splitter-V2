#!/usr/bin/env python3
"""
ENHANCED AUTHENTICATION SYSTEM TEST
Tests the enhanced authentication system for Video Splitter Pro as requested in review.

Expected Features to Test:
1. User Registration with Approval Workflow (pending status)
2. Admin Authentication (admin@videosplitter.com / TempAdmin123!)
3. Admin User Management Endpoints
4. User Login Restrictions for non-approved users
5. Account Locking after failed attempts
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from current system
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class EnhancedAuthTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.admin_token = None
        
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
        
    def test_api_discovery(self):
        """Test 0: API Discovery - Check what endpoints are actually available"""
        print("🔍 Testing API Discovery...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('endpoints', [])
                
                # Check for admin endpoints
                admin_endpoints = [ep for ep in endpoints if '/admin/' in ep]
                auth_endpoints = [ep for ep in endpoints if '/auth/' in ep]
                
                details = f"Available endpoints: {len(endpoints)} total. Auth endpoints: {auth_endpoints}. Admin endpoints: {admin_endpoints if admin_endpoints else 'NONE FOUND'}"
                
                # Success if we can discover the API structure
                self.log_test("API Discovery", True, details, response_time)
                return endpoints, admin_endpoints
                
            else:
                self.log_test("API Discovery", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return [], []
                
        except Exception as e:
            self.log_test("API Discovery", False, f"Request failed: {str(e)}")
            return [], []
    
    def test_admin_login(self):
        """Test 1: Admin Authentication - Test login with admin@videosplitter.com / TempAdmin123!"""
        print("🔍 Testing Admin Authentication...")
        
        admin_credentials = {
            "email": "admin@videosplitter.com",
            "password": "TempAdmin123!"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/login",
                json=admin_credentials,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if admin user exists and can login
                if 'access_token' in data:
                    self.admin_token = data['access_token']
                    user_info = data.get('user', {})
                    is_admin = user_info.get('role') == 'admin' or user_info.get('is_admin') == True
                    
                    details = f"Admin login successful. Token received. Admin role: {is_admin}. User info: {user_info}"
                    self.log_test("Admin Authentication", True, details, response_time)
                    return True
                else:
                    details = f"Login successful but no access_token. Response: {data}"
                    self.log_test("Admin Authentication", False, details, response_time)
                    return False
                    
            elif response.status_code == 401:
                details = "Admin credentials rejected - admin account may not exist or password incorrect"
                self.log_test("Admin Authentication", False, details, response_time)
                return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_test("Admin Authentication", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_endpoints(self):
        """Test 2: Admin User Management Endpoints"""
        print("🔍 Testing Admin User Management Endpoints...")
        
        admin_endpoints_to_test = [
            ("GET", "/api/admin/users", "List all users"),
            ("POST", "/api/admin/users/approve", "Approve/reject users"),
            ("POST", "/api/admin/users", "Create new users"),
            ("DELETE", "/api/admin/users/test-user-id", "Soft delete users")
        ]
        
        results = []
        
        for method, endpoint, description in admin_endpoints_to_test:
            try:
                headers = {'Content-Type': 'application/json'}
                if self.admin_token:
                    headers['Authorization'] = f'Bearer {self.admin_token}'
                
                start_time = time.time()
                
                if method == "GET":
                    response = requests.get(f"{self.api_base}{endpoint}", headers=headers, timeout=10)
                elif method == "POST":
                    test_data = {"test": "data"} if "approve" not in endpoint else {"user_id": "test", "action": "approve"}
                    response = requests.post(f"{self.api_base}{endpoint}", json=test_data, headers=headers, timeout=10)
                elif method == "DELETE":
                    response = requests.delete(f"{self.api_base}{endpoint}", headers=headers, timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201, 202]:
                    details = f"{description} - HTTP {response.status_code}: Endpoint exists and responds"
                    results.append(f"✅ {endpoint}")
                elif response.status_code == 404:
                    details = f"{description} - HTTP 404: Endpoint not implemented"
                    results.append(f"❌ {endpoint} (404 Not Found)")
                elif response.status_code == 401:
                    details = f"{description} - HTTP 401: Authentication required"
                    results.append(f"⚠️ {endpoint} (401 Unauthorized)")
                else:
                    details = f"{description} - HTTP {response.status_code}: {response.text[:100]}"
                    results.append(f"❌ {endpoint} ({response.status_code})")
                
                self.log_test(f"Admin Endpoint: {endpoint}", response.status_code in [200, 201, 202], details, response_time)
                
            except Exception as e:
                details = f"{description} - Request failed: {str(e)}"
                results.append(f"❌ {endpoint} (Error)")
                self.log_test(f"Admin Endpoint: {endpoint}", False, details)
        
        # Overall admin endpoints assessment
        working_endpoints = len([r for r in results if "✅" in r])
        total_endpoints = len(results)
        
        overall_success = working_endpoints > 0
        overall_details = f"Admin endpoints working: {working_endpoints}/{total_endpoints}. Results: {'; '.join(results)}"
        self.log_test("Admin User Management Endpoints", overall_success, overall_details)
        
        return working_endpoints > 0
    
    def test_user_registration_with_approval(self):
        """Test 3: User Registration with Approval Workflow"""
        print("🔍 Testing User Registration with Approval Workflow...")
        
        test_user = {
            "email": f"test-pending-{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "firstName": "Test",
            "lastName": "User",
            "confirmPassword": "TestPassword123!"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/register",
                json=test_user,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Check if user is created with "pending" status
                user_info = data.get('user', {})
                status = user_info.get('status') or user_info.get('approval_status')
                
                success_criteria = []
                
                if status == 'pending':
                    success_criteria.append("✅ User created with 'pending' status")
                elif status:
                    success_criteria.append(f"❌ User status: '{status}' (expected 'pending')")
                else:
                    success_criteria.append("❌ No status field found - may not have approval workflow")
                
                # Check for email notification indication
                email_sent = data.get('email_sent') or data.get('notification_sent')
                if email_sent:
                    success_criteria.append("✅ Email notification indicated")
                else:
                    success_criteria.append("⚠️ No email notification indication")
                
                # Check if access_token is NOT provided (pending users shouldn't get tokens)
                if 'access_token' not in data:
                    success_criteria.append("✅ No access_token for pending user")
                else:
                    success_criteria.append("❌ Access_token provided to pending user")
                
                all_success = status == 'pending'
                details = "; ".join(success_criteria)
                
                self.log_test("User Registration with Approval Workflow", all_success, details, response_time)
                return all_success, test_user['email']
                
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_test("User Registration with Approval Workflow", False, details, response_time)
                return False, None
                
        except Exception as e:
            self.log_test("User Registration with Approval Workflow", False, f"Request failed: {str(e)}")
            return False, None
    
    def test_pending_user_login_restriction(self, pending_user_email):
        """Test 4: User Login Restrictions for Pending Users"""
        print("🔍 Testing User Login Restrictions for Pending Users...")
        
        if not pending_user_email:
            self.log_test("User Login Restrictions", False, "No pending user email available for testing")
            return False
        
        login_data = {
            "email": pending_user_email,
            "password": "TestPassword123!"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                message = data.get('message', response.text)
                
                # Check if rejection is due to pending status
                if 'pending' in message.lower() or 'approval' in message.lower():
                    details = f"✅ Pending user login correctly rejected: {message}"
                    self.log_test("User Login Restrictions", True, details, response_time)
                    return True
                else:
                    details = f"⚠️ Login rejected but reason unclear: {message}"
                    self.log_test("User Login Restrictions", False, details, response_time)
                    return False
                    
            elif response.status_code == 200:
                details = "❌ Pending user was able to login (should be rejected)"
                self.log_test("User Login Restrictions", False, details, response_time)
                return False
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_test("User Login Restrictions", False, details, response_time)
                return False
                
        except Exception as e:
            self.log_test("User Login Restrictions", False, f"Request failed: {str(e)}")
            return False
    
    def test_account_locking(self):
        """Test 5: Account Locking after Failed Login Attempts"""
        print("🔍 Testing Account Locking after Failed Login Attempts...")
        
        # Create a test user first
        test_user = {
            "email": f"test-locking-{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "firstName": "Lock",
            "lastName": "Test",
            "confirmPassword": "TestPassword123!"
        }
        
        try:
            # Register user
            register_response = requests.post(
                f"{self.api_base}/api/auth/register",
                json=test_user,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if register_response.status_code not in [200, 201]:
                self.log_test("Account Locking", False, "Failed to create test user for locking test")
                return False
            
            # Attempt multiple failed logins
            failed_attempts = 0
            for attempt in range(6):  # Try 6 failed attempts
                wrong_login = {
                    "email": test_user['email'],
                    "password": "WrongPassword123!"
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.api_base}/api/auth/login",
                    json=wrong_login,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 401:
                    failed_attempts += 1
                    data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    message = data.get('message', response.text)
                    
                    # Check if account gets locked
                    if 'locked' in message.lower() or 'too many' in message.lower():
                        details = f"✅ Account locked after {failed_attempts} failed attempts: {message}"
                        self.log_test("Account Locking", True, details, response_time)
                        return True
                
                time.sleep(0.5)  # Brief pause between attempts
            
            # If we get here, account locking may not be implemented
            details = f"❌ Account not locked after {failed_attempts} failed login attempts"
            self.log_test("Account Locking", False, details)
            return False
            
        except Exception as e:
            self.log_test("Account Locking", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all enhanced authentication system tests"""
        print("🚀 ENHANCED AUTHENTICATION SYSTEM TEST")
        print("Testing enhanced authentication system for Video Splitter Pro")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("=" * 80)
        print()
        
        # Test 0: API Discovery
        endpoints, admin_endpoints = self.test_api_discovery()
        
        # Test 1: Admin Authentication
        admin_login_success = self.test_admin_login()
        
        # Test 2: Admin User Management Endpoints
        admin_endpoints_working = self.test_admin_endpoints()
        
        # Test 3: User Registration with Approval Workflow
        registration_success, pending_user_email = self.test_user_registration_with_approval()
        
        # Test 4: User Login Restrictions
        login_restriction_success = self.test_pending_user_login_restriction(pending_user_email)
        
        # Test 5: Account Locking
        account_locking_success = self.test_account_locking()
        
        # Summary
        test_results = [
            admin_login_success,
            admin_endpoints_working,
            registration_success,
            login_restriction_success,
            account_locking_success
        ]
        
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 ENHANCED AUTHENTICATION SYSTEM TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Assessment based on review request requirements
        if len(admin_endpoints) == 0:
            print("🚨 CRITICAL FINDING: No admin endpoints found in API")
            print("   Expected endpoints:")
            print("   - GET /api/admin/users (list all users)")
            print("   - POST /api/admin/users/approve (approve/reject users)")
            print("   - POST /api/admin/users (create new users)")
            print("   - DELETE /api/admin/users/{user_id} (soft delete users)")
            print()
        
        if not admin_login_success:
            print("🚨 CRITICAL FINDING: Admin account not accessible")
            print("   Expected: admin@videosplitter.com / TempAdmin123!")
            print()
        
        if not registration_success:
            print("🚨 CRITICAL FINDING: User registration approval workflow not implemented")
            print("   Expected: New users should register with 'pending' status")
            print()
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            print()
        
        print("CONCLUSION:")
        if success_rate >= 80:
            print("✅ Enhanced authentication system is mostly working")
        elif success_rate >= 50:
            print("⚠️ Enhanced authentication system is partially implemented")
        else:
            print("❌ Enhanced authentication system is not implemented or not working")
            print("   Current system appears to be basic authentication without admin features")
        
        print()
        return success_rate >= 80

if __name__ == "__main__":
    tester = EnhancedAuthTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)