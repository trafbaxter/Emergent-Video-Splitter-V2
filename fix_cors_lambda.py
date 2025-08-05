#!/usr/bin/env python3
"""
Fix CORS configuration in the AWS Lambda function for Video Splitter Pro
This script updates the Lambda function to allow requests from multiple origins.
"""

import json
import os
import boto3
import logging
from typing import Any, Dict, List, Optional
import tempfile
import subprocess
from botocore.exceptions import ClientError
import uuid
import re
from datetime import datetime, timedelta

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Authentication imports with fallbacks
try:
    import jwt
    JWT_AVAILABLE = True
    logger.info("✅ JWT library loaded successfully")
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("⚠️ JWT library not available")

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    logger.info("✅ bcrypt library loaded successfully")
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("⚠️ bcrypt library not available")

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
    logger.info("✅ pymongo library loaded successfully")
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("⚠️ pymongo library not available")

# Environment variables
BUCKET_NAME = 'videosplitter-storage-1751560247'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Updated CORS configuration - allow multiple origins
ALLOWED_ORIGINS = [
    'https://www.tads-video-splitter.com',
    'https://tads-video-splitter.com'
    'https://develop.tads-video-splitter.com',
    'https://main.tads-video-splitter.com', 
    'https://master.tads-video-splitter.com',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
    'https://working.tads-video-splitter.com'
]

# Authentication configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'change-this-in-production')
JWT_REFRESH_SECRET = os.environ.get('JWT_REFRESH_SECRET', 'change-this-refresh-secret')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# MongoDB configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
MONGODB_DB_NAME = os.environ.get('DB_NAME', 'videosplitter')

# In-memory user storage for demo purposes (fallback when MongoDB not available)
DEMO_USERS = {}

# Initialize AWS clients
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'

def get_cors_headers(origin=None):
    """Get CORS headers for API responses with origin checking"""
    # Check if the origin is in our allowed list
    allowed_origin = '*'  # Default fallback
    
    if origin:
        for allowed in ALLOWED_ORIGINS:
            if origin == allowed or origin.endswith(allowed.replace('https://', '').replace('http://', '')):
                allowed_origin = origin
                break
    
    return {
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }

def get_mongo_client():
    """Get MongoDB client connection with fallback handling"""
    if not MONGODB_AVAILABLE:
        logger.warning("MongoDB client not available - pymongo not installed")
        return None
    
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
        # Test the connection
        client.server_info()
        logger.info("✅ MongoDB connection successful")
        return client
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {str(e)}")
        logger.info("🔄 Falling back to in-memory storage for demo purposes")
        return None

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    if not BCRYPT_AVAILABLE:
        # Simple fallback hashing for demo (NOT for production)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    if not BCRYPT_AVAILABLE:
        # Simple fallback verification for demo (NOT for production)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    if not JWT_AVAILABLE:
        # Simple fallback token for demo (NOT for production)
        import base64
        token_data = json.dumps(data)
        return base64.b64encode(token_data.encode()).decode()
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    if not JWT_AVAILABLE:
        # Simple fallback token for demo (NOT for production)
        import base64
        token_data = json.dumps({**data, "type": "refresh"})
        return base64.b64encode(token_data.encode()).decode()
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token"""
    if not JWT_AVAILABLE:
        # Simple fallback verification for demo (NOT for production)
        try:
            import base64
            token_data = base64.b64decode(token.encode()).decode()
            payload = json.loads(token_data)
            return payload
        except Exception:
            return None
    
    try:
        secret = JWT_SECRET if token_type == "access" else JWT_REFRESH_SECRET
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != token_type:
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email from database or fallback storage"""
    client = get_mongo_client()
    
    if client:
        try:
            db = client[MONGODB_DB_NAME]
            users = db.users
            user = users.find_one({"email": email})
            client.close()
            return user
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            client.close()
    
    # Fallback to in-memory storage
    return DEMO_USERS.get(email)

def create_user(user_data: dict) -> str:
    """Create new user in database or fallback storage"""
    user_id = str(uuid.uuid4())
    user_data['user_id'] = user_id
    user_data['created_at'] = datetime.utcnow().isoformat()
    
    client = get_mongo_client()
    
    if client:
        try:
            db = client[MONGODB_DB_NAME]
            users = db.users
            users.insert_one(user_data)
            client.close()
            return user_id
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            client.close()
    
    # Fallback to in-memory storage
    DEMO_USERS[user_data['email']] = user_data
    return user_id

def handle_options(event):
    """Handle OPTIONS requests for CORS preflight"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(origin),
        'body': ''
    }

def handle_health_check(event):
    """Handle health check requests"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    # Check database connection status
    mongo_client = get_mongo_client()
    db_status = "connected" if mongo_client else "fallback_mode"
    if mongo_client:
        mongo_client.close()
    
    response_data = {
        'message': 'Video Splitter Pro API - Enhanced CORS Version',
        'version': '2.3',
        'timestamp': datetime.utcnow().isoformat(),
        'authentication': {
            'jwt_available': JWT_AVAILABLE,
            'bcrypt_available': BCRYPT_AVAILABLE,
            'mongodb_available': MONGODB_AVAILABLE
        },
        'database': db_status,
        'dependencies': {
            'bcrypt': BCRYPT_AVAILABLE,
            'jwt': JWT_AVAILABLE,
            'pymongo': MONGODB_AVAILABLE
        },
        'cors': {
            'allowed_origins': ALLOWED_ORIGINS,
            'current_origin': origin
        },
        'endpoints': [
            'POST /api/auth/register',
            'POST /api/auth/login', 
            'POST /api/auth/refresh',
            'GET /api/user/profile',
            'POST /api/generate-presigned-url',
            'POST /api/get-video-info',
            'GET /api/video-stream/{key}',
            'POST /api/split-video',
            'GET /api/job-status/{job_id}',
            'GET /api/download/{job_id}/{filename}'
        ]
    }
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(origin),
        'body': json.dumps(response_data)
    }

def handle_register(event):
    """Handle user registration"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')
        first_name = body.get('firstName', '')
        last_name = body.get('lastName', '')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Email and password are required'})
            }
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'User already exists'})
            }
        
        # Hash password and create user
        hashed_password = hash_password(password)
        user_data = {
            'email': email,
            'password': hashed_password,
            'first_name': first_name,
            'last_name': last_name,
            'email_verified': True  # For demo purposes
        }
        
        user_id = create_user(user_data)
        
        # Create tokens
        token_data = {'user_id': user_id, 'email': email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user_id,
            'demo_mode': not get_mongo_client(),
            'user': {
                'email': email,
                'firstName': first_name,
                'lastName': last_name
            }
        }
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(origin),
            'body': json.dumps(response_data)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Invalid JSON in request body'})
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Registration failed', 'error': str(e)})
        }

def handle_login(event):
    """Handle user login"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        password = body.get('password')
        
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Email and password are required'})
            }
        
        # Get user from database
        user = get_user_by_email(email)
        if not user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Invalid credentials'})
            }
        
        # Verify password
        if not verify_password(password, user['password']):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Invalid credentials'})
            }
        
        # Create tokens
        token_data = {'user_id': user['user_id'], 'email': email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'email': user['email'],
                'firstName': user.get('first_name', ''),
                'lastName': user.get('last_name', '')
            }
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(origin),
            'body': json.dumps(response_data)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Invalid JSON in request body'})
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Login failed', 'error': str(e)})
        }

def handle_user_profile(event):
    """Handle user profile requests"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        # Extract token from Authorization header
        auth_header = event.get('headers', {}).get('authorization') or event.get('headers', {}).get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Missing or invalid authorization header'})
            }
        
        token = auth_header.replace('Bearer ', '')
        payload = verify_token(token)
        
        if not payload:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Invalid or expired token'})
            }
        
        # Get user from database
        user = get_user_by_email(payload['email'])
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'User not found'})
            }
        
        response_data = {
            'user': {
                'email': user['email'],
                'firstName': user.get('first_name', ''),
                'lastName': user.get('last_name', ''),
                'userId': user['user_id']
            }
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(origin),
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to get profile', 'error': str(e)})
        }

def handle_video_stream(event):
    """Handle video streaming requests"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        # Extract S3 key from path
        path_parameters = event.get('pathParameters', {})
        s3_key = path_parameters.get('key') if path_parameters else None
        
        # Alternative: extract from path
        if not s3_key:
            path = event.get('path', '')
            if '/api/video-stream/' in path:
                s3_key = path.split('/api/video-stream/')[-1]
        
        if not s3_key:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'S3 key is required'})
            }
        
        logger.info(f"Generating video stream URL for key: {s3_key}")
        
        # Generate presigned URL for video streaming (longer expiration for streaming)
        try:
            stream_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                ExpiresIn=7200  # 2 hours for video streaming
            )
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({
                    'stream_url': stream_url,
                    's3_key': s3_key,
                    'expires_in': 7200
                })
            }
            
        except Exception as e:
            logger.error(f"Failed to generate stream URL: {str(e)}")
            return {
                'statusCode': 404,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Video not found or access denied'})
            }
        
    except Exception as e:
        logger.error(f"Video stream error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to generate video stream', 'error': str(e)})
        }

def handle_get_video_info(event):
    """Handle video metadata extraction requests"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        body = json.loads(event['body'])
        s3_key = body.get('s3_key')
        
        if not s3_key:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'S3 key is required'})
            }
        
        logger.info(f"Getting video info for key: {s3_key}")
        
        # Get basic file information from S3
        try:
            response = s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            file_size = response.get('ContentLength', 0)
            content_type = response.get('ContentType', 'video/unknown')
            last_modified = response.get('LastModified')
            
            # Extract format from filename or content type
            filename = s3_key.split('/')[-1] if '/' in s3_key else s3_key
            file_extension = filename.lower().split('.')[-1] if '.' in filename else 'unknown'
            
            # Enhanced metadata based on file type and size
            if file_extension == 'mkv':
                format_name = 'x-matroska'
                # MKV files commonly have subtitles
                estimated_subtitle_streams = 1
                estimated_audio_streams = 1
                estimated_video_streams = 1
            elif file_extension == 'mp4':
                format_name = 'mp4'
                estimated_subtitle_streams = 0  # Less common in MP4
                estimated_audio_streams = 1
                estimated_video_streams = 1
            elif file_extension == 'avi':
                format_name = 'avi'
                estimated_subtitle_streams = 0
                estimated_audio_streams = 1
                estimated_video_streams = 1
            else:
                format_name = file_extension
                estimated_subtitle_streams = 0
                estimated_audio_streams = 1
                estimated_video_streams = 1
            
            # Estimate duration based on file size (rough approximation)
            # Typical video bitrate: ~1-10 Mbps, so 1MB ~= 8-80 seconds
            # Conservative estimate: 1MB = 10 seconds for decent quality
            estimated_duration = max(60, int(file_size / (1024 * 1024 * 0.1)))  # At least 1 minute
            
            video_info = {
                'duration': estimated_duration,
                'format': format_name,
                'size': file_size,
                'video_streams': estimated_video_streams,
                'audio_streams': estimated_audio_streams,
                'subtitle_streams': estimated_subtitle_streams,
                'filename': filename,
                'file_extension': file_extension,
                'content_type': content_type,
                'last_modified': last_modified.isoformat() if last_modified else None,
                'estimated': True,
                'note': 'Metadata estimated from file properties - FFmpeg analysis not available in current Lambda'
            }
            
            logger.info(f"Generated video info: {video_info}")
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps(video_info)
            }
            
        except s3.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Video file not found'})
            }
        except Exception as e:
            logger.error(f"S3 error getting video info: {str(e)}")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Failed to access video file', 'error': str(e)})
            }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Invalid JSON in request body'})
        }
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to get video info', 'error': str(e)})
        }

def handle_split_video(event):
    """Handle video splitting requests - placeholder implementation"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    return {
        'statusCode': 501,
        'headers': get_cors_headers(origin),
        'body': json.dumps({
            'message': 'Video splitting not yet implemented',
            'note': 'This feature requires FFmpeg Lambda layer implementation',
            'status': 'coming_soon'
        })
    }

def handle_job_status(event):
    """Handle job status requests - placeholder implementation"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    return {
        'statusCode': 501,
        'headers': get_cors_headers(origin),
        'body': json.dumps({
            'message': 'Job status tracking not yet implemented',
            'note': 'This feature requires background processing implementation',
            'status': 'coming_soon'
        })
    }

def handle_download_file(event):
    """Handle file download requests - placeholder implementation"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    return {
        'statusCode': 501,
        'headers': get_cors_headers(origin),
        'body': json.dumps({
            'message': 'File download not yet implemented',
            'note': 'This feature requires processed file management',
            'status': 'coming_soon'
        })
    }

def handle_generate_presigned_url(event):
    """Handle presigned URL generation for S3 uploads"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        body = json.loads(event['body'])
        filename = body.get('filename')
        content_type = body.get('contentType', 'video/mp4')
        
        if not filename:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Filename is required'})
            }
        
        # Generate unique key for S3
        key = f"uploads/{uuid.uuid4()}/{filename}"
        
        # Generate presigned URL for upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key, 'ContentType': content_type},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(origin),
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'key': key
            })
        }
        
    except Exception as e:
        logger.error(f"Presigned URL error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to generate upload URL', 'error': str(e)})
        }
    
    try:
        body = json.loads(event['body'])
        filename = body.get('filename')
        content_type = body.get('contentType', 'video/mp4')
        
        if not filename:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Filename is required'})
            }
        
        # Generate unique key for S3
        key = f"uploads/{uuid.uuid4()}/{filename}"
        
        # Generate presigned URL for upload
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key, 'ContentType': content_type},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(origin),
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'key': key
            })
        }
        
    except Exception as e:
        logger.error(f"Presigned URL error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to generate upload URL', 'error': str(e)})
        }

def lambda_handler(event, context):
    """Main Lambda handler with enhanced CORS support"""
    # Log the incoming request
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    # Extract request details
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    logger.info(f"Method: {http_method}, Path: {path}, Origin: {origin}")
    
    try:
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return handle_options(event)
        
        # Route requests based on path
        if path == '/api/' or path == '/api':
            return handle_health_check(event)
        elif path == '/api/auth/register':
            return handle_register(event)
        elif path == '/api/auth/login':
            return handle_login(event)
        elif path == '/api/user/profile':
            return handle_user_profile(event)
        elif path == '/api/generate-presigned-url':
            return handle_generate_presigned_url(event)
        elif path.startswith('/api/video-stream/'):
            return handle_video_stream(event)
        elif path == '/api/get-video-info':
            return handle_get_video_info(event)
        elif path == '/api/split-video':
            return handle_split_video(event)
        elif path.startswith('/api/job-status/'):
            return handle_job_status(event)
        elif path.startswith('/api/download/'):
            return handle_download_file(event)
        else:
            # Return 404 for unknown paths
            return {
                'statusCode': 404,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': f'Path not found: {path}'})
            }
            
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)})
        }


if __name__ == "__main__":
    # Test the function locally
    test_event = {
        'httpMethod': 'GET',
        'path': '/api/',
        'headers': {
            'origin': 'http://localhost:3000'
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))