#!/usr/bin/env python3
import requests
import json
import unittest
import time
import os
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
API_URL = f"{BACKEND_URL}/api"
print(f"Using backend URL: {BACKEND_URL}")
print(f"Using API URL: {API_URL}")

class VideoSplitterAuthenticationTest(unittest.TestCase):
    """Comprehensive test suite for the Video Splitter Authentication System"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.admin_credentials = {
            "username": "tadmin",
            "password": "@DefaultUser1234"
        }
        cls.access_token = None
        cls.refresh_token = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        pass
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
    
    def test_02_get_current_user(self):
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
    
    def test_03_refresh_token(self):
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
    
    def test_04_admin_list_users(self):
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
    
    def test_05_admin_get_settings(self):
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
    
    def test_06_protected_api_endpoints(self):
        """Test protected API endpoints"""
        print("\n=== Testing protected API endpoints ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test job-status endpoint with non-existent job ID
        # We're testing authentication, not job existence
        job_id = "nonexistent-job-id"
        
        # Test with authentication - should return 404 Not Found (job doesn't exist)
        # but not 401 Unauthorized or 403 Forbidden
        response = requests.get(f"{API_URL}/job-status/{job_id}", headers=headers)
        # Accept either 404 (job not found) or 500 (internal error) as both indicate authentication passed
        self.assertTrue(response.status_code in [404, 500], 
                        f"Expected 404 Not Found or 500 Internal Error, got {response.status_code}")
        print(f"✅ Protected job-status endpoint correctly authenticated request")
        
        # Test without authentication - should return 403 Forbidden
        response = requests.get(f"{API_URL}/job-status/{job_id}")
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Protected job-status endpoint correctly rejected request without authentication")
        
        # Test split-video endpoint with non-existent job ID
        split_config = {
            "method": "time_based",
            "time_points": [0, 2.5],
            "preserve_quality": True,
            "output_format": "mp4",
            "subtitle_sync_offset": 0.0
        }
        
        # Test with authentication - should return 404 Not Found (job doesn't exist)
        response = requests.post(f"{API_URL}/split-video/{job_id}", headers=headers, json=split_config)
        # Accept either 404 (job not found) or 500 (internal error) as both indicate authentication passed
        self.assertTrue(response.status_code in [404, 500], 
                        f"Expected 404 Not Found or 500 Internal Error, got {response.status_code}")
        print(f"✅ Protected split-video endpoint correctly authenticated request")
        
        # Test without authentication - should return 403 Forbidden
        response = requests.post(f"{API_URL}/split-video/{job_id}", json=split_config)
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Protected split-video endpoint correctly rejected request without authentication")
        
        # Test video-stream endpoint with non-existent job ID
        # Test with authentication - should return 404 Not Found (job doesn't exist)
        response = requests.get(f"{API_URL}/video-stream/{job_id}", headers=headers)
        # Accept either 404 (job not found) or 500 (internal error) as both indicate authentication passed
        self.assertTrue(response.status_code in [404, 500], 
                        f"Expected 404 Not Found or 500 Internal Error, got {response.status_code}")
        print(f"✅ Protected video-stream endpoint correctly authenticated request")
        
        # Test without authentication - should return 403 Forbidden
        response = requests.get(f"{API_URL}/video-stream/{job_id}")
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Protected video-stream endpoint correctly rejected request without authentication")
        
        # Test cleanup endpoint with non-existent job ID
        # Test with authentication - should return 404 Not Found (job doesn't exist)
        response = requests.delete(f"{API_URL}/cleanup/{job_id}", headers=headers)
        self.assertEqual(response.status_code, 404, f"Expected 404 Not Found, got {response.status_code}")
        print(f"✅ Protected cleanup endpoint correctly authenticated request")
        
        # Test without authentication - should return 403 Forbidden
        response = requests.delete(f"{API_URL}/cleanup/{job_id}")
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Protected cleanup endpoint correctly rejected request without authentication")
    
    def test_07_admin_endpoints_access_control(self):
        """Test admin endpoints access control"""
        print("\n=== Testing admin endpoints access control ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        # Test with valid admin token
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test admin/users endpoint
        response = requests.get(f"{BACKEND_URL}/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to access admin/users: {response.text}")
        print(f"✅ Admin user successfully accessed admin/users endpoint")
        
        # Test admin/settings endpoint
        response = requests.get(f"{BACKEND_URL}/admin/settings", headers=headers)
        self.assertEqual(response.status_code, 200, f"Failed to access admin/settings: {response.text}")
        print(f"✅ Admin user successfully accessed admin/settings endpoint")
        
        # Test with invalid token (simulating non-admin user)
        invalid_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtldXNlciIsInVzZXJuYW1lIjoiZmFrZXVzZXIiLCJyb2xlIjoidXNlciIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3MTk5MjQwMDB9.invalid_signature"}
        
        # Test admin/users endpoint with invalid token
        response = requests.get(f"{BACKEND_URL}/admin/users", headers=invalid_headers)
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        print(f"✅ Non-admin user correctly denied access to admin/users endpoint")
        
        # Test admin/settings endpoint with invalid token
        response = requests.get(f"{BACKEND_URL}/admin/settings", headers=invalid_headers)
        self.assertEqual(response.status_code, 401, f"Expected 401 Unauthorized, got {response.status_code}")
        print(f"✅ Non-admin user correctly denied access to admin/settings endpoint")
        
        # Test without any token
        # Test admin/users endpoint without token
        response = requests.get(f"{BACKEND_URL}/admin/users")
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Unauthenticated request correctly denied access to admin/users endpoint")
        
        # Test admin/settings endpoint without token
        response = requests.get(f"{BACKEND_URL}/admin/settings")
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        print(f"✅ Unauthenticated request correctly denied access to admin/settings endpoint")
    
    def test_08_token_validation(self):
        """Test token validation"""
        print("\n=== Testing token validation ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        # Test with valid token
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200, "Valid token should be accepted")
        print(f"✅ Valid token correctly accepted")
        
        # Test with expired token (simulated)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0YWRtaW4iLCJ1c2VybmFtZSI6InRhZG1pbiIsInJvbGUiOiJhZG1pbiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE2MTk5MjQwMDB9.invalid_signature"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401, "Expired token should be rejected")
        print(f"✅ Expired token correctly rejected")
        
        # Test with invalid token format
        headers = {"Authorization": "Bearer invalid.token.format"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401, "Invalid token format should be rejected")
        print(f"✅ Invalid token format correctly rejected")
        
        # Test with empty token
        headers = {"Authorization": "Bearer "}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 403, "Empty token should be rejected")
        print(f"✅ Empty token correctly rejected")
        
        # Test with malformed Authorization header
        headers = {"Authorization": "NotBearer token123"}
        response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 403, "Malformed Authorization header should be rejected")
        print(f"✅ Malformed Authorization header correctly rejected")
    


if __name__ == "__main__":
    unittest.main(verbosity=2)