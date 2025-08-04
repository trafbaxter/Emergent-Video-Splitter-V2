#!/usr/bin/env python3
"""
Deploy the Lambda function with authentication dependencies
This script creates a deployment package with all required Python libraries
"""
import boto3
import zipfile
import sys
import os
import tempfile
import subprocess
import shutil
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package with all dependencies"""
    
    print("📦 Creating Lambda package with authentication dependencies...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, 'package')
    os.makedirs(package_dir)
    
    try:
        # Install dependencies
        print("📥 Installing Python dependencies...")
        dependencies = [
            'PyJWT',  # JWT library (latest compatible)
            'bcrypt',  # Password hashing (latest compatible)  
            'pymongo',  # MongoDB client (latest compatible)
        ]
        
        for dep in dependencies:
            print(f"  Installing {dep}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                '--target', package_dir,
                '--platform', 'linux_x86_64',
                '--implementation', 'cp',
                '--python-version', '3.9',
                '--only-binary=:all:',
                dep
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to install {dep}")
                print(f"Error: {result.stderr}")
                continue
            else:
                print(f"✅ Installed {dep}")
        
        # Copy Lambda function
        print("📄 Adding Lambda function code...")
        shutil.copy2('lambda_function.py', package_dir)
        
        # Create zip file
        zip_path = 'lambda-auth-package.zip'
        print(f"🗜️  Creating deployment package: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zip_file.write(file_path, arcname)
        
        # Get package size
        package_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
        print(f"📊 Package size: {package_size:.2f} MB")
        
        return zip_path
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def deploy_lambda_function(zip_path):
    """Deploy the Lambda function"""
    
    print("🚀 Deploying Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Update function code
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function deployed successfully!")
        print(f"Function ARN: {response.get('FunctionArn')}")
        print(f"Last Modified: {response.get('LastModified')}")
        print(f"Runtime: {response.get('Runtime')}")
        print(f"Code Size: {response.get('CodeSize')} bytes")
        
        # Update function configuration for better performance
        print("⚙️  Updating function configuration...")
        config_response = lambda_client.update_function_configuration(
            FunctionName='videosplitter-api',
            Timeout=30,  # 30 seconds timeout
            MemorySize=512,  # 512 MB memory
            Environment={
                'Variables': {
                    'JWT_SECRET': os.environ.get('JWT_SECRET', 'change-this-in-production'),
                    'JWT_REFRESH_SECRET': os.environ.get('JWT_REFRESH_SECRET', 'change-this-in-production-refresh'),
                    'AWS_REGION': os.environ.get('AWS_REGION', 'us-east-1'),
                    'FRONTEND_URL': os.environ.get('FRONTEND_URL', 'https://develop.tads-video-splitter.com'),
                    'MONGO_URL': os.environ.get('MONGO_URL', ''),
                    'SES_SENDER_EMAIL': os.environ.get('SES_SENDER_EMAIL', '')
                }
            }
        )
        
        print(f"✅ Function configuration updated!")
        print(f"Timeout: {config_response.get('Timeout')} seconds")
        print(f"Memory: {config_response.get('MemorySize')} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying Lambda function: {str(e)}")
        return False

def main():
    """Main deployment process"""
    
    print("🎯 Lambda Authentication System Deployment")
    print("=" * 50)
    
    # Check if lambda_function.py exists
    if not os.path.exists('lambda_function.py'):
        print("❌ lambda_function.py not found in current directory")
        sys.exit(1)
    
    try:
        # Create package
        zip_path = create_lambda_package()
        
        # Deploy
        success = deploy_lambda_function(zip_path)
        
        # Cleanup
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"🧹 Cleaned up {zip_path}")
        
        if success:
            print("\n🎉 Deployment completed successfully!")
            print("📝 What was deployed:")
            print("  ✅ Lambda function with authentication code")
            print("  ✅ PyJWT 2.8.0 for JWT token handling")
            print("  ✅ bcrypt 4.1.2 for password hashing")
            print("  ✅ pymongo 4.6.1 for MongoDB connectivity")
            print("  ✅ Updated function configuration (30s timeout, 512MB memory)")
            print("\n🔧 Next steps:")
            print("  1. Set environment variables in AWS Lambda console if needed")
            print("  2. Test authentication endpoints")
            print("  3. Deploy frontend with authentication UI")
            
        else:
            print("\n❌ Deployment failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()