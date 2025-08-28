#!/usr/bin/env python3
"""
JOB STATUS ANALYSIS TEST: Analyze the specific job and compare with other jobs
Job ID: c5e2575b-0896-4080-8be9-25ff9212d96d

This will test the specific job and also test a few other job IDs to understand
if this is a specific job issue or a general system issue.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class JobStatusAnalyzer:
    def __init__(self):
        self.api_base = API_BASE
        self.target_job_id = "c5e2575b-0896-4080-8be9-25ff9212d96d"
        
    def test_job_status(self, job_id, description=""):
        """Test a specific job status"""
        print(f"🔍 Testing Job: {job_id} {description}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{job_id}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            print(f"   Response time: {response_time:.2f}s")
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Job ID: {data.get('job_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Progress: {data.get('progress')}%")
                print(f"   Message: {data.get('message')}")
                
                # Additional fields
                for field in ['created_at', 'updated_at', 'output_files', 'estimated_time']:
                    if field in data and data[field]:
                        print(f"   {field}: {data[field]}")
                
                return True, data
            elif response.status_code == 404:
                print("   ❌ Job not found (404)")
                return False, None
            elif response.status_code == 504:
                print("   ❌ Gateway timeout (504)")
                return False, None
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                return False, None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False, None
        
        print()
    
    def test_multiple_job_checks(self):
        """Test the target job multiple times to see if progress changes"""
        print("🎯 MULTIPLE CHECKS OF TARGET JOB")
        print("=" * 60)
        
        results = []
        for i in range(1, 4):
            print(f"Check #{i}:")
            success, data = self.test_job_status(self.target_job_id, f"(Check #{i})")
            if success and data:
                results.append({
                    'check': i,
                    'progress': data.get('progress'),
                    'status': data.get('status'),
                    'timestamp': datetime.now().isoformat()
                })
            print()
            
            if i < 3:  # Don't wait after the last check
                print("   ⏳ Waiting 10 seconds...")
                time.sleep(10)
        
        # Analyze results
        if results:
            print("📊 PROGRESS ANALYSIS:")
            progresses = [r['progress'] for r in results if r['progress'] is not None]
            
            if len(set(progresses)) > 1:
                print(f"   ✅ Progress changed: {progresses}")
                print("   🎉 Job is actively processing!")
            else:
                print(f"   ⚠️  Progress stable at: {progresses[0] if progresses else 'N/A'}%")
                if progresses and progresses[0] == 25:
                    print("   🚨 Job appears stuck at 25%")
        
        return results
    
    def test_other_job_ids(self):
        """Test some other job IDs to see if the system is working generally"""
        print("🔍 TESTING OTHER JOB IDs FOR COMPARISON")
        print("=" * 60)
        
        # Test some other job IDs that might exist (from previous test results)
        other_job_ids = [
            "test-job-123",  # Common test job ID
            "81ccaaac-c506-40b5-8dc9-0ea774d2fa42",  # From previous test results
            "24955ecf-6152-435f-a392-5c0ee6b07916",  # From previous test results
            "d44d8e74-6915-49f2-b994-4b7260814fed",  # From previous test results
            "65992b78-4120-4a45-a4af-d8c835a58635",  # From previous test results
        ]
        
        working_jobs = 0
        total_jobs = len(other_job_ids)
        
        for job_id in other_job_ids:
            success, data = self.test_job_status(job_id, "(Comparison)")
            if success:
                working_jobs += 1
            print()
        
        print(f"📊 COMPARISON RESULTS: {working_jobs}/{total_jobs} jobs responded")
        
        if working_jobs > 0:
            print("   ✅ Job status endpoint is working for other jobs")
            print("   🔍 Target job issue may be specific to that job")
        else:
            print("   ⚠️  No other jobs found - may be normal if jobs are cleaned up")
        
        return working_jobs > 0
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis of the job status system"""
        print("🚀 COMPREHENSIVE JOB STATUS ANALYSIS")
        print("=" * 80)
        print(f"Target Job ID: {self.target_job_id}")
        print(f"Backend URL: {self.api_base}")
        print("=" * 80)
        print()
        
        # Test 1: Multiple checks of target job
        target_results = self.test_multiple_job_checks()
        
        # Test 2: Test other job IDs
        other_jobs_working = self.test_other_job_ids()
        
        # Test 3: Final assessment
        print("🎯 FINAL ASSESSMENT")
        print("=" * 60)
        
        if target_results:
            latest_result = target_results[-1]
            progress = latest_result.get('progress')
            status = latest_result.get('status')
            
            print(f"Target Job Status: {status}")
            print(f"Target Job Progress: {progress}%")
            
            if progress == 25:
                print()
                print("🚨 CRITICAL FINDING: Job stuck at 25%")
                print("   Possible causes:")
                print("   1. FFmpeg Lambda not actually processing the job")
                print("   2. Job queue processor didn't successfully invoke FFmpeg")
                print("   3. Large video file requiring more processing time")
                print("   4. FFmpeg Lambda timeout or resource constraints")
                print("   5. S3 permissions issues preventing file access")
                print()
                print("🔧 RECOMMENDATIONS:")
                print("   1. Check FFmpeg Lambda logs for this specific job")
                print("   2. Verify S3 bucket has the source video file")
                print("   3. Check if job queue processor actually invoked FFmpeg")
                print("   4. Monitor for longer period (10-15 minutes)")
                print("   5. Check S3 outputs directory for partial results")
            elif progress > 25:
                print(f"✅ Job is processing: Progress increased to {progress}%")
                print("🎉 FFmpeg Lambda is working correctly!")
            else:
                print(f"ℹ️  Job progress: {progress}% (status: {status})")
        else:
            print("❌ Could not get target job status")
        
        if other_jobs_working:
            print("✅ Job status system is working for other jobs")
        else:
            print("ℹ️  No other active jobs found for comparison")
        
        print()
        return target_results is not None and len(target_results) > 0

if __name__ == "__main__":
    analyzer = JobStatusAnalyzer()
    success = analyzer.run_comprehensive_analysis()
    
    if not success:
        exit(1)