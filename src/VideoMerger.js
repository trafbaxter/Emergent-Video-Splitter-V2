import React, { useState, useRef, useEffect } from 'react';
import './VideoMerger.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const VideoMerger = () => {
  const [mergeJobId, setMergeJobId] = useState(null);
  const [uploadedVideos, setUploadedVideos] = useState([]);
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [merging, setMerging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [mergeResult, setMergeResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Merge configuration
  const [mergeConfig, setMergeConfig] = useState({
    output_format: 'mp4',
    quality_mode: 'auto',
    custom_quality: {
      width: 1920,
      height: 1080,
      bitrate: '2M',
      fps: 30
    },
    preserve_audio: true,
    transition_duration: 0.0
  });
  
  const fileInputRef = useRef(null);
  
  useEffect(() => {
    // Create merge job on component mount
    createMergeJob();
  }, []);
  
  useEffect(() => {
    let pollInterval;
    
    if (merging && mergeJobId) {
      pollInterval = setInterval(() => {
        pollMergeStatus();
      }, 2000);
    }
    
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [merging, mergeJobId]);
  
  const createMergeJob = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/merge/create-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMergeJobId(data.job_id);
      } else {
        throw new Error('Failed to create merge job');
      }
    } catch (err) {
      setError('Failed to initialize merge job: ' + err.message);
    }
  };
  
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    uploadVideos(files);
  };
  
  const handleDrop = (event) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    const videoFiles = files.filter(file => 
      file.type.startsWith('video/') || 
      /\.(mp4|mkv|avi|mov|wmv|flv|webm)$/i.test(file.name)
    );
    
    if (videoFiles.length > 0) {
      uploadVideos(videoFiles);
    }
  };
  
  const handleDragOver = (event) => {
    event.preventDefault();
  };
  
  const uploadVideos = async (files) => {
    if (!mergeJobId) {
      setError('No merge job available. Please refresh the page.');
      return;
    }
    
    setUploading(true);
    setError(null);
    
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${BACKEND_URL}/api/merge/upload-video/${mergeJobId}`, {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          const videoData = await response.json();
          setUploadedVideos(prev => [...prev, {
            ...videoData,
            file: file,
            preview: URL.createObjectURL(file)
          }]);
        } else {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload failed');
        }
      }
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };
  
  const handleDragStart = (index) => {
    setDraggedIndex(index);
  };
  
  const handleDragOverVideo = (event, index) => {
    event.preventDefault();
    setDragOverIndex(index);
  };
  
  const handleDragLeave = () => {
    setDragOverIndex(null);
  };
  
  const handleDrop2 = async (event, dropIndex) => {
    event.preventDefault();
    setDragOverIndex(null);
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null);
      return;
    }
    
    // Reorder videos locally
    const newVideos = [...uploadedVideos];
    const draggedVideo = newVideos[draggedIndex];
    newVideos.splice(draggedIndex, 1);
    newVideos.splice(dropIndex, 0, draggedVideo);
    
    // Update order values
    const reorderedVideos = newVideos.map((video, index) => ({
      ...video,
      order: index
    }));
    
    setUploadedVideos(reorderedVideos);
    setDraggedIndex(null);
    
    // Update order on backend
    try {
      const orderData = reorderedVideos.map(video => ({
        video_id: video.video_id,
        order: video.order
      }));
      
      await fetch(`${BACKEND_URL}/api/merge/reorder-videos/${mergeJobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
      });
    } catch (err) {
      console.error('Failed to update video order:', err);
      setError('Failed to update video order');
    }
  };
  
  const removeVideo = async (videoId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/merge/remove-video/${mergeJobId}/${videoId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setUploadedVideos(prev => prev.filter(video => video.video_id !== videoId));
      } else {
        throw new Error('Failed to remove video');
      }
    } catch (err) {
      setError('Failed to remove video: ' + err.message);
    }
  };
  
  const startMerge = async () => {
    if (uploadedVideos.length < 2) {
      setError('Please upload at least 2 videos to merge');
      return;
    }
    
    setMerging(true);
    setProgress(0);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/merge/start/${mergeJobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mergeConfig)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start merge');
      }
    } catch (err) {
      setError('Failed to start merge: ' + err.message);
      setMerging(false);
    }
  };
  
  const pollMergeStatus = async () => {
    if (!mergeJobId) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/merge/status/${mergeJobId}`);
      
      if (response.ok) {
        const data = await response.json();
        setProgress(data.progress);
        
        if (data.status === 'completed') {
          setMerging(false);
          setMergeResult(data);
        } else if (data.status === 'failed') {
          setMerging(false);
          setError('Merge failed: ' + (data.error_message || 'Unknown error'));
        }
      }
    } catch (err) {
      console.error('Failed to poll merge status:', err);
    }
  };
  
  const downloadMergedVideo = async () => {
    if (!mergeResult) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/merge/download/${mergeJobId}`);
      
      if (response.ok) {
        const data = await response.json();
        window.open(data.download_url, '_blank');
      } else {
        throw new Error('Failed to get download URL');
      }
    } catch (err) {
      setError('Download failed: ' + err.message);
    }
  };
  
  const resetMerger = () => {
    setUploadedVideos([]);
    setMerging(false);
    setProgress(0);
    setMergeResult(null);
    setError(null);
    createMergeJob();
  };
  
  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
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
            🎬 Video Merger Pro
          </h1>
          <p style={{ 
            color: 'rgba(255,255,255,0.8)', 
            fontSize: '1.2rem', 
            margin: 0,
            fontWeight: '300'
          }}>
            Upload multiple videos and merge them into a single file
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div style={{
            ...cardStyle,
            backgroundColor: 'rgba(244, 67, 54, 0.2)',
            border: '1px solid rgba(244, 67, 54, 0.4)',
            marginBottom: '20px'
          }}>
            <div style={{ color: '#ff6b6b', fontSize: '16px' }}>
              ❌ {error}
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
            Upload Videos to Merge
          </h2>
          
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: '2px dashed rgba(255,255,255,0.3)',
              borderRadius: '15px',
              padding: '40px 20px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              marginBottom: '20px'
            }}
          >
            <input
              type="file"
              accept="video/*,.mp4,.avi,.mov,.mkv,.webm,.flv,.wmv"
              multiple
              onChange={handleFileSelect}
              ref={fileInputRef}
              style={{ display: 'none' }}
            />
            
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🎥</div>
            <h3 style={{ color: 'white', fontSize: '1.3rem', margin: '0 0 10px 0' }}>
              Choose Videos to Merge
            </h3>
            <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0 }}>
              Drag & drop multiple video files or click to browse<br/>
              <small>Supports: MP4, AVI, MOV, MKV, WebM, FLV, WMV</small>
            </p>
          </div>
          
          {uploading && (
            <div style={{
              textAlign: 'center',
              color: 'rgba(255,255,255,0.8)',
              fontSize: '16px'
            }}>
              Uploading videos... ⏳
            </div>
          )}
        </div>

        {/* Video List with Drag & Drop */}
        {uploadedVideos.length > 0 && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              Videos to Merge ({uploadedVideos.length})
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '20px', fontSize: '14px' }}>
              💡 Drag and drop videos to reorder them
            </p>
            
            <div style={{ display: 'grid', gap: '15px' }}>
              {uploadedVideos.map((video, index) => (
                <div
                  key={video.video_id}
                  draggable
                  onDragStart={() => handleDragStart(index)}
                  onDragOver={(e) => handleDragOverVideo(e, index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop2(e, index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '15px',
                    padding: '15px',
                    background: dragOverIndex === index ? 
                      'rgba(255,255,255,0.2)' : 
                      'rgba(255,255,255,0.05)',
                    borderRadius: '10px',
                    border: dragOverIndex === index ? 
                      '2px solid rgba(255,255,255,0.4)' :
                      '1px solid rgba(255,255,255,0.1)',
                    cursor: 'grab',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <div style={{
                    background: 'rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    color: 'white',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    minWidth: '30px',
                    textAlign: 'center'
                  }}>
                    {index + 1}
                  </div>
                  
                  <div style={{ flex: 1, color: 'white' }}>
                    <div style={{ fontWeight: '600', marginBottom: '5px' }}>
                      {video.filename}
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      color: 'rgba(255,255,255,0.7)',
                      display: 'flex',
                      gap: '15px'
                    }}>
                      <span>Duration: {formatDuration(video.duration)}</span>
                      <span>Size: {(video.size / (1024 * 1024)).toFixed(1)} MB</span>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeVideo(video.video_id);
                    }}
                    style={{
                      background: 'rgba(244, 67, 54, 0.2)',
                      border: '1px solid rgba(244, 67, 54, 0.4)',
                      borderRadius: '5px',
                      color: '#ff6b6b',
                      padding: '5px 10px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Merge Configuration */}
        {uploadedVideos.length > 1 && !merging && !mergeResult && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              Merge Settings
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Output Format</h3>
                <select
                  value={mergeConfig.output_format}
                  onChange={(e) => setMergeConfig(prev => ({...prev, output_format: e.target.value}))}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.3)',
                    background: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    fontSize: '14px'
                  }}
                >
                  <option value="mp4" style={{backgroundColor: '#2d3748', color: 'white'}}>MP4</option>
                  <option value="mkv" style={{backgroundColor: '#2d3748', color: 'white'}}>MKV</option>
                  <option value="avi" style={{backgroundColor: '#2d3748', color: 'white'}}>AVI</option>
                  <option value="mov" style={{backgroundColor: '#2d3748', color: 'white'}}>MOV</option>
                </select>
              </div>
              
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Quality Mode</h3>
                <select
                  value={mergeConfig.quality_mode}
                  onChange={(e) => setMergeConfig(prev => ({...prev, quality_mode: e.target.value}))}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.3)',
                    background: 'rgba(255,255,255,0.1)',
                    color: 'white',
                    fontSize: '14px'
                  }}
                >
                  <option value="auto" style={{backgroundColor: '#2d3748', color: 'white'}}>Auto-detect Best Settings</option>
                  <option value="highest" style={{backgroundColor: '#2d3748', color: 'white'}}>Highest Quality</option>
                  <option value="custom" style={{backgroundColor: '#2d3748', color: 'white'}}>Custom Settings</option>
                </select>
              </div>
            </div>
            
            {mergeConfig.quality_mode === 'custom' && (
              <div style={{ marginTop: '20px' }}>
                <h3 style={{ color: 'white', fontSize: '1.1rem', marginBottom: '15px' }}>Custom Quality Settings</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '15px' }}>
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Width</label>
                    <input
                      type="number"
                      value={mergeConfig.custom_quality.width}
                      onChange={(e) => setMergeConfig(prev => ({
                        ...prev,
                        custom_quality: {...prev.custom_quality, width: parseInt(e.target.value)}
                      }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        borderRadius: '5px',
                        border: '1px solid rgba(255,255,255,0.3)',
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        fontSize: '14px'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Height</label>
                    <input
                      type="number"
                      value={mergeConfig.custom_quality.height}
                      onChange={(e) => setMergeConfig(prev => ({
                        ...prev,
                        custom_quality: {...prev.custom_quality, height: parseInt(e.target.value)}
                      }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        borderRadius: '5px',
                        border: '1px solid rgba(255,255,255,0.3)',
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        fontSize: '14px'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Bitrate</label>
                    <input
                      type="text"
                      value={mergeConfig.custom_quality.bitrate}
                      onChange={(e) => setMergeConfig(prev => ({
                        ...prev,
                        custom_quality: {...prev.custom_quality, bitrate: e.target.value}
                      }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        borderRadius: '5px',
                        border: '1px solid rgba(255,255,255,0.3)',
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        fontSize: '14px'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>FPS</label>
                    <input
                      type="number"
                      value={mergeConfig.custom_quality.fps}
                      onChange={(e) => setMergeConfig(prev => ({
                        ...prev,
                        custom_quality: {...prev.custom_quality, fps: parseInt(e.target.value)}
                      }))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        borderRadius: '5px',
                        border: '1px solid rgba(255,255,255,0.3)',
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        fontSize: '14px'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
            
            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button
                onClick={startMerge}
                disabled={uploadedVideos.length < 2}
                style={{
                  ...buttonStyle,
                  background: uploadedVideos.length < 2 ? 
                    'rgba(255,255,255,0.2)' : 
                    'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)',
                  fontSize: '18px',
                  padding: '15px 40px',
                  cursor: uploadedVideos.length < 2 ? 'not-allowed' : 'pointer',
                  opacity: uploadedVideos.length < 2 ? 0.5 : 1
                }}
              >
                🎬 Start Merging Videos
              </button>
            </div>
          </div>
        )}

        {/* Merging Progress */}
        {merging && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              🎬 Merging Videos...
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
              {progress.toFixed(1)}% Complete
            </div>
            
            <div style={{
              textAlign: 'center',
              color: 'rgba(255,255,255,0.7)',
              fontSize: '14px',
              marginTop: '10px'
            }}>
              {progress < 30 ? 'Downloading videos...' :
               progress < 40 ? 'Analyzing video properties...' :
               progress < 80 ? 'Merging videos...' :
               progress < 95 ? 'Uploading merged video...' :
               'Finalizing...'}
            </div>
          </div>
        )}

        {/* Merge Result */}
        {mergeResult && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              ✅ Merge Complete!
            </h2>
            
            <div style={{
              background: 'rgba(74, 222, 128, 0.2)',
              borderRadius: '15px',
              padding: '20px',
              marginBottom: '20px'
            }}>
              <div style={{ color: 'white', fontSize: '16px', marginBottom: '10px' }}>
                <strong>Output File:</strong> {mergeResult.output_filename}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                Successfully merged {uploadedVideos.length} videos into a single file
              </div>
            </div>
            
            <div style={{ textAlign: 'center', display: 'flex', gap: '15px', justifyContent: 'center' }}>
              <button
                onClick={downloadMergedVideo}
                style={{
                  ...buttonStyle,
                  background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                }}
              >
                📥 Download Merged Video
              </button>
              
              <button
                onClick={resetMerger}
                style={{
                  ...buttonStyle,
                  background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'
                }}
              >
                🔄 Start New Merge
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoMerger;