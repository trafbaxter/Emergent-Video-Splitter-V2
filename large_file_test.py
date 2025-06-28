#!/usr/bin/env python3
import os
import requests
import time
import json
import unittest
import tempfile
import psutil
import sys
import io
from pathlib import Path
import shutil
import random

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# Ensure the URL has no trailing slash
BACKEND_URL = BACKEND_URL.rstrip('/')
API_URL = f"{BACKEND_URL}/api"

print(f"Using API URL: {API_URL}")

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

class LargeFileUploadTest(unittest.TestCase):
    """Test suite for large file upload handling in Video Splitter Backend API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.job_ids = []
        cls.test_files = []
        
        # Create test directory if it doesn't exist
        cls.test_dir = Path("/tmp/large_file_tests")
        cls.test_dir.mkdir(exist_ok=True)
        
        # Create test files of different sizes
        cls.create_test_files()
    
    @classmethod
    def create_test_files(cls):
        """Create test files of different sizes for testing"""
        # Small test file (1MB)
        small_file = cls.test_dir / "small_test_video.mp4"
        cls.create_dummy_video_file(small_file, 1 * 1024 * 1024)
        cls.test_files.append(small_file)
        
        # Medium test file (10MB)
        medium_file = cls.test_dir / "medium_test_video.mp4"
        cls.create_dummy_video_file(medium_file, 10 * 1024 * 1024)
        cls.test_files.append(medium_file)
        
        # Large test file (50MB) - large enough to test chunking but not too large for the test
        large_file = cls.test_dir / "large_test_video.mp4"
        cls.create_dummy_video_file(large_file, 50 * 1024 * 1024)
        cls.test_files.append(large_file)
        
        print(f"Created test files: {[str(f) for f in cls.test_files]}")
    
    @classmethod
    def create_dummy_video_file(cls, file_path, size_bytes):
        """Create a dummy video file with MP4 header and random data"""
        # MP4 file header (simplified)
        mp4_header = bytes.fromhex('00 00 00 18 66 74 79 70 6D 70 34 32 00 00 00 00 6D 70 34 32 69 73 6F 6D')
        
        with open(file_path, 'wb') as f:
            # Write MP4 header
            f.write(mp4_header)
            
            # Calculate remaining bytes needed
            remaining_bytes = size_bytes - len(mp4_header)
            
            # Write random data in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            while remaining_bytes > 0:
                write_size = min(chunk_size, remaining_bytes)
                f.write(random.randbytes(write_size))
                remaining_bytes -= write_size
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Clean up any remaining job data
        for job_id in cls.job_ids:
            try:
                requests.delete(f"{API_URL}/cleanup/{job_id}")
            except Exception as e:
                print(f"Error cleaning up job {job_id}: {e}")
        
        # Clean up test files
        for file_path in cls.test_files:
            if file_path.exists():
                file_path.unlink()
        
        # Remove test directory
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    def test_01_small_file_upload(self):
        """Test small file upload to establish baseline"""
        print("\n=== Testing small file upload (1MB) ===")
        
        file_path = self.test_files[0]
        file_size = file_path.stat().st_size
        print(f"Uploading file: {file_path}, size: {format_size(file_size)}")
        
        # Measure memory before upload
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        
        # Upload file
        start_time = time.time()
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", files=files)
        
        upload_time = time.time() - start_time
        
        # Measure memory after upload
        mem_after = process.memory_info().rss
        mem_diff = mem_after - mem_before
        
        self.assertEqual(response.status_code, 200, f"Upload failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIn('job_id', data, "Response missing job_id")
        self.assertIn('video_info', data, "Response missing video_info")
        
        # Store job ID for later cleanup
        job_id = data['job_id']
        self.__class__.job_ids.append(job_id)
        
        print(f"Successfully uploaded small file, job_id: {job_id}")
        print(f"Upload time: {upload_time:.2f} seconds")
        print(f"Memory usage increase: {format_size(mem_diff)}")
        
        # Verify file size in response
        self.assertEqual(data['size'], file_size, "File size in response doesn't match actual file size")
        
        return job_id
    
    def test_02_medium_file_upload(self):
        """Test medium file upload"""
        print("\n=== Testing medium file upload (10MB) ===")
        
        file_path = self.test_files[1]
        file_size = file_path.stat().st_size
        print(f"Uploading file: {file_path}, size: {format_size(file_size)}")
        
        # Measure memory before upload
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        
        # Upload file
        start_time = time.time()
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", files=files)
        
        upload_time = time.time() - start_time
        
        # Measure memory after upload
        mem_after = process.memory_info().rss
        mem_diff = mem_after - mem_before
        
        self.assertEqual(response.status_code, 200, f"Upload failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIn('job_id', data, "Response missing job_id")
        self.assertIn('video_info', data, "Response missing video_info")
        
        # Store job ID for later cleanup
        job_id = data['job_id']
        self.__class__.job_ids.append(job_id)
        
        print(f"Successfully uploaded medium file, job_id: {job_id}")
        print(f"Upload time: {upload_time:.2f} seconds")
        print(f"Memory usage increase: {format_size(mem_diff)}")
        
        # Verify file size in response
        self.assertEqual(data['size'], file_size, "File size in response doesn't match actual file size")
        
        return job_id
    
    def test_03_large_file_upload(self):
        """Test large file upload to verify chunked processing"""
        print("\n=== Testing large file upload (50MB) ===")
        
        file_path = self.test_files[2]
        file_size = file_path.stat().st_size
        print(f"Uploading file: {file_path}, size: {format_size(file_size)}")
        
        # Measure memory before upload
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        
        # Upload file
        start_time = time.time()
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", files=files)
        
        upload_time = time.time() - start_time
        
        # Measure memory after upload
        mem_after = process.memory_info().rss
        mem_diff = mem_after - mem_before
        
        self.assertEqual(response.status_code, 200, f"Upload failed with status {response.status_code}: {response.text}")
        
        data = response.json()
        self.assertIn('job_id', data, "Response missing job_id")
        self.assertIn('video_info', data, "Response missing video_info")
        
        # Store job ID for later cleanup
        job_id = data['job_id']
        self.__class__.job_ids.append(job_id)
        self.__class__.large_file_job_id = job_id
        
        print(f"Successfully uploaded large file, job_id: {job_id}")
        print(f"Upload time: {upload_time:.2f} seconds")
        print(f"Memory usage increase: {format_size(mem_diff)}")
        
        # Verify file size in response
        self.assertEqual(data['size'], file_size, "File size in response doesn't match actual file size")
        
        # Verify memory usage is reasonable (should not increase by more than file size)
        # This test verifies that the file is not loaded entirely into memory
        self.assertLess(mem_diff, file_size, 
                        "Memory usage increased by more than file size, suggesting non-streaming upload")
        
        return job_id
    
    def test_04_verify_large_file_processing(self):
        """Test that large files can be processed correctly"""
        print("\n=== Testing large file processing ===")
        
        job_id = getattr(self.__class__, 'large_file_job_id', None)
        if not job_id:
            self.skipTest("Large file upload test did not complete successfully")
        
        # Configure time-based splitting
        split_config = {
            "method": "time_based",
            "time_points": [0, 1.0],  # Split at 1 second (dummy video doesn't have real duration)
            "preserve_quality": True,
            "output_format": "mp4",
            "subtitle_sync_offset": 0.0
        }
        
        response = requests.post(f"{API_URL}/split-video/{job_id}", json=split_config)
        self.assertEqual(response.status_code, 200, f"Split request failed with status {response.status_code}: {response.text}")
        
        print("Split request accepted, waiting for processing...")
        
        # Wait for processing to complete
        max_wait_time = 120  # seconds (longer for large file)
        start_time = time.time()
        completed = False
        
        # Track progress updates to verify progress tracking works
        progress_updates = []
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{API_URL}/job-status/{job_id}")
            self.assertEqual(response.status_code, 200, f"Status check failed with status {response.status_code}: {response.text}")
            
            status_data = response.json()
            current_progress = status_data['progress']
            current_status = status_data['status']
            
            print(f"Job status: {current_status}, progress: {current_progress}%")
            progress_updates.append((current_status, current_progress))
            
            if current_status == 'completed':
                completed = True
                break
            elif current_status == 'failed':
                self.fail(f"Job failed: {status_data.get('error_message', 'Unknown error')}")
            
            time.sleep(2)
        
        self.assertTrue(completed, f"Job did not complete within {max_wait_time} seconds")
        
        # Verify progress tracking worked
        self.assertTrue(len(progress_updates) > 1, "Not enough progress updates received")
        
        # Verify final progress is 100%
        self.assertEqual(progress_updates[-1][1], 100.0, "Final progress is not 100%")
        
        # Verify split results
        response = requests.get(f"{API_URL}/job-status/{job_id}")
        status_data = response.json()
        
        self.assertIn('splits', status_data, "Response missing splits information")
        self.assertTrue(len(status_data['splits']) > 0, "No split files generated")
        
        print(f"Successfully split large video into {len(status_data['splits'])} parts")
        for i, split in enumerate(status_data['splits']):
            print(f"Split {i+1}: {split['file']}")
    
    def test_05_file_size_formatting(self):
        """Test file size formatting for different size ranges"""
        print("\n=== Testing file size formatting ===")
        
        # Test various file sizes
        test_sizes = [
            (500, "500.00 B"),
            (1023, "1023.00 B"),
            (1024, "1.00 KB"),
            (1536, "1.50 KB"),
            (1024 * 1024, "1.00 MB"),
            (1024 * 1024 * 1.5, "1.50 MB"),
            (1024 * 1024 * 1024, "1.00 GB"),
            (1024 * 1024 * 1024 * 1.5, "1.50 GB"),
        ]
        
        for size_bytes, expected_format in test_sizes:
            formatted = format_size(size_bytes)
            print(f"{size_bytes} bytes -> {formatted}")
            self.assertEqual(formatted, expected_format, 
                            f"Size formatting incorrect for {size_bytes} bytes")
        
        print("File size formatting works correctly for all size ranges")
    
    def test_06_cleanup_large_files(self):
        """Test cleanup works properly for large files"""
        print("\n=== Testing cleanup for large files ===")
        
        job_id = getattr(self.__class__, 'large_file_job_id', None)
        if not job_id:
            self.skipTest("Large file upload test did not complete successfully")
        
        # Verify job exists before cleanup
        response = requests.get(f"{API_URL}/job-status/{job_id}")
        self.assertEqual(response.status_code, 200, "Job not found before cleanup")
        
        # Clean up the job
        response = requests.delete(f"{API_URL}/cleanup/{job_id}")
        self.assertEqual(response.status_code, 200, f"Cleanup failed with status {response.status_code}: {response.text}")
        
        print(f"Successfully cleaned up large file job: {job_id}")
        
        # Verify job no longer exists
        response = requests.get(f"{API_URL}/job-status/{job_id}")
        self.assertEqual(response.status_code, 404, "Job still exists after cleanup")
        
        # Remove from job_ids list to avoid double cleanup
        if job_id in self.__class__.job_ids:
            self.__class__.job_ids.remove(job_id)

if __name__ == "__main__":
    # Install psutil if not already installed
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    unittest.main(verbosity=2)