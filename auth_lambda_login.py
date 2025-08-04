#!/usr/bin/env python3
"""
User Login Lambda Function
Handles user login and JWT token generation
"""
import json
import bcrypt
import jwt
import os
import uuid
from datetime import datetime, timedelta
from pymongo import MongoClient

# Environment variables
MONGODB_URI = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'videosplitter'
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_REFRESH_SECRET = os.environ.get('JWT_REFRESH_SECRET', 'your-super-secret-refresh-key-change-in-production')

def lambda_handler(event, context):
    """Handle user login requests"""
    try:
        print(f"Login request received: {event}")
        
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        
        print(f"Login attempt for email: {email}")
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Email and password are required'
                })
            }
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        users_collection = db.users
        
        # Find user by email
        user = users_collection.find_one({'email': email})
        if not user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Invalid email or password'
                })
            }
        
        # Check if account is locked
        if user.get('accountLocked') and user.get('lockedUntil'):
            if datetime.utcnow() < user['lockedUntil']:
                remaining_time = (user['lockedUntil'] - datetime.utcnow()).total_seconds() / 60
                return {
                    'statusCode': 423,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'success': False,
                        'message': f'Account is locked. Try again in {int(remaining_time)} minutes.'
                    })
                }
            else:
                # Unlock account if lock period has expired
                users_collection.update_one(
                    {'_id': user['_id']},
                    {
                        '$set': {
                            'accountLocked': False,
                            'lockedUntil': None,
                            'loginAttempts': 0
                        }
                    }
                )
                user['accountLocked'] = False
                user['loginAttempts'] = 0
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['passwordHash'].encode('utf-8')):
            # Increment login attempts
            login_attempts = user.get('loginAttempts', 0) + 1
            update_data = {
                'loginAttempts': login_attempts,
                'updatedAt': datetime.utcnow()
            }
            
            # Lock account if too many failed attempts
            if login_attempts >= 5:
                update_data.update({
                    'accountLocked': True,
                    'lockedUntil': datetime.utcnow() + timedelta(minutes=30)
                })
            
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
            
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Invalid email or password'
                })
            }
        
        # Check if email is verified
        if not user.get('isEmailVerified', False):
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Please verify your email address before logging in',
                    'requiresEmailVerification': True,
                    'userId': user['userId']
                })
            }
        
        # Reset login attempts on successful login
        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'loginAttempts': 0,
                    'lastLoginAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        # Generate JWT tokens
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        
        # Store refresh token in database (sessions collection)
        sessions_collection = db.sessions
        session_data = {
            'sessionId': str(uuid.uuid4()),
            'userId': user['userId'],
            'refreshToken': refresh_token,
            'createdAt': datetime.utcnow(),
            'expiresAt': datetime.utcnow() + timedelta(days=30),
            'isActive': True
        }
        sessions_collection.insert_one(session_data)
        
        # Prepare user data for response (exclude sensitive fields)
        user_response = {
            'userId': user['userId'],
            'email': user['email'],
            'firstName': user['firstName'],
            'lastName': user['lastName'],
            'role': user['role'],
            'profileImage': user.get('profileImage'),
            'isEmailVerified': user.get('isEmailVerified', False)
        }
        
        print(f"Login successful for user: {user['userId']}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Login successful',
                'user': user_response,
                'accessToken': access_token,
                'refreshToken': refresh_token,
                'expiresIn': 3600  # 1 hour
            })
        }
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error during login',
                'error': str(e)
            })
        }

def generate_access_token(user):
    """Generate JWT access token"""
    payload = {
        'userId': user['userId'],
        'email': user['email'],
        'role': user['role'],
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def generate_refresh_token(user):
    """Generate JWT refresh token"""
    payload = {
        'userId': user['userId'],
        'type': 'refresh',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm='HS256')

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
        'httpMethod': 'POST',
        'body': json.dumps({
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")