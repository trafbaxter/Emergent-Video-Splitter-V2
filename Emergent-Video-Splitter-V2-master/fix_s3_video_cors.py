#!/usr/bin/env python3
"""
Fix S3 CORS configuration specifically for video streaming
This script updates the S3 bucket CORS policy to allow video streaming with proper headers.
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
S3_BUCKET_NAME = 'videosplitter-storage-1751560247'

def configure_s3_video_streaming_cors():
    """Configure S3 bucket CORS specifically for video streaming"""
    s3_client = boto3.client('s3')
    
    # Enhanced CORS configuration for video streaming
    cors_configuration = {
        'CORSRules': [
            {
                'ID': 'VideoStreamingCORS',
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],  # Only need GET and HEAD for video streaming
                'AllowedOrigins': [
                    'https://develop.tads-video-splitter.com',
                    'https://main.tads-video-splitter.com', 
                    'https://master.tads-video-splitter.com',
                    'https://working.tads-video-splitter.com',
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000'
                ],
                'ExposeHeaders': [
                    'Content-Length',
                    'Content-Range', 
                    'Content-Type',
                    'ETag',
                    'Accept-Ranges',
                    'Last-Modified',
                    'x-amz-request-id'
                ],
                'MaxAgeSeconds': 3000
            },
            {
                'ID': 'FileUploadCORS', 
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'HEAD'],
                'AllowedOrigins': [
                    'https://develop.tads-video-splitter.com',
                    'https://main.tads-video-splitter.com', 
                    'https://master.tads-video-splitter.com',
                    'https://working.tads-video-splitter.com',
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000'
                ],
                'ExposeHeaders': [
                    'ETag',
                    'x-amz-request-id'
                ],
                'MaxAgeSeconds': 3600
            }
        ]
    }
    
    try:
        print("🚀 Configuring S3 CORS for video streaming...")
        print(f"   Bucket: {S3_BUCKET_NAME}")
        
        # Update CORS configuration
        s3_client.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        print("✅ S3 CORS configuration updated successfully!")
        print("   Rule 1: Video Streaming CORS")
        print("   Rule 2: File Upload CORS")
        print("   Methods: GET, HEAD for streaming + PUT, POST for uploads")
        print("   Origins: 7 domains")
        print("   Headers: Content-Length, Content-Range, Content-Type, Accept-Ranges")
        
        # Verify the configuration
        try:
            cors_config = s3_client.get_bucket_cors(Bucket=S3_BUCKET_NAME)
            rules_count = len(cors_config['CORSRules'])
            print(f"✅ CORS configuration verified! ({rules_count} rules)")
            
            return True
        except Exception as verify_error:
            print(f"⚠️  Could not verify CORS config: {verify_error}")
            return True  # Still consider it successful if update worked
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS S3 Error: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"❌ Failed to configure S3 CORS: {str(e)}")
        return False

if __name__ == "__main__":
    success = configure_s3_video_streaming_cors()
    
    if success:
        print("\n🎉 S3 Video Streaming CORS Configuration Complete!")
        print("\n📋 What this enables:")
        print("   • Video preview should now work (no more black screen)")
        print("   • Browser can access S3 video files directly")
        print("   • Proper headers for video streaming (Content-Range, Accept-Ranges)")
        print("   • File upload functionality preserved")
        print("\n⚠️  Note: It may take 1-2 minutes for CORS changes to take effect.")
    else:
        print("\n❌ CORS configuration failed!")