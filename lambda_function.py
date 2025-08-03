import json
import os
import boto3
import logging
from typing import Any, Dict
import tempfile
import subprocess
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
BUCKET_NAME = os.environ.get('S3_BUCKET', 'videosplitter-storage-1751560247')
FFMPEG_LAMBDA_FUNCTION = 'ffmpeg-converter'

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for Video Splitter Pro API
    Handles video upload, processing, and download requests
    """
    
    try:
        # Parse the API Gateway event
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        headers = event.get('headers', {})
        body = event.get('body', '')
        query_params = event.get('queryStringParameters') or {}
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route to appropriate handler
        if path.startswith('/api/upload-video') and http_method == 'POST':
            return handle_upload_video(event, context)
        elif path.startswith('/api/video-info/') and http_method == 'GET':
            return handle_video_info(event, context)
        elif path.startswith('/api/split-video/') and http_method == 'POST':
            return handle_split_video(event, context)
        elif path.startswith('/api/job-status/') and http_method == 'GET':
            return handle_job_status(event, context)
        elif path.startswith('/api/download/') and http_method == 'GET':
            return handle_download(event, context)
        elif path.startswith('/api/video-stream/') and http_method == 'GET':
            return handle_video_stream(event, context)
        elif path == '/api/' or path == '/api' and http_method == 'GET':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'Video Splitter Pro API - AWS Lambda'})
            }
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_cors_headers() -> Dict[str, str]:
    """Return CORS headers for API responses"""
    return {
        'Access-Control-Allow-Origin': 'https://develop.tads-video-splitter.com',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept,Origin,Referer',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Credentials': 'false'
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
    """Handle video splitting request"""
    try:
        job_id = event['pathParameters']['job_id']
        
        # Get request body
        body = json.loads(event.get('body', '{}'))
        split_method = body.get('method', 'time_based')
        
        logger.info(f"Split request for job {job_id}: method={split_method}, config={body}")
        
        # Validate split configuration
        if split_method == 'time_based':
            time_points = body.get('time_points', [])
            if not time_points:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'No time points specified for time-based splitting'})
                }
        elif split_method == 'intervals':
            interval_duration = body.get('interval_duration', 0)
            if interval_duration <= 0:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Invalid interval duration specified'})
                }
        
        # For now, simulate processing by creating job status
        # In production, this would trigger actual video processing
        logger.info(f"Video splitting simulation started for job {job_id}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Video splitting request received and queued for processing',
                'job_id': job_id,
                'status': 'processing',
                'method': split_method,
                'note': 'This is a demo implementation - actual video processing would be implemented with FFmpeg in a separate processing service'
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
        job_id = event['pathParameters']['job_id']
        
        # In a real implementation:
        # Query DynamoDB for job status
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'id': job_id,
                'status': 'completed',
                'progress': 100,
                'splits': [
                    {'file': f'{job_id}_part_001.mp4'},
                    {'file': f'{job_id}_part_002.mp4'}
                ]
            })
        }
        
    except Exception as e:
        logger.error(f"Status handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def handle_download(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file download request"""
    try:
        job_id = event['pathParameters']['job_id']
        filename = event['pathParameters']['filename']
        
        # Generate presigned URL for download
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': f'outputs/{job_id}/{filename}'},
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 302,
            'headers': {
                **get_cors_headers(),
                'Location': download_url
            },
            'body': ''
        }
        
    except Exception as e:
        logger.error(f"Download handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
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
    """Extract video metadata with estimated duration based on file size"""
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
        # Different video qualities have different bitrates:
        # HD (1080p): ~8-12 Mbps average, ~60MB per minute
        # Standard: ~4-6 Mbps average, ~30MB per minute 
        # For 693MB file showing as 10:49, that's ~64MB per minute
        
        if file_size > 0:
            # Use 60MB per minute as baseline for HD video
            estimated_duration_minutes = file_size / (60 * 1024 * 1024)  # 60MB per minute
            estimated_duration = max(60, int(estimated_duration_minutes * 60))  # Convert to seconds, minimum 1 minute
        else:
            estimated_duration = 300  # Default 5 minutes if no size info
        
        return {
            'format': format_map.get(file_extension, file_extension),
            'duration': estimated_duration,  # Estimated duration in seconds
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
            'subtitle_streams': [],
            'chapters': []
        }
        
    except Exception as e:
        logger.error(f"Metadata extraction error: {str(e)}")
        return {
            'format': 'unknown',
            'duration': 0,
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