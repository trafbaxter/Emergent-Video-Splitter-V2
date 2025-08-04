#!/usr/bin/env python3
"""
JWT Token Authorizer Lambda Function
Validates JWT tokens for API Gateway
"""
import json
import jwt
import os
from datetime import datetime
from pymongo import MongoClient

# Environment variables
MONGODB_URI = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'videosplitter'
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')

def lambda_handler(event, context):
    """Handle JWT token authorization for API Gateway"""
    try:
        print(f"Authorization request received: {event}")
        
        # Extract token from authorization header
        auth_token = event.get('authorizationToken', '')
        method_arn = event.get('methodArn', '')
        
        if not auth_token:
            print("Error: No authorization token provided")
            return generate_policy("user", "Deny", method_arn, "Unauthorized: No token provided")
        
        # Remove Bearer prefix if present
        if auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]
        
        # Decode and validate JWT token
        try:
            decoded_token = jwt.decode(
                auth_token, 
                JWT_SECRET, 
                algorithms=['HS256']
            )
            print(f"Token decoded successfully: {decoded_token}")
        except jwt.ExpiredSignatureError:
            print("Error: Token has expired")
            return generate_policy("user", "Deny", method_arn, "Error: Token has expired")
        except jwt.InvalidTokenError as e:
            print(f"Error: Invalid token - {str(e)}")
            return generate_policy("user", "Deny", method_arn, "Error: Invalid JWT Token")
        
        # Extract user information from token
        user_id = decoded_token.get('userId')
        user_role = decoded_token.get('role', 'user')
        
        if not user_id:
            print("Error: No user ID in token")
            return generate_policy("user", "Deny", method_arn, "Error: Invalid token structure")
        
        # Verify user still exists and is active
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            users_collection = db.users
            
            user = users_collection.find_one({'userId': user_id})
            if not user:
                print(f"Error: User {user_id} not found")
                return generate_policy("user", "Deny", method_arn, "Error: User not found")
            
            if user.get('accountLocked', False):
                print(f"Error: User {user_id} account is locked")
                return generate_policy("user", "Deny", method_arn, "Error: Account is locked")
            
            if not user.get('isEmailVerified', False):
                print(f"Error: User {user_id} email not verified")
                return generate_policy("user", "Deny", method_arn, "Error: Email not verified")
                
        except Exception as db_error:
            print(f"Database error during user verification: {str(db_error)}")
            # Allow request to proceed if database is temporarily unavailable
            # In production, you might want to deny access instead
        
        # Generate allow policy with user context
        print(f'Authorized JWT Token for user: {user_id}')
        return generate_policy(
            user_id, 
            'Allow', 
            method_arn, 
            "Authorized: Valid JWT Token",
            {
                'userId': user_id,
                'email': decoded_token.get('email', ''),
                'role': user_role,
                'iat': str(decoded_token.get('iat', '')),
                'exp': str(decoded_token.get('exp', ''))
            }
        )
        
    except Exception as e:
        print(f"Lambda authorizer error: {str(e)}")
        return generate_policy("user", "Deny", event.get("methodArn", "*"), f"Lambda Error: {str(e)}")

def generate_policy(principal_id, effect, resource, message, context=None):
    """Generate IAM policy for API Gateway"""
    auth_response = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        'context': {
            'errorMessage': message
        }
    }
    
    # Add user context if provided
    if context:
        auth_response['context'].update(context)
    
    print(f"Generated policy: {auth_response}")
    return auth_response

if __name__ == "__main__":
    # Test locally
    test_event = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer test-jwt-token',
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/resource'
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")