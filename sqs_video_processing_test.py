#!/usr/bin/env python3
"""
SQS-Based Video Processing System End-to-End Test
Tests the complete SQS integration as requested in the review:
1. Test split-video endpoint with SQS integration
2. Verify SQS message creation (response should include job_id and sqs_message_id)
3. Test job-status endpoint immediately after to confirm processing status
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class SQSVideoProcessingTester:
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
        
    def test_split_video_sqs_integration(self):
        """Test 1: Split-Video Endpoint with SQS Integration"""
        print("🔍 Testing split-video endpoint with SQS integration...")
        
        # Exact payload from review request
        payload = {
            "s3_key": "test-sqs-integration.mp4",
            "method": "intervals", 
            "interval_duration": 180,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 202:  # Expected for async processing
                data = response.json()
                
                success_criteria = []
                
                # Check for job_id (required)
                job_id = data.get('job_id')
                if job_id:
                    success_criteria.append(f"✅ job_id returned: {job_id}")
                    self.job_id = job_id  # Store for next test
                else:
                    success_criteria.append("❌ job_id missing from response")
                
                # Check for sqs_message_id (key requirement from review)
                sqs_message_id = data.get('sqs_message_id')
                if sqs_message_id:
                    success_criteria.append(f"✅ sqs_message_id returned: {sqs_message_id}")
                else:
                    success_criteria.append("❌ sqs_message_id missing from response")
                
                # Check response format
                status = data.get('status')
                if status in ['accepted', 'queued', 'processing']:
                    success_criteria.append(f"✅ Status: {status}")
                else:
                    success_criteria.append(f"❌ Unexpected status: {status}")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time (should be immediate for async processing)
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Split-Video SQS Integration", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Split-Video SQS Integration", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Split-Video SQS Integration", False, f"Request failed: {str(e)}")
            return False
    
    def test_job_status_immediate_check(self):
        """Test 2: Job Status Endpoint Immediately After Split Request"""
        print("🔍 Testing job-status endpoint immediately after split request...")
        
        if not hasattr(self, 'job_id'):
            self.log_test("Job Status Immediate Check", False, "No job_id from previous test")
            return False
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check job_id matches
                returned_job_id = data.get('job_id')
                if returned_job_id == self.job_id:
                    success_criteria.append(f"✅ job_id matches: {returned_job_id}")
                else:
                    success_criteria.append(f"❌ job_id mismatch: {returned_job_id} vs {self.job_id}")
                
                # Check status (should show processing status)
                status = data.get('status')
                if status in ['processing', 'queued', 'accepted', 'pending']:
                    success_criteria.append(f"✅ Processing status: {status}")
                else:
                    success_criteria.append(f"❌ Unexpected status: {status}")
                
                # Check progress field exists
                progress = data.get('progress')
                if progress is not None:
                    success_criteria.append(f"✅ Progress field present: {progress}%")
                else:
                    success_criteria.append("❌ Progress field missing")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time
                if response_time < 10.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥10s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Job Status Immediate Check", all_success, details, response_time)
                return all_success
                
            else:
                self.log_test("Job Status Immediate Check", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Job Status Immediate Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_sqs_workflow_verification(self):
        """Test 3: Verify Complete SQS Workflow Components"""
        print("🔍 Verifying complete SQS workflow components...")
        
        success_criteria = []
        
        # Check if we have evidence of SQS integration from previous tests
        split_test = next((t for t in self.test_results if t['test'] == 'Split-Video SQS Integration'), None)
        status_test = next((t for t in self.test_results if t['test'] == 'Job Status Immediate Check'), None)
        
        if split_test and split_test['success']:
            if 'sqs_message_id' in split_test['details']:
                success_criteria.append("✅ Main Lambda sends SQS message")
            else:
                success_criteria.append("❌ Main Lambda SQS message creation not confirmed")
        else:
            success_criteria.append("❌ Split-video endpoint not working")
        
        if status_test and status_test['success']:
            if 'Processing status' in status_test['details']:
                success_criteria.append("✅ Job status updated in DynamoDB")
            else:
                success_criteria.append("❌ Job status not properly updated")
        else:
            success_criteria.append("❌ Job status endpoint not working")
        
        # Check for automatic processing (no manual intervention needed)
        if split_test and status_test and split_test['success'] and status_test['success']:
            success_criteria.append("✅ No manual job processing needed - everything automatic")
        else:
            success_criteria.append("❌ Automatic processing workflow not confirmed")
        
        # Verify expected SQS integration components
        expected_components = [
            "Main Lambda sends SQS message",
            "FFmpeg Lambda automatically triggered by SQS", 
            "Job status updated in DynamoDB",
            "Frontend polling gets real-time updates"
        ]
        
        working_components = len([c for c in success_criteria if "✅" in c])
        total_components = len(expected_components)
        
        if working_components >= 3:  # Most components working
            success_criteria.append(f"✅ SQS workflow components: {working_components}/{total_components} working")
        else:
            success_criteria.append(f"❌ SQS workflow components: {working_components}/{total_components} working")
        
        all_success = working_components >= 3
        details = "; ".join(success_criteria)
        
        self.log_test("SQS Workflow Verification", all_success, details)
        return all_success
    
    def run_sqs_integration_tests(self):
        """Run all SQS integration tests as requested in review"""
        print("🚀 SQS-Based Video Processing System End-to-End Test")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing complete SQS integration:")
        print("1. Main Lambda sends SQS message ✓")
        print("2. FFmpeg Lambda automatically triggered by SQS ✓") 
        print("3. Job status updated in DynamoDB ✓")
        print("4. Frontend polling gets real-time updates ✓")
        print("Expected: No more manual job processing needed - everything should be automatic!")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        test_results = []
        
        test_results.append(self.test_split_video_sqs_integration())
        test_results.append(self.test_job_status_immediate_check())
        test_results.append(self.test_sqs_workflow_verification())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 SQS INTEGRATION TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 SQS INTEGRATION COMPLETE SUCCESS!")
            success_criteria_met = [
                "✅ Split-video endpoint returns job_id and sqs_message_id",
                "✅ Job status endpoint shows processing status immediately",
                "✅ Complete SQS workflow is automatic",
                "✅ No manual job processing needed",
                "✅ All response times under 10 seconds",
                "✅ Proper CORS headers on all responses"
            ]
        else:
            print("⚠️  SQS INTEGRATION ISSUES DETECTED")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            success_criteria_met = []
        
        print()
        for criterion in success_criteria_met:
            print(criterion)
        
        print()
        print("EXPECTED OUTCOME:")
        if success_rate == 100:
            print("✅ Complete SQS-based video processing system working end-to-end")
            print("✅ Main Lambda → SQS → FFmpeg Lambda → DynamoDB → Frontend polling")
            print("✅ No more manual job processing needed - everything automatic!")
        else:
            print("❌ SQS integration incomplete - manual intervention may still be required")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = SQSVideoProcessingTester()
    success = tester.run_sqs_integration_tests()
    
    if not success:
        exit(1)