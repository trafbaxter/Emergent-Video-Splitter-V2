#!/usr/bin/env python3
"""
Focused Video Processing Test - Test with proper request data
"""

import requests
import json
import time

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 15

def test_video_metadata_with_data():
    """Test video metadata with proper s3_key"""
    print("🔍 Testing Video Metadata with proper data...")
    
    session = requests.Session()
    session.timeout = TIMEOUT
    
    try:
        # Test with proper s3_key
        metadata_data = {
            "s3_key": "uploads/test-video.mp4"
        }
        
        start_time = time.time()
        response = session.post(f"{API_GATEWAY_URL}/api/get-video-info", json=metadata_data)
        response_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.content:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}")
        else:
            print("Empty response")
            
        if response.status_code == 200:
            print("✅ RESTORED: Video metadata endpoint working")
        elif response.status_code == 404:
            print("✅ RESTORED: Endpoint working (404 for non-existent file)")
        elif response.status_code == 504:
            print("❌ TIMEOUT: FFmpeg Lambda timing out")
        elif response.status_code == 501:
            print("❌ PLACEHOLDER: Still returns 501")
        else:
            print(f"❓ UNKNOWN: HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request timeout after {TIMEOUT}s")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_video_splitting_with_data():
    """Test video splitting with proper data"""
    print("\n🔍 Testing Video Splitting with proper data...")
    
    session = requests.Session()
    session.timeout = TIMEOUT
    
    try:
        # Test with proper split data
        split_data = {
            "s3_key": "uploads/test-video.mp4",
            "segments": [
                {
                    "start_time": "00:00:00",
                    "end_time": "00:00:30",
                    "output_name": "segment_1.mp4"
                }
            ]
        }
        
        start_time = time.time()
        response = session.post(f"{API_GATEWAY_URL}/api/split-video", json=split_data)
        response_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.content:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}")
        else:
            print("Empty response")
            
        if response.status_code == 202:
            print("✅ RESTORED: Video splitting now returns 202 (processing started)")
        elif response.status_code == 404:
            print("✅ RESTORED: Endpoint working (404 for non-existent file)")
        elif response.status_code == 504:
            print("❌ TIMEOUT: FFmpeg Lambda timing out")
        elif response.status_code == 501:
            print("❌ PLACEHOLDER: Still returns 501")
        else:
            print(f"❓ UNKNOWN: HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request timeout after {TIMEOUT}s")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_job_status():
    """Test job status endpoint"""
    print("\n🔍 Testing Job Status endpoint...")
    
    session = requests.Session()
    session.timeout = TIMEOUT
    
    try:
        job_id = "test-job-123"
        
        start_time = time.time()
        response = session.get(f"{API_GATEWAY_URL}/api/job-status/{job_id}")
        response_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.content:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}")
        else:
            print("Empty response")
            
        if response.status_code == 200:
            print("✅ RESTORED: Job status endpoint working")
        elif response.status_code == 404:
            print("✅ RESTORED: Endpoint working (404 for non-existent job)")
        elif response.status_code == 501:
            print("❌ PLACEHOLDER: Still returns 501")
        else:
            print(f"❓ UNKNOWN: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_download():
    """Test download endpoint"""
    print("\n🔍 Testing Download endpoint...")
    
    session = requests.Session()
    session.timeout = TIMEOUT
    
    try:
        job_id = "test-job-123"
        filename = "segment_1.mp4"
        
        start_time = time.time()
        response = session.get(f"{API_GATEWAY_URL}/api/download/{job_id}/{filename}")
        response_time = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.content:
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response Text: {response.text[:500]}")
        else:
            print("Empty response")
            
        if response.status_code == 200:
            print("✅ RESTORED: Download endpoint working")
        elif response.status_code == 404:
            print("✅ RESTORED: Endpoint working (404 for non-existent file)")
        elif response.status_code == 501:
            print("❌ PLACEHOLDER: Still returns 501")
        else:
            print(f"❓ UNKNOWN: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 FOCUSED VIDEO PROCESSING RESTORATION TEST")
    print("=" * 80)
    print(f"Testing API Gateway URL: {API_GATEWAY_URL}")
    print(f"Timeout: {TIMEOUT}s")
    print()
    
    test_video_metadata_with_data()
    test_video_splitting_with_data()
    test_job_status()
    test_download()
    
    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETE")
    print("=" * 80)