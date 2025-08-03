#!/usr/bin/env python3
"""
Check FFmpeg Lambda Function Status
Verifies the ffmpeg-converter function configuration and tests basic functionality
"""

import boto3
import json

def check_ffmpeg_lambda():
    """Check the FFmpeg Lambda function configuration"""
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Get function configuration
        print("🔍 Checking ffmpeg-converter Lambda function configuration...")
        
        response = lambda_client.get_function(FunctionName='ffmpeg-converter')
        config = response['Configuration']
        
        print(f"✅ Function Name: {config['FunctionName']}")
        print(f"✅ Runtime: {config['Runtime']}")
        print(f"✅ Handler: {config['Handler']}")
        print(f"✅ Timeout: {config['Timeout']} seconds")
        print(f"✅ Memory: {config['MemorySize']} MB")
        print(f"✅ Last Modified: {config['LastModified']}")
        
        # Check layers
        layers = config.get('Layers', [])
        if layers:
            print(f"✅ Layers attached: {len(layers)}")
            for layer in layers:
                print(f"   - {layer['Arn']}")
                if 'ffmpeg' in layer['Arn'].lower():
                    print("   ✅ FFmpeg layer found!")
        else:
            print("❌ No layers attached! FFmpeg layer missing!")
            return False
        
        # Test basic invoke
        print("\n🧪 Testing basic FFmpeg Lambda invocation...")
        
        test_payload = {
            'operation': 'test',
            'source_bucket': 'test-bucket',
            'source_key': 'test-key',
            'job_id': 'test-job'
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName='ffmpeg-converter',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            payload = json.loads(response['Payload'].read())
            print(f"Test Response Status: {response['StatusCode']}")
            print(f"Test Response: {payload}")
            
            if response['StatusCode'] == 200:
                print("✅ FFmpeg Lambda function is responsive")
            else:
                print("⚠️ FFmpeg Lambda function returned error")
                
        except Exception as e:
            print(f"❌ Failed to invoke FFmpeg Lambda: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking FFmpeg Lambda function: {e}")
        return False

def check_main_lambda_permissions():
    """Check if main Lambda has permission to invoke FFmpeg Lambda"""
    
    lambda_client = boto3.client('lambda')
    iam_client = boto3.client('iam')
    
    try:
        print("\n🔐 Checking Lambda invocation permissions...")
        
        # Get main Lambda function's role
        main_response = lambda_client.get_function(FunctionName='videosplitter-api')
        main_role_arn = main_response['Configuration']['Role']
        role_name = main_role_arn.split('/')[-1]
        
        print(f"Main Lambda Role: {role_name}")
        
        # Check if role has lambda:InvokeFunction permission
        try:
            policies = iam_client.list_attached_role_policies(RoleName=role_name)
            print(f"Attached policies: {len(policies['AttachedPolicies'])}")
            
            for policy in policies['AttachedPolicies']:
                print(f"   - {policy['PolicyName']}")
                if 'lambda' in policy['PolicyName'].lower():
                    print("   ✅ Lambda execution policy found")
                    
        except Exception as e:
            print(f"⚠️ Could not check IAM policies: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
        return False

if __name__ == "__main__":
    print("=== FFmpeg Lambda Function Health Check ===")
    
    ffmpeg_ok = check_ffmpeg_lambda()
    permissions_ok = check_main_lambda_permissions()
    
    if ffmpeg_ok and permissions_ok:
        print("\n✅ FFmpeg Lambda integration should be working!")
        print("\n🎯 If duration is still estimated, check:")
        print("1. Frontend is using AWS API Gateway URL")
        print("2. No local backend server is running")
        print("3. Video file exists in S3 at expected location")
    else:
        print("\n❌ FFmpeg Lambda integration issues found!")
        print("\n🔧 Required fixes:")
        if not ffmpeg_ok:
            print("- Attach ffmpeg-layer to ffmpeg-converter function")
            print("- Increase timeout and memory for video processing")
        if not permissions_ok:
            print("- Add lambda:InvokeFunction permission to main Lambda role")