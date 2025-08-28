#!/usr/bin/env python3
"""
Test Lambda S3 permissions for presigned URL generation
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_BUCKET_NAME = 'videosplitter-storage-1751560247'
LAMBDA_FUNCTION_NAME = 'videosplitter-api'

def test_lambda_s3_permissions():
    """Test if Lambda has proper S3 permissions"""
    
    # Test direct S3 access with current credentials
    s3_client = boto3.client('s3')
    test_key = "uploads/43ab1ed4-1c23-488f-b29e-fbab160a0079/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"
    
    print("🔍 Testing S3 permissions with current credentials...")
    
    # Test 1: Check if we can access the object
    try:
        print(f"📋 Testing HEAD object for: {test_key}")
        response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=test_key)
        print("✅ HEAD object successful - object exists and is accessible")
        print(f"   Content-Type: {response.get('ContentType', 'Unknown')}")
        print(f"   Content-Length: {response.get('ContentLength', 'Unknown')}")
    except ClientError as e:
        print(f"❌ HEAD object failed: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False
    
    # Test 2: Test presigned URL generation
    try:
        print(f"\n📎 Testing presigned URL generation...")
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': test_key},
            ExpiresIn=3600
        )
        print("✅ Presigned URL generation successful")
        print(f"   URL: {presigned_url[:100]}...")
        
        # Test 3: Test direct access to presigned URL
        import requests
        print(f"\n🧪 Testing direct access to presigned URL...")
        
        # Use proper headers that match browser request
        headers = {
            'Origin': 'https://working.tads-video-splitter.com',
            'User-Agent': 'Mozilla/5.0 (compatible test client)',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Range': 'bytes=0-1023'  # Request first 1KB only for testing
        }
        
        try:
            response = requests.get(presigned_url, headers=headers, timeout=10)
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   🌐 CORS Origin: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
            print(f"   📄 Content-Type: {response.headers.get('Content-Type', 'None')}")
            print(f"   📏 Content-Length: {response.headers.get('Content-Length', 'None')}")
            print(f"   📦 Accept-Ranges: {response.headers.get('Accept-Ranges', 'None')}")
            
            if response.status_code == 206:  # Partial content for range request
                print("✅ SUCCESS: Presigned URL is working with range requests!")
                print("   This should enable video streaming")
                return True
            elif response.status_code == 200:
                print("✅ SUCCESS: Presigned URL is working!")
                print("   This should enable video streaming")
                return True
            elif response.status_code == 403:
                print("❌ FAILURE: Still getting 403 Forbidden")
                print("   This confirms the permissions issue")
                return False
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as request_error:
            print(f"❌ Request error: {str(request_error)}")
            return False
        
    except ClientError as e:
        print(f"❌ Presigned URL generation failed: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False
    
def check_lambda_execution_role():
    """Check Lambda execution role and permissions"""
    lambda_client = boto3.client('lambda')
    
    try:
        print(f"\n🔍 Checking Lambda execution role for: {LAMBDA_FUNCTION_NAME}")
        
        response = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        role_arn = response['Configuration']['Role']
        
        print(f"✅ Lambda Execution Role: {role_arn}")
        
        # Extract role name from ARN
        role_name = role_arn.split('/')[-1]
        print(f"   Role Name: {role_name}")
        
        # Get role details
        iam_client = boto3.client('iam')
        try:
            role_details = iam_client.get_role(RoleName=role_name)
            assume_role_policy = role_details['Role']['AssumeRolePolicyDocument']
            
            print(f"✅ Role found:")
            print(f"   Created: {role_details['Role']['CreateDate']}")
            print(f"   Path: {role_details['Role']['Path']}")
            
            # List attached policies
            policies = iam_client.list_attached_role_policies(RoleName=role_name)
            print(f"\n📋 Attached Policies:")
            for policy in policies['AttachedPolicies']:
                print(f"   📄 {policy['PolicyName']} - {policy['PolicyArn']}")
                
        except ClientError as e:
            print(f"❌ Could not get role details: {e.response['Error']['Code']}")
            
        return True
        
    except ClientError as e:
        print(f"❌ Could not get Lambda function details: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False

if __name__ == "__main__":
    print("🚀 Lambda S3 Permissions Test")
    print("=" * 50)
    
    success1 = test_lambda_s3_permissions()
    success2 = check_lambda_execution_role()
    
    print(f"\n🎯 Results:")
    print(f"   S3 Permissions Test: {'PASS' if success1 else 'FAIL'}")
    print(f"   Lambda Role Check: {'PASS' if success2 else 'FAIL'}")
    
    if not success1:
        print(f"\n💡 If presigned URLs fail with 403:")
        print(f"   1. Check Lambda execution role has s3:GetObject permission")
        print(f"   2. Verify bucket policy doesn't deny access")
        print(f"   3. Check if object was uploaded with correct permissions")
        print(f"   4. Consider temporary credentials expiry")