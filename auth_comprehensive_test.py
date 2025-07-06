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
        cls.job_ids = []
        
        # Create a small test video file
        cls.test_video_path = "/tmp/test_video.mp4"
        if not os.path.exists(cls.test_video_path):
            print(f"Creating test video file at {cls.test_video_path}")
            # Create a simple binary file instead of using ffmpeg
            with open(cls.test_video_path, 'wb') as f:
                # Write a minimal MP4 header (not a valid video but enough for testing)
                f.write(bytes([
                    0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70,
                    0x6D, 0x70, 0x34, 0x32, 0x00, 0x00, 0x00, 0x00,
                    0x6D, 0x70, 0x34, 0x32, 0x69, 0x73, 0x6F, 0x6D,
                    0x00, 0x00, 0x00, 0x08, 0x66, 0x72, 0x65, 0x65,
                    0x00, 0x00, 0x00, 0x08, 0x6D, 0x64, 0x61, 0x74
                ]))
                # Add some dummy data
                f.write(b'Test video content for authentication testing')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Clean up any remaining job data
        if cls.access_token:
            headers = {"Authorization": f"Bearer {cls.access_token}"}
            for job_id in cls.job_ids:
                try:
                    requests.delete(f"{API_URL}/cleanup/{job_id}", headers=headers)
                except Exception as e:
                    print(f"Error cleaning up job {job_id}: {e}")
    
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
    
    def test_06_protected_video_upload(self):
        """Test protected video upload endpoint"""
        print("\n=== Testing protected video upload endpoint ===")
        
        if not self.__class__.access_token:
            self.skipTest("No access token available")
        
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test with authentication
        with open(self.test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", headers=headers, files=files)
        
        self.assertEqual(response.status_code, 200, f"Upload failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIn('job_id', data, "Response missing job_id")
        self.assertIn('video_info', data, "Response missing video_info")
        self.assertIn('user_id', data, "Response missing user_id")
        
        # Store job ID for later tests
        job_id = data['job_id']
        self.__class__.job_ids.append(job_id)
        
        print(f"✅ Successfully uploaded video with authentication, job_id: {job_id}")
        print(f"User ID associated with upload: {data['user_id']}")
        
        # Test without authentication
        with open(self.test_video_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", files=files)
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ Upload endpoint correctly rejected request without authentication")
    
    def test_07_protected_job_status(self):
        """Test protected job status endpoint"""
        print("\n=== Testing protected job status endpoint ===")
        
        if not self.__class__.access_token or not self.__class__.job_ids:
            self.skipTest("No access token or job IDs available")
        
        job_id = self.__class__.job_ids[0]
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test with authentication
        response = requests.get(f"{API_URL}/job-status/{job_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Job status request failed: {response.text}")
        
        data = response.json()
        self.assertEqual(data['id'], job_id, "Job ID mismatch")
        self.assertIn('user_id', data, "Response missing user_id")
        
        print(f"✅ Successfully retrieved job status with authentication")
        print(f"Job status: {data['status']}")
        
        # Test without authentication
        response = requests.get(f"{API_URL}/job-status/{job_id}")
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ Job status endpoint correctly rejected request without authentication")
    
    def test_08_protected_split_video(self):
        """Test protected split video endpoint"""
        print("\n=== Testing protected split video endpoint ===")
        
        if not self.__class__.access_token or not self.__class__.job_ids:
            self.skipTest("No access token or job IDs available")
        
        job_id = self.__class__.job_ids[0]
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Configure time-based splitting
        split_config = {
            "method": "time_based",
            "time_points": [0, 2.5],  # Split at 2.5 seconds
            "preserve_quality": True,
            "output_format": "mp4",
            "subtitle_sync_offset": 0.0
        }
        
        # Test with authentication
        response = requests.post(
            f"{API_URL}/split-video/{job_id}", 
            headers=headers, 
            json=split_config
        )
        
        self.assertEqual(response.status_code, 200, f"Split request failed: {response.text}")
        
        print(f"✅ Successfully initiated video splitting with authentication")
        
        # Test without authentication
        response = requests.post(
            f"{API_URL}/split-video/{job_id}", 
            json=split_config
        )
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ Split video endpoint correctly rejected request without authentication")
        
        # Wait for processing to complete
        max_wait_time = 30  # seconds
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{API_URL}/job-status/{job_id}", headers=headers)
            
            if response.status_code != 200:
                break
                
            status_data = response.json()
            print(f"Job status: {status_data['status']}, progress: {status_data['progress']}%")
            
            if status_data['status'] == 'completed':
                completed = True
                break
            elif status_data['status'] == 'failed':
                print(f"Job failed: {status_data.get('error_message', 'Unknown error')}")
                break
            
            time.sleep(2)
        
        if completed:
            print(f"✅ Video splitting completed successfully")
        else:
            print(f"⚠️ Video splitting did not complete within {max_wait_time} seconds")
    
    def test_09_protected_video_stream(self):
        """Test protected video stream endpoint"""
        print("\n=== Testing protected video stream endpoint ===")
        
        if not self.__class__.access_token or not self.__class__.job_ids:
            self.skipTest("No access token or job IDs available")
        
        job_id = self.__class__.job_ids[0]
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test with authentication
        response = requests.get(f"{API_URL}/video-stream/{job_id}", headers=headers)
        
        # Should be 200 OK or 206 Partial Content
        self.assertTrue(
            response.status_code in [200, 206], 
            f"Video stream request failed with status {response.status_code}"
        )
        
        print(f"✅ Successfully accessed video stream with authentication")
        print(f"Content type: {response.headers.get('Content-Type')}")
        
        # Test without authentication
        response = requests.get(f"{API_URL}/video-stream/{job_id}")
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ Video stream endpoint correctly rejected request without authentication")
    
    def test_10_protected_cleanup(self):
        """Test protected cleanup endpoint"""
        print("\n=== Testing protected cleanup endpoint ===")
        
        if not self.__class__.access_token or not self.__class__.job_ids:
            self.skipTest("No access token or job IDs available")
        
        # Use the first job for cleanup test
        job_id = self.__class__.job_ids[0]
        headers = {"Authorization": f"Bearer {self.__class__.access_token}"}
        
        # Test without authentication
        response = requests.delete(f"{API_URL}/cleanup/{job_id}")
        
        self.assertEqual(response.status_code, 403, f"Expected 403 Forbidden, got {response.status_code}")
        
        print(f"✅ Cleanup endpoint correctly rejected request without authentication")
        
        # Test with authentication
        response = requests.delete(f"{API_URL}/cleanup/{job_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Cleanup request failed: {response.text}")
        
        print(f"✅ Successfully cleaned up job with authentication")
        
        # Remove from job_ids list to avoid double cleanup
        if job_id in self.__class__.job_ids:
            self.__class__.job_ids.remove(job_id)
        
        # Verify job no longer exists
        response = requests.get(f"{API_URL}/job-status/{job_id}", headers=headers)
        
        self.assertEqual(response.status_code, 404, f"Expected 404 Not Found, got {response.status_code}")
        
        print(f"✅ Job successfully deleted")

if __name__ == "__main__":
    unittest.main(verbosity=2)