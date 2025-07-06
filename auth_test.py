#!/usr/bin/env python3
import requests
import json
import unittest
import time
from pprint import pprint

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# If not found, use the default URL
if 'BACKEND_URL' not in locals():
    BACKEND_URL = "http://localhost:8001"

# Ensure the URL has no trailing slash
BACKEND_URL = BACKEND_URL.rstrip('/')
print(f"Using backend URL: {BACKEND_URL}")

class AuthenticationTest(unittest.TestCase):
    """Test suite for the Video Splitter Authentication API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.admin_credentials = {
            "username": "tadmin",
            "password": "@DefaultUser1234"
        }
        cls.access_token = None
        cls.refresh_token = None
    
    def test_01_login_with_valid_credentials(self):
        """Test login with valid admin credentials"""
        print("\n=== Testing login with valid admin credentials ===")
        
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json=self.admin_credentials
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data, "Response missing access_token")
        self.assertIn('refresh_token', data, "Response missing refresh_token")
        self.assertIn('user', data, "Response missing user data")
        
        # Store tokens for later tests
        self.__class__.access_token = data['access_token']
        self.__class__.refresh_token = data['refresh_token']
        
        # Verify user data
        user = data['user']
        self.assertEqual(user['username'], self.admin_credentials['username'], "Username mismatch")
        self.assertEqual(user['role'], "admin", "Role should be admin")
        self.assertTrue(user['is_verified'], "Admin should be verified")
        
        print(f"✅ Successfully logged in as admin user")
        print(f"User details: {user['username']} (role: {user['role']})")
        
        return data
    
    def test_02_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        print("\n=== Testing login with invalid credentials ===")
        
        invalid_credentials = {
            "username": "tadmin",
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json=invalid_credentials
        )
        
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        
        print(f"✅ Login correctly rejected invalid credentials with status {response.status_code}")
        print(f"Error message: {response.json().get('detail')}")
    
    def test_03_get_current_user(self):
        """Test getting current user info with valid token"""
        print("\n=== Testing GET /auth/me endpoint ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get user info: {response.text}")
        
        user_data = response.json()
        self.assertEqual(user_data['username'], self.admin_credentials['username'], "Username mismatch")
        self.assertEqual(user_data['role'], "admin", "Role should be admin")
        
        print(f"✅ Successfully retrieved current user info")
        print(f"User details: {user_data['username']} (role: {user_data['role']})")
    
    def test_04_get_current_user_without_token(self):
        """Test getting current user info without token"""
        print("\n=== Testing GET /auth/me without token ===")
        
        response = requests.get(f"{BACKEND_URL}/auth/me")
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ /auth/me correctly rejected request without token with status {response.status_code}")
        print(f"Error message: {response.json().get('detail')}")
    
    def test_05_get_current_user_with_invalid_token(self):
        """Test getting current user info with invalid token"""
        print("\n=== Testing GET /auth/me with invalid token ===")
        
        headers = {"Authorization": "Bearer invalidtoken12345"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        
        print(f"✅ /auth/me correctly rejected invalid token with status {response.status_code}")
        print(f"Error message: {response.json().get('detail')}")
    
    def test_06_refresh_token(self):
        """Test refreshing JWT token"""
        print("\n=== Testing token refresh ===")
        
        if not self.__class__.refresh_token:
            self.skipTest("No refresh token available")
        
        refresh_data = {
            "refresh_token": self.__class__.refresh_token
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/refresh", json=refresh_data)
        
        self.assertEqual(response.status_code, 200, f"Token refresh failed: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data, "Response missing access_token")
        self.assertIn('refresh_token', data, "Response missing refresh_token")
        
        # Update tokens for later tests
        self.__class__.access_token = data['access_token']
        self.__class__.refresh_token = data['refresh_token']
        
        print(f"✅ Successfully refreshed tokens")
        
        # Verify new token works
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        verify_response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        
        self.assertEqual(verify_response.status_code, 200, "New token doesn't work")
        
        print(f"✅ New token verified and working")
    
    def test_07_refresh_with_invalid_token(self):
        """Test refreshing with invalid refresh token"""
        print("\n=== Testing token refresh with invalid token ===")
        
        refresh_data = {
            "refresh_token": "invalid_refresh_token_12345"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/refresh", json=refresh_data)
        
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        
        print(f"✅ Token refresh correctly rejected invalid token with status {response.status_code}")
        print(f"Error message: {response.json().get('detail')}")
    
    def test_08_admin_list_users(self):
        """Test admin endpoint to list all users"""
        print("\n=== Testing admin endpoint to list users ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        response = requests.get(f"{BACKEND_URL}/admin/users", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to list users: {response.text}")
        
        users = response.json()
        self.assertIsInstance(users, list, "Expected a list of users")
        self.assertTrue(len(users) > 0, "User list should not be empty")
        
        # Verify admin user is in the list
        admin_found = False
        for user in users:
            if user['username'] == self.admin_credentials['username']:
                admin_found = True
                break
        
        self.assertTrue(admin_found, "Admin user not found in user list")
        
        print(f"✅ Successfully retrieved user list with {len(users)} users")
        print(f"First user: {users[0]['username']} (role: {users[0]['role']})")
    
    def test_09_admin_get_settings(self):
        """Test admin endpoint to get system settings"""
        print("\n=== Testing admin endpoint to get system settings ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        response = requests.get(f"{BACKEND_URL}/admin/settings", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get settings: {response.text}")
        
        settings = response.json()
        self.assertIn('allow_user_registration', settings, "Settings missing allow_user_registration")
        self.assertIn('max_failed_login_attempts', settings, "Settings missing max_failed_login_attempts")
        self.assertIn('account_lockout_duration', settings, "Settings missing account_lockout_duration")
        
        print(f"✅ Successfully retrieved system settings")
        print(f"Settings: {json.dumps(settings, indent=2)}")
    
    def test_10_admin_endpoint_without_admin_role(self):
        """Test accessing admin endpoint without admin role (simulated)"""
        print("\n=== Testing admin endpoint access without admin role ===")
        
        # Since we only have admin user, we'll simulate a non-admin token
        # by modifying the Authorization header to be invalid
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtldXNlciIsInVzZXJuYW1lIjoiZmFrZXVzZXIiLCJyb2xlIjoidXNlciIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3MTk5MjQwMDB9.invalid_signature"}
        
        response = requests.get(f"{BACKEND_URL}/admin/users", headers=headers)
        
        # Should be 401 Unauthorized since the token is invalid
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        
        print(f"✅ Admin endpoint correctly rejected invalid token with status {response.status_code}")
        print(f"Error message: {response.json().get('detail')}")
    
    def test_11_protected_api_with_valid_token(self):
        """Test accessing protected API endpoint with valid token"""
        print("\n=== Testing protected API endpoint with valid token ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        # Test job-status endpoint (should require auth)
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Use a non-existent job ID to test authentication (not job existence)
        response = requests.get(f"{BACKEND_URL}/api/job-status/nonexistent-job", headers=headers)
        
        # Should be 404 Not Found (job doesn't exist) but not 401 Unauthorized
        self.assertEqual(response.status_code, 404, f"Expected 404 Not Found, got {response.status_code}")
        
        print(f"✅ Protected API endpoint correctly authenticated request")
        print(f"Response: {response.json().get('detail')}")
    
    def test_12_protected_api_without_token(self):
        """Test accessing protected API endpoint without token"""
        print("\n=== Testing protected API endpoint without token ===")
        
        # Test job-status endpoint without auth
        response = requests.get(f"{BACKEND_URL}/api/job-status/nonexistent-job")
        
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        
        print(f"✅ Protected API endpoint correctly rejected request without token")
        print(f"Error message: {response.json().get('detail')}")

if __name__ == "__main__":
    unittest.main(verbosity=2)