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
        # Add extensive logging for debugging
        logger.info(f"🚀 FFmpeg Lambda started")
        logger.info(f"📥 Raw event received: {json.dumps(event)}")
        logger.info(f"📋 Context: {context}")
        
        # Parse event
        operation = event.get('operation')
        source_bucket = event.get('source_bucket')
        source_key = event.get('source_key')
        job_id = event.get('job_id')
        
        logger.info(f"🔍 Parsed parameters:")
        logger.info(f"  - operation: {operation}")
        logger.info(f"  - source_bucket: {source_bucket}")
        logger.info(f"  - source_key: {source_key}")
        logger.info(f"  - job_id: {job_id}")
        
        if not all([operation, source_bucket, source_key, job_id]):
            missing = [param for param, value in [
                ('operation', operation),
                ('source_bucket', source_bucket), 
                ('source_key', source_key),
                ('job_id', job_id)
            ] if not value]
            error_msg = f"Missing required parameters: {missing}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"✅ All required parameters present")
        
        # Test FFmpeg availability
        logger.info(f"🧪 Testing FFmpeg availability...")
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ FFmpeg available: {result.stdout.split()[2]}")  # Version info
            else:
                logger.error(f"❌ FFmpeg test failed: {result.stderr}")
        except Exception as ffmpeg_error:
            logger.error(f"❌ FFmpeg test exception: {str(ffmpeg_error)}")
        
        # Download video file to /tmp
        logger.info(f"📥 Downloading video from S3: {source_bucket}/{source_key}")
        input_path = f'/tmp/{job_id}_input.mp4'
        
        try:
            s3.download_file(source_bucket, source_key, input_path)
            logger.info(f"✅ Downloaded to {input_path}")
            
            # Check file size
            import os
            file_size = os.path.getsize(input_path)
            logger.info(f"📊 Downloaded file size: {file_size} bytes")
            
        except Exception as download_error:
            logger.error(f"❌ Download failed: {str(download_error)}")
            raise download_error
        
        if operation == "extract_metadata":
            logger.info(f"🎬 Starting metadata extraction")
            return extract_video_metadata(input_path, job_id)
        elif operation == "split_video":
            logger.info(f"✂️ Starting video splitting")
            split_config = event.get('split_config', {})
            return split_video(input_path, source_bucket, job_id, split_config)
        else:
            error_msg = f"Unknown operation: {operation}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
            
    except Exception as e:
        logger.error(f"❌ FFmpeg Lambda error: {str(e)}")
        logger.error(f"💥 Exception type: {type(e).__name__}")
        logger.error(f"📍 Error occurred in lambda_handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': event.get('job_id'),
                'operation': event.get('operation'),
                'error_type': type(e).__name__
            })
        }

def extract_video_metadata(input_path: str, job_id: str) -> Dict[str, Any]:
    """Extract video metadata using FFmpeg (since ffprobe might not be available)"""
    try:
        logger.info(f"🎬 Starting metadata extraction for {job_id}")
        
        # Test if ffprobe is available
        try:
            ffprobe_test = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=5)
            if ffprobe_test.returncode == 0:
                logger.info("✅ ffprobe is available - using ffprobe")
                return extract_with_ffprobe(input_path, job_id)
            else:
                logger.warning("⚠️ ffprobe test failed - using ffmpeg instead")
                return extract_with_ffmpeg(input_path, job_id)
        except Exception as probe_error:
            logger.warning(f"⚠️ ffprobe not available: {probe_error}")
            logger.info("🔄 Falling back to ffmpeg for metadata extraction")
            return extract_with_ffmpeg(input_path, job_id)
        
    except Exception as e:
        logger.error(f"❌ Metadata extraction error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'operation': 'extract_metadata',
                'job_id': job_id
            })
        }

def extract_with_ffmpeg(input_path: str, job_id: str) -> Dict[str, Any]:
    """Extract metadata using ffmpeg -i (which outputs to stderr)"""
    try:
        logger.info(f"🔍 Using ffmpeg -i for metadata extraction")
        
        # Use ffmpeg -i to get file info (outputs to stderr)
        cmd = ['ffmpeg', '-i', input_path, '-f', 'null', '-']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # ffmpeg -i outputs info to stderr, and returns non-zero when no output file
        metadata_output = result.stderr
        
        logger.info(f"📊 FFmpeg output length: {len(metadata_output)} characters")
        
        if not metadata_output:
            raise Exception("No metadata output from ffmpeg")
        
        # Parse duration from ffmpeg output
        duration = 0
        if "Duration:" in metadata_output:
            import re
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', metadata_output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                duration = hours * 3600 + minutes * 60 + seconds
                logger.info(f"✅ Extracted duration: {duration} seconds ({duration//60}:{duration%60:02d})")
        
        # Parse format
        format_name = "unknown"
        if "Input #0" in metadata_output:
            import re
            format_match = re.search(r'Input #0, ([^,]+)', metadata_output)
            if format_match:
                format_name = format_match.group(1).strip()
                logger.info(f"✅ Extracted format: {format_name}")
        
        # Parse video stream info
        video_info = {}
        if "Video:" in metadata_output:
            import re
            video_match = re.search(r'Video: (\w+).*?(\d+)x(\d+)', metadata_output)
            if video_match:
                video_info = {
                    'codec': video_match.group(1),
                    'width': int(video_match.group(2)),
                    'height': int(video_match.group(3)),
                    'fps': 30  # Default, hard to parse reliably
                }
                logger.info(f"✅ Extracted video info: {video_info}")
        
        # Parse audio stream info  
        audio_info = {}
        if "Audio:" in metadata_output:
            import re
            audio_match = re.search(r'Audio: (\w+).*?(\d+) Hz', metadata_output)
            if audio_match:
                audio_info = {
                    'codec': audio_match.group(1),
                    'sample_rate': int(audio_match.group(2)),
                    'channels': 2  # Default
                }
                logger.info(f"✅ Extracted audio info: {audio_info}")
        
        # Get file size
        import os
        file_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
        
        metadata = {
            'job_id': job_id,
            'format': format_name,
            'duration': duration,
            'size': file_size,
            'bitrate': 0,  # Not easily extractable from ffmpeg -i
            'video_streams': 1 if video_info else 0,
            'audio_streams': 1 if audio_info else 0,
            'subtitle_streams': 0,  # Would need more parsing
            'video_info': video_info,
            'audio_info': audio_info
        }
        
        logger.info(f"🎉 Metadata extraction successful: duration={duration}s, format={format_name}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'operation': 'extract_metadata',
                'job_id': job_id,
                'metadata': metadata
            })
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "FFmpeg metadata extraction timed out (30s)"
        logger.error(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg, 'operation': 'extract_metadata', 'job_id': job_id})
        }
    except Exception as e:
        error_msg = f"FFmpeg metadata extraction failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg, 'operation': 'extract_metadata', 'job_id': job_id})
        }

def extract_with_ffprobe(input_path: str, job_id: str) -> Dict[str, Any]:
    """Extract metadata using ffprobe (preferred method if available)"""
    try:
        # Use ffprobe to get detailed video information
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
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
        logger.error(f"FFprobe metadata extraction error: {str(e)}")
        raise e

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