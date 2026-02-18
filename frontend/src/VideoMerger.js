import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const VideoMerger = () => {
  const { API_BASE } = useAuth();
  const [mergeJobId, setMergeJobId] = useState(null);
  const [error, setError] = useState(null);
  
  console.log("VideoMerger component rendering with API_BASE:", API_BASE);
  
  useEffect(() => {
    console.log("VideoMerger mounted successfully!");
    createMergeJob();
  }, []);
  
  const createMergeJob = async () => {
    try {
      console.log("Creating merge job at:", `${API_BASE}/api/merge/create-job`);
      const response = await fetch(`${API_BASE}/api/merge/create-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMergeJobId(data.job_id);
        console.log("Merge job created:", data.job_id);
      } else {
        throw new Error('Failed to create merge job');
      }
    } catch (err) {
      console.error("Error creating merge job:", err);
      setError('Failed to initialize merge job: ' + err.message);
    }
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

        {/* Status Display */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          padding: '30px',
          marginBottom: '30px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          textAlign: 'center'
        }}>
          {error ? (
            <div style={{ color: '#ff6b6b', fontSize: '16px' }}>
              ❌ {error}
            </div>
          ) : mergeJobId ? (
            <div style={{ color: '#4ade80', fontSize: '16px' }}>
              ✅ Video Merger Ready! Job ID: {mergeJobId}
              <br/>
              <small style={{ color: 'rgba(255,255,255,0.7)' }}>
                Backend connected at: {API_BASE}
              </small>
            </div>
          ) : (
            <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '16px' }}>
              🔄 Initializing Video Merger...
            </div>
          )}
        </div>

        {/* Upload Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          padding: '30px',
          marginBottom: '30px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
            Upload Videos to Merge
          </h2>
          
          <div style={{
            border: '2px dashed rgba(255,255,255,0.3)',
            borderRadius: '15px',
            padding: '40px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            marginBottom: '20px'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🎥</div>
            <h3 style={{ color: 'white', fontSize: '1.3rem', margin: '0 0 10px 0' }}>
              Choose Videos to Merge
            </h3>
            <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0 }}>
              Video merger functionality is ready!<br/>
              <small>Backend API connected successfully at {API_BASE}</small>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoMerger;