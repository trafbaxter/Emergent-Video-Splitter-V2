#!/usr/bin/env python3

import requests
import sys
import os
import tempfile
import time
import subprocess
from datetime import datetime

class VideoMergerAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.current_job_id = None

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def create_test_video_file(self, filename="test_video.mp4", duration=1):
        """Create a valid test video file using ffmpeg"""
        import subprocess
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.close()
        
        try:
            # Create a simple test video using ffmpeg
            cmd = [
                'ffmpeg', '-f', 'lavfi', 
                '-i', f'testsrc=duration={duration}:size=320x240:rate=1',
                '-c:v', 'libx264', '-t', str(duration), 
                '-pix_fmt', 'yuv420p', temp_file.name, '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"❌ Failed to create test video: {result.stderr}")
                return None
                
            return temp_file.name
        except Exception as e:
            self.log(f"❌ Error creating test video: {e}")
            return None

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        success, _ = self.run_test(
            "Basic API Connectivity",
            "GET",
            "",
            200
        )
        return success

    def test_create_merge_job(self):
        """Test creating a new merge job"""
        success, response = self.run_test(
            "Create Merge Job",
            "POST",
            "create-merge-job",
            200
        )
        
        if success and 'job_id' in response:
            self.current_job_id = response['job_id']
            self.log(f"   Created job ID: {self.current_job_id}")
            return True
        return False

    def test_upload_merge_videos(self):
        """Test uploading multiple videos to merge job"""
        if not self.current_job_id:
            self.log("❌ No job ID available for upload test")
            return False

        # Create test video files
        video_files = []
        for i in range(3):  # Create 3 test videos
            video_path = self.create_test_video_file(f"test_video_{i+1}.mp4", duration=1)
            if video_path:
                video_files.append(video_path)
            else:
                self.log(f"❌ Failed to create test video {i+1}")
                return False

        upload_success = True
        
        for i, video_path in enumerate(video_files):
            try:
                with open(video_path, 'rb') as f:
                    files = {'file': (f"test_video_{i+1}.mp4", f, 'video/mp4')}
                    success, response = self.run_test(
                        f"Upload Video {i+1}",
                        "POST",
                        f"upload-merge-video/{self.current_job_id}",
                        200,
                        files=files
                    )
                    if not success:
                        upload_success = False
            except Exception as e:
                self.log(f"❌ Error uploading video {i+1}: {e}")
                upload_success = False
            finally:
                # Clean up temp file
                try:
                    os.unlink(video_path)
                except:
                    pass

        return upload_success

    def test_merge_job_status(self):
        """Test getting merge job status"""
        if not self.current_job_id:
            self.log("❌ No job ID available for status test")
            return False

        success, response = self.run_test(
            "Get Merge Job Status",
            "GET",
            f"merge-job-status/{self.current_job_id}",
            200
        )
        
        if success:
            self.log(f"   Job status: {response.get('status', 'unknown')}")
            self.log(f"   Input files: {len(response.get('input_files', []))}")
        
        return success

    def test_reorder_merge_files(self):
        """Test reordering files in merge job"""
        if not self.current_job_id:
            self.log("❌ No job ID available for reorder test")
            return False

        # First get current file list
        success, response = self.run_test(
            "Get Files for Reorder",
            "GET",
            f"merge-job-status/{self.current_job_id}",
            200
        )
        
        if not success or not response.get('input_files'):
            self.log("❌ No files available to reorder")
            return False

        # Create reversed order
        files = response['input_files']
        file_order = [f['filename'] for f in reversed(files)]
        
        success, _ = self.run_test(
            "Reorder Merge Files",
            "POST",
            f"reorder-merge-files/{self.current_job_id}",
            200,
            data=file_order
        )
        
        return success

    def test_start_merge(self):
        """Test starting the merge process"""
        if not self.current_job_id:
            self.log("❌ No job ID available for merge test")
            return False

        merge_config = {
            "output_format": "mp4",
            "preserve_quality": True,
            "audio_handling": "concat",
            "include_subtitles": True,
            "video_file_order": []
        }

        success, response = self.run_test(
            "Start Merge Process",
            "POST",
            f"start-merge/{self.current_job_id}",
            200,
            data=merge_config
        )
        
        if success:
            self.log("   Merge process started, waiting for completion...")
            # Wait a bit for processing to start
            time.sleep(2)
        
        return success

    def test_merge_progress_polling(self):
        """Test polling merge progress until completion"""
        if not self.current_job_id:
            self.log("❌ No job ID available for progress test")
            return False

        max_polls = 30  # Maximum 60 seconds
        poll_count = 0
        
        while poll_count < max_polls:
            success, response = self.run_test(
                f"Poll Progress ({poll_count + 1})",
                "GET",
                f"merge-job-status/{self.current_job_id}",
                200
            )
            
            if not success:
                return False
            
            status = response.get('status', 'unknown')
            progress = response.get('progress', 0)
            
            self.log(f"   Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                self.log("✅ Merge completed successfully!")
                return True
            elif status == 'failed':
                error_msg = response.get('error_message', 'Unknown error')
                self.log(f"❌ Merge failed: {error_msg}")
                return False
            
            poll_count += 1
            time.sleep(2)
        
        self.log("❌ Merge did not complete within timeout")
        return False

    def test_download_merged_video(self):
        """Test downloading the merged video"""
        if not self.current_job_id:
            self.log("❌ No job ID available for download test")
            return False

        try:
            url = f"{self.base_url}/api/download-merged/{self.current_job_id}"
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                self.tests_passed += 1
                self.log("✅ Download Merged Video - Status: 200")
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                self.log(f"   Content-Type: {content_type}")
                
                # Check if we got some data
                content_length = response.headers.get('content-length', '0')
                self.log(f"   Content-Length: {content_length} bytes")
                
                return True
            else:
                self.log(f"❌ Download Merged Video - Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Download Merged Video - Error: {str(e)}")
            return False
        finally:
            self.tests_run += 1

    def test_cleanup_merge_job(self):
        """Test cleaning up merge job"""
        if not self.current_job_id:
            self.log("❌ No job ID available for cleanup test")
            return False

        success, _ = self.run_test(
            "Cleanup Merge Job",
            "DELETE",
            f"cleanup-merge/{self.current_job_id}",
            200
        )
        
        if success:
            self.current_job_id = None
        
        return success

    def test_error_handling(self):
        """Test various error conditions"""
        error_tests_passed = 0
        total_error_tests = 0
        
        # Test invalid job ID
        total_error_tests += 1
        success, _ = self.run_test(
            "Invalid Job ID Status",
            "GET",
            "merge-job-status/invalid-job-id",
            404
        )
        if success:
            error_tests_passed += 1

        # Test starting merge with insufficient files
        total_error_tests += 1
        # Create job with only one file
        success, response = self.run_test(
            "Create Job for Error Test",
            "POST",
            "create-merge-job",
            200
        )
        
        if success:
            test_job_id = response['job_id']
            
            # Try to start merge without enough files
            merge_config = {
                "output_format": "mp4",
                "preserve_quality": True,
                "audio_handling": "concat",
                "include_subtitles": True,
                "video_file_order": []
            }
            
            success, _ = self.run_test(
                "Start Merge with Insufficient Files",
                "POST",
                f"start-merge/{test_job_id}",
                400
            )
            if success:
                error_tests_passed += 1
            
            # Clean up test job
            self.run_test(
                "Cleanup Error Test Job",
                "DELETE",
                f"cleanup-merge/{test_job_id}",
                200
            )

        self.log(f"Error handling tests: {error_tests_passed}/{total_error_tests} passed")
        return error_tests_passed == total_error_tests

def main():
    """Main test execution"""
    print("🚀 Starting Video Merger API Tests")
    print("=" * 50)
    
    tester = VideoMergerAPITester()
    
    # Test sequence
    test_sequence = [
        ("Basic Connectivity", tester.test_basic_connectivity),
        ("Create Merge Job", tester.test_create_merge_job),
        ("Upload Videos", tester.test_upload_merge_videos),
        ("Check Job Status", tester.test_merge_job_status),
        ("Reorder Files", tester.test_reorder_merge_files),
        ("Start Merge", tester.test_start_merge),
        ("Monitor Progress", tester.test_merge_progress_polling),
        ("Download Result", tester.test_download_merged_video),
        ("Cleanup Job", tester.test_cleanup_merge_job),
        ("Error Handling", tester.test_error_handling)
    ]
    
    failed_tests = []
    
    for test_name, test_func in test_sequence:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if not test_func():
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    # Final results
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"  - {test}")
        return 1
    else:
        print("\n🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())