import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

export default function VideoSplitter() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [splitConfig, setSplitConfig] = useState({
    type: 'time',
    time_points: [0, 30],
    output_format: 'mp4',
    preserve_quality: true
  });
  const [jobStatus, setJobStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const videoRef = useRef(null);

  const { user } = useAuth();
  
  // Use environment variable for API URL
  const API = import.meta.env.VITE_REACT_APP_API_GATEWAY_URL || 'https://ztu91dvx96.execute-api.us-east-1.amazonaws.com/prod';

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    console.log('Selected file:', file.name, file.size, file.type);
    setSelectedFile(file);
    
    // Reset previous state
    setVideoInfo(null);
    setJobStatus(null);
    setCurrentTime(0);
    setSplitConfig(prev => ({ ...prev, time_points: [0, 30] }));

    try {
      // Get upload URL with authentication
      console.log('Getting upload URL...');
      const uploadResponse = await axios.post(`${API}/api/upload`, {
        filename: file.name,
        content_type: file.type,
        file_size: file.size
      });

      console.log('Upload response:', uploadResponse.data);

      if (uploadResponse.data.upload_method === 'presigned_post') {
        // S3 presigned POST upload
        const { presigned_post } = uploadResponse.data;
        const formData = new FormData();
        
        // Add all the required fields from presigned post
        Object.keys(presigned_post.fields).forEach(key => {
          formData.append(key, presigned_post.fields[key]);
        });
        formData.append('file', file);

        console.log('Uploading to S3 via presigned POST...');
        await axios.post(presigned_post.url, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        console.log('File uploaded successfully');
        
        // Get video info using the job_id
        await getVideoInfo(uploadResponse.data.job_id);
        
      } else if (uploadResponse.data.upload_method === 'presigned_put') {
        // S3 presigned PUT upload
        console.log('Uploading to S3 via presigned PUT...');
        await axios.put(uploadResponse.data.presigned_url, file, {
          headers: {
            'Content-Type': file.type
          }
        });

        console.log('File uploaded successfully');
        
        // Get video info using the job_id
        await getVideoInfo(uploadResponse.data.job_id);
      }

    } catch (error) {
      console.error('Upload failed:', error);
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.');
      } else {
        alert('Upload failed: ' + (error.response?.data?.error || error.message));
      }
    }
  };

  const getVideoInfo = async (jobId) => {
    try {
      console.log('Getting video info for job:', jobId);
      const response = await axios.get(`${API}/api/video-info/${jobId}`);
      console.log('Video info response:', response.data);
      setVideoInfo(response.data);
      
      // Update split config with reasonable defaults based on video duration
      if (response.data.duration) {
        const halfDuration = Math.floor(response.data.duration / 2);
        setSplitConfig(prev => ({
          ...prev,
          time_points: [0, halfDuration]
        }));
      }
    } catch (error) {
      console.error('Failed to get video info:', error);
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.');
      } else {
        console.error('Error response:', error.response?.data);
      }
    }
  };

  const formatTime = (seconds) => {
    if (!seconds && seconds !== 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimePointChange = (index, value) => {
    const newTimePoints = [...splitConfig.time_points];
    newTimePoints[index] = Math.max(0, Math.min(value, videoInfo?.duration || 3600));
    setSplitConfig(prev => ({ ...prev, time_points: newTimePoints }));
  };

  const addTimePoint = () => {
    const lastPoint = splitConfig.time_points[splitConfig.time_points.length - 1];
    const newPoint = Math.min(lastPoint + 30, videoInfo?.duration || 3600);
    setSplitConfig(prev => ({
      ...prev,
      time_points: [...prev.time_points, newPoint]
    }));
  };

  const removeTimePoint = (index) => {
    if (splitConfig.time_points.length > 2) {
      const newTimePoints = splitConfig.time_points.filter((_, i) => i !== index);
      setSplitConfig(prev => ({ ...prev, time_points: newTimePoints }));
    }
  };

  const startSplitting = async () => {
    if (!videoInfo || !videoInfo.job_id) {
      alert('Please upload a video first');
      return;
    }

    setIsProcessing(true);
    setProgress(0);

    try {
      console.log('Starting video splitting...');
      
      // Ensure the split configuration includes the total duration as the final time point
      const timePoints = [...splitConfig.time_points];
      
      // Add video duration as final time point if not already present
      if (videoInfo.duration && timePoints[timePoints.length - 1] !== videoInfo.duration) {
        timePoints.push(videoInfo.duration);
      }
      
      console.log('Time points for splitting:', timePoints);
      
      const splitPayload = {
        ...splitConfig,
        time_points: timePoints
      };
      
      const response = await axios.post(`${API}/api/split/${videoInfo.job_id}`, splitPayload);
      
      console.log('Split response:', response.data);
      setJobStatus({ status: 'processing', job_id: videoInfo.job_id });
      
      // Poll for status updates
      pollJobStatus(videoInfo.job_id);
      
    } catch (error) {
      console.error('Split failed:', error);
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.');
      } else {
        alert('Split failed: ' + (error.response?.data?.error || error.message));
      }
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API}/api/job/${jobId}/status`);
      console.log('Job status:', response.data);
      
      setJobStatus(response.data);
      
      if (response.data.progress !== undefined) {
        setProgress(response.data.progress);
      }
      
      if (response.data.status === 'completed') {
        setIsProcessing(false);
        console.log('Processing completed!');
      } else if (response.data.status === 'failed') {
        setIsProcessing(false);
        alert('Processing failed: ' + (response.data.error || 'Unknown error'));
      } else {
        // Continue polling
        setTimeout(() => pollJobStatus(jobId), 2000);
      }
    } catch (error) {
      console.error('Status check failed:', error);
      if (error.response?.status === 401) {
        alert('Authentication required. Please log in again.');
      }
      setIsProcessing(false);
    }
  };

  // Update current time from video
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-blue-600 text-white p-6">
            <h1 className="text-3xl font-bold">Video Splitter</h1>
            <p className="mt-2 text-blue-100">Upload and split your videos with precision</p>
            <p className="mt-1 text-blue-200 text-sm">Logged in as: {user?.firstName} {user?.lastName}</p>
          </div>

          <div className="p-6">
            {/* Upload Section */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Upload Video</h2>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="text-gray-600">
                    <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <p className="text-lg">Click to upload video</p>
                    <p className="text-sm">or drag and drop</p>
                    <p className="text-xs text-gray-500 mt-2">Supports MP4, MKV, AVI, MOV, and more</p>
                  </div>
                </label>
              </div>
              {selectedFile && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p><strong>Selected:</strong> {selectedFile.name}</p>
                  <p><strong>Size:</strong> {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  <p><strong>Type:</strong> {selectedFile.type}</p>
                </div>
              )}
            </div>

            {/* Video Info Section */}
            {videoInfo && (
              <div className="mb-8 grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h2 className="text-xl font-semibold">Video Information</h2>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Duration:</span>
                        <span className="ml-2">{formatTime(videoInfo.duration)}</span>
                      </div>
                      <div>
                        <span className="font-medium">Format:</span>
                        <span className="ml-2">{videoInfo.format}</span>
                      </div>
                      <div>
                        <span className="font-medium">Size:</span>
                        <span className="ml-2">{videoInfo.size}</span>
                      </div>
                      <div>
                        <span className="font-medium">Resolution:</span>
                        <span className="ml-2">{videoInfo.resolution}</span>
                      </div>
                      <div>
                        <span className="font-medium">Video Streams:</span>
                        <span className="ml-2">{videoInfo.video_streams}</span>
                      </div>
                      <div>
                        <span className="font-medium">Audio Streams:</span>
                        <span className="ml-2">{videoInfo.audio_streams}</span>
                      </div>
                      <div>
                        <span className="font-medium">Subtitle Streams:</span>
                        <span className="ml-2">{videoInfo.subtitle_streams}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h2 className="text-xl font-semibold">Video Preview</h2>
                  <video
                    ref={videoRef}
                    controls
                    onTimeUpdate={handleTimeUpdate}
                    className="w-full rounded-lg shadow-md"
                    style={{ maxHeight: '300px' }}
                  >
                    <source src={`${API}/api/stream/${videoInfo.job_id}/${videoInfo.filename}`} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                  <p className="text-sm text-gray-600">Current time: {formatTime(currentTime)}</p>
                </div>
              </div>
            )}

            {/* Split Configuration */}
            {videoInfo && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold mb-4">Split Configuration</h2>
                <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Output Format
                      </label>
                      <select
                        value={splitConfig.output_format}
                        onChange={(e) => setSplitConfig(prev => ({ ...prev, output_format: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="mp4">MP4</option>
                        <option value="mkv">MKV</option>
                        <option value="avi">AVI</option>
                      </select>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="preserve_quality"
                        checked={splitConfig.preserve_quality}
                        onChange={(e) => setSplitConfig(prev => ({ ...prev, preserve_quality: e.target.checked }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="preserve_quality" className="ml-2 text-sm text-gray-700">
                        Preserve Original Quality
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Split Points (seconds)
                    </label>
                    <div className="space-y-2">
                      {splitConfig.time_points.map((point, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600 w-16">Point {index + 1}:</span>
                          <input
                            type="number"
                            value={point}
                            onChange={(e) => handleTimePointChange(index, parseInt(e.target.value) || 0)}
                            className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            min="0"
                            max={videoInfo?.duration || 3600}
                          />
                          <span className="text-sm text-gray-500">({formatTime(point)})</span>
                          {splitConfig.time_points.length > 2 && (
                            <button
                              onClick={() => removeTimePoint(index)}
                              className="px-2 py-1 bg-red-100 text-red-600 rounded-md hover:bg-red-200 text-sm"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={addTimePoint}
                      className="mt-2 px-3 py-1 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm"
                    >
                      Add Split Point
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Process Button */}
            {videoInfo && !isProcessing && (
              <div className="mb-8">
                <button
                  onClick={startSplitting}
                  className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-semibold text-lg"
                >
                  Start Splitting Video
                </button>
              </div>
            )}

            {/* Processing Status */}
            {isProcessing && (
              <div className="mb-8">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-blue-800 mb-2">Processing Video...</h3>
                  <div className="w-full bg-blue-200 rounded-full h-3 mb-2">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-blue-700">Progress: {progress}%</p>
                </div>
              </div>
            )}

            {/* Results */}
            {jobStatus && jobStatus.status === 'completed' && jobStatus.output_files && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold mb-4">Split Results</h2>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {jobStatus.output_files.map((file, index) => (
                      <div key={index} className="bg-white p-4 rounded-lg border border-green-200">
                        <h4 className="font-medium text-green-800 mb-2">{file.filename}</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Size: {file.size || 'Processing...'}
                        </p>
                        <a
                          href={`${API}/api/download/${jobStatus.job_id}/${file.filename}`}
                          className="inline-block w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors text-center text-sm"
                          download
                        >
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}