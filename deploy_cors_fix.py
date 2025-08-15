#!/usr/bin/env python3
"""
Deploy the CORS-fixed Lambda function to AWS
"""

import boto3
import json
import zipfile
import os
import tempfile
import shutil

# Configuration
LAMBDA_FUNCTION_NAME = 'videosplitter-api'
LAMBDA_RUNTIME = 'python3.9'
LAMBDA_HANDLER = 'lambda_function.lambda_handler'
LAMBDA_TIMEOUT = 300
LAMBDA_MEMORY = 512

def create_deployment_package():
    """Create deployment package for Lambda function"""
    print("📦 Creating deployment package...")
    
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
            # Add the lambda function
            zipf.write(os.path.join(package_dir, 'lambda_function.py'), 'lambda_function.py')
            
            # Add 2FA dependencies if they exist
            deps_dir = '/app/python_2fa_deps'
            if os.path.exists(deps_dir):
                print("📦 Adding 2FA dependencies to package...")
                for root, dirs, files in os.walk(deps_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, deps_dir)
                        zipf.write(file_path, arcname)
                print(f"✅ Added 2FA dependencies from {deps_dir}")
            else:
                print("⚠️ No 2FA dependencies found, deploying without TOTP support")
        
        print(f"✅ Package created: {zip_path}")
        return zip_path, temp_dir
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def deploy_lambda_function():
    """Deploy the Lambda function to AWS"""
    print("🚀 Deploying Lambda function...")
    
    # Create AWS Lambda client
    lambda_client = boto3.client('lambda')
    
    # Create deployment package
    zip_path, temp_dir = create_deployment_package()
    
    try:
        # Read the deployment package
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Update the Lambda function code
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"   Function Name: {response['FunctionName']}")
        print(f"   Version: {response['Version']}")
        print(f"   Size: {response['CodeSize']} bytes")
        print(f"   Last Modified: {response['LastModified']}")
        
        # Update function configuration for timeout and environment variables
        config_response = lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={
                'Variables': {
                    'SES_SENDER_EMAIL': 'taddobbins@gmail.com'
                }
            }
        )
        
        print(f"✅ Lambda configuration updated!")
        print(f"   Timeout: {config_response['Timeout']} seconds")
        print(f"   Memory: {config_response['MemorySize']} MB")
        print(f"   SES Sender Email: {config_response.get('Environment', {}).get('Variables', {}).get('SES_SENDER_EMAIL', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

def test_lambda_function():
    """Test the deployed Lambda function"""
    print("🧪 Testing Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    # Test health check
    test_payload = {
        'httpMethod': 'GET',
        'path': '/api/',
        'headers': {
            'origin': 'http://localhost:3000'
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            print("✅ Lambda function test successful!")
            print(f"   Message: {body.get('message', 'N/A')}")
            print(f"   Version: {body.get('version', 'N/A')}")
            print(f"   CORS Origins: {len(body.get('cors', {}).get('allowed_origins', []))}")
            return True
        else:
            print(f"❌ Lambda function test failed with status: {result.get('statusCode')}")
            print(f"   Response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda function test failed: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print("🔧 Starting CORS Fix Deployment for Video Splitter Pro")
    print("=" * 60)
    
    # Deploy the function
    if deploy_lambda_function():
        print("\n" + "=" * 60)
        
        # Test the function
        if test_lambda_function():
            print("\n🎉 CORS Fix Deployment Complete!")
            print("\nUpdated CORS configuration allows requests from:")
            print("   • https://develop.tads-video-splitter.com")
            print("   • https://main.tads-video-splitter.com")
            print("   • https://working.tads-video-splitter.com") 
            print("   • http://localhost:3000")
            print("   • http://localhost:3001")
            print("   • http://127.0.0.1:3000")
            print("\n✨ Your frontend should now be able to register users successfully!")
        else:
            print("\n⚠️  Deployment succeeded but function test failed.")
            print("Please check AWS CloudWatch logs for details.")
    else:
        print("\n❌ Deployment failed. Please check your AWS credentials and try again.")

if __name__ == "__main__":
    main()