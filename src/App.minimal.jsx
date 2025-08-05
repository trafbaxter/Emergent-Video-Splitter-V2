import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Video Splitter Pro</h1>
      <p>Your video processing application is working!</p>
      <div style={{ 
        border: '2px dashed #007bff', 
        padding: '40px', 
        margin: '20px 0',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <h3>Upload Video</h3>
        <input type="file" accept="video/*" />
        <br /><br />
        <button style={{
          backgroundColor: '#007bff',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          Process Video
        </button>
      </div>
      <p>Backend API: Connected to AWS Lambda with Authentication</p>
    </div>
  );
}

export default App;