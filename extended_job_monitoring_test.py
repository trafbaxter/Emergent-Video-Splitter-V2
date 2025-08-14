#!/usr/bin/env python3
"""
EXTENDED JOB MONITORING TEST: Monitor the specific job for longer period
Job ID: c5e2575b-0896-4080-8be9-25ff9212d96d

This will monitor the job for a longer period to see if progress actually changes
and also check if we can get more detailed information about the processing.
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class ExtendedJobMonitor:
    def __init__(self):
        self.api_base = API_BASE
        self.job_id = "c5e2575b-0896-4080-8be9-25ff9212d96d"
        self.monitoring_results = []
        
    def check_job_status(self, check_number):
        """Check job status and return detailed information"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/job-status/{self.job_id}",
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'check_number': check_number,
                    'timestamp': datetime.now().isoformat(),
                    'response_time': response_time,
                    'job_id': data.get('job_id'),
                    'status': data.get('status'),
                    'progress': data.get('progress'),
                    'message': data.get('message'),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at'),
                    'output_files': data.get('output_files'),
                    'estimated_time': data.get('estimated_time'),
                    'raw_response': data
                }
                
                self.monitoring_results.append(result)
                
                print(f"Check #{check_number} ({response_time:.2f}s):")
                print(f"  Status: {data.get('status')}")
                print(f"  Progress: {data.get('progress')}%")
                print(f"  Message: {data.get('message')}")
                if data.get('output_files'):
                    print(f"  Output Files: {data.get('output_files')}")
                if data.get('estimated_time'):
                    print(f"  Estimated Time: {data.get('estimated_time')}")
                print()
                
                return True, data
                
            else:
                print(f"Check #{check_number}: HTTP {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            print(f"Check #{check_number}: Error - {str(e)}")
            return False, None
    
    def monitor_job_extended(self, duration_minutes=5, check_interval_seconds=30):
        """Monitor the job for an extended period"""
        print(f"🔍 EXTENDED JOB MONITORING: {self.job_id}")
        print(f"Duration: {duration_minutes} minutes, Check interval: {check_interval_seconds} seconds")
        print("=" * 80)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        check_number = 1
        
        while time.time() < end_time:
            success, data = self.check_job_status(check_number)
            
            if success and data:
                # Check if job is completed
                status = data.get('status')
                if status in ['completed', 'failed', 'error']:
                    print(f"🎯 JOB FINISHED: Status changed to '{status}'")
                    break
                
                # Check if progress changed significantly
                progress = data.get('progress')
                if progress and progress > 25:
                    print(f"🎉 PROGRESS CHANGED: Now at {progress}%!")
            
            check_number += 1
            
            # Wait for next check
            if time.time() < end_time:
                print(f"⏳ Waiting {check_interval_seconds} seconds for next check...")
                time.sleep(check_interval_seconds)
        
        print("=" * 80)
        print("📊 MONITORING SUMMARY")
        print("=" * 80)
        
        if self.monitoring_results:
            print(f"Total checks: {len(self.monitoring_results)}")
            print()
            
            # Progress analysis
            progresses = [r['progress'] for r in self.monitoring_results if r['progress'] is not None]
            statuses = [r['status'] for r in self.monitoring_results if r['status']]
            
            if progresses:
                print("Progress over time:")
                for i, result in enumerate(self.monitoring_results):
                    timestamp = result['timestamp'].split('T')[1][:8]  # Just time part
                    print(f"  {timestamp}: {result['progress']}% ({result['status']})")
                
                print()
                
                if len(set(progresses)) > 1:
                    print(f"✅ PROGRESS CHANGED: {min(progresses)}% → {max(progresses)}%")
                    print("🎉 FFmpeg Lambda is actively processing the video!")
                else:
                    print(f"⚠️  PROGRESS STABLE: Remained at {progresses[0]}%")
                    if progresses[0] == 25:
                        print("   This suggests the job may be stuck or processing very slowly")
                    else:
                        print("   This may be normal depending on video size and processing stage")
            
            # Status analysis
            if statuses:
                unique_statuses = list(set(statuses))
                if len(unique_statuses) == 1:
                    print(f"Status: Consistent '{unique_statuses[0]}'")
                else:
                    print(f"Status changes: {' → '.join(unique_statuses)}")
            
            # Output files analysis
            output_files_found = any(r.get('output_files') for r in self.monitoring_results)
            if output_files_found:
                print("✅ Output files detected - processing is generating results")
                for result in self.monitoring_results:
                    if result.get('output_files'):
                        print(f"  Files: {result['output_files']}")
            else:
                print("ℹ️  No output files detected yet")
            
            print()
            
            # Final assessment
            latest_result = self.monitoring_results[-1]
            print("FINAL ASSESSMENT:")
            
            if latest_result['progress'] and latest_result['progress'] > 25:
                print("✅ Job is actively processing - progress increased from 25%")
            elif latest_result['status'] == 'processing' and latest_result['progress'] == 25:
                print("⚠️  Job appears stuck at 25% - may need investigation")
                print("   Possible causes:")
                print("   - Large video file taking longer than expected")
                print("   - FFmpeg Lambda timeout or resource issues")
                print("   - Job queue processing delays")
            elif latest_result['status'] in ['completed', 'failed', 'error']:
                print(f"✅ Job finished with status: {latest_result['status']}")
            else:
                print(f"ℹ️  Job status: {latest_result['status']}, Progress: {latest_result['progress']}%")
        
        return len(self.monitoring_results) > 0

if __name__ == "__main__":
    monitor = ExtendedJobMonitor()
    
    # Monitor for 3 minutes with 20-second intervals
    success = monitor.monitor_job_extended(duration_minutes=3, check_interval_seconds=20)
    
    if not success:
        exit(1)