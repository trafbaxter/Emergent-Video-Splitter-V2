#!/usr/bin/env python3
"""
Setup DynamoDB tables for Video Splitter Pro migration from MongoDB
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = 'us-east-1'
TABLE_PREFIX = 'VideoSplitter'

def create_users_table():
    """Create DynamoDB Users table to replace MongoDB users collection"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    table_name = f'{TABLE_PREFIX}-Users'
    
    try:
        print(f"🚀 Creating DynamoDB table: {table_name}")
        
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'VideoSplitterPro'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Production'
                }
            ]
        )
        
        print(f"⏳ Waiting for table to be created...")
        table.wait_until_exists()
        
        print(f"✅ Table created successfully!")
        print(f"   Table Name: {table_name}")
        print(f"   Table ARN: {table.table_arn}")
        print(f"   Billing Mode: Pay per request")
        print(f"   Global Secondary Index: EmailIndex (for email lookups)")
        
        return table_name
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✅ Table {table_name} already exists")
            return table_name
        else:
            print(f"❌ Error creating table: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def create_jobs_table():
    """Create DynamoDB Jobs table for video processing job tracking"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    table_name = f'{TABLE_PREFIX}-Jobs'
    
    try:
        print(f"🚀 Creating DynamoDB table: {table_name}")
        
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserJobsIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'job_id',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'VideoSplitterPro'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Production'
                }
            ]
        )
        
        print(f"⏳ Waiting for table to be created...")
        table.wait_until_exists()
        
        print(f"✅ Table created successfully!")
        print(f"   Table Name: {table_name}")
        print(f"   Global Secondary Indexes: UserJobsIndex, StatusIndex")
        
        return table_name
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✅ Table {table_name} already exists")
            return table_name
        else:
            print(f"❌ Error creating table: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None

def list_tables():
    """List all DynamoDB tables"""
    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
    
    try:
        response = dynamodb.list_tables()
        tables = response['TableNames']
        
        print(f"📋 DynamoDB Tables in {AWS_REGION}:")
        video_splitter_tables = [t for t in tables if 'VideoSplitter' in t]
        
        if video_splitter_tables:
            for table in video_splitter_tables:
                print(f"   ✅ {table}")
        else:
            print("   ❌ No VideoSplitter tables found")
            
        return video_splitter_tables
        
    except Exception as e:
        print(f"❌ Error listing tables: {str(e)}")
        return []

if __name__ == "__main__":
    print("🗄️  DynamoDB Setup for Video Splitter Pro")
    print("=" * 50)
    
    # Check existing tables
    print("🔍 Checking existing tables...")
    existing_tables = list_tables()
    
    print("\n🚀 Creating required tables...")
    
    # Create Users table
    users_table = create_users_table()
    
    # Create Jobs table  
    jobs_table = create_jobs_table()
    
    print("\n" + "=" * 50)
    
    if users_table and jobs_table:
        print("🎉 DynamoDB setup complete!")
        print(f"✅ Users table: {users_table}")
        print(f"✅ Jobs table: {jobs_table}")
        print("\n📋 Next steps:")
        print("   1. Update Lambda function to use DynamoDB")
        print("   2. Test authentication with DynamoDB")
        print("   3. Migrate job tracking to DynamoDB")
    else:
        print("❌ DynamoDB setup failed!")
        print("   Please check AWS permissions and try again")