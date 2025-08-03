#!/usr/bin/env python3
"""
Deploy FFmpeg Lambda Function
Updates the ffmpeg-converter Lambda function with the new code
"""

import boto3
import zipfile
import os
import tempfile

def deploy_ffmpeg_lambda():
    """Deploy the FFmpeg Lambda function"""
    
    # Initialize AWS Lambda client
    lambda_client = boto3.client('lambda')
    
    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        zip_path = tmp_file.name
    
    try:
        # Create zip file with the Lambda function
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write('/app/ffmpeg_lambda_function.py', 'lambda_function.py')
        
        print("📦 Created deployment package for FFmpeg Lambda function")
        
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        print("🚀 Updating ffmpeg-converter Lambda function...")
        
        # Update the Lambda function code
        response = lambda_client.update_function_code(
            FunctionName='ffmpeg-converter',
            ZipFile=zip_content
        )
        
        print(f"✅ FFmpeg Lambda function updated successfully!")
        print(f"   Function: {response['FunctionName']}")
        print(f"   Runtime: {response['Runtime']}")
        print(f"   Handler: {response['Handler']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        print(f"   Last Modified: {response['LastModified']}")
        
        # Update Lambda configuration to use the ffmpeg-layer
        print("🔧 Updating Lambda configuration to use ffmpeg-layer...")
        
        try:
            config_response = lambda_client.update_function_configuration(
                FunctionName='ffmpeg-converter',
                Layers=['arn:aws:lambda:us-east-1:' + boto3.session.Session().get_credentials().access_key[:12] + ':layer:ffmpeg-layer'],
                Timeout=300,  # 5 minutes timeout for video processing
                MemorySize=1024  # Increase memory for video processing
            )
            print("✅ Lambda configuration updated with ffmpeg-layer")
        except Exception as e:
            print(f"⚠️ Could not update layer configuration: {e}")
            print("   Please manually add the ffmpeg-layer to the Lambda function")
        
        print("\n🎯 Next steps:")
        print("1. Verify the ffmpeg-layer is attached to ffmpeg-converter function")
        print("2. Test the metadata extraction and video splitting")
        print("3. Update the main videosplitter-api Lambda function")
        
    except Exception as e:
        print(f"❌ Error deploying FFmpeg Lambda function: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(zip_path):
            os.remove(zip_path)
    
    return True

if __name__ == "__main__":
    print("=== FFmpeg Lambda Function Deployment ===")
    success = deploy_ffmpeg_lambda()
    
    if success:
        print("\n✅ FFmpeg Lambda deployment completed!")
    else:
        print("\n❌ FFmpeg Lambda deployment failed!")