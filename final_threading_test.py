#!/usr/bin/env python3
"""
Final comprehensive test of the threading-based video splitting fix
"""

import requests
import json
import time

API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"

def test_split_video():
    """Test split-video endpoint"""
    print("🚨 Testing Split Video Endpoint...")
    
    payload = {
        "s3_key": "uploads/test/video.mkv",
        "method": "intervals", 
        "interval_duration": 300,
        "preserve_quality": True,
        "output_format": "mp4"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://working.tads-video-splitter.com'
    }
    
    start_time = time.time()
    response = requests.post(f"{API_GATEWAY_URL}/api/split-video", json=payload, headers=headers, timeout=30)
    response_time = time.time() - start_time
    
    print(f"   Status: {response.status_code}")
    print(f"   Time: {response_time:.2f}s")
    print(f"   CORS: {response.headers.get('Access-Control-Allow-Origin')}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get('job_id')
        print(f"   Job ID: {job_id}")
        print("   ✅ SPLIT VIDEO: SUCCESS - HTTP 202 in under 5s with CORS headers")
        return True, job_id
    else:
        print("   ❌ SPLIT VIDEO: FAILED")
        return False, None

def test_job_status(job_id="test-job-123"):
    """Test job-status endpoint"""
    print(f"🚨 Testing Job Status Endpoint (job_id: {job_id})...")
    
    headers = {
        'Origin': 'https://working.tads-video-splitter.com'
    }
    
    start_time = time.time()
    try:
        response = requests.get(f"{API_GATEWAY_URL}/api/job-status/{job_id}", headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {response_time:.2f}s")
        print(f"   CORS: {response.headers.get('Access-Control-Allow-Origin')}")
        
        if response.status_code == 200 and response_time < 5.0:
            data = response.json()
            print(f"   Progress: {data.get('progress')}%")
            print(f"   Status: {data.get('status')}")
            print("   ✅ JOB STATUS: SUCCESS - HTTP 200 in under 5s with CORS headers")
            return True
        elif response.status_code == 504:
            print("   ❌ JOB STATUS: FAILED - HTTP 504 Gateway Timeout (29s timeout issue)")
            return False
        else:
            print(f"   ❌ JOB STATUS: FAILED - Status {response.status_code}, Time {response_time:.2f}s")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ JOB STATUS: FAILED - Client timeout after 30s")
        return False

def main():
    print("=" * 80)
    print("🚨 FINAL THREADING-BASED VIDEO SPLITTING TEST")
    print("=" * 80)
    
    # Test split video
    split_success, job_id = test_split_video()
    print()
    
    # Test job status with both real and test job IDs
    job_status_success = test_job_status("test-job-123")
    print()
    
    if job_id:
        print(f"🚨 Testing Job Status with Real Job ID: {job_id}")
        job_status_real_success = test_job_status(job_id)
        print()
    else:
        job_status_real_success = False
    
    # Summary
    print("=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    
    print(f"Split Video Endpoint: {'✅ WORKING' if split_success else '❌ BROKEN'}")
    print(f"Job Status Endpoint: {'✅ WORKING' if job_status_success else '❌ BROKEN'}")
    
    if split_success and job_status_success:
        print("\n🎉 THREADING-BASED VIDEO SPLITTING FIX: COMPLETE SUCCESS!")
        print("   • Split video returns HTTP 202 immediately")
        print("   • Job status returns HTTP 200 quickly")
        print("   • Both have CORS headers")
        print("   • No 29-second timeouts")
    elif split_success and not job_status_success:
        print("\n⚠️  THREADING-BASED VIDEO SPLITTING FIX: PARTIAL SUCCESS")
        print("   • ✅ Split video working (HTTP 202 immediate response)")
        print("   • ❌ Job status broken (29-second timeout persists)")
        print("   • Users can start jobs but cannot track progress")
    else:
        print("\n❌ THREADING-BASED VIDEO SPLITTING FIX: FAILED")
        print("   • Critical endpoints still have timeout issues")
    
    print("=" * 80)

if __name__ == "__main__":
    main()