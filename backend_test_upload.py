#!/usr/bin/env python3
import os
import requests
import json
import sys

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# Ensure the URL has no trailing slash
BACKEND_URL = BACKEND_URL.rstrip('/')
API_URL = f"{BACKEND_URL}/api"

print(f"Testing API connectivity to: {API_URL}")

def test_upload_endpoint():
    """Test the upload-video endpoint with a small test file"""
    print("\n=== Testing upload-video endpoint ===")
    
    # Create a small test video file
    test_file_path = "/tmp/test_video.mp4"
    with open(test_file_path, 'wb') as f:
        # Write a minimal valid MP4 file header
        f.write(bytes([
            0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70,
            0x6D, 0x70, 0x34, 0x32, 0x00, 0x00, 0x00, 0x00,
            0x6D, 0x70, 0x34, 0x32, 0x69, 0x73, 0x6F, 0x6D,
            0x00, 0x00, 0x00, 0x08, 0x66, 0x72, 0x65, 0x65,
            0x00, 0x00, 0x00, 0x08, 0x6D, 0x64, 0x61, 0x74
        ]))
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_video.mp4', f, 'video/mp4')}
            response = requests.post(f"{API_URL}/upload-video", files=files)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload endpoint test PASSED")
            return True
        else:
            print("❌ Upload endpoint test FAILED - Received non-200 status code")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload endpoint test FAILED - Connection error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    print("=== Backend API Upload Test ===")
    
    # Test basic connectivity
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Basic connectivity test: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print("✅ Basic connectivity test PASSED")
        else:
            print("❌ Basic connectivity test FAILED")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Basic connectivity test FAILED - Connection error: {e}")
        sys.exit(1)
    
    # Test upload endpoint
    upload_success = test_upload_endpoint()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Upload endpoint: {'✅ PASSED' if upload_success else '❌ FAILED'}")
    
    if upload_success:
        print("\n✅ All tests PASSED")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED")
        sys.exit(1)