#!/usr/bin/env python3
"""
Remove Lambda layer and deploy clean function
"""
import boto3
import zipfile
import json

def remove_lambda_layer():
    """Remove the problematic layer from Lambda function"""
    
    print("🔧 Removing problematic Lambda layer...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Update function to remove all layers
        response = lambda_client.update_function_configuration(
            FunctionName='videosplitter-api',
            Layers=[]  # Remove all layers
        )
        
        print(f"✅ All layers removed from Lambda function!")
        print(f"Total layers: {len(response.get('Layers', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing layers: {str(e)}")
        return False

def deploy_clean_lambda():
    """Deploy Lambda function without layers"""
    
    print("📄 Deploying clean Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Create zip with just the Lambda function
        with zipfile.ZipFile('lambda-clean.zip', 'w') as zip_file:
            zip_file.write('lambda_function.py', 'lambda_function.py')
        
        # Update function code
        with open('lambda-clean.zip', 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Clean function deployed!")
        print(f"Code Size: {response.get('CodeSize')} bytes")
        
        # Cleanup
        import os
        os.remove('lambda-clean.zip')
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying function: {str(e)}")
        return False

def test_clean_function():
    """Test the clean Lambda function"""
    
    print("🧪 Testing clean Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName='videosplitter-api',
            Payload=json.dumps({"httpMethod": "GET", "path": "/api/", "headers": {}})
        )
        
        status_code = response.get('StatusCode', 0)
        payload = response['Payload'].read().decode('utf-8')
        
        if status_code == 200:
            if 'ImportModuleError' in payload:
                print("❌ Still getting import errors")
                print(f"Response: {payload[:200]}...")
                return False
            else:
                print("✅ Lambda function executing successfully!")
                print(f"Response preview: {payload[:200]}...")
                return True
        else:
            print(f"❌ Lambda execution failed with status {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main cleanup and deployment"""
    
    print("🎯 Clean Lambda Function Deployment")
    print("=" * 40)
    
    # Step 1: Remove layers
    if not remove_lambda_layer():
        print("❌ Failed to remove layers")
        return
    
    # Step 2: Deploy clean function
    if not deploy_clean_lambda():
        print("❌ Failed to deploy clean function")
        return
    
    # Step 3: Test function
    success = test_clean_function()
    
    if success:
        print("\n🎉 Clean Lambda deployment successful!")
        print("✅ Core video processing functionality should be restored")
        print("📝 Authentication features are temporarily disabled")
        print("🔧 Next: Test core video endpoints")
    else:
        print("\n❌ Lambda function still has issues")

if __name__ == "__main__":
    main()