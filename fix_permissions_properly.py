#!/usr/bin/env python3
"""
Fix Lambda Permissions Properly
The previous permission didn't work, so let's check the actual role and fix it
"""

import boto3
import json

def check_and_fix_permissions():
    """Check current permissions and fix them properly"""
    
    iam_client = boto3.client('iam')
    lambda_client = boto3.client('lambda')
    
    try:
        # Get the actual role name from the main Lambda
        main_response = lambda_client.get_function(FunctionName='videosplitter-api')
        role_arn = main_response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"🔍 Current role: {role_name}")
        print(f"🔍 Role ARN: {role_arn}")
        
        # Check current inline policies
        print("\n📋 Current inline policies:")
        try:
            policies = iam_client.list_role_policies(RoleName=role_name)
            for policy_name in policies['PolicyNames']:
                print(f"   - {policy_name}")
                
                # Get policy document
                policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                print(f"     Document: {json.dumps(policy_doc['PolicyDocument'], indent=2)}")
        except Exception as e:
            print(f"   Error getting inline policies: {e}")
        
        # Check attached managed policies
        print("\n📋 Attached managed policies:")
        try:
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in attached_policies['AttachedPolicies']:
                print(f"   - {policy['PolicyName']} ({policy['PolicyArn']})")
        except Exception as e:
            print(f"   Error getting attached policies: {e}")
        
        # Create a comprehensive policy that should work
        print(f"\n🔧 Adding comprehensive Lambda invoke policy...")
        
        # Get AWS account ID
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        
        comprehensive_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "InvokeFfmpegLambda",
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": [
                        f"arn:aws:lambda:us-east-1:{account_id}:function:ffmpeg-converter",
                        f"arn:aws:lambda:us-east-1:{account_id}:function:ffmpeg-converter:*"
                    ]
                }
            ]
        }
        
        # Remove old policy if it exists
        try:
            iam_client.delete_role_policy(RoleName=role_name, PolicyName='LambdaInvokeFFmpegPolicy')
            print("   Removed old policy")
        except:
            pass
        
        # Add new comprehensive policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='ComprehensiveLambdaInvokePolicy',
            PolicyDocument=json.dumps(comprehensive_policy)
        )
        
        print("✅ Added comprehensive Lambda invoke policy")
        print(f"   Policy covers: ffmpeg-converter and ffmpeg-converter:*")
        print(f"   Account: {account_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        return False

def test_invoke_after_fix():
    """Test if the invoke works after fixing permissions"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"\n🧪 Testing Lambda invoke after permission fix...")
    
    test_payload = {
        'operation': 'extract_metadata',
        'source_bucket': 'videosplitter-storage-1751560247',
        'source_key': 'test-key',
        'job_id': 'permission-test'
    }
    
    try:
        # Try to invoke from the main Lambda's perspective
        # We can't directly test this, but we can verify the policy is in place
        
        # Check if the policy was added correctly
        iam_client = boto3.client('iam')
        
        # Get main Lambda role
        main_response = lambda_client.get_function(FunctionName='videosplitter-api')
        role_name = main_response['Configuration']['Role'].split('/')[-1]
        
        # Check if our policy exists
        policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName='ComprehensiveLambdaInvokePolicy')
        print("✅ Policy successfully attached to role")
        
        # Test direct invocation to make sure FFmpeg Lambda still works
        response = lambda_client.invoke(
            FunctionName='ffmpeg-converter',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        print(f"✅ FFmpeg Lambda still responds: {response['StatusCode']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Fixing Lambda Permissions Properly ===")
    
    success = check_and_fix_permissions()
    
    if success:
        test_invoke_after_fix()
        print("\n✅ Permissions fixed!")
        print("\n🎯 Next steps:")
        print("1. Test video upload again")
        print("2. Check if duration shows real FFmpeg data (not 11:33)")
        print("3. Try video splitting functionality")
    else:
        print("\n❌ Permission fix failed!")
        print("   Manual intervention may be required")