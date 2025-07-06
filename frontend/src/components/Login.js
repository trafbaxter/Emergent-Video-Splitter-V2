import React, { useState } from 'react';
import { useAuth } from './AuthContext';

const Login = () => {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    totpCode: ''
  });
  const [error, setError] = useState('');
  const [showTwoFA, setShowTwoFA] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.username || !formData.password) {
      setError('Please enter both username and password');
      return;
    }

    const result = await login(
      formData.username, 
      formData.password, 
      formData.totpCode || null
    );

    if (!result.success) {
      if (result.error.includes('2FA code required')) {
        setShowTwoFA(true);
        setError('Please enter your 2FA code');
      } else {
        setError(result.error);
      }
    }
  };

  const handleDemoLogin = async () => {
    setFormData({
      username: 'tadmin',
      password: '@DefaultUser1234',
      totpCode: ''
    });
    setError('');
    
    const result = await login('tadmin', '@DefaultUser1234');
    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🎬</h1>
          <h2 className="text-2xl font-bold text-white mb-2">Video Splitter Pro</h2>
          <p className="text-purple-200">Sign in to your account</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 mb-6">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-white font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="w-full bg-black/30 text-white rounded-lg p-3 border border-white/20 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
              placeholder="Enter your username"
              required
            />
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-white font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full bg-black/30 text-white rounded-lg p-3 border border-white/20 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
              placeholder="Enter your password"
              required
            />
          </div>

          {/* 2FA Code (shown conditionally) */}
          {showTwoFA && (
            <div>
              <label htmlFor="totpCode" className="block text-white font-medium mb-2">
                2FA Code
              </label>
              <input
                type="text"
                id="totpCode"
                name="totpCode"
                value={formData.totpCode}
                onChange={handleChange}
                className="w-full bg-black/30 text-white rounded-lg p-3 border border-white/20 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                placeholder="Enter 6-digit 2FA code"
                maxLength="6"
              />
              <p className="text-purple-200 text-sm mt-1">
                Enter the 6-digit code from your authenticator app
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-6 rounded-xl transition-all duration-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Demo Login */}
        <div className="mt-6 pt-6 border-t border-white/20">
          <p className="text-purple-200 text-sm text-center mb-3">
            Demo Account Available
          </p>
          <button
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing In...' : 'Try Demo (Admin Account)'}
          </button>
          <p className="text-purple-300 text-xs text-center mt-2">
            Username: tadmin | Password: @DefaultUser1234
          </p>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-purple-300 text-sm">
            Secure authentication with JWT tokens
          </p>
          <p className="text-purple-400 text-xs mt-1">
            Protected by 2FA • Email verification required
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;