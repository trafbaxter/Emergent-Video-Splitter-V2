#!/usr/bin/env python3
"""
SQS-BASED VIDEO PROCESSING SYSTEM TEST
Tests the complete SQS-based video processing system with the function signature fix for FFmpeg Lambda.
Focus: Testing if the Lambda error "split_video() missing 1 required positional argument" is resolved.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class SQSVideoProcessingTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # Test data as specified in review request
        self.test_payload = {
            "s3_key": "test-fixed-ffmpeg.mp4",
            "method": "intervals", 
            "interval_duration": 120,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        self.job_id = None
        
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
        
    def test_create_split_video_job(self):
        """Test 1: Create a new job to test the fixed FFmpeg Lambda"""
        print("🔍 Testing POST /api/split-video with function signature fix...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=self.test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 202:
                success_criteria.append("✅ HTTP 202 (Accepted) status")
                
                try:
                    data = response.json()
                    
                    # Check for job_id
                    if 'job_id' in data:
                        self.job_id = data['job_id']
                        success_criteria.append(f"✅ job_id returned: {self.job_id}")
                    else:
                        success_criteria.append("❌ job_id missing from response")
                    
                    # Check for SQS message indication
                    if 'sqs_message_id' in data or 'status' in data:
                        if 'sqs_message_id' in data:
                            success_criteria.append(f"✅ SQS message sent: {data['sqs_message_id']}")
                        else:
                            success_criteria.append(f"✅ Job status: {data.get('status', 'unknown')}")
                    else:
                        success_criteria.append("⚠️ No SQS message confirmation (may still be working)")
                    
                    # Check response time (should be immediate for async processing)
                    if response_time < 10.0:
                        success_criteria.append(f"✅ Fast response time: {response_time:.2f}s (<10s)")
                    else:
                        success_criteria.append(f"❌ Slow response time: {response_time:.2f}s (≥10s)")
                    
                    # Check CORS headers
                    cors_headers = response.headers.get('Access-Control-Allow-Origin')
                    if cors_headers:
                        success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                    else:
                        success_criteria.append("❌ CORS headers missing")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
                    
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 202)")
                success_criteria.append(f"Response: {response.text[:200]}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Create Split Video Job", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Create Split Video Job", False, f"Request failed: {str(e)}")
            return False
    
    def test_verify_sqs_message_sent(self):
        """Test 2: Verify the SQS message is sent and job_id is returned"""
        print("🔍 Verifying SQS message was sent and job_id returned...")
        
        if not self.job_id:
            self.log_test("Verify SQS Message Sent", False, "No job_id available from previous test")
            return False
        
        success_criteria = []
        
        # Job ID format validation
        try:
            uuid.UUID(self.job_id)
            success_criteria.append("✅ Valid UUID job_id format")
        except ValueError:
            success_criteria.append(f"❌ Invalid job_id format: {self.job_id}")
        
        # Check if job_id is not empty and reasonable length
        if len(self.job_id) >= 32:
            success_criteria.append("✅ job_id has reasonable length")
        else:
            success_criteria.append(f"❌ job_id too short: {len(self.job_id)} chars")
        
        all_success = all("✅" in criterion for criterion in success_criteria)
        details = "; ".join(success_criteria)
        
        self.log_test("Verify SQS Message Sent", all_success, details)
        return all_success
    
    def test_wait_and_check_job_status(self):
        """Test 3: Wait 30 seconds then check job status"""
        print("🔍 Waiting 30 seconds then checking job status...")
        
        if not self.job_id:
            self.log_test("Wait and Check Job Status", False, "No job_id available from previous test")
            return False
        
        print("⏳ Waiting 30 seconds for processing...")
        time.sleep(30)
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                success_criteria.append("✅ HTTP 200 status")
                
                try:
                    data = response.json()
                    
                    # Check job_id matches
                    if data.get('job_id') == self.job_id:
                        success_criteria.append("✅ job_id matches request")
                    else:
                        success_criteria.append(f"❌ job_id mismatch: {data.get('job_id')} vs {self.job_id}")
                    
                    # Check status field
                    status = data.get('status', 'unknown')
                    if status in ['processing', 'completed', 'queued', 'accepted']:
                        success_criteria.append(f"✅ Valid status: {status}")
                    else:
                        success_criteria.append(f"❌ Invalid status: {status}")
                    
                    # Check progress field
                    progress = data.get('progress', 0)
                    if isinstance(progress, (int, float)) and progress >= 0:
                        success_criteria.append(f"✅ Progress value: {progress}%")
                        
                        # Key test: Check if job progresses beyond 25%
                        if progress > 25:
                            success_criteria.append("🎉 CRITICAL SUCCESS: Job progressed beyond 25%!")
                        elif progress == 25:
                            success_criteria.append("⚠️ Job at 25% - may be initial state or processing")
                        else:
                            success_criteria.append(f"⚠️ Job at {progress}% - early stage")
                    else:
                        success_criteria.append(f"❌ Invalid progress: {progress}")
                    
                    # Check response time
                    if response_time < 10.0:
                        success_criteria.append(f"✅ Fast response time: {response_time:.2f}s (<10s)")
                    else:
                        success_criteria.append(f"❌ Slow response time: {response_time:.2f}s (≥10s)")
                    
                    # Check CORS headers
                    cors_headers = response.headers.get('Access-Control-Allow-Origin')
                    if cors_headers:
                        success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                    else:
                        success_criteria.append("❌ CORS headers missing")
                        
                except json.JSONDecodeError:
                    success_criteria.append("❌ Invalid JSON response")
                    
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} (expected 200)")
                success_criteria.append(f"Response: {response.text[:200]}")
            
            all_success = all("✅" in criterion or "🎉" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("Wait and Check Job Status", all_success, details, response_time)
            return all_success
                
        except Exception as e:
            self.log_test("Wait and Check Job Status", False, f"Request failed: {str(e)}")
            return False
    
    def test_ffmpeg_lambda_error_resolution(self):
        """Test 4: Focus on whether the Lambda error is resolved"""
        print("🔍 Testing if FFmpeg Lambda error 'split_video() missing 1 required positional argument' is resolved...")
        
        if not self.job_id:
            self.log_test("FFmpeg Lambda Error Resolution", False, "No job_id available for testing")
            return False
        
        # Check job status again to see if there are any error messages
        try:
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for error messages in response
                error_message = data.get('error', '')
                message = data.get('message', '')
                status = data.get('status', '')
                
                # Look for the specific error we're testing for
                function_signature_error = "missing 1 required positional argument" in str(error_message).lower() or \
                                        "missing 1 required positional argument" in str(message).lower()
                
                if function_signature_error:
                    success_criteria.append("❌ CRITICAL: Function signature error still present!")
                else:
                    success_criteria.append("✅ No function signature error detected")
                
                # Check if status indicates successful processing start
                if status in ['processing', 'completed']:
                    success_criteria.append("✅ Job is processing/completed (no Lambda error)")
                elif status == 'failed' or 'error' in status.lower():
                    success_criteria.append(f"❌ Job failed: {status}")
                else:
                    success_criteria.append(f"⚠️ Job status: {status}")
                
                # Check progress to see if real processing is occurring
                progress = data.get('progress', 0)
                if progress > 0:
                    success_criteria.append(f"✅ Real video processing occurring: {progress}% progress")
                else:
                    success_criteria.append("⚠️ No progress detected yet")
                
            else:
                success_criteria.append(f"❌ Cannot check error status: HTTP {response.status_code}")
            
            all_success = all("✅" in criterion for criterion in success_criteria)
            details = "; ".join(success_criteria)
            
            self.log_test("FFmpeg Lambda Error Resolution", all_success, details)
            return all_success
                
        except Exception as e:
            self.log_test("FFmpeg Lambda Error Resolution", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all SQS video processing tests as per review request"""
        print("🚀 SQS-BASED VIDEO PROCESSING SYSTEM TEST")
        print("Testing the complete SQS-based video processing system with the function signature fix")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Test Payload: {json.dumps(self.test_payload, indent=2)}")
        print("=" * 80)
        print()
        
        # Run tests in order as specified in review request
        test_results = []
        
        test_results.append(self.test_create_split_video_job())
        test_results.append(self.test_verify_sqs_message_sent())
        test_results.append(self.test_wait_and_check_job_status())
        test_results.append(self.test_ffmpeg_lambda_error_resolution())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 SQS VIDEO PROCESSING TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        print("EXPECTED BEHAVIOR VERIFICATION:")
        expected_behaviors = [
            "✅ SQS message sent",
            "✅ FFmpeg Lambda processes without error", 
            "✅ Job progresses beyond 25%",
            "✅ Real video processing occurs"
        ]
        
        # Analyze results for expected behaviors
        actual_results = []
        
        # Check if SQS message was sent (from first test)
        sqs_test = next((r for r in self.test_results if r['test'] == 'Create Split Video Job'), None)
        if sqs_test and sqs_test['success']:
            actual_results.append("✅ SQS message sent")
        else:
            actual_results.append("❌ SQS message NOT sent")
        
        # Check if FFmpeg Lambda processes without error (from error resolution test)
        error_test = next((r for r in self.test_results if r['test'] == 'FFmpeg Lambda Error Resolution'), None)
        if error_test and error_test['success']:
            actual_results.append("✅ FFmpeg Lambda processes without error")
        else:
            actual_results.append("❌ FFmpeg Lambda has errors")
        
        # Check if job progresses beyond 25% (from status test)
        status_test = next((r for r in self.test_results if r['test'] == 'Wait and Check Job Status'), None)
        if status_test and "progressed beyond 25%" in status_test['details']:
            actual_results.append("✅ Job progresses beyond 25%")
        elif status_test and "25%" in status_test['details']:
            actual_results.append("⚠️ Job at 25% (may need more time)")
        else:
            actual_results.append("❌ Job does NOT progress beyond 25%")
        
        # Check if real video processing occurs
        if status_test and ("processing" in status_test['details'] or "progress" in status_test['details']):
            actual_results.append("✅ Real video processing occurs")
        else:
            actual_results.append("❌ Real video processing NOT detected")
        
        print("\nEXPECTED vs ACTUAL:")
        for expected, actual in zip(expected_behaviors, actual_results):
            print(f"Expected: {expected}")
            print(f"Actual:   {actual}")
            print()
        
        # Final assessment
        print("FOCUS QUESTION: Is the Lambda error 'split_video() missing 1 required positional argument' resolved?")
        if error_test and error_test['success']:
            print("🎉 YES - The function signature fix appears to be working!")
        else:
            print("❌ NO - The function signature error may still be present")
        
        print()
        return success_rate >= 75  # 3 out of 4 tests should pass for success

if __name__ == "__main__":
    tester = SQSVideoProcessingTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)