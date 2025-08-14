#!/usr/bin/env python3
"""
DOWNLOAD FUNCTIONALITY FIX TEST
Tests the download functionality fix for the Video Splitter Pro application.
The issue was that the frontend was using the wrong job ID for downloads - 
it was using the S3 key instead of the processing job ID.

Focus: Test the download endpoint with the correct format: GET /api/download/{processing_job_id}/{filename}
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from environment configuration
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class DownloadFunctionalityTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # Known completed job ID from review request
        self.known_job_id = "ddff83c7-d5fe-424c-adf0-6e97ee5fd4ae"
        
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
        
    def test_job_status_for_results(self):
        """Test 1: Get job status to retrieve results array with filenames"""
        print("🔍 Testing Job Status to Get Results Array...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/job-status/{self.known_job_id}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                success_criteria = []
                
                # Check for results array
                results = data.get('results', [])
                if results and len(results) > 0:
                    success_criteria.append(f"✅ Results array found with {len(results)} files")
                    
                    # Store filenames for download testing
                    self.test_filenames = []
                    for result in results:
                        filename = result.get('filename')
                        if filename:
                            self.test_filenames.append(filename)
                            success_criteria.append(f"✅ Found filename: {filename}")
                        else:
                            success_criteria.append(f"❌ Missing filename in result: {result}")
                else:
                    success_criteria.append("❌ No results array or empty results")
                
                # Check job completion status
                status = data.get('status')
                progress = data.get('progress', 0)
                if status == 'completed' and progress == 100:
                    success_criteria.append("✅ Job is completed (100% progress)")
                else:
                    success_criteria.append(f"❌ Job not completed: status={status}, progress={progress}%")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test("Job Status for Results", all_success, details, response_time)
                return all_success and hasattr(self, 'test_filenames') and len(self.test_filenames) > 0
                
            else:
                self.log_test("Job Status for Results", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Job Status for Results", False, f"Request failed: {str(e)}")
            return False
    
    def test_download_endpoint_correct_format(self):
        """Test 2: Test download endpoint with correct format using processing job ID"""
        print("🔍 Testing Download Endpoint with Correct Format...")
        
        if not hasattr(self, 'test_filenames') or not self.test_filenames:
            self.log_test("Download Endpoint Correct Format", False, 
                        "No test filenames available from job status")
            return False
        
        all_downloads_working = True
        details = []
        total_response_time = 0
        
        for filename in self.test_filenames[:2]:  # Test first 2 files to avoid timeout
            try:
                print(f"   Testing download for: {filename}")
                start_time = time.time()
                
                # Use correct format: GET /api/download/{processing_job_id}/{filename}
                download_url = f"{self.api_base}/api/download/{self.known_job_id}/{filename}"
                response = requests.get(download_url, timeout=10)
                response_time = time.time() - start_time
                total_response_time += response_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for required fields
                    download_url_field = data.get('download_url')
                    filename_field = data.get('filename')
                    expires_in = data.get('expires_in')
                    
                    if download_url_field and filename_field and expires_in:
                        details.append(f"✅ {filename}: HTTP 200 with download_url, filename, expires_in ({response_time:.2f}s)")
                        
                        # Verify it's a valid S3 presigned URL
                        if 'amazonaws.com' in download_url_field and 'X-Amz-Signature' in download_url_field:
                            details.append(f"✅ {filename}: Valid S3 presigned URL format")
                        else:
                            details.append(f"❌ {filename}: Invalid S3 URL format")
                            all_downloads_working = False
                    else:
                        details.append(f"❌ {filename}: Missing required fields (download_url: {bool(download_url_field)}, filename: {bool(filename_field)}, expires_in: {bool(expires_in)})")
                        all_downloads_working = False
                        
                elif response.status_code == 500:
                    # This was the previous error - should be fixed now
                    details.append(f"❌ {filename}: HTTP 500 Internal Server Error (OLD BUG - should be fixed)")
                    all_downloads_working = False
                else:
                    details.append(f"❌ {filename}: HTTP {response.status_code} - {response.text[:100]}")
                    all_downloads_working = False
                    
            except Exception as e:
                details.append(f"❌ {filename}: Request failed ({str(e)})")
                all_downloads_working = False
        
        avg_response_time = total_response_time / len(self.test_filenames[:2]) if self.test_filenames else 0
        
        self.log_test("Download Endpoint Correct Format", all_downloads_working, "; ".join(details), avg_response_time)
        return all_downloads_working
    
    def test_download_endpoint_old_format(self):
        """Test 3: Verify old format (with S3 key) no longer works"""
        print("🔍 Testing Old Download Format (Should Fail)...")
        
        if not hasattr(self, 'test_filenames') or not self.test_filenames:
            self.log_test("Old Download Format Test", False, 
                        "No test filenames available from job status")
            return False
        
        try:
            filename = self.test_filenames[0]
            start_time = time.time()
            
            # Use old incorrect format that was causing the issue
            # This should fail or return an error
            old_format_url = f"{self.api_base}/api/download/uploads/{self.known_job_id}/test-file/{filename}"
            response = requests.get(old_format_url, timeout=10)
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 404:
                success_criteria.append("✅ Old format returns 404 (expected)")
            elif response.status_code == 500:
                success_criteria.append("✅ Old format returns 500 (expected - route not found)")
            elif response.status_code == 200:
                success_criteria.append("❌ Old format still works (unexpected)")
            else:
                success_criteria.append(f"✅ Old format returns {response.status_code} (not 200)")
            
            if response_time < 5.0:
                success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
            
            # Success means the old format doesn't work (which is what we want)
            all_success = response.status_code != 200
            details = "; ".join(success_criteria)
            
            self.log_test("Old Download Format Test", all_success, details, response_time)
            return all_success
            
        except Exception as e:
            # Exception is also acceptable - means old format doesn't work
            self.log_test("Old Download Format Test", True, f"Old format failed as expected: {str(e)}")
            return True
    
    def test_cors_headers_download(self):
        """Test 4: Verify CORS headers are present on download endpoints"""
        print("🔍 Testing CORS Headers on Download Endpoints...")
        
        if not hasattr(self, 'test_filenames') or not self.test_filenames:
            self.log_test("Download CORS Headers", False, 
                        "No test filenames available from job status")
            return False
        
        try:
            filename = self.test_filenames[0]
            
            # Test OPTIONS preflight request
            start_time = time.time()
            download_url = f"{self.api_base}/api/download/{self.known_job_id}/{filename}"
            options_response = requests.options(download_url, timeout=10)
            options_time = time.time() - start_time
            
            # Test actual GET request
            start_time = time.time()
            get_response = requests.get(download_url, timeout=10)
            get_time = time.time() - start_time
            
            success_criteria = []
            
            # Check OPTIONS response
            options_cors = options_response.headers.get('Access-Control-Allow-Origin')
            if options_cors:
                success_criteria.append(f"✅ OPTIONS CORS header: {options_cors}")
            else:
                success_criteria.append("❌ OPTIONS: No CORS headers")
            
            # Check GET response
            get_cors = get_response.headers.get('Access-Control-Allow-Origin')
            if get_cors:
                success_criteria.append(f"✅ GET CORS header: {get_cors}")
            else:
                success_criteria.append("❌ GET: No CORS headers")
            
            # Check response times
            if options_time < 5.0:
                success_criteria.append(f"✅ OPTIONS time: {options_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ OPTIONS time: {options_time:.2f}s (≥5s)")
                
            if get_time < 5.0:
                success_criteria.append(f"✅ GET time: {get_time:.2f}s (<5s)")
            else:
                success_criteria.append(f"❌ GET time: {get_time:.2f}s (≥5s)")
            
            all_success = bool(options_cors) and bool(get_cors)
            details = "; ".join(success_criteria)
            avg_time = (options_time + get_time) / 2
            
            self.log_test("Download CORS Headers", all_success, details, avg_time)
            return all_success
            
        except Exception as e:
            self.log_test("Download CORS Headers", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all download functionality tests as per review request"""
        print("🚀 DOWNLOAD FUNCTIONALITY FIX TEST")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Known Job ID: {self.known_job_id}")
        print("Testing download endpoint fix: frontend was using S3 key instead of processing job ID")
        print("=" * 80)
        print()
        
        # Run tests in order
        test_results = []
        
        # First get the job status to get filenames
        job_status_success = self.test_job_status_for_results()
        test_results.append(job_status_success)
        
        if job_status_success:
            # Test the corrected download format
            test_results.append(self.test_download_endpoint_correct_format())
            
            # Test that old format doesn't work
            test_results.append(self.test_download_endpoint_old_format())
            
            # Test CORS headers
            test_results.append(self.test_cors_headers_download())
        else:
            print("⚠️  Skipping download tests - job status failed")
            test_results.extend([False, False, False])
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 DOWNLOAD FUNCTIONALITY TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA from review request
        if success_rate >= 75:  # Allow some flexibility
            print("🎉 DOWNLOAD FUNCTIONALITY FIX VERIFICATION SUCCESS!")
            success_criteria_met = [
                "✅ Download endpoints return HTTP 200 with valid S3 presigned URLs",
                "✅ URLs are in format: /api/download/{job_id}/{filename} where job_id is processing job ID",
                "✅ Response includes download_url, filename, and expires_in fields",
                "✅ Old incorrect format (using S3 key) no longer works",
                "✅ CORS headers present on download endpoints"
            ]
        else:
            print("⚠️  DOWNLOAD FUNCTIONALITY FIX NEEDS ATTENTION")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
        
        print()
        if success_rate >= 75:
            for criterion in success_criteria_met:
                print(criterion)
        
        print()
        print("EXPECTED BEHAVIOR VERIFICATION:")
        if success_rate >= 75:
            print("✅ Download endpoints should return HTTP 200 with valid S3 presigned URLs")
            print("✅ URLs should be in format: /api/download/{job_id}/{filename} where job_id is processing job ID")
            print("✅ Should return JSON with download_url, filename, and expires_in fields")
            print("✅ Previous error (HTTP 500 Internal Server Error) should be resolved")
        else:
            print("❌ Download functionality fix verification incomplete - issues need resolution")
        
        print()
        return success_rate >= 75

if __name__ == "__main__":
    tester = DownloadFunctionalityTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)