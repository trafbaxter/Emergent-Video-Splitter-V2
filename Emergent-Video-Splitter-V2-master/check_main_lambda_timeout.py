#!/usr/bin/env python3
"""
Check and fix the main Lambda function timeout
"""

import boto3
from botocore.exceptions import ClientError

MAIN_LAMBDA_FUNCTION = 'videosplitter-api'

def check_and_fix_main_lambda():
    """Check and fix main Lambda timeout"""
    lambda_client = boto3.client('lambda')
    
    try:
        print("🔍 Checking main Lambda (videosplitter-api) configuration...")
        
        config = lambda_client.get_function_configuration(
            FunctionName=MAIN_LAMBDA_FUNCTION
        )
        
        current_timeout = config['Timeout']
        current_memory = config['MemorySize']
        
        print(f"📊 Current Main Lambda Configuration:")
        print(f"   Timeout: {current_timeout} seconds")
        print(f"   Memory: {current_memory} MB")
        
        # Check if timeout is too low
        if current_timeout < 300:  # Less than 5 minutes
            print(f"\n⚠️  ISSUE FOUND: Timeout too low for video processing!")
            print(f"   Current: {current_timeout} seconds")
            print(f"   This explains the 29-second timeout issue!")
            
            print("\n🔧 Updating main Lambda timeout...")
            
            response = lambda_client.update_function_configuration(
                FunctionName=MAIN_LAMBDA_FUNCTION,
                Timeout=900,  # 15 minutes
                MemorySize=max(1024, current_memory)  # At least 1GB
            )
            
            print("✅ Main Lambda configuration updated!")
            print(f"   New timeout: {response['Timeout']} seconds")
            print(f"   New memory: {response['MemorySize']} MB")
            
            return True
        else:
            print(f"✅ Main Lambda timeout looks good: {current_timeout} seconds")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎬 Main Lambda Timeout Check for Video Splitter Pro")
    print("=" * 60)
    
    if check_and_fix_main_lambda():
        print("\n🎉 Main Lambda timeout issue fixed!")
        print("\nThis should resolve the 504 Gateway Timeout errors.")
        print("Video processing should now work properly!")
    else:
        print("\nMain Lambda timeout was already sufficient.")