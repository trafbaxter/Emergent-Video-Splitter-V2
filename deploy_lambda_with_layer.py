#!/usr/bin/env python3
"""
Deploy Lambda with proper dependency layer
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

def create_dependency_layer():
    """Create a Lambda layer with all dependencies"""
    
    print("🔧 Creating Lambda layer with dependencies...")
    
    # Create temp directory for layer
    temp_dir = tempfile.mkdtemp()
    layer_dir = os.path.join(temp_dir, 'python')
    os.makedirs(layer_dir)
    
    try:
        # Install dependencies to layer directory
        print("📥 Installing dependencies for Lambda layer...")
        
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', 'requirements.txt',
            '--target', layer_dir,
            '--no-cache-dir'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return None
        
        print("✅ Dependencies installed successfully")
        
        # Create layer zip
        layer_zip = 'lambda-layer.zip'
        print(f"🗜️  Creating layer package: {layer_zip}")
        
        with zipfile.ZipFile(layer_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arcname)
        
        layer_size = os.path.getsize(layer_zip) / (1024 * 1024)  # MB
        print(f"📊 Layer size: {layer_size:.2f} MB")
        
        return layer_zip
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def deploy_lambda_layer(layer_zip):
    """Deploy or update Lambda layer"""
    
    print("🚀 Deploying Lambda layer...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        with open(layer_zip, 'rb') as zip_file:
            response = lambda_client.publish_layer_version(
                LayerName='video-splitter-auth-deps',
                Description='Authentication dependencies for Video Splitter (PyJWT, bcrypt, pymongo)',
                Content={'ZipFile': zip_file.read()},
                CompatibleRuntimes=['python3.9'],
                CompatibleArchitectures=['x86_64']
            )
        
        layer_arn = response['LayerVersionArn']
        print(f"✅ Layer deployed successfully!")
        print(f"Layer ARN: {layer_arn}")
        print(f"Version: {response['Version']}")
        
        return layer_arn
        
    except Exception as e:
        print(f"❌ Error deploying layer: {str(e)}")
        return None

def update_lambda_with_layer(layer_arn):
    """Update Lambda function to use the layer"""
    
    print("🔗 Attaching layer to Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Get current function config
        current_config = lambda_client.get_function_configuration(
            FunctionName='videosplitter-api'
        )
        
        # Get existing layers and add our new one
        existing_layers = current_config.get('Layers', [])
        layer_arns = [layer['Arn'] for layer in existing_layers]
        
        # Add our auth layer if not already present
        if layer_arn not in layer_arns:
            layer_arns.append(layer_arn)
        
        # Update function configuration
        response = lambda_client.update_function_configuration(
            FunctionName='videosplitter-api',
            Layers=layer_arns
        )
        
        print(f"✅ Layer attached successfully!")
        print(f"Total layers: {len(response.get('Layers', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error attaching layer: {str(e)}")
        return False

def deploy_lambda_function():
    """Deploy the Lambda function code"""
    
    print("📄 Deploying Lambda function code...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Create zip with just the Lambda function
        with zipfile.ZipFile('lambda-function.zip', 'w') as zip_file:
            zip_file.write('lambda_function.py', 'lambda_function.py')
        
        # Update function code
        with open('lambda-function.zip', 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName='videosplitter-api',
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Function code updated!")
        print(f"Code Size: {response.get('CodeSize')} bytes")
        
        # Cleanup
        os.remove('lambda-function.zip')
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying function: {str(e)}")
        return False

def test_authentication():
    """Test the authentication system"""
    
    print("\n🧪 Testing authentication system...")
    
    lambda_client = boto3.client('lambda')
    
    test_cases = [
        {
            "name": "Basic function execution",
            "payload": {"httpMethod": "GET", "path": "/", "headers": {}}
        },
        {
            "name": "Health check",
            "payload": {"httpMethod": "GET", "path": "/api/", "headers": {}}
        }
    ]
    
    for test in test_cases:
        try:
            print(f"Testing: {test['name']}")
            
            response = lambda_client.invoke(
                FunctionName='videosplitter-api',
                Payload=json.dumps(test['payload'])
            )
            
            status_code = response.get('StatusCode', 0)
            payload = response['Payload'].read().decode('utf-8')
            
            if status_code == 200:
                # Check if the response contains error messages
                if 'errorMessage' in payload and 'ImportModuleError' in payload:
                    print(f"❌ {test['name']}: Import error still present")
                    print(f"Response: {payload[:200]}...")
                elif 'errorMessage' in payload:
                    print(f"⚠️  {test['name']}: Function error (but imports work)")
                    print(f"Response: {payload[:200]}...")
                else:
                    print(f"✅ {test['name']}: Success!")
            else:
                print(f"❌ {test['name']}: Status {status_code}")
                
        except Exception as e:
            print(f"❌ {test['name']}: {str(e)}")

def main():
    """Main deployment process"""
    
    print("🎯 Lambda Authentication System with Layer Deployment")
    print("=" * 60)
    
    try:
        # Step 1: Create and deploy layer
        layer_zip = create_dependency_layer()
        if not layer_zip:
            print("❌ Failed to create dependency layer")
            sys.exit(1)
        
        layer_arn = deploy_lambda_layer(layer_zip)
        if not layer_arn:
            print("❌ Failed to deploy layer")
            sys.exit(1)
        
        # Cleanup layer zip
        os.remove(layer_zip)
        
        # Step 2: Update Lambda function with layer
        if not update_lambda_with_layer(layer_arn):
            print("❌ Failed to attach layer to function")
            sys.exit(1)
        
        # Step 3: Deploy function code
        if not deploy_lambda_function():
            print("❌ Failed to deploy function code")
            sys.exit(1)
        
        # Step 4: Test the system
        test_authentication()
        
        print("\n🎉 Deployment completed successfully!")
        print("📝 What was deployed:")
        print(f"  ✅ Lambda layer with authentication dependencies")
        print(f"  ✅ Updated Lambda function with layer attached")
        print(f"  ✅ Layer ARN: {layer_arn}")
        
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()