#!/usr/bin/env python3
"""
FINAL TEST: Verify split-video endpoint returns immediately with complete decoupling

CRITICAL OBJECTIVE:
Test that the split-video endpoint now returns HTTP 202 immediately (under 5 seconds) 
using the AWS-recommended complete decoupling pattern.

TEST:
1. POST to /api/split-video with exact payload from review request
2. MUST return HTTP 202 in under 5 seconds
3. MUST include CORS headers
4. MUST NOT timeout at 29 seconds

SUCCESS CRITERIA:
✅ HTTP 202 status (not 504 timeout)
✅ Response time < 5 seconds (not 29+ seconds)
✅ CORS headers present
✅ Job ID returned
✅ Status = "accepted" or "queued"
"""

import requests
import json
import time
import sys

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
TIMEOUT = 30

def test_split_video_immediate_response():
    """Test the exact payload from review request"""
    print("🚨 FINAL TEST: Split-video endpoint immediate response with complete decoupling")
    print("=" * 80)
    
    # Exact payload from review request
    payload = {
        "s3_key": "test-video.mp4",
        "method": "intervals", 
        "interval_duration": 300
    }
    
    print(f"📋 Testing with EXACT review request payload:")
    print(f"   {json.dumps(payload, indent=2)}")
    print()
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://working.tads-video-splitter.com'
        }
        
        print("🎯 Making POST request to /api/split-video...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_GATEWAY_URL}/api/split-video", 
            json=payload, 
            headers=headers,
            timeout=TIMEOUT
        )
        
        response_time = time.time() - start_time
        
        print(f"⏱️  Response time: {response_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        # Check CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        print(f"🌐 CORS Origin header: {cors_origin}")
        
        # Parse response
        try:
            data = response.json()
            job_id = data.get('job_id')
            status = data.get('status')
            
            print(f"📄 Response data:")
            print(f"   job_id: {job_id}")
            print(f"   status: {status}")
            print(f"   full response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response")
            data = {}
            job_id = None
            status = None
        
        print()
        print("📋 SUCCESS CRITERIA EVALUATION:")
        
        # Evaluate success criteria
        criteria = {
            'http_202': response.status_code == 202,
            'under_5_seconds': response_time < 5.0,
            'cors_headers': cors_origin is not None,
            'job_id_present': job_id is not None,
            'status_accepted_or_queued': status in ['accepted', 'queued'],
            'no_timeout': response.status_code != 504
        }
        
        for criterion, passed in criteria.items():
            status_icon = "✅" if passed else "❌"
            print(f"   {status_icon} {criterion.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
        
        print()
        
        # Overall assessment
        all_passed = all(criteria.values())
        
        if all_passed:
            print("🎉 SUCCESS: ALL CRITERIA MET!")
            print("   • HTTP 202 returned immediately")
            print("   • Response time under 5 seconds")
            print("   • CORS headers present")
            print("   • Job ID returned for tracking")
            print("   • Status indicates job accepted/queued")
            print("   • No timeout errors")
            print()
            print("✅ The AWS-recommended complete decoupling pattern is working perfectly!")
            print("✅ Users can now initiate video splitting without timeout issues!")
            return True
        else:
            failed_criteria = [k for k, v in criteria.items() if not v]
            print(f"❌ FAILURE: Some criteria not met: {failed_criteria}")
            
            if response.status_code == 504:
                print("🚨 CRITICAL: Still getting 504 Gateway Timeout!")
                print("   The endpoint is NOT using complete decoupling pattern")
                print("   It's still trying to process synchronously")
            elif response_time >= 5.0:
                print(f"🚨 CRITICAL: Response time {response_time:.2f}s exceeds 5s threshold!")
                print("   The endpoint is not returning immediately")
            elif not cors_origin:
                print("🚨 CRITICAL: Missing CORS headers!")
                print("   Browser requests will be blocked")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request timed out after {TIMEOUT}s")
        print("🚨 CRITICAL: Endpoint is not responding fast enough")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("FINAL TEST: Verify split-video endpoint returns immediately with complete decoupling")
    print("=" * 80)
    print(f"API Gateway URL: {API_GATEWAY_URL}")
    print()
    
    success = test_split_video_immediate_response()
    
    print("=" * 80)
    if success:
        print("🎉 FINAL TEST RESULT: COMPLETE SUCCESS!")
        print("The split-video endpoint is working as expected with complete decoupling.")
    else:
        print("❌ FINAL TEST RESULT: FAILURE!")
        print("The split-video endpoint still has issues that need investigation.")
    
    sys.exit(0 if success else 1)