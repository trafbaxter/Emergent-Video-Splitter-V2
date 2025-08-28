#!/usr/bin/env python3
"""
Check S3 bucket policy that might be blocking access
"""

import boto3
import json
from botocore.exceptions import ClientError

S3_BUCKET_NAME = 'videosplitter-storage-1751560247'

def check_bucket_policy():
    """Check S3 bucket policy"""
    s3_client = boto3.client('s3')
    
    try:
        print(f"🔍 Checking S3 bucket policy for: {S3_BUCKET_NAME}")
        
        policy = s3_client.get_bucket_policy(Bucket=S3_BUCKET_NAME)
        policy_doc = json.loads(policy['Policy'])
        
        print("✅ Bucket Policy Found:")
        print(json.dumps(policy_doc, indent=2))
        
        # Check if policy is blocking access
        for statement in policy_doc.get('Statement', []):
            effect = statement.get('Effect', '')
            principal = statement.get('Principal', '')
            action = statement.get('Action', [])
            resource = statement.get('Resource', [])
            
            print(f"\n📋 Statement:")
            print(f"   Effect: {effect}")
            print(f"   Principal: {principal}")
            print(f"   Action: {action}")
            print(f"   Resource: {resource}")
            
            if effect == 'Deny':
                print("   ⚠️  DENY statement found - this could be blocking access")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            print("✅ No bucket policy found (using default permissions)")
            return True
        else:
            print(f"❌ Error checking bucket policy: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_bucket_public_access():
    """Check public access block settings"""
    s3_client = boto3.client('s3')
    
    try:
        print(f"\n🔍 Checking Public Access Block settings...")
        
        response = s3_client.get_public_access_block(Bucket=S3_BUCKET_NAME)
        config = response['PublicAccessBlockConfiguration']
        
        print(f"✅ Public Access Block Configuration:")
        print(f"   BlockPublicAcls: {config.get('BlockPublicAcls', False)}")
        print(f"   IgnorePublicAcls: {config.get('IgnorePublicAcls', False)}")
        print(f"   BlockPublicPolicy: {config.get('BlockPublicPolicy', False)}")
        print(f"   RestrictPublicBuckets: {config.get('RestrictPublicBuckets', False)}")
        
        if any(config.values()):
            print("⚠️  Public access is blocked - this might affect presigned URL access")
        else:
            print("✅ Public access is allowed")
            
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            print("✅ No public access block configuration (default allow)")
            return True
        else:
            print(f"❌ Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return False

def check_object_permissions():
    """Check permissions on a specific object"""
    s3_client = boto3.client('s3')
    
    # Use one of the known video files
    test_key = "uploads/43ab1ed4-1c23-488f-b29e-fbab160a0079/Rise of the Teenage Mutant Ninja Turtles.S01E01.Mystic Mayhem.mkv"
    
    try:
        print(f"\n🔍 Checking object ACL for: {test_key}")
        
        acl = s3_client.get_object_acl(Bucket=S3_BUCKET_NAME, Key=test_key)
        
        print("✅ Object ACL:")
        for grant in acl.get('Grants', []):
            grantee = grant.get('Grantee', {})
            permission = grant.get('Permission', '')
            
            print(f"   {grantee.get('Type', '')}: {grantee.get('ID', grantee.get('URI', 'Unknown'))} - {permission}")
            
        return True
        
    except ClientError as e:
        print(f"❌ Error checking object ACL: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False

if __name__ == "__main__":
    print("🚀 S3 Permissions Diagnostic")
    print("=" * 50)
    
    check_bucket_policy()
    check_bucket_public_access() 
    check_object_permissions()
    
    print("\n🎯 Summary:")
    print("   If presigned URLs return 403, the issue is likely:")
    print("   1. Bucket policy denying access") 
    print("   2. Public access blocks preventing access")
    print("   3. Object ACLs not allowing read access")
    print("   4. IAM policy not allowing s3:GetObject")