#!/usr/bin/env python3
"""
Check Recent Upload Logs
Look at the most recent logs to see what happened with the latest video upload
"""

import boto3
import json
from datetime import datetime, timedelta

def check_recent_upload():
    """Check the most recent upload activity"""
    
    logs_client = boto3.client('logs')
    
    # Get logs from last 10 minutes (user just uploaded)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)
    
    print("=== Checking Recent Upload Activity ===")
    print(f"Looking at logs from: {start_time} to {end_time}")
    
    # Check main Lambda for recent video-info requests
    main_log_group = '/aws/lambda/videosplitter-api'
    
    print(f"\n🔍 Recent main Lambda activity:")
    try:
        response = logs_client.filter_log_events(
            logGroupName=main_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern="video-info"
        )
        
        events = response.get('events', [])
        if events:
            print(f"Found {len(events)} video-info events:")
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"  [{timestamp}] {event['message'].strip()}")
        else:
            print("❌ No video-info requests found")
            
        # Check for any upload-related activity
        upload_response = logs_client.filter_log_events(
            logGroupName=main_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern="upload-video"
        )
        
        upload_events = upload_response.get('events', [])
        if upload_events:
            print(f"Found {len(upload_events)} upload events:")
            for event in upload_events[-3:]:  # Last 3 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"  [{timestamp}] {event['message'].strip()}")
        
    except Exception as e:
        print(f"❌ Error checking main Lambda: {e}")
    
    # Check FFmpeg Lambda for recent activity
    ffmpeg_log_group = '/aws/lambda/ffmpeg-converter'
    
    print(f"\n🔍 Recent FFmpeg Lambda activity:")
    try:
        response = logs_client.filter_log_events(
            logGroupName=ffmpeg_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000)
        )
        
        events = response.get('events', [])
        if events:
            print(f"Found {len(events)} FFmpeg events:")
            for event in events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                if len(message) > 100:
                    message = message[:97] + "..."
                print(f"  [{timestamp}] {message}")
        else:
            print("❌ No FFmpeg Lambda activity during upload")
            
    except Exception as e:
        print(f"❌ Error checking FFmpeg Lambda: {e}")
    
    # Check for errors
    print(f"\n🚨 Checking for recent errors:")
    try:
        error_response = logs_client.filter_log_events(
            logGroupName=main_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern="ERROR"
        )
        
        error_events = error_response.get('events', [])
        if error_events:
            print(f"Found {len(error_events)} errors:")
            for event in error_events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"  [{timestamp}] {event['message'].strip()}")
        else:
            print("✅ No errors found in recent activity")
            
    except Exception as e:
        print(f"❌ Error checking for errors: {e}")

def diagnose_metadata_issue():
    """Try to diagnose why metadata is showing all zeros"""
    
    print(f"\n🔬 METADATA ISSUE DIAGNOSIS:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    print(f"\nObserved Symptoms:")
    print(f"• Video preview works (shows 10:49 duration)")
    print(f"• Metadata shows: Duration 0:00, Format unknown, Size 0 Bytes")
    print(f"• All stream counts are 0")
    print(f"• No more file size estimation (11:33) - progress!")
    
    print(f"\nPossible Root Causes:")
    print(f"1. FFmpeg Lambda not being called for metadata extraction")
    print(f"2. FFmpeg Lambda called but ffprobe command fails")
    print(f"3. S3 permissions preventing FFmpeg Lambda from accessing video")
    print(f"4. Video file corrupt or in unsupported format")
    print(f"5. FFmpeg layer missing or corrupted")
    
    print(f"\nNext Troubleshooting Steps:")
    print(f"• Check if video-info endpoint calls FFmpeg Lambda")
    print(f"• Test FFmpeg Lambda with actual uploaded video")
    print(f"• Verify ffprobe works in Lambda environment")
    print(f"• Check S3 permissions for FFmpeg Lambda")

if __name__ == "__main__":
    check_recent_upload()
    diagnose_metadata_issue()