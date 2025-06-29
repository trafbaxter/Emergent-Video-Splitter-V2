from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, StreamingResponse
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="Video Splitter API",
    description="API for splitting video files while preserving subtitles",
    version="1.0.0"
)

# Configure app for large file uploads
app.router.route_class = type('CustomRoute', (app.router.route_class,), {
    'get_route_handler': lambda self: lambda: self.get_route_handler()
})

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

print(f"Upload directory: {UPLOAD_DIR}")
print(f"Process directory: {PROCESS_DIR}")
print(f"Output directory: {OUTPUT_DIR}")

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
                print(f"Using stream copy (no keyframes) for split {i+1}")
            else:
                # Re-encode with optional keyframe control
                output_args = {
                    'c:v': 'libx264',  # Video codec
                    'c:a': 'aac',      # Audio codec
                    'c:s': 'copy'      # Copy subtitle streams
                }
                
                # Add keyframe settings (simplified)
                if config.force_keyframes:
                    print(f"Enabling keyframes every {config.keyframe_interval}s for split {i+1}")
                    # Simplified keyframe settings
                    fps = 25  # Default FPS assumption
                    gop_size = int(config.keyframe_interval * fps)
                    
                    output_args.update({
                        'g': gop_size,  # GOP size 
                        'keyint_min': gop_size,  # Minimum interval between keyframes
                        'sc_threshold': '0',  # Disable scene change detection
                        'force_key_frames': f'expr:gte(t,n_forced*{config.keyframe_interval})'  # Force keyframes at intervals
                    })
                
                # Quality settings for re-encoding
                if config.preserve_quality:
                    output_args.update({
                        'crf': '18',  # High quality (lower = better quality)
                        'preset': 'medium'  # Balanced speed/quality
                    })
                    print(f"Using high quality encoding (CRF 18) for split {i+1}")
                else:
                    output_args.update({
                        'crf': '23',  # Standard quality
                        'preset': 'medium'
                    })
                    print(f"Using standard quality encoding (CRF 23) for split {i+1}")
            
            # Add subtitle sync offset if specified
            if config.subtitle_sync_offset != 0:
                output_args['itsoffset'] = -config.subtitle_sync_offset
            
            # Run ffmpeg
            try:
                print(f"Starting FFmpeg for split {i+1} with args: {output_args}")
                
                (
                    input_stream
                    .output(output_path, **output_args)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                output_files.append(output_path)
                print(f"Successfully completed split {i+1}: {output_filename}")
                
                # Update progress
                progress = ((i + 1) / total_splits) * 100
                await update_job_progress(job_id, progress)
                
            except ffmpeg.Error as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                print(f"FFmpeg error for split {i+1}: {error_msg}")
                logger.error(f"FFmpeg error for split {i+1}: {error_msg}")
                raise Exception(f"Error processing split {i+1}: {error_msg}")
            except Exception as e:
                print(f"General error for split {i+1}: {str(e)}")
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

@api_router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file with support for large files"""
    if not file.filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm')):
        raise HTTPException(status_code=400, detail="Unsupported video format")
    
    # Create job record
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
        async with aiofiles.open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(1024 * 1024)  # Read 1MB chunks
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
        
        # Save to database
        await db.video_jobs.insert_one(job.dict())
        
        logger.info(f"Successfully uploaded video: {file.filename}, size: {total_size / 1024 / 1024:.1f} MB")
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "size": job.original_size,
            "video_info": video_info
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
    background_tasks: BackgroundTasks
):
    """Start video splitting process"""
    # Get job from database
    job = await db.video_jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'uploaded':
        raise HTTPException(status_code=400, detail="Video not ready for processing")
    
    # Start background processing
    background_tasks.add_task(process_video_job, job_id, job['file_path'], config)
    
    return {"message": "Video splitting started", "job_id": job_id}

@api_router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    job = await db.video_jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job['id'],
        "filename": job['filename'],
        "status": job['status'],
        "progress": job['progress'],
        "splits": job.get('splits', []),
        "error_message": job.get('error_message'),
        "video_info": job.get('video_info')
    }

@api_router.get("/download/{job_id}/{filename}")
async def download_split(job_id: str, filename: str):
    """Download split video file"""
    job = await db.video_jobs.find_one({"id": job_id})
    if not job or job['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    file_path = OUTPUT_DIR / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=filename
    )

@api_router.get("/video-stream/{job_id}")
async def stream_video(job_id: str):
    """Stream video file for preview"""
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
        '.webm': 'video/webm'
    }
    media_type = media_type_map.get(file_ext, 'video/mp4')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=job['filename']
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()