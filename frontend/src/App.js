import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import axios from 'axios';
<<<<<<< HEAD

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
// Use external URL since we removed the proxy
const API = `${BACKEND_URL}/api`;

function App() {
=======
import { Amplify } from 'aws-amplify';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './components/Login';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';

// AWS Configuration
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

// Main App Component with Authentication
function AppContent() {
  const { isAuthenticated, isLoading, getAuthHeader } = useAuth();
  
  // Use API Gateway URL if available, otherwise fallback to current backend
  const BACKEND_URL = process.env.REACT_APP_API_GATEWAY_URL || process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

>>>>>>> conflict_050725_2128
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
<<<<<<< HEAD
    force_keyframes: true,      // Enable keyframes by default
    keyframe_interval: 2.0      // Keyframe every 2 seconds
=======
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
>>>>>>> conflict_050725_2128
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
<<<<<<< HEAD
  }, []); // Run once on mount

  // Set video source when jobId changes (only for real uploads)
  useEffect(() => {
    if (jobId && !jobId.includes('mock')) {
      // Use a timeout to ensure video element is rendered when preview section appears
=======
  }, []);

  // Set video source when jobId changes
  useEffect(() => {
    if (jobId && !jobId.includes('mock')) {
>>>>>>> conflict_050725_2128
      const setVideoSource = () => {
        if (videoRef.current) {
          const timestamp = Date.now();
          const videoUrl = `${API}/video-stream/${jobId}?t=${timestamp}`;
<<<<<<< HEAD
          console.log('useEffect: Setting video src to:', videoUrl);
          videoRef.current.src = videoUrl;
          videoRef.current.load();
          
          // Test the URL
          fetch(videoUrl, { method: 'HEAD' })
            .then(response => {
              console.log('useEffect: Video URL test response:', response.status, response.headers.get('content-type'));
            })
            .catch(error => {
              console.error('useEffect: Video URL test failed:', error);
            });
        } else {
          // Retry after a short delay if video element not ready
=======
          console.log('Setting video src to:', videoUrl);
          videoRef.current.src = videoUrl;
          videoRef.current.load();
        } else {
>>>>>>> conflict_050725_2128
          setTimeout(setVideoSource, 100);
        }
      };
      
      setVideoSource();
    }
<<<<<<< HEAD
  }, [jobId, API]); // Run when jobId changes
=======
  }, [jobId, API]);
>>>>>>> conflict_050725_2128

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
<<<<<<< HEAD
      return parts[0] * 60 + parts[1]; // MM:SS
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2]; // HH:MM:SS
=======
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
>>>>>>> conflict_050725_2128
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
<<<<<<< HEAD
      setSplitConfig({...splitConfig, time_points: []}); // Reset split points
      
      // Reset video player
=======
      setSplitConfig({...splitConfig, time_points: []});
      
>>>>>>> conflict_050725_2128
      if (videoRef.current) {
        videoRef.current.src = '';
        videoRef.current.load();
      }
    }
  };

<<<<<<< HEAD
  // Upload video
  const uploadVideo = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadProgress(0);
      const response = await axios.post(`${API}/upload-video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      setJobId(response.data.job_id);
      setVideoInfo(response.data.video_info);
      
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
=======
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
        
        const { upload_url, job_id } = response.data;
        
        // Upload directly to S3 using presigned URL
        await axios.put(upload_url, selectedFile, {
          headers: { 'Content-Type': selectedFile.type },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        });
        
        setJobId(job_id);
        setVideoInfo({
          duration: 120, // Placeholder - would be extracted by Lambda
          format: 'mp4',
          size: selectedFile.size,
          video_streams: [],
          audio_streams: [],
          subtitle_streams: [],
          chapters: []
        });
        
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
>>>>>>> conflict_050725_2128
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
<<<<<<< HEAD
      if (videoInfo && time < videoInfo.duration) {
=======
      if (time > 0 && videoInfo && time < videoInfo.duration) {
>>>>>>> conflict_050725_2128
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

<<<<<<< HEAD
  // Generate splits from chapters
  const useChapterSplits = () => {
    if (videoInfo && videoInfo.chapters && videoInfo.chapters.length > 0) {
      setSplitConfig({...splitConfig, method: 'chapters'});
    } else {
      alert('No chapters found in this video');
    }
  };

  // Start splitting
=======
  // Start splitting - Now with authentication
>>>>>>> conflict_050725_2128
  const startSplitting = async () => {
    if (!jobId) return;

    try {
      setProcessing(true);
      setProgress(0);
      
<<<<<<< HEAD
      await axios.post(`${API}/split-video/${jobId}`, splitConfig);
=======
      await axios.post(`${API}/split-video/${jobId}`, splitConfig, {
        headers: getAuthHeader()
      });
>>>>>>> conflict_050725_2128
      
      // Poll for progress
      const pollProgress = setInterval(async () => {
        try {
<<<<<<< HEAD
          const response = await axios.get(`${API}/job-status/${jobId}`);
=======
          const response = await axios.get(`${API}/job-status/${jobId}`, {
            headers: getAuthHeader()
          });
>>>>>>> conflict_050725_2128
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
<<<<<<< HEAD
=======
          if (error.response?.status === 401 || error.response?.status === 403) {
            alert('Authentication expired. Please log in again.');
            setProcessing(false);
            clearInterval(pollProgress);
          }
>>>>>>> conflict_050725_2128
        }
      }, 2000);
      
    } catch (error) {
      console.error('Split failed:', error);
<<<<<<< HEAD
      alert('Split failed: ' + (error.response?.data?.detail || error.message));
=======
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
>>>>>>> conflict_050725_2128
      setProcessing(false);
    }
  };

<<<<<<< HEAD
  // Download split file
  const downloadSplit = (filename) => {
    const downloadUrl = `${API}/download/${jobId}/${filename}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
=======
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
>>>>>>> conflict_050725_2128
  };

  // Update current time from video
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

<<<<<<< HEAD
  // Handle video load errors
  const handleVideoError = (e) => {
    console.error('Video error:', e);
    console.error('Video error details:', {
      error: e.target.error,
      code: e.target.error?.code,
      message: e.target.error?.message,
      src: e.target.src,
      networkState: e.target.networkState,
      readyState: e.target.readyState
    });
  };

  // Handle video load success
  const handleVideoLoad = () => {
    console.log('Video loaded successfully');
    console.log('Video details:', {
      src: videoRef.current?.src,
      duration: videoRef.current?.duration,
      videoWidth: videoRef.current?.videoWidth,
      videoHeight: videoRef.current?.videoHeight,
      readyState: videoRef.current?.readyState
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            Video Splitter Pro
          </h1>
          <p className="text-xl text-purple-200">
            Split videos of any size while preserving subtitles and quality
          </p>
        </div>

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
                Upload Video
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
                  onError={handleVideoError}
                  onLoadedData={handleVideoLoad}
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
                  
                  {videoInfo.chapters.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-2">Chapters:</h4>
                      <div className="bg-black/30 rounded-lg p-4 max-h-32 overflow-y-auto">
                        {videoInfo.chapters.map((chapter, index) => (
                          <div key={index} className="text-sm py-1">
                            {formatTime(chapter.start)} - {chapter.title}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
=======
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
>>>>>>> conflict_050725_2128
                </div>
              )}
            </div>
          </div>
<<<<<<< HEAD
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

                {/* Chapter Configuration */}
                {splitConfig.method === 'chapters' && (
                  <div>
                    {videoInfo.chapters.length > 0 ? (
                      <p className="text-green-400">✓ {videoInfo.chapters.length} chapters detected</p>
                    ) : (
                      <p className="text-red-400">No chapters found in this video</p>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-6">
                {/* Quality Settings */}
                <div>
                  <label className="block text-white font-bold mb-3">Quality Settings</label>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={splitConfig.preserve_quality}
                        onChange={(e) => setSplitConfig({...splitConfig, preserve_quality: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-white">Preserve original quality</span>
                    </label>
                    
                    <div>
                      <label className="block text-white mb-2">Output Format</label>
                      <select
                        value={splitConfig.output_format}
                        onChange={(e) => setSplitConfig({...splitConfig, output_format: e.target.value})}
                        className="w-full bg-black/30 text-white rounded-lg p-2 border border-white/20"
                      >
                        <option value="mp4">MP4</option>
                        <option value="mkv">MKV</option>
                        <option value="avi">AVI</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Subtitle Settings */}
                <div>
                  <label className="block text-white font-bold mb-3">Subtitle Settings</label>
                  <div>
                    <label className="block text-white mb-2">Sync Offset (seconds)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={splitConfig.subtitle_sync_offset}
                      onChange={(e) => setSplitConfig({...splitConfig, subtitle_sync_offset: parseFloat(e.target.value)})}
                      className="w-full bg-black/30 text-white rounded-lg p-2 border border-white/20"
                    />
                  </div>
                </div>

                {/* Keyframe Settings */}
                <div>
                  <label className="block text-white font-bold mb-3">Keyframe Settings</label>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={splitConfig.force_keyframes}
                        onChange={(e) => setSplitConfig({...splitConfig, force_keyframes: e.target.checked})}
                        className="mr-2"
                      />
                      <span className="text-white">Force keyframes at split points (recommended)</span>
                    </label>
                    
                    {splitConfig.force_keyframes && (
                      <div>
                        <label className="block text-white mb-2">Keyframe Interval (seconds)</label>
                        <input
                          type="number"
                          step="0.5"
                          min="1"
                          max="10"
                          value={splitConfig.keyframe_interval}
                          onChange={(e) => setSplitConfig({...splitConfig, keyframe_interval: parseFloat(e.target.value)})}
                          className="w-full bg-black/30 text-white rounded-lg p-2 border border-white/20"
                        />
                        <p className="text-sm text-gray-300 mt-1">
                          Smaller intervals = more keyframes = better seeking but larger files
                        </p>
                      </div>
                    )}
                  </div>
                </div>

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
=======

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
    </AuthProvider>
>>>>>>> conflict_050725_2128
  );
}

export default App;