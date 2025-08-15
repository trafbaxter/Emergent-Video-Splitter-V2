import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import QRCode from 'qrcode.react';

const TwoFactorSetup = ({ isOpen, onClose, onSetupComplete }) => {
  const { accessToken, API_BASE } = useAuth();
  const [step, setStep] = useState(1); // 1: Setup, 2: Verify, 3: Complete
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [qrCodeDataURL, setQrCodeDataURL] = useState('');

  useEffect(() => {
    if (isOpen && step === 1) {
      initiate2FASetup();
    }
  }, [isOpen, step]);

  const initiate2FASetup = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE}/api/user/2fa/setup`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSetupData(data);
        
        // Generate QR code from provisioning URI using JavaScript
        if (data.qr_code && data.qr_code.provisioning_uri) {
          generateQRCode(data.qr_code.provisioning_uri);
        }
        
        setStep(2);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to setup 2FA');
      }
    } catch (error) {
      console.error('2FA setup error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateQRCode = (provisioning_uri) => {
    // QR code will be generated using QRCode.react component directly in render
    // This function is kept for compatibility but qrCodeDataURL is set to provisioning_uri
    setQrCodeDataURL(provisioning_uri);
  };

  const verify2FASetup = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/user/2fa/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: verificationCode })
      });

      if (response.ok) {
        const data = await response.json();
        setStep(3);
        
        // Notify parent component
        if (onSetupComplete) {
          onSetupComplete(true);
        }
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Invalid verification code');
      }
    } catch (error) {
      console.error('2FA verification error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStep(1);
    setError('');
    setVerificationCode('');
    setSetupData(null);
    setQrCodeDataURL('');
    onClose();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(() => {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('Copied to clipboard!');
    });
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
        maxWidth: '500px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}>
        {/* Step 1: Loading */}
        {step === 1 && (
          <div>
            <h2 style={{ marginTop: 0, textAlign: 'center', color: '#333' }}>
              🔐 Setting up Two-Factor Authentication
            </h2>
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              {loading ? (
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
                  <p>Generating your 2FA setup...</p>
                </div>
              ) : (
                <button
                  onClick={initiate2FASetup}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  Start Setup
                </button>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Setup & Verification */}
        {step === 2 && setupData && (
          <div>
            <h2 style={{ marginTop: 0, textAlign: 'center', color: '#333' }}>
              📱 Configure Your Authenticator
            </h2>
            
            <div style={{ marginBottom: '25px' }}>
              <h3 style={{ color: '#555', fontSize: '16px' }}>Step 1: Install an Authenticator App</h3>
              <p style={{ color: '#666', fontSize: '14px', margin: '10px 0' }}>
                Download one of these apps on your mobile device:
              </p>
              <ul style={{ color: '#666', fontSize: '14px', paddingLeft: '20px' }}>
                <li>Google Authenticator</li>
                <li>Microsoft Authenticator</li>
                <li>Authy</li>
                <li>1Password</li>
              </ul>
            </div>

            <div style={{ marginBottom: '25px' }}>
              <h3 style={{ color: '#555', fontSize: '16px' }}>Step 2: Add Your Account</h3>
              
              {qrCodeDataURL ? (
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <p style={{ color: '#666', fontSize: '14px' }}>Scan this QR code with your app:</p>
                  <img 
                    src={qrCodeDataURL} 
                    alt="2FA QR Code" 
                    style={{ 
                      border: '1px solid #ddd', 
                      borderRadius: '8px',
                      maxWidth: '200px',
                      margin: '10px 0'
                    }} 
                  />
                </div>
              ) : (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '20px', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '8px',
                  marginBottom: '20px'
                }}>
                  <p style={{ color: '#666', fontSize: '14px', margin: 0 }}>
                    QR code generation unavailable. Use manual entry below.
                  </p>
                </div>
              )}

              <div style={{ 
                backgroundColor: '#f8f9fa', 
                padding: '15px', 
                borderRadius: '8px',
                marginBottom: '15px'
              }}>
                <p style={{ margin: '0 0 10px 0', fontWeight: 'bold', fontSize: '14px' }}>
                  Manual Entry:
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <code style={{ 
                    flex: 1,
                    padding: '8px',
                    backgroundColor: 'white',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '12px',
                    wordBreak: 'break-all'
                  }}>
                    {setupData.totp_secret}
                  </code>
                  <button
                    onClick={() => copyToClipboard(setupData.totp_secret)}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '25px' }}>
              <h3 style={{ color: '#555', fontSize: '16px' }}>Step 3: Enter Verification Code</h3>
              <p style={{ color: '#666', fontSize: '14px', margin: '10px 0' }}>
                Enter the 6-digit code from your authenticator app:
              </p>
              
              <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: '2px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '18px',
                    textAlign: 'center',
                    letterSpacing: '2px',
                    fontFamily: 'monospace'
                  }}
                />
                <button
                  onClick={verify2FASetup}
                  disabled={loading || verificationCode.length !== 6}
                  style={{
                    padding: '12px 20px',
                    backgroundColor: verificationCode.length === 6 ? '#007bff' : '#ccc',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: verificationCode.length === 6 ? 'pointer' : 'not-allowed',
                    fontSize: '14px'
                  }}
                >
                  {loading ? 'Verifying...' : 'Verify'}
                </button>
              </div>
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
          </div>
        )}

        {/* Step 3: Complete */}
        {step === 3 && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🎉</div>
            <h2 style={{ marginTop: 0, color: '#28a745' }}>
              Two-Factor Authentication Enabled!
            </h2>
            <p style={{ color: '#666', fontSize: '16px', margin: '20px 0' }}>
              Your account is now protected with 2FA. You'll need to enter a code from your authenticator app each time you log in.
            </p>
            
            <div style={{
              backgroundColor: '#d4edda',
              border: '1px solid #c3e6cb',
              borderRadius: '8px',
              padding: '15px',
              margin: '20px 0',
              textAlign: 'left'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#155724' }}>Important Security Tips:</h4>
              <ul style={{ color: '#155724', fontSize: '14px', margin: 0, paddingLeft: '20px' }}>
                <li>Keep your authenticator app secure and backed up</li>
                <li>Don't share your 2FA codes with anyone</li>
                <li>Contact support if you lose access to your authenticator</li>
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
              Complete Setup
            </button>
          </div>
        )}

        {/* Close button for steps 1 and 2 */}
        {step < 3 && (
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
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
          </div>
        )}
      </div>

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

export default TwoFactorSetup;