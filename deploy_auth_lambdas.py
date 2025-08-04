#!/usr/bin/env python3
"""
Deploy authentication Lambda functions to AWS
"""
import boto3
import zipfile
import os
import json
import tempfile
import shutil
from datetime import datetime

def deploy_auth_lambdas():
    """Deploy all authentication Lambda functions"""
    
    # AWS credentials (same as main Lambda)
    aws_access_key = 'REDACTED_AWS_KEY'
    aws_secret_key = 'kSLXhxXDBZjgxZF9nHZHG8cZKrHM6KrNKv4gCXBE'
    region = 'us-east-1'
    
    # Initialize AWS clients
    lambda_client = boto3.client(
        'lambda',
        region_name=region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    # Lambda function configurations
    lambda_configs = [
        {
            'function_name': 'auth-register',
            'handler': 'auth_lambda_register.lambda_handler',
            'description': 'User registration with email verification',
            'source_file': 'auth_lambda_register.py'
        },
        {
            'function_name': 'auth-login',
            'handler': 'auth_lambda_login.lambda_handler', 
            'description': 'User login and JWT token generation',
            'source_file': 'auth_lambda_login.py'
        },
        {
            'function_name': 'auth-verify-email',
            'handler': 'auth_lambda_verify_email.lambda_handler',
            'description': 'Email verification token validation',
            'source_file': 'auth_lambda_verify_email.py'
        },
        {
            'function_name': 'auth-jwt-authorizer',
            'handler': 'auth_lambda_jwt_authorizer.lambda_handler',
            'description': 'JWT token authorizer for API Gateway',
            'source_file': 'auth_lambda_jwt_authorizer.py'
        }
    ]
    
    print("🚀 Starting authentication Lambda deployment...")
    
    # Environment variables for Lambda functions
    env_vars = {
        'MONGO_URL': 'mongodb://3.235.150.62:27017',  # Use your MongoDB connection
        'JWT_SECRET': 'tads-video-splitter-jwt-secret-2025-change-in-production',
        'JWT_REFRESH_SECRET': 'tads-video-splitter-refresh-secret-2025-change-in-production',
        'AWS_REGION': region
    }
    
    # Deploy each Lambda function
    for config in lambda_configs:
        try:
            print(f"\n📦 Deploying {config['function_name']}...")
            
            # Create deployment package
            zip_buffer = create_deployment_package(config['source_file'])
            
            # Check if function exists
            function_exists = check_function_exists(lambda_client, config['function_name'])
            
            if function_exists:
                # Update existing function
                print(f"  ⬆️  Updating existing function...")
                response = lambda_client.update_function_code(
                    FunctionName=config['function_name'],
                    ZipFile=zip_buffer
                )
                
                # Update configuration
                lambda_client.update_function_configuration(
                    FunctionName=config['function_name'],
                    Environment={'Variables': env_vars},
                    Description=config['description'],
                    Timeout=30,
                    MemorySize=256
                )
                
            else:
                # Create new function
                print(f"  🆕 Creating new function...")
                response = lambda_client.create_function(
                    FunctionName=config['function_name'],
                    Runtime='python3.9',
                    Role='arn:aws:iam::756530070939:role/lambda-execution-role',  # Use existing role
                    Handler=config['handler'],
                    Code={'ZipFile': zip_buffer},
                    Description=config['description'],
                    Timeout=30,
                    MemorySize=256,
                    Environment={'Variables': env_vars},
                    Publish=True
                )
            
            print(f"  ✅ {config['function_name']} deployed successfully!")
            print(f"     ARN: {response['FunctionArn']}")
            
        except Exception as e:
            print(f"  ❌ Error deploying {config['function_name']}: {str(e)}")
    
    print(f"\n🎯 Authentication Lambda deployment completed!")
    print(f"📋 Next steps:")
    print(f"1. Configure API Gateway routes for authentication endpoints")
    print(f"2. Set up domain verification in AWS SES")
    print(f"3. Update frontend to use authentication endpoints")

def create_deployment_package(source_file):
    """Create Lambda deployment ZIP package"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy source file
        shutil.copy(source_file, temp_dir)
        
        # Install dependencies
        requirements = [
            'pymongo==4.5.0',
            'bcrypt==4.0.1', 
            'PyJWT==2.8.0',
            'boto3==1.28.0'
        ]
        
        # Create requirements.txt
        req_file = os.path.join(temp_dir, 'requirements.txt')
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        # Install packages
        os.system(f'pip install -r {req_file} -t {temp_dir}')
        
        # Create ZIP file
        zip_buffer = b''
        with tempfile.NamedTemporaryFile() as zip_file:
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.py') or not file.startswith('.'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            
            zip_file.seek(0)
            zip_buffer = zip_file.read()
    
    return zip_buffer

def check_function_exists(lambda_client, function_name):
    """Check if Lambda function already exists"""
    try:
        lambda_client.get_function(FunctionName=function_name)
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        return False
    except Exception:
        return False

if __name__ == "__main__":
    deploy_auth_lambdas()