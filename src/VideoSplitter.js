import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';
import './VideoSplitter.css';

const VideoPlayer = ({ videoUrl, videoRef, currentTime, setCurrentTime, formatTime, filename }) => {
  const [videoError, setVideoError] = useState(null);
  const [canPlay, setCanPlay] = useState(false);
  
  const handleVideoError = (e) => {
    console.error('Video error:', e);
    console.error('Video error details:', e.target.error);
    
    if (e.target.error) {
      const errorCode = e.target.error.code;
      const errorMessage = e.target.error.message;
      
      let userFriendlyMessage = '';
      if (errorCode === 4) {
        userFriendlyMessage = `Format not supported: Your ${filename.split('.').pop().toUpperCase()} file cannot be previewed in the browser, but it can still be processed for splitting.`;
      } else {
        userFriendlyMessage = `Playback error (Code ${errorCode}): ${errorMessage}`;
      }
      
      setVideoError(userFriendlyMessage);
    }
  };

  if (videoError) {
    return (
      <div style={{
        background: 'rgba(255, 165, 0, 0.2)',
        border: '1px solid rgba(255, 165, 0, 0.4)',
        borderRadius: '10px',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '10px' }}>⚠️</div>
        <h4 style={{ color: '#ffa500', margin: '0 0 10px 0' }}>Video Preview Not Available</h4>
        <p style={{ color: 'rgba(255,255,255,0.9)', margin: '0 0 15px 0', fontSize: '14px' }}>
          {videoError}
        </p>
        <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0, fontSize: '12px' }}>
          You can still configure split points manually or use equal intervals for processing.
        </p>
      </div>
    );
  }

  return (
    <div>
      <video
        ref={videoRef}
        src={videoUrl}
        controls
        onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
        onLoadStart={() => {
          console.log('Video loading started');
          setVideoError(null);
          setCanPlay(false);
        }}
        onLoadedData={() => console.log('Video data loaded')}
        onError={handleVideoError}
        onCanPlay={() => {
          console.log('Video can play');
          setCanPlay(true);
        }}
        style={{ 
          width: '100%', 
          borderRadius: '10px',
          maxHeight: '300px'
        }}
        crossOrigin="anonymous"
      />
      <div style={{ 
        marginTop: '15px', 
        color: 'rgba(255,255,255,0.8)',
        textAlign: 'center'
      }}>
        Current Time: {formatTime(currentTime)}
        {canPlay && <span style={{ color: '#4ade80', marginLeft: '15px' }}>✓ Ready to play</span>}
      </div>
      <div style={{ 
        marginTop: '5px', 
        color: 'rgba(255,255,255,0.6)',
        textAlign: 'center',
        fontSize: '12px'
      }}>
        Stream URL: {videoUrl.substring(0, 50)}...
      </div>
    </div>
  );
};

const VideoSplitter = () => {
  const { accessToken, API_BASE } = useAuth();
  
  // File handling
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  
  // Upload and processing state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [splitResults, setSplitResults] = useState(null);
  
  // Video player state
  const [videoUrl, setVideoUrl] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef(null);
  
  // Split configuration
  const [splitMethod, setSplitMethod] = useState('time');
  const [timePoints, setTimePoints] = useState([]);
  const [intervalDuration, setIntervalDuration] = useState(300); // 5 minutes
  const [preserveQuality, setPreserveQuality] = useState(true);
  const [outputFormat, setOutputFormat] = useState('mp4');
  const [forceKeyframes, setForceKeyframes] = useState(true);
  const [keyframeInterval, setKeyframeInterval] = useState(2);
  const [subtitleOffset, setSubtitleOffset] = useState(0);

  // Format time for display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle file selection
  const handleFileSelect = (files) => {
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        setSelectedFile(file);
        resetState();
      } else {
        alert('Please select a video file.');
      }
    }
  };

  // Reset component state
  const resetState = () => {
    setJobId(null);
    setVideoInfo(null);
    setVideoUrl(null);
    setTimePoints([]);
    setProgress(0);
    setSplitResults(null);
    setProcessing(false);
  };

  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, []);

  // File input change
  const handleFileInputChange = (e) => {
    handleFileSelect(e.target.files);
  };

  // Upload file to AWS S3
  const uploadFile = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      console.log('Starting upload process...');
      
      // Get presigned URL
      const presignedResponse = await fetch(`${API_BASE}/api/generate-presigned-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          filename: selectedFile.name,
          contentType: selectedFile.type
        })
      });

      if (!presignedResponse.ok) {
        const errorText = await presignedResponse.text();
        console.error('Presigned URL error:', errorText);
        throw new Error('Failed to get upload URL');
      }

      const { uploadUrl, key } = await presignedResponse.json();
      console.log('Got presigned URL, uploading to S3...');

      // Upload file to S3 with progress tracking
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentage = Math.round((e.loaded / e.total) * 100);
            setUploadProgress(percentage);
            console.log(`Upload progress: ${percentage}%`);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            console.log('Upload successful!');
            setUploadProgress(100);
            resolve();
          } else {
            console.error('Upload failed with status:', xhr.status);
            reject(new Error(`Upload failed with status: ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          console.error('Upload error');
          reject(new Error('Upload failed'));
        });

        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', selectedFile.type);
        xhr.send(selectedFile);
      });

      // Use the S3 key directly but ensure proper encoding
      console.log('S3 key from upload:', key);
      setJobId(key);

      // Get video metadata and stream URL using the S3 key
      console.log('Getting video metadata...');
      await getVideoInfo(key);
      await getVideoStream(key);

    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  // Get video information
  const getVideoInfo = async (key) => {
    try {
      console.log('Getting video info for key:', key);
      
      const response = await fetch(`${API_BASE}/api/get-video-info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ s3_key: key })
      });

      console.log('Video info response status:', response.status);

      if (response.ok) {
        const info = await response.json();
        console.log('Video info received:', info);
        setVideoInfo(info);
      } else {
        console.warn('Video info extraction failed, using enhanced fallback');
        const errorText = await response.text();
        console.error('Video info error:', errorText);
        
        // Enhanced fallback metadata based on file type
        const fileExtension = selectedFile.name.toLowerCase().split('.').pop();
        const estimatedDuration = Math.floor(selectedFile.size / (1024 * 1024 * 10)); // Better estimation
        
        setVideoInfo({
          duration: estimatedDuration,
          format: fileExtension === 'mkv' ? 'x-matroska' : (selectedFile.type.split('/')[1] || fileExtension),
          size: selectedFile.size,
          video_streams: 1,
          audio_streams: 1,
          // MKV files commonly have subtitles, so make a reasonable assumption
          subtitle_streams: fileExtension === 'mkv' ? 1 : 0,
          filename: selectedFile.name,
          container: fileExtension
        });
      }
    } catch (error) {
      console.error('Failed to get video info:', error);
      
      // Enhanced fallback metadata
      const fileExtension = selectedFile.name.toLowerCase().split('.').pop();
      const estimatedDuration = Math.floor(selectedFile.size / (1024 * 1024 * 10));
      
      setVideoInfo({
        duration: estimatedDuration,
        format: fileExtension === 'mkv' ? 'x-matroska' : (selectedFile.type.split('/')[1] || fileExtension),
        size: selectedFile.size,
        video_streams: 1,
        audio_streams: 1,
        subtitle_streams: fileExtension === 'mkv' ? 1 : 0,
        filename: selectedFile.name,
        container: fileExtension
      });
    }
  };

  // Get video stream URL for preview
  const getVideoStream = async (key) => {
    try {
      console.log('Getting video stream for key:', key);
      
      // Encode the S3 key properly for the URL path
      // But avoid double encoding if it's already encoded
      let encodedKey = key;
      if (!key.includes('%')) {
        encodedKey = encodeURIComponent(key);
      }
      
      // Add timestamp for cache busting
      const timestamp = Date.now();
      const response = await fetch(`${API_BASE}/api/video-stream/${encodedKey}?t=${timestamp}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      console.log('Video stream response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Video stream data:', data);
        
        if (data.stream_url) {
          setVideoUrl(data.stream_url);
          console.log('Video URL set:', data.stream_url);
          
          // Use direct DOM manipulation like the working version
          setTimeout(() => {
            if (videoRef.current) {
              console.log('Setting video src directly to DOM element');
              videoRef.current.src = data.stream_url;
              videoRef.current.load(); // Critical: explicit load() call!
            }
          }, 100);
        } else {
          console.warn('No stream_url in response:', data);
        }
      } else {
        console.error('Failed to get video stream, status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Failed to get video stream:', error);
    }
  };

  // Add current time to split points
  const addCurrentTime = () => {
    if (videoRef.current) {
      const time = Math.floor(videoRef.current.currentTime);
      if (!timePoints.includes(time)) {
        setTimePoints([...timePoints, time].sort((a, b) => a - b));
      }
    }
  };

  // Remove time point
  const removeTimePoint = (time) => {
    setTimePoints(timePoints.filter(t => t !== time));
  };

  // Add manual time point
  const addManualTimePoint = (timeInput) => {
    const parts = timeInput.split(':');
    let seconds = 0;
    
    if (parts.length === 2) {
      // MM:SS format
      seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
    } else if (parts.length === 3) {
      // HH:MM:SS format  
      seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    } else {
      // Assume it's just seconds
      seconds = parseInt(timeInput);
    }
    
    if (!isNaN(seconds) && seconds >= 0 && !timePoints.includes(seconds)) {
      setTimePoints([...timePoints, seconds].sort((a, b) => a - b));
    }
  };

  // Start video splitting
  const startSplitting = async () => {
    if (!jobId) return;

    setProcessing(true);
    setProgress(0);

    try {
      let splitConfig = {
        s3_key: jobId,
        method: splitMethod,
        preserve_quality: preserveQuality,
        output_format: outputFormat
      };

      if (splitMethod === 'time') {
        // Ensure we have the video end time for proper splitting
        const points = [...timePoints];
        if (videoInfo && videoInfo.duration > 0) {
          points.push(videoInfo.duration);
        }
        splitConfig.time_points = points.sort((a, b) => a - b);
      } else if (splitMethod === 'intervals') {
        splitConfig.interval_duration = intervalDuration;
      }

      if (forceKeyframes) {
        splitConfig.keyframe_interval = keyframeInterval;
      }

      if (subtitleOffset !== 0) {
        splitConfig.subtitle_offset = subtitleOffset;
      }

      const response = await fetch(`${API_BASE}/api/split-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(splitConfig)
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Split response:', data);
        
        if (data.job_id) {
          console.log('About to start polling with job_id:', data.job_id);
          // Start polling for progress using the actual processing job ID
          pollProgress(data.job_id);
        } else {
          console.error('No job_id in response:', data);
          throw new Error('No job ID received from server');
        }
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Split failed');
      }

    } catch (error) {
      console.error('Split failed:', error);
      alert('Split failed: ' + error.message);
      setProcessing(false);
    }
  };

  // Poll for split progress
  const pollProgress = (processingJobId) => {
    console.log('Starting progress polling for job_id:', processingJobId);
    
    const poll = async () => {
      try {
        console.log('Polling job status for:', processingJobId);
        const response = await fetch(`${API_BASE}/api/job-status/${processingJobId}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });

        console.log('Job status response:', response.status, response.statusText);

        if (response.ok) {
          const data = await response.json();
          console.log('Job status data:', data);
          setProgress(data.progress || 0);

          if (data.status === 'completed') {
            console.log('Job completed! Results:', data.results);
            setSplitResults(data.results || []);
            setProcessing(false);
          } else if (data.status === 'failed') {
            console.error('Job failed:', data.error);
            alert('Processing failed: ' + (data.error || 'Unknown error'));
            setProcessing(false);
          } else {
            console.log('Job still processing, progress:', data.progress || 0, 'status:', data.status);
            // Continue polling
            setTimeout(poll, 2000);
          }
        } else {
          console.warn('Job status request failed, retrying in 2 seconds');
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('Polling error:', error);
        setTimeout(poll, 2000);
      }
    };

    poll();
  };

  // Download split file
  const downloadFile = async (filename) => {
    try {
      const response = await fetch(`${API_BASE}/api/download/${jobId}/${filename}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        window.open(data.download_url, '_blank');
      } else {
        alert('Download failed');
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed');
    }
  };

  const cardStyle = {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    padding: '30px',
    marginBottom: '30px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
  };

  const buttonStyle = {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: '10px',
    padding: '12px 24px',
    color: 'white',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)'
  };

  const inputStyle = {
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '10px',
    padding: '10px 15px',
    color: 'white',
    fontSize: '14px',
    width: '100%',
    boxSizing: 'border-box'
  };

  const selectStyle = {
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '10px',
    padding: '10px 15px',
    color: 'white',
    fontSize: '14px',
    width: '100%',
    boxSizing: 'border-box'
  };

  return (
    <div className="video-splitter" style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: '700', 
            color: 'white', 
            margin: '0 0 10px 0',
            textShadow: '0 2px 10px rgba(0,0,0,0.3)'
          }}>
            Video Splitter Pro
          </h1>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            gap: '10px',
            marginBottom: '10px'
          }}>
            <span style={{ color: '#4ade80', fontSize: '1.2rem' }}>⚡</span>
            <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: '1.1rem', fontWeight: '500' }}>
              AWS Amplify Mode
            </span>
          </div>
          <p style={{ 
            color: 'rgba(255,255,255,0.8)', 
            fontSize: '1.2rem', 
            margin: 0,
            fontWeight: '300'
          }}>
            Split videos of any size while preserving subtitles and quality
          </p>
        </div>

        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
            Upload Video
          </h2>
          
          {!selectedFile ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${dragOver ? '#4ade80' : 'rgba(255,255,255,0.3)'}`,
                borderRadius: '15px',
                padding: '50px 20px',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                background: dragOver ? 'rgba(74, 222, 128, 0.1)' : 'transparent'
              }}
            >
              <input
                type="file"
                accept="video/*,.mp4,.avi,.mov,.mkv,.webm,.flv,.wmv,.m4v,.3gp,.ogv"
                onChange={handleFileInputChange}
                ref={fileInputRef}
                style={{ display: 'none' }}
              />
              
              <div style={{ fontSize: '3rem', marginBottom: '20px' }}>📁</div>
              <h3 style={{ color: 'white', fontSize: '1.3rem', margin: '0 0 10px 0' }}>
                Choose Video File
              </h3>
              <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0 }}>
                Drag & drop or click to browse<br/>
                <small>Supports: MP4, AVI, MOV, MKV, WebM, FLV, WMV, M4V</small>
              </p>
            </div>
          ) : (
            <div style={{
              background: 'rgba(74, 222, 128, 0.2)',
              borderRadius: '15px',
              padding: '20px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.2rem', color: '#4ade80', marginBottom: '10px', fontWeight: '600' }}>
                Selected: {selectedFile.name}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '20px' }}>
                Size: {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
              </div>
              
              {!jobId && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    uploadFile();
                  }}
                  disabled={uploading}
                  style={{
                    ...buttonStyle,
                    background: uploading ? 'rgba(255,255,255,0.2)' : 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    opacity: uploading ? 0.7 : 1
                  }}
                >
                  {uploading ? `Uploading... ${uploadProgress}%` : 'Upload to AWS S3'}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Video Preview and Info */}
        {videoInfo && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'fr 1fr',
            gap: '30px',
            marginBottom: '30px'
          }}>
            
            {/* Video Preview */}
            <div style={cardStyle}>
              <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
                Video Preview
              </h2>
              
              {videoUrl ? (
                <div>
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    controls
                    onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
                    onLoadStart={() => console.log('Video loading started')}
                    onLoadedData={() => console.log('Video data loaded')}
                    onError={(e) => {
                      console.error('Video error:', e);
                      console.error('Video error details:', e.target.error);
                      if (e.target.error && e.target.error.code === 4) {
                        console.warn('Video format may not be supported by browser player');
                      }
                    }}
                    onCanPlay={() => console.log('Video can play')}
                    style={{ 
                      width: '100%', 
                      borderRadius: '10px',
                      maxHeight: '300px'
                    }}
                  />
                  <div style={{ 
                    marginTop: '15px', 
                    color: 'rgba(255,255,255,0.8)',
                    textAlign: 'center'
                  }}>
                    Current Time: {formatTime(currentTime)}
                  </div>
                  <div style={{ 
                    marginTop: '5px', 
                    color: 'rgba(255,255,255,0.6)',
                    textAlign: 'center',
                    fontSize: '12px'
                  }}>
                    Stream URL: {videoUrl.substring(0, 50)}... (Content-Type: video/x-matroska for MKV)
                  </div>
                </div>
              ) : (
                <div style={{
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '10px',
                  padding: '50px',
                  textAlign: 'center',
                  color: 'rgba(255,255,255,0.6)'
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🎥</div>
                  <p>Video preview loading...</p>
                </div>
              )}
            </div>

            {/* Video Information */}
            <div style={cardStyle}>
              <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
                Video Information
              </h2>
              
              <div style={{ display: 'grid', gap: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Duration:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{formatTime(videoInfo.duration)}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Format:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{videoInfo.format}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Size:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{(videoInfo.size / (1024 * 1024)).toFixed(1)} MB</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Video Streams:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{videoInfo.video_streams}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Audio Streams:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{videoInfo.audio_streams}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(255,255,255,0.8)' }}>Subtitle Streams:</span>
                  <span style={{ color: 'white', fontWeight: '600' }}>{videoInfo.subtitle_streams}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Split Configuration */}
        {jobId && !processing && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '30px', fontWeight: '600' }}>
              Split Configuration
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' }}>
              
              {/* Left Column - Split Method */}
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Split Method</h3>
                
                <select
                  value={splitMethod}
                  onChange={(e) => setSplitMethod(e.target.value)}
                  style={{
                    ...selectStyle,
                    marginBottom: '20px',
                    height: '45px'
                  }}
                >
                  <option value="time" style={{backgroundColor: '#2d3748', color: 'white'}}>Time-based (Manual Points)</option>
                  <option value="intervals" style={{backgroundColor: '#2d3748', color: 'white'}}>Equal Intervals</option>
                </select>

                {splitMethod === 'time' && (
                  <div>
                    <div style={{ marginBottom: '15px' }}>
                      <button
                        onClick={addCurrentTime}
                        disabled={!videoRef.current}
                        style={{
                          ...buttonStyle,
                          marginRight: '10px',
                          fontSize: '14px',
                          padding: '8px 16px'
                        }}
                      >
                        Add Current Time ({formatTime(currentTime)})
                      </button>
                    </div>
                    
                    <div style={{ marginBottom: '15px' }}>
                      <input
                        type="text"
                        placeholder="MM:SS or HH:MM:SS"
                        style={inputStyle}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            addManualTimePoint(e.target.value);
                            e.target.value = '';
                          }
                        }}
                      />
                      <button
                        onClick={(e) => {
                          const input = e.target.previousSibling;
                          addManualTimePoint(input.value);
                          input.value = '';
                        }}
                        style={{
                          ...buttonStyle,
                          marginTop: '10px',
                          fontSize: '14px',
                          padding: '8px 16px'
                        }}
                      >
                        Add
                      </button>
                    </div>
                    
                    {timePoints.length > 0 && (
                      <div>
                        <h4 style={{ color: 'white', marginBottom: '10px' }}>Split Points:</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {timePoints.map((time, index) => (
                            <div
                              key={index}
                              style={{
                                background: 'rgba(74, 222, 128, 0.2)',
                                border: '1px solid rgba(74, 222, 128, 0.4)',
                                borderRadius: '20px',
                                padding: '5px 12px',
                                color: '#4ade80',
                                fontSize: '14px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                              }}
                            >
                              {formatTime(time)}
                              <button
                                onClick={() => removeTimePoint(time)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: '#ef4444',
                                  cursor: 'pointer',
                                  fontSize: '16px',
                                  padding: 0
                                }}
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {splitMethod === 'intervals' && (
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.9)', display: 'block', marginBottom: '8px' }}>
                      Interval Duration (seconds):
                    </label>
                    <input
                      type="number"
                      value={intervalDuration}
                      onChange={(e) => setIntervalDuration(parseInt(e.target.value))}
                      min="30"
                      max="3600"
                      style={inputStyle}
                    />
                  </div>
                )}
              </div>

              {/* Right Column - Quality Settings */}
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Quality Settings</h3>
                
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px', 
                    color: 'rgba(255,255,255,0.9)',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={preserveQuality}
                      onChange={(e) => setPreserveQuality(e.target.checked)}
                      style={{ transform: 'scale(1.2)' }}
                    />
                    Preserve original quality
                  </label>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label style={{ color: 'rgba(255,255,255,0.9)', display: 'block', marginBottom: '8px' }}>
                    Output Format:
                  </label>
                  <select
                    value={outputFormat}
                    onChange={(e) => setOutputFormat(e.target.value)}
                    style={{
                      ...selectStyle,
                      height: '45px'
                    }}
                  >
                    <option value="mp4" style={{backgroundColor: '#2d3748', color: 'white'}}>MP4</option>
                    <option value="mkv" style={{backgroundColor: '#2d3748', color: 'white'}}>MKV</option>
                    <option value="avi" style={{backgroundColor: '#2d3748', color: 'white'}}>AVI</option>
                    <option value="mov" style={{backgroundColor: '#2d3748', color: 'white'}}>MOV</option>
                    <option value="webm" style={{backgroundColor: '#2d3748', color: 'white'}}>WebM</option>
                  </select>
                </div>

                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px', marginTop: '30px' }}>Subtitle Settings</h3>
                
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ color: 'rgba(255,255,255,0.9)', display: 'block', marginBottom: '8px' }}>
                    Sync Offset (seconds):
                  </label>
                  <input
                    type="number"
                    value={subtitleOffset}
                    onChange={(e) => setSubtitleOffset(parseFloat(e.target.value))}
                    step="0.1"
                    style={inputStyle}
                  />
                </div>

                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px', marginTop: '30px' }}>Keyframe Settings</h3>
                
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px', 
                    color: 'rgba(255,255,255,0.9)',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={forceKeyframes}
                      onChange={(e) => setForceKeyframes(e.target.checked)}
                      style={{ transform: 'scale(1.2)' }}
                    />
                    Force keyframes at split points (recommended)
                  </label>
                </div>

                {forceKeyframes && (
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.9)', display: 'block', marginBottom: '8px' }}>
                      Keyframe Interval (seconds):
                    </label>
                    <input
                      type="number"
                      value={keyframeInterval}
                      onChange={(e) => setKeyframeInterval(parseInt(e.target.value))}
                      min="1"
                      max="10"
                      style={inputStyle}
                    />
                    <p style={{ 
                      color: 'rgba(255,255,255,0.6)', 
                      fontSize: '12px', 
                      margin: '5px 0 0 0' 
                    }}>
                      Smaller intervals = more keyframes = better seeking but larger files
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button
                onClick={startSplitting}
                disabled={splitMethod === 'time' && timePoints.length === 0}
                style={{
                  ...buttonStyle,
                  background: (splitMethod === 'time' && timePoints.length === 0) 
                    ? 'rgba(255,255,255,0.2)' 
                    : 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
                  fontSize: '18px',
                  padding: '15px 40px',
                  cursor: (splitMethod === 'time' && timePoints.length === 0) ? 'not-allowed' : 'pointer',
                  opacity: (splitMethod === 'time' && timePoints.length === 0) ? 0.5 : 1
                }}
              >
                Start Splitting
              </button>
            </div>
          </div>
        )}

        {/* Processing Progress */}
        {processing && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              🎬 Processing Video...
            </h2>
            
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '15px',
              height: '30px',
              overflow: 'hidden',
              marginBottom: '15px'
            }}>
              <div
                style={{
                  background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                  height: '100%',
                  width: `${progress}%`,
                  transition: 'width 0.3s ease',
                  borderRadius: '15px'
                }}
              />
            </div>
            
            <div style={{ 
              textAlign: 'center', 
              color: 'white', 
              fontSize: '18px', 
              fontWeight: '600' 
            }}>
              {progress}% Complete
            </div>
          </div>
        )}

        {/* Split Results */}
        {splitResults && splitResults.length > 0 && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              ✅ Split Complete!
            </h2>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
              gap: '20px' 
            }}>
              {splitResults.map((result, index) => (
                <div
                  key={index}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '15px',
                    padding: '20px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}
                >
                  <h3 style={{ 
                    color: 'white', 
                    fontSize: '1.1rem', 
                    margin: '0 0 15px 0', 
                    fontWeight: '600' 
                  }}>
                    Segment {index + 1}
                  </h3>
                  
                  <div style={{ marginBottom: '15px', color: 'rgba(255,255,255,0.8)' }}>
                    <div style={{ marginBottom: '5px' }}>
                      <strong>File:</strong> {result.filename}
                    </div>
                    <div style={{ marginBottom: '5px' }}>
                      <strong>Duration:</strong> {formatTime(result.duration || 0)}
                    </div>
                    <div>
                      <strong>Size:</strong> {((result.size || 0) / (1024 * 1024)).toFixed(1)} MB
                    </div>
                  </div>
                  
                  <button
                    onClick={() => downloadFile(result.filename)}
                    style={{
                      ...buttonStyle,
                      width: '100%',
                      background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                    }}
                  >
                    Download
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoSplitter;