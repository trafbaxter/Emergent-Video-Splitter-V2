import json
import os
import boto3
import logging
from typing import Any, Dict, List
import tempfile
import subprocess
from botocore.exceptions import ClientError
import uuid
import re
from datetime import datetime

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
BUCKET_NAME = 'videosplitter-uploads'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://develop.tads-video-splitter.com')

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
    """Main Lambda handler for Video Splitter Pro API"""
    
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
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'message': 'Video Splitter Pro API - Core Functionality',
                    'version': '2.0',
                    'endpoints': [
                        'POST /api/generate-presigned-url',
                        'POST /api/get-video-info', 
                        'POST /api/split-video',
                        'GET /api/download/{key}'
                    ],
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Video processing endpoints
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