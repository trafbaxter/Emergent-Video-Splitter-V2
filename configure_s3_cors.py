#!/usr/bin/env python3
"""
Configure CORS for S3 bucket to allow video uploads from Amplify frontend
"""
import boto3
import json
import sys

def configure_s3_cors():
    """Configure CORS for the S3 bucket"""
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    bucket_name = 'videosplitter-storage-1751560247'
    
    # CORS configuration
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': [
                    'Authorization',
                    'Content-Length',
                    'Content-Type',
                    'Date',
                    'Host',
                    'User-Agent',
                    'X-Amz-Content-Sha256',
                    'X-Amz-Date',
                    'X-Amz-Security-Token',
                    'X-Amz-User-Agent',
                    'x-amz-acl',
                    'x-amz-meta-*',
                    'key',
                    'policy',
                    'x-amz-algorithm',
                    'x-amz-credential',
                    'x-amz-signature'
                ],
                'AllowedMethods': ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'],
                'AllowedOrigins': [
                    'https://develop.tads-video-splitter.com',
                    'http://localhost:3000',
                    'http://localhost:8000',
                    'http://localhost:8001'
                ],
                'ExposeHeaders': [
                    'ETag',
                    'Content-Length',
                    'Content-Type'
                ],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    
    try:
        # Apply CORS configuration
        response = s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        
        print(f"✅ CORS configuration applied successfully to bucket: {bucket_name}")
        print("Configuration:")
        print(json.dumps(cors_configuration, indent=2))
        
        # Verify the configuration
        cors_result = s3_client.get_bucket_cors(Bucket=bucket_name)
        print(f"✅ CORS configuration verified for bucket: {bucket_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring CORS for bucket {bucket_name}: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Configuring S3 CORS for Video Splitter Pro...")
    success = configure_s3_cors()
    
    if success:
        print("✅ S3 CORS configuration completed successfully!")
        print("📝 Next steps:")
        print("1. Deploy the updated Lambda function")
        print("2. Test video upload from your Amplify app")
    else:
        print("❌ S3 CORS configuration failed!")
        sys.exit(1)