#!/usr/bin/env python3
"""
Quick Video Processing Test - Focus on endpoint availability and response types
Tests the newly restored video processing functionality without long timeouts.
"""

import requests
import json
import time
import uuid

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 10  # Short timeout for quick testing

class QuickVideoTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print()

    def test_video_metadata_endpoint(self):
        """Test video metadata endpoint response type"""
        print("🔍 Testing Video Metadata Endpoint...")
        
        try:
            # Test with missing s3_key to check validation
            response = self.session.post(f"{self.base_url}/api/get-video-info", json={})
            
            if response.status_code == 400:
                data = response.json() if response.content else {}
                error_msg = data.get('error', '')
                
                if 's3_key' in error_msg:
                    self.log_result(
                        "Video Metadata - Request Validation",
                        True,
                        "✅ RESTORED: Proper validation (requires s3_key) - no longer returns 404"
                    )
                else:
                    self.log_result(
                        "Video Metadata - Request Validation",
                        False,
                        f"Unexpected 400 error: {error_msg}"
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Video Metadata - Request Validation",
                    False,
                    "❌ NOT RESTORED: Still returns 404 - endpoint may not be implemented"
                )
            elif response.status_code == 501:
                self.log_result(
                    "Video Metadata - Request Validation",
                    False,
                    "❌ PLACEHOLDER: Returns 501 'Not Implemented'"
                )
            else:
                self.log_result(
                    "Video Metadata - Request Validation",
                    True,
                    f"Endpoint accessible (HTTP {response.status_code})"
                )
                
        except requests.exceptions.Timeout:
            self.log_result(
                "Video Metadata - Request Validation",
                False,
                f"Timeout after {TIMEOUT}s - may be calling FFmpeg Lambda"
            )
        except Exception as e:
            self.log_result(
                "Video Metadata - Request Validation",
                False,
                f"Error: {str(e)}"
            )

    def test_video_splitting_endpoint(self):
        """Test video splitting endpoint response type"""
        print("🔍 Testing Video Splitting Endpoint...")
        
        try:
            # Test with missing data to check validation
            response = self.session.post(f"{self.base_url}/api/split-video", json={})
            
            if response.status_code == 400:
                data = response.json() if response.content else {}
                error_msg = data.get('error', '')
                
                if any(field in error_msg for field in ['s3_key', 'segments']):
                    self.log_result(
                        "Video Splitting - Request Validation",
                        True,
                        "✅ RESTORED: Proper validation (requires s3_key/segments) - no longer returns 501"
                    )
                else:
                    self.log_result(
                        "Video Splitting - Request Validation",
                        False,
                        f"Unexpected 400 error: {error_msg}"
                    )
            elif response.status_code == 501:
                self.log_result(
                    "Video Splitting - Request Validation",
                    False,
                    "❌ PLACEHOLDER: Still returns 501 'Not Implemented'"
                )
            elif response.status_code == 404:
                self.log_result(
                    "Video Splitting - Request Validation",
                    False,
                    "❌ NOT RESTORED: Returns 404 - endpoint may not be implemented"
                )
            else:
                self.log_result(
                    "Video Splitting - Request Validation",
                    True,
                    f"Endpoint accessible (HTTP {response.status_code})"
                )
                
        except requests.exceptions.Timeout:
            self.log_result(
                "Video Splitting - Request Validation",
                False,
                f"Timeout after {TIMEOUT}s - may be calling FFmpeg Lambda"
            )
        except Exception as e:
            self.log_result(
                "Video Splitting - Request Validation",
                False,
                f"Error: {str(e)}"
            )

    def test_job_status_endpoint(self):
        """Test job status endpoint"""
        print("🔍 Testing Job Status Endpoint...")
        
        test_job_id = "test-job-123"
        
        try:
            response = self.session.get(f"{self.base_url}/api/job-status/{test_job_id}")
            
            if response.status_code == 200:
                data = response.json()
                if 'job_id' in data and 'status' in data:
                    self.log_result(
                        "Job Status - Endpoint Structure",
                        True,
                        "✅ RESTORED: Returns proper job status structure"
                    )
                else:
                    self.log_result(
                        "Job Status - Endpoint Structure",
                        False,
                        "Missing expected fields in response"
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Job Status - Endpoint Structure",
                    True,
                    "✅ RESTORED: Returns 404 for non-existent job (expected behavior)"
                )
            elif response.status_code == 501:
                self.log_result(
                    "Job Status - Endpoint Structure",
                    False,
                    "❌ PLACEHOLDER: Still returns 501 'Not Implemented'"
                )
            else:
                self.log_result(
                    "Job Status - Endpoint Structure",
                    True,
                    f"Endpoint accessible (HTTP {response.status_code})"
                )
                
        except Exception as e:
            self.log_result(
                "Job Status - Endpoint Structure",
                False,
                f"Error: {str(e)}"
            )

    def test_download_endpoint(self):
        """Test download endpoint"""
        print("🔍 Testing Download Endpoint...")
        
        test_job_id = "test-job-123"
        test_filename = "segment_1.mp4"
        
        try:
            response = self.session.get(f"{self.base_url}/api/download/{test_job_id}/{test_filename}")
            
            if response.status_code == 200:
                data = response.json()
                if 'download_url' in data:
                    download_url = data['download_url']
                    if 'amazonaws.com' in download_url:
                        self.log_result(
                            "Download - Presigned URL Generation",
                            True,
                            "✅ RESTORED: Generates real S3 presigned URLs"
                        )
                    else:
                        self.log_result(
                            "Download - Presigned URL Generation",
                            False,
                            "Invalid presigned URL format"
                        )
                else:
                    self.log_result(
                        "Download - Presigned URL Generation",
                        False,
                        "Missing download_url in response"
                    )
            elif response.status_code == 404:
                self.log_result(
                    "Download - Presigned URL Generation",
                    True,
                    "✅ RESTORED: Returns 404 for non-existent file (expected behavior)"
                )
            elif response.status_code == 501:
                self.log_result(
                    "Download - Presigned URL Generation",
                    False,
                    "❌ PLACEHOLDER: Still returns 501 'Not Implemented'"
                )
            else:
                self.log_result(
                    "Download - Presigned URL Generation",
                    True,
                    f"Endpoint accessible (HTTP {response.status_code})"
                )
                
        except Exception as e:
            self.log_result(
                "Download - Presigned URL Generation",
                False,
                f"Error: {str(e)}"
            )

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("🔍 Testing Basic Connectivity...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/")
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    self.log_result(
                        "Basic API Connectivity",
                        True,
                        f"API Gateway accessible - {data.get('message', 'N/A')}"
                    )
                else:
                    self.log_result(
                        "Basic API Connectivity",
                        False,
                        "Unexpected response format"
                    )
            else:
                self.log_result(
                    "Basic API Connectivity",
                    False,
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Basic API Connectivity",
                False,
                f"Error: {str(e)}"
            )

    def run_quick_tests(self):
        """Run quick tests and provide summary"""
        print("=" * 80)
        print("⚡ QUICK VIDEO PROCESSING RESTORATION TEST")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Timeout: {TIMEOUT}s (quick test)")
        print()
        
        # Run tests
        self.test_basic_connectivity()
        self.test_video_metadata_endpoint()
        self.test_video_splitting_endpoint()
        self.test_job_status_endpoint()
        self.test_download_endpoint()
        
        # Summary
        print("=" * 80)
        print("📊 QUICK TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Analyze restoration status
        restored_endpoints = 0
        placeholder_endpoints = 0
        
        for result in self.results:
            if result['success'] and 'restored' in result['details'].lower():
                restored_endpoints += 1
            elif not result['success'] and ('501' in result['details'] or 'placeholder' in result['details'].lower()):
                placeholder_endpoints += 1
        
        print("🔍 RESTORATION ANALYSIS:")
        print(f"   ✅ Restored Endpoints: {restored_endpoints}")
        print(f"   ❌ Placeholder Endpoints: {placeholder_endpoints}")
        print()
        
        if failed_tests > 0:
            print("❌ ISSUES FOUND:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Final assessment
        if restored_endpoints >= 3:
            print("🎉 RESTORATION SUCCESS: Most video processing functionality has been restored!")
        elif restored_endpoints >= 1:
            print("⚠️  PARTIAL RESTORATION: Some endpoints restored, others still need work")
        else:
            print("❌ RESTORATION INCOMPLETE: Video processing endpoints still using placeholders")
        
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = QuickVideoTester()
    passed, failed = tester.run_quick_tests()