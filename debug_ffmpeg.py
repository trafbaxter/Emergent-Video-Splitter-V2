#!/usr/bin/env python3

import ffmpeg
import tempfile
from pathlib import Path

def test_ffmpeg_keyframes():
    """Test FFmpeg keyframe functionality"""
    
    # Test keyframe parameters
    keyframe_interval = 2.0
    fps = 25
    gop_size = int(keyframe_interval * fps)
    
    print(f"Testing keyframe settings:")
    print(f"Keyframe interval: {keyframe_interval}s")
    print(f"GOP size: {gop_size}")
    
    # Test output args
    output_args = {
        'c:v': 'libx264',
        'c:a': 'aac', 
        'c:s': 'copy',
        'g': gop_size,
        'keyint_min': gop_size,
        'sc_threshold': '0',
        'force_key_frames': f'expr:gte(t,n_forced*{keyframe_interval})',
        'crf': '18',
        'preset': 'medium'
    }
    
    print(f"Output args: {output_args}")
    
    # Test FFmpeg command generation (without running)
    try:
        input_stream = ffmpeg.input('test_input.mp4', ss=0, t=10)
        output_stream = input_stream.output('test_output.mp4', **output_args)
        cmd = ffmpeg.compile(output_stream)
        print(f"Generated FFmpeg command: {' '.join(cmd)}")
        return True
    except Exception as e:
        print(f"Error generating FFmpeg command: {e}")
        return False

if __name__ == "__main__":
    test_ffmpeg_keyframes()