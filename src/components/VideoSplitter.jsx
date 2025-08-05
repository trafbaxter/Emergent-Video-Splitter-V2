import React from 'react';

function VideoSplitter() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Video Splitter Pro</h2>
      <p>Video processing application coming soon...</p>
      <div style={{ 
        border: '2px dashed #ccc', 
        padding: '40px', 
        margin: '20px 0',
        borderRadius: '8px'
      }}>
        <p>Upload your video files here</p>
        <input type="file" accept="video/*" />
      </div>
    </div>
  );
}

export default VideoSplitter;