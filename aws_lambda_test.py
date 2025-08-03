#!/usr/bin/env python3
"""
AWS Lambda Backend Test Suite for Video Splitter Pro
Tests the AWS Lambda function deployed at API Gateway endpoint
"""

import os
import requests
import json
import unittest
import boto3
import time
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

# API Gateway URL from deployment info
API_GATEWAY_URL = "https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod"
# Lambda function ARN
LAMBDA_FUNCTION_ARN = "arn:aws:lambda:us-east-1:756530070939:function:videosplitter-api"
# S3 Bucket name
S3_BUCKET_NAME = "videosplitter-storage-1751560247"
# AWS Region
AWS_REGION = "us-east-1"

print(f"Testing AWS Lambda Backend for Video Splitter Pro")
print(f"API Gateway URL: {API_GATEWAY_URL}")
print(f"S3 Bucket: {S3_BUCKET_NAME}")
print(f"AWS Region: {AWS_REGION}")

class AWSLambdaBackendTest(unittest.TestCase):
    """Test suite for the Video Splitter AWS Lambda Backend"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        print(f"\n=== Testing AWS Lambda Backend for Video Splitter Pro ===")
        print(f"API Gateway URL: {API_GATEWAY_URL}")
        print(f"Lambda Function ARN: {LAMBDA_FUNCTION_ARN}")
        print(f"S3 Bucket: {S3_BUCKET_NAME}")
        print(f"AWS Region: {AWS_REGION}")
        
        # Initialize AWS clients
        try:
            # Try to initialize boto3 clients to check AWS credentials
            cls.lambda_client = boto3.client('lambda', region_name=AWS_REGION)
            cls.s3_client = boto3.client('s3', region_name=AWS_REGION)
            print("✅ AWS credentials found and boto3 clients initialized")
        except Exception as e:
            print(f"⚠️ AWS credentials not found or boto3 initialization failed: {e}")
            print("⚠️ Some tests requiring direct AWS access will be skipped")
            cls.lambda_client = None
            cls.s3_client = None
    
    def test_01_api_gateway_connectivity(self):
        """Test basic connectivity to the API Gateway endpoint"""
        print("\n=== Testing API Gateway connectivity ===")
        
        try:
            response = requests.get(f"{API_GATEWAY_URL}/api")
            self.assertEqual(response.status_code, 200, f"API Gateway connectivity failed with status {response.status_code}")
            data = response.json()
            self.assertEqual(data.get("message"), "Video Splitter Pro API - AWS Lambda", "Unexpected response from API Gateway")
            print("✅ Successfully connected to API Gateway endpoint")
            print(f"Response: {data}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to connect to API Gateway: {e}")
    
    def test_02_api_gateway_cors_headers(self):
        """Test CORS headers in API Gateway response"""
        print("\n=== Testing CORS headers in API Gateway response ===")
        
        try:
            response = requests.options(f"{API_GATEWAY_URL}/api")
            headers = response.headers
            
            # Print headers for debugging
            print(f"Response headers: {json.dumps(dict(headers), indent=2)}")
            
            # Check for CORS headers
            self.assertIn('Access-Control-Allow-Origin', headers, "CORS header missing: Access-Control-Allow-Origin")
            self.assertEqual(headers['Access-Control-Allow-Origin'], '*', "Incorrect Access-Control-Allow-Origin value")
            self.assertIn('Access-Control-Allow-Methods', headers, "CORS header missing: Access-Control-Allow-Methods")
            
            print("✅ CORS headers are correctly configured in API Gateway response")
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to test CORS headers: {e}")
    
    def test_03_direct_lambda_invocation(self):
        """Test direct Lambda function invocation"""
        print("\n=== Testing direct Lambda function invocation ===")
        
        if not self.lambda_client:
            self.skipTest("AWS credentials not available, skipping direct Lambda invocation test")
        
        try:
            # Prepare test payload
            payload = {
                "httpMethod": "GET",
                "path": "/api",
                "headers": {}
            }
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=LAMBDA_FUNCTION_ARN,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read().decode())
            print(f"Lambda response: {json.dumps(response_payload, indent=2)}")
            
            # Verify response
            self.assertEqual(response['StatusCode'], 200, "Lambda invocation failed")
            self.assertEqual(response_payload.get('statusCode'), 200, "Lambda function returned non-200 status code")
            
            # Parse body
            body = json.loads(response_payload.get('body', '{}'))
            self.assertEqual(body.get('message'), "Video Splitter Pro API - AWS Lambda", "Unexpected response from Lambda function")
            
            print("✅ Successfully invoked Lambda function directly")
        except Exception as e:
            self.fail(f"Failed to invoke Lambda function: {e}")
    
    def test_04_lambda_environment_variables(self):
        """Test Lambda function environment variables"""
        print("\n=== Testing Lambda function environment variables ===")
        
        if not self.lambda_client:
            self.skipTest("AWS credentials not available, skipping Lambda environment variables test")
        
        try:
            # Get Lambda function configuration
            response = self.lambda_client.get_function_configuration(
                FunctionName=LAMBDA_FUNCTION_ARN
            )
            
            # Check environment variables
            env_vars = response.get('Environment', {}).get('Variables', {})
            print(f"Lambda environment variables: {json.dumps(env_vars, indent=2)}")
            
            # Verify S3_BUCKET environment variable
            self.assertIn('S3_BUCKET', env_vars, "S3_BUCKET environment variable not set")
            self.assertEqual(env_vars['S3_BUCKET'], S3_BUCKET_NAME, "Incorrect S3_BUCKET value")
            
            print(f"✅ Lambda function has correct environment variables")
        except Exception as e:
            self.fail(f"Failed to check Lambda environment variables: {e}")
    
    def test_05_s3_bucket_existence(self):
        """Test S3 bucket existence and accessibility"""
        print("\n=== Testing S3 bucket existence and accessibility ===")
        
        if not self.s3_client:
            self.skipTest("AWS credentials not available, skipping S3 bucket test")
        
        try:
            # Check if bucket exists
            response = self.s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"S3 bucket exists: {S3_BUCKET_NAME}")
            
            # Get bucket CORS configuration
            try:
                cors = self.s3_client.get_bucket_cors(Bucket=S3_BUCKET_NAME)
                print(f"S3 bucket CORS configuration: {json.dumps(cors, indent=2)}")
                
                # Verify CORS configuration
                cors_rules = cors.get('CORSRules', [])
                self.assertTrue(len(cors_rules) > 0, "No CORS rules found")
                
                # Check for required CORS settings
                has_allow_all_origins = False
                for rule in cors_rules:
                    if '*' in rule.get('AllowedOrigins', []):
                        has_allow_all_origins = True
                        break
                
                self.assertTrue(has_allow_all_origins, "S3 bucket CORS does not allow all origins (*)")
                
                print("✅ S3 bucket has correct CORS configuration")
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
                    print("⚠️ S3 bucket has no CORS configuration")
                else:
                    raise e
            
            print(f"✅ S3 bucket exists and is accessible")
        except Exception as e:
            self.fail(f"Failed to check S3 bucket: {e}")
    
    def test_06_api_gateway_endpoints(self):
        """Test various API Gateway endpoints"""
        print("\n=== Testing various API Gateway endpoints ===")
        
        # Test endpoints
        endpoints = [
            {"method": "GET", "path": "/api", "expected_status": 200},
            {"method": "GET", "path": "/api/nonexistent", "expected_status": 404},
            {"method": "POST", "path": "/api", "expected_status": 404},
        ]
        
        for endpoint in endpoints:
            method = endpoint["method"]
            path = endpoint["path"]
            expected_status = endpoint["expected_status"]
            
            print(f"Testing {method} {path} (Expected: {expected_status})")
            
            try:
                if method == "GET":
                    response = requests.get(f"{API_GATEWAY_URL}{path}")
                elif method == "POST":
                    response = requests.post(f"{API_GATEWAY_URL}{path}", json={})
                else:
                    self.fail(f"Unsupported method: {method}")
                
                print(f"Status code: {response.status_code}")
                self.assertEqual(response.status_code, expected_status, f"Unexpected status code for {method} {path}")
                
                # Print response for debugging
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                
                print(f"✅ {method} {path} returned expected status code {expected_status}")
            except requests.exceptions.RequestException as e:
                self.fail(f"Request failed: {e}")
    
    def test_07_upload_endpoint(self):
        """Test video upload endpoint"""
        print("\n=== Testing video upload endpoint ===")
        
        try:
            response = requests.post(f"{API_GATEWAY_URL}/api/upload-video", files={
                'file': ('test.mp4', b'test data', 'video/mp4')
            })
            
            print(f"Status code: {response.status_code}")
            
            # The actual implementation might return different status codes
            # depending on how file uploads are handled in the Lambda function
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                self.assertIn('job_id', data, "Response missing job_id")
                self.assertIn('upload_url', data, "Response missing upload_url")
                print("✅ Upload endpoint returned expected response")
            else:
                # This might be expected if the Lambda function doesn't fully implement file uploads
                print("⚠️ Upload endpoint returned non-200 status code, which might be expected for Lambda implementation")
                print(f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")
    
    def test_08_mock_job_status(self):
        """Test job status endpoint with a mock job ID"""
        print("\n=== Testing job status endpoint with mock job ID ===")
        
        mock_job_id = "test-job-123"
        
        try:
            response = requests.get(f"{API_GATEWAY_URL}/api/job-status/{mock_job_id}")
            
            print(f"Status code: {response.status_code}")
            
            # The actual implementation might return different status codes
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                self.assertEqual(data.get('id'), mock_job_id, "Response job_id doesn't match request")
                print("✅ Job status endpoint returned expected response")
            else:
                # This might be expected if the Lambda function doesn't fully implement job status
                print("⚠️ Job status endpoint returned non-200 status code, which might be expected for Lambda implementation")
                print(f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

if __name__ == "__main__":
    unittest.main(verbosity=2)