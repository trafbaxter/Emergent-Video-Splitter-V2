#!/usr/bin/env python3
"""
VIDEO SPLITTING FIXES VERIFICATION TEST
Tests the two specific fixes mentioned in the review request:
1. Download API fix - should return HTTP 200 with download_url instead of HTTP 500
2. Duration Metadata fix - job status should preserve duration, start_time, end_time, s3_key
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from existing configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class ReviewFixesTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # Specific job ID from review request
        self.job_id = "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5"
        self.filename = "33749042-9f5e-4fcf-a6ef-4cecbe9c99c5_part_001.mkv"
        
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
        
    def test_download_api_fix(self):
        """Test Fix 1: Download API - Should return HTTP 200 with download_url instead of HTTP 500"""
        print("🔍 Testing Download API Fix...")
        
        download_url = f"{self.api_base}/api/download/{self.job_id}/{self.filename}"
        
        try:
            start_time = time.time()
            response = requests.get(download_url, timeout=30)
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code (should be 200, not 500)
            if response.status_code == 200:
                success_criteria.append("✅ HTTP 200 status (not 500 error)")
            elif response.status_code == 500:
                success_criteria.append("❌ HTTP 500 error (fix not working)")
            else:
                success_criteria.append(f"⚠️ HTTP {response.status_code} (unexpected status)")
            
            # Check response content
            try:
                data = response.json()
                
                # Check for download_url in response
                if 'download_url' in data:
                    success_criteria.append("✅ download_url present in response")
                    
                    # Validate download_url format
                    download_url_value = data['download_url']
                    if download_url_value and isinstance(download_url_value, str) and len(download_url_value) > 10:
                        success_criteria.append("✅ download_url has valid format")
                    else:
                        success_criteria.append(f"❌ download_url invalid: {download_url_value}")
                else:
                    success_criteria.append("❌ download_url missing from response")
                
                # Check for other expected fields
                if 'filename' in data:
                    success_criteria.append("✅ filename present")
                if 's3_key' in data:
                    success_criteria.append("✅ s3_key present")
                    
            except json.JSONDecodeError:
                success_criteria.append("❌ Invalid JSON response")
                success_criteria.append(f"Response text: {response.text[:200]}")
            
            # Check response time
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"⚠️ Response time: {response_time:.2f}s (≥10s)")
            
            # Check CORS headers
            cors_headers = response.headers.get('Access-Control-Allow-Origin')
            if cors_headers:
                success_criteria.append(f"✅ CORS headers present: {cors_headers}")
            else:
                success_criteria.append("⚠️ No CORS headers")
            
            all_success = response.status_code == 200 and 'download_url' in (data if 'data' in locals() else {})
            details = "; ".join(success_criteria)
            
            self.log_test("Download API Fix", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("Download API Fix", False, f"Request failed: {str(e)}")
            return False
    
    def test_duration_metadata_fix(self):
        """Test Fix 2: Duration Metadata - Job status should preserve duration, start_time, end_time, s3_key"""
        print("🔍 Testing Duration Metadata Fix...")
        
        job_status_url = f"{self.api_base}/api/job-status/{self.job_id}"
        
        try:
            start_time = time.time()
            response = requests.get(job_status_url, timeout=30)
            response_time = time.time() - start_time
            
            success_criteria = []
            
            # Check status code
            if response.status_code == 200:
                success_criteria.append("✅ HTTP 200 status")
            else:
                success_criteria.append(f"❌ HTTP {response.status_code} status")
            
            # Check response content
            try:
                data = response.json()
                
                # Check for results array
                if 'results' in data and isinstance(data['results'], list):
                    success_criteria.append("✅ results array present")
                    
                    results = data['results']
                    if len(results) > 0:
                        success_criteria.append(f"✅ {len(results)} result(s) in array")
                        
                        # Check first result for required metadata fields
                        first_result = results[0]
                        
                        # Check for duration
                        if 'duration' in first_result:
                            duration = first_result['duration']
                            if isinstance(duration, (int, float)) and duration > 0:
                                success_criteria.append(f"✅ duration present: {duration}s")
                            else:
                                success_criteria.append(f"⚠️ duration present but invalid: {duration}")
                        else:
                            success_criteria.append("❌ duration missing from results")
                        
                        # Check for start_time
                        if 'start_time' in first_result:
                            start_time_val = first_result['start_time']
                            success_criteria.append(f"✅ start_time present: {start_time_val}")
                        else:
                            success_criteria.append("❌ start_time missing from results")
                        
                        # Check for end_time
                        if 'end_time' in first_result:
                            end_time_val = first_result['end_time']
                            success_criteria.append(f"✅ end_time present: {end_time_val}")
                        else:
                            success_criteria.append("❌ end_time missing from results")
                        
                        # Check for s3_key (full S3 path)
                        if 's3_key' in first_result:
                            s3_key = first_result['s3_key']
                            if s3_key and isinstance(s3_key, str) and len(s3_key) > 10:
                                success_criteria.append(f"✅ s3_key present: {s3_key[:50]}...")
                            else:
                                success_criteria.append(f"⚠️ s3_key present but invalid: {s3_key}")
                        else:
                            success_criteria.append("❌ s3_key missing from results")
                            
                    else:
                        success_criteria.append("❌ results array is empty")
                else:
                    success_criteria.append("❌ results array missing or invalid")
                
                # Check job status
                if 'status' in data:
                    status = data['status']
                    success_criteria.append(f"✅ job status: {status}")
                
                # Check progress
                if 'progress' in data:
                    progress = data['progress']
                    success_criteria.append(f"✅ progress: {progress}%")
                    
            except json.JSONDecodeError:
                success_criteria.append("❌ Invalid JSON response")
                success_criteria.append(f"Response text: {response.text[:200]}")
            
            # Check response time
            if response_time < 10.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<10s)")
            else:
                success_criteria.append(f"⚠️ Response time: {response_time:.2f}s (≥10s)")
            
            # Check CORS headers
            cors_headers = response.headers.get('Access-Control-Allow-Origin')
            if cors_headers:
                success_criteria.append(f"✅ CORS headers present: {cors_headers}")
            else:
                success_criteria.append("⚠️ No CORS headers")
            
            # Determine success based on key criteria
            has_results = 'data' in locals() and 'results' in data and len(data['results']) > 0
            has_duration = has_results and 'duration' in data['results'][0]
            has_times = has_results and 'start_time' in data['results'][0] and 'end_time' in data['results'][0]
            has_s3_key = has_results and 's3_key' in data['results'][0]
            
            all_success = response.status_code == 200 and has_duration and has_times and has_s3_key
            details = "; ".join(success_criteria)
            
            self.log_test("Duration Metadata Fix", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            self.log_test("Duration Metadata Fix", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all review fixes tests"""
        print("🚀 REVIEW FIXES VERIFICATION TEST")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Job ID: {self.job_id}")
        print(f"Test File: {self.filename}")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        test_results.append(self.test_download_api_fix())
        test_results.append(self.test_duration_metadata_fix())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 REVIEW FIXES TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate == 100:
            print("🎉 ALL REVIEW FIXES VERIFIED SUCCESSFULLY!")
            success_criteria_met = [
                "✅ Fix 1: Download API returns HTTP 200 with download_url (not HTTP 500)",
                "✅ Fix 2: Job status preserves duration, start_time, end_time, s3_key metadata"
            ]
        else:
            print("⚠️  SOME REVIEW FIXES NOT WORKING - Review issues above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        if success_rate == 100:
            for criterion in success_criteria_met:
                print(criterion)
        
        print()
        print("EXPECTED OUTCOMES:")
        print("✅ Fix 1: Download path changed from results/{job_id}/ to outputs/{job_id}/")
        print("✅ Fix 2: Main Lambda no longer overwrites detailed FFmpeg results")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = ReviewFixesTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)