#!/bin/bash

# AWS Amplify Deployment Script for Video Splitter Pro
# This script deploys the Video Splitter application to AWS Amplify

set -e

echo "🚀 Starting AWS Amplify deployment for Video Splitter Pro..."

# Configuration
BUCKET_NAME="videosplitter-storage-1751560247"
LAMBDA_FUNCTION_NAME="videosplitter-api"
REGION="us-east-1"

# Step 1: Create and deploy Lambda function
echo "📦 Creating Lambda deployment package..."

# Create temp directory for Lambda package
mkdir -p /tmp/lambda-deploy
cp /app/lambda_function.py /tmp/lambda-deploy/

# Create requirements.txt for Lambda
cat > /tmp/lambda-deploy/requirements.txt << EOF
boto3>=1.26.0
botocore>=1.29.0
EOF

# Create deployment package
cd /tmp/lambda-deploy
zip -r lambda-deployment-package.zip .

echo "⚡ Deploying Lambda function..."

# Create or update Lambda function
aws lambda create-function \
  --function-name $LAMBDA_FUNCTION_NAME \
  --runtime python3.9 \
  --role arn:aws:iam::756530070939:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-deployment-package.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{S3_BUCKET=$BUCKET_NAME}" \
  --region $REGION || \
aws lambda update-function-code \
  --function-name $LAMBDA_FUNCTION_NAME \
  --zip-file fileb://lambda-deployment-package.zip \
  --region $REGION

echo "✅ Lambda function deployed: $LAMBDA_FUNCTION_NAME"

# Step 2: Create API Gateway
echo "🌐 Creating API Gateway..."

# Create API Gateway
API_ID=$(aws apigateway create-rest-api \
  --name "videosplitter-api" \
  --description "Video Splitter Pro API" \
  --region $REGION \
  --query 'id' --output text) || echo "API Gateway may already exist"

if [ ! -z "$API_ID" ]; then
  echo "✅ API Gateway created: $API_ID"
  
  # Get root resource ID
  ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query 'items[?path==`/`].id' --output text)
  
  # Create /api resource
  API_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part "api" \
    --region $REGION \
    --query 'id' --output text)
  
  # Create {proxy+} resource for all API routes
  PROXY_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $API_RESOURCE_ID \
    --path-part "{proxy+}" \
    --region $REGION \
    --query 'id' --output text)
  
  # Create ANY method for proxy resource
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $REGION
  
  # Set up Lambda integration
  LAMBDA_ARN="arn:aws:lambda:$REGION:756530070939:function:$LAMBDA_FUNCTION_NAME"
  
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PROXY_RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
    --region $REGION
  
  # Add Lambda permission for API Gateway
  aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION_NAME \
    --statement-id "apigateway-invoke" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:756530070939:$API_ID/*/*" \
    --region $REGION || echo "Permission may already exist"
  
  # Deploy API
  aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION
  
  API_GATEWAY_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
  echo "✅ API Gateway deployed: $API_GATEWAY_URL"
  
  # Save API Gateway URL for frontend
  echo "REACT_APP_API_GATEWAY_URL=$API_GATEWAY_URL" > /app/frontend/.env.aws
  echo "REACT_APP_S3_BUCKET=$BUCKET_NAME" >> /app/frontend/.env.aws
  echo "REACT_APP_AWS_REGION=$REGION" >> /app/frontend/.env.aws
fi

# Step 3: Prepare frontend for Amplify hosting
echo "🎨 Preparing frontend for AWS Amplify hosting..."

cd /app/frontend

# Install dependencies
echo "📦 Installing frontend dependencies..."
yarn install

# Copy AWS-ready App.js
cp src/App.amplify.js src/App.js

# Create AWS environment file
cp .env.aws .env

# Build the application
echo "🔨 Building frontend application..."
yarn build

echo "✅ Frontend build completed"

# Step 4: Create amplify.yml for CI/CD
cat > /app/amplify.yml << EOF
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - yarn install
    build:
      commands:
        - cd frontend
        - yarn build
  artifacts:
    baseDirectory: frontend/build
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
EOF

echo "✅ Amplify configuration created"

# Step 5: Output deployment information
echo ""
echo "🎉 AWS Amplify deployment preparation completed!"
echo ""
echo "📋 Deployment Summary:"
echo "  • S3 Bucket: $BUCKET_NAME"
echo "  • Lambda Function: $LAMBDA_FUNCTION_NAME"
if [ ! -z "$API_GATEWAY_URL" ]; then
echo "  • API Gateway: $API_GATEWAY_URL"
fi
echo "  • Frontend build: /app/frontend/build/"
echo ""
echo "📝 Next Steps:"
echo "  1. Create a new Amplify app in AWS Console"
echo "  2. Connect your GitHub repository (if available)"
echo "  3. Or upload the frontend/build folder directly"
echo "  4. Set environment variables in Amplify Console:"
echo "     - REACT_APP_API_GATEWAY_URL=$API_GATEWAY_URL"
echo "     - REACT_APP_S3_BUCKET=$BUCKET_NAME"
echo "     - REACT_APP_AWS_REGION=$REGION"
echo ""
echo "🌐 For manual hosting, upload the contents of frontend/build/ to:"
echo "   - AWS Amplify Console"
echo "   - AWS S3 static website hosting"
echo "   - Or any static hosting service"
echo ""

# Save deployment info
cat > /app/DEPLOYMENT_INFO.md << EOF
# AWS Amplify Deployment Information

## Resources Created:
- **S3 Bucket**: $BUCKET_NAME
- **Lambda Function**: $LAMBDA_FUNCTION_NAME
$(if [ ! -z "$API_GATEWAY_URL" ]; then echo "- **API Gateway**: $API_GATEWAY_URL"; fi)

## Frontend Configuration:
Environment variables set in \`frontend/.env.aws\`:
\`\`\`
REACT_APP_API_GATEWAY_URL=$API_GATEWAY_URL
REACT_APP_S3_BUCKET=$BUCKET_NAME
REACT_APP_AWS_REGION=$REGION
\`\`\`

## Deployment Status:
- ✅ Lambda function deployed
$(if [ ! -z "$API_GATEWAY_URL" ]; then echo "- ✅ API Gateway configured"; else echo "- ⚠️  API Gateway setup needed"; fi)
- ✅ Frontend built for production
- ✅ S3 bucket configured with CORS

## Next Steps:
1. Deploy frontend to AWS Amplify Console
2. Test video upload and processing
3. Configure custom domain (optional)
4. Set up monitoring and logging

## Testing:
Test the API Gateway endpoint:
\`\`\`bash
curl $API_GATEWAY_URL/api/
\`\`\`

Expected response:
\`\`\`json
{"message": "Video Splitter Pro API - AWS Lambda"}
\`\`\`
EOF

echo "💾 Deployment information saved to DEPLOYMENT_INFO.md"
echo ""
echo "🚀 Your Video Splitter Pro is ready for AWS Amplify!"