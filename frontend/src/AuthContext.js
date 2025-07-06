import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Get backend URL from environment
const BACKEND_URL = process.env.REACT_APP_API_GATEWAY_URL || process.env.REACT_APP_BACKEND_URL;

// Create Auth Context
const AuthContext = createContext();

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [tokens, setTokens] = useState({
    access_token: null,
    refresh_token: null
  });

  // Initialize authentication on app load
  useEffect(() => {
    initializeAuth();
  }, []);

  // Initialize authentication state
  const initializeAuth = async () => {
    try {
      const storedTokens = getStoredTokens();
      
      if (storedTokens.access_token) {
        setTokens(storedTokens);
        
        // Verify token by getting current user
        const userData = await getCurrentUser(storedTokens.access_token);
        if (userData) {
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          // Token invalid, try to refresh
          const refreshed = await refreshTokens(storedTokens.refresh_token);
          if (!refreshed) {
            logout();
          }
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  // Get stored tokens from localStorage
  const getStoredTokens = () => {
    try {
      return {
        access_token: localStorage.getItem('access_token'),
        refresh_token: localStorage.getItem('refresh_token')
      };
    } catch (error) {
      console.error('Error reading tokens from storage:', error);
      return { access_token: null, refresh_token: null };
    }
  };

  // Store tokens in localStorage
  const storeTokens = (accessToken, refreshToken) => {
    try {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    } catch (error) {
      console.error('Error storing tokens:', error);
    }
  };

  // Clear stored tokens
  const clearStoredTokens = () => {
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } catch (error) {
      console.error('Error clearing tokens:', error);
    }
  };

  // Get current user info
  const getCurrentUser = async (accessToken) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  };

  // Login function
  const login = async (username, password, totpCode = null) => {
    try {
      setIsLoading(true);
      
      const response = await axios.post(`${BACKEND_URL}/auth/login`, {
        username,
        password,
        totp_code: totpCode
      });

      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens
      setTokens({ access_token, refresh_token });
      storeTokens(access_token, refresh_token);

      // Set user data
      setUser(userData);
      setIsAuthenticated(true);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Login error:', error);
      
      let errorMessage = 'Login failed';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    setTokens({ access_token: null, refresh_token: null });
    clearStoredTokens();
  };

  // Refresh tokens
  const refreshTokens = async (refreshToken) => {
    try {
      if (!refreshToken) return false;

      const response = await axios.post(`${BACKEND_URL}/auth/refresh`, {
        refresh_token: refreshToken
      });

      const { access_token, refresh_token: new_refresh_token } = response.data;

      // Update tokens
      setTokens({ access_token, refresh_token: new_refresh_token });
      storeTokens(access_token, new_refresh_token);

      // Get updated user info
      const userData = await getCurrentUser(access_token);
      if (userData) {
        setUser(userData);
        setIsAuthenticated(true);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  };

  // Setup axios interceptor for automatic token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          const refreshed = await refreshTokens(tokens.refresh_token);
          if (refreshed && tokens.access_token) {
            originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
            return axios(originalRequest);
          } else {
            logout();
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [tokens.refresh_token, tokens.access_token]);

  // Get authorization header
  const getAuthHeader = () => {
    return tokens.access_token ? { Authorization: `Bearer ${tokens.access_token}` } : {};
  };

  // Check if user has specific role
  const hasRole = (role) => {
    return user?.role === role;
  };

  // Check if user is admin
  const isAdmin = () => {
    return hasRole('admin');
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshTokens,
    getAuthHeader,
    hasRole,
    isAdmin,
    tokens
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};