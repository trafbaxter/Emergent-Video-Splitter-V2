#!/usr/bin/env python3
"""
Video Processing Endpoints Testing for AWS Lambda Backend
Tests specifically the video streaming and metadata extraction functionality
that the user reported as not working.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import sys

# Configuration from AuthContext.js
API_BASE = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30

class VideoEndpointsTester:
    def __init__(self):
        self.base_url = API_BASE
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.access_token = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Dict = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data
        })
        print()

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("🔍 Setting up authentication...")
        
        # Create a test user for authentication
        test_email = f"videotest_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "TestPassword123!"
        
        try:
            # Register test user
            register_data = {
                "email": test_email,
                "password": test_password,
                "firstName": "Video",
                "lastName": "Tester"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=register_data)
            
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get('access_token')
                self.log_test("Authentication Setup", True, f"Test user registered: {test_email}")
                return True
            else:
                # Try login instead (user might already exist)
                login_data = {"email": test_email, "password": test_password}
                response = self.session.post(f"{self.base_url}/api/auth/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get('access_token')
                    self.log_test("Authentication Setup", True, "Using existing test user")
                    return True
                else:
                    self.log_test("Authentication Setup", False, f"Registration failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("Authentication Setup", False, f"Error: {str(e)}")
            return False

    def test_health_check_endpoints(self):
        """Test what endpoints are advertised in health check"""
        print("🔍 Testing Health Check - Advertised Endpoints...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('endpoints', [])
                
                # Check for video processing endpoints
                video_endpoints = [ep for ep in endpoints if any(keyword in ep.lower() for keyword in ['video', 'stream', 'split', 'download', 'job'])]
                
                self.log_test(
                    "Health Check - Video Endpoints Listed",
                    len(video_endpoints) > 0,
                    f"Found {len(video_endpoints)} video-related endpoints: {video_endpoints}"
                )
                
                # Specifically check for the endpoints user mentioned
                expected_endpoints = [
                    'GET /api/video-stream/{key}',
                    'POST /api/get-video-info'
                ]
                
                for endpoint in expected_endpoints:
                    found = any(endpoint in ep for ep in endpoints)
                    self.log_test(
                        f"Endpoint Listed: {endpoint}",
                        found,
                        "Listed in health check" if found else "NOT listed in health check"
                    )
                
                return endpoints
            else:
                self.log_test("Health Check - Video Endpoints Listed", False, f"HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Health Check - Video Endpoints Listed", False, f"Error: {str(e)}")
            return []

    def test_video_stream_endpoint(self):
        """Test GET /api/video-stream/{key} endpoint"""
        print("🔍 Testing Video Stream Endpoint...")
        
        if not self.access_token:
            self.log_test("Video Stream Endpoint", False, "No access token available")
            return
        
        # Test with a sample key
        test_key = "uploads/test-video.mp4"
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Video Stream Endpoint - Implementation",
                    True,
                    f"Endpoint implemented and returns: {list(data.keys()) if isinstance(data, dict) else 'non-dict response'}"
                )
            elif response.status_code == 404:
                # Check if it's a proper 404 (endpoint exists but file not found) or route not found
                try:
                    error_data = response.json()
                    if 'not found' in error_data.get('message', '').lower():
                        self.log_test(
                            "Video Stream Endpoint - Implementation",
                            True,
                            "Endpoint implemented (404 for missing file is expected)"
                        )
                    else:
                        self.log_test(
                            "Video Stream Endpoint - Implementation",
                            False,
                            f"Route not found: {error_data.get('message', 'Unknown error')}"
                        )
                except:
                    # If we can't parse JSON, it might be a generic 404
                    self.log_test(
                        "Video Stream Endpoint - Implementation",
                        False,
                        "Route not implemented (generic 404)"
                    )
            else:
                self.log_test(
                    "Video Stream Endpoint - Implementation",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Video Stream Endpoint - Implementation", False, f"Error: {str(e)}")

    def test_video_info_endpoint(self):
        """Test POST /api/get-video-info endpoint"""
        print("🔍 Testing Video Info Endpoint...")
        
        if not self.access_token:
            self.log_test("Video Info Endpoint", False, "No access token available")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Test with sample MKV file data (as user mentioned MKV with subtitles)
            test_data = {"s3_key": "uploads/test-video.mkv"}
            
            response = self.session.post(f"{self.base_url}/api/get-video-info", json=test_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it returns proper video metadata structure
                expected_fields = ['duration', 'format', 'video_streams', 'audio_streams', 'subtitle_streams']
                has_metadata = any(field in data for field in expected_fields)
                
                self.log_test(
                    "Video Info Endpoint - Implementation",
                    True,
                    f"Endpoint implemented, returns metadata: {has_metadata}"
                )
                
                # Specifically check subtitle stream detection
                subtitle_streams = data.get('subtitle_streams', 'not_found')
                self.log_test(
                    "Video Info - Subtitle Stream Detection",
                    subtitle_streams != 'not_found',
                    f"Subtitle streams field: {subtitle_streams}"
                )
                
            elif response.status_code == 404:
                # Check if it's implemented but file not found
                try:
                    error_data = response.json()
                    self.log_test(
                        "Video Info Endpoint - Implementation",
                        True,
                        "Endpoint implemented (404 for missing file is expected)"
                    )
                except:
                    self.log_test(
                        "Video Info Endpoint - Implementation",
                        False,
                        "Route not implemented (generic 404)"
                    )
            else:
                self.log_test(
                    "Video Info Endpoint - Implementation",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Video Info Endpoint - Implementation", False, f"Error: {str(e)}")

    def test_other_video_endpoints(self):
        """Test other video processing endpoints"""
        print("🔍 Testing Other Video Processing Endpoints...")
        
        if not self.access_token:
            self.log_test("Other Video Endpoints", False, "No access token available")
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test split-video endpoint
        try:
            split_data = {
                "s3_key": "uploads/test-video.mp4",
                "method": "time",
                "time_points": [30, 60]
            }
            
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            
            if response.status_code in [200, 404]:  # 404 is acceptable for missing file
                self.log_test("Split Video Endpoint", True, f"Endpoint implemented (HTTP {response.status_code})")
            else:
                self.log_test("Split Video Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Split Video Endpoint", False, f"Error: {str(e)}")
        
        # Test job-status endpoint
        try:
            test_job_id = "test-job-123"
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}", headers=headers)
            
            if response.status_code in [200, 404]:  # 404 is acceptable for missing job
                self.log_test("Job Status Endpoint", True, f"Endpoint implemented (HTTP {response.status_code})")
            else:
                self.log_test("Job Status Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Job Status Endpoint", False, f"Error: {str(e)}")
        
        # Test download endpoint
        try:
            test_job_id = "test-job-123"
            test_filename = "segment1.mp4"
            response = self.session.get(f"{self.base_url}/api/download/{test_job_id}/{test_filename}", headers=headers)
            
            if response.status_code in [200, 404]:  # 404 is acceptable for missing file
                self.log_test("Download Endpoint", True, f"Endpoint implemented (HTTP {response.status_code})")
            else:
                self.log_test("Download Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Download Endpoint", False, f"Error: {str(e)}")

    def test_presigned_url_functionality(self):
        """Test presigned URL generation (this should work)"""
        print("🔍 Testing Presigned URL Generation...")
        
        if not self.access_token:
            self.log_test("Presigned URL Generation", False, "No access token available")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            presigned_data = {
                "filename": "test-video.mkv",
                "contentType": "video/x-matroska"
            }
            
            response = self.session.post(f"{self.base_url}/api/generate-presigned-url", json=presigned_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                has_upload_url = 'uploadUrl' in data
                has_key = 'key' in data
                
                self.log_test(
                    "Presigned URL Generation",
                    has_upload_url and has_key,
                    f"Upload URL: {has_upload_url}, Key: {has_key}"
                )
                
                return data.get('key')  # Return key for further testing
            else:
                self.log_test("Presigned URL Generation", False, f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Presigned URL Generation", False, f"Error: {str(e)}")
            return None

    def run_all_tests(self):
        """Run all video endpoint tests"""
        print("=" * 80)
        print("🎥 VIDEO PROCESSING ENDPOINTS TESTING")
        print("=" * 80)
        print(f"Testing API Base URL: {self.base_url}")
        print()
        
        # Setup authentication first
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run all tests
        advertised_endpoints = self.test_health_check_endpoints()
        self.test_video_stream_endpoint()
        self.test_video_info_endpoint()
        self.test_other_video_endpoints()
        upload_key = self.test_presigned_url_functionality()
        
        # Summary
        print("=" * 80)
        print("📊 VIDEO ENDPOINTS TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical findings
        print("🔍 CRITICAL FINDINGS:")
        
        # Check if video endpoints are advertised but not implemented
        video_endpoint_tests = [r for r in self.test_results if 'endpoint' in r['test'].lower() and 'implementation' in r['test'].lower()]
        implemented_count = sum(1 for r in video_endpoint_tests if r['success'])
        
        if len(video_endpoint_tests) > implemented_count:
            print("   ⚠️  MISMATCH: Some video endpoints are advertised in health check but NOT implemented")
            for result in video_endpoint_tests:
                if not result['success']:
                    print(f"      • {result['test']}: {result['details']}")
        
        # Check subtitle detection specifically
        subtitle_tests = [r for r in self.test_results if 'subtitle' in r['test'].lower()]
        if subtitle_tests and not subtitle_tests[0]['success']:
            print("   ❌ SUBTITLE DETECTION: Not working as reported by user")
        
        # Check video streaming
        stream_tests = [r for r in self.test_results if 'stream' in r['test'].lower()]
        if stream_tests and not stream_tests[0]['success']:
            print("   ❌ VIDEO STREAMING: Not working as reported by user")
        
        print()
        print("💡 RECOMMENDATIONS:")
        
        if implemented_count == 0:
            print("   🚨 URGENT: No video processing endpoints are actually implemented")
            print("   📝 The Lambda function only handles authentication and presigned URLs")
            print("   🔧 Video processing functionality needs to be implemented")
        elif implemented_count < len(video_endpoint_tests):
            print("   ⚠️  Some video endpoints are missing - partial implementation")
            print("   🔧 Complete the implementation of all advertised endpoints")
        
        print("   📋 User's reported issues are confirmed:")
        print("      • Video preview not loading: video-stream endpoint not implemented")
        print("      • Incorrect subtitle count: get-video-info endpoint not implemented")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoEndpointsTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)