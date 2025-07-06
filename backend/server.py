from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, Request, Depends
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
import json
import ffmpeg
import aiofiles
import tempfile
import shutil
import subprocess
import re
from io import BytesIO
import time

# Import authentication modules
from models import UserResponse
from auth import get_current_verified_user, AuthService
from auth_routes import auth_router, admin_router
from email_service import get_email_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="Video Splitter API",
    description="API for splitting video files while preserving subtitles - with authentication",
    version="2.0.0"
)

# Configure app for large file uploads
app.router.route_class = type('CustomRoute', (app.router.route_class,), {
    'get_route_handler': lambda self: lambda: self.get_route_handler()
})

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Database dependency
def get_db():
    """Get database connection"""
    return db

# Initialize authentication services on startup
auth_service = None
email_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global auth_service, email_service
    
    # Initialize authentication service
    auth_service = AuthService(db)
    email_service = get_email_service(db)
    
    # Initialize database (create default admin, indexes, etc.)
    try:
        from init_db import initialize_database
        await initialize_database()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def get_auth_service():
    """Get authentication service"""
    return auth_service

def get_email_service_instance():
    """Get email service"""
    return email_service

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create temp directories for video processing (Windows compatible)
TEMP_BASE = Path(tempfile.gettempdir()) / "video_splitter"
UPLOAD_DIR = TEMP_BASE / "uploads"
PROCESS_DIR = TEMP_BASE / "processing"
OUTPUT_DIR = TEMP_BASE / "outputs"

# Create directories if they don't exist
for dir_path in [UPLOAD_DIR, PROCESS_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Models
class VideoProcessingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_size: int
    status: str  # "uploading", "processing", "completed", "failed"
    progress: float = 0.0
    splits: List[Dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    video_info: Optional[Dict] = None

class SplitConfig(BaseModel):
    method: str  # "time_based", "intervals", "chapters"
    time_points: Optional[List[float]] = None  # for time_based splitting
    interval_duration: Optional[float] = None  # for interval splitting
    preserve_quality: bool = True
    output_format: str = "mp4"
    subtitle_sync_offset: float = 0.0
    force_keyframes: bool = True  # Force keyframes at split points
    keyframe_interval: float = 2.0  # Keyframe interval in seconds

class VideoInfo(BaseModel):
    duration: float
    format: str
    size: int
    video_streams: List[Dict]
    audio_streams: List[Dict]
    subtitle_streams: List[Dict]
    chapters: List[Dict] = []

# Helper functions
async def get_video_info(file_path: str) -> Dict:
    """Extract video information using ffprobe"""
    try:
        probe = ffmpeg.probe(file_path)
        
        video_streams = []
        audio_streams = []
        subtitle_streams = []
        
        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                video_streams.append({
                    'index': stream['index'],
                    'codec': stream['codec_name'],
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'fps': eval(stream.get('r_frame_rate', '0/1'))
                })
            elif stream['codec_type'] == 'audio':
                audio_streams.append({
                    'index': stream['index'],
                    'codec': stream['codec_name'],
                    'language': stream.get('tags', {}).get('language', 'unknown')
                })
            elif stream['codec_type'] == 'subtitle':
                subtitle_streams.append({
                    'index': stream['index'],
                    'codec': stream['codec_name'],
                    'language': stream.get('tags', {}).get('language', 'unknown')
                })
        
        # Extract chapters if available
        chapters = []
        if 'chapters' in probe:
            for chapter in probe['chapters']:
                chapters.append({
                    'id': chapter['id'],
                    'start': float(chapter['start_time']),
                    'end': float(chapter['end_time']),
                    'title': chapter.get('tags', {}).get('title', f'Chapter {chapter["id"]}')
                })
        
        return {
            'duration': float(probe['format']['duration']),
            'format': probe['format']['format_name'],
            'size': int(probe['format']['size']),
            'video_streams': video_streams,
            'audio_streams': audio_streams,
            'subtitle_streams': subtitle_streams,
            'chapters': chapters
        }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing video: {str(e)}")

async def split_video_with_subtitles(
    input_path: str, 
    output_dir: str, 
    splits: List[Dict], 
    config: SplitConfig,
    job_id: str
) -> List[str]:
    """Split video while preserving subtitles"""
    output_files = []
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        total_splits = len(splits)
        
        for i, split in enumerate(splits):
            start_time = split['start']
            end_time = split['end']
            duration = end_time - start_time
            
            # Generate output filename
            base_name = Path(input_path).stem
            output_filename = f"{base_name}_part_{i+1:03d}.{config.output_format}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Build ffmpeg command
            input_stream = ffmpeg.input(input_path, ss=start_time, t=duration)
            
            # Configure output based on quality settings and keyframes
            if config.preserve_quality and not config.force_keyframes:
                # Copy streams without re-encoding (fastest but no keyframe control)
                output_args = {
                    'c:v': 'copy',
                    'c:a': 'copy',
                    'c:s': 'copy'  # Copy subtitle streams
                }
            else:
                # Re-encode with optional keyframe control
                output_args = {
                    'c:v': 'libx264',  # Video codec
                    'c:a': 'aac',      # Audio codec
                    'c:s': 'copy'      # Copy subtitle streams
                }
                
                # Add keyframe settings (simplified)
                if config.force_keyframes:
                    # Very simple keyframe settings
                    gop_size = int(config.keyframe_interval * 30)  # 30fps assumption
                    
                    output_args.update({
                        'g': gop_size,  # GOP size 
                        'keyint_min': gop_size,  # Minimum interval between keyframes
                        'sc_threshold': '0'  # Disable scene change detection
                        # Removed complex force_key_frames for now
                    })
                
                # Quality settings for re-encoding
                if config.preserve_quality:
                    output_args.update({
                        'crf': '18',  # High quality (lower = better quality)
                        'preset': 'medium'  # Balanced speed/quality
                    })
                else:
                    output_args.update({
                        'crf': '23',  # Standard quality
                        'preset': 'medium'
                    })
            
            # Add subtitle sync offset if specified
            if config.subtitle_sync_offset != 0:
                output_args['itsoffset'] = -config.subtitle_sync_offset
            
            # Run ffmpeg
            try:
                (
                    input_stream
                    .output(output_path, **output_args)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                output_files.append(output_path)
                
                # Update progress
                progress = ((i + 1) / total_splits) * 100
                await update_job_progress(job_id, progress)
                
            except ffmpeg.Error as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                logger.error(f"FFmpeg error for split {i+1}: {error_msg}")
                raise Exception(f"Error processing split {i+1}: {error_msg}")
            except Exception as e:
                logger.error(f"General error for split {i+1}: {str(e)}")
                raise e
    
    except Exception as e:
        logger.error(f"Error splitting video: {e}")
        raise e
    
    return output_files

async def update_job_progress(job_id: str, progress: float, status: str = None):
    """Update job progress in database"""
    update_data = {
        'progress': progress,
        'updated_at': datetime.utcnow()
    }
    if status:
        update_data['status'] = status
    
    await db.video_jobs.update_one(
        {'id': job_id},
        {'$set': update_data}
    )

async def process_video_job(job_id: str, file_path: str, config: SplitConfig):
    """Background task to process video splitting"""
    try:
        # Update status to processing
        await update_job_progress(job_id, 0, "processing")
        
        # Get video info
        video_info = await get_video_info(file_path)
        
        # Generate splits based on method
        splits = []
        if config.method == "time_based" and config.time_points:
            # Sort time points
            time_points = sorted(config.time_points)
            for i in range(len(time_points)):
                start = time_points[i]
                end = time_points[i + 1] if i + 1 < len(time_points) else video_info['duration']
                splits.append({'start': start, 'end': end})
        
        elif config.method == "intervals" and config.interval_duration:
            duration = video_info['duration']
            current_time = 0
            while current_time < duration:
                end_time = min(current_time + config.interval_duration, duration)
                splits.append({'start': current_time, 'end': end_time})
                current_time = end_time
        
        elif config.method == "chapters" and video_info['chapters']:
            for chapter in video_info['chapters']:
                splits.append({'start': chapter['start'], 'end': chapter['end']})
        
        if not splits:
            raise Exception("No valid splits generated")
        
        # Create output directory for this job
        output_dir = OUTPUT_DIR / job_id
        
        # Split the video
        output_files = await split_video_with_subtitles(
            file_path, str(output_dir), splits, config, job_id
        )
        
        # Update job with completion
        await db.video_jobs.update_one(
            {'id': job_id},
            {'$set': {
                'status': 'completed',
                'progress': 100.0,
                'splits': [{'file': os.path.basename(f)} for f in output_files],
                'updated_at': datetime.utcnow()
            }}
        )
        
    except Exception as e:
        logger.error(f"Error processing video job {job_id}: {e}")
        await db.video_jobs.update_one(
            {'id': job_id},
            {'$set': {
                'status': 'failed',
                'error_message': str(e),
                'updated_at': datetime.utcnow()
            }}
        )

# API Endpoints
# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.get("/debug/test-video-preview")
async def test_video_preview():
    """Test video preview functionality with a small video"""
    # Create a more proper minimal MP4 file
    # This is a minimal MP4 file that should be recognizable by browsers
    mp4_header = bytes([
        # ftyp box
        0x00, 0x00, 0x00, 0x20,  # box size
        0x66, 0x74, 0x79, 0x70,  # 'ftyp'
        0x69, 0x73, 0x6F, 0x6D,  # major brand 'isom'
        0x00, 0x00, 0x02, 0x00,  # minor version
        0x69, 0x73, 0x6F, 0x6D,  # compatible brand 'isom'
        0x69, 0x73, 0x6F, 0x32,  # compatible brand 'iso2'
        0x61, 0x76, 0x63, 0x31,  # compatible brand 'avc1'
        0x6D, 0x70, 0x34, 0x31,  # compatible brand 'mp41'
        
        # mdat box with minimal data
        0x00, 0x00, 0x00, 0x10,  # box size
        0x6D, 0x64, 0x61, 0x74,  # 'mdat'
        0x00, 0x00, 0x00, 0x00,  # minimal data
        0x00, 0x00, 0x00, 0x00   # minimal data
    ])
    
    test_file_path = UPLOAD_DIR / "test_preview_video.mp4"
    
    with open(test_file_path, 'wb') as f:
        f.write(mp4_header)
    
    job_id = "test-preview-123"
    
    # Remove existing job if it exists
    await db.video_jobs.delete_one({"id": job_id})
    
    test_job = {
        "id": job_id,
        "filename": "test_preview_video.mp4",
        "original_size": len(mp4_header),
        "status": "uploaded",
        "file_path": str(test_file_path),
        "video_info": {
            "duration": 1.0,
            "format": "mp4",
            "size": len(mp4_header),
            "video_streams": [{"index": 0, "codec": "h264", "width": 640, "height": 480}],
            "audio_streams": [],
            "subtitle_streams": [],
            "chapters": []
        }
    }
    
    await db.video_jobs.insert_one(test_job)
    
    return {
        "message": "Test video created", 
        "job_id": job_id, 
        "streaming_url": f"/api/video-stream/{job_id}",
        "test_url": f"http://localhost:8000/api/video-stream/{job_id}"
    }

@api_router.get("/debug/create-mock-job")
async def create_mock_job():
    """Create a mock job for testing video streaming"""
    # Create a minimal MP4 file using base64 encoded data
    # This is a tiny valid MP4 file
    mp4_data = b''.join([
        b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom',
        b'\x00\x00\x00\x08free',
        b'\x00\x00\x00\x28mdat',
        b'Quick brown fox jumps over lazy dog'
    ])
    
    test_file_path = UPLOAD_DIR / "mock_test_video.mp4"
    
    # Create the mock MP4 file
    with open(test_file_path, 'wb') as f:
        f.write(mp4_data)
    
    job_id = "mock-job-123"
    
    # Remove existing mock job if it exists
    await db.video_jobs.delete_one({"id": job_id})
    
    mock_job = {
        "id": job_id,
        "filename": "mock_test_video.mp4",
        "original_size": len(mp4_data),
        "status": "uploaded",
        "file_path": str(test_file_path),
        "video_info": {
            "duration": 1.0,
            "format": "mp4",
            "size": len(mp4_data),
            "video_streams": [{"index": 0, "codec": "h264"}],
            "audio_streams": [],
            "subtitle_streams": [],
            "chapters": []
        }
    }
    
    # Save to database
    await db.video_jobs.insert_one(mock_job)
    
    return {"message": "Mock job created", "job_id": job_id, "streaming_url": f"/api/video-stream/{job_id}"}

@api_router.get("/debug/create-working-video")
async def create_working_video():
    """Create a simple HTML5 video that actually works"""
    
    # Instead of trying to create a complex MP4, let's create a simple WebM or use a different approach
    # For now, let's create a small test image that can be displayed
    
    # Simple 1x1 pixel GIF (browsers can handle this)
    gif_data = bytes([
        0x47, 0x49, 0x46, 0x38, 0x39, 0x61,  # GIF89a header
        0x01, 0x00, 0x01, 0x00,              # 1x1 pixels
        0x00, 0x00, 0x00,                    # Global color table flag
        0x21, 0xF9, 0x04,                    # Graphic control extension
        0x01, 0x00, 0x00, 0x00, 0x00,        # Delay, transparent color
        0x2C, 0x00, 0x00, 0x00, 0x00,        # Image descriptor
        0x01, 0x00, 0x01, 0x00, 0x00,        # Image dimensions
        0x02, 0x02, 0x04, 0x01, 0x00, 0x3B   # Image data and trailer
    ])
    
    test_file_path = UPLOAD_DIR / "working_test.gif"
    
    with open(test_file_path, 'wb') as f:
        f.write(gif_data)
    
    job_id = "working-test-456"
    
    # Remove existing job if it exists
    await db.video_jobs.delete_one({"id": job_id})
    
    test_job = {
        "id": job_id,
        "filename": "working_test.gif",
        "original_size": len(gif_data),
        "status": "uploaded",
        "file_path": str(test_file_path),
        "video_info": {
            "duration": 1.0,
            "format": "gif",
            "size": len(gif_data),
            "video_streams": [{"index": 0, "codec": "gif"}],
            "audio_streams": [],
            "subtitle_streams": [],
            "chapters": []
        }
    }
    
    await db.video_jobs.insert_one(test_job)
    
    return {
        "message": "Working test file created", 
        "job_id": job_id, 
        "streaming_url": f"/api/video-stream/{job_id}",
        "test_url": f"http://localhost:8000/api/video-stream/{job_id}",
        "note": "This is a GIF file for testing streaming"
    }
async def create_mock_job():
    """Create a mock job for testing video streaming"""
    # Create a minimal MP4 file using base64 encoded data
    # This is a tiny valid MP4 file
    mp4_data = b''.join([
        b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom',
        b'\x00\x00\x00\x08free',
        b'\x00\x00\x00\x28mdat',
        b'Quick brown fox jumps over lazy dog'
    ])
    
    test_file_path = UPLOAD_DIR / "mock_test_video.mp4"
    
    # Create the mock MP4 file
    with open(test_file_path, 'wb') as f:
        f.write(mp4_data)
    
    job_id = "mock-job-123"
    
    # Remove existing mock job if it exists
    await db.video_jobs.delete_one({"id": job_id})
    
    mock_job = {
        "id": job_id,
        "filename": "mock_test_video.mp4",
        "original_size": len(mp4_data),
        "status": "uploaded",
        "file_path": str(test_file_path),
        "video_info": {
            "duration": 1.0,
            "format": "mp4",
            "size": len(mp4_data),
            "video_streams": [{"index": 0, "codec": "h264"}],
            "audio_streams": [],
            "subtitle_streams": [],
            "chapters": []
        }
    }
    
    # Save to database
    await db.video_jobs.insert_one(mock_job)
    
    return {"message": "Mock job created", "job_id": job_id, "streaming_url": f"/api/video-stream/{job_id}"}

@api_router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Upload video file with support for large files (requires authentication)"""
    logger.info(f"Upload attempt by user {current_user.username} - filename: {file.filename}, content_type: {file.content_type}")
    
    if not file.filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm')):
        logger.error(f"Unsupported format: {file.filename}")
        raise HTTPException(status_code=400, detail="Unsupported video format")
    
    # Create job record with user ID
    job_id = str(uuid.uuid4())
    job = VideoProcessingJob(
        id=job_id,
        filename=file.filename,
        original_size=0,
        status="uploading"
    )
    
    # Save file with streaming to handle large files efficiently
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    try:
        # Stream file to disk to handle large files without loading into memory
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        async with aiofiles.open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                await f.write(chunk)
                total_size += len(chunk)
        
        job.original_size = total_size
        job.file_path = str(file_path)
        
        # Get video info
        video_info = await get_video_info(str(file_path))
        job.video_info = video_info
        job.status = "uploaded"
        
        # Save to database with user ID
        job_dict = job.dict()
        job_dict["user_id"] = current_user.id  # Link upload to user
        await db.video_jobs.insert_one(job_dict)
        
        logger.info(f"Successfully uploaded video by {current_user.username}: {file.filename}, size: {total_size / 1024 / 1024:.1f} MB")
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "size": job.original_size,
            "video_info": video_info,
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        # Clean up partial file if upload failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.post("/split-video/{job_id}")
async def split_video(
    job_id: str, 
    config: SplitConfig,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Start video splitting process (requires authentication)"""
    # Get job from database and verify ownership
    job = await db.video_jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user owns this job (admins can access any job)
    if current_user.role != "admin" and job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job['status'] != 'uploaded':
        raise HTTPException(status_code=400, detail="Video not ready for processing")
    
    # Start background processing
    background_tasks.add_task(process_video_job, job_id, job['file_path'], config)
    
    return {"message": "Video splitting started", "job_id": job_id}

@api_router.get("/job-status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Get job status and progress (requires authentication)"""
    job = await db.video_jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user owns this job (admins can access any job)
    if current_user.role != "admin" and job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": job['id'],
        "filename": job['filename'],
        "status": job['status'],
        "progress": job['progress'],
        "splits": job.get('splits', []),
        "error_message": job.get('error_message'),
        "video_info": job.get('video_info'),
        "user_id": job.get('user_id')
    }

@api_router.get("/download/{job_id}/{filename}")
async def download_split(
    job_id: str, 
    filename: str,
    current_user: UserResponse = Depends(get_current_verified_user)
):
    """Download split video file (requires authentication)"""
    job = await db.video_jobs.find_one({"id": job_id})
    if not job or job['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    # Check if user owns this job (admins can access any job)
    if current_user.role != "admin" and job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = OUTPUT_DIR / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@api_router.head("/video-stream/{job_id}")
async def video_stream_head(job_id: str):
    """Handle HEAD requests for video streaming"""
    job = await db.video_jobs.find_one({"id": job_id})
    if not job or not job.get('file_path'):
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = Path(job['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Determine media type based on file extension
    file_ext = file_path.suffix.lower()
    media_type_map = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.gif': 'image/gif'
    }
    media_type = media_type_map.get(file_ext, 'video/mp4')
    
    # Get file size
    file_size = file_path.stat().st_size
    
    return JSONResponse(
        content={},
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
            'Content-Type': media_type,
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Range'
        }
    )

@api_router.options("/video-stream/{job_id}")
async def video_stream_options(job_id: str):
    """Handle CORS preflight for video streaming"""
    return JSONResponse(
        content={},
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Range, Content-Type',
            'Access-Control-Max-Age': '3600'
        }
    )

@api_router.get("/video-stream/{job_id}")
async def stream_video(job_id: str, request: Request):
    """Stream video file for preview with proper headers"""
    job = await db.video_jobs.find_one({"id": job_id})
    
    if not job or not job.get('file_path'):
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = Path(job['file_path'])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Determine media type based on file extension
    file_ext = file_path.suffix.lower()
    media_type_map = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.gif': 'image/gif'
    }
    media_type = media_type_map.get(file_ext, 'video/mp4')
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Handle range requests for video streaming
    range_header = request.headers.get('range')
    if range_header:
        # Parse range header
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            # Read the requested range
            with open(file_path, 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)
            
            return StreamingResponse(
                BytesIO(data),
                status_code=206,
                headers={
                    'Accept-Ranges': 'bytes',
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Content-Length': str(end - start + 1),
                    'Content-Type': media_type,
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Range'
                },
                media_type=media_type
            )
    
    # Return full file for non-range requests
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=job['filename'],
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Range, Content-Type',
            'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges'
        }
    )

@api_router.get("/download-source")
async def download_source():
    """Download complete source code as zip"""
    import zipfile
    import tempfile
    
    # Create temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add backend files
        for root, dirs, files in os.walk('/app/backend'):
            for file in files:
                if not file.endswith(('.pyc', '.log')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, '/app')
                    zipf.write(file_path, arcname)
        
        # Add frontend files (excluding node_modules)
        for root, dirs, files in os.walk('/app/frontend'):
            if 'node_modules' in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '/app')
                zipf.write(file_path, arcname)
    
    return FileResponse(
        temp_zip.name,
        media_type='application/zip',
        filename='VideoSplitter.zip'
    )

@api_router.delete("/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Clean up job files"""
    try:
        # Remove upload file
        job = await db.video_jobs.find_one({"id": job_id})
        if job and job.get('file_path'):
            upload_path = Path(job['file_path'])
            if upload_path.exists():
                upload_path.unlink()
        
        # Remove output directory
        output_dir = OUTPUT_DIR / job_id
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        # Remove job from database
        await db.video_jobs.delete_one({"id": job_id})
        
        return {"message": "Job cleaned up successfully"}
    
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Add CORS middleware before including routes
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router in the main app
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()