import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../AuthContext';

const Header = ({ isAWSMode }) => {
  const { user, logout, isAdmin } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const buttonRef = useRef(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });

  // Calculate dropdown position based on button position
  useEffect(() => {
    if (showUserMenu && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + 8, // 8px gap below button
        right: window.innerWidth - rect.right // Position from right edge
      });
    }
  }, [showUserMenu]);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
  };

  // Dropdown component to be portaled
  const DropdownMenu = () => (
    <>
      {/* Backdrop overlay */}
      <div 
        className="fixed inset-0 z-[999999]" 
        onClick={() => setShowUserMenu(false)}
      />
      
      {/* Dropdown content */}
      <div 
        className="fixed w-64 bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 shadow-xl z-[9999999]"
        style={{
          top: `${dropdownPosition.top}px`,
          right: `${dropdownPosition.right}px`,
          maxHeight: `${window.innerHeight - dropdownPosition.top - 20}px`,
          overflowY: 'auto'
        }}
      >
        <div className="p-4 border-b border-white/20">
          <p className="text-white font-medium">{user?.name || user?.username}</p>
          <p className="text-purple-300 text-sm">{user?.email}</p>
          <div className="flex items-center space-x-2 mt-2 flex-wrap gap-1">
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              user?.role === 'admin' 
                ? 'bg-purple-500/30 text-purple-200' 
                : 'bg-blue-500/30 text-blue-200'
            }`}>
              {user?.role === 'admin' ? '👑 Admin' : '👤 User'}
            </span>
            {user?.is_verified && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/30 text-green-200">
                ✅ Verified
              </span>
            )}
            {user?.is_2fa_enabled && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500/30 text-orange-200">
                🔐 2FA
              </span>
            )}
          </div>
        </div>

        <div className="p-2">
          {/* Profile option */}
          <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
            👤 Profile
          </button>

          {/* Upload History */}
          <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
            📁 Upload History
          </button>

          {/* Admin Panel (admin only) */}
          {isAdmin() && (
            <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
              ⚙️ Admin Panel
            </button>
          )}

          {/* 2FA Setup */}
          <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
            🔐 {user?.is_2fa_enabled ? 'Manage 2FA' : 'Setup 2FA'}
          </button>

          <div className="border-t border-white/20 my-2"></div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-red-300 hover:bg-red-500/10 rounded-md transition-colors"
          >
            🚪 Sign Out
          </button>
        </div>
      </div>
    </>
  );

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-8 border border-white/20">
      <div className="flex justify-between items-center">
        {/* Left side - Title and AWS indicator */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">
            🎬 Video Splitter Pro
            {isAWSMode && <span className="text-sm text-green-400 block">⚡ AWS Amplify Mode</span>}
          </h1>
          <p className="text-xl text-purple-200">
            Split videos of any size while preserving subtitles and quality
          </p>
        </div>

        {/* Right side - User menu */}
        <div className="relative z-[9999]">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center space-x-3 bg-black/30 rounded-lg px-4 py-2 text-white hover:bg-black/40 transition-colors relative z-[10000]"
          >
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-sm font-bold">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium">{user?.name || user?.username}</p>
              <p className="text-xs text-purple-300">
                {user?.role === 'admin' ? '👑 Admin' : '👤 User'}
                {user?.is_verified && ' ✅'}
              </p>
            </div>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown menu - using portal-like approach */}
          {showUserMenu && (
            <>
              {/* Backdrop overlay */}
              <div 
                className="fixed inset-0 z-[999999]" 
                onClick={() => setShowUserMenu(false)}
              ></div>
              
              {/* Dropdown content - positioned at viewport level */}
              <div 
                className="fixed w-64 bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 shadow-xl z-[9999999]"
                style={{
                  top: '80px',
                  right: '20px',
                  maxHeight: 'calc(100vh - 100px)',
                  overflowY: 'auto'
                }}
              >
                <div className="p-4 border-b border-white/20">
                  <p className="text-white font-medium">{user?.name || user?.username}</p>
                  <p className="text-purple-300 text-sm">{user?.email}</p>
                  <div className="flex items-center space-x-2 mt-2 flex-wrap">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      user?.role === 'admin' 
                        ? 'bg-purple-500/30 text-purple-200' 
                        : 'bg-blue-500/30 text-blue-200'
                    }`}>
                      {user?.role === 'admin' ? '👑 Admin' : '👤 User'}
                    </span>
                    {user?.is_verified && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/30 text-green-200">
                        ✅ Verified
                      </span>
                    )}
                    {user?.is_2fa_enabled && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500/30 text-orange-200">
                        🔐 2FA
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-2">
                  {/* Profile option */}
                  <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
                    👤 Profile
                  </button>

                  {/* Upload History */}
                  <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
                    📁 Upload History
                  </button>

                  {/* Admin Panel (admin only) */}
                  {isAdmin() && (
                    <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
                      ⚙️ Admin Panel
                    </button>
                  )}

                  {/* 2FA Setup */}
                  <button className="w-full text-left px-3 py-2 text-white hover:bg-white/10 rounded-md transition-colors">
                    🔐 {user?.is_2fa_enabled ? 'Manage 2FA' : 'Setup 2FA'}
                  </button>

                  <div className="border-t border-white/20 my-2"></div>

                  {/* Logout */}
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 text-red-300 hover:bg-red-500/10 rounded-md transition-colors"
                  >
                    🚪 Sign Out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Header;