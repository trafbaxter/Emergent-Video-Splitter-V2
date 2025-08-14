#!/usr/bin/env python3
"""
Job Queue Processor for Video Splitter Pro
This script processes jobs from the S3 job queue and invokes FFmpeg Lambda for video processing.
"""

import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

# Configuration
S3_BUCKET = 'videosplitter-storage-1751560247'
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'
AWS_REGION = 'us-east-1'

def process_job_queue():
    """Process all pending jobs in the S3 job queue"""
    print("🚀 Starting job queue processor...")
    
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    
    try:
        # List all job files in the queue
        print(f"📋 Checking S3 job queue: s3://{S3_BUCKET}/jobs/")
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='jobs/',
            MaxKeys=10  # Process up to 10 jobs at a time
        )
        
        if 'Contents' not in response:
            print("   ℹ️  No jobs found in queue")
            return
        
        job_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.json')]
        print(f"   📁 Found {len(job_files)} job files to process")
        
        for job_file in job_files:
            job_key = job_file['Key']
            job_id = job_key.split('/')[-1].replace('.json', '')
            
            print(f"\n🎯 Processing job: {job_id}")
            print(f"   📄 Job file: {job_key}")
            
            try:
                # Read job details from S3
                job_response = s3_client.get_object(Bucket=S3_BUCKET, Key=job_key)
                job_data = json.loads(job_response['Body'].read().decode('utf-8'))
                
                print(f"   📋 Job details:")
                print(f"      Source: {job_data.get('source_key')}")
                print(f"      Method: {job_data.get('split_config', {}).get('method')}")
                print(f"      Status: {job_data.get('status')}")
                
                # Check if job is already processed or processing
                if job_data.get('status') != 'queued':
                    print(f"   ⏭️  Skipping job {job_id} - status: {job_data.get('status')}")
                    continue
                
                # Check if output already exists
                output_prefix = job_data.get('output_prefix', f'outputs/{job_id}/')
                output_check = s3_client.list_objects_v2(
                    Bucket=S3_BUCKET,
                    Prefix=output_prefix,
                    MaxKeys=1
                )
                
                if 'Contents' in output_check:
                    print(f"   ✅ Output already exists for job {job_id} - marking as completed")
                    # Update job status to completed
                    job_data['status'] = 'completed'
                    job_data['completed_at'] = datetime.now().isoformat()
                    
                    # Move job file to completed
                    completed_key = f'jobs/completed/{job_id}.json'
                    s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=completed_key,
                        Body=json.dumps(job_data, indent=2),
                        ContentType='application/json'
                    )
                    s3_client.delete_object(Bucket=S3_BUCKET, Key=job_key)
                    print(f"   📁 Moved job file to: {completed_key}")
                    continue
                
                # Prepare FFmpeg Lambda payload
                ffmpeg_payload = {
                    'operation': 'split_video',
                    'source_bucket': job_data['source_bucket'],
                    'source_key': job_data['source_key'],
                    'job_id': job_id,
                    'split_config': job_data['split_config']
                }
                
                print(f"   🎬 Invoking FFmpeg Lambda...")
                print(f"      Function: {FFMPEG_LAMBDA_FUNCTION}")
                print(f"      Operation: {ffmpeg_payload['operation']}")
                
                # Invoke FFmpeg Lambda asynchronously
                lambda_response = lambda_client.invoke(
                    FunctionName=FFMPEG_LAMBDA_FUNCTION,
                    InvocationType='Event',  # Asynchronous
                    Payload=json.dumps(ffmpeg_payload)
                )
                
                invoke_status = lambda_response.get('StatusCode', 0)
                print(f"   📊 Lambda invoke status: {invoke_status}")
                
                if invoke_status == 202:
                    print(f"   ✅ FFmpeg Lambda invoked successfully for job {job_id}")
                    
                    # Update job status to processing
                    job_data['status'] = 'processing'
                    job_data['processing_started_at'] = datetime.now().isoformat()
                    job_data['ffmpeg_invoke_status'] = invoke_status
                    
                    # Update job file
                    s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=job_key,
                        Body=json.dumps(job_data, indent=2),
                        ContentType='application/json'
                    )
                    
                    print(f"   📝 Updated job status to 'processing'")
                    
                else:
                    print(f"   ❌ FFmpeg Lambda invocation failed: status {invoke_status}")
                    
                    # Update job status to failed
                    job_data['status'] = 'failed'
                    job_data['error'] = f'FFmpeg Lambda invoke failed with status {invoke_status}'
                    job_data['failed_at'] = datetime.now().isoformat()
                    
                    # Update job file
                    s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=job_key,
                        Body=json.dumps(job_data, indent=2),
                        ContentType='application/json'
                    )
                    
            except Exception as job_error:
                print(f"   ❌ Error processing job {job_id}: {str(job_error)}")
                continue
        
        print(f"\n✅ Job queue processing complete. Processed {len(job_files)} jobs.")
        
    except Exception as e:
        print(f"❌ Job queue processor error: {str(e)}")

if __name__ == "__main__":
    print("Video Splitter Pro - Job Queue Processor")
    print("=" * 50)
    
    process_job_queue()
    
    print("\n" + "=" * 50)
    print("Job queue processing finished.")