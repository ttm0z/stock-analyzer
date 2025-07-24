import { createContext, useContext, useReducer, useEffect, useMemo } from 'react';
import AuthAPI from '../services/authAPI';
import { tokenStorage } from '../utils/secureStorage';
import { config } from '../config/environment';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
      return { 
        ...state, 
        loading: false, 
        isAuthenticated: true, 
        user: action.payload.user,
        token: action.payload.token,
        error: null 
      };
    case 'LOGIN_FAILURE':
      return { 
        ...state, 
        loading: false, 
        isAuthenticated: false, 
        user: null,
        token: null,
        error: action.payload 
      };
    case 'LOGOUT':
      return { 
        ...state, 
        isAuthenticated: false, 
        user: null,
        token: null,
        loading: false,
        error: null 
      };
    case 'UPDATE_PROFILE':
      return { 
        ...state, 
        user: { ...state.user, ...action.payload } 
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    default:
      return state;
  }
};

const initialState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: false,
  error: null,
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const token = tokenStorage.getToken();
    const storedUser = tokenStorage.getUser();
    
    if (token && storedUser) {
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user: storedUser, token }
      });
    }
    
    // Listen for token expiration events
    const handleTokenExpired = () => {
      dispatch({ type: 'LOGOUT' });
    };
    
    window.addEventListener('auth:token-expired', handleTokenExpired);
    
    return () => {
      window.removeEventListener('auth:token-expired', handleTokenExpired);
    };
  }, []);

  const login = async (email, password) => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await AuthAPI.login(email, password);
      
      // Store tokens securely
      const token = response.token || response.access_token;
      // Backend JWT tokens expire after 8 hours (28800 seconds), so store for 480 minutes
      const tokenExpiration = response.expires_in ? response.expires_in / 60 : 480; // 8 hours in minutes
      
      if (config.isDevelopment) {
        console.log('🔐 About to store token:', token ? 'Token received' : 'No token received');
      }
      
      AuthAPI.setToken(token, tokenExpiration);
      
      if (response.refresh_token) {
        AuthAPI.setRefreshToken(response.refresh_token);
      }
      
      AuthAPI.setUser(response.user);
      
      // Verify token was stored before dispatching success
      const storedToken = tokenStorage.getToken();
      if (config.isDevelopment) {
        console.log('🔍 Token storage verification:', storedToken ? 'Token stored successfully' : 'Token NOT stored');
      }
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: response.user,
          token: token
        }
      });
      
      if (config.isDevelopment) {
        console.log('✅ User logged in successfully');
      }
      
      return response;
    } catch (error) {
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: error.message
      });
      
      if (config.isDevelopment) {
        console.error('❌ Login failed:', error.message);
      }
      
      throw error;
    }
  };

  const register = async (email, password, firstName, lastName, username) => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await AuthAPI.register(email, password, firstName, lastName, username);
      
      // Store tokens securely
      const token = response.token || response.access_token;
      // Backend JWT tokens expire after 8 hours (28800 seconds), so store for 480 minutes
      const tokenExpiration = response.expires_in ? response.expires_in / 60 : 480; // 8 hours in minutes
      AuthAPI.setToken(token, tokenExpiration);
      
      if (response.refresh_token) {
        AuthAPI.setRefreshToken(response.refresh_token);
      }
      
      AuthAPI.setUser(response.user);
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: response.user,
          token: token
        }
      });
      
      if (config.isDevelopment) {
        console.log('✅ User registered successfully');
      }
      
      return response;
    } catch (error) {
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: error.message
      });
      
      if (config.isDevelopment) {
        console.error('❌ Registration failed:', error.message);
      }
      
      throw error;
    }
  };

  const logout = async () => {
    try {
      await AuthAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  const updateProfile = async (updates) => {
    try {
      const updatedUser = await AuthAPI.updateProfile(updates);
      AuthAPI.setUser(updatedUser);
      
      dispatch({
        type: 'UPDATE_PROFILE',
        payload: updatedUser
      });
      
      if (config.isDevelopment) {
        console.log('✅ Profile updated successfully');
      }
      
      return updatedUser;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      
      if (config.isDevelopment) {
        console.error('❌ Profile update failed:', error.message);
      }
      
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo(() => ({
    ...state,
    login,
    register,
    logout,
    updateProfile,
    clearError,
  }), [state, login, register, logout, updateProfile, clearError]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};