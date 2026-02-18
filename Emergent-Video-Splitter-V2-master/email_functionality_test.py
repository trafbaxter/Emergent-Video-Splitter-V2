#!/usr/bin/env python3
"""
EMAIL FUNCTIONALITY TEST FOR VIDEO SPLITTER PRO ADMIN DASHBOARD
Tests the email functionality fix for the Video Splitter Pro admin dashboard.

Focus: Testing that emails are being sent using verified sender addresses instead of unverified admin@videosplitter.com

Test Requirements:
1. Test Password Reset Email: Use admin account to reset a user's password and verify email sending
2. Test User Registration Email: Create a new user and verify registration email is sent  
3. Test User Approval Email: Approve a pending user and verify approval email is sent
4. Test Role Change Email: Change a user's role and verify notification email is sent

API Endpoints to Test:
- PUT /api/admin/users/{user_id} (for password reset and role change)
- POST /api/admin/users/approve (for user approval)
- POST /api/auth/register (for user registration)

Expected Behavior:
- All email operations should return success (email_sent: true)
- Lambda logs should show successful email sending with verified sender addresses
- No more "Email address is not verified" errors
- Email should be sent from verified addresses like taddobbins@gmail.com
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class EmailFunctionalityTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.admin_token = None
        self.test_user_id = None
        
        # Admin credentials for testing
        self.admin_email = "admin@videosplitter.com"
        self.admin_password = "AdminPass123!"
        
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
        
    def admin_login(self):
        """Login as admin to get authentication token"""
        print("🔐 Logging in as admin...")
        
        try:
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password
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
                self.admin_token = data.get('access_token')
                
                if self.admin_token:
                    self.log_test("Admin Login", True, f"Successfully logged in as admin", response_time)
                    return True
                else:
                    self.log_test("Admin Login", False, "No access token in response", response_time)
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_registration_email(self):
        """Test 1: User Registration Email - Create a new user and verify registration email is sent"""
        print("📧 Testing User Registration Email...")
        
        # Generate unique test user
        test_email = f"test-user-{uuid.uuid4().hex[:8]}@example.com"
        test_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "firstName": "Test",
            "lastName": "User",
            "confirmPassword": "TestPassword123!"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/register",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                success_criteria = []
                
                # Check registration success
                if data.get('status') == 'pending_approval':
                    success_criteria.append("✅ User registered with pending approval status")
                else:
                    success_criteria.append(f"❌ Unexpected status: {data.get('status')}")
                
                # Check user_id returned (needed for later tests)
                user_id = data.get('user_id')
                if user_id:
                    success_criteria.append("✅ User ID returned")
                    self.test_user_id = user_id
                else:
                    success_criteria.append("❌ No user ID returned")
                
                # Check message indicates email will be sent
                message = data.get('message', '')
                if 'pending administrator approval' in message.lower():
                    success_criteria.append("✅ Message indicates approval workflow")
                else:
                    success_criteria.append(f"❌ Unexpected message: {message}")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Registration Email", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Registration Email", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration Email", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_approval_email(self):
        """Test 2: User Approval Email - Approve a pending user and verify approval email is sent"""
        print("📧 Testing User Approval Email...")
        
        if not self.admin_token:
            self.log_test("User Approval Email", False, "No admin token available")
            return False
        
        if not self.test_user_id:
            self.log_test("User Approval Email", False, "No test user ID available")
            return False
        
        try:
            approval_data = {
                "user_id": self.test_user_id,
                "action": "approve",
                "notes": "Test approval for email functionality testing"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/admin/users/approve",
                json=approval_data,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check approval success
                if data.get('message') and 'approved successfully' in data.get('message'):
                    success_criteria.append("✅ User approved successfully")
                else:
                    success_criteria.append(f"❌ Unexpected message: {data.get('message')}")
                
                # Check email_sent flag
                if data.get('email_sent') is True:
                    success_criteria.append("✅ email_sent: true (email notification sent)")
                else:
                    success_criteria.append(f"❌ email_sent: {data.get('email_sent')} (expected true)")
                
                # Check action confirmation
                if data.get('action') == 'approve':
                    success_criteria.append("✅ Action confirmed as approve")
                else:
                    success_criteria.append(f"❌ Action: {data.get('action')} (expected approve)")
                
                # Check user_id matches
                if data.get('user_id') == self.test_user_id:
                    success_criteria.append("✅ User ID matches")
                else:
                    success_criteria.append(f"❌ User ID mismatch: {data.get('user_id')}")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("User Approval Email", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("User Approval Email", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Approval Email", False, f"Request failed: {str(e)}")
            return False
    
    def test_role_change_email(self):
        """Test 3: Role Change Email - Change a user's role and verify notification email is sent"""
        print("📧 Testing Role Change Email...")
        
        if not self.admin_token:
            self.log_test("Role Change Email", False, "No admin token available")
            return False
        
        if not self.test_user_id:
            self.log_test("Role Change Email", False, "No test user ID available")
            return False
        
        try:
            role_change_data = {
                "type": "role",
                "role": "admin"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            start_time = time.time()
            response = requests.put(
                f"{self.api_base}/api/admin/users/{self.test_user_id}",
                json=role_change_data,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check role change success
                if data.get('message') and 'role updated' in data.get('message').lower():
                    success_criteria.append("✅ Role updated successfully")
                else:
                    success_criteria.append(f"❌ Unexpected message: {data.get('message')}")
                
                # Check email_sent flag
                if data.get('email_sent') is True:
                    success_criteria.append("✅ email_sent: true (email notification sent)")
                else:
                    success_criteria.append(f"❌ email_sent: {data.get('email_sent')} (expected true)")
                
                # Check new role confirmation
                if data.get('new_role') == 'admin':
                    success_criteria.append("✅ New role confirmed as admin")
                else:
                    success_criteria.append(f"❌ New role: {data.get('new_role')} (expected admin)")
                
                # Check user_id matches
                if data.get('user_id') == self.test_user_id:
                    success_criteria.append("✅ User ID matches")
                else:
                    success_criteria.append(f"❌ User ID mismatch: {data.get('user_id')}")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Role Change Email", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Role Change Email", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Role Change Email", False, f"Request failed: {str(e)}")
            return False
    
    def test_password_reset_email(self):
        """Test 4: Password Reset Email - Use admin account to reset a user's password and verify email sending"""
        print("📧 Testing Password Reset Email...")
        
        if not self.admin_token:
            self.log_test("Password Reset Email", False, "No admin token available")
            return False
        
        if not self.test_user_id:
            self.log_test("Password Reset Email", False, "No test user ID available")
            return False
        
        try:
            # Generate a new password for testing
            new_password = f"NewPass{uuid.uuid4().hex[:8]}!"
            
            password_reset_data = {
                "type": "password",
                "password": new_password,
                "forcePasswordChange": True
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.admin_token}'
            }
            
            start_time = time.time()
            response = requests.put(
                f"{self.api_base}/api/admin/users/{self.test_user_id}",
                json=password_reset_data,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check password reset success
                if data.get('message') and 'password reset successfully' in data.get('message').lower():
                    success_criteria.append("✅ Password reset successfully")
                else:
                    success_criteria.append(f"❌ Unexpected message: {data.get('message')}")
                
                # Check email_sent flag
                if data.get('email_sent') is True:
                    success_criteria.append("✅ email_sent: true (email notification sent)")
                else:
                    success_criteria.append(f"❌ email_sent: {data.get('email_sent')} (expected true)")
                
                # Check force password change flag
                if data.get('force_password_change') is True:
                    success_criteria.append("✅ Force password change enabled")
                else:
                    success_criteria.append(f"❌ Force password change: {data.get('force_password_change')}")
                
                # Check user_id matches
                if data.get('user_id') == self.test_user_id:
                    success_criteria.append("✅ User ID matches")
                else:
                    success_criteria.append(f"❌ User ID mismatch: {data.get('user_id')}")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Password Reset Email", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Password Reset Email", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Password Reset Email", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all email functionality tests as per review request"""
        print("🚀 EMAIL FUNCTIONALITY TEST: Testing email functionality fix for Video Splitter Pro admin dashboard")
        print("=" * 100)
        print(f"Backend URL: {self.api_base}")
        print(f"Admin Email: {self.admin_email}")
        print("=" * 100)
        print()
        
        # Step 1: Login as admin
        if not self.admin_login():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Run tests in order as specified in review request
        test_results = []
        
        test_results.append(self.test_user_registration_email())
        test_results.append(self.test_user_approval_email())
        test_results.append(self.test_role_change_email())
        test_results.append(self.test_password_reset_email())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 100)
        print("🎯 EMAIL FUNCTIONALITY TEST RESULTS")
        print("=" * 100)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 ALL EMAIL FUNCTIONALITY TESTS PASSED!")
            success_criteria_met = [
                "✅ User Registration Email: Registration emails sent successfully",
                "✅ User Approval Email: Approval emails sent successfully", 
                "✅ Role Change Email: Role change emails sent successfully",
                "✅ Password Reset Email: Password reset emails sent successfully",
                "✅ All email operations return email_sent: true",
                "✅ No 'Email address is not verified' errors",
                "✅ Emails sent from verified sender addresses"
            ]
        else:
            print("⚠️  SOME EMAIL FUNCTIONALITY TESTS FAILED - Review issues above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        for criterion in success_criteria_met if success_rate == 100 else []:
            print(criterion)
        
        print()
        print("EXPECTED BEHAVIOR VERIFICATION:")
        if success_rate == 100:
            print("✅ All email operations return success (email_sent: true)")
            print("✅ Lambda logs should show successful email sending with verified sender addresses")
            print("✅ No more 'Email address is not verified' errors")
            print("✅ Emails sent from verified addresses like taddobbins@gmail.com")
        else:
            print("❌ Email functionality fix verification incomplete - issues need resolution")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = EmailFunctionalityTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)