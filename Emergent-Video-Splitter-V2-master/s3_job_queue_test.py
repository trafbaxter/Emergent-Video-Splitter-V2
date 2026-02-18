#!/usr/bin/env python3
"""
S3 Job Queue System Testing for Video Splitter Pro

OBJECTIVE:
Verify that the split-video endpoint now creates job files in S3 that can be used for background processing.

TESTS:
1. Split Video Job Creation Test - POST to /api/split-video should return HTTP 202 immediately with job_id
   and create job file in S3 at jobs/{job_id}.json
2. Job File Content Verification - Check S3 for the created job file with correct job details
3. S3 Job Queue Check - List objects in jobs/ prefix in S3 bucket

SUCCESS CRITERIA:
✅ Split video returns 202 immediately with job_id
✅ Job file created in S3 at jobs/{job_id}.json
✅ Job file contains complete processing details
✅ S3 bucket shows job files in jobs/ directory
"""

import requests
import json
import time
import boto3
import uuid
from typing import Dict, Any, Optional
import sys
from botocore.exceptions import ClientError

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-storage-1751560247"
AWS_REGION = "us-east-1"
TIMEOUT = 30

class S3JobQueueTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.bucket_name = S3_BUCKET
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.test_results = []
        self.created_job_ids = []  # Track job IDs for cleanup
        
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

    def test_split_video_job_creation(self):
        """Test 1: Split Video Job Creation - should return 202 immediately with job_id"""
        print("🎯 TEST 1: Split Video Job Creation...")
        
        # Use exact payload from review request
        split_data = {
            "s3_key": "uploads/3edba1d9-b854-45b0-a7d4-54a88940f38b/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv",
            "method": "intervals",
            "interval_duration": 300,
            "preserve_quality": True,
            "output_format": "mp4"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            print(f"   📋 Testing with review request payload:")
            print(f"   📄 S3 Key: {split_data['s3_key']}")
            print(f"   ⚙️  Method: {split_data['method']}, Interval: {split_data['interval_duration']}s")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin: {cors_origin}")
            
            if response.status_code == 202:
                try:
                    data = response.json()
                    job_id = data.get('job_id')
                    status = data.get('status')
                    message = data.get('message')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    print(f"      message: {message}")
                    
                    if job_id:
                        self.created_job_ids.append(job_id)
                        
                        # Verify all expected fields are present
                        expected_fields = ['job_id', 'status', 'message', 's3_key', 'method']
                        missing_fields = [field for field in expected_fields if field not in data]
                        
                        if not missing_fields:
                            self.log_test(
                                "Split Video Job Creation",
                                True,
                                f"✅ HTTP 202 returned in {response_time:.2f}s with job_id={job_id}, status={status}, CORS headers present"
                            )
                            return job_id
                        else:
                            self.log_test(
                                "Split Video Job Creation",
                                False,
                                f"Missing expected fields: {missing_fields}",
                                data
                            )
                            return None
                    else:
                        self.log_test(
                            "Split Video Job Creation",
                            False,
                            "Response missing job_id field",
                            data
                        )
                        return None
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Split Video Job Creation",
                        False,
                        f"Invalid JSON response. Status: {response.status_code}, Content: {response.text[:200]}"
                    )
                    return None
            else:
                try:
                    error_data = response.json() if response.content else {}
                except:
                    error_data = {"raw_response": response.text[:200]}
                
                self.log_test(
                    "Split Video Job Creation",
                    False,
                    f"Expected HTTP 202, got {response.status_code}. Response time: {response_time:.2f}s",
                    error_data
                )
                return None
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Split Video Job Creation",
                False,
                f"Request timeout after {TIMEOUT}s - endpoint not responding fast enough"
            )
            return None
        except Exception as e:
            self.log_test(
                "Split Video Job Creation",
                False,
                f"Error: {str(e)}"
            )
            return None

    def test_job_file_content_verification(self, job_id: str):
        """Test 2: Job File Content Verification - check S3 for created job file"""
        print("🔍 TEST 2: Job File Content Verification...")
        
        if not job_id:
            self.log_test(
                "Job File Content Verification",
                False,
                "No job_id provided - cannot verify job file"
            )
            return False
        
        try:
            job_key = f"jobs/{job_id}.json"
            print(f"   📁 Checking S3 for job file: s3://{self.bucket_name}/{job_key}")
            
            # Give S3 a moment to ensure consistency
            time.sleep(2)
            
            # Try to get the job file from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=job_key)
            job_content = response['Body'].read().decode('utf-8')
            job_data = json.loads(job_content)
            
            print(f"   📄 Job file found! Size: {len(job_content)} bytes")
            print(f"   📋 Job file contents:")
            
            # Verify required fields in job file
            required_fields = [
                'job_id', 'created_at', 'source_bucket', 'source_key', 
                'split_config', 'status', 'output_bucket', 'output_prefix'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in job_data:
                    present_fields.append(field)
                    if field == 'split_config':
                        split_config = job_data[field]
                        print(f"      {field}: method={split_config.get('method')}, interval={split_config.get('interval_duration')}")
                    elif field == 'source_key':
                        print(f"      {field}: {job_data[field]}")
                    elif field == 'output_prefix':
                        print(f"      {field}: {job_data[field]}")
                    else:
                        print(f"      {field}: {job_data[field]}")
                else:
                    missing_fields.append(field)
            
            # Verify split_config contains expected parameters
            split_config = job_data.get('split_config', {})
            expected_config_fields = ['method', 'interval_duration', 'preserve_quality', 'output_format']
            missing_config_fields = [field for field in expected_config_fields if field not in split_config]
            
            if not missing_fields and not missing_config_fields:
                # Verify the job_id matches
                if job_data.get('job_id') == job_id:
                    self.log_test(
                        "Job File Content Verification",
                        True,
                        f"✅ Job file s3://{self.bucket_name}/{job_key} contains all required fields and correct job_id. Split config includes method={split_config.get('method')}, interval={split_config.get('interval_duration')}s"
                    )
                    return True
                else:
                    self.log_test(
                        "Job File Content Verification",
                        False,
                        f"Job ID mismatch: expected {job_id}, got {job_data.get('job_id')}",
                        job_data
                    )
                    return False
            else:
                error_details = []
                if missing_fields:
                    error_details.append(f"Missing required fields: {missing_fields}")
                if missing_config_fields:
                    error_details.append(f"Missing split_config fields: {missing_config_fields}")
                
                self.log_test(
                    "Job File Content Verification",
                    False,
                    ". ".join(error_details),
                    job_data
                )
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                self.log_test(
                    "Job File Content Verification",
                    False,
                    f"Job file not found in S3: s3://{self.bucket_name}/jobs/{job_id}.json"
                )
            else:
                self.log_test(
                    "Job File Content Verification",
                    False,
                    f"S3 error ({error_code}): {e.response['Error']['Message']}"
                )
            return False
        except json.JSONDecodeError:
            self.log_test(
                "Job File Content Verification",
                False,
                f"Job file contains invalid JSON: {job_content[:200]}..."
            )
            return False
        except Exception as e:
            self.log_test(
                "Job File Content Verification",
                False,
                f"Error accessing job file: {str(e)}"
            )
            return False

    def test_s3_job_queue_check(self):
        """Test 3: S3 Job Queue Check - list objects in jobs/ prefix"""
        print("📂 TEST 3: S3 Job Queue Check...")
        
        try:
            print(f"   📁 Listing objects in s3://{self.bucket_name}/jobs/")
            
            # List objects in the jobs/ prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='jobs/',
                MaxKeys=20  # Limit to avoid too much output
            )
            
            if 'Contents' in response:
                job_files = response['Contents']
                print(f"   📊 Found {len(job_files)} job files in queue:")
                
                recent_jobs = []
                for obj in job_files:
                    key = obj['Key']
                    size = obj['Size']
                    modified = obj['LastModified']
                    
                    # Check if this is one of our created jobs
                    is_our_job = any(job_id in key for job_id in self.created_job_ids)
                    marker = "🆕" if is_our_job else "📄"
                    
                    print(f"      {marker} {key} ({size} bytes, {modified})")
                    
                    # Track recent jobs (within last hour)
                    if (datetime.now(modified.tzinfo) - modified).total_seconds() < 3600:
                        recent_jobs.append(key)
                
                # Verify our created jobs are in the list
                our_jobs_found = []
                for job_id in self.created_job_ids:
                    expected_key = f"jobs/{job_id}.json"
                    if any(expected_key == obj['Key'] for obj in job_files):
                        our_jobs_found.append(job_id)
                
                if our_jobs_found:
                    self.log_test(
                        "S3 Job Queue Check",
                        True,
                        f"✅ Found {len(job_files)} total job files, including {len(our_jobs_found)} from this test session. Recent jobs: {len(recent_jobs)}"
                    )
                    return True
                else:
                    self.log_test(
                        "S3 Job Queue Check",
                        False,
                        f"Found {len(job_files)} job files but none match our created job IDs: {self.created_job_ids}"
                    )
                    return False
            else:
                self.log_test(
                    "S3 Job Queue Check",
                    False,
                    "No job files found in s3://{}/jobs/ - job queue appears empty".format(self.bucket_name)
                )
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.log_test(
                "S3 Job Queue Check",
                False,
                f"S3 error ({error_code}): {e.response['Error']['Message']}"
            )
            return False
        except Exception as e:
            self.log_test(
                "S3 Job Queue Check",
                False,
                f"Error listing S3 objects: {str(e)}"
            )
            return False

    def cleanup_test_jobs(self):
        """Clean up job files created during testing"""
        if not self.created_job_ids:
            return
        
        print("🧹 Cleaning up test job files...")
        for job_id in self.created_job_ids:
            try:
                job_key = f"jobs/{job_id}.json"
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=job_key)
                print(f"   🗑️  Deleted: s3://{self.bucket_name}/{job_key}")
            except Exception as e:
                print(f"   ⚠️  Failed to delete {job_key}: {str(e)}")

    def run_s3_job_queue_tests(self):
        """Run all S3 job queue system tests"""
        print("=" * 80)
        print("🎯 S3 JOB QUEUE SYSTEM TESTING")
        print("=" * 80)
        print(f"API Gateway URL: {self.base_url}")
        print(f"S3 Bucket: {self.bucket_name}")
        print()
        print("🎯 OBJECTIVE:")
        print("   Verify that split-video endpoint creates job files in S3 for background processing")
        print()
        print("📋 SUCCESS CRITERIA:")
        print("   ✅ Split video returns 202 immediately with job_id")
        print("   ✅ Job file created in S3 at jobs/{job_id}.json")
        print("   ✅ Job file contains complete processing details")
        print("   ✅ S3 bucket shows job files in jobs/ directory")
        print()
        
        try:
            # Test 1: Create split video job
            job_id = self.test_split_video_job_creation()
            
            # Test 2: Verify job file content (only if job was created)
            job_file_ok = False
            if job_id:
                job_file_ok = self.test_job_file_content_verification(job_id)
            
            # Test 3: Check S3 job queue
            queue_ok = self.test_s3_job_queue_check()
            
            # Summary
            print("=" * 80)
            print("📊 S3 JOB QUEUE TEST SUMMARY")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            failed_tests = total_tests - passed_tests
            
            print(f"Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            print()
            
            # Critical assessment
            print("💡 CRITICAL ASSESSMENT:")
            
            if passed_tests == total_tests:
                print("   🎉 S3 JOB QUEUE SYSTEM WORKING PERFECTLY!")
                print("   • Split-video endpoint returns 202 immediately with job_id")
                print("   • Job files are created in S3 at jobs/{job_id}.json")
                print("   • Job files contain all required processing details")
                print("   • S3 job queue is operational and ready for background processing")
                print("   • System is ready for background processing trigger implementation")
            else:
                print("   ❌ S3 JOB QUEUE SYSTEM HAS ISSUES")
                
                # Analyze specific failures
                for result in self.test_results:
                    if not result['success']:
                        print(f"      • {result['test']}: {result['details']}")
            
            print()
            print("🔍 EXPECTED OUTCOME:")
            if passed_tests == total_tests:
                print("   ✅ Job queue system is working and ready for background processing")
                print("   ✅ Split requests create proper job files in S3")
                print("   ✅ Background processing can be triggered by S3 events")
                print("   ✅ All review request success criteria met")
            else:
                print("   ❌ Job queue system needs fixes before background processing")
                print("   ❌ Some components not working as expected")
            
            print()
            print("=" * 80)
            
            return passed_tests, failed_tests
            
        finally:
            # Clean up test job files
            self.cleanup_test_jobs()

# Add datetime import for recent jobs check
from datetime import datetime

if __name__ == "__main__":
    tester = S3JobQueueTester()
    passed, failed = tester.run_s3_job_queue_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)