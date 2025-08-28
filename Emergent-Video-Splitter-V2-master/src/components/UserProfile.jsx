import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import TwoFactorSetup from './TwoFactorSetup';

const UserProfile = () => {
  const { user, accessToken, API_BASE } = useAuth();
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState(null);
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [show2FADisable, setShow2FADisable] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/user/profile`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserProfile(data.user);
      } else {
        setError('Failed to load user profile');
      }
    } catch (error) {
      console.error('Profile fetch error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handle2FASetupComplete = (success) => {
    if (success) {
      setSuccess('Two-factor authentication has been enabled successfully!');
      fetchUserProfile(); // Refresh profile data
    }
    setShow2FASetup(false);
  };

  const handle2FADisable = async () => {
    if (!disablePassword) {
      setError('Password is required to disable 2FA');
      return;
    }

    setActionLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/user/2fa/disable`, {
        method: 'POST',  
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: disablePassword })
      });

      if (response.ok) {
        setSuccess('Two-factor authentication has been disabled successfully!');
        setShow2FADisable(false);
        setDisablePassword('');
        fetchUserProfile(); // Refresh profile data
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to disable 2FA');
      }
    } catch (error) {
      console.error('2FA disable error:', error);
      setError('Network error. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        minHeight: '400px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div>
          <div style={{
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #007bff',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#fff',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '30px',
          textAlign: 'center'
        }}>
          <h1 style={{ margin: '0 0 10px 0', fontSize: '28px' }}>User Profile</h1>
          <p style={{ margin: 0, opacity: 0.9 }}>Manage your account settings and security</p>
        </div>

        {/* Content */}
        <div style={{ padding: '30px' }}>
          {/* Success/Error Messages */}
          {success && (
            <div style={{
              padding: '15px',
              backgroundColor: '#d4edda',
              color: '#155724',
              borderRadius: '8px',
              marginBottom: '20px',
              border: '1px solid #c3e6cb'
            }}>
              {success}
              <button
                onClick={() => setSuccess('')}
                style={{
                  float: 'right',
                  background: 'none',
                  border: 'none',
                  color: '#155724',
                  cursor: 'pointer',
                  fontSize: '18px'
                }}
              >
                ×
              </button>
            </div>
          )}

          {error && (
            <div style={{
              padding: '15px',
              backgroundColor: '#f8d7da',
              color: '#721c24',
              borderRadius: '8px',
              marginBottom: '20px',
              border: '1px solid #f5c6cb'
            }}>
              {error}
              <button
                onClick={() => setError('')}
                style={{
                  float: 'right',
                  background: 'none',
                  border: 'none',
                  color: '#721c24',
                  cursor: 'pointer',
                  fontSize: '18px'
                }}
              >
                ×
              </button>
            </div>
          )}

          {/* Account Information */}
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>Account Information</h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px'
            }}>
              <div style={{
                padding: '20px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#495057', fontSize: '16px' }}>
                  👤 Personal Details
                </h3>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Name:</strong> {userProfile?.firstName} {userProfile?.lastName}
                </p>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Email:</strong> {userProfile?.email}
                </p>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Role:</strong> {userProfile?.role === 'admin' ? '🔒 Administrator' : '👤 User'}
                </p>
              </div>

              <div style={{
                padding: '20px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
              }}>
                <h3 style={{ margin: '0 0 10px 0', color: '#495057', fontSize: '16px' }}>
                  📊 Account Status
                </h3>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Email Verified:</strong> {userProfile?.emailVerified ? '✅ Yes' : '❌ No'}
                </p>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Member Since:</strong> {userProfile?.createdAt ? new Date(userProfile.createdAt).toLocaleDateString() : 'N/A'}
                </p>
                <p style={{ margin: '5px 0', color: '#6c757d' }}>
                  <strong>Last Login:</strong> {userProfile?.lastLogin ? new Date(userProfile.lastLogin).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Two-Factor Authentication */}
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>🔐 Two-Factor Authentication</h2>
            <div style={{
              padding: '25px',
              backgroundColor: userProfile?.totpEnabled ? '#d4edda' : '#fff3cd',
              borderRadius: '8px',
              border: `1px solid ${userProfile?.totpEnabled ? '#c3e6cb' : '#ffeaa7'}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
                <div>
                  <h3 style={{ 
                    margin: '0 0 10px 0', 
                    color: userProfile?.totpEnabled ? '#155724' : '#856404',
                    fontSize: '18px'
                  }}>
                    {userProfile?.totpEnabled ? '🛡️ 2FA Enabled' : '⚠️ 2FA Not Enabled'}
                  </h3>
                  <p style={{ 
                    margin: 0, 
                    color: userProfile?.totpEnabled ? '#155724' : '#856404',
                    fontSize: '14px'
                  }}>
                    {userProfile?.totpEnabled 
                      ? 'Your account is protected with two-factor authentication using TOTP.'
                      : 'Enable 2FA to add an extra layer of security to your account.'
                    }
                  </p>
                </div>
                
                <div>
                  {userProfile?.totpEnabled ? (
                    <button
                      onClick={() => setShow2FADisable(true)}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: 'bold'
                      }}
                    >
                      Disable 2FA
                    </button>
                  ) : (
                    <button
                      onClick={() => setShow2FASetup(true)}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: 'bold'
                      }}
                    >
                      Enable 2FA
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Security Recommendations */}
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>🔒 Security Recommendations</h2>
            <div style={{
              padding: '20px',
              backgroundColor: '#e7f3ff',
              borderRadius: '8px',
              border: '1px solid #b3d9ff'
            }}>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#0066cc' }}>
                <li style={{ marginBottom: '8px' }}>
                  {userProfile?.totpEnabled ? '✅' : '❌'} Enable two-factor authentication
                </li>
                <li style={{ marginBottom: '8px' }}>
                  ✅ Use a strong, unique password
                </li>
                <li style={{ marginBottom: '8px' }}>
                  ✅ Keep your contact information up to date
                </li>
                <li style={{ marginBottom: '8px' }}>
                  ✅ Log out from shared devices
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 2FA Setup Modal */}
      <TwoFactorSetup
        isOpen={show2FASetup}
        onClose={() => setShow2FASetup(false)}
        onSetupComplete={handle2FASetupComplete}
      />

      {/* 2FA Disable Modal */}
      {show2FADisable && (
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
            maxWidth: '400px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
          }}>
            <h2 style={{ marginTop: 0, color: '#dc3545', textAlign: 'center' }}>
              ⚠️ Disable Two-Factor Authentication
            </h2>
            
            <div style={{
              backgroundColor: '#f8d7da',
              border: '1px solid #f5c6cb',
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '20px',
              color: '#721c24'
            }}>
              <strong>Warning:</strong> Disabling 2FA will reduce your account security. 
              You will no longer need a code from your authenticator app to log in.
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Enter your password to confirm:
              </label>
              <input
                type="password"
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
                placeholder="Your account password"
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

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShow2FADisable(false);
                  setDisablePassword('');
                  setError('');
                }}
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
                onClick={handle2FADisable}
                disabled={actionLoading || !disablePassword}
                style={{
                  padding: '10px 20px',
                  backgroundColor: actionLoading || !disablePassword ? '#ccc' : '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: actionLoading || !disablePassword ? 'not-allowed' : 'pointer',
                  fontSize: '14px'
                }}
              >
                {actionLoading ? 'Disabling...' : 'Disable 2FA'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default UserProfile;