import React from 'react';
import VideoSplitter from './components/VideoSplitter';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Video Splitter Pro
              </h1>
            </div>
          </div>
        </div>
      </header>
      <main>
        <VideoSplitter />
      </main>
    </div>
  );
}

export default App;