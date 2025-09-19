import React, { createContext, useContext, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { useGetCurrentUserQuery, useLoginMutation, useLogoutMutation } from '../store/api';
import { setCredentials, logout, setLoading, setError } from '../store/slices/authSlice';
import type { User, LoginForm } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginForm) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, isLoading, error, token } = useAppSelector((state) => state.auth);
  
  const [loginMutation] = useLoginMutation();
  const [logoutMutation] = useLogoutMutation();
  
  // Only fetch user if we have a token and are authenticated
  const { data: userData, isLoading: isUserLoading, error: userError } = useGetCurrentUserQuery(
    undefined,
    {
      skip: !token || !isAuthenticated,
    }
  );

  // Update user data when it's fetched
  useEffect(() => {
    if (userData?.data) {
      dispatch(setCredentials({
        user: userData.data,
        token: token!,
        refreshToken: localStorage.getItem('refresh_token') || '',
      }));
    }
  }, [userData, dispatch, token]);

  // Handle user fetch errors
  useEffect(() => {
    if (userError) {
      console.error('Failed to fetch user info:', userError);
      dispatch(logout());
    }
  }, [userError, dispatch]);

  // Update loading state
  useEffect(() => {
    dispatch(setLoading(isUserLoading));
  }, [isUserLoading, dispatch]);

  const login = async (credentials: LoginForm): Promise<void> => {
    try {
      dispatch(setLoading(true));
      dispatch(clearError());
      
      const result = await loginMutation(credentials).unwrap();
      
      if (result.success && result.data) {
        dispatch(setCredentials({
          user: result.data.user,
          token: result.data.access_token,
          refreshToken: result.data.refresh_token,
        }));
      } else {
        throw new Error(result.message || 'Login failed');
      }
    } catch (error: any) {
      const errorMessage = error?.data?.message || error?.message || 'Login failed';
      dispatch(setError(errorMessage));
      throw new Error(errorMessage);
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleLogout = async (): Promise<void> => {
    try {
      await logoutMutation().unwrap();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch(logout());
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.roles.some(role => 
      role.permissions.includes(permission)
    );
  };

  const clearError = (): void => {
    dispatch(setError(null));
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout: handleLogout,
    hasPermission,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
