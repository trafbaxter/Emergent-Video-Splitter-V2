#!/usr/bin/env python3
"""
Increase Lambda Function Timeouts
Both main and FFmpeg Lambda functions need longer timeouts for video processing
"""

import boto3

def increase_timeouts():
    """Increase timeout for both Lambda functions"""
    
    lambda_client = boto3.client('lambda')
    
    functions_to_update = [
        {
            'name': 'videosplitter-api',
            'timeout': 300,  # 5 minutes
            'memory': 1024   # 1GB for better performance
        },
        {
            'name': 'ffmpeg-converter', 
            'timeout': 300,  # 5 minutes for video processing
            'memory': 2048   # 2GB for FFmpeg processing
        }
    ]
    
    for func_config in functions_to_update:
        try:
            print(f"🔧 Updating {func_config['name']} Lambda configuration...")
            
            response = lambda_client.update_function_configuration(
                FunctionName=func_config['name'],
                Timeout=func_config['timeout'],
                MemorySize=func_config['memory']
            )
            
            print(f"✅ Updated {func_config['name']}:")
            print(f"   Timeout: {response['Timeout']} seconds")
            print(f"   Memory: {response['MemorySize']} MB")
            print(f"   Last Modified: {response['LastModified']}")
            
        except Exception as e:
            print(f"❌ Failed to update {func_config['name']}: {e}")
    
    print(f"\n🎯 Configuration Summary:")
    print(f"• videosplitter-api: 5 min timeout, 1GB memory")
    print(f"• ffmpeg-converter: 5 min timeout, 2GB memory") 
    print(f"• This should handle large video files properly")

if __name__ == "__main__":
    print("=== Increasing Lambda Function Timeouts ===")
    increase_timeouts()
    print("\n✅ Lambda timeout configuration completed!")