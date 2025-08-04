import json
import os
import boto3
import logging
from typing import Any, Dict
import tempfile
import subprocess
from botocore.exceptions import ClientError
import jwt
import bcrypt
import uuid
import re
from pymongo import MongoClient
from datetime import datetime

# Initialize
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BUCKET_NAME = 'videosplitter-uploads'
JWT_SECRET = os.environ.get('JWT_SECRET', 'tads-video-splitter-jwt-secret-2025-change-in-production')
JWT_REFRESH_SECRET = os.environ.get('JWT_REFRESH_SECRET', 'tads-video-splitter-refresh-secret-2025-change-in-production')
AWS_ACCESS_KEY = 'REDACTED_AWS_KEY'
AWS_SECRET_KEY = 'kSLXhxXDBZjgxZF9nHZHG8cZKrHM6KrNKv4gCXBE'
FRONTEND_URL = 'https://develop.tads-video-splitter.com'

# Initialize S3 client
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'

# Authentication Functions
def validate_jwt_from_context(event):
    """Extract and validate user information from API Gateway context or Authorization header"""
    try:
        # First try to get from API Gateway context (if using authorizer)
        request_context = event.get('requestContext', {})
        authorizer_context = request_context.get('authorizer', {})
        
        user_id = authorizer_context.get('userId')
        if user_id:
            return {
                'userId': user_id,
                'email': authorizer_context.get('email'),
                'role': authorizer_context.get('role', 'user')
            }
        
        # If not from context, try to extract from Authorization header
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Decode JWT token
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        
        return {
            'userId': decoded_token.get('userId'),
            'email': decoded_token.get('email'),
            'role': decoded_token.get('role', 'user')
        }
        
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error validating JWT from context: {str(e)}")
        return None

def get_mongo_client():
    """Get MongoDB client connection"""
    try:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        return MongoClient(mongo_url)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        return None

def generate_access_token(user_data):
    """Generate JWT access token"""
    try:
        from datetime import timedelta
        payload = {
            'userId': user_data['userId'],
            'email': user_data['email'],
            'role': user_data.get('role', 'user'),
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    except Exception as e:
        logger.error(f"Error generating access token: {str(e)}")
        return None

def generate_refresh_token(user_data):
    """Generate JWT refresh token"""
    try:
        from datetime import timedelta
        payload = {
            'userId': user_data['userId'],
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm='HS256')
    except Exception as e:
        logger.error(f"Error generating refresh token: {str(e)}")
        return None

def validate_registration_data(email, password, first_name, last_name):
    """Validate registration input data"""
    errors = []
    
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        errors.append('Valid email address is required')
    
    # Password validation (strong password policy)
    if not password:
        errors.append('Password is required')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    elif not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    elif not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    elif not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    # Name validation
    if not first_name or len(first_name.strip()) < 2:
        errors.append('First name must be at least 2 characters long')
    
    if not last_name or len(last_name.strip()) < 2:
        errors.append('Last name must be at least 2 characters long')
    
    return errors

def send_verification_email(email, first_name, verification_token):
    """Send email verification using AWS SES"""
    try:
        ses_client = boto3.client(
            'ses',
            region_name='us-east-1',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        
        verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = "Verify Your Tad's Video Splitter Account"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Tad's Video Splitter!</h1>
                </div>
                <div class="content">
                    <h2>Hello {first_name},</h2>
                    <p>Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    <p>Or copy this link: {verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        response = ses_client.send_email(
            Source="Tad's Video Splitter <noreply@tads-video-splitter.com>",
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
            }
        )
        
        logger.info(f"Verification email sent successfully: {response['MessageId']}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return False

def add_to_user_upload_history(user_id, upload_data):
    """Add upload record to user's history"""
    try:
        client = get_mongo_client()
        if not client:
            return
            
        db = client['videosplitter']
        users_collection = db.users
        
        upload_record = {
            'uploadId': upload_data.get('uploadId'),
            'fileName': upload_data.get('fileName'),
            'fileSize': upload_data.get('fileSize', 0),
            'uploadedAt': datetime.utcnow(),
            'status': 'uploaded',
            'processingStatus': 'pending'
        }
        
        users_collection.update_one(
            {'userId': user_id},
            {'$push': {'uploadHistory': upload_record}}
        )
        
        logger.info(f"Added upload record to user {user_id} history")
        
    except Exception as e:
        logger.error(f"Error adding to user upload history: {str(e)}")

def get_user_files_path(user_id):
    """Get S3 path prefix for user-specific files"""
    return f"user-files/{user_id}/"

def handle_user_registration(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user registration"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        
        # Validate input data
        validation_errors = validate_registration_data(email, password, first_name, last_name)
        if validation_errors:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Validation failed',
                    'details': validation_errors
                })
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User with this email already exists'})
            }
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Generate verification token
        verification_token = str(uuid.uuid4())
        
        # Create user document
        user_data = {
            'userId': str(uuid.uuid4()),
            'email': email,
            'passwordHash': password_hash,
            'firstName': first_name,
            'lastName': last_name,
            'role': 'user',
            'isEmailVerified': False,
            'emailVerificationToken': verification_token,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'uploadHistory': []
        }
        
        # Insert user into database
        users_collection.insert_one(user_data)
        
        # Send verification email
        email_sent = send_verification_email(email, first_name, verification_token)
        
        logger.info(f"User registered successfully: {email}")
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'User registered successfully',
                'userId': user_data['userId'],
                'emailVerificationSent': email_sent
            })
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Registration failed'})
        }

def handle_user_login(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user login"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Find user
        user = users_collection.find_one({'email': email})
        if not user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid email or password'})
            }
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['passwordHash']):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid email or password'})
            }
        
        # Check if email is verified
        if not user.get('isEmailVerified', False):
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Email not verified',
                    'message': 'Please verify your email before logging in'
                })
            }
        
        # Generate tokens
        user_data = {
            'userId': user['userId'],
            'email': user['email'],
            'role': user.get('role', 'user')
        }
        
        access_token = generate_access_token(user_data)
        refresh_token = generate_refresh_token(user_data)
        
        if not access_token or not refresh_token:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Token generation failed'})
            }
        
        # Update last login
        users_collection.update_one(
            {'userId': user['userId']},
            {'$set': {'lastLoginAt': datetime.utcnow()}}
        )
        
        logger.info(f"User logged in successfully: {email}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Login successful',
                'user': {
                    'userId': user['userId'],
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName'],
                    'role': user.get('role', 'user')
                },
                'accessToken': access_token,
                'refreshToken': refresh_token
            })
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Login failed'})
        }

def handle_email_verification(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle email verification"""
    try:
        query_params = event.get('queryStringParameters') or {}
        token = query_params.get('token')
        
        if not token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Verification token is required'})
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Find user with verification token
        user = users_collection.find_one({'emailVerificationToken': token})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid or expired verification token'})
            }
        
        # Update user as verified
        users_collection.update_one(
            {'userId': user['userId']},
            {
                '$set': {
                    'isEmailVerified': True,
                    'emailVerifiedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                },
                '$unset': {'emailVerificationToken': ''}
            }
        )
        
        logger.info(f"Email verified successfully: {user['email']}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Email verified successfully',
                'email': user['email']
            })
        }
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Email verification failed'})
        }

def handle_token_refresh(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle token refresh"""
    try:
        body = json.loads(event.get('body', '{}'))
        refresh_token = body.get('refreshToken')
        
        if not refresh_token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Refresh token is required'})
            }
        
        # Validate refresh token
        try:
            decoded_token = jwt.decode(refresh_token, JWT_REFRESH_SECRET, algorithms=['HS256'])
            user_id = decoded_token.get('userId')
            token_type = decoded_token.get('type')
            
            if token_type != 'refresh':
                raise jwt.InvalidTokenError("Invalid token type")
                
        except jwt.ExpiredSignatureError:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Refresh token has expired'})
            }
        except jwt.InvalidTokenError:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid refresh token'})
            }
        
        # Get user from database
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        user = users_collection.find_one({'userId': user_id})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Generate new access token
        user_data = {
            'userId': user['userId'],
            'email': user['email'],
            'role': user.get('role', 'user')
        }
        
        new_access_token = generate_access_token(user_data)
        if not new_access_token:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Token generation failed'})
            }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'accessToken': new_access_token,
                'message': 'Token refreshed successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Token refresh failed'})
        }

def handle_user_profile(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user profile requests"""
    try:
        # Validate JWT token
        user_info = validate_jwt_from_context(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        method = event.get('httpMethod', 'GET')
        
        if method == 'GET':
            # Get user profile
            client = get_mongo_client()
            if not client:
                return {
                    'statusCode': 500,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Database connection failed'})
                }
            
            db = client['videosplitter']
            users_collection = db.users
            
            user = users_collection.find_one({'userId': user_info['userId']})
            if not user:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'User not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'user': {
                        'userId': user['userId'],
                        'email': user['email'],
                        'firstName': user['firstName'],
                        'lastName': user['lastName'],
                        'role': user.get('role', 'user'),
                        'createdAt': user['createdAt'].isoformat() if user.get('createdAt') else None,
                        'isEmailVerified': user.get('isEmailVerified', False)
                    }
                })
            }
        
        elif method == 'PUT':
            # Update user profile
            body = json.loads(event.get('body', '{}'))
            first_name = body.get('firstName', '').strip()
            last_name = body.get('lastName', '').strip()
            
            if not first_name or not last_name:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'First name and last name are required'})
                }
            
            client = get_mongo_client()
            if not client:
                return {
                    'statusCode': 500,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Database connection failed'})
                }
            
            db = client['videosplitter']
            users_collection = db.users
            
            # Update user profile
            result = users_collection.update_one(
                {'userId': user_info['userId']},
                {
                    '$set': {
                        'firstName': first_name,
                        'lastName': last_name,
                        'updatedAt': datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'User not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'message': 'Profile updated successfully',
                    'user': {
                        'firstName': first_name,
                        'lastName': last_name
                    }
                })
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
    except Exception as e:
        logger.error(f"User profile error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Profile operation failed'})
        }

def handle_user_history(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user upload history requests"""
    try:
        # Validate JWT token
        user_info = validate_jwt_from_context(event)
        if not user_info:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Get user with upload history
        user = users_collection.find_one({'userId': user_info['userId']})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        upload_history = user.get('uploadHistory', [])
        
        # Format upload history for response
        formatted_history = []
        for upload in upload_history:
            formatted_upload = {
                'uploadId': upload.get('uploadId'),
                'fileName': upload.get('fileName'),
                'fileSize': upload.get('fileSize', 0),
                'uploadedAt': upload.get('uploadedAt').isoformat() if upload.get('uploadedAt') else None,
                'status': upload.get('status', 'unknown'),
                'processingStatus': upload.get('processingStatus', 'unknown')
            }
            formatted_history.append(formatted_upload)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'uploadHistory': formatted_history,
                'totalUploads': len(formatted_history)
            })
        }
        
    except Exception as e:
        logger.error(f"User history error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to retrieve upload history'})
        }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for Video Splitter Pro API
    Now includes user authentication endpoints
    """
    
    logger.info(f"📥 Request received: {event}")
    
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    # Extract request information
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    logger.info(f"🔍 Processing {method} {path}")
    
    try:
        # Authentication endpoints (no auth required)
        if path == '/api/auth/register':
            return handle_user_registration(event, context)
        elif path == '/api/auth/login':
            return handle_user_login(event, context)
        elif path == '/api/auth/verify-email':
            return handle_email_verification(event, context)
        elif path == '/api/auth/refresh':
            return handle_token_refresh(event, context)
        
        # Protected endpoints (require authentication)
        elif path.startswith('/api/video-info'):
            return handle_video_info(event, context)
        elif path.startswith('/api/upload'):
            return handle_upload_video(event, context)
        elif path.startswith('/api/stream'):
            return handle_video_stream(event, context)
        elif path.startswith('/api/job'):
            return handle_job_status(event, context)
        elif path.startswith('/api/split'):
            return handle_split_video(event, context)
        elif path.startswith('/api/download'):
            return handle_download(event, context)
        elif path == '/api/user/profile':
            return handle_user_profile(event, context)
        elif path == '/api/user/history':
            return handle_user_history(event, context)
        
        # Default response for unmatched paths
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Endpoint not found',
                'path': path,
                'method': method,
                'availableEndpoints': [
                    '/api/auth/register',
                    '/api/auth/login', 
                    '/api/auth/verify-email',
                    '/api/video-info',
                    '/api/upload',
                    '/api/stream',
                    '/api/split',
                    '/api/download'
                ]
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

# Authentication Handler Functions
def handle_user_registration(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user registration"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        
        # Validate input data
        validation_errors = validate_registration_data(email, password, first_name, last_name)
        if validation_errors:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': validation_errors
                })
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'User with this email already exists'})
            }
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate verification token
        verification_token = str(uuid.uuid4())
        
        # Create user document
        user_data = {
            'userId': str(uuid.uuid4()),
            'email': email,
            'passwordHash': password_hash,
            'firstName': first_name,
            'lastName': last_name,
            'role': 'user',
            'isEmailVerified': False,
            'emailVerificationToken': verification_token,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
            'uploadHistory': []
        }
        
        # Insert user into database
        users_collection.insert_one(user_data)
        
        # Send verification email
        email_sent = send_verification_email(email, first_name, verification_token)
        
        logger.info(f"User registered successfully: {email}")
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'User registered successfully. Please check your email for verification.',
                'userId': user_data['userId'],
                'emailSent': email_sent
            })
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'success': False, 'message': 'Registration failed'})
        }

def handle_user_login(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user login"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Email and password are required'})
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Find user
        user = users_collection.find_one({'email': email})
        if not user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Invalid email or password'})
            }
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['passwordHash'].encode('utf-8')):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Invalid email or password'})
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
        
        # Generate tokens
        user_token_data = {
            'userId': user['userId'],
            'email': user['email'],
            'role': user.get('role', 'user')
        }
        
        access_token = generate_access_token(user_token_data)
        refresh_token = generate_refresh_token(user_token_data)
        
        if not access_token or not refresh_token:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Token generation failed'})
            }
        
        # Update last login
        users_collection.update_one(
            {'userId': user['userId']},
            {'$set': {'lastLoginAt': datetime.utcnow(), 'updatedAt': datetime.utcnow()}}
        )
        
        logger.info(f"User logged in successfully: {email}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'userId': user['userId'],
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName'],
                    'role': user.get('role', 'user'),
                    'isEmailVerified': user.get('isEmailVerified', False)
                },
                'accessToken': access_token,
                'refreshToken': refresh_token,
                'expiresIn': 3600
            })
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'success': False, 'message': 'Login failed'})
        }

def handle_email_verification(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle email verification"""
    try:
        query_params = event.get('queryStringParameters') or {}
        token = query_params.get('token')
        
        if not token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Verification token is required'})
            }
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        # Find user with verification token
        user = users_collection.find_one({
            'emailVerificationToken': token,
            'isEmailVerified': False
        })
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Invalid or expired verification token'})
            }
        
        # Update user as verified
        result = users_collection.update_one(
            {'userId': user['userId']},
            {
                '$set': {
                    'isEmailVerified': True,
                    'emailVerifiedAt': datetime.utcnow(),
                    'updatedAt': datetime.utcnow()
                },
                '$unset': {'emailVerificationToken': ''}
            }
        )
        
        if result.modified_count == 0:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Failed to verify email'})
            }
        
        logger.info(f"Email verified successfully: {user['email']}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Email verified successfully! You can now log in.',
                'user': {
                    'userId': user['userId'],
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName']
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'success': False, 'message': 'Email verification failed'})
        }

def handle_token_refresh(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle token refresh"""
    try:
        body = json.loads(event.get('body', '{}'))
        refresh_token = body.get('refreshToken')
        
        if not refresh_token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Refresh token is required'})
            }
        
        # Decode refresh token
        try:
            decoded_token = jwt.decode(refresh_token, JWT_REFRESH_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Refresh token has expired'})
            }
        except jwt.InvalidTokenError:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Invalid refresh token'})
            }
        
        user_id = decoded_token.get('userId')
        if not user_id:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Invalid refresh token'})
            }
        
        # Get user from database
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        user = users_collection.find_one({'userId': user_id})
        if not user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'User not found'})
            }
        
        # Generate new access token
        user_token_data = {
            'userId': user['userId'],
            'email': user['email'],
            'role': user.get('role', 'user')
        }
        
        new_access_token = generate_access_token(user_token_data)
        
        if not new_access_token:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'success': False, 'message': 'Token generation failed'})
            }
        
        logger.info(f"Token refreshed successfully for user: {user_id}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'accessToken': new_access_token,
                'expiresIn': 3600
            })
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'success': False, 'message': 'Token refresh failed'})
        }

def handle_user_profile(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user profile GET/PUT requests"""
    user_context = validate_jwt_from_context(event)
    if not user_context:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Authentication required'})
        }
    
    method = event.get('httpMethod', 'GET')
    
    try:
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        if method == 'GET':
            user = users_collection.find_one({'userId': user_context['userId']})
            if not user:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'User not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'user': {
                        'userId': user['userId'],
                        'email': user['email'],
                        'firstName': user['firstName'],
                        'lastName': user['lastName'],
                        'role': user.get('role', 'user'),
                        'createdAt': user['createdAt'].isoformat() if user.get('createdAt') else None,
                        'lastLoginAt': user.get('lastLoginAt').isoformat() if user.get('lastLoginAt') else None
                    }
                })
            }
        
        elif method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            update_data = {}
            
            if 'firstName' in body:
                update_data['firstName'] = body['firstName'].strip()
            if 'lastName' in body:
                update_data['lastName'] = body['lastName'].strip()
            
            if not update_data:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'No valid fields to update'})
                }
            
            update_data['updatedAt'] = datetime.utcnow()
            
            result = users_collection.update_one(
                {'userId': user_context['userId']},
                {'$set': update_data}
            )
            
            if result.modified_count == 0:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'User not found or no changes made'})
                }
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Profile updated successfully'})
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Profile handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Profile operation failed'})
        }

def handle_user_history(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user upload history"""
    user_context = validate_jwt_from_context(event)
    if not user_context:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Authentication required'})
        }
    
    try:
        client = get_mongo_client()
        if not client:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Database connection failed'})
            }
        
        db = client['videosplitter']
        users_collection = db.users
        
        user = users_collection.find_one({'userId': user_context['userId']})
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        upload_history = user.get('uploadHistory', [])
        
        # Convert datetime objects to ISO strings
        for record in upload_history:
            if 'uploadedAt' in record and record['uploadedAt']:
                record['uploadedAt'] = record['uploadedAt'].isoformat()
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'uploadHistory': upload_history,
                'totalUploads': len(upload_history)
            })
        }
        
    except Exception as e:
        logger.error(f"User history error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to retrieve upload history'})
        }

def get_cors_headers() -> Dict[str, str]:
    """Return CORS headers for API responses"""
    return {
        'Access-Control-Allow-Origin': '*',  # Allow all origins for now - more permissive
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,Referer,User-Agent,Cache-Control,X-Requested-With',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS,HEAD',
        'Access-Control-Allow-Credentials': 'false',
        'Access-Control-Expose-Headers': 'Content-Length,Content-Type,Date,Server,x-amzn-RequestId',
        'Access-Control-Max-Age': '3600'
    }

def handle_upload_video(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle video file upload to S3"""
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        filename = body.get('filename', 'video.mp4')
        file_type = body.get('fileType', 'video/mp4')
        file_size = body.get('fileSize', 0)
        
        upload_id = f"job-{context.aws_request_id}"
        s3_key = f"videos/{upload_id}/{filename}"
        
        # Generate presigned URL for PUT operation with proper CORS headers
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME, 
                'Key': s3_key,
                'ContentType': file_type
            },
            ExpiresIn=3600
        )
        
        # Also generate presigned POST for better browser compatibility
        presigned_post = s3.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Fields={
                'Content-Type': file_type
            },
            Conditions=[
                {'Content-Type': file_type},
                ['content-length-range', 1, file_size + 1000000]  # Allow some buffer
            ],
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'job_id': upload_id,
                'upload_url': presigned_url,
                'upload_post': presigned_post,
                'bucket': BUCKET_NAME,
                'key': s3_key,
                'content_type': file_type
            })
        }
        
    except Exception as e:
        logger.error(f"Upload handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def handle_split_video(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle video splitting request using FFmpeg Lambda function"""
    try:
        # Debug the event structure to understand the issue
        logger.info(f"🔍 Split video event debug: {json.dumps(event, indent=2)}")
        
        # Extract job_id from path parameters with better error handling
        path_params = event.get('pathParameters') or {}
        job_id = path_params.get('job_id')
        
        # If pathParameters is None or job_id is missing, try to extract from path
        if not job_id:
            path = event.get('path', '')
            logger.info(f"🔍 PathParameters missing, trying to extract from path: {path}")
            
            # Extract job_id from path like: /api/split-video/{job_id}
            if '/api/split-video/' in path:
                path_parts = path.split('/api/split-video/')
                if len(path_parts) > 1:
                    job_id = path_parts[1].strip('/')
                    logger.info(f"✅ Extracted job_id from path: {job_id}")
        
        if not job_id:
            logger.error(f"❌ Could not extract job_id. Event pathParameters: {path_params}, path: {event.get('path', 'N/A')}")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Missing job_id in path parameters',
                    'debug_info': {
                        'pathParameters': path_params,
                        'path': event.get('path', 'N/A'),
                        'available_keys': list(event.keys())
                    }
                })
            }
        
        # Get request body
        body = json.loads(event.get('body', '{}'))
        split_method = body.get('method', 'time_based')
        
        logger.info(f"Split request for job {job_id}: method={split_method}, config={body}")
        
        # Validate split configuration
        if split_method == 'time_based':
            time_points = body.get('time_points', [])
            if not time_points or len(time_points) < 2:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Time-based splitting requires at least 2 time points'})
                }
        elif split_method == 'intervals':
            interval_duration = body.get('interval_duration', 0)
            if interval_duration <= 0:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Invalid interval duration specified'})
                }
        
        # Find the uploaded video file in S3
        # Try different possible S3 key patterns
        possible_keys = [
            f"uploads/{job_id}",
            f"videos/{job_id}",
            f"videos/{job_id}/"
        ]
        
        video_key = None
        for key_pattern in possible_keys:
            try:
                if key_pattern.endswith('/'):
                    # List objects with prefix to find the actual file
                    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=key_pattern, MaxKeys=1)
                    if 'Contents' in response and response['Contents']:
                        video_key = response['Contents'][0]['Key']
                        logger.info(f"✅ Found video at: {video_key}")
                        break
                else:
                    # Direct key check
                    s3.head_object(Bucket=BUCKET_NAME, Key=key_pattern)
                    video_key = key_pattern
                    logger.info(f"✅ Found video at: {video_key}")
                    break
            except Exception:
                logger.info(f"❌ Video not found at: {key_pattern}")
                continue
        
        if not video_key:
            logger.error(f"Video not found for job {job_id} in any expected location")
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Video file not found. Please upload video first.'})
            }
        
        logger.info(f"🎬 Using video file: {video_key}")
        
        # Prepare payload for FFmpeg Lambda
        payload = {
            'operation': 'split_video',
            'source_bucket': BUCKET_NAME,
            'source_key': video_key,
            'job_id': job_id,
            'split_config': {
                'method': split_method,
                'time_points': body.get('time_points', []),
                'interval_duration': body.get('interval_duration', 300),
                'preserve_quality': body.get('preserve_quality', True),
                'output_format': body.get('output_format', 'mp4'),
                'force_keyframes': body.get('force_keyframes', False),
                'keyframe_interval': body.get('keyframe_interval', 2.0),
                'subtitle_sync_offset': body.get('subtitle_sync_offset', 0.0)
            }
        }
        
        logger.info(f"🚀 Invoking FFmpeg Lambda for video splitting: {job_id}")
        
        # Invoke FFmpeg Lambda function asynchronously for long operations
        response = lambda_client.invoke(
            FunctionName=FFMPEG_LAMBDA_FUNCTION,
            InvocationType='Event',  # Asynchronous call for splitting
            Payload=json.dumps(payload)
        )
        
        logger.info(f"✅ FFmpeg Lambda invoked successfully for splitting job {job_id}")
        
        return {
            'statusCode': 202,  # Accepted for processing
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Video splitting started using FFmpeg processing',
                'job_id': job_id,
                'status': 'processing',
                'method': split_method,
                'video_file': video_key,
                'note': 'Processing is running asynchronously. Check status for updates.'
            })
        }
        
    except KeyError as e:
        logger.error(f"Missing required parameter: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Missing required parameter: {str(e)}'})
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        logger.error(f"Split handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_job_status(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle job status request"""
    try:
        # Extract job_id with robust error handling (same as split function)
        path_params = event.get('pathParameters') or {}
        job_id = path_params.get('job_id')
        
        # If pathParameters is None, try to extract from path
        if not job_id:
            path = event.get('path', '')
            logger.info(f"🔍 PathParameters missing in status request, extracting from path: {path}")
            
            # Extract job_id from path like: /api/job-status/{job_id}
            if '/api/job-status/' in path:
                path_parts = path.split('/api/job-status/')
                if len(path_parts) > 1:
                    job_id = path_parts[1].strip('/')
                    logger.info(f"✅ Extracted job_id from path: {job_id}")
        
        if not job_id:
            logger.error(f"❌ Could not extract job_id for status check")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing job_id in path'})
            }
        
        logger.info(f"📊 Checking status for job: {job_id}")
        
        # Check if there are any output files in S3 for this job
        try:
            output_prefix = f"outputs/{job_id}/"
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=output_prefix)
            
            output_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith(('.mp4', '.mkv', '.avi', '.mov')):  # Video files only
                        filename = obj['Key'].split('/')[-1]  # Get just the filename
                        output_files.append({
                            'file': filename,
                            'size': obj['Size'],
                            'url': f"https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/{obj['Key']}"
                        })
                        
            # Determine status based on output files
            if len(output_files) >= 2:
                status = 'completed'
                progress = 100
                logger.info(f"✅ Job {job_id} completed with {len(output_files)} output files")
            elif len(output_files) == 1:
                status = 'processing'
                progress = 50  # Partial completion
                logger.info(f"🔄 Job {job_id} in progress with {len(output_files)} output files")
            else:
                status = 'processing'
                progress = 0
                logger.info(f"🔄 Job {job_id} starting - no output files yet")
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'id': job_id,
                    'status': status,
                    'progress': progress,
                    'splits': output_files,
                    'output_count': len(output_files)
                })
            }
                
        except Exception as s3_error:
            logger.error(f"S3 error checking output files: {str(s3_error)}")
            # Return a default processing status if S3 check fails
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'id': job_id,
                    'status': 'processing',
                    'progress': 25,
                    'splits': [],
                    'note': 'Status check in progress'
                })
            }
        
    except Exception as e:
        logger.error(f"Status handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Status check failed: {str(e)}'})
        }

def handle_download(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file download request"""
    try:
        # Extract path parameters with robust error handling (same pattern as other functions)
        path_params = event.get('pathParameters') or {}
        job_id = path_params.get('job_id')
        filename = path_params.get('filename')
        
        # If pathParameters is None, try to extract from path
        if not job_id or not filename:
            path = event.get('path', '')
            logger.info(f"🔍 PathParameters missing in download request, extracting from path: {path}")
            
            # Extract from path like: /api/download/{job_id}/{filename}
            if '/api/download/' in path:
                path_parts = path.split('/api/download/')
                if len(path_parts) > 1:
                    remaining_path = path_parts[1].strip('/')
                    path_segments = remaining_path.split('/')
                    if len(path_segments) >= 2:
                        job_id = path_segments[0]
                        filename = path_segments[1]
                        logger.info(f"✅ Extracted from path - job_id: {job_id}, filename: {filename}")
        
        if not job_id or not filename:
            logger.error(f"❌ Could not extract job_id or filename from download request")
            logger.error(f"   pathParameters: {path_params}")
            logger.error(f"   path: {event.get('path', 'N/A')}")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Missing job_id or filename in path parameters',
                    'debug_info': {
                        'pathParameters': path_params,
                        'path': event.get('path', 'N/A'),
                        'required_format': '/api/download/{job_id}/{filename}'
                    }
                })
            }
        
        logger.info(f"📥 Download request for job: {job_id}, file: {filename}")
        
        # Check if the file exists in S3 before generating presigned URL
        s3_key = f'outputs/{job_id}/{filename}'
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            logger.info(f"✅ File exists in S3: {s3_key}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == 'NoSuchKey':
                logger.error(f"❌ File not found in S3: {s3_key}")
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'error': f'File not found: {filename}',
                        'job_id': job_id,
                        'expected_location': s3_key
                    })
                }
            else:
                logger.error(f"❌ S3 error checking file existence: {str(e)}")
                return {
                    'statusCode': 500,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f'Error accessing file: {str(e)}'})
                }
        except Exception as s3_error:
            logger.error(f"❌ S3 error checking file existence: {str(s3_error)}")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'Error accessing file: {str(s3_error)}'})
            }
        
        # Generate presigned URL for download
        logger.info(f"🔗 Generating presigned URL for download: {s3_key}")
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        logger.info(f"✅ Download URL generated successfully for {filename}")
        
        return {
            'statusCode': 302,
            'headers': {
                **get_cors_headers(),
                'Location': download_url
            },
            'body': ''
        }
        
    except KeyError as e:
        logger.error(f"❌ Missing required parameter in download request: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Missing required parameter: {str(e)}'})
        }
    except Exception as e:
        logger.error(f"❌ Download handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Download failed: {str(e)}'})
        }

def handle_video_stream(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle video streaming request"""
    try:
        # Extract job_id from path
        path = event.get('path', '')
        job_id = path.split('/')[-1]  # Get job_id from /api/video-stream/{job_id}
        
        # List objects to find the actual video file
        try:
            response = s3.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f'videos/{job_id}/'
            )
            
            if 'Contents' not in response or len(response['Contents']) == 0:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Video not found'})
                }
            
            # Get the first video file
            video_key = response['Contents'][0]['Key']
            
        except Exception as e:
            logger.error(f"Error finding video: {str(e)}")
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Video not found'})
            }
        
        # Generate presigned URL for video streaming
        stream_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': video_key},
            ExpiresIn=3600
        )
        
        # Return the stream URL as JSON instead of redirect
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'stream_url': stream_url})
        }
        
    except Exception as e:
        logger.error(f"Stream handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def handle_video_info(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle video info request"""
    try:
        # Extract job_id from path
        path = event.get('path', '')
        job_id = path.split('/')[-1]  # Get job_id from /api/video-info/{job_id}
        
        # List objects to find the actual video file
        try:
            response = s3.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f'videos/{job_id}/'
            )
            
            if 'Contents' not in response or len(response['Contents']) == 0:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Video not found'})
                }
            
            # Get the first video file
            video_key = response['Contents'][0]['Key']
            
        except Exception as e:
            logger.error(f"Error finding video: {str(e)}")
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Video not found'})
            }
        
        # Extract video metadata
        metadata = extract_video_metadata(video_key)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'job_id': job_id,
                'video_key': video_key,
                'metadata': metadata
            })
        }
        
    except Exception as e:
        logger.error(f"Video info handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def extract_video_metadata(s3_key: str) -> dict:
    """Extract video metadata using FFmpeg Lambda function"""
    try:
        logger.info(f"Extracting metadata for {s3_key} using FFmpeg Lambda")
        
        # Prepare payload for FFmpeg Lambda
        payload = {
            'operation': 'extract_metadata',
            'source_bucket': BUCKET_NAME,
            'source_key': s3_key,
            'job_id': s3_key.replace('/', '_').replace('.', '_')
        }
        
        # Invoke FFmpeg Lambda function
        response = lambda_client.invoke(
            FunctionName=FFMPEG_LAMBDA_FUNCTION,
            InvocationType='RequestResponse',  # Synchronous call
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        logger.info(f"FFmpeg Lambda response: {response_payload.get('statusCode')}")
        
        if response_payload.get('statusCode') != 200:
            logger.error(f"FFmpeg Lambda error: {response_payload}")
            # Fallback to file size estimation
            return extract_video_metadata_fallback(s3_key)
        
        # Parse the successful response
        body = json.loads(response_payload.get('body', '{}'))
        metadata = body.get('metadata', {})
        
        # Convert to our expected format
        return {
            'format': metadata.get('format', 'unknown'),
            'duration': metadata.get('duration', 0),
            'size': metadata.get('size', 0),
            'video_streams': [
                {
                    'index': 0,
                    'codec_name': metadata.get('video_info', {}).get('codec', 'unknown'),
                    'width': metadata.get('video_info', {}).get('width', 1920),
                    'height': metadata.get('video_info', {}).get('height', 1080),
                    'fps': metadata.get('video_info', {}).get('fps', 30)
                }
            ] if metadata.get('video_streams', 0) > 0 else [],
            'audio_streams': [
                {
                    'index': 1,
                    'codec_name': metadata.get('audio_info', {}).get('codec', 'aac'),
                    'sample_rate': metadata.get('audio_info', {}).get('sample_rate', 44100),
                    'channels': metadata.get('audio_info', {}).get('channels', 2)
                }
            ] if metadata.get('audio_streams', 0) > 0 else [],
            'subtitle_streams': [
                {
                    'index': i + 2,  # Usually after video and audio streams
                    'codec_name': 'unknown',  # FFmpeg Lambda doesn't provide codec details yet
                    'language': 'unknown'
                } for i in range(metadata.get('subtitle_streams', 0))
            ],
            'chapters': []
        }
        
    except Exception as e:
        logger.error(f"FFmpeg metadata extraction failed: {str(e)}")
        # Fallback to file size estimation
        return extract_video_metadata_fallback(s3_key)

def extract_video_metadata_fallback(s3_key: str) -> dict:
    """Fallback metadata extraction based on file size (original method)"""
    try:
        # Get file extension to determine format
        file_extension = s3_key.lower().split('.')[-1]
        format_map = {
            'mp4': 'mp4',
            'mkv': 'matroska,webm',
            'avi': 'avi',
            'mov': 'mov,mp4,m4a,3gp,3g2,mj2',
            'wmv': 'asf',
            'flv': 'flv',
            'webm': 'matroska,webm'
        }
        
        # Get file info from S3
        try:
            response = s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            file_size = response['ContentLength']
        except Exception:
            file_size = 0
        
        # Estimate duration based on file size (improved approximation)
        if file_size > 0:
            estimated_duration_minutes = file_size / (60 * 1024 * 1024)  # 60MB per minute
            estimated_duration = max(60, int(estimated_duration_minutes * 60))  # Convert to seconds
        else:
            estimated_duration = 300  # Default 5 minutes if no size info
        
        return {
            'format': format_map.get(file_extension, file_extension),
            'duration': estimated_duration,
            'size': file_size,
            'video_streams': [
                {
                    'index': 0,
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080,
                    'fps': 30
                }
            ],
            'audio_streams': [
                {
                    'index': 1,
                    'codec_name': 'aac',
                    'sample_rate': 44100,
                    'channels': 2
                }
            ],
            'subtitle_streams': [],  # Fallback doesn't detect subtitles
            'chapters': []
        }
        
    except Exception as e:
        logger.error(f"Fallback metadata extraction error: {str(e)}")
        return {
            'format': 'unknown',
            'duration': 300,
            'size': 0,
            'video_streams': [],
            'audio_streams': [],
            'subtitle_streams': [],
            'chapters': []
        }

# For FFmpeg processing in Lambda:
def process_video_with_ffmpeg(input_path: str, output_path: str, start_time: float, duration: float):
    """
    Process video with FFmpeg in Lambda environment
    Note: Requires FFmpeg Lambda layer
    """
    try:
        cmd = [
            '/opt/bin/ffmpeg',  # FFmpeg from Lambda layer
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # Copy streams for speed
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
            
        return True
        
    except Exception as e:
        logger.error(f"FFmpeg processing error: {str(e)}")
        raise e