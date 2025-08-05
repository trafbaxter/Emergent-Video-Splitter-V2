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
BUCKET_NAME = 'videosplitter-uploads'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://develop.tads-video-splitter.com')

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

def get_cors_headers():
    """Get CORS headers for API responses"""
    return {
        'Access-Control-Allow-Origin': FRONTEND_URL,
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
        except:
            return None
    
    try:
        secret = JWT_SECRET if token_type == "access" else JWT_REFRESH_SECRET
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != token_type:
            return None
            
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> List[str]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    return errors

# ================================
# USER STORAGE FUNCTIONS (with MongoDB fallback)
# ================================

def find_user_by_email(email: str) -> Optional[dict]:
    """Find user by email with MongoDB fallback"""
    # Try MongoDB first
    client = get_mongo_client()
    if client:
        try:
            db = client[MONGODB_DB_NAME]
            users_collection = db.users
            user = users_collection.find_one({'email': email})
            client.close()
            if user:
                user['_id'] = str(user['_id']) if '_id' in user else None
            return user
        except Exception as e:
            logger.error(f"MongoDB query failed: {str(e)}")
            client.close()
    
    # Fallback to in-memory storage
    return DEMO_USERS.get(email)

def create_user(user_data: dict) -> bool:
    """Create user with MongoDB fallback"""
    # Try MongoDB first
    client = get_mongo_client()
    if client:
        try:
            db = client[MONGODB_DB_NAME]
            users_collection = db.users
            users_collection.insert_one(user_data)
            client.close()
            logger.info(f"User created in MongoDB: {user_data['email']}")
            return True
        except Exception as e:
            logger.error(f"MongoDB insert failed: {str(e)}")
            client.close()
    
    # Fallback to in-memory storage
    DEMO_USERS[user_data['email']] = user_data
    logger.info(f"User created in memory: {user_data['email']}")
    return True

def find_user_by_id(user_id: str) -> Optional[dict]:
    """Find user by ID with MongoDB fallback"""
    # Try MongoDB first
    client = get_mongo_client()
    if client:
        try:
            db = client[MONGODB_DB_NAME]
            users_collection = db.users
            user = users_collection.find_one({'user_id': user_id})
            client.close()
            if user:
                user['_id'] = str(user['_id']) if '_id' in user else None
            return user
        except Exception as e:
            logger.error(f"MongoDB query failed: {str(e)}")
            client.close()
    
    # Fallback to in-memory storage
    for email, user in DEMO_USERS.items():
        if user.get('user_id') == user_id:
            return user
    return None

# ================================
# AUTHENTICATION ENDPOINTS
# ================================

def handle_auth_register(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle user registration"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        first_name = body.get('firstName', '').strip()
        last_name = body.get('lastName', '').strip()
        
        # Validate input
        if not email or not password:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Email and password are required'})
            }
        
        if not validate_email(email):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid email format'})
            }
        
        password_errors = validate_password(password)
        if password_errors:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Password validation failed', 'details': password_errors})
            }
        
        # Check if user already exists
        existing_user = find_user_by_email(email)
        if existing_user:
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User already exists'})
            }
        
        # Hash password and create user
        hashed_password = hash_password(password)
        user_id = str(uuid.uuid4())
        
        user_doc = {
            'user_id': user_id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': hashed_password,
            'created_at': datetime.utcnow(),
            'is_active': True,
            'email_verified': False
        }
        
        if not create_user(user_doc):
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Failed to create user'})
            }
        
        # Create tokens
        token_data = {'user_id': user_id, 'email': email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"User registered successfully: {email}")
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'User registered successfully',
                'user_id': user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'demo_mode': not MONGODB_AVAILABLE or get_mongo_client() is None
            })
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Registration failed'})
        }

def handle_auth_login(event: Dict[str, Any], context) -> Dict[str, Any]:
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
        
        # Find user
        user = find_user_by_email(email)
        if not user or not verify_password(password, user['password']):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        
        if not user.get('is_active', True):
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Account is deactivated'})
            }
        
        # Create tokens
        token_data = {'user_id': user['user_id'], 'email': user['email']}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"User logged in successfully: {email}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Login successful',
                'user_id': user['user_id'],
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'user': {
                    'email': user['email'],
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'email_verified': user.get('email_verified', False)
                },
                'demo_mode': not MONGODB_AVAILABLE or get_mongo_client() is None
            })
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Login failed'})
        }

def handle_auth_refresh(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle token refresh"""
    try:
        body = json.loads(event.get('body', '{}'))
        refresh_token = body.get('refresh_token', '')
        
        if not refresh_token:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Refresh token is required'})
            }
        
        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid refresh token'})
            }
        
        # Create new access token
        token_data = {'user_id': payload['user_id'], 'email': payload['email']}
        new_access_token = create_access_token(token_data)
        
        logger.info(f"Token refreshed for user: {payload['email']}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'access_token': new_access_token,
                'token_type': 'Bearer'
            })
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Token refresh failed'})
        }

def get_current_user(event: Dict[str, Any]) -> Optional[dict]:
    """Extract current user from JWT token"""
    try:
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        payload = verify_token(token, "access")
        
        return payload
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

def handle_user_profile(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Get user profile (protected endpoint)"""
    try:
        # Check authentication
        current_user = get_current_user(event)
        if not current_user:
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Authentication required'})
            }
        
        # Get user data
        user = find_user_by_id(current_user['user_id'])
        if not user:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User not found'})
            }
        
        # Remove sensitive data
        if 'password' in user:
            del user['password']
        if '_id' in user:
            del user['_id']
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'user': user,
                'demo_mode': not MONGODB_AVAILABLE or get_mongo_client() is None
            })
        }
        
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to get profile'})
        }

# ================================
# CORE VIDEO PROCESSING ENDPOINTS (unchanged)
# ================================

def handle_generate_presigned_url(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Generate presigned URL for video upload"""
    try:
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename')
        content_type = body.get('contentType', 'video/mp4')
        
        if not filename:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Filename is required'})
            }
        
        # Generate unique object key
        object_key = f"uploads/{uuid.uuid4()}-{filename}"
        
        # Generate presigned URL
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': object_key,
                'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        logger.info(f"Generated presigned URL for {filename}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'objectKey': object_key
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to generate upload URL'})
        }

def handle_get_video_info(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Get video metadata using FFprobe via FFmpeg Lambda"""
    try:
        body = json.loads(event.get('body', '{}'))
        object_key = body.get('objectKey')
        
        if not object_key:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Object key is required'})
            }
        
        # Call FFmpeg Lambda for metadata extraction
        ffmpeg_payload = {
            'action': 'get_metadata',
            'bucket': BUCKET_NAME,
            'key': object_key
        }
        
        logger.info(f"Calling FFmpeg Lambda for metadata: {object_key}")
        
        response = lambda_client.invoke(
            FunctionName=FFMPEG_LAMBDA_FUNCTION,
            Payload=json.dumps(ffmpeg_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            result_body = json.loads(result['body'])
            logger.info(f"Video info retrieved for {object_key}")
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps(result_body)
            }
        else:
            logger.error(f"FFmpeg Lambda error: {result}")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Failed to get video information'})
            }
        
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to process request'})
        }

def handle_split_video(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Split video using FFmpeg Lambda"""
    try:
        body = json.loads(event.get('body', '{}'))
        object_key = body.get('objectKey')
        segments = body.get('segments', [])
        
        if not object_key or not segments:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Object key and segments are required'})
            }
        
        # Call FFmpeg Lambda for video splitting
        ffmpeg_payload = {
            'action': 'split_video',
            'bucket': BUCKET_NAME,
            'key': object_key,
            'segments': segments
        }
        
        logger.info(f"Calling FFmpeg Lambda for splitting: {object_key}")
        
        response = lambda_client.invoke(
            FunctionName=FFMPEG_LAMBDA_FUNCTION,
            Payload=json.dumps(ffmpeg_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            result_body = json.loads(result['body'])
            logger.info(f"Video split completed for {object_key}")
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps(result_body)
            }
        else:
            logger.error(f"FFmpeg Lambda error: {result}")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Failed to split video'})
            }
        
    except Exception as e:
        logger.error(f"Error splitting video: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to process request'})
        }

def handle_download_video(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Generate presigned URL for video download"""
    try:
        path_params = event.get('pathParameters', {})
        object_key = path_params.get('key')
        
        if not object_key:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Object key is required'})
            }
        
        # Generate presigned URL for download
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': object_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        logger.info(f"Generated download URL for {object_key}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'downloadUrl': presigned_url
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Failed to generate download URL'})
        }

def handle_options_request(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({})
    }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main Lambda handler for Video Splitter Pro API with Authentication"""
    
    try:
        # Log the incoming event for debugging
        logger.info(f"Event: {json.dumps(event)}")
        
        # Get HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return handle_options_request(event, context)
        
        # Route API requests
        if path == '/api/' or path == '/api':
            # Check MongoDB connectivity
            mongo_client = get_mongo_client()
            mongodb_status = "connected" if mongo_client else "fallback_mode"
            if mongo_client:
                mongo_client.close()
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'message': 'Video Splitter Pro API - Full Stack with Authentication',
                    'version': '2.2',
                    'authentication': "available",
                    'database': mongodb_status,
                    'core_endpoints': [
                        'POST /api/generate-presigned-url',
                        'POST /api/get-video-info', 
                        'POST /api/split-video',
                        'GET /api/download/{key}'
                    ],
                    'auth_endpoints': [
                        'POST /api/auth/register',
                        'POST /api/auth/login',
                        'POST /api/auth/refresh',
                        'GET /api/user/profile'
                    ],
                    'dependencies': {
                        'bcrypt': BCRYPT_AVAILABLE,
                        'jwt': JWT_AVAILABLE, 
                        'pymongo': MONGODB_AVAILABLE
                    },
                    'demo_mode': mongodb_status == "fallback_mode",
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Authentication endpoints
        elif path == '/api/auth/register' and http_method == 'POST':
            return handle_auth_register(event, context)
            
        elif path == '/api/auth/login' and http_method == 'POST':
            return handle_auth_login(event, context)
            
        elif path == '/api/auth/refresh' and http_method == 'POST':
            return handle_auth_refresh(event, context)
        
        # Protected user endpoints
        elif path == '/api/user/profile' and http_method == 'GET':
            return handle_user_profile(event, context)
        
        # Core video processing endpoints (unchanged)
        elif path == '/api/generate-presigned-url' and http_method == 'POST':
            return handle_generate_presigned_url(event, context)
            
        elif path == '/api/get-video-info' and http_method == 'POST':
            return handle_get_video_info(event, context)
            
        elif path == '/api/split-video' and http_method == 'POST':
            return handle_split_video(event, context)
            
        elif path.startswith('/api/download/') and http_method == 'GET':
            # Extract key from path
            object_key = path.replace('/api/download/', '')
            event['pathParameters'] = {'key': object_key}
            return handle_download_video(event, context)
        
        # Default response for unmatched routes
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Endpoint not found',
                    'path': path,
                    'method': http_method
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