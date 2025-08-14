#!/usr/bin/env python3
"""
Extended Job Analysis Test
Tests multiple job IDs and analyzes the job status system more comprehensively.
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from .env configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class ExtendedJobAnalysisTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        
        # Original job IDs from review request
        self.original_job_ids = [
            "c5e2575b-0896-4080-8be9-25ff9212d96d",  # User's original job
            "7cd38811-46a3-42a5-acf1-44b5aad9ecd7",  # Newest job that was just processed
            "446b9ce0-1c24-46d7-81c3-0efae25a5e15"   # One more recent job
        ]
        
        # Additional job IDs to test (from test_result.md history)
        self.additional_job_ids = [
            "test-job-123",  # Test job ID used in previous tests
            "81ccaaac-c506-40b5-8dc9-0ea774d2fa42",  # From test history
            "24955ecf-6152-435f-a392-5c0ee6b07916",  # From test history
            "65992b78-4120-4a45-a4af-d8c835a58635",  # From test history
            "0c205835-9155-4a86-b364-c84b1ab0f03d",  # Ninja Turtles video job
            "a27beb30-44dd-4fad-b45f-7f30f76434a5"   # Intervals processing job
        ]
        
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
        
    def test_job_status_detailed(self, job_id, job_description):
        """Test job status endpoint with detailed analysis"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'job_id': job_id,
                        'description': job_description,
                        'success': True,
                        'status': data.get('status'),
                        'progress': data.get('progress'),
                        'message': data.get('message', ''),
                        'response_time': response_time,
                        'raw_response': data
                    }
                except json.JSONDecodeError:
                    return {
                        'job_id': job_id,
                        'description': job_description,
                        'success': False,
                        'error': 'Invalid JSON response',
                        'response_time': response_time
                    }
            else:
                return {
                    'job_id': job_id,
                    'description': job_description,
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time
                }
                
        except Exception as e:
            return {
                'job_id': job_id,
                'description': job_description,
                'success': False,
                'error': str(e),
                'response_time': None
            }
    
    def test_create_new_job(self):
        """Test creating a new job to see if it gets different progress"""
        print("🔍 Testing Split Video to Create New Job...")
        
        try:
            payload = {
                "s3_key": "test-video-ffprobe-check.mp4",
                "method": "intervals",
                "interval_duration": 300,
                "preserve_quality": True,
                "output_format": "mp4"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/split-video",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 202:
                data = response.json()
                job_id = data.get('job_id')
                
                if job_id:
                    self.log_test("Create New Job", True, 
                                f"Created job {job_id} in {response_time:.2f}s", response_time)
                    
                    # Wait a moment then check status
                    time.sleep(2)
                    return self.test_job_status_detailed(job_id, "Newly Created Job")
                else:
                    self.log_test("Create New Job", False, 
                                f"No job_id in response: {data}", response_time)
                    return None
            else:
                self.log_test("Create New Job", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_test("Create New Job", False, f"Request failed: {str(e)}")
            return None
    
    def run_extended_analysis(self):
        """Run extended job analysis"""
        print("🚀 Extended Job Analysis Test")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print("Testing multiple job IDs to analyze job status system behavior")
        print("=" * 80)
        print()
        
        all_results = []
        
        # Test original job IDs
        print("📋 TESTING ORIGINAL JOB IDs FROM REVIEW REQUEST:")
        original_descriptions = [
            "User's Original Job",
            "Newest Processed Job", 
            "Recent Job"
        ]
        
        for i, job_id in enumerate(self.original_job_ids):
            result = self.test_job_status_detailed(job_id, original_descriptions[i])
            all_results.append(result)
            
            if result['success']:
                print(f"   {result['description']}: {result['progress']}% (Status: {result['status']})")
            else:
                print(f"   {result['description']}: FAILED - {result.get('error', 'Unknown error')}")
        
        print()
        
        # Test additional job IDs
        print("📋 TESTING ADDITIONAL JOB IDs FROM TEST HISTORY:")
        for job_id in self.additional_job_ids:
            result = self.test_job_status_detailed(job_id, f"Historical Job")
            all_results.append(result)
            
            if result['success']:
                print(f"   {job_id}: {result['progress']}% (Status: {result['status']})")
            else:
                print(f"   {job_id}: FAILED - {result.get('error', 'Unknown error')}")
        
        print()
        
        # Create a new job to test
        print("📋 CREATING NEW JOB FOR FRESH TESTING:")
        new_job_result = self.test_create_new_job()
        if new_job_result:
            all_results.append(new_job_result)
            if new_job_result['success']:
                print(f"   New Job: {new_job_result['progress']}% (Status: {new_job_result['status']})")
            else:
                print(f"   New Job: FAILED - {new_job_result.get('error', 'Unknown error')}")
        
        print()
        
        # Analysis
        successful_jobs = [r for r in all_results if r and r['success']]
        failed_jobs = [r for r in all_results if r and not r['success']]
        
        if successful_jobs:
            progress_values = [r['progress'] for r in successful_jobs if r['progress'] is not None]
            status_values = [r['status'] for r in successful_jobs if r['status']]
            
            print("=" * 80)
            print("📊 COMPREHENSIVE ANALYSIS")
            print("=" * 80)
            print(f"Total Jobs Tested: {len(all_results)}")
            print(f"Successful Responses: {len(successful_jobs)}")
            print(f"Failed Responses: {len(failed_jobs)}")
            print()
            
            if progress_values:
                unique_progress = list(set(progress_values))
                print(f"Progress Values Found: {unique_progress}")
                
                progress_25 = len([p for p in progress_values if p == 25])
                progress_above_25 = len([p for p in progress_values if p > 25])
                progress_below_25 = len([p for p in progress_values if p < 25])
                
                print(f"Jobs at 25% progress: {progress_25}")
                print(f"Jobs above 25% progress: {progress_above_25}")
                print(f"Jobs below 25% progress: {progress_below_25}")
                print()
            
            if status_values:
                unique_statuses = list(set(status_values))
                print(f"Status Values Found: {unique_statuses}")
                print()
            
            # Check for patterns
            print("🔍 PATTERN ANALYSIS:")
            if len(set(progress_values)) == 1 and progress_values[0] == 25:
                print("❌ ALL jobs show exactly 25% progress - this indicates a systemic issue")
                print("❌ Progress calculation appears to be returning a default/placeholder value")
                print("❌ This suggests the ffprobe fix may not be working, or there's another issue")
            elif any(p > 25 for p in progress_values):
                print("✅ Some jobs show progress > 25% - ffprobe/FFmpeg appears to be working!")
                working_jobs = [r for r in successful_jobs if r['progress'] and r['progress'] > 25]
                for job in working_jobs:
                    print(f"   - {job['description']}: {job['progress']}%")
            else:
                print("⚠️ Mixed progress values but none above 25% - inconclusive results")
            
            print()
            
            # Final assessment
            print("🎯 FFPROBE FIX ASSESSMENT:")
            if any(p > 25 for p in progress_values):
                print("✅ SUCCESS: FFprobe lambda layer fix appears to be working!")
                print("✅ At least some jobs are progressing beyond the 25% threshold.")
            elif all(p == 25 for p in progress_values):
                print("❌ ISSUE CONFIRMED: All jobs stuck at exactly 25% progress.")
                print("❌ This indicates the ffprobe fix is NOT working, or there are other blocking issues.")
                print("❌ The job status system is returning placeholder values instead of real progress.")
            else:
                print("⚠️ INCONCLUSIVE: Mixed results - need further investigation.")
        
        else:
            print("❌ No successful job status responses - unable to assess ffprobe fix")
        
        print()
        return len([r for r in all_results if r and r['success'] and r.get('progress', 0) > 25]) > 0

if __name__ == "__main__":
    tester = ExtendedJobAnalysisTester()
    success = tester.run_extended_analysis()