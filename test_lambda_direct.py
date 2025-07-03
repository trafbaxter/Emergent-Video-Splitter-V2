#!/usr/bin/env python3
import boto3
import json

# Lambda function ARN
LAMBDA_FUNCTION_ARN = "arn:aws:lambda:us-east-1:756530070939:function:videosplitter-api"
# AWS Region
AWS_REGION = "us-east-1"

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

# Prepare test payload as specified in the test requirements
payload = {
    "httpMethod": "GET",
    "path": "/api",
    "headers": {}
}

print(f"Invoking Lambda function with payload: {json.dumps(payload, indent=2)}")

# Invoke Lambda function
response = lambda_client.invoke(
    FunctionName=LAMBDA_FUNCTION_ARN,
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

# Parse response
response_payload = json.loads(response['Payload'].read().decode())
print(f"Lambda response status code: {response['StatusCode']}")
print(f"Lambda response payload: {json.dumps(response_payload, indent=2)}")

# Verify response matches expected format
expected_response = {
    "statusCode": 200,
    "body": "{\"message\": \"Video Splitter Pro API - AWS Lambda\"}"
}

# Extract body as JSON for comparison
response_body = json.loads(response_payload.get('body', '{}'))
expected_body = json.loads(expected_response.get('body', '{}'))

print("\nVerification:")
print(f"Status code matches: {response_payload.get('statusCode') == expected_response.get('statusCode')}")
print(f"Body message matches: {response_body.get('message') == expected_body.get('message')}")

if (response_payload.get('statusCode') == expected_response.get('statusCode') and
    response_body.get('message') == expected_body.get('message')):
    print("\n✅ Lambda function response matches expected format")
else:
    print("\n❌ Lambda function response does not match expected format")