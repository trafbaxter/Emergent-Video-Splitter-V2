#!/usr/bin/env python3
import boto3
import sys

def deploy_lambda():
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        print('📦 Loading deployment package...')
        with open('/app/videosplitter-api-fixed.zip', 'rb') as f:
            zip_content = f.read()
        
        print(f'📤 Deploying {len(zip_content):,} bytes...')
        
        response = lambda_client.update_function_code(
            FunctionName='videosplitter-api',
            ZipFile=zip_content
        )
        
        print('✅ Deployment successful!')
        print(f'Function: {response["FunctionName"]}')
        print(f'Size: {response["CodeSize"]:,} bytes')
        return True
        
    except Exception as e:
        print(f'❌ Deployment failed: {e}')
        return False

if __name__ == '__main__':
    deploy_lambda()
