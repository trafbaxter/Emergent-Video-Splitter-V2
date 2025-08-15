import React, { useState } from 'react';

const PasswordReset = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1); // 1: Email entry, 2: Success message
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod';

  const handlePasswordReset = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        setStep(2);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to send password reset email');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStep(1);
    setEmail('');
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '450px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {step === 1 && (
          <>
            <h2 style={{ marginTop: 0, textAlign: 'center', color: '#333' }}>
              🔑 Reset Your Password
            </h2>
            
            <p style={{ color: '#666', fontSize: '14px', textAlign: 'center', margin: '20px 0' }}>
              Enter your email address and we'll send you instructions to reset your password.
            </p>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#333' }}>
                Email Address:
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '16px',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            {error && (
              <div style={{
                padding: '12px',
                backgroundColor: '#f8d7da',
                color: '#721c24',
                borderRadius: '6px',
                marginBottom: '20px',
                border: '1px solid #f5c6cb'
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={handleClose}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handlePasswordReset}
                disabled={loading || !email}
                style={{
                  padding: '10px 20px',
                  backgroundColor: loading || !email ? '#ccc' : '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: loading || !email ? 'not-allowed' : 'pointer',
                  fontSize: '14px'
                }}
              >
                {loading ? 'Sending...' : 'Send Reset Email'}
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>📧</div>
            <h2 style={{ marginTop: 0, color: '#28a745' }}>
              Password Reset Email Sent!
            </h2>
            <p style={{ color: '#666', fontSize: '16px', margin: '20px 0' }}>
              We've sent password reset instructions to <strong>{email}</strong>. 
              Please check your email and follow the link to reset your password.
            </p>
            
            <div style={{
              backgroundColor: '#e7f3ff',
              border: '1px solid #b3d9ff',
              borderRadius: '8px',
              padding: '15px',
              margin: '20px 0',
              textAlign: 'left'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#0066cc' }}>Didn't receive the email?</h4>
              <ul style={{ color: '#0066cc', fontSize: '14px', margin: 0, paddingLeft: '20px' }}>
                <li>Check your spam/junk folder</li>
                <li>Make sure you entered the correct email address</li>
                <li>Wait a few minutes - emails may be delayed</li>
                <li>Contact support if you still don't receive it</li>
              </ul>
            </div>

            <button
              onClick={handleClose}
              style={{
                padding: '12px 24px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '16px',
                marginTop: '10px'
              }}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PasswordReset;