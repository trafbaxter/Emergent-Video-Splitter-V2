#!/usr/bin/env python3
"""
Update the Lambda function with the fixed CORS configuration
"""
import boto3
import zipfile
import sys
import os

def update_lambda_function():
    """Update the Lambda function with CORS fixes"""
    
    # Create a zip file with the updated lambda function
    with zipfile.ZipFile('lambda-update.zip', 'w') as zip_file:
        zip_file.write('lambda_function.py')
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda')
    
    try:
        # Update function code
        with open('lambda-update.zip', 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Lambda function updated successfully!")
        print(f"Function ARN: {response.get('FunctionArn')}")
        print(f"Last Modified: {response.get('LastModified')}")
        print(f"Runtime: {response.get('Runtime')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda function: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Updating Lambda function with CORS fixes...")
    success = update_lambda_function()
    
    if success:
        print("✅ Lambda function update completed successfully!")
        print("📝 CORS fixes applied:")
        print("  - Added OPTIONS preflight request handling")
        print("  - Updated CORS headers for your domain")
        print("  - Fixed Access-Control-Allow-Origin")
        print("🎯 Next step: Test video upload from your Amplify app")
    else:
        print("❌ Lambda function update failed!")
        sys.exit(1)