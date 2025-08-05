import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

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
        throw new Error('Failed to get upload URL');
      }

      const { uploadUrl, key } = await presignedResponse.json();

      // Upload file to S3 with progress tracking
      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentage = Math.round((e.loaded / e.total) * 100);
            setUploadProgress(percentage);
          }
        });

        xhr.addEventListener('load', async () => {
          if (xhr.status === 200) {
            setJobId(key);
            setUploadProgress(100);
            
            // Get video metadata and stream URL
            await getVideoInfo(key);
            await getVideoStream(key);
            resolve();
          } else {
            reject(new Error('Upload failed'));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });

        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', selectedFile.type);
        xhr.send(selectedFile);
      });

    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // Get video information
  const getVideoInfo = async (key) => {
    try {
      const response = await fetch(`${API_BASE}/api/get-video-info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ s3_key: key })
      });

      if (response.ok) {
        const info = await response.json();
        setVideoInfo(info);
      } else {
        // Fallback metadata
        setVideoInfo({
          duration: Math.floor(selectedFile.size / (1024 * 1024 * 60)), // Rough estimate
          format: selectedFile.type.split('/')[1] || 'unknown',
          size: selectedFile.size,
          video_streams: 1,
          audio_streams: 1,
          subtitle_streams: 0
        });
      }
    } catch (error) {
      console.error('Failed to get video info:', error);
      // Set fallback metadata
      setVideoInfo({
        duration: Math.floor(selectedFile.size / (1024 * 1024 * 60)),
        format: selectedFile.type.split('/')[1] || 'unknown',
        size: selectedFile.size,
        video_streams: 1,
        audio_streams: 1,
        subtitle_streams: 0
      });
    }
  };

  // Get video stream URL for preview
  const getVideoStream = async (key) => {
    try {
      const response = await fetch(`${API_BASE}/api/video-stream/${key}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVideoUrl(data.stream_url);
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
        // Start polling for progress
        pollProgress();
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
  const pollProgress = () => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/job-status/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setProgress(data.progress || 0);

          if (data.status === 'completed') {
            setSplitResults(data.results || []);
            setProcessing(false);
          } else if (data.status === 'failed') {
            alert('Processing failed: ' + (data.error || 'Unknown error'));
            setProcessing(false);
          } else {
            // Continue polling
            setTimeout(poll, 2000);
          }
        } else {
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

  return (
    <div style={{ 
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
                Drag & drop or click to browse
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
                    ...inputStyle,
                    marginBottom: '20px',
                    height: '45px'
                  }}
                >
                  <option value="time">Time-based (Manual Points)</option>
                  <option value="intervals">Equal Intervals</option>
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
                    style={inputStyle}
                  >
                    <option value="mp4">MP4</option>
                    <option value="mkv">MKV</option>
                    <option value="avi">AVI</option>
                    <option value="mov">MOV</option>
                    <option value="webm">WebM</option>
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