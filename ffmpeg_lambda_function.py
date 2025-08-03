import json
import subprocess
import boto3
import os
import logging
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client('s3')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    FFmpeg Lambda function for video processing
    
    Expected event structure:
    {
        "operation": "extract_metadata" | "split_video",
        "source_bucket": "bucket-name",
        "source_key": "path/to/video.mp4", 
        "job_id": "unique-job-id",
        "split_config": {  # Only for split_video operation
            "method": "time_based" | "intervals",
            "time_points": [0, 300, 600],  # for time_based
            "interval_duration": 300,      # for intervals
            "preserve_quality": true,
            "output_format": "mp4"
        }
    }
    """
    
    try:
        # Parse event
        operation = event.get('operation')
        source_bucket = event.get('source_bucket')
        source_key = event.get('source_key')
        job_id = event.get('job_id')
        
        logger.info(f"Processing {operation} for job {job_id}: {source_key}")
        
        if not all([operation, source_bucket, source_key, job_id]):
            raise ValueError("Missing required parameters: operation, source_bucket, source_key, job_id")
        
        # Download video file to /tmp
        input_path = f'/tmp/{job_id}_input.mp4'
        s3.download_file(source_bucket, source_key, input_path)
        logger.info(f"Downloaded {source_key} to {input_path}")
        
        if operation == "extract_metadata":
            return extract_video_metadata(input_path, job_id)
        elif operation == "split_video":
            split_config = event.get('split_config', {})
            return split_video(input_path, source_bucket, job_id, split_config)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"FFmpeg Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': event.get('job_id'),
                'operation': event.get('operation')
            })
        }

def extract_video_metadata(input_path: str, job_id: str) -> Dict[str, Any]:
    """Extract video metadata using FFprobe"""
    try:
        # Use ffprobe to get detailed video information
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFprobe failed: {result.stderr}")
        
        probe_data = json.loads(result.stdout)
        
        # Extract relevant information
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        # Find video and audio streams
        video_streams = [s for s in streams if s.get('codec_type') == 'video']
        audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
        subtitle_streams = [s for s in streams if s.get('codec_type') == 'subtitle']
        
        # Get actual duration
        duration = float(format_info.get('duration', 0))
        
        metadata = {
            'job_id': job_id,
            'format': format_info.get('format_name', 'unknown'),
            'duration': int(duration),  # Duration in seconds
            'size': int(format_info.get('size', 0)),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'video_streams': len(video_streams),
            'audio_streams': len(audio_streams), 
            'subtitle_streams': len(subtitle_streams),
            'video_info': {
                'codec': video_streams[0].get('codec_name') if video_streams else None,
                'width': video_streams[0].get('width') if video_streams else None,
                'height': video_streams[0].get('height') if video_streams else None,
                'fps': eval(video_streams[0].get('r_frame_rate', '0/1')) if video_streams else None
            } if video_streams else {},
            'audio_info': {
                'codec': audio_streams[0].get('codec_name') if audio_streams else None,
                'sample_rate': audio_streams[0].get('sample_rate') if audio_streams else None,
                'channels': audio_streams[0].get('channels') if audio_streams else None
            } if audio_streams else {}
        }
        
        logger.info(f"Extracted metadata for {job_id}: duration={duration}s, format={metadata['format']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'operation': 'extract_metadata',
                'job_id': job_id,
                'metadata': metadata
            })
        }
        
    except Exception as e:
        logger.error(f"Metadata extraction error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'operation': 'extract_metadata',
                'job_id': job_id
            })
        }

def split_video(input_path: str, output_bucket: str, job_id: str, split_config: Dict[str, Any]) -> Dict[str, Any]:
    """Split video using FFmpeg"""
    try:
        method = split_config.get('method', 'time_based')
        preserve_quality = split_config.get('preserve_quality', True)
        output_format = split_config.get('output_format', 'mp4')
        
        logger.info(f"Splitting video {job_id} using method: {method}")
        
        output_files = []
        
        if method == 'time_based':
            time_points = split_config.get('time_points', [])
            if not time_points or len(time_points) < 2:
                raise ValueError("Time-based splitting requires at least 2 time points")
            
            output_files = split_by_time_points(input_path, output_bucket, job_id, time_points, 
                                              preserve_quality, output_format)
                                              
        elif method == 'intervals':
            interval_duration = split_config.get('interval_duration', 300)  # 5 minutes default
            if interval_duration <= 0:
                raise ValueError("Invalid interval duration")
            
            output_files = split_by_intervals(input_path, output_bucket, job_id, interval_duration,
                                            preserve_quality, output_format)
        else:
            raise ValueError(f"Unknown split method: {method}")
        
        logger.info(f"Split completed for {job_id}: {len(output_files)} segments created")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'operation': 'split_video',
                'job_id': job_id,
                'method': method,
                'output_files': output_files,
                'segments_created': len(output_files)
            })
        }
        
    except Exception as e:
        logger.error(f"Video splitting error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'operation': 'split_video',
                'job_id': job_id
            })
        }

def split_by_time_points(input_path: str, output_bucket: str, job_id: str, 
                        time_points: List[int], preserve_quality: bool, output_format: str) -> List[str]:
    """Split video at specific time points"""
    output_files = []
    
    # Sort time points and create segments
    sorted_points = sorted(set(time_points))
    
    for i in range(len(sorted_points) - 1):
        start_time = sorted_points[i]
        end_time = sorted_points[i + 1]
        duration = end_time - start_time
        
        if duration <= 0:
            continue
            
        part_num = f"{i+1:03d}"
        output_filename = f"{job_id}_part_{part_num}.{output_format}"
        output_path = f"/tmp/{output_filename}"
        
        # FFmpeg command for segment
        cmd = ['ffmpeg', '-i', input_path, '-ss', str(start_time), '-t', str(duration)]
        
        if preserve_quality:
            cmd.extend(['-c', 'copy'])  # Copy without re-encoding
        else:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])  # Re-encode
            
        cmd.extend(['-avoid_negative_ts', 'make_zero', output_path])
        
        logger.info(f"Creating segment {part_num}: {start_time}s to {end_time}s")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error for segment {part_num}: {result.stderr}")
            continue
        
        # Upload to S3
        s3_key = f"outputs/{job_id}/{output_filename}"
        s3.upload_file(output_path, output_bucket, s3_key)
        
        output_files.append({
            'filename': output_filename,
            's3_key': s3_key,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        })
        
        # Clean up local file
        os.remove(output_path)
    
    return output_files

def split_by_intervals(input_path: str, output_bucket: str, job_id: str,
                      interval_duration: int, preserve_quality: bool, output_format: str) -> List[str]:
    """Split video into equal intervals"""
    
    # Get video duration first
    cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
           '-of', 'csv=p=0', input_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception("Could not determine video duration")
    
    total_duration = float(result.stdout.strip())
    
    # Generate time points based on interval
    time_points = []
    current_time = 0
    while current_time < total_duration:
        time_points.append(int(current_time))
        current_time += interval_duration
    
    # Add final time point
    time_points.append(int(total_duration))
    
    return split_by_time_points(input_path, output_bucket, job_id, time_points, 
                               preserve_quality, output_format)