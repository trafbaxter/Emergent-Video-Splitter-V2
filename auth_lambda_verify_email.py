#!/usr/bin/env python3
"""
Email Verification Lambda Function
Handles email verification token validation
"""
import json
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Environment variables
MONGODB_URI = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'videosplitter'

def lambda_handler(event, context):
    """Handle email verification requests"""
    try:
        print(f"Email verification request received: {event}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Get verification token from query parameters or body
        verification_token = None
        
        # Try query parameters first
        if event.get('queryStringParameters'):
            verification_token = event['queryStringParameters'].get('token')
        
        # Try request body if not in query parameters
        if not verification_token and event.get('body'):
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
            verification_token = body.get('token')
        
        print(f"Verification token: {verification_token}")
        
        if not verification_token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Verification token is required',
                    'code': 'MISSING_TOKEN'
                })
            }
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        users_collection = db.users
        
        # Find user by verification token
        user = users_collection.find_one({
            'emailVerificationToken': verification_token,
            'isEmailVerified': False
        })
        
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Invalid or expired verification token',
                    'code': 'INVALID_TOKEN'
                })
            }
        
        # Check if token has expired (24 hours)
        token_created = user.get('createdAt', datetime.utcnow())
        if datetime.utcnow() > token_created + timedelta(hours=24):
            return {
                'statusCode': 410,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Verification token has expired. Please request a new verification email.',
                    'code': 'TOKEN_EXPIRED',
                    'canResend': True
                })
            }
        
        # Update user as verified
        update_result = users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'isEmailVerified': True,
                    'emailVerifiedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                },
                '$unset': {
                    'emailVerificationToken': 1
                }
            }
        )
        
        if update_result.modified_count == 0:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Failed to verify email address'
                })
            }
        
        print(f"Email verification successful for user: {user['userId']}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Email address verified successfully! You can now log in.',
                'user': {
                    'userId': user['userId'],
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName']
                }
            })
        }
        
    except Exception as e:
        print(f"Email verification error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error during email verification',
                'error': str(e)
            })
        }

def get_cors_headers():
    """Get CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
        'Content-Type': 'application/json'
    }

if __name__ == "__main__":
    # Test locally
    test_event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'token': 'test-token-123'
        }
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")