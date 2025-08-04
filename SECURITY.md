# Security Configuration Guide

## 🔒 Removing Hardcoded Secrets

This guide explains how to securely configure the Video Splitter Pro application without hardcoded credentials.

## 1. AWS Lambda Security

### Environment Variables Setup
Set these environment variables in your AWS Lambda function:

```bash
JWT_SECRET=your-randomly-generated-secret-key-256-bits
JWT_REFRESH_SECRET=your-randomly-generated-refresh-key-256-bits
AWS_REGION=us-east-1
MONGO_URL=mongodb://your-mongodb-host:27017
FRONTEND_URL=https://your-domain.com
```

### Generate Secure JWT Secrets
```python
import secrets
import base64

# Generate 256-bit secrets
jwt_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
refresh_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

print(f"JWT_SECRET={jwt_secret}")
print(f"JWT_REFRESH_SECRET={refresh_secret}")
```

### AWS IAM Role Configuration
Instead of hardcoded AWS credentials, configure IAM roles:

1. **Lambda Execution Role** should have policies for:
   - `AmazonS3FullAccess` (or custom S3 policy)
   - `AmazonSESFullAccess` (or custom SES policy)
   - `CloudWatchLogsFullAccess`

2. **Lambda Function Configuration:**
```bash
# Set environment variables via AWS CLI
aws lambda update-function-configuration \
  --function-name videosplitter-api \
  --environment Variables='{
    "JWT_SECRET":"your-generated-secret",
    "JWT_REFRESH_SECRET":"your-generated-refresh-secret",
    "AWS_REGION":"us-east-1",
    "MONGO_URL":"mongodb://your-host:27017",
    "FRONTEND_URL":"https://your-domain.com"
  }'
```

## 2. Frontend Configuration

### Environment Variables (.env file)
```bash
# Frontend environment variables
VITE_REACT_APP_API_GATEWAY_URL=https://your-api-gateway.execute-api.us-east-1.amazonaws.com/prod
```

## 3. AWS SES Configuration

### Domain Verification
1. Go to AWS SES Console
2. Add and verify your domain: `tads-video-splitter.com`
3. Configure DNS records for domain verification
4. Enable email sending for the domain

### SES IAM Policy (for Lambda)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

## 4. MongoDB Security

### Connection Security
- Use MongoDB Atlas with IP whitelisting
- Use connection strings with authentication
- Enable SSL/TLS connections

Example secure connection string:
```
mongodb+srv://username:password@cluster.mongodb.net/videosplitter?retryWrites=true&w=majority
```

## 5. Production Deployment Checklist

### ✅ Security Checklist
- [ ] Remove all hardcoded credentials from code
- [ ] Use environment variables for all secrets
- [ ] Configure AWS IAM roles instead of access keys
- [ ] Enable CloudTrail for AWS API logging
- [ ] Use strong, randomly generated JWT secrets
- [ ] Enable HTTPS only for all endpoints
- [ ] Configure CORS properly
- [ ] Validate all user inputs
- [ ] Use MongoDB authentication
- [ ] Enable AWS CloudWatch monitoring

### ✅ Code Repository Security
- [ ] Add `.env` to `.gitignore`
- [ ] Remove any hardcoded secrets from git history
- [ ] Use GitHub/GitLab secrets for CI/CD
- [ ] Regular security audits of dependencies

## 6. Emergency Response

### If Credentials Are Exposed
1. **Immediately rotate all secrets:**
   - Generate new JWT secrets
   - Update Lambda environment variables
   - Invalidate all existing user sessions

2. **AWS Account Security:**
   - Deactivate exposed AWS access keys
   - Create new IAM roles with minimal permissions
   - Review CloudTrail logs for unauthorized access

3. **Database Security:**
   - Change MongoDB connection credentials
   - Review database access logs
   - Consider rotating database certificates

## 7. Monitoring and Alerts

### Set up CloudWatch Alarms for:
- Unusual API Gateway traffic patterns
- Failed authentication attempts
- Lambda function errors
- S3 access patterns

### Log Monitoring
- Monitor authentication failures
- Track user registration patterns
- Monitor JWT token usage
- Alert on suspicious database queries

---

## 🔐 Best Practices Summary

1. **Never commit secrets to version control**
2. **Use IAM roles instead of access keys when possible**
3. **Rotate secrets regularly**
4. **Monitor access patterns**
5. **Use least privilege principle**
6. **Enable multi-factor authentication where possible**
7. **Regular security audits and penetration testing**

For questions or security concerns, please follow responsible disclosure practices.