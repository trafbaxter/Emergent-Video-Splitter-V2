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
  const [forceKeyframes, setForceKeyframes] = useState(false);
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

      // Upload file to S3
      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        body: selectedFile,
        headers: {
          'Content-Type': selectedFile.type
        }
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file');
      }

      setJobId(key);
      setUploadProgress(100);

      // Get video metadata
      await getVideoInfo(key);
      await getVideoStream(key);

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
        // Metadata extraction might fail due to timeout, but video can still be processed
        console.warn('Failed to get video info, using fallback');
        setVideoInfo({
          duration: 0,
          format: selectedFile.type.split('/')[1] || 'unknown',
          size: selectedFile.size,
          video_streams: 1,
          audio_streams: 1,
          subtitle_streams: 0
        });
      }
    } catch (error) {
      console.error('Failed to get video info:', error);
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

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
        Video Splitter Pro
      </h1>

      {/* File Upload Section */}
      <div style={{ marginBottom: '30px' }}>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `3px dashed ${dragOver ? '#007bff' : '#ccc'}`,
            borderRadius: '10px',
            padding: '40px',
            textAlign: 'center',
            backgroundColor: dragOver ? '#f8f9fa' : '#fafafa',
            cursor: selectedFile ? 'default' : 'pointer',
            transition: 'all 0.3s ease'
          }}
          onClick={() => !selectedFile && fileInputRef.current?.click()}
        >
          <input
            type="file"
            accept="video/*"
            onChange={handleFileInputChange}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          
          {selectedFile ? (
            <div>
              <h3 style={{ margin: '0 0 10px 0', color: '#28a745' }}>✓ File Selected</h3>
              <p style={{ margin: '5px 0', fontSize: '18px', fontWeight: 'bold' }}>
                {selectedFile.name}
              </p>
              <p style={{ margin: '5px 0', color: '#666' }}>
                Size: {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
              </p>
              {!jobId && (
                <button
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent event bubbling to parent div
                    uploadFile();
                  }}
                  disabled={uploading}
                  style={{
                    marginTop: '20px',
                    padding: '12px 30px',
                    fontSize: '16px',
                    backgroundColor: uploading ? '#6c757d' : '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: uploading ? 'not-allowed' : 'pointer'
                  }}
                >
                  {uploading ? `Uploading... ${uploadProgress}%` : 'Upload & Process'}
                </button>
              )}
            </div>
          ) : (
            <div>
              <h3 style={{ margin: '0 0 15px 0', color: '#666' }}>
                Drop your video file here or click to browse
              </h3>
              <p style={{ color: '#999' }}>
                Supports: MP4, AVI, MOV, MKV, WebM, FLV, WMV
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Video Info and Preview */}
      {videoInfo && (
        <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '10px' }}>
          <h3 style={{ marginBottom: '15px' }}>Video Information</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginBottom: '20px' }}>
            <div><strong>Duration:</strong> {videoInfo.duration > 0 ? formatTime(videoInfo.duration) : 'Processing...'}</div>
            <div><strong>Format:</strong> {videoInfo.format}</div>
            <div><strong>Size:</strong> {(videoInfo.size / (1024 * 1024)).toFixed(1)} MB</div>
            <div><strong>Video Streams:</strong> {videoInfo.video_streams}</div>
            <div><strong>Audio Streams:</strong> {videoInfo.audio_streams}</div>
            <div><strong>Subtitle Streams:</strong> {videoInfo.subtitle_streams}</div>
          </div>

          {videoUrl && (
            <div>
              <video
                ref={videoRef}
                src={videoUrl}
                controls
                onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
                style={{ width: '100%', maxHeight: '400px', borderRadius: '5px' }}
              />
              <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
                Current time: {formatTime(currentTime)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Split Configuration */}
      {jobId && !processing && (
        <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '10px' }}>
          <h3 style={{ marginBottom: '15px' }}>Split Configuration</h3>
          
          {/* Split Method */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Split Method:</label>
            <div>
              <label style={{ marginRight: '20px', cursor: 'pointer' }}>
                <input
                  type="radio"
                  value="time"
                  checked={splitMethod === 'time'}
                  onChange={(e) => setSplitMethod(e.target.value)}
                  style={{ marginRight: '5px' }}
                />
                Time-based
              </label>
              <label style={{ cursor: 'pointer' }}>
                <input
                  type="radio"
                  value="intervals"
                  checked={splitMethod === 'intervals'}
                  onChange={(e) => setSplitMethod(e.target.value)}
                  style={{ marginRight: '5px' }}
                />
                Equal intervals
              </label>
            </div>
          </div>

          {/* Time-based configuration */}
          {splitMethod === 'time' && (
            <div style={{ marginBottom: '20px' }}>
              <div style={{ marginBottom: '10px' }}>
                <button
                  onClick={addCurrentTime}
                  disabled={!videoRef.current}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginRight: '10px'
                  }}
                >
                  Add Current Time ({formatTime(currentTime)})
                </button>
              </div>
              
              {timePoints.length > 0 && (
                <div>
                  <strong>Split Points:</strong>
                  <div style={{ marginTop: '5px' }}>
                    {timePoints.map((time, index) => (
                      <span
                        key={index}
                        style={{
                          display: 'inline-block',
                          margin: '2px',
                          padding: '4px 8px',
                          backgroundColor: '#007bff',
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      >
                        {formatTime(time)}
                        <button
                          onClick={() => removeTimePoint(time)}
                          style={{
                            marginLeft: '5px',
                            background: 'none',
                            border: 'none',
                            color: 'white',
                            cursor: 'pointer'
                          }}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Interval configuration */}
          {splitMethod === 'intervals' && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Interval Duration (seconds):
              </label>
              <input
                type="number"
                value={intervalDuration}
                onChange={(e) => setIntervalDuration(parseInt(e.target.value))}
                min="30"
                max="3600"
                style={{
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  width: '120px'
                }}
              />
            </div>
          )}

          {/* Output Settings */}
          <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
            <h4 style={{ marginBottom: '10px' }}>Output Settings</h4>
            
            <div style={{ marginBottom: '10px' }}>
              <label style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={preserveQuality}
                  onChange={(e) => setPreserveQuality(e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Preserve Original Quality
              </label>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Output Format:</label>
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value)}
                style={{ padding: '5px', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value="mp4">MP4</option>
                <option value="mkv">MKV</option>
                <option value="avi">AVI</option>
                <option value="mov">MOV</option>
                <option value="webm">WebM</option>
              </select>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <label style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={forceKeyframes}
                  onChange={(e) => setForceKeyframes(e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                Force Keyframe Insertion
              </label>
              {forceKeyframes && (
                <div style={{ marginLeft: '25px', marginTop: '5px' }}>
                  <label>Keyframe Interval (seconds): </label>
                  <input
                    type="number"
                    value={keyframeInterval}
                    onChange={(e) => setKeyframeInterval(parseInt(e.target.value))}
                    min="1"
                    max="10"
                    style={{ width: '60px', marginLeft: '5px' }}
                  />
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '5px' }}>Subtitle Sync Offset (seconds):</label>
              <input
                type="number"
                value={subtitleOffset}
                onChange={(e) => setSubtitleOffset(parseFloat(e.target.value))}
                step="0.1"
                style={{
                  padding: '5px',
                  borderRadius: '4px',
                  border: '1px solid #ccc',
                  width: '80px'
                }}
              />
            </div>
          </div>

          <button
            onClick={startSplitting}
            disabled={splitMethod === 'time' && timePoints.length === 0}
            style={{
              padding: '12px 30px',
              fontSize: '16px',
              backgroundColor: (splitMethod === 'time' && timePoints.length === 0) ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: (splitMethod === 'time' && timePoints.length === 0) ? 'not-allowed' : 'pointer'
            }}
          >
            Start Splitting
          </button>
        </div>
      )}

      {/* Processing Progress */}
      {processing && (
        <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #007bff', borderRadius: '10px' }}>
          <h3 style={{ marginBottom: '15px', color: '#007bff' }}>Processing Video...</h3>
          <div style={{ backgroundColor: '#e9ecef', borderRadius: '10px', height: '20px', marginBottom: '10px' }}>
            <div
              style={{
                backgroundColor: '#007bff',
                height: '100%',
                borderRadius: '10px',
                width: `${progress}%`,
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <div style={{ textAlign: 'center', fontSize: '16px' }}>
            {progress}% Complete
          </div>
        </div>
      )}

      {/* Split Results */}
      {splitResults && splitResults.length > 0 && (
        <div style={{ padding: '20px', border: '1px solid #28a745', borderRadius: '10px' }}>
          <h3 style={{ marginBottom: '15px', color: '#28a745' }}>✓ Split Complete!</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
            {splitResults.map((result, index) => (
              <div
                key={index}
                style={{
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: '#f8f9fa'
                }}
              >
                <h4 style={{ margin: '0 0 10px 0' }}>Segment {index + 1}</h4>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  <strong>File:</strong> {result.filename}
                </p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  <strong>Duration:</strong> {formatTime(result.duration || 0)}
                </p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  <strong>Size:</strong> {((result.size || 0) / (1024 * 1024)).toFixed(1)} MB
                </p>
                <button
                  onClick={() => downloadFile(result.filename)}
                  style={{
                    marginTop: '10px',
                    padding: '8px 16px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    width: '100%'
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
  );
};

export default VideoSplitter;