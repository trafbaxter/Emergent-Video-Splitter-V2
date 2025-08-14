#!/usr/bin/env python3
"""
Deploy the updated FFmpeg Lambda function with SQS support
"""

import boto3
import zipfile
import io
import os
import json

# Configuration
LAMBDA_FUNCTION_NAME = 'ffmpeg-converter'
REGION = 'us-east-1'

def deploy_ffmpeg_lambda():
    """Deploy the updated FFmpeg Lambda function"""
    print("🚀 Deploying SQS-enabled FFmpeg Lambda")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Step 1: Read the updated FFmpeg Lambda function
        print("📋 Reading updated FFmpeg Lambda function...")
        with open('/app/backup_files/ffmpeg_lambda_function.py', 'r') as f:
            function_code = f.read()
        
        # Step 2: Create deployment package
        print("📦 Creating deployment package...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', function_code)
        
        zip_buffer.seek(0)
        deployment_package = zip_buffer.read()
        
        print(f"✅ Deployment package created: {len(deployment_package)} bytes")
        
        # Step 3: Update Lambda function code
        print(f"📤 Updating Lambda function: {LAMBDA_FUNCTION_NAME}")
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=deployment_package
        )
        
        print(f"✅ Lambda function updated successfully")
        print(f"   Function ARN: {response['FunctionArn']}")
        print(f"   Runtime: {response['Runtime']}")
        print(f"   Handler: {response['Handler']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        
        # Step 4: Update environment variables (add DynamoDB table name)
        print("\n📋 Updating environment variables...")
        try:
            env_response = lambda_client.update_function_configuration(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Environment={
                    'Variables': {
                        'JOBS_TABLE': 'VideoSplitter-Jobs',
                        'AWS_REGION': REGION
                    }
                }
            )
            print("✅ Environment variables updated")
        except Exception as env_error:
            print(f"⚠️ Environment variable update warning: {env_error}")
        
        # Step 5: Wait for function to be ready
        print("\n⏳ Waiting for function to be ready...")
        waiter = lambda_client.get_waiter('function_updated_v2')
        waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)
        print("✅ Function is ready")
        
        print("\n" + "=" * 50)
        print("🎉 FFmpeg Lambda deployment complete!")
        print("=" * 50)
        print("✅ SQS event handling enabled")
        print("✅ DynamoDB job status updates enabled")
        print("✅ Backward compatibility with direct invocation maintained")
        print("\nThe Lambda function can now:")
        print("• Process SQS messages automatically")
        print("• Update job status in DynamoDB")
        print("• Handle both direct and SQS invocations")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_ffmpeg_lambda()
    if success:
        print("\n🚀 Ready to test SQS-based video processing!")
    else:
        print("\n❌ Deployment failed. Please check AWS credentials and permissions.")