import React, { useState } from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import VideoSplitter from './VideoSplitter';
import AdminDashboard from './components/AdminDashboard';
import UserProfile from './components/UserProfile';
import TwoFactorSetup from './components/TwoFactorSetup';

const AppContent = () => {
  const { user, logout, requires2FASetup, complete2FASetup } = useAuth();
  const [showRegister, setShowRegister] = useState(false);
  const [currentView, setCurrentView] = useState('video-splitter'); // 'video-splitter', 'admin', or 'profile'

  const handleToggleForm = () => {
    setShowRegister(!showRegister);
  };

  const handleLogout = () => {
    logout();
    setCurrentView('video-splitter'); // Reset to default view
  };

  if (!user) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {showRegister ? (
          <RegisterForm onToggleForm={handleToggleForm} />
        ) : (
          <LoginForm onToggleForm={handleToggleForm} />
        )}
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      {/* Navigation Header */}
      <nav style={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        padding: '15px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
          <h1 style={{ 
            margin: 0, 
            color: '#333',
            fontSize: '24px',
            fontWeight: 'bold'
          }}>
            Video Splitter Pro
          </h1>
          
          <div style={{ display: 'flex', gap: '20px' }}>
            <button
              onClick={() => setCurrentView('video-splitter')}
              style={{
                padding: '8px 16px',
                backgroundColor: currentView === 'video-splitter' ? '#007bff' : 'transparent',
                color: currentView === 'video-splitter' ? 'white' : '#333',
                border: '1px solid #007bff',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold'
              }}
            >
              Video Splitter
            </button>
            
            {user.role === 'admin' && (
              <button
                onClick={() => setCurrentView('admin')}
                style={{
                  padding: '8px 16px',
                  backgroundColor: currentView === 'admin' ? '#dc3545' : 'transparent',
                  color: currentView === 'admin' ? 'white' : '#dc3545',
                  border: '1px solid #dc3545',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                Admin Dashboard
              </button>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
              {user.firstName} {user.lastName}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {user.role === 'admin' ? '🔒 Administrator' : '👤 User'} • {user.email}
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{ padding: '20px 0' }}>
        {currentView === 'video-splitter' ? (
          <VideoSplitter />
        ) : currentView === 'admin' && user.role === 'admin' ? (
          <AdminDashboard />
        ) : (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            color: 'white'
          }}>
            <h2>Access Denied</h2>
            <p>You don't have permission to access this page.</p>
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;