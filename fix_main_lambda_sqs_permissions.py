#!/usr/bin/env python3
"""
Fix Main Lambda SQS Permissions
Adds SQS SendMessage permissions to the main Lambda execution role
"""

import boto3
import json

# Configuration
MAIN_LAMBDA_FUNCTION = 'videosplitter-api'
REGION = 'us-east-1'

def fix_main_lambda_sqs_permissions():
    """Add SQS SendMessage permissions to main Lambda execution role"""
    print("🔧 Fixing Main Lambda SQS Permissions")
    print("=" * 50)
    
    # Initialize clients
    lambda_client = boto3.client('lambda', region_name=REGION)
    iam_client = boto3.client('iam', region_name=REGION)
    
    try:
        # Step 1: Get Lambda function configuration
        print(f"📋 Getting Lambda function configuration: {MAIN_LAMBDA_FUNCTION}")
        lambda_config = lambda_client.get_function(FunctionName=MAIN_LAMBDA_FUNCTION)
        role_arn = lambda_config['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        print(f"✅ Lambda execution role: {role_name}")
        
        # Step 2: Create SQS SendMessage policy for main Lambda
        print("\n📋 Creating SQS SendMessage policy for main Lambda...")
        sqs_send_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "sqs:SendMessage",
                        "sqs:GetQueueUrl",
                        "sqs:GetQueueAttributes"
                    ],
                    "Resource": [
                        f"arn:aws:sqs:{REGION}:*:video-processing-queue"
                    ]
                }
            ]
        }
        
        # Step 3: Create/attach policy
        policy_name = 'VideoSplitterMainLambdaSQSPolicy'
        try:
            # Try to create the policy
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(sqs_send_policy),
                Description='SQS SendMessage permissions for Video Splitter main Lambda'
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
        time.sleep(15)
        print("✅ Permissions should now be active")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up permissions: {e}")
        return False

if __name__ == "__main__":
    success = fix_main_lambda_sqs_permissions()
    if success:
        print("\n🎉 Main Lambda SQS permissions configured successfully!")
        print("The main Lambda can now send messages to the SQS queue")
    else:
        print("\n❌ Failed to configure permissions")