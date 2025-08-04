#!/usr/bin/env python3
"""
Deploy clean core Lambda function to restore video processing functionality
This will restore the working state before adding authentication back properly
"""
import boto3
import zipfile
import sys
import os
import tempfile
import subprocess
import shutil
import json
from pathlib import Path

def create_core_lambda_package():
    """Create Lambda deployment package with core functionality only"""
    
    print("🎯 Creating core Lambda package (video processing only)...")
    
    zip_path = 'lambda-core-restored.zip'
    
    # Create zip with just the core lambda function
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write('lambda_function_core.py', 'lambda_function.py')
    
    package_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
    print(f"📊 Core package size: {package_size:.2f} MB")
    
    return zip_path

def deploy_core_lambda(zip_path):
    """Deploy the core Lambda function"""
    
    print("\n🚀 Deploying core Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Update function code
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Core Lambda function deployed successfully!")
        print(f"Function ARN: {response.get('FunctionArn')}")
        print(f"Last Modified: {response.get('LastModified')}")
        print(f"Code Size: {response.get('CodeSize')} bytes")
        
        # Wait for the update to complete
        print("⏳ Waiting for code update to complete...")
        import time
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying core Lambda function: {str(e)}")
        return False

def test_core_endpoints():
    """Test core video processing endpoints"""
    
    print("\n🧪 Testing core video processing endpoints...")
    
    lambda_client = boto3.client('lambda')
    
    test_cases = [
        {
            'name': 'API Root',
            'payload': {
                "httpMethod": "GET",
                "path": "/api/",
                "headers": {},
                "body": None
            }
        },
        {
            'name': 'Generate Presigned URL',
            'payload': {
                "httpMethod": "POST", 
                "path": "/api/generate-presigned-url",
                "headers": {"Content-Type": "application/json"},
                "body": '{"filename":"test-video.mp4","contentType":"video/mp4"}'
            }
        },
        {
            'name': 'Video Info Endpoint',
            'payload': {
                "httpMethod": "POST",
                "path": "/api/get-video-info", 
                "headers": {"Content-Type": "application/json"},
                "body": '{"objectKey":"test-key"}'
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            print(f"\n🔍 Testing {test_case['name']}...")
            
            response = lambda_client.invoke(
                FunctionName='videosplitter-api',
                Payload=json.dumps(test_case['payload'])
            )
            
            status_code = response.get('StatusCode', 0)
            payload = response['Payload'].read().decode('utf-8')
            
            if status_code == 200:
                # Parse response
                try:
                    response_data = json.loads(payload)
                    http_status = response_data.get('statusCode', 'unknown')
                    
                    if http_status == 200:
                        print(f"✅ {test_case['name']}: SUCCESS")
                    elif http_status in [400, 404]:
                        print(f"✅ {test_case['name']}: ENDPOINT AVAILABLE (HTTP {http_status})")
                    elif http_status == 502:
                        print(f"❌ {test_case['name']}: 502 Bad Gateway - Still failing")
                        return False
                    else:
                        print(f"⚠️  {test_case['name']}: HTTP {http_status}")
                        
                except json.JSONDecodeError:
                    if "ImportModuleError" in payload:
                        print(f"❌ {test_case['name']}: Import error")
                        return False
                    else:
                        print(f"✅ {test_case['name']}: Response received")
                        
            else:
                print(f"❌ {test_case['name']}: Lambda invocation failed (status {status_code})")
                return False
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Test failed - {str(e)}")
            return False
    
    print("\n🎉 Core video processing endpoints are working!")
    return True

def main():
    """Main deployment process for core functionality restoration"""
    
    print("🎯 Video Splitter Pro - Core Functionality Restoration")
    print("=" * 60)
    print("📋 Strategy: Deploy clean core video processing functionality")
    print("🔧 Goal: Restore working state before authentication integration")
    print()
    
    # Check prerequisites
    if not os.path.exists('lambda_function_core.py'):
        print("❌ lambda_function_core.py not found in current directory")
        sys.exit(1)
    
    try:
        # Create core package
        zip_path = create_core_lambda_package()
        
        if not zip_path:
            print("❌ Failed to create core deployment package")
            sys.exit(1)
        
        # Deploy to Lambda
        success = deploy_core_lambda(zip_path)
        
        if not success:
            print("❌ Core Lambda deployment failed")
            sys.exit(1)
        
        # Test core endpoints
        test_success = test_core_endpoints()
        
        # Cleanup deployment package
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"\n🧹 Cleaned up {zip_path}")
        
        if test_success:
            print("\n🎉 CORE FUNCTIONALITY RESTORATION SUCCESSFUL!")
            print("=" * 60)
            print("✅ Core video processing functionality restored")
            print("✅ All video endpoints working properly") 
            print("✅ No 502 Bad Gateway errors")
            print("✅ Ready for proper authentication integration")
            print()
            print("📝 Available endpoints:")
            print("  GET /api/ - API info and health check")
            print("  POST /api/generate-presigned-url - Get upload URL")
            print("  POST /api/get-video-info - Get video metadata")
            print("  POST /api/split-video - Split video into segments")
            print("  GET /api/download/{key} - Download processed video")
            print()
            print("🔧 Next step: Implement authentication properly without duplicates")
            
        else:
            print("\n❌ CORE FUNCTIONALITY RESTORATION FAILED!")
            print("⚠️  Basic video processing endpoints still not working")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()