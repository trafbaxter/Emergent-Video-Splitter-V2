#!/usr/bin/env python3
"""
Simple CORS fix deployment - just update the code
"""

import boto3
import json
import zipfile
import os
import tempfile
import shutil

def deploy_cors_fix():
    """Deploy just the code update"""
    print("🚀 Deploying CORS fix...")
    
    # Create AWS Lambda client
    lambda_client = boto3.client('lambda')
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, 'package')
    os.makedirs(package_dir)
    
    try:
        # Copy the fixed lambda function
        shutil.copy2('/app/fix_cors_lambda.py', os.path.join(package_dir, 'lambda_function.py'))
        
        # Create ZIP file
        zip_path = os.path.join(temp_dir, 'lambda_package.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join(package_dir, 'lambda_function.py'), 'lambda_function.py')
        
        # Read and deploy
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        response = lambda_client.update_function_code(
            FunctionName='videosplitter-api',
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"   Function: {response['FunctionName']}")
        print(f"   Size: {response['CodeSize']} bytes")
        
        # Test the function
        test_payload = {
            'httpMethod': 'GET',
            'path': '/api/',
            'headers': {
                'origin': 'http://localhost:3000'
            }
        }
        
        print("🧪 Testing function...")
        test_response = lambda_client.invoke(
            FunctionName='videosplitter-api',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(test_response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            print("✅ Test successful!")
            print(f"   Version: {body.get('version', 'N/A')}")
            print(f"   CORS Origins: {len(body.get('cors', {}).get('allowed_origins', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    deploy_cors_fix()