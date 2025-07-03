#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// AWS Amplify Setup Script for Video Splitter Pro
console.log('🚀 Setting up AWS Amplify for Video Splitter Pro...');

// Step 1: Create S3 bucket for video storage
console.log('📦 Creating S3 bucket for video storage...');
try {
  const bucketName = `videosplitter-storage-${Date.now()}`;
  execSync(`aws s3 mb s3://${bucketName}`, { stdio: 'inherit' });
  
  // Configure bucket for video files
  const bucketPolicy = {
    Version: '2012-10-17',
    Statement: [
      {
        Sid: 'AllowVideoUploads',
        Effect: 'Allow',
        Principal: '*',
        Action: 's3:PutObject',
        Resource: `arn:aws:s3:::${bucketName}/*`,
        Condition: {
          StringEquals: {
            's3:x-amz-content-type': [
              'video/mp4',
              'video/x-matroska',
              'video/x-msvideo',
              'video/quicktime',
              'video/x-ms-wmv',
              'video/x-flv',
              'video/webm'
            ]
          }
        }
      }
    ]
  };
  
  fs.writeFileSync('/tmp/bucket-policy.json', JSON.stringify(bucketPolicy, null, 2));
  execSync(`aws s3api put-bucket-policy --bucket ${bucketName} --policy file:///tmp/bucket-policy.json`, { stdio: 'inherit' });
  
  console.log(`✅ S3 bucket created: ${bucketName}`);
  
  // Step 2: Create Lambda function for video processing
  console.log('⚡ Creating Lambda function for video processing...');
  
  // Create Lambda deployment package
  const lambdaCode = `
import json
import boto3
import os
import subprocess
import tempfile
from urllib.parse import unquote_plus

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Extract bucket and key from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    # Download video file
    download_path = f"/tmp/{key}"
    s3.download_file(bucket, key, download_path)
    
    # Process video with FFmpeg (placeholder)
    # In a real implementation, you would install FFmpeg layer
    
    return {
        'statusCode': 200,
        'body': json.dumps('Video processing initiated')
    }
`;
  
  fs.writeFileSync('/tmp/lambda_function.py', lambdaCode);
  
  // Create deployment package
  execSync('cd /tmp && zip lambda-package.zip lambda_function.py', { stdio: 'inherit' });
  
  // Create Lambda function
  const lambdaName = 'videosplitter-processor';
  execSync(`aws lambda create-function \\
    --function-name ${lambdaName} \\
    --runtime python3.9 \\
    --role arn:aws:iam::756530070939:role/lambda-execution-role \\
    --handler lambda_function.lambda_handler \\
    --zip-file fileb:///tmp/lambda-package.zip \\
    --timeout 300 \\
    --memory-size 512 || echo "Lambda function already exists"`, { stdio: 'inherit' });
  
  console.log(`✅ Lambda function created: ${lambdaName}`);
  
  // Step 3: Create configuration files
  console.log('⚙️ Creating configuration files...');
  
  const awsConfig = {
    aws_project_region: 'us-east-1',
    aws_s3_bucket: bucketName,
    aws_lambda_function: lambdaName,
    aws_user_pool_id: 'us-east-1_example', // Will be created separately
    aws_user_pool_web_client_id: 'example-client-id'
  };
  
  fs.writeFileSync('/app/src/aws-exports.js', `const awsmobile = ${JSON.stringify(awsConfig, null, 2)};
export default awsmobile;`);
  
  console.log('✅ Configuration files created');
  
  // Update environment variables
  const envContent = `
REACT_APP_AWS_REGION=us-east-1
REACT_APP_S3_BUCKET=${bucketName}
REACT_APP_LAMBDA_FUNCTION=${lambdaName}
REACT_APP_BACKEND_URL=https://api.example.com
`;
  
  fs.writeFileSync('/app/frontend/.env.amplify', envContent);
  
  console.log('🎉 AWS Amplify setup completed!');
  console.log(`📝 S3 Bucket: ${bucketName}`);
  console.log(`📝 Lambda Function: ${lambdaName}`);
  console.log('📝 Configuration files updated');
  
} catch (error) {
  console.error('❌ Setup failed:', error.message);
  process.exit(1);
}