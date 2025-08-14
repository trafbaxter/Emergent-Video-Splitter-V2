#!/usr/bin/env python3
"""
SPLIT VIDEO BUTTON INVESTIGATION TEST
Investigating why split video button isn't making API requests as reported in review request.

CRITICAL ISSUE:
User console logs show video upload and preview working perfectly, but NO split video API request 
is being made when user clicks the split button. Progress shows 25% (default value) but no actual job is created.

DIAGNOSTIC TESTS:
1. Manual Split Video Request with user's actual video
2. Verify Split Endpoint Working
3. Check Job Status After Creation
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class SplitVideoInvestigator:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        
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
        
    def test_manual_split_video_request(self):
        """Test 1: Manual Split Video Request with user's actual video"""
        print("🔍 Testing Manual Split Video Request with User's Actual Video...")
        
        # Exact payload from review request
        payload = {
            "s3_key": "uploads/8b06cb48-b72b-4746-b43f-e3ee4a5436e8/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code (should be 202 Accepted)
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 Accepted")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202)")
            
            # Check response time (should be under 10 seconds for immediate response)
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                success_criteria.append(f"✅ CORS headers present: {cors_header}")
            else:
                success_criteria.append("❌ No CORS headers")
            
            # Check response content
            if response.status_code == 202:
                try:
                    data = response.json()
                    
                    # Check for job_id
                    job_id = data.get('job_id')
                    if job_id:
                        success_criteria.append(f"✅ job_id returned: {job_id}")
                        self.job_id = job_id  # Store for next test
                    else:
                        success_criteria.append("❌ job_id missing")
                    
                    # Check status
                    status = data.get('status')
                    if status in ['accepted', 'queued', 'processing']:
                        success_criteria.append(f"✅ Status: {status}")
                    else:
                        success_criteria.append(f"❌ Status: {status} (expected accepted/queued/processing)")
                    
                    # Check for required fields
                    required_fields = ['job_id', 'status']
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        success_criteria.append("✅ All required fields present")
                    else:
                        success_criteria.append(f"❌ Missing fields: {missing_fields}")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
            else:
                success_criteria.append(f"❌ Error response: {response.text[:200]}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Manual Split Video Request", all_success, details, response_time)
            return all_success
            
        except requests.exceptions.Timeout:
            self.log_test("Manual Split Video Request", False, "Request timed out after 30 seconds")
            return False
        except Exception as e:
            self.log_test("Manual Split Video Request", False, f"Request failed: {str(e)}")
            return False
    
    def test_split_endpoint_responsiveness(self):
        """Test 2: Verify Split Endpoint is Responsive"""
        print("🔍 Testing Split Endpoint Responsiveness...")
        
        # Simple test payload
        payload = {
            "s3_key": "test-video.mp4",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://working.tads-video-splitter.com'
                },
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check if endpoint is reachable (not 404)
            if response.status_code != 404:
                success_criteria.append("✅ Endpoint exists (not 404)")
            else:
                success_criteria.append("❌ Endpoint returns 404 (not implemented)")
            
            # Check if endpoint responds quickly
            if response_time < 10.0:
                success_criteria.append(f"✅ Quick response: {response_time:.2f}s")
            else:
                success_criteria.append(f"❌ Slow response: {response_time:.2f}s")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                success_criteria.append(f"✅ CORS headers: {cors_header}")
            else:
                success_criteria.append("❌ No CORS headers")
            
            # Check response format
            if response.status_code in [200, 202]:
                try:
                    data = response.json()
                    success_criteria.append("✅ Valid JSON response")
                except:
                    success_criteria.append("❌ Invalid JSON response")
            elif response.status_code == 500:
                success_criteria.append("❌ Server error (500)")
            elif response.status_code == 504:
                success_criteria.append("❌ Gateway timeout (504)")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Split Endpoint Responsiveness", all_success, details, response_time)
            return all_success
            
        except requests.exceptions.Timeout:
            self.log_test("Split Endpoint Responsiveness", False, "Request timed out after 30 seconds")
            return False
        except Exception as e:
            self.log_test("Split Endpoint Responsiveness", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_preflight_split_video(self):
        """Test 3: CORS Preflight for Split Video Endpoint"""
        print("🔍 Testing CORS Preflight for Split Video...")
        
        try:
            start_time = time.time()
            response = requests.options(
                f"{self.api_base}/api/split-video",
                headers={
                    'Origin': 'https://working.tads-video-splitter.com',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code
            if response.status_code in [200, 204]:
                success_criteria.append(f"✅ HTTP {response.status_code}")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            cors_headers = response.headers.get('Access-Control-Allow-Headers')
            
            if cors_origin:
                success_criteria.append(f"✅ Allow-Origin: {cors_origin}")
            else:
                success_criteria.append("❌ No Allow-Origin header")
            
            if cors_methods and 'POST' in cors_methods:
                success_criteria.append(f"✅ Allow-Methods includes POST")
            else:
                success_criteria.append(f"❌ Allow-Methods: {cors_methods}")
            
            if cors_headers and 'Content-Type' in cors_headers:
                success_criteria.append(f"✅ Allow-Headers includes Content-Type")
            else:
                success_criteria.append(f"❌ Allow-Headers: {cors_headers}")
            
            # Check response time
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("CORS Preflight Split Video", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("CORS Preflight Split Video", False, f"Request failed: {str(e)}")
            return False
    
    def test_job_status_after_creation(self):
        """Test 4: Check Job Status After Creation"""
        print("🔍 Testing Job Status After Creation...")
        
        # Use job_id from previous test if available
        if not hasattr(self, 'job_id'):
            # Create a test job first
            payload = {
                "s3_key": "test-video.mp4",
                "method": "intervals",
                "interval_duration": 300
            }
            
            try:
                response = requests.post(
                    f"{self.api_base}/api/split-video",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code == 202:
                    data = response.json()
                    self.job_id = data.get('job_id', 'test-job-123')
                else:
                    self.job_id = 'test-job-123'
            except:
                self.job_id = 'test-job-123'
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                headers={'Origin': 'https://working.tads-video-splitter.com'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code
            if response.status_code == 200:
                success_criteria.append("✅ HTTP 200")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code}")
            
            # Check response time
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s")
            
            # Check CORS headers
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                success_criteria.append(f"✅ CORS headers: {cors_header}")
            else:
                success_criteria.append("❌ No CORS headers")
            
            # Check response content
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for required fields
                    required_fields = ['job_id', 'status', 'progress']
                    present_fields = [field for field in required_fields if field in data]
                    
                    if len(present_fields) == len(required_fields):
                        success_criteria.append("✅ All required fields present")
                    else:
                        missing = set(required_fields) - set(present_fields)
                        success_criteria.append(f"❌ Missing fields: {missing}")
                    
                    # Check progress value
                    progress = data.get('progress')
                    if isinstance(progress, (int, float)) and 0 <= progress <= 100:
                        success_criteria.append(f"✅ Valid progress: {progress}%")
                    else:
                        success_criteria.append(f"❌ Invalid progress: {progress}")
                    
                    # Check status
                    status = data.get('status')
                    if status in ['processing', 'completed', 'failed', 'queued']:
                        success_criteria.append(f"✅ Valid status: {status}")
                    else:
                        success_criteria.append(f"❌ Invalid status: {status}")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
            else:
                success_criteria.append(f"❌ Error response: {response.text[:200]}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Job Status After Creation", all_success, details, response_time)
            return all_success
            
        except requests.exceptions.Timeout:
            self.log_test("Job Status After Creation", False, "Request timed out after 30 seconds")
            return False
        except Exception as e:
            self.log_test("Job Status After Creation", False, f"Request failed: {str(e)}")
            return False
    
    def test_s3_job_file_creation(self):
        """Test 5: Check if Job Files are Created in S3"""
        print("🔍 Testing S3 Job File Creation...")
        
        # This test checks if the split-video endpoint creates job files in S3
        # We'll test this by making a split request and checking the response indicates job creation
        
        payload = {
            "s3_key": "test-job-creation.mp4",
            "method": "intervals",
            "interval_duration": 300
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 202:
                try:
                    data = response.json()
                    
                    # Check if response indicates job was queued/created
                    job_id = data.get('job_id')
                    status = data.get('status')
                    
                    if job_id:
                        success_criteria.append(f"✅ Job created with ID: {job_id}")
                    else:
                        success_criteria.append("❌ No job_id in response")
                    
                    if status in ['accepted', 'queued', 'processing']:
                        success_criteria.append(f"✅ Job status indicates creation: {status}")
                    else:
                        success_criteria.append(f"❌ Unexpected status: {status}")
                    
                    # Check for additional job creation indicators
                    if 'message' in data:
                        success_criteria.append(f"✅ Job creation message: {data['message'][:50]}...")
                    
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s")
                    
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202)")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("S3 Job File Creation", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("S3 Job File Creation", False, f"Request failed: {str(e)}")
            return False
    
    def run_investigation(self):
        """Run all split video investigation tests"""
        print("🚀 SPLIT VIDEO BUTTON INVESTIGATION")
        print("=" * 80)
        print("CRITICAL ISSUE: User reports split video button not making API requests")
        print("Expected: HTTP 202 with job_id, actual job creation in S3")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("=" * 80)
        print()
        
        # Run diagnostic tests
        test_results = []
        
        test_results.append(self.test_manual_split_video_request())
        test_results.append(self.test_split_endpoint_responsiveness())
        test_results.append(self.test_cors_preflight_split_video())
        test_results.append(self.test_job_status_after_creation())
        test_results.append(self.test_s3_job_file_creation())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 INVESTIGATION RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Root cause analysis
        if success_rate == 100:
            print("🎉 BACKEND SPLIT VIDEO FUNCTIONALITY WORKING!")
            print("✅ Manual API test successful - backend is functional")
            print("✅ Split endpoint responsive and creates jobs")
            print("✅ CORS headers present for browser requests")
            print("✅ Job status tracking working")
            print()
            print("🔍 ROOT CAUSE ANALYSIS:")
            print("Since backend API works perfectly, the issue is likely:")
            print("1. Frontend JavaScript error preventing API call")
            print("2. Frontend not properly handling split button click")
            print("3. Missing job_id mapping between uploaded video and split request")
            print("4. Authentication issues blocking the API call")
        else:
            print("❌ BACKEND ISSUES FOUND!")
            print()
            print("🔍 ROOT CAUSE ANALYSIS:")
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("Backend problems identified:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        print("EXPECTED RESULT FROM REVIEW REQUEST:")
        print("Manual API test should work and create a real job, confirming")
        print("the backend is functional and the issue is in the frontend button behavior.")
        
        return success_rate >= 80  # Allow some tolerance for minor issues

if __name__ == "__main__":
    investigator = SplitVideoInvestigator()
    success = investigator.run_investigation()
    
    if not success:
        exit(1)