#!/usr/bin/env python3
"""
Update the Lambda function with authentication dependencies
"""
import boto3
import os

def update_lambda_function():
    """Update the Lambda function with authentication dependencies"""
    
    # Initialize Lambda client (uses default AWS credentials)
    lambda_client = boto3.client('lambda')
    
    try:
        print("🚀 Updating Lambda function with authentication dependencies...")
        
        # Update function code with dependencies
        with open('lambda-update-with-deps.zip', 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function code updated successfully!")
        print(f"Function ARN: {response.get('FunctionArn')}")
        print(f"Code Size: {response.get('CodeSize')} bytes ({response.get('CodeSize')/(1024*1024):.2f} MB)")
        print(f"Last Modified: {response.get('LastModified')}")
        
        # Update function configuration
        print("🔧 Updating Lambda function configuration...")
        
        env_vars = {
            'MONGO_URL': 'mongodb://3.235.150.62:27017',
            'JWT_SECRET': 'tads-video-splitter-jwt-secret-2025-change-in-production',
            'JWT_REFRESH_SECRET': 'tads-video-splitter-refresh-secret-2025-change-in-production'
        }
        
        config_response = lambda_client.update_function_configuration(
            FunctionName='videosplitter-api',
            Environment={'Variables': env_vars},
            Timeout=30,
            MemorySize=512  # Increase memory for dependencies
        )
        
        print(f"✅ Lambda function configuration updated!")
        print(f"Runtime: {config_response.get('Runtime')}")
        print(f"Memory: {config_response.get('MemorySize')} MB")
        print(f"Timeout: {config_response.get('Timeout')} seconds")
        print("📝 Environment variables configured for authentication")
        
        # Clean up
        if os.path.exists('lambda-update-with-deps.zip'):
            os.remove('lambda-update-with-deps.zip')
        
        print("\n🎯 Authentication system deployment completed!")
        print("💡 Ready to test:")
        print("  - User registration: POST /api/auth/register")
        print("  - User login: POST /api/auth/login")
        print("  - Email verification: GET /api/auth/verify-email")
        print("  - Protected endpoints now require JWT tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Lambda function update failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_lambda_function()
    
    if success:
        print("\n🎉 Success! Authentication system is now deployed.")
    else:
        print("\n❌ Deployment failed. Please check the error above.")