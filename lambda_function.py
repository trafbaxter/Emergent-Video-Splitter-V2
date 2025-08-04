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
        except s3.exceptions.NoSuchKey:
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
            'subtitle_streams': [],
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
            'subtitle_streams': [],
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