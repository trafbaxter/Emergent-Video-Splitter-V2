#!/usr/bin/env python3
"""
Fix S3 CORS configuration for Video Splitter Pro
This script updates the S3 bucket CORS policy to allow direct uploads from the frontend.
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
S3_BUCKET_NAME = 'videosplitter-uploads'

# Allowed origins for S3 CORS - matching our Lambda CORS configuration
ALLOWED_ORIGINS = [
    'https://develop.tads-video-splitter.com',
    'https://main.tads-video-splitter.com', 
    'https://master.tads-video-splitter.com',
    'https://working.tads-video-splitter.com',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000'
]

def create_s3_cors_configuration():
    """Create S3 CORS configuration"""
    
    cors_configuration = {
        'CORSRules': [
            {
                'ID': 'VideoSplitterCORS',
                'AllowedHeaders': [
                    '*'
                ],
                'AllowedMethods': [
                    'GET',
                    'PUT',
                    'POST',
                    'DELETE',
                    'HEAD'
                ],
                'AllowedOrigins': ALLOWED_ORIGINS,
                'ExposeHeaders': [
                    'ETag',
                    'x-amz-request-id'
                ],
                'MaxAgeSeconds': 3600
            }
        ]
    }
    
    return cors_configuration

def get_current_s3_cors():
    """Get current S3 CORS configuration"""
    s3 = boto3.client('s3')
    
    try:
        response = s3.get_bucket_cors(Bucket=S3_BUCKET_NAME)
        return response.get('CORSRules', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print("ℹ️  No existing CORS configuration found")
            return []
        else:
            print(f"❌ Error getting CORS configuration: {e}")
            return None

def deploy_s3_cors():
    """Deploy S3 CORS configuration"""
    s3 = boto3.client('s3')
    
    print(f"🔧 Updating S3 CORS configuration for bucket: {S3_BUCKET_NAME}")
    
    # Get current configuration
    print("📋 Checking current CORS configuration...")
    current_cors = get_current_s3_cors()
    
    if current_cors is not None:
        print(f"   Current rules: {len(current_cors)}")
        for i, rule in enumerate(current_cors):
            print(f"   Rule {i+1}: {len(rule.get('AllowedOrigins', []))} origins, {len(rule.get('AllowedMethods', []))} methods")
    
    # Create new configuration
    cors_config = create_s3_cors_configuration()
    
    try:
        # Apply CORS configuration
        s3.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_config
        )
        
        print("✅ S3 CORS configuration updated successfully!")
        
        # Verify the update
        print("🔍 Verifying updated configuration...")
        updated_cors = get_current_s3_cors()
        
        if updated_cors:
            rule = updated_cors[0]
            print(f"✅ Verification successful:")
            print(f"   Rule ID: {rule.get('ID', 'N/A')}")
            print(f"   Allowed Origins: {len(rule.get('AllowedOrigins', []))}")
            print(f"   Allowed Methods: {', '.join(rule.get('AllowedMethods', []))}")
            print(f"   Max Age: {rule.get('MaxAgeSeconds', 'N/A')} seconds")
            
            print("\n📋 Allowed Origins:")
            for i, origin in enumerate(rule.get('AllowedOrigins', []), 1):
                print(f"   {i}. {origin}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Failed to update S3 CORS configuration: {e}")
        return False

def test_s3_access():
    """Test S3 bucket access"""
    s3 = boto3.client('s3')
    
    print("🧪 Testing S3 bucket access...")
    
    try:
        # Test bucket exists and is accessible
        response = s3.head_bucket(Bucket=S3_BUCKET_NAME)
        print("✅ S3 bucket is accessible")
        
        # List first few objects to verify read access
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=5)
        object_count = response.get('KeyCount', 0)
        print(f"✅ S3 bucket contains {object_count} objects (showing max 5)")
        
        return True
        
    except ClientError as e:
        print(f"❌ S3 bucket access failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 S3 CORS Configuration Fix for Video Splitter Pro")
    print("=" * 60)
    
    # Test S3 access first
    if not test_s3_access():
        print("\n❌ Cannot access S3 bucket. Please check your AWS credentials.")
        return False
    
    print("\n" + "=" * 60)
    
    # Deploy CORS configuration
    if deploy_s3_cors():
        print("\n🎉 S3 CORS Configuration Complete!")
        print("\nS3 bucket now accepts uploads from:")
        for origin in ALLOWED_ORIGINS:
            print(f"   • {origin}")
        print("\n✨ Frontend file uploads should now work without CORS errors!")
        print("\n⚠️  Note: It may take a few minutes for the CORS changes to propagate.")
        return True
    else:
        print("\n❌ S3 CORS configuration failed.")
        return False

if __name__ == "__main__":
    main()