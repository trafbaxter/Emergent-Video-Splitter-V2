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

def test_basic_connectivity():
    """Test basic connectivity to the API root endpoint"""
    print("\n=== Testing basic connectivity to /api/ endpoint ===")
    
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Basic connectivity test PASSED")
            return True
        else:
            print("❌ Basic connectivity test FAILED - Received non-200 status code")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Basic connectivity test FAILED - Connection error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers on API endpoints"""
    print("\n=== Testing CORS headers ===")
    
    try:
        # Send OPTIONS request to check CORS headers
        response = requests.options(f"{API_URL}/")
        print(f"Status code: {response.status_code}")
        print("Response headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        # Check for CORS headers
        has_cors_headers = (
            'Access-Control-Allow-Origin' in response.headers and
            'Access-Control-Allow-Methods' in response.headers and
            'Access-Control-Allow-Headers' in response.headers
        )
        
        if has_cors_headers:
            print("✅ CORS headers test PASSED")
            return True
        else:
            print("❌ CORS headers test FAILED - Missing required CORS headers")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS headers test FAILED - Connection error: {e}")
        return False

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

def test_request_details():
    """Test detailed request information to diagnose connectivity issues"""
    print("\n=== Testing request details ===")
    
    try:
        # Use a session to see more details
        session = requests.Session()
        
        # Make request with verbose output
        print(f"Making request to {API_URL}/")
        response = session.get(f"{API_URL}/", timeout=10)
        
        print(f"Request URL: {response.request.url}")
        print(f"Request method: {response.request.method}")
        print(f"Request headers:")
        for header, value in response.request.headers.items():
            print(f"  {header}: {value}")
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        print(f"Response content: {response.text}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        
        # Try to get more details about the connection error
        if isinstance(e, requests.exceptions.ConnectionError):
            print("Connection error details:")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error message: {str(e)}")
            
            # Try to extract the underlying error
            if e.__context__ is not None:
                print(f"  Underlying error: {type(e.__context__).__name__}: {str(e.__context__)}")
        
        return False

if __name__ == "__main__":
    print("=== Backend API Connectivity Test ===")
    
    # Run all tests
    basic_connectivity = test_basic_connectivity()
    
    if basic_connectivity:
        cors_headers = test_cors_headers()
        upload_endpoint = test_upload_endpoint()
    else:
        # If basic connectivity fails, run detailed request test
        print("\nBasic connectivity failed. Running detailed request test...")
        test_request_details()
        
        # Exit with error code
        sys.exit(1)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Basic connectivity: {'✅ PASSED' if basic_connectivity else '❌ FAILED'}")
    
    if basic_connectivity:
        print(f"CORS headers: {'✅ PASSED' if cors_headers else '❌ FAILED'}")
        print(f"Upload endpoint: {'✅ PASSED' if upload_endpoint else '❌ FAILED'}")
    
    # Exit with appropriate code
    if basic_connectivity and cors_headers and upload_endpoint:
        print("\n✅ All tests PASSED")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED")
        sys.exit(1)