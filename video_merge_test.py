#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
import os
import tempfile

class VideoMergeAPITester:
    def __init__(self, base_url="https://video-merge-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.job_id = None
        self.video_ids = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        # Don't set Content-Type for file uploads
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    self.log(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    self.log(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}")
            return False, {}

    def create_test_video_file(self, filename="test_video.mp4", size_mb=1):
        """Create a small test video file"""
        # Create a minimal MP4 file header for testing
        mp4_header = bytes([
            # ftyp box
            0x00, 0x00, 0x00, 0x20,  # box size
            0x66, 0x74, 0x79, 0x70,  # 'ftyp'
            0x69, 0x73, 0x6F, 0x6D,  # major brand 'isom'
            0x00, 0x00, 0x02, 0x00,  # minor version
            0x69, 0x73, 0x6F, 0x6D,  # compatible brand 'isom'
            0x69, 0x73, 0x6F, 0x32,  # compatible brand 'iso2'
            0x61, 0x76, 0x63, 0x31,  # compatible brand 'avc1'
            0x6D, 0x70, 0x34, 0x31,  # compatible brand 'mp41'
            
            # mdat box with minimal data
            0x00, 0x00, 0x00, 0x10,  # box size
            0x6D, 0x64, 0x61, 0x74,  # 'mdat'
            0x00, 0x00, 0x00, 0x00,  # minimal data
            0x00, 0x00, 0x00, 0x00   # minimal data
        ])
        
        # Pad to desired size
        padding_size = (size_mb * 1024 * 1024) - len(mp4_header)
        if padding_size > 0:
            padding = b'\x00' * padding_size
            content = mp4_header + padding
        else:
            content = mp4_header
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(content)
        temp_file.close()
        
        return temp_file.name

    def test_create_merge_job(self):
        """Test creating a new merge job"""
        success, response = self.run_test(
            "Create Merge Job",
            "POST",
            "api/merge/create-job",
            200
        )
        
        if success and 'job_id' in response:
            self.job_id = response['job_id']
            self.log(f"   Job ID: {self.job_id}")
            return True
        return False

    def test_upload_video_for_merge(self, video_number=1):
        """Test uploading a video for merging"""
        if not self.job_id:
            self.log("❌ No job ID available for video upload")
            return False
        
        # Create test video file
        test_file_path = self.create_test_video_file(f"test_video_{video_number}.mp4")
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': (f"test_video_{video_number}.mp4", f, 'video/mp4')}
                
                success, response = self.run_test(
                    f"Upload Video {video_number}",
                    "POST",
                    f"api/merge/upload-video/{self.job_id}",
                    200,
                    files=files
                )
                
                if success and 'video_id' in response:
                    self.video_ids.append(response['video_id'])
                    self.log(f"   Video ID: {response['video_id']}")
                    return True
                return False
        finally:
            # Clean up temp file
            try:
                os.unlink(test_file_path)
            except:
                pass

    def test_reorder_videos(self):
        """Test reordering videos in merge job"""
        if not self.job_id or len(self.video_ids) < 2:
            self.log("❌ Need at least 2 videos to test reordering")
            return False
        
        # Reverse the order of videos
        reorder_data = []
        for i, video_id in enumerate(reversed(self.video_ids)):
            reorder_data.append({
                "video_id": video_id,
                "order": i
            })
        
        success, response = self.run_test(
            "Reorder Videos",
            "PUT",
            f"api/merge/reorder-videos/{self.job_id}",
            200,
            data=reorder_data
        )
        
        return success

    def test_get_merge_status(self):
        """Test getting merge job status"""
        if not self.job_id:
            self.log("❌ No job ID available for status check")
            return False
        
        success, response = self.run_test(
            "Get Merge Status",
            "GET",
            f"api/merge/status/{self.job_id}",
            200
        )
        
        if success:
            self.log(f"   Status: {response.get('status', 'unknown')}")
            self.log(f"   Progress: {response.get('progress', 0)}%")
            self.log(f"   Videos: {len(response.get('videos', []))}")
        
        return success

    def test_start_merge(self):
        """Test starting the merge process"""
        if not self.job_id or len(self.video_ids) < 2:
            self.log("❌ Need at least 2 videos to start merge")
            return False
        
        merge_config = {
            "output_format": "mp4",
            "quality_mode": "auto",
            "preserve_audio": True,
            "transition_duration": 0.0
        }
        
        success, response = self.run_test(
            "Start Merge Process",
            "POST",
            f"api/merge/start/{self.job_id}",
            200,
            data=merge_config
        )
        
        return success

    def test_remove_video(self):
        """Test removing a video from merge job"""
        if not self.job_id or not self.video_ids:
            self.log("❌ No videos available to remove")
            return False
        
        # Remove the last video
        video_to_remove = self.video_ids[-1]
        
        success, response = self.run_test(
            "Remove Video",
            "DELETE",
            f"api/merge/remove-video/{self.job_id}/{video_to_remove}",
            200
        )
        
        if success:
            self.video_ids.remove(video_to_remove)
        
        return success

    def test_list_merge_jobs(self):
        """Test listing merge jobs"""
        success, response = self.run_test(
            "List Merge Jobs",
            "GET",
            "api/merge/jobs?limit=10",
            200
        )
        
        if success:
            jobs = response.get('jobs', [])
            self.log(f"   Found {len(jobs)} jobs")
        
        return success

    def test_cleanup_merge_job(self):
        """Test cleaning up merge job"""
        if not self.job_id:
            self.log("❌ No job ID available for cleanup")
            return False
        
        success, response = self.run_test(
            "Cleanup Merge Job",
            "DELETE",
            f"api/merge/cleanup/{self.job_id}",
            200
        )
        
        return success

    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        # Test root endpoint
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "api/",
            200
        )
        
        return success

def main():
    """Main test function"""
    print("🎬 Video Merge API Testing Suite")
    print("=" * 50)
    
    tester = VideoMergeAPITester()
    
    # Test basic connectivity
    if not tester.test_basic_endpoints():
        print("❌ Basic connectivity failed. Stopping tests.")
        return 1
    
    # Test merge workflow
    print("\n📋 Testing Video Merge Workflow:")
    print("-" * 30)
    
    # 1. Create merge job
    if not tester.test_create_merge_job():
        print("❌ Failed to create merge job. Stopping tests.")
        return 1
    
    # 2. Upload multiple videos
    for i in range(1, 4):  # Upload 3 test videos
        if not tester.test_upload_video_for_merge(i):
            print(f"❌ Failed to upload video {i}")
            break
    
    # 3. Test status check
    tester.test_get_merge_status()
    
    # 4. Test reordering (if we have enough videos)
    if len(tester.video_ids) >= 2:
        tester.test_reorder_videos()
    
    # 5. Test removing a video
    if len(tester.video_ids) > 2:
        tester.test_remove_video()
    
    # 6. Test status after removal
    tester.test_get_merge_status()
    
    # 7. Test starting merge (if we have enough videos)
    if len(tester.video_ids) >= 2:
        tester.test_start_merge()
        
        # Wait a bit and check status
        print("\n⏳ Waiting 5 seconds to check merge progress...")
        time.sleep(5)
        tester.test_get_merge_status()
    
    # 8. Test listing jobs
    tester.test_list_merge_jobs()
    
    # 9. Cleanup (optional - comment out if you want to keep the job for manual testing)
    # tester.test_cleanup_merge_job()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())