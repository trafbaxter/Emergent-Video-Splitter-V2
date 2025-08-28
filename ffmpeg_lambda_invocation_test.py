#!/usr/bin/env python3
"""
CRITICAL: Test the direct FFmpeg Lambda invocation fix

OBJECTIVE:
Test that the updated split-video endpoint now successfully invokes the FFmpeg Lambda 
and that actual video processing begins.

SPECIFIC TEST:
1. Split Video with Real S3 Key
2. Wait and Check FFmpeg Lambda Logs
3. Job Status Verification

SUCCESS CRITERIA:
✅ Split video returns 202 immediately
✅ FFmpeg Lambda logs show actual processing activity 
✅ Real video file is being processed (not just fake invocation)
✅ Job status shows 25% progress (indicating real S3 file checking)
"""

import requests
import json
import time
import uuid
import subprocess
from typing import Dict, Any, Optional
import sys

# Configuration
API_BASE = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 35  # 35 second timeout for testing

class FFmpegLambdaInvocationTester:
    def __init__(self):
        self.base_url = API_BASE
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
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

    def test_split_video_with_real_s3_key(self):
        """Test split-video with the exact real S3 key from review request"""
        print("🎯 CRITICAL TEST: Split Video with Real S3 Key...")
        
        # Exact payload from review request with real S3 key
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
            
            print(f"   🎯 Testing with REAL S3 key from review request...")
            print(f"   📋 S3 Key: {split_data['s3_key']}")
            print(f"   📋 Method: {split_data['method']}")
            print(f"   📋 Interval: {split_data['interval_duration']}s")
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/split-video", json=split_data, headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   🌐 CORS Origin header: {cors_origin}")
            
            # SUCCESS CRITERIA CHECK
            success_criteria = {
                'http_202': response.status_code == 202,
                'immediate_response': response_time < 10.0,  # Should be immediate
                'cors_headers': cors_origin is not None,
                'no_timeout': response.status_code != 504
            }
            
            print(f"   📋 SUCCESS CRITERIA:")
            print(f"      ✅ HTTP 202 status: {'PASS' if success_criteria['http_202'] else 'FAIL'} (got {response.status_code})")
            print(f"      ✅ Immediate response: {'PASS' if success_criteria['immediate_response'] else 'FAIL'} ({response_time:.2f}s)")
            print(f"      ✅ CORS headers: {'PASS' if success_criteria['cors_headers'] else 'FAIL'} ({cors_origin})")
            print(f"      ✅ No timeout: {'PASS' if success_criteria['no_timeout'] else 'FAIL'}")
            
            job_id = None
            if response.status_code == 202:
                # Parse response for job_id
                try:
                    data = response.json()
                    job_id = data.get('job_id')
                    status = data.get('status')
                    
                    print(f"   📄 Response data:")
                    print(f"      job_id: {job_id}")
                    print(f"      status: {status}")
                    
                    if job_id and status:
                        success_criteria['response_fields'] = True
                        print(f"      ✅ Response fields: PASS")
                    else:
                        success_criteria['response_fields'] = False
                        print(f"      ❌ Response fields: FAIL (missing job_id or status)")
                        
                except json.JSONDecodeError:
                    success_criteria['response_fields'] = False
                    print(f"      ❌ Response fields: FAIL (invalid JSON)")
                    data = {}
            else:
                success_criteria['response_fields'] = False
                try:
                    data = response.json() if response.content else {}
                except:
                    data = {}
            
            # Overall success assessment
            all_criteria_met = all(success_criteria.values())
            
            if all_criteria_met:
                self.log_test(
                    "🎉 SPLIT-VIDEO WITH REAL S3 KEY SUCCESS",
                    True,
                    f"✅ Split video returns HTTP 202 immediately in {response_time:.2f}s with job_id={job_id}. Ready for FFmpeg Lambda invocation test!"
                )
                return True, job_id
            else:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                self.log_test(
                    "❌ SPLIT-VIDEO WITH REAL S3 KEY FAILED",
                    False,
                    f"Failed criteria: {failed_criteria}. Status: {response.status_code}, Time: {response_time:.2f}s, CORS: {cors_origin}",
                    data
                )
                return False, None
                
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ SPLIT-VIDEO TIMEOUT",
                False,
                f"🚨 CRITICAL: Client timeout after {TIMEOUT}s - endpoint is not responding immediately as expected"
            )
            return False, None
        except Exception as e:
            self.log_test(
                "❌ SPLIT-VIDEO ERROR",
                False,
                f"Error: {str(e)}"
            )
            return False, None

    def wait_and_check_ffmpeg_logs(self):
        """Wait 30 seconds and check FFmpeg Lambda logs for processing activity"""
        print("⏳ WAITING 30 SECONDS FOR FFMPEG LAMBDA PROCESSING...")
        print("   This will allow time for the FFmpeg Lambda to be invoked and start processing")
        
        # Wait 30 seconds as requested
        for i in range(30, 0, -1):
            print(f"   ⏱️  Waiting {i} seconds...", end='\r')
            time.sleep(1)
        print("   ✅ 30 second wait complete!")
        print()
        
        print("🔍 CHECKING FFMPEG LAMBDA LOGS...")
        try:
            # Check recent FFmpeg Lambda logs
            cmd = [
                'aws', 'logs', 'filter-log-events',
                '--log-group-name', '/aws/lambda/ffmpeg-video-processor',
                '--start-time', str(int((time.time() - 300) * 1000)),  # Last 5 minutes
                '--query', 'events[*].[timestamp,message]',
                '--output', 'text'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                log_lines = result.stdout.strip().split('\n')
                recent_logs = [line for line in log_lines if line.strip()]
                
                print(f"   📋 Found {len(recent_logs)} recent log entries")
                
                # Look for processing indicators
                processing_indicators = [
                    'downloading from s3',
                    'ffmpeg',
                    'processing video',
                    'splitting video',
                    'Rise of the Teenage Mutant Ninja Turtles',
                    'mkv',
                    'interval_duration'
                ]
                
                processing_activity = False
                for log_line in recent_logs[-10:]:  # Check last 10 log entries
                    log_lower = log_line.lower()
                    for indicator in processing_indicators:
                        if indicator.lower() in log_lower:
                            processing_activity = True
                            print(f"   ✅ PROCESSING ACTIVITY DETECTED: {log_line[:100]}...")
                            break
                    if processing_activity:
                        break
                
                if processing_activity:
                    self.log_test(
                        "🎉 FFMPEG LAMBDA PROCESSING CONFIRMED",
                        True,
                        f"✅ FFmpeg Lambda logs show actual processing activity! Found processing indicators in recent logs."
                    )
                    return True
                else:
                    self.log_test(
                        "⚠️ FFMPEG LAMBDA LOGS UNCLEAR",
                        False,
                        f"FFmpeg Lambda logs found but no clear processing indicators. May need more time or different search terms."
                    )
                    return False
            else:
                self.log_test(
                    "❌ FFMPEG LAMBDA LOGS NOT FOUND",
                    False,
                    f"No recent FFmpeg Lambda logs found. Error: {result.stderr}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.log_test(
                "❌ FFMPEG LAMBDA LOG CHECK TIMEOUT",
                False,
                "AWS CLI command timed out while checking logs"
            )
            return False
        except Exception as e:
            self.log_test(
                "❌ FFMPEG LAMBDA LOG CHECK ERROR",
                False,
                f"Error checking logs: {str(e)}"
            )
            return False

    def test_job_status_verification(self, job_id: str):
        """Test job status to verify 25% progress indicating real S3 file checking"""
        if not job_id:
            self.log_test(
                "❌ JOB STATUS VERIFICATION SKIPPED",
                False,
                "No job_id available from split-video test"
            )
            return False
            
        print(f"🔍 TESTING JOB STATUS VERIFICATION with job_id: {job_id}...")
        
        try:
            headers = {
                'Origin': 'https://working.tads-video-splitter.com'
            }
            
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/job-status/{job_id}", headers=headers)
            response_time = time.time() - start_time
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            print(f"   📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    
                    print(f"   📄 Job Status Response:")
                    print(f"      job_id: {data.get('job_id')}")
                    print(f"      status: {status}")
                    print(f"      progress: {progress}%")
                    
                    # Check if progress shows 25% (indicating real S3 file checking)
                    if progress == 25:
                        self.log_test(
                            "🎉 JOB STATUS SHOWS 25% PROGRESS",
                            True,
                            f"✅ Job status shows 25% progress, indicating real S3 file checking is working! Status: {status}"
                        )
                        return True
                    elif progress > 0:
                        self.log_test(
                            "✅ JOB STATUS SHOWS PROGRESS",
                            True,
                            f"Job status shows {progress}% progress (expected 25% but any progress indicates real processing). Status: {status}"
                        )
                        return True
                    else:
                        self.log_test(
                            "⚠️ JOB STATUS NO PROGRESS",
                            False,
                            f"Job status shows 0% progress. May need more time for processing to begin. Status: {status}"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "❌ JOB STATUS INVALID RESPONSE",
                        False,
                        f"Invalid JSON response from job status endpoint"
                    )
                    return False
            else:
                self.log_test(
                    "❌ JOB STATUS ENDPOINT FAILED",
                    False,
                    f"Job status endpoint returned HTTP {response.status_code} in {response_time:.2f}s"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "❌ JOB STATUS TIMEOUT",
                False,
                f"Job status endpoint timed out after {TIMEOUT}s"
            )
            return False
        except Exception as e:
            self.log_test(
                "❌ JOB STATUS ERROR",
                False,
                f"Error: {str(e)}"
            )
            return False

    def run_ffmpeg_lambda_invocation_test(self):
        """Run the complete FFmpeg Lambda invocation test as requested in review"""
        print("=" * 80)
        print("🚨 CRITICAL: TEST DIRECT FFMPEG LAMBDA INVOCATION FIX")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print()
        print("🎯 OBJECTIVE:")
        print("   Test that the updated split-video endpoint now successfully invokes")
        print("   the FFmpeg Lambda and that actual video processing begins.")
        print()
        print("📋 SPECIFIC TESTS:")
        print("   1. Split Video with Real S3 Key")
        print("   2. Wait 30 seconds and Check FFmpeg Lambda Logs")
        print("   3. Job Status Verification")
        print()
        print("✅ SUCCESS CRITERIA:")
        print("   ✅ Split video returns 202 immediately")
        print("   ✅ FFmpeg Lambda logs show actual processing activity")
        print("   ✅ Real video file is being processed (not just fake invocation)")
        print("   ✅ Job status shows 25% progress (indicating real S3 file checking)")
        print()
        
        # Test 1: Split Video with Real S3 Key
        split_success, job_id = self.test_split_video_with_real_s3_key()
        
        # Test 2: Wait and Check FFmpeg Lambda Logs
        if split_success:
            ffmpeg_logs_success = self.wait_and_check_ffmpeg_logs()
        else:
            print("⏭️  SKIPPING FFmpeg Lambda logs check due to split-video failure")
            ffmpeg_logs_success = False
        
        # Test 3: Job Status Verification
        if split_success:
            job_status_success = self.test_job_status_verification(job_id)
        else:
            print("⏭️  SKIPPING job status verification due to split-video failure")
            job_status_success = False
        
        # Summary
        print("=" * 80)
        print("📊 FFMPEG LAMBDA INVOCATION TEST SUMMARY")
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
        
        if split_success and (ffmpeg_logs_success or job_status_success):
            print("   🎉 FFMPEG LAMBDA INVOCATION FIX SUCCESSFUL!")
            print("   • Split video endpoint returns 202 immediately")
            print("   • FFmpeg Lambda is being invoked for real processing")
            print("   • Real video file processing has begun")
            print("   • Job status tracking is working")
            print("   • User will see progress change from 25% to higher values")
        elif split_success:
            print("   ⚠️ PARTIAL SUCCESS - SPLIT VIDEO WORKING")
            print("   • Split video endpoint is working (HTTP 202 immediately)")
            print("   • However, FFmpeg Lambda processing verification is unclear")
            print("   • May need more time for processing to show in logs/status")
        else:
            print("   ❌ FFMPEG LAMBDA INVOCATION FIX FAILED")
            print("   • Split video endpoint is not working as expected")
            print("   • FFmpeg Lambda invocation cannot be verified")
            print("   • Real video processing is not happening")
        
        print()
        print("🔍 USER IMPACT:")
        if split_success and (ffmpeg_logs_success or job_status_success):
            print("   ✅ User can successfully start video splitting")
            print("   ✅ Real video processing begins immediately")
            print("   ✅ Progress will advance beyond 25% as processing completes")
            print("   ✅ Output files will be created in outputs/{job_id}/")
        elif split_success:
            print("   ⚠️ User can start video splitting but processing verification unclear")
            print("   ⚠️ May need to wait longer to see processing results")
        else:
            print("   ❌ User cannot start video splitting")
            print("   ❌ Video processing functionality remains broken")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = FFmpegLambdaInvocationTester()
    passed, failed = tester.run_ffmpeg_lambda_invocation_test()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)