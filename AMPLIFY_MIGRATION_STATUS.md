# AWS Amplify Migration Guide for Video Splitter Pro

## Current Status: Infrastructure Setup Complete

### AWS Resources Created:
1. ✅ **S3 Bucket**: `videosplitter-storage-1751560247`
   - CORS configured for video uploads
   - Bucket policy for video files

2. ✅ **IAM Role**: `lambda-execution-role`
   - Lambda execution permissions
   - S3 full access permissions

### Next Steps Required:

#### 1. MongoDB Atlas Setup (Required)
You need to create a MongoDB Atlas cluster to replace the local MongoDB:

1. Go to https://cloud.mongodb.com/
2. Create a free account or sign in
3. Create a new cluster (Free tier is fine)
4. Get the connection string in format:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/videosplitter?retryWrites=true&w=majority
   ```

#### 2. FastAPI Backend Deployment Options:

**Option A: AWS Lambda (Recommended)**
- Convert FastAPI to Lambda function
- Use AWS API Gateway
- Serverless and cost-effective

**Option B: AWS App Runner**
- Deploy as containerized service
- Full FastAPI compatibility
- Easier migration

**Option C: Amazon ECS**
- Full container orchestration
- More complex but highly scalable

#### 3. Frontend Deployment:
- AWS Amplify Hosting
- Static site hosting with CI/CD
- Custom domain support

### Configuration Updates Needed:

1. **Backend Environment Variables:**
   ```
   MONGO_URL=<MongoDB Atlas connection string>
   AWS_S3_BUCKET=videosplitter-storage-1751560247
   AWS_REGION=us-east-1
   ```

2. **Frontend Environment Variables:**
   ```
   REACT_APP_BACKEND_URL=<API Gateway URL or App Runner URL>
   REACT_APP_S3_BUCKET=videosplitter-storage-1751560247
   ```

### Files Created:
- `/app/bucket-name.txt` - Contains S3 bucket name
- IAM roles and policies configured in AWS

### What I Need From You:
1. **MongoDB Atlas connection string** (after you create the cluster)
2. **Preferred deployment method** for FastAPI backend:
   - Lambda (serverless, cheapest)
   - App Runner (easiest migration)
   - ECS (most scalable)

Once you provide these, I'll complete the migration!