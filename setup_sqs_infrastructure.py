#!/usr/bin/env python3
"""
Setup SQS Infrastructure for Video Splitter Pro
Creates SQS queue, dead letter queue, and configures Lambda trigger
"""

import boto3
import json
import time

# Configuration
SQS_QUEUE_NAME = 'video-processing-queue'
DLQ_NAME = 'video-processing-dlq'
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'
REGION = 'us-east-1'

def create_sqs_infrastructure():
    """Create SQS queues and configure Lambda trigger"""
    print("🚀 Setting up SQS Infrastructure for Video Splitter Pro")
    print("=" * 60)
    
    # Initialize clients
    sqs_client = boto3.client('sqs', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    try:
        # Step 1: Create Dead Letter Queue first
        print("📋 Step 1: Creating Dead Letter Queue...")
        dlq_response = sqs_client.create_queue(
            QueueName=DLQ_NAME,
            Attributes={
                'MessageRetentionPeriod': '1209600',  # 14 days
                'VisibilityTimeout': '30'
            }
        )
        dlq_url = dlq_response['QueueUrl']
        
        # Get DLQ ARN
        dlq_attributes = sqs_client.get_queue_attributes(
            QueueUrl=dlq_url,
            AttributeNames=['QueueArn']
        )
        dlq_arn = dlq_attributes['Attributes']['QueueArn']
        print(f"✅ Dead Letter Queue created: {dlq_arn}")
        
        # Step 2: Create main processing queue with DLQ
        print("\n📋 Step 2: Creating main processing queue...")
        queue_response = sqs_client.create_queue(
            QueueName=SQS_QUEUE_NAME,
            Attributes={
                'MessageRetentionPeriod': '1209600',  # 14 days
                'VisibilityTimeout': '960',     # 16 minutes (longer than Lambda timeout)
                'ReceiveMessageWaitTimeSeconds': '20', # Long polling
                'RedrivePolicy': json.dumps({
                    'deadLetterTargetArn': dlq_arn,
                    'maxReceiveCount': 3  # Retry 3 times before moving to DLQ
                })
            }
        )
        queue_url = queue_response['QueueUrl']
        
        # Get queue ARN
        queue_attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attributes['Attributes']['QueueArn']
        print(f"✅ Main queue created: {queue_arn}")
        
        # Step 3: Configure Lambda trigger
        print(f"\n📋 Step 3: Configuring Lambda trigger for {FFMPEG_LAMBDA_FUNCTION}...")
        
        # Add SQS as event source for Lambda
        try:
            lambda_client.create_event_source_mapping(
                EventSourceArn=queue_arn,
                FunctionName=FFMPEG_LAMBDA_FUNCTION,
                BatchSize=1,  # Process one video at a time
                MaximumBatchingWindowInSeconds=0  # Process immediately
            )
            print("✅ Lambda trigger configured successfully")
        except lambda_client.exceptions.ResourceConflictException:
            print("⚠️  Lambda trigger already exists - skipping")
        
        # Step 4: Save configuration
        print("\n📋 Step 4: Saving configuration...")
        config = {
            'sqs_queue_url': queue_url,
            'sqs_queue_arn': queue_arn,
            'dlq_url': dlq_url,
            'dlq_arn': dlq_arn,
            'region': REGION,
            'lambda_function': FFMPEG_LAMBDA_FUNCTION
        }
        
        with open('/app/sqs_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration saved to sqs_config.json")
        
        # Step 5: Display results
        print("\n" + "=" * 60)
        print("🎉 SQS Infrastructure Setup Complete!")
        print("=" * 60)
        print(f"Queue URL: {queue_url}")
        print(f"Queue ARN: {queue_arn}")
        print(f"DLQ URL: {dlq_url}")
        print(f"Lambda Function: {FFMPEG_LAMBDA_FUNCTION}")
        print("\nNext Steps:")
        print("1. Update main Lambda to send SQS messages")
        print("2. Update FFmpeg Lambda to handle SQS events")
        print("3. Test the complete flow")
        
        return config
        
    except Exception as e:
        print(f"❌ Error setting up SQS infrastructure: {e}")
        return None

if __name__ == "__main__":
    config = create_sqs_infrastructure()
    if config:
        print(f"\n📋 Configuration available at: /app/sqs_config.json")
    else:
        print("\n❌ Setup failed. Please check AWS credentials and permissions.")