#!/usr/bin/env python3
"""
Check current S3 CORS configuration
"""

import boto3
import json
from botocore.exceptions import ClientError

S3_BUCKET_NAME = 'videosplitter-storage-1751560247'

def check_s3_cors():
    """Check current S3 CORS configuration"""
    s3_client = boto3.client('s3')
    
    try:
        print(f"🔍 Checking S3 CORS configuration for bucket: {S3_BUCKET_NAME}")
        
        cors_config = s3_client.get_bucket_cors(Bucket=S3_BUCKET_NAME)
        
        print("✅ Current CORS Configuration:")
        print(json.dumps(cors_config, indent=2, default=str))
        
        print("\n📋 CORS Rules Summary:")
        for i, rule in enumerate(cors_config['CORSRules']):
            print(f"   Rule {i+1}:")
            print(f"      ID: {rule.get('ID', 'None')}")
            print(f"      Methods: {rule.get('AllowedMethods', [])}")
            print(f"      Origins: {len(rule.get('AllowedOrigins', []))} origins")
            print(f"      Headers: {rule.get('AllowedHeaders', [])}")
            print(f"      Expose: {rule.get('ExposeHeaders', [])}")
            print(f"      Max Age: {rule.get('MaxAgeSeconds', 0)}s")
            print()
        
        # Test if our domain is in the allowed origins
        working_domain = 'https://working.tads-video-splitter.com'
        found_working_domain = False
        
        for rule in cors_config['CORSRules']:
            if working_domain in rule.get('AllowedOrigins', []):
                found_working_domain = True
                break
        
        if found_working_domain:
            print(f"✅ {working_domain} is configured in CORS rules")
        else:
            print(f"❌ {working_domain} is NOT found in CORS rules")
            
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print("❌ No CORS configuration found on the bucket!")
            return False
        else:
            print(f"❌ Error checking CORS: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    check_s3_cors()