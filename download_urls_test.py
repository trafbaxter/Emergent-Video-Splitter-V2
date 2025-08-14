#!/usr/bin/env python3
"""
Download URLs Test - Verify download endpoint provides URLs for completed job
Tests the download endpoint to get actual download URLs for the split video files
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from AuthContext.js
API_BASE = 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod'

class DownloadUrlsTester:
    def __init__(self):
        self.api_base = API_BASE
        self.test_results = []
        # Specific job ID from review request
        self.target_job_id = "7e38b588-fe5a-46d5-b0c9-e876f3293e2a"
        # File names from job status response
        self.file_names = [
            "7e38b588-fe5a-46d5-b0c9-e876f3293e2a_part_001.mkv",
            "7e38b588-fe5a-46d5-b0c9-e876f3293e2a_part_002.mkv"
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
        
    def test_download_endpoint_file1(self):
        """Test download endpoint for first split video file"""
        filename = self.file_names[0]
        print(f"🔍 Testing Download Endpoint for: {filename}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/download/{self.target_job_id}/{filename}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for download_url
                download_url = data.get('download_url')
                if download_url and isinstance(download_url, str) and 'http' in download_url:
                    success_criteria.append(f"✅ download_url present: {download_url[:50]}...")
                else:
                    success_criteria.append(f"❌ download_url missing or invalid: {download_url}")
                
                # Check for filename
                returned_filename = data.get('filename')
                if returned_filename == filename:
                    success_criteria.append(f"✅ filename matches: {returned_filename}")
                else:
                    success_criteria.append(f"❌ filename mismatch: {returned_filename}")
                
                # Check for expires_in
                expires_in = data.get('expires_in')
                if expires_in and isinstance(expires_in, int) and expires_in > 0:
                    success_criteria.append(f"✅ expires_in: {expires_in} seconds")
                else:
                    success_criteria.append(f"❌ expires_in missing or invalid: {expires_in}")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test(f"Download URL - File 1", all_success, details, response_time)
                
                # Print full response for debugging
                print("📋 Download Response Data (File 1):")
                print(json.dumps(data, indent=2))
                print()
                
                return all_success
                
            else:
                self.log_test(f"Download URL - File 1", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"Download URL - File 1", False, f"Request failed: {str(e)}")
            return False
    
    def test_download_endpoint_file2(self):
        """Test download endpoint for second split video file"""
        filename = self.file_names[1]
        print(f"🔍 Testing Download Endpoint for: {filename}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_base}/api/download/{self.target_job_id}/{filename}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            success_criteria = []
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for download_url
                download_url = data.get('download_url')
                if download_url and isinstance(download_url, str) and 'http' in download_url:
                    success_criteria.append(f"✅ download_url present: {download_url[:50]}...")
                else:
                    success_criteria.append(f"❌ download_url missing or invalid: {download_url}")
                
                # Check for filename
                returned_filename = data.get('filename')
                if returned_filename == filename:
                    success_criteria.append(f"✅ filename matches: {returned_filename}")
                else:
                    success_criteria.append(f"❌ filename mismatch: {returned_filename}")
                
                # Check for expires_in
                expires_in = data.get('expires_in')
                if expires_in and isinstance(expires_in, int) and expires_in > 0:
                    success_criteria.append(f"✅ expires_in: {expires_in} seconds")
                else:
                    success_criteria.append(f"❌ expires_in missing or invalid: {expires_in}")
                
                # Check CORS headers
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    success_criteria.append(f"✅ CORS headers present: {cors_headers}")
                else:
                    success_criteria.append("❌ CORS headers missing")
                
                # Check response time
                if response_time < 5.0:
                    success_criteria.append(f"✅ Response time: {response_time:.2f}s (<5s)")
                else:
                    success_criteria.append(f"❌ Response time: {response_time:.2f}s (≥5s)")
                
                all_success = all("✅" in criterion for criterion in success_criteria)
                details = "; ".join(success_criteria)
                
                self.log_test(f"Download URL - File 2", all_success, details, response_time)
                
                # Print full response for debugging
                print("📋 Download Response Data (File 2):")
                print(json.dumps(data, indent=2))
                print()
                
                return all_success
                
            else:
                self.log_test(f"Download URL - File 2", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"Download URL - File 2", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all download URL tests"""
        print("🚀 DOWNLOAD URLS TEST - Verify Download Endpoints")
        print("=" * 80)
        print(f"Backend URL: {self.api_base}")
        print(f"Target Job ID: {self.target_job_id}")
        print("Expected Results:")
        print("  - Download URLs for both split video files")
        print("  - Proper response format with download_url, filename, expires_in")
        print("=" * 80)
        print()
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_download_endpoint_file1())
        test_results.append(self.test_download_endpoint_file2())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print("=" * 80)
        print("🎯 DOWNLOAD URLS TEST RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Check SUCCESS CRITERIA
        if success_rate == 100:
            print("🎉 SUCCESS CRITERIA VERIFICATION:")
            print("✅ Download endpoints respond correctly")
            print("✅ Download URLs provided for both split video files")
            print("✅ Proper response format with all required fields")
            print("✅ CORS headers working properly")
            print()
            print("EXPECTED OUTCOME ACHIEVED:")
            print("✅ Users can download the 2 split video files via provided URLs")
        else:
            print("⚠️ SOME SUCCESS CRITERIA NOT MET:")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['details']}")
            
            print("\nEXPECTED OUTCOME NOT ACHIEVED:")
            print("❌ Users may not be able to download split video files properly")
        
        print()
        return success_rate == 100

if __name__ == "__main__":
    tester = DownloadUrlsTester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)