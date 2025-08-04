<<<<<<< HEAD
import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './components/Login';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';

// Conditionally import and configure AWS Amplify only if available
let Amplify = null;
try {
  const amplifyModule = require('aws-amplify');
  Amplify = amplifyModule.Amplify;
  
  // AWS Configuration - only configure if Amplify is available
  const awsConfig = {
    API: {
      endpoints: [
        {
          name: 'videoapi',
          endpoint: process.env.REACT_APP_API_GATEWAY_URL || 'https://your-api-gateway-url/prod',
          region: 'us-east-1'
        }
      ]
    },
    Storage: {
      AWSS3: {
        bucket: process.env.REACT_APP_S3_BUCKET || 'videosplitter-storage-1751560247',
        region: 'us-east-1'
      }
    }
  };

  Amplify.configure(awsConfig);
  console.log('✅ AWS Amplify configured successfully');
} catch (error) {
  console.log('⚠️ AWS Amplify not available - running in local mode');
}

// Main App Component with Authentication
function AppContent() {
  const { isAuthenticated, isLoading, getAuthHeader } = useAuth();
  
  // Use API Gateway URL if available, otherwise fallback to current backend
  const BACKEND_URL = process.env.REACT_APP_API_GATEWAY_URL || process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [splitConfig, setSplitConfig] = useState({
    method: 'time_based',
    time_points: [],
    interval_duration: 300, // 5 minutes
    preserve_quality: true,
    output_format: 'mp4',
    subtitle_sync_offset: 0,
    force_keyframes: true,
    keyframe_interval: 2.0
  });
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [splits, setSplits] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [manualTimeInput, setManualTimeInput] = useState('');
  const [isAWSMode, setIsAWSMode] = useState(false);
  
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

  // Detect if we're running in AWS mode
  useEffect(() => {
    const awsMode = process.env.REACT_APP_API_GATEWAY_URL || process.env.REACT_APP_S3_BUCKET;
    setIsAWSMode(!!awsMode);
    
    if (awsMode) {
      console.log('🚀 Running in AWS Amplify mode');
      console.log('API Gateway:', process.env.REACT_APP_API_GATEWAY_URL);
      console.log('S3 Bucket:', process.env.REACT_APP_S3_BUCKET);
    } else {
      console.log('🖥️ Running in local development mode');
    }
  }, []);

  // Clear any stale state on component mount
  useEffect(() => {
    setJobId(null);
    setVideoInfo(null);
    setSplits([]);
    setProgress(0);
    setSelectedFile(null);
  }, []);

  // Set video source when jobId changes
  useEffect(() => {
    if (jobId && !jobId.includes('mock')) {
      const setVideoSource = async () => {
        if (videoRef.current) {
          try {
            const timestamp = Date.now();
            const response = await fetch(`${API}/video-stream/${jobId}?t=${timestamp}`);
            const data = await response.json();
            
            if (data.stream_url) {
              console.log('Setting video src to:', data.stream_url);
              videoRef.current.src = data.stream_url;
              videoRef.current.load();
            } else {
              console.error('No stream URL received:', data);
            }
          } catch (error) {
            console.error('Error fetching video stream:', error);
          }
        } else {
          setTimeout(setVideoSource, 100);
        }
      };
      
      setVideoSource();
    }
  }, [jobId, API]);

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 text-center border border-white/20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Video Splitter Pro...</p>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  // Main authenticated app content
  return <AuthenticatedApp 
    BACKEND_URL={BACKEND_URL}
    API={API}
    isAWSMode={isAWSMode}
    getAuthHeader={getAuthHeader}
  />;
}

// Separate component for authenticated app to avoid hooks issues
function AuthenticatedApp({ BACKEND_URL, API, isAWSMode, getAuthHeader }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [splitConfig, setSplitConfig] = useState({
    method: 'time_based',
    time_points: [],
    interval_duration: 300, // 5 minutes
    preserve_quality: true,
    output_format: 'mp4',
    subtitle_sync_offset: 0,
    force_keyframes: true,
    keyframe_interval: 2.0
  });
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [splits, setSplits] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [manualTimeInput, setManualTimeInput] = useState('');
  
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

  // Clear any stale state on component mount
  useEffect(() => {
    setJobId(null);
    setVideoInfo(null);
    setSplits([]);
    setProgress(0);
    setSelectedFile(null);
  }, []);

  // Set video source when jobId changes
  useEffect(() => {
    if (jobId && !jobId.includes('mock')) {
      const setVideoSource = () => {
        if (videoRef.current) {
          const timestamp = Date.now();
          const videoUrl = `${API}/video-stream/${jobId}?t=${timestamp}`;
          console.log('Setting video src to:', videoUrl);
          videoRef.current.src = videoUrl;
          videoRef.current.load();
        } else {
          setTimeout(setVideoSource, 100);
        }
      };
      
      setVideoSource();
    }
  }, [jobId, API]);

  // Format file size for display
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // Format time for display
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Parse time input (MM:SS or HH:MM:SS)
  const parseTime = (timeStr) => {
    const parts = timeStr.split(':').map(p => parseInt(p));
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    return 0;
  };

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setJobId(null);
      setVideoInfo(null);
      setSplits([]);
      setProgress(0);
      setSplitConfig({...splitConfig, time_points: []});
      
      if (videoRef.current) {
        videoRef.current.src = '';
        videoRef.current.load();
      }
    }
  };

  // Upload video (AWS mode vs Local mode) - Now with authentication
  const uploadVideo = async () => {
    if (!selectedFile) return;

    try {
      setUploadProgress(0);
      
      if (isAWSMode) {
        // AWS mode: Use presigned URL upload with authentication
        console.log('🚀 Uploading to AWS S3...');
        
        // Get presigned URL from API Gateway with auth headers
        const response = await axios.post(`${API}/upload-video`, {
          filename: selectedFile.name,
          fileType: selectedFile.type,
          fileSize: selectedFile.size
        }, {
          headers: getAuthHeader()
        });
        
        const { upload_url, upload_post, job_id, content_type } = response.data;
        
        // Try presigned POST first (more reliable for browsers)
        if (upload_post) {
          const formData = new FormData();
          
          // Add all the required fields from presigned POST
          Object.entries(upload_post.fields).forEach(([key, value]) => {
            formData.append(key, value);
          });
          
          // Add the file last
          formData.append('file', selectedFile);
          
          await axios.post(upload_post.url, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(percentCompleted);
            }
          });
        } else {
          // Fallback to presigned PUT
          await axios.put(upload_url, selectedFile, {
            headers: { 
              'Content-Type': content_type || selectedFile.type,
              'x-amz-acl': 'private'
            },
            onUploadProgress: (progressEvent) => {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(percentCompleted);
            }
          });
        }
        
        setJobId(job_id);
        
        // Fetch actual video metadata from the API
        try {
          const infoResponse = await axios.get(`${API}/video-info/${job_id}`);
          const { metadata } = infoResponse.data;
          setVideoInfo(metadata);
        } catch (infoError) {
          console.warn('Could not fetch video metadata:', infoError);
          // Fallback to basic info
          setVideoInfo({
            duration: 0,
            format: selectedFile.name.split('.').pop() || 'unknown',
            size: selectedFile.size,
            video_streams: [],
            audio_streams: [],
            subtitle_streams: [],
            chapters: []
          });
        }
        
      } else {
        // Local mode: Direct upload to FastAPI with authentication
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await axios.post(`${API}/upload-video`, formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            ...getAuthHeader()
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        });

        setJobId(response.data.job_id);
        setVideoInfo(response.data.video_info);
      }
      
    } catch (error) {
      console.error('Upload failed:', error);
      let errorMessage = 'Upload failed';
      
      if (error.response?.status === 401) {
        errorMessage = 'Authentication required. Please log in again.';
      } else if (error.response?.status === 403) {
        errorMessage = 'Access denied. You do not have permission to upload files.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(errorMessage);
    }
  };

  // Add split point
  const addSplitPoint = (time = null) => {
    const splitTime = time !== null ? time : currentTime;
    if (splitConfig.method === 'time_based') {
      const newPoints = [...splitConfig.time_points, splitTime].sort((a, b) => a - b);
      setSplitConfig({...splitConfig, time_points: newPoints});
    }
  };

  // Add manual time point
  const addManualTime = () => {
    if (manualTimeInput) {
      const time = parseTime(manualTimeInput);
      if (time > 0 && videoInfo && time < videoInfo.duration) {
        addSplitPoint(time);
        setManualTimeInput('');
      } else {
        alert('Invalid time format or time exceeds video duration');
      }
    }
  };

  // Remove split point
  const removeSplitPoint = (index) => {
    const newPoints = splitConfig.time_points.filter((_, i) => i !== index);
    setSplitConfig({...splitConfig, time_points: newPoints});
  };

  // Start splitting - Now with authentication
  const startSplitting = async () => {
    if (!jobId) return;

    try {
      setProcessing(true);
      setProgress(0);
      
      await axios.post(`${API}/split-video/${jobId}`, splitConfig, {
        headers: getAuthHeader()
      });
      
      // Poll for progress
      const pollProgress = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/job-status/${jobId}`, {
            headers: getAuthHeader()
          });
          const job = response.data;
          
          setProgress(job.progress);
          
          if (job.status === 'completed') {
            setSplits(job.splits);
            setProcessing(false);
            clearInterval(pollProgress);
          } else if (job.status === 'failed') {
            alert('Processing failed: ' + job.error_message);
            setProcessing(false);
            clearInterval(pollProgress);
          }
        } catch (error) {
          console.error('Progress poll error:', error);
          if (error.response?.status === 401 || error.response?.status === 403) {
            alert('Authentication expired. Please log in again.');
            setProcessing(false);
            clearInterval(pollProgress);
          }
        }
      }, 2000);
      
    } catch (error) {
      console.error('Split failed:', error);
      let errorMessage = 'Split failed';
      
      if (error.response?.status === 401) {
        errorMessage = 'Authentication required. Please log in again.';
      } else if (error.response?.status === 403) {
        errorMessage = 'Access denied. You do not have permission to process videos.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(errorMessage);
      setProcessing(false);
    }
  };

  // Download split file - Now with authentication
  const downloadSplit = (filename) => {
    const authHeader = getAuthHeader();
    const downloadUrl = `${API}/download/${jobId}/${filename}`;
    
    // Create a temporary link with auth headers (for newer browsers)
    if (authHeader.Authorization) {
      fetch(downloadUrl, {
        headers: authHeader
      })
      .then(response => response.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      })
      .catch(error => {
        console.error('Download failed:', error);
        alert('Download failed. Please try again or check your authentication.');
      });
    } else {
      // Fallback for direct link (if no auth needed)
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Update current time from video
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        <div className="container mx-auto px-4 py-8">
          {/* Header with User Info */}
          <Header isAWSMode={isAWSMode} />

          {/* Upload Section */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6">Upload Video</h2>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*,.mkv,.mp4,.avi,.mov,.wmv,.flv,.webm"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <div className="space-y-4">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105"
              >
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Choose Video File'}
              </button>
              
              {selectedFile && !jobId && (
                <button
                  onClick={uploadVideo}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-3 px-6 rounded-xl transition-all duration-300"
                >
                  {isAWSMode ? 'Upload to AWS S3' : 'Upload Video'}
                </button>
              )}
              
              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full transition-all duration-300"
                    style={{width: `${uploadProgress}%`}}
                  ></div>
                </div>
              )}
            </div>
          </div>

          {/* Video Preview */}
          {(videoInfo || jobId) && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Video Preview</h2>
              
              <div className="grid lg:grid-cols-2 gap-8">
                <div>
                  <video
                    ref={videoRef}
                    controls
                    onTimeUpdate={handleTimeUpdate}
                    className="w-full rounded-xl shadow-2xl"
                    preload="metadata"
                    crossOrigin="anonymous"
                  >
                    Your browser does not support the video tag.
                  </video>
                  
                  <div className="mt-4 text-white">
                    <p><strong>Current Time:</strong> {formatTime(currentTime)}</p>
                  </div>
                </div>
                
                {videoInfo && (
                  <div className="text-white space-y-4">
                    <h3 className="text-xl font-bold">Video Information</h3>
                    <div className="bg-black/30 rounded-lg p-4 space-y-2">
                      <p><strong>Duration:</strong> {formatTime(videoInfo.duration)}</p>
                      <p><strong>Format:</strong> {videoInfo.format}</p>
                      <p><strong>Size:</strong> {formatFileSize(videoInfo.size)}</p>
                      <p><strong>Video Streams:</strong> {videoInfo.video_streams.length}</p>
                      <p><strong>Audio Streams:</strong> {videoInfo.audio_streams.length}</p>
                      <p><strong>Subtitle Streams:</strong> {videoInfo.subtitle_streams.length}</p>
                      {videoInfo.chapters.length > 0 && (
                        <p><strong>Chapters:</strong> {videoInfo.chapters.length}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Split Configuration */}
          {videoInfo && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Split Configuration</h2>
              
              <div className="grid lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                  {/* Split Method */}
                  <div>
                    <label className="block text-white font-bold mb-3">Split Method</label>
                    <select
                      value={splitConfig.method}
                      onChange={(e) => setSplitConfig({...splitConfig, method: e.target.value})}
                      className="w-full bg-black/30 text-white rounded-lg p-3 border border-white/20"
                    >
                      <option value="time_based">Time-based (Manual Points)</option>
                      <option value="intervals">Equal Intervals</option>
                      <option value="chapters">Chapter-based</option>
                    </select>
                  </div>

                  {/* Time-based Configuration */}
                  {splitConfig.method === 'time_based' && (
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => addSplitPoint()}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                        >
                          Add Current Time ({formatTime(currentTime)})
                        </button>
                      </div>
                      
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="MM:SS or HH:MM:SS"
                          value={manualTimeInput}
                          onChange={(e) => setManualTimeInput(e.target.value)}
                          className="flex-1 bg-black/30 text-white rounded-lg p-2 border border-white/20"
                        />
                        <button
                          onClick={addManualTime}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                        >
                          Add
                        </button>
                      </div>
                      
                      <div>
                        <h4 className="text-white font-bold mb-2">Split Points:</h4>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {splitConfig.time_points.map((time, index) => (
                            <div key={index} className="flex justify-between items-center bg-black/30 rounded p-2">
                              <span className="text-white">{formatTime(time)}</span>
                              <button
                                onClick={() => removeSplitPoint(index)}
                                className="text-red-400 hover:text-red-300"
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Interval Configuration */}
                  {splitConfig.method === 'intervals' && (
                    <div>
                      <label className="block text-white font-bold mb-2">Interval Duration (seconds)</label>
                      <input
                        type="number"
                        value={splitConfig.interval_duration}
                        onChange={(e) => setSplitConfig({...splitConfig, interval_duration: parseFloat(e.target.value)})}
                        className="w-full bg-black/30 text-white rounded-lg p-3 border border-white/20"
                      />
                    </div>
                  )}

                  {/* Start Processing */}
                  <button
                    onClick={startSplitting}
                    disabled={processing || (splitConfig.method === 'time_based' && splitConfig.time_points.length === 0)}
                    className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-6 rounded-xl transition-all duration-300 disabled:cursor-not-allowed"
                  >
                    {processing ? 'Processing...' : 'Start Splitting'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Processing Progress */}
          {processing && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Processing Progress</h2>
              <div className="w-full bg-gray-700 rounded-full h-4 mb-4">
                <div 
                  className="bg-gradient-to-r from-orange-500 to-red-500 h-4 rounded-full transition-all duration-300"
                  style={{width: `${progress}%`}}
                ></div>
              </div>
              <p className="text-white text-center">{progress.toFixed(1)}% Complete</p>
            </div>
          )}

          {/* Results */}
          {splits.length > 0 && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6">Split Results</h2>
              <div className="grid gap-4">
                {splits.map((split, index) => (
                  <div key={index} className="flex justify-between items-center bg-black/30 rounded-lg p-4">
                    <span className="text-white font-medium">Part {index + 1}: {split.file}</span>
                    <button
                      onClick={() => downloadSplit(split.file)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
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
    </ProtectedRoute>
  );
}

// Main App with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
=======
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import EmailVerification from './components/auth/EmailVerification';
import VideoSplitter from './components/VideoSplitter';
import './App.css';

// Navigation Header Component
function NavigationHeader() {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) return null;

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              Tad's Video Splitter
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              Welcome, {user?.firstName}!
            </span>
            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <NavigationHeader />
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            <Route path="/verify-email" element={<EmailVerification />} />
            
            {/* Protected routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <VideoSplitter />
                </ProtectedRoute>
              } 
            />
            
            {/* Redirect any other path to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
>>>>>>> 3c1a9381a2bbf306e9e3761b31de97962165c8fc
    </AuthProvider>
  );
}

export default App;