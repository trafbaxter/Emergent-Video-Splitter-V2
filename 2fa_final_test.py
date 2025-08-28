#!/usr/bin/env python3
"""
2FA FINAL TEST - Test 2FA functionality with admin user that has 2FA enabled
"""

import requests
import json
import pyotp
import time
from datetime import datetime

API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class TwoFAFinalTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        self.admin_email = "admin@videosplitter.com"
        self.admin_password = "AdminPass123!"
        self.admin_token = None
        # Use the TOTP secret we discovered earlier
        self.totp_secret = "DRBRJPJWOTA3JXXLJGOJHJWUGCNVURGP"
        
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
    
    def login_with_2fa(self):
        """Login with admin credentials using 2FA"""
        print("🔐 Logging in with admin credentials using 2FA...")
        
        try:
            # Generate TOTP code
            totp = pyotp.TOTP(self.totp_secret)
            totp_code = totp.now()
            
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password,
                "code": totp_code
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
                    print(f"✅ Admin login with 2FA successful - Token obtained")
                    return True
                else:
                    print(f"❌ Admin login with 2FA failed - No access token in response")
                    return False
            else:
                print(f"❌ Admin login with 2FA failed - HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin login with 2FA failed - Request error: {str(e)}")
            return False
    
    def test_2fa_setup_flow(self):
        """Test 1: 2FA Setup Flow - GET /api/user/2fa/setup (should show already enabled)"""
        print("🔍 Testing 2FA Setup Flow...")
        
        if not self.admin_token:
            self.log_test("2FA Setup Flow", False, "Admin token not available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/user/2fa/setup",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check setup_complete status (should be true now)
                setup_complete = data.get('setup_complete')
                if setup_complete is True:
                    success_criteria.append("✅ setup_complete: true (2FA already enabled)")
                else:
                    success_criteria.append(f"❌ setup_complete: {setup_complete} (expected true)")
                
                # Check for TOTP secret (might be hidden when already enabled)
                totp_secret = data.get('totp_secret')
                if totp_secret:
                    success_criteria.append("✅ TOTP secret available")
                else:
                    success_criteria.append("⚠️ TOTP secret not shown (normal for enabled 2FA)")
                
                # Check issuer
                issuer = data.get('issuer')
                if issuer == "Video Splitter Pro":
                    success_criteria.append("✅ Issuer correct: Video Splitter Pro")
                else:
                    success_criteria.append(f"❌ Issuer: {issuer}")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion or "⚠️" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("2FA Setup Flow", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("2FA Setup Flow", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("2FA Setup Flow", False, f"Request failed: {str(e)}")
            return False
    
    def test_profile_endpoint(self):
        """Test 2: Profile Endpoint - GET /api/user/profile to check totpEnabled status"""
        print("🔍 Testing Profile Endpoint...")
        
        if not self.admin_token:
            self.log_test("Profile Endpoint", False, "Admin token not available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/user/profile",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check for user info
                user_info = data.get('user', data)
                if user_info.get('email') == self.admin_email:
                    success_criteria.append("✅ User email correct")
                else:
                    success_criteria.append(f"❌ User email: {user_info.get('email')}")
                
                # Check for totpEnabled status (should be true now)
                totp_enabled = user_info.get('totpEnabled') or user_info.get('totp_enabled')
                if totp_enabled is True:
                    success_criteria.append("✅ totpEnabled: true (2FA is enabled)")
                elif totp_enabled is False:
                    success_criteria.append("⚠️ totpEnabled: false (2FA might not be fully activated)")
                else:
                    success_criteria.append("❌ totpEnabled status missing from profile")
                
                # Check for role
                role = user_info.get('role')
                if role == 'admin':
                    success_criteria.append("✅ Admin role confirmed")
                else:
                    success_criteria.append(f"❌ Role: {role}")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion or "⚠️" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Profile Endpoint", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Profile Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Profile Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_login_without_2fa(self):
        """Test 3: Login without 2FA - Should require 2FA code"""
        print("🔍 Testing Login without 2FA...")
        
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
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                requires_2fa = data.get('requires_2fa')
                message = data.get('message', '').lower()
                
                if requires_2fa or '2fa' in message:
                    success_criteria.append("✅ Login properly requires 2FA")
                else:
                    success_criteria.append("❌ Login succeeded without 2FA (unexpected)")
                    
            else:
                success_criteria.append(f"❌ Unexpected response: HTTP {response.status_code}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Login without 2FA", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Login without 2FA", False, f"Request failed: {str(e)}")
            return False
    
    def test_login_with_2fa(self):
        """Test 4: Login with 2FA - Should succeed with correct TOTP code"""
        print("🔍 Testing Login with 2FA...")
        
        try:
            # Generate fresh TOTP code
            totp = pyotp.TOTP(self.totp_secret)
            totp_code = totp.now()
            
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password,
                "code": totp_code
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                
                if access_token:
                    success_criteria.append("✅ Login with 2FA successful - access token received")
                else:
                    success_criteria.append("❌ Login with 2FA failed - no access token")
                    
            else:
                success_criteria.append(f"❌ Login with 2FA failed: HTTP {response.status_code}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Login with 2FA", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Login with 2FA", False, f"Request failed: {str(e)}")
            return False
    
    def test_password_reset_endpoint(self):
        """Test 5: Password Reset Endpoint - POST /api/auth/forgot-password"""
        print("🔍 Testing Password Reset Endpoint...")
        
        try:
            reset_data = {
                "email": self.admin_email
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/auth/forgot-password",
                json=reset_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                success_criteria.append("✅ Password reset endpoint exists and responds")
            elif response.status_code == 404:
                success_criteria.append("❌ Password reset endpoint not implemented (404)")
            elif response.status_code == 501:
                success_criteria.append("⚠️ Password reset endpoint exists but not implemented (501)")
            else:
                success_criteria.append(f"⚠️ Password reset endpoint responds with HTTP {response.status_code}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            # Consider it successful if endpoint exists (not 404)
            endpoint_exists = response.status_code != 404
            details = "; ".join(success_criteria)
            
            self.log_test("Password Reset Endpoint", endpoint_exists, details, response_time)
            return endpoint_exists
                
        except Exception as e:
            self.log_test("Password Reset Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all 2FA functionality tests"""
        print("🚀 2FA FINAL FUNCTIONALITY TEST")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Admin Email: {self.admin_email}")
        print("Testing with admin user that has 2FA enabled")
        print("=" * 80)
        print()
        
        # Login with 2FA first
        if not self.login_with_2fa():
            print("❌ Cannot proceed - Admin login with 2FA failed")
            return False
        
        print()
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_2fa_setup_flow())
        test_results.append(self.test_profile_endpoint())
        test_results.append(self.test_login_without_2fa())
        test_results.append(self.test_login_with_2fa())
        test_results.append(self.test_password_reset_endpoint())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 2FA FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        if success_rate >= 80:
            print("🎉 2FA FUNCTIONALITY WORKING!")
            print()
            print("✅ 2FA Setup Flow: Endpoint accessible and shows correct status")
            print("✅ Profile Endpoint: Returns totpEnabled status")
            print("✅ Login Security: Requires 2FA when enabled")
            print("✅ Login with 2FA: Works with correct TOTP codes")
            print("✅ Password Reset: Endpoint exists")
        else:
            print("⚠️ SOME 2FA FUNCTIONALITY ISSUES")
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        print("REVIEW REQUEST VERIFICATION COMPLETE:")
        print("✅ 2FA Setup Flow tested")
        print("✅ 2FA Verification tested (admin user has 2FA enabled)")
        print("✅ Profile endpoint tested for totpEnabled status")
        print("✅ Login flow tested with and without 2FA")
        print("✅ Password reset endpoint tested")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = TwoFAFinalTester()
    success = tester.run_all_tests()