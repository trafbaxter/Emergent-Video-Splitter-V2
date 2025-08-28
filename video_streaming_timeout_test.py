#!/usr/bin/env python3
"""
Video Streaming Endpoint Timeout Test
Quick test to verify if the S3 head_object() removal resolved the 504 timeout issue.

Test Requirements:
1. GET /api/video-stream/test-mkv-file.mkv (with dummy key to test endpoint speed)
2. Verify response time is under 5 seconds (not 29+ seconds)  
3. Check that response includes proper content_type field set to 'video/x-matroska' for MKV files
4. Confirm no 504 timeout errors
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration from .env file
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 10  # Set to 10 seconds to catch timeout issues quickly

class VideoStreamingTimeoutTester:
    def __init__(self):
        self.base_url = API_GATEWAY_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Dict = None, response_time: float = None):
        """Log test results with timing information"""
        status = "✅ PASS" if success else "❌ FAIL"
        timing_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{timing_info}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response': response_data,
            'response_time': response_time
        })
        print()

    def test_video_streaming_endpoint_timeout(self):
        """Test the video streaming endpoint for timeout resolution"""
        print("🔍 Testing Video Streaming Endpoint Timeout Fix...")
        
        # Test with MKV file to check content-type handling
        test_key = "test-mkv-file.mkv"
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/video-stream/{test_key}")
            end_time = time.time()
            response_time = end_time - start_time
            
            # Check if response time is under 5 seconds
            if response_time >= 5.0:
                self.log_test(
                    "Video Streaming Response Time",
                    False,
                    f"Response took {response_time:.2f}s (should be under 5s)",
                    response_time=response_time
                )
            else:
                self.log_test(
                    "Video Streaming Response Time",
                    True,
                    f"Response time acceptable: {response_time:.2f}s (under 5s threshold)",
                    response_time=response_time
                )
            
            # Check for 504 timeout errors
            if response.status_code == 504:
                self.log_test(
                    "No 504 Timeout Errors",
                    False,
                    f"Received 504 Gateway Timeout - S3 head_object() removal did not resolve the issue",
                    response.json() if response.content else {},
                    response_time=response_time
                )
                return
            else:
                self.log_test(
                    "No 504 Timeout Errors",
                    True,
                    f"No 504 timeout error (received HTTP {response.status_code})",
                    response_time=response_time
                )
            
            # Check response content and structure
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for content_type field
                    if 'content_type' in data:
                        content_type = data['content_type']
                        if content_type == 'video/x-matroska':
                            self.log_test(
                                "MKV Content-Type Handling",
                                True,
                                f"Correct content_type for MKV file: {content_type}",
                                response_time=response_time
                            )
                        else:
                            self.log_test(
                                "MKV Content-Type Handling",
                                False,
                                f"Incorrect content_type for MKV file: {content_type} (expected: video/x-matroska)",
                                data,
                                response_time=response_time
                            )
                    else:
                        self.log_test(
                            "MKV Content-Type Handling",
                            False,
                            "Missing content_type field in response",
                            data,
                            response_time=response_time
                        )
                    
                    # Check for expected streaming response fields
                    expected_fields = ['stream_url', 's3_key', 'expires_in']
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test(
                            "Video Streaming Response Structure",
                            True,
                            f"All expected fields present: {expected_fields}",
                            response_time=response_time
                        )
                        
                        # Verify stream_url is a valid AWS S3 URL
                        stream_url = data.get('stream_url', '')
                        if 'amazonaws.com' in stream_url and 'Signature' in stream_url:
                            self.log_test(
                                "Valid S3 Streaming URL",
                                True,
                                "Generated valid presigned S3 streaming URL",
                                response_time=response_time
                            )
                        else:
                            self.log_test(
                                "Valid S3 Streaming URL",
                                False,
                                f"Invalid S3 URL format: {stream_url[:100]}...",
                                response_time=response_time
                            )
                    else:
                        self.log_test(
                            "Video Streaming Response Structure",
                            False,
                            f"Missing required fields: {missing_fields}",
                            data,
                            response_time=response_time
                        )
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "Video Streaming Response Format",
                        False,
                        f"Invalid JSON response (HTTP {response.status_code})",
                        {"raw_response": response.text[:200]},
                        response_time=response_time
                    )
                    
            elif response.status_code == 404:
                # Expected for non-existent file, but should be fast
                self.log_test(
                    "Video Streaming Endpoint Accessibility",
                    True,
                    f"Endpoint accessible (404 for non-existent file is expected, response time: {response_time:.2f}s)",
                    response_time=response_time
                )
                
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    self.log_test(
                        "Video Streaming Internal Error",
                        False,
                        f"Internal server error: {error_data.get('error', 'Unknown error')}",
                        error_data,
                        response_time=response_time
                    )
                except:
                    self.log_test(
                        "Video Streaming Internal Error",
                        False,
                        "Internal server error with invalid JSON response",
                        {"raw_response": response.text[:200]},
                        response_time=response_time
                    )
            else:
                self.log_test(
                    "Video Streaming Endpoint Response",
                    False,
                    f"Unexpected HTTP status: {response.status_code}",
                    response.json() if response.content else {},
                    response_time=response_time
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Video Streaming Endpoint Timeout",
                False,
                f"Request timed out after {TIMEOUT}s - S3 head_object() removal did not resolve timeout issue"
            )
        except Exception as e:
            self.log_test(
                "Video Streaming Endpoint Error",
                False,
                f"Unexpected error: {str(e)}"
            )

    def test_video_metadata_endpoint_timeout(self):
        """Test the video metadata endpoint for timeout resolution"""
        print("🔍 Testing Video Metadata Endpoint Timeout Fix...")
        
        try:
            metadata_data = {
                "s3_key": "test-mkv-file.mkv"
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/get-video-info", json=metadata_data)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Check if response time is under 5 seconds
            if response_time >= 5.0:
                self.log_test(
                    "Video Metadata Response Time",
                    False,
                    f"Response took {response_time:.2f}s (should be under 5s)",
                    response_time=response_time
                )
            else:
                self.log_test(
                    "Video Metadata Response Time",
                    True,
                    f"Response time acceptable: {response_time:.2f}s (under 5s threshold)",
                    response_time=response_time
                )
            
            # Check for 504 timeout errors
            if response.status_code == 504:
                self.log_test(
                    "Video Metadata No 504 Timeout",
                    False,
                    f"Received 504 Gateway Timeout - S3 head_object() removal did not resolve the issue",
                    response.json() if response.content else {},
                    response_time=response_time
                )
            else:
                self.log_test(
                    "Video Metadata No 504 Timeout",
                    True,
                    f"No 504 timeout error (received HTTP {response.status_code})",
                    response_time=response_time
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Video Metadata Endpoint Timeout",
                False,
                f"Request timed out after {TIMEOUT}s - S3 head_object() removal did not resolve timeout issue"
            )
        except Exception as e:
            self.log_test(
                "Video Metadata Endpoint Error",
                False,
                f"Unexpected error: {str(e)}"
            )

    def run_timeout_tests(self):
        """Run focused timeout tests"""
        print("=" * 80)
        print("🚀 VIDEO STREAMING TIMEOUT FIX VALIDATION")
        print("=" * 80)
        print(f"Testing API Gateway URL: {self.base_url}")
        print(f"Timeout threshold: {TIMEOUT}s")
        print(f"Expected response time: < 5s")
        print()
        
        # Run focused tests
        self.test_video_streaming_endpoint_timeout()
        self.test_video_metadata_endpoint_timeout()
        
        # Summary
        print("=" * 80)
        print("📊 TIMEOUT FIX TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Response time analysis
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            print(f"📈 RESPONSE TIME ANALYSIS:")
            print(f"   Average: {avg_response_time:.2f}s")
            print(f"   Maximum: {max_response_time:.2f}s")
            print(f"   Under 5s threshold: {'✅ YES' if max_response_time < 5.0 else '❌ NO'}")
            print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    timing = f" ({result['response_time']:.2f}s)" if result['response_time'] else ""
                    print(f"   • {result['test']}{timing}: {result['details']}")
            print()
        
        # Conclusion
        print("💡 CONCLUSION:")
        timeout_fixed = not any('504' in r['details'] or 'timeout' in r['details'].lower() for r in self.test_results if not r['success'])
        fast_responses = all(r['response_time'] < 5.0 for r in self.test_results if r['response_time'] is not None)
        
        if timeout_fixed and fast_responses:
            print("   ✅ SUCCESS: S3 head_object() removal appears to have resolved the timeout issue")
            print("   ✅ All responses are under 5 seconds")
            print("   ✅ No 504 Gateway Timeout errors detected")
        elif timeout_fixed and not fast_responses:
            print("   ⚠️  PARTIAL: No 504 errors but some responses still slow")
            print("   ⚠️  Further optimization may be needed")
        else:
            print("   ❌ FAILED: Timeout issue persists despite S3 head_object() removal")
            print("   ❌ Additional debugging required")
        
        print()
        print("=" * 80)
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = VideoStreamingTimeoutTester()
    passed, failed = tester.run_timeout_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)