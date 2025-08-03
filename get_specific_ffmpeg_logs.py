#!/usr/bin/env python3
"""
Get Specific FFmpeg Lambda Logs
Look at the specific request that was processing recently
"""

import boto3
import json
from datetime import datetime, timedelta

def get_full_request_logs():
    """Get the complete logs for the recent FFmpeg request"""
    
    logs_client = boto3.client('logs')
    
    # The request ID we saw: ca54d5be-341b-4d84-8ab6-83e03d2e010e
    request_id = "ca54d5be-341b-4d84-8ab6-83e03d2e010e"
    
    print(f"=== Getting Complete FFmpeg Lambda Logs ===")
    print(f"Request ID: {request_id}")
    
    ffmpeg_log_group = '/aws/lambda/ffmpeg-converter'
    
    # Get logs from last 15 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    try:
        response = logs_client.filter_log_events(
            logGroupName=ffmpeg_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern=request_id
        )
        
        events = response.get('events', [])
        
        if events:
            print(f"\n📋 Complete request logs ({len(events)} events):")
            print("=" * 80)
            
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"[{timestamp}] {message}")
                
        else:
            print(f"❌ No logs found for request ID: {request_id}")
            
            # Try to get any recent events
            print(f"\n📋 Recent FFmpeg Lambda events:")
            recent_response = logs_client.filter_log_events(
                logGroupName=ffmpeg_log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                limit=30
            )
            
            recent_events = recent_response.get('events', [])
            for event in recent_events[-15:]:  # Last 15 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                if len(message) > 120:
                    message = message[:117] + "..."
                print(f"[{timestamp}] {message}")
        
    except Exception as e:
        print(f"❌ Error getting FFmpeg logs: {e}")

def check_error_patterns():
    """Check for common error patterns in recent logs"""
    
    logs_client = boto3.client('logs')
    ffmpeg_log_group = '/aws/lambda/ffmpeg-converter'
    
    # Get logs from last 15 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    print(f"\n🚨 Checking for Error Patterns:")
    print("=" * 50)
    
    error_patterns = [
        "ERROR",
        "Exception", 
        "Failed",
        "denied",
        "timeout",
        "not found",
        "permission"
    ]
    
    for pattern in error_patterns:
        try:
            response = logs_client.filter_log_events(
                logGroupName=ffmpeg_log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern=pattern
            )
            
            events = response.get('events', [])
            if events:
                print(f"\n🔍 Found {len(events)} events matching '{pattern}':")
                for event in events[-3:]:  # Show last 3 matches
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    print(f"  [{timestamp}] {event['message'].strip()}")
        except:
            pass
    
    print(f"\n✅ Error pattern check complete")

if __name__ == "__main__":
    get_full_request_logs()
    check_error_patterns()