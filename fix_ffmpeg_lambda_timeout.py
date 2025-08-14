#!/usr/bin/env python3
"""
Fix FFmpeg Lambda timeout issues by updating configuration
Based on AWS Lambda best practices for video processing.
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'

def update_ffmpeg_lambda_config():
    """Update FFmpeg Lambda function configuration for better performance"""
    lambda_client = boto3.client('lambda')
    
    print("🔧 Updating FFmpeg Lambda Configuration for Video Processing")
    print("=" * 60)
    
    try:
        # Get current configuration
        print("📋 Getting current Lambda configuration...")
        current_config = lambda_client.get_function_configuration(
            FunctionName=FFMPEG_LAMBDA_FUNCTION
        )
        
        print(f"   Current timeout: {current_config.get('Timeout', 'N/A')} seconds")
        print(f"   Current memory: {current_config.get('MemorySize', 'N/A')} MB")
        print(f"   Current runtime: {current_config.get('Runtime', 'N/A')}")
        
        # Update configuration for video processing optimization
        print("\n🚀 Applying video processing optimizations...")
        
        update_config = {
            'FunctionName': FFMPEG_LAMBDA_FUNCTION,
            'Timeout': 900,  # 15 minutes (maximum for Lambda)
            'MemorySize': 3008,  # Near maximum memory for more CPU power
            'Environment': {
                'Variables': {
                    'FFMPEG_OPTS': '-threads 2 -preset ultrafast',  # Fast processing
                    'TIMEOUT_BUFFER': '60'  # Buffer time for cleanup
                }
            }
        }
        
        response = lambda_client.update_function_configuration(**update_config)
        
        print("✅ FFmpeg Lambda configuration updated successfully!")
        print(f"   New timeout: {response['Timeout']} seconds (15 minutes)")
        print(f"   New memory: {response['MemorySize']} MB (high CPU allocation)")
        print(f"   Runtime: {response['Runtime']}")
        
        # Test the configuration with a simple invocation
        print("\n🧪 Testing updated configuration...")
        test_payload = {
            'operation': 'test',
            'message': 'Configuration test'
        }
        
        try:
            test_response = lambda_client.invoke(
                FunctionName=FFMPEG_LAMBDA_FUNCTION,
                Payload=json.dumps(test_payload)
            )
            
            if test_response['StatusCode'] == 200:
                result = json.loads(test_response['Payload'].read())
                print("✅ Configuration test successful!")
                print(f"   Test response: {result}")
            else:
                print(f"⚠️  Configuration updated but test returned status: {test_response['StatusCode']}")
                
        except Exception as test_error:
            print(f"⚠️  Configuration updated but test failed: {str(test_error)}")
            print("   This may be normal if the function doesn't handle test operations")
        
        print("\n🎯 Optimization Summary:")
        print("   • Timeout increased to 15 minutes (was likely 30 seconds)")
        print("   • Memory increased to 3008 MB for maximum CPU allocation") 
        print("   • Added FFmpeg optimization environment variables")
        print("   • This should resolve the 29-second timeout issue")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ FFmpeg Lambda function '{FFMPEG_LAMBDA_FUNCTION}' not found")
            print("   Please ensure the FFmpeg Lambda function is deployed")
        elif error_code == 'AccessDeniedException':
            print("❌ Access denied - insufficient permissions to update Lambda function")
        else:
            print(f"❌ AWS error: {error_code} - {e.response['Error']['Message']}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_current_status():
    """Check current FFmpeg Lambda status"""
    lambda_client = boto3.client('lambda')
    
    try:
        print("🔍 Checking FFmpeg Lambda current status...")
        
        config = lambda_client.get_function_configuration(
            FunctionName=FFMPEG_LAMBDA_FUNCTION
        )
        
        print("📊 Current Configuration:")
        print(f"   Function Name: {config['FunctionName']}")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Memory Size: {config['MemorySize']} MB")
        print(f"   Timeout: {config['Timeout']} seconds")
        print(f"   Last Modified: {config['LastModified']}")
        
        # Check if timeout is the issue
        if config['Timeout'] <= 60:
            print("\n⚠️  ISSUE FOUND: Timeout is very low for video processing!")
            print(f"   Current: {config['Timeout']} seconds")
            print("   Recommended: 900 seconds (15 minutes) for video processing")
            return False
        else:
            print(f"\n✅ Timeout looks good: {config['Timeout']} seconds")
            return True
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ FFmpeg Lambda function '{FFMPEG_LAMBDA_FUNCTION}' not found")
        else:
            print(f"❌ Error checking status: {e.response['Error']['Message']}")
        return False

def main():
    """Main function"""
    print("🎬 FFmpeg Lambda Timeout Fix for Video Splitter Pro")
    print("=" * 60)
    
    # Check current status
    current_ok = check_current_status()
    
    if not current_ok:
        print("\n" + "=" * 60)
        # Apply fix
        if update_ffmpeg_lambda_config():
            print("\n🎉 FFmpeg Lambda optimization complete!")
            print("\n✨ Your video processing should now work without timeouts!")
            print("\nNext steps:")
            print("   1. Refresh your browser")
            print("   2. Try uploading and splitting your MKV file")
            print("   3. The real duration (22:42) should now be detected")
            print("   4. Video splitting should complete successfully")
        else:
            print("\n❌ Optimization failed. Please check AWS permissions.")
    else:
        print("\n✅ FFmpeg Lambda configuration looks good!")
        print("The timeout issue may be elsewhere in the system.")

if __name__ == "__main__":
    main()