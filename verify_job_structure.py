#!/usr/bin/env python3
"""
Verify the exact structure of job files created in S3 job queue
"""

import requests
import json
import boto3
import time

# Configuration
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
S3_BUCKET = "videosplitter-storage-1751560247"
AWS_REGION = "us-east-1"

def test_job_file_structure():
    """Create a job and examine its exact structure"""
    
    # Create a split video job
    split_data = {
        "s3_key": "uploads/3edba1d9-b854-45b0-a7d4-54a88940f38b/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv",
        "method": "intervals",
        "interval_duration": 300,
        "preserve_quality": True,
        "output_format": "mp4"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://working.tads-video-splitter.com'
    }
    
    print("🎯 Creating split video job...")
    response = requests.post(f"{API_GATEWAY_URL}/api/split-video", json=split_data, headers=headers)
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get('job_id')
        print(f"✅ Job created: {job_id}")
        
        # Wait a moment for S3 consistency
        time.sleep(3)
        
        # Get the job file from S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        job_key = f"jobs/{job_id}.json"
        
        try:
            print(f"📁 Retrieving job file: s3://{S3_BUCKET}/{job_key}")
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=job_key)
            job_content = response['Body'].read().decode('utf-8')
            job_data = json.loads(job_content)
            
            print("📋 COMPLETE JOB FILE STRUCTURE:")
            print("=" * 60)
            print(json.dumps(job_data, indent=2))
            print("=" * 60)
            
            # Verify all required fields for FFmpeg processing
            print("\n🔍 VERIFICATION FOR BACKGROUND PROCESSING:")
            
            required_for_ffmpeg = [
                'job_id', 'source_bucket', 'source_key', 'split_config', 
                'output_bucket', 'output_prefix'
            ]
            
            all_present = True
            for field in required_for_ffmpeg:
                if field in job_data:
                    print(f"   ✅ {field}: {job_data[field]}")
                else:
                    print(f"   ❌ {field}: MISSING")
                    all_present = False
            
            # Check split_config details
            split_config = job_data.get('split_config', {})
            print(f"\n📋 SPLIT CONFIG DETAILS:")
            for key, value in split_config.items():
                print(f"   • {key}: {value}")
            
            if all_present:
                print(f"\n🎉 JOB FILE STRUCTURE PERFECT!")
                print(f"   • Contains all fields needed for FFmpeg processing")
                print(f"   • Source: s3://{job_data['source_bucket']}/{job_data['source_key']}")
                print(f"   • Output: s3://{job_data['output_bucket']}/{job_data['output_prefix']}")
                print(f"   • Method: {split_config.get('method')} with {split_config.get('interval_duration')}s intervals")
            
            # Cleanup
            print(f"\n🧹 Cleaning up test job file...")
            s3_client.delete_object(Bucket=S3_BUCKET, Key=job_key)
            print(f"   🗑️  Deleted: s3://{S3_BUCKET}/{job_key}")
            
        except Exception as e:
            print(f"❌ Error retrieving job file: {str(e)}")
    else:
        print(f"❌ Failed to create job: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_job_file_structure()