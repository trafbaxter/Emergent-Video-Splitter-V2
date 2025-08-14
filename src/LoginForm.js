import React, { useState } from 'react';
import { useAuth } from './AuthContext';

const LoginForm = ({ onToggleForm }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showTotpInput, setShowTotpInput] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setStatusMessage('');

    const result = await login(email, password, totpCode);
    
    if (!result.success) {
      // Handle different error types
      if (result.status === 'pending_approval') {
        setStatusMessage({
          type: 'warning',
          title: 'Account Pending Approval',
          message: 'Your account is awaiting administrator approval. You will receive an email once your account is approved.'
        });
      } else if (result.status === 'rejected') {
        setStatusMessage({
          type: 'error',
          title: 'Access Denied',
          message: 'Your account registration has been rejected. Please contact an administrator for more information.'
        });
      } else if (result.status === 'locked') {
        setStatusMessage({
          type: 'error',
          title: 'Account Locked',
          message: 'Your account has been temporarily locked due to multiple failed login attempts. Please try again later.'
        });
      } else if (result.requires_2fa) {
        setShowTotpInput(true);
        setError('Please enter your 2FA code to continue.');
      } else {
        setError(result.error);
      }
    } else if (result.force_password_change) {
      setStatusMessage({
        type: 'info',
        title: 'Password Change Required',
        message: 'You must change your password before continuing. Please use the password reset feature.'
      });
    }
    
    setLoading(false);
  };

  const StatusAlert = ({ status }) => {
    const styles = {
      warning: {
        backgroundColor: '#fff3cd',
        borderColor: '#ffeaa7',
        color: '#856404'
      },
      error: {
        backgroundColor: '#f8d7da',
        borderColor: '#f5c6cb',
        color: '#721c24'
      },
      info: {
        backgroundColor: '#d1ecf1',
        borderColor: '#bee5eb',
        color: '#0c5460'
      }
    };

    return (
      <div style={{
        ...styles[status.type],
        padding: '15px',
        marginBottom: '15px',
        border: '1px solid',
        borderRadius: '4px'
      }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>{status.title}</h4>
        <p style={{ margin: 0, fontSize: '14px' }}>{status.message}</p>
      </div>
    );
  };

  return (
    <div style={{ 
      maxWidth: '400px', 
      margin: '50px auto', 
      padding: '30px', 
      border: '1px solid #ddd', 
      borderRadius: '10px',
      backgroundColor: '#fff',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    }}>
      <h2 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>
        Login to Video Splitter Pro
      </h2>
      
      {statusMessage && <StatusAlert status={statusMessage} />}
      
      {error && (
        <div style={{ 
          padding: '10px', 
          marginBottom: '15px', 
          backgroundColor: '#f8d7da', 
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Email:
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '16px',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <div style={{ marginBottom: showTotpInput ? '15px' : '20px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Password:
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '16px',
              boxSizing: 'border-box'
            }}
          />
        </div>

        {showTotpInput && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              2FA Code:
            </label>
            <input
              type="text"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              placeholder="Enter 6-digit code"
              maxLength={6}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '16px',
                boxSizing: 'border-box',
                textAlign: 'center',
                letterSpacing: '2px'
              }}
            />
            <small style={{ color: '#666', fontSize: '12px' }}>
              Enter the 6-digit code from your authenticator app
            </small>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            fontSize: '16px',
            backgroundColor: loading ? '#6c757d' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginBottom: '15px'
          }}
        >
          {loading ? 'Logging in...' : showTotpInput ? 'Verify & Login' : 'Login'}
        </button>
      </form>

      <div style={{ textAlign: 'center' }}>
        <p style={{ margin: '0 0 10px 0', color: '#666' }}>
          Don't have an account?{' '}
          <button
            onClick={onToggleForm}
            style={{
              background: 'none',
              border: 'none',
              color: '#007bff',
              textDecoration: 'underline',
              cursor: 'pointer'
            }}
          >
            Sign up
          </button>
        </p>
        
        <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <small style={{ color: '#666' }}>
            <strong>Demo Admin Access:</strong><br />
            Email: admin@videosplitter.com<br />
            Password: AdminPass123!
          </small>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;