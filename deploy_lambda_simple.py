#!/usr/bin/env python3
"""
Deploy Lambda with dependencies using local installation
"""
import boto3
import zipfile
import sys
import os
import tempfile
import subprocess
import shutil
from pathlib import Path

def create_lambda_package_simple():
    """Create Lambda package with minimal dependencies approach"""
    
    print("📦 Creating simplified Lambda package...")
    
    # Create zip file directly
    zip_path = 'lambda-minimal.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add main lambda function
        zip_file.write('lambda_function.py', 'lambda_function.py')
        
        # Try to add some basic dependencies if available locally
        try:
            import jwt
            import bcrypt  
            import pymongo
            print("✅ Found dependencies locally, but Lambda will need to install them")
        except ImportError as e:
            print(f"⚠️  Missing dependencies locally: {e}")
            print("Lambda function will need dependencies installed via layers or package")
    
    package_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
    print(f"📊 Package size: {package_size:.2f} MB")
    
    return zip_path

def deploy_lambda_simple(zip_path):
    """Deploy Lambda function with basic configuration"""
    
    print("🚀 Deploying Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Update function code
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"Code Size: {response.get('CodeSize')} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying Lambda function: {str(e)}")
        return False

def main():
    """Main deployment"""
    
    print("🎯 Simple Lambda Deployment")
    print("=" * 30)
    
    try:
        # Create minimal package
        zip_path = create_lambda_package_simple()
        
        # Deploy
        success = deploy_lambda_simple(zip_path)
        
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
        
        if success:
            print("\n✅ Basic deployment completed!")
            print("📝 Note: You may need to add Lambda layers for dependencies")
            print("🔧 Testing the authentication endpoints...")
            
            # Let's test if the Lambda function can execute
            test_lambda_execution()
            
        else:
            print("\n❌ Deployment failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def test_lambda_execution():
    """Test if Lambda can execute with current dependencies"""
    
    print("\n🧪 Testing Lambda execution...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Test basic Lambda execution
        response = lambda_client.invoke(
            FunctionName='videosplitter-api',
            Payload='{"httpMethod": "GET", "path": "/", "headers": {}}'
        )
        
        status_code = response.get('StatusCode', 0)
        
        if status_code == 200:
            payload = response['Payload'].read().decode('utf-8')
            print(f"✅ Lambda execution successful!")
            print(f"Response: {payload[:200]}...")
        else:
            print(f"⚠️  Lambda execution returned status {status_code}")
            
    except Exception as e:
        print(f"❌ Lambda execution test failed: {str(e)}")
        print("This likely indicates missing dependencies")

if __name__ == "__main__":
    main()