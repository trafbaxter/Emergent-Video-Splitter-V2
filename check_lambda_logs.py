#!/usr/bin/env python3
"""
Check Lambda Function Logs
Examines CloudWatch logs for both main and FFmpeg Lambda functions
"""

import boto3
import json
from datetime import datetime, timedelta

def check_lambda_logs():
    """Check recent logs for both Lambda functions"""
    
    logs_client = boto3.client('logs')
    
    # Define log groups
    main_log_group = '/aws/lambda/videosplitter-api'
    ffmpeg_log_group = '/aws/lambda/ffmpeg-converter'
    
    # Get logs from last 30 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)
    
    print("=== Checking Lambda Function Logs ===")
    print(f"Time range: {start_time} to {end_time}")
    
    # Check main Lambda logs
    print(f"\n🔍 Checking {main_log_group} logs...")
    try:
        response = logs_client.filter_log_events(
            logGroupName=main_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern="ERROR"  # Look for errors first
        )
        
        events = response.get('events', [])
        if events:
            print(f"Found {len(events)} error events in main Lambda:")
            for event in events[-5:]:  # Show last 5 errors
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"  [{timestamp}] {event['message'].strip()}")
        else:
            print("No error events found in main Lambda")
            
            # Check for any recent events
            all_response = logs_client.filter_log_events(
                logGroupName=main_log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                limit=10
            )
            
            all_events = all_response.get('events', [])
            if all_events:
                print(f"Found {len(all_events)} recent events in main Lambda:")
                for event in all_events[-3:]:  # Show last 3 events
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    message = event['message'].strip()[:100]  # Truncate long messages
                    print(f"  [{timestamp}] {message}...")
            else:
                print("No recent events in main Lambda (might indicate no traffic)")
        
    except Exception as e:
        print(f"❌ Error checking main Lambda logs: {e}")
    
    # Check FFmpeg Lambda logs
    print(f"\n🔍 Checking {ffmpeg_log_group} logs...")
    try:
        response = logs_client.filter_log_events(
            logGroupName=ffmpeg_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=20
        )
        
        events = response.get('events', [])
        if events:
            print(f"Found {len(events)} events in FFmpeg Lambda:")
            for event in events[-5:]:  # Show last 5 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()[:100]  # Truncate long messages
                print(f"  [{timestamp}] {message}...")
        else:
            print("❌ No events found in FFmpeg Lambda (indicates it's not being called)")
            
    except Exception as e:
        print(f"❌ Error checking FFmpeg Lambda logs: {e}")
        if "does not exist" in str(e):
            print("   This indicates the FFmpeg Lambda function has never been invoked")
    
    # Look for specific invocation patterns
    print(f"\n🔍 Searching for Lambda invocation patterns...")
    try:
        response = logs_client.filter_log_events(
            logGroupName=main_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern="ffmpeg"  # Look for FFmpeg-related logs
        )
        
        events = response.get('events', [])
        if events:
            print(f"Found {len(events)} FFmpeg-related events in main Lambda:")
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"  [{timestamp}] {event['message'].strip()}")
        else:
            print("❌ No FFmpeg-related events in main Lambda (confirms it's not calling FFmpeg Lambda)")
            
    except Exception as e:
        print(f"⚠️ Error searching for invocation patterns: {e}")

def test_direct_lambda_invocation():
    """Test direct invocation of FFmpeg Lambda to verify it works"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"\n🧪 Testing direct FFmpeg Lambda invocation...")
    
    test_payload = {
        'operation': 'extract_metadata',
        'source_bucket': 'videosplitter-storage-1751560247',
        'source_key': 'uploads/test-video',
        'job_id': 'direct-test-001'
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='ffmpeg-converter',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        payload = json.loads(response['Payload'].read())
        print(f"Direct invocation status: {response['StatusCode']}")
        print(f"Direct invocation response: {payload}")
        
        if response['StatusCode'] == 200:
            print("✅ FFmpeg Lambda function responds to direct invocation")
        else:
            print("❌ FFmpeg Lambda function failed direct invocation")
            
        return True
        
    except Exception as e:
        print(f"❌ Direct invocation failed: {e}")
        return False

if __name__ == "__main__":
    check_lambda_logs()
    test_direct_lambda_invocation()
    
    print("\n🎯 Analysis:")
    print("- If no FFmpeg Lambda events found: Main Lambda is not calling FFmpeg Lambda")
    print("- If main Lambda shows errors: Check IAM permissions or code issues")  
    print("- If FFmpeg Lambda has events but errors: Check FFmpeg layer or S3 permissions")
    print("- If direct invocation works but main doesn't call it: Check invocation code")