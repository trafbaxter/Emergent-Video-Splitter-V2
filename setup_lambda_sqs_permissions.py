#!/usr/bin/env python3
"""
Setup Lambda SQS Permissions for FFmpeg Lambda
Adds necessary IAM permissions for SQS integration
"""

import boto3
import json

# Configuration
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'
REGION = 'us-east-1'

def setup_lambda_sqs_permissions():
    """Add SQS permissions to FFmpeg Lambda execution role"""
    print("🔧 Setting up Lambda SQS Permissions")
    print("=" * 50)
    
    # Initialize clients
    lambda_client = boto3.client('lambda', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    
    try:
        # Step 1: Get Lambda function configuration
        print(f"📋 Getting Lambda function configuration: {FFMPEG_LAMBDA_FUNCTION}")
        lambda_config = lambda_client.get_function(FunctionName=FFMPEG_LAMBDA_FUNCTION)
        role_arn = lambda_config['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        print(f"✅ Lambda execution role: {role_name}")
        
        # Step 2: Create SQS policy
        print("\n📋 Creating SQS policy for Lambda...")
        sqs_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility"
                    ],
                    "Resource": [
                        f"arn:aws:sqs:{REGION}:*:video-processing-queue",
                        f"arn:aws:sqs:{REGION}:*:video-processing-dlq"
                    ]
                }
            ]
        }
        
        # Step 3: Create/attach policy
        policy_name = 'VideoSplitterSQSPolicy'
        try:
            # Try to create the policy
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(sqs_policy),
                Description='SQS permissions for Video Splitter FFmpeg Lambda'
            )
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ Created policy: {policy_arn}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            # Policy already exists, get its ARN
            account_id = boto3.client('sts').get_caller_identity()['Account']
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            print(f"⚠️  Policy already exists: {policy_arn}")
        
        # Step 4: Attach policy to role
        print(f"\n📋 Attaching policy to role: {role_name}")
        try:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print("✅ Policy attached successfully")
        except iam_client.exceptions.NoSuchEntityException:
            print(f"❌ Role {role_name} not found")
            return False
        except Exception as e:
            if 'already attached' in str(e).lower():
                print("⚠️  Policy already attached to role")
            else:
                raise e
        
        # Step 5: Wait for permissions to propagate
        print("\n📋 Waiting for permissions to propagate...")
        import time
        time.sleep(10)
        print("✅ Permissions should now be active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up permissions: {e}")
        return False

if __name__ == "__main__":
    success = setup_lambda_sqs_permissions()
    if success:
        print("\n🎉 Lambda SQS permissions configured successfully!")
        print("You can now run setup_sqs_infrastructure.py again to create the event source mapping")
    else:
        print("\n❌ Failed to configure permissions")