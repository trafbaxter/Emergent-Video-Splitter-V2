import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'));
  const [requires2FASetup, setRequires2FASetup] = useState(false);
  
  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://2419j971hh.execute-api.us-east-1.amazonaws.com/prod';

  useEffect(() => {
    if (accessToken) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/user/profile`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        // Token is invalid or expired
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, totpCode = null) => {
    try {
      const requestBody = { email, password };
      if (totpCode) {
        requestBody.totpCode = totpCode;
      }

      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (response.ok) {
        // Check if 2FA is required
        if (data.requires_2fa) {
          return { 
            success: false, 
            requires_2fa: true, 
            user_id: data.user_id,
            error: '2FA code required' 
          };
        }

        // Successful login
        setAccessToken(data.access_token);
        localStorage.setItem('access_token', data.access_token);
        setUser(data.user);
        
        return { 
          success: true, 
          force_password_change: data.force_password_change 
        };
      } else {
        // Handle different error statuses
        if (response.status === 403) {
          return { 
            success: false, 
            status: data.status,
            error: data.message || 'Access denied' 
          };
        } else if (response.status === 423) {
          return { 
            success: false, 
            status: 'locked',
            error: data.message || 'Account locked' 
          };
        } else {
          return { 
            success: false, 
            error: data.message || 'Login failed' 
          };
        }
      }
    } catch (error) {
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });

      const data = await response.json();

      if (response.ok) {
        // Check if registration requires approval
        if (data.status === 'pending_approval') {
          return { 
            success: true, 
            status: 'pending_approval',
            message: data.message 
          };
        } else {
          // Auto-approved registration (shouldn't happen with new system, but handle it)
          setAccessToken(data.access_token);
          localStorage.setItem('access_token', data.access_token);
          setUser(data.user);
          return { success: true };
        }
      } else {
        return { success: false, error: data.message || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem('access_token');
  };

  const value = {
    user,
    loading,
    accessToken,
    login,
    register,
    logout,
    API_BASE
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};