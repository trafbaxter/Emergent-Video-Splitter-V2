#!/usr/bin/env python3
"""
Deploy Lambda function with Python dependencies
"""
import boto3
import zipfile
import os
import tempfile
import shutil
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package with dependencies"""
    
    print("📦 Creating Lambda deployment package with dependencies...")
    
    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir)
        
        # Copy main Lambda function
        shutil.copy('/app/lambda_function.py', package_dir / 'lambda_function.py')
        
        # Copy dependencies
        deps_dir = Path('/app/lambda_deps')
        if deps_dir.exists():
            print("📚 Copying Python dependencies...")
            for item in deps_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, package_dir / item.name)
                else:
                    shutil.copy(item, package_dir / item.name)
        
        # Create ZIP file
        zip_path = '/tmp/lambda_function.zip'
        print(f"🗜️  Creating ZIP package: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        # Get package size
        package_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
        print(f"📏 Package size: {package_size:.2f} MB")
        
        if package_size > 50:
            print("⚠️  Warning: Package is over 50MB, might hit Lambda limits")
        
        return zip_path

def deploy_lambda():
    """Deploy Lambda function with dependencies"""
    
    print("🚀 Deploying Lambda function with authentication dependencies...")
    
    # AWS configuration
    lambda_client = boto3.client(
        'lambda',
        region_name='us-east-1',
        aws_access_key_id='REDACTED_AWS_KEY',
        aws_secret_access_key='kSLXhxXDBZjgxZF9nHZHG8cZKrNKv4gCXBE'
    )
    
    function_name = 'videosplitter-api'
    
    try:
        # Create deployment package
        zip_path = create_lambda_package()
        
        # Read the ZIP file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Update Lambda function code
        print(f"📤 Updating Lambda function: {function_name}")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"   Function ARN: {response['FunctionArn']}")
        print(f"   Runtime: {response['Runtime']}")
        print(f"   Last Modified: {response['LastModified']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        
        # Update function configuration with environment variables
        print("🔧 Updating function configuration...")
        
        env_vars = {
            'MONGO_URL': 'mongodb://3.235.150.62:27017',
            'JWT_SECRET': 'tads-video-splitter-jwt-secret-2025-change-in-production',
            'JWT_REFRESH_SECRET': 'tads-video-splitter-refresh-secret-2025-change-in-production'
        }
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars},
            Timeout=30,
            MemorySize=512  # Increase memory for dependencies
        )
        
        print("✅ Lambda function configuration updated!")
        print("📝 Environment variables set:")
        for key, value in env_vars.items():
            masked_value = value[:10] + '...' if len(value) > 10 else value
            print(f"   {key}: {masked_value}")
        
        # Clean up
        os.remove(zip_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Lambda deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_lambda()
    if success:
        print("\n🎯 Deployment completed successfully!")
        print("💡 Next steps:")
        print("1. Test authentication endpoints")
        print("2. Verify user registration and login")
        print("3. Test protected video endpoints")
    else:
        print("\n❌ Deployment failed!")
        print("💡 Try:")
        print("1. Check AWS credentials and permissions")
        print("2. Verify Lambda function exists")
        print("3. Check dependency installation")