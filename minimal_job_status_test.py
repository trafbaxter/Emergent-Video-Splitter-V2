#!/usr/bin/env python3
"""
Minimal job status test to identify the timeout issue
"""

import json
import boto3
import logging
import time

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
BUCKET_NAME = 'videosplitter-storage-1751560247'
s3 = boto3.client('s3')

def get_cors_headers(origin=None):
    """Get CORS headers for API responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Credentials': 'false'
    }

def handle_job_status_minimal(event):
    """Minimal job status handler to test timeout issue"""
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    try:
        # Extract job ID from path
        path = event.get('path', '')
        job_id = None
        
        if '/api/job-status/' in path:
            job_id = path.split('/api/job-status/')[-1]
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'Job ID is required'})
            }
        
        logger.info(f"Minimal job status request for: {job_id}")
        
        # Test 1: Return immediately without S3 call
        if job_id.startswith('immediate-'):
            logger.info("Returning immediate response")
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({
                    'job_id': job_id,
                    'status': 'processing',
                    'progress': 25,
                    'message': 'Immediate response test - no S3 call',
                    'test': 'immediate'
                })
            }
        
        # Test 2: Quick S3 call with timeout
        logger.info("Starting S3 operation")
        start_time = time.time()
        
        try:
            output_prefix = f"outputs/{job_id}/"
            response = s3.list_objects_v2(
                Bucket=BUCKET_NAME, 
                Prefix=output_prefix,
                MaxKeys=5
            )
            
            s3_time = time.time() - start_time
            logger.info(f"S3 operation completed in {s3_time:.2f}s")
            
            file_count = len(response.get('Contents', []))
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({
                    'job_id': job_id,
                    'status': 'processing',
                    'progress': 25 if file_count == 0 else 50 if file_count == 1 else 100,
                    'message': f'S3 check completed in {s3_time:.2f}s, found {file_count} files',
                    'file_count': file_count,
                    's3_time': s3_time,
                    'test': 's3_check'
                })
            }
            
        except Exception as s3_error:
            s3_time = time.time() - start_time
            logger.error(f"S3 error after {s3_time:.2f}s: {str(s3_error)}")
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({
                    'job_id': job_id,
                    'status': 'processing',
                    'progress': 30,
                    'message': f'S3 error after {s3_time:.2f}s: {str(s3_error)}',
                    'test': 's3_error'
                })
            }
        
    except Exception as e:
        logger.error(f"Job status error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(origin),
            'body': json.dumps({'message': 'Failed to get job status', 'error': str(e)})
        }

def lambda_handler(event, context):
    """Minimal Lambda handler for testing"""
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin')
    
    logger.info(f"Method: {http_method}, Path: {path}, Origin: {origin}")
    
    try:
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Handle job status requests
        if path.startswith('/api/job-status/'):
            return handle_job_status_minimal(event)
        
        # Health check
        if path == '/api/' or path == '/api':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(origin),
                'body': json.dumps({
                    'message': 'Minimal job status test API',
                    'version': '1.0',
                    'timestamp': time.time()
                })
            }
        
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
    # Test locally
    test_event = {
        'httpMethod': 'GET',
        'path': '/api/job-status/test-job-123',
        'headers': {'origin': 'https://working.tads-video-splitter.com'}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))