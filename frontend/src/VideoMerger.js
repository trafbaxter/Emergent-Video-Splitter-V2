import React, { useEffect } from 'react';

const VideoMerger = () => {
  console.log("VideoMerger component is rendering!");
  
  useEffect(() => {
    console.log("VideoMerger mounted and ready!");
    // Force a style change to document body
    document.body.style.border = "5px solid red";
    document.title = "Video Merger Pro - Active";
    
    return () => {
      console.log("VideoMerger unmounting");
      document.body.style.border = "";
      document.title = "Video Splitter & Merger Pro";
    };
  }, []);
  
  return (
    <div 
      className="video-merger-container" 
      id="video-merger-active"
      style={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%)', // VERY different colors
        padding: '40px 20px',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        border: '10px solid orange' // Obvious visual indicator
      }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ 
            fontSize: '4rem', 
            fontWeight: '900', 
            color: 'yellow', 
            margin: '0 0 10px 0',
            textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            border: '5px solid black'
          }}>
            🎬 VIDEO MERGER PRO 🎬
          </h1>
          <p style={{ 
            color: 'white', 
            fontSize: '1.5rem', 
            margin: 0,
            fontWeight: '700',
            backgroundColor: 'rgba(0,0,0,0.5)',
            padding: '10px',
            borderRadius: '10px'
          }}>
            THIS IS THE MERGER COMPONENT - NOT SPLITTER!
          </p>
        </div>

        {/* Very obvious content */}
        <div style={{
          background: 'rgba(255, 255, 0, 0.9)',
          border: '5px solid red',
          borderRadius: '20px',
          padding: '30px',
          marginBottom: '30px',
          textAlign: 'center'
        }}>
          <h2 style={{ color: 'red', fontSize: '2rem', marginBottom: '20px', fontWeight: '900' }}>
            🔥 VIDEO MERGER IS ACTIVE 🔥
          </h2>
          
          <div style={{
            border: '5px dashed red',
            borderRadius: '15px',
            padding: '40px 20px',
            textAlign: 'center',
            backgroundColor: 'white',
            marginBottom: '20px'
          }}>
            <div style={{ fontSize: '5rem', marginBottom: '20px' }}>🎥🔀🎥</div>
            <h3 style={{ color: 'black', fontSize: '2rem', margin: '0 0 10px 0' }}>
              MERGE MULTIPLE VIDEOS HERE
            </h3>
            <p style={{ color: 'black', margin: 0, fontSize: '1.2rem' }}>
              This is definitely the VideoMerger component!<br/>
              <strong>NOT the Video Splitter</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoMerger;