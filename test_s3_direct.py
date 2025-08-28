#!/usr/bin/env python3
"""
Test direct S3 access and CORS for video streaming
"""

import boto3
import requests
import json
from botocore.exceptions import ClientError

S3_BUCKET_NAME = 'videosplitter-storage-1751560247'

def test_s3_direct_access():
    """Test direct S3 access and generate real presigned URLs"""
    s3_client = boto3.client('s3')
    
    print(f"🔍 Testing S3 Direct Access for bucket: {S3_BUCKET_NAME}")
    
    try:
        # List actual objects in the bucket
        print("\n📋 Listing actual objects in S3 bucket...")
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=10)
        
        if 'Contents' not in response:
            print("❌ No objects found in S3 bucket")
            return False
        
        print(f"✅ Found {len(response['Contents'])} objects:")
        
        real_keys = []
        for obj in response['Contents']:
            key = obj['Key']
            size = obj['Size']
            print(f"   📁 {key} ({size} bytes)")
            if key.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                real_keys.append(key)
        
        if not real_keys:
            print("❌ No video files found in S3 bucket")
            return False
            
        print(f"\n🎥 Found {len(real_keys)} video files:")
        for key in real_keys:
            print(f"   🎬 {key}")
        
        # Test with a real video file
        test_key = real_keys[0]  # Use the first video file found
        print(f"\n🧪 Testing CORS with real video file: {test_key}")
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': test_key},
            ExpiresIn=3600
        )
        
        print(f"📎 Generated presigned URL: {presigned_url[:100]}...")
        
        # Test direct access to presigned URL with proper CORS headers
        headers = {
            'Origin': 'https://working.tads-video-splitter.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"\n🔍 Testing direct access with CORS headers...")
        print(f"   Origin: {headers['Origin']}")
        
        try:
            response = requests.head(presigned_url, headers=headers, timeout=10)
            print(f"   📊 Status Code: {response.status_code}")
            
            # Check response headers
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
            content_type = response.headers.get('Content-Type', 'NOT SET')
            content_length = response.headers.get('Content-Length', 'NOT SET')
            
            print(f"   🌐 CORS Origin: {cors_origin}")
            print(f"   📄 Content-Type: {content_type}")
            print(f"   📏 Content-Length: {content_length}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: S3 CORS is working!")
                print("   Video streaming should work correctly")
                return True
            elif response.status_code == 403:
                print("❌ FAILURE: Still getting 403 Forbidden")
                print("   This explains the black screen issue")
                print("   CORS configuration may not have propagated yet")
                return False
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_s3_direct_access()
    
    print(f"\n🎯 S3 Direct Access Test Result: {'PASS' if success else 'FAIL'}")
    
    if not success:
        print("\n💡 Possible Solutions:")
        print("   1. Wait 2-5 minutes for S3 CORS configuration to propagate")
        print("   2. Check if S3 bucket policy is blocking access") 
        print("   3. Verify presigned URL generation includes proper permissions")
        print("   4. Consider using S3 website endpoint instead of bucket endpoint")