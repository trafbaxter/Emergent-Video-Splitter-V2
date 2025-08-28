import React, { useState, useRef, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const VideoMerger = () => {
  const [mergeJobId, setMergeJobId] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [mergedResult, setMergedResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);
  
  // Merge configuration
  const [outputFormat, setOutputFormat] = useState('mp4');
  const [preserveQuality, setPreserveQuality] = useState(true);
  const [audioHandling, setAudioHandling] = useState('concat');
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  
  const fileInputRef = useRef();

  // Format time helper
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Create new merge job
  const createMergeJob = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/create-merge-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMergeJobId(data.job_id);
        return data.job_id;
      } else {
        throw new Error('Failed to create merge job');
      }
    } catch (error) {
      console.error('Error creating merge job:', error);
      alert('Failed to create merge job');
      return null;
    }
  };

  // Handle file selection
  const handleFileInputChange = (event) => {
    const files = Array.from(event.target.files);
    handleFiles(files);
  };

  // Handle drag and drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  // Process selected files
  const handleFiles = async (files) => {
    if (files.length === 0) return;

    // Filter video files
    const videoFiles = files.filter(file => 
      file.type.startsWith('video/') || 
      file.name.toLowerCase().match(/\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)$/i)
    );

    if (videoFiles.length === 0) {
      alert('Please select valid video files');
      return;
    }

    setUploading(true);

    try {
      // Create merge job if not exists
      let jobId = mergeJobId;
      if (!jobId) {
        jobId = await createMergeJob();
        if (!jobId) return;
      }

      // Upload each file
      for (const file of videoFiles) {
        await uploadFileToMergeJob(jobId, file);
      }

      // Refresh job status
      await refreshJobStatus(jobId);

    } catch (error) {
      console.error('Error handling files:', error);
      alert('Error uploading files: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  // Upload file to merge job
  const uploadFileToMergeJob = async (jobId, file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/upload-merge-video/${jobId}`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to upload ${file.name}: ${error}`);
    }

    return response.json();
  };

  // Refresh job status
  const refreshJobStatus = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE}/api/merge-job-status/${jobId}`);
      if (response.ok) {
        const job = await response.json();
        setUploadedFiles(job.input_files || []);
        setProgress(job.progress || 0);
        
        if (job.status === 'completed') {
          setMergedResult(job.merged_file);
          setProcessing(false);
        } else if (job.status === 'processing') {
          setProcessing(true);
        }
      }
    } catch (error) {
      console.error('Error refreshing job status:', error);
    }
  };

  // Remove file from merge
  const removeFile = async (filename) => {
    if (!mergeJobId) return;

    try {
      const response = await fetch(`${API_BASE}/api/remove-merge-file/${mergeJobId}/${filename}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await refreshJobStatus(mergeJobId);
      } else {
        alert('Failed to remove file');
      }
    } catch (error) {
      console.error('Error removing file:', error);
      alert('Error removing file');
    }
  };

  // Drag and drop reordering
  const handleDragStart = useCallback((e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragOverItem = useCallback((e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDropItem = useCallback(async (e, dropIndex) => {
    e.preventDefault();
    
    if (draggedItem === null || draggedItem === dropIndex) return;

    // Reorder files locally first for immediate feedback
    const reorderedFiles = [...uploadedFiles];
    const [draggedFile] = reorderedFiles.splice(draggedItem, 1);
    reorderedFiles.splice(dropIndex, 0, draggedFile);
    
    setUploadedFiles(reorderedFiles);
    setDraggedItem(null);

    // Update order on server
    try {
      const fileOrder = reorderedFiles.map(f => f.filename);
      const response = await fetch(`${API_BASE}/api/reorder-merge-files/${mergeJobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(fileOrder)
      });

      if (!response.ok) {
        // Revert on error
        await refreshJobStatus(mergeJobId);
      }
    } catch (error) {
      console.error('Error reordering files:', error);
      await refreshJobStatus(mergeJobId);
    }
  }, [draggedItem, uploadedFiles, mergeJobId]);

  // Start merging process
  const startMerging = async () => {
    if (!mergeJobId || uploadedFiles.length < 2) return;

    setProcessing(true);
    setProgress(0);

    try {
      const mergeConfig = {
        output_format: outputFormat,
        preserve_quality: preserveQuality,
        audio_handling: audioHandling,
        include_subtitles: includeSubtitles,
        video_file_order: uploadedFiles.map(f => f.filename)
      };

      const response = await fetch(`${API_BASE}/api/start-merge/${mergeJobId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mergeConfig)
      });

      if (response.ok) {
        // Start polling for progress
        pollMergeProgress();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to start merge');
      }
    } catch (error) {
      console.error('Error starting merge:', error);
      alert('Failed to start merge: ' + error.message);
      setProcessing(false);
    }
  };

  // Poll merge progress
  const pollMergeProgress = () => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/merge-job-status/${mergeJobId}`);
        if (response.ok) {
          const job = await response.json();
          setProgress(job.progress || 0);

          if (job.status === 'completed') {
            setMergedResult(job.merged_file);
            setProcessing(false);
          } else if (job.status === 'failed') {
            alert('Merge failed: ' + (job.error_message || 'Unknown error'));
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

  // Download merged video
  const downloadMergedVideo = async () => {
    if (!mergeJobId) return;

    try {
      window.open(`${API_BASE}/api/download-merged/${mergeJobId}`, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('Download failed');
    }
  };

  // Reset merger
  const resetMerger = () => {
    setMergeJobId(null);
    setUploadedFiles([]);
    setMergedResult(null);
    setProgress(0);
    setProcessing(false);
  };

  // Styles
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
    <div className="video-merger" style={{ 
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
            Video Merger Pro
          </h1>
          <p style={{ 
            color: 'rgba(255,255,255,0.8)', 
            fontSize: '1.2rem', 
            margin: 0,
            fontWeight: '300'
          }}>
            Combine multiple videos into one seamless file
          </p>
        </div>

        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
            Select Videos to Merge
          </h2>
          
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
              accept="video/*,.mp4,.avi,.mov,.mkv,.webm,.flv,.wmv,.m4v"
              onChange={handleFileInputChange}
              ref={fileInputRef}
              multiple
              style={{ display: 'none' }}
            />
            
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🎬</div>
            <h3 style={{ color: 'white', fontSize: '1.3rem', margin: '0 0 10px 0' }}>
              Select Multiple Video Files
            </h3>
            <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0 }}>
              Drag & drop or click to browse<br/>
              <small>Select 2 or more videos to merge together</small>
            </p>
            
            {uploading && (
              <div style={{ marginTop: '20px', color: '#4ade80', fontSize: '16px' }}>
                Uploading files...
              </div>
            )}
          </div>
        </div>

        {/* File List */}
        {uploadedFiles.length > 0 && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              Files to Merge ({uploadedFiles.length})
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '20px', fontSize: '14px' }}>
              Drag and drop to reorder • Files will be merged in this order
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {uploadedFiles.map((file, index) => (
                <div
                  key={file.filename}
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragOver={(e) => handleDragOverItem(e, index)}
                  onDrop={(e) => handleDropItem(e, index)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '15px',
                    padding: '20px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'move',
                    transition: 'all 0.3s ease',
                    opacity: draggedItem === index ? 0.5 : 1
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '18px' }}>
                      ⋮⋮
                    </div>
                    <div style={{ color: 'white', fontSize: '1.5rem' }}>
                      {index + 1}
                    </div>
                    <div>
                      <div style={{ color: 'white', fontSize: '16px', fontWeight: '600' }}>
                        {file.filename}
                      </div>
                      <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
                        {formatTime(file.video_info?.duration || 0)} • {(file.size / (1024 * 1024)).toFixed(1)} MB
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(file.filename);
                    }}
                    style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      borderRadius: '8px',
                      padding: '8px 12px',
                      color: '#ef4444',
                      cursor: 'pointer',
                      fontSize: '14px'
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
        {uploadedFiles.length >= 2 && !processing && !mergedResult && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '30px', fontWeight: '600' }}>
              Merge Settings
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' }}>
              
              {/* Left Column - Output Settings */}
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Output Settings</h3>
                
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
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px', 
                    color: 'rgba(255,255,255,0.9)',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={includeSubtitles}
                      onChange={(e) => setIncludeSubtitles(e.target.checked)}
                      style={{ transform: 'scale(1.2)' }}
                    />
                    Include subtitles
                  </label>
                </div>
              </div>

              {/* Right Column - Audio Settings */}
              <div>
                <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px' }}>Audio Handling</h3>
                
                <div style={{ marginBottom: '20px' }}>
                  <select
                    value={audioHandling}
                    onChange={(e) => setAudioHandling(e.target.value)}
                    style={{
                      ...selectStyle,
                      height: '45px'
                    }}
                  >
                    <option value="concat" style={{backgroundColor: '#2d3748', color: 'white'}}>
                      Concatenate (Keep all audio)
                    </option>
                    <option value="first_only" style={{backgroundColor: '#2d3748', color: 'white'}}>
                      First video audio only
                    </option>
                    <option value="mix" style={{backgroundColor: '#2d3748', color: 'white'}}>
                      Mix all audio tracks
                    </option>
                  </select>
                </div>

                <div style={{ 
                  background: 'rgba(255,255,255,0.05)', 
                  borderRadius: '10px', 
                  padding: '15px',
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: '14px'
                }}>
                  <strong>Audio Options:</strong>
                  <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
                    <li><strong>Concatenate:</strong> Join audio sequentially (recommended)</li>
                    <li><strong>First only:</strong> Use audio from first video throughout</li>
                    <li><strong>Mix:</strong> Blend audio tracks together (experimental)</li>
                  </ul>
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button
                onClick={startMerging}
                style={{
                  ...buttonStyle,
                  background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
                  fontSize: '18px',
                  padding: '15px 40px'
                }}
              >
                Start Merging Videos
              </button>
            </div>
          </div>
        )}

        {/* Processing Progress */}
        {processing && (
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
              {progress}% Complete
            </div>
          </div>
        )}

        {/* Merge Result */}
        {mergedResult && (
          <div style={cardStyle}>
            <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
              ✅ Merge Complete!
            </h2>
            
            <div style={{
              background: 'rgba(74, 222, 128, 0.2)',
              borderRadius: '15px',
              padding: '25px',
              textAlign: 'center'
            }}>
              <div style={{ color: 'white', fontSize: '18px', marginBottom: '15px', fontWeight: '600' }}>
                {mergedResult.filename}
              </div>
              
              <div style={{ color: 'rgba(255,255,255,0.8)', marginBottom: '20px' }}>
                Duration: {formatTime(mergedResult.duration || 0)} • 
                Size: {((mergedResult.size || 0) / (1024 * 1024)).toFixed(1)} MB
              </div>
              
              <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
                <button
                  onClick={downloadMergedVideo}
                  style={{
                    ...buttonStyle,
                    background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                  }}
                >
                  Download Merged Video
                </button>
                
                <button
                  onClick={resetMerger}
                  style={{
                    ...buttonStyle,
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.3)'
                  }}
                >
                  Merge New Videos
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tips */}
        {uploadedFiles.length === 0 && (
          <div style={{
            ...cardStyle,
            background: 'rgba(255,255,255,0.05)'
          }}>
            <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '15px', fontWeight: '600' }}>
              💡 Tips for Best Results
            </h3>
            
            <ul style={{ color: 'rgba(255,255,255,0.8)', lineHeight: '1.6', paddingLeft: '20px' }}>
              <li>Use videos with similar resolutions and frame rates for best quality</li>
              <li>Videos will be merged in the order you arrange them</li>
              <li>Drag and drop to reorder videos before merging</li>
              <li>Choose "Preserve quality" for fastest processing without re-encoding</li>
              <li>Select appropriate audio handling based on your content</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoMerger;