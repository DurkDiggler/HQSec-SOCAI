import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

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
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    if (token) {
      // Verify token and get user info
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // Token might be invalid, clear it
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, mfaCode = null) => {
    try {
      const response = await api.post('/auth/login', {
        email,
        password,
        mfa_code: mfaCode
      });
      
      const { access_token, refresh_token, user: userData } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (email, username, password, fullName) => {
    try {
      const response = await api.post('/auth/register', {
        email,
        username,
        password,
        full_name: fullName
      });
      
      return { success: true, user: response.data };
    } catch (error) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setUser(null);
    }
  };

  const refreshToken = async () => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      if (!refreshTokenValue) {
        throw new Error('No refresh token');
      }

      const response = await api.post('/auth/refresh', null, {
        params: { refresh_token: refreshTokenValue }
      });
      
      const { access_token, refresh_token: newRefreshToken } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', newRefreshToken);
      
      setToken(access_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  };

  const setupMFA = async () => {
    try {
      const response = await api.post('/auth/mfa/setup');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('MFA setup failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'MFA setup failed' 
      };
    }
  };

  const enableMFA = async (totpCode) => {
    try {
      await api.post('/auth/mfa/enable', { totp_code: totpCode });
      return { success: true };
    } catch (error) {
      console.error('MFA enable failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'MFA enable failed' 
      };
    }
  };

  const disableMFA = async (mfaCode) => {
    try {
      await api.post('/auth/mfa/disable', { mfa_code: mfaCode });
      return { success: true };
    } catch (error) {
      console.error('MFA disable failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'MFA disable failed' 
      };
    }
  };

  const getOAuthUrl = async (provider = 'google') => {
    try {
      const response = await api.get(`/auth/oauth/${provider}/url`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('OAuth URL fetch failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'OAuth URL fetch failed' 
      };
    }
  };

  const hasPermission = (permission) => {
    if (!user || !user.roles) return false;
    
    return user.roles.some(role => 
      role.permissions && role.permissions.includes(permission)
    );
  };

  const hasRole = (roleName) => {
    if (!user || !user.roles) return false;
    
    return user.roles.some(role => role.name === roleName);
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshToken,
    setupMFA,
    enableMFA,
    disableMFA,
    getOAuthUrl,
    hasPermission,
    hasRole
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
