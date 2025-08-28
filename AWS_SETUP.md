# AWS Configuration for Video Merger

## Security Notice
AWS credentials are NOT stored in the codebase for security reasons. They must be provided via environment variables or AWS credential files.

## Setup Options

### Option 1: Environment Variables (Recommended for Development)
**Note**: Some environments don't allow variables starting with "AWS_". Use these variable names instead:

```bash
export ACCESS_KEY_ID="your_access_key_here"
export SECRET_ACCESS_KEY="your_secret_key_here" 
export AWS_REGION="us-east-1"
export S3_BUCKET="videosplitter-storage-1751560247"
```

**Alternative** (if your environment allows AWS_ prefixes):
```bash
export AWS_ACCESS_KEY_ID="your_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_key_here"
export AWS_REGION="us-east-1"
export S3_BUCKET="videosplitter-storage-1751560247"
```

### Option 2: AWS Credentials File
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = your_access_key_here
aws_secret_access_key = your_secret_key_here
```

Create `~/.aws/config`:
```ini
[default]
region = us-east-1
```

### Option 3: IAM Roles (Recommended for Production)
When running on AWS EC2/ECS/Lambda, use IAM roles instead of access keys.

## Variable Precedence
The application checks for credentials in this order:
1. `ACCESS_KEY_ID` and `SECRET_ACCESS_KEY` (preferred for restricted environments)
2. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (standard AWS naming)
3. AWS default credential chain (IAM roles, credentials file, etc.)

## Required AWS Permissions
The AWS user/role needs the following S3 permissions:
- `s3:GetObject`
- `s3:PutObject`
- `s3:DeleteObject`
- `s3:GeneratePresignedUrl`

For bucket: `videosplitter-storage-1751560247`

## Testing AWS Configuration
Run this command to test your AWS setup:
```bash
aws s3 ls s3://videosplitter-storage-1751560247/
```

## Application Behavior
- **With AWS credentials**: Full video merging functionality with S3 storage
- **Without AWS credentials**: Video merging will fail gracefully with appropriate error messages

## Production Deployment
For production deployments:
1. Use IAM roles instead of access keys
2. Set environment variables via your deployment platform
3. Never commit credentials to version control
4. Use AWS Secrets Manager for sensitive data