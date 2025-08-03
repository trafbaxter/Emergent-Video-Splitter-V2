#!/usr/bin/env python3
"""
Fix Lambda Permissions
Adds lambda:InvokeFunction permission to the main Lambda role
"""

import boto3
import json

def fix_lambda_permissions():
    """Add Lambda invoke permissions to the main Lambda role"""
    
    iam_client = boto3.client('iam')
    lambda_client = boto3.client('lambda')
    
    try:
        # Get main Lambda function's role
        main_response = lambda_client.get_function(FunctionName='videosplitter-api')
        main_role_arn = main_response['Configuration']['Role']
        role_name = main_role_arn.split('/')[-1]
        
        print(f"🔧 Adding Lambda invoke permission to role: {role_name}")
        
        # Create inline policy for Lambda invocation
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": [
                        "arn:aws:lambda:us-east-1:*:function:ffmpeg-converter"
                    ]
                }
            ]
        }
        
        # Attach the policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='LambdaInvokeFFmpegPolicy',
            PolicyDocument=json.dumps(policy_document)
        )
        
        print("✅ Lambda invoke permission added successfully!")
        print("   Policy: LambdaInvokeFFmpegPolicy")
        print("   Resource: ffmpeg-converter function")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding Lambda permissions: {e}")
        return False

if __name__ == "__main__":
    print("=== Fixing Lambda Permissions ===")
    
    success = fix_lambda_permissions()
    
    if success:
        print("\n✅ Lambda permissions fixed!")
        print("\n🎯 Next step: Test video upload with real FFmpeg processing")
    else:
        print("\n❌ Failed to fix Lambda permissions!")
        print("   You may need to add this permission manually in AWS Console")