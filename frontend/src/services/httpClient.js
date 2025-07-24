import axios from 'axios';
import { config } from '../config/environment';
import { tokenStorage } from '../utils/secureStorage';
import { csrfProtection } from '../utils/csrfProtection';

// Create axios instance with default configuration
const httpClient = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: config.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for CSRF protection
});

// Request interceptor to add auth token and CSRF protection
httpClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = tokenStorage.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add CSRF token using protection utility
    const csrfToken = csrfProtection.getToken();
    if (csrfToken) {
      config.headers[config.CSRF_TOKEN_HEADER] = csrfToken;
    }

    // Add request timestamp for replay attack prevention
    config.headers['X-Request-Timestamp'] = Date.now().toString();

    // Log request in development
    if (config.isDevelopment && !config.url?.includes('/auth/refresh')) {
      console.log(`🔄 ${config.method?.toUpperCase()} ${config.url}`, {
        headers: config.headers,
        data: config.data
      });
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh and error handling
httpClient.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (config.isDevelopment && !response.config.url?.includes('/auth/refresh')) {
      console.log(`✅ ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 (Unauthorized) - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = tokenStorage.getRefreshToken();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Attempt to refresh token
        const response = await axios.post(`${config.API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;

        // Store new tokens
        tokenStorage.setToken(access_token);
        if (newRefreshToken) {
          tokenStorage.setRefreshToken(newRefreshToken);
        }

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return httpClient(originalRequest);

      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        
        // Clear all stored data and redirect to login
        tokenStorage.clearAll();
        
        // Dispatch custom event for auth context to handle
        window.dispatchEvent(new CustomEvent('auth:token-expired'));
        
        return Promise.reject(refreshError);
      }
    }

    // Handle 403 (Forbidden) - CSRF token issues
    if (error.response?.status === 403) {
      const csrfError = error.response?.data?.message?.includes('CSRF') || 
                       error.response?.statusText?.includes('Forbidden');
      if (csrfError) {
        console.error('CSRF token validation failed');
        // Handle CSRF error using protection utility
        csrfProtection.handleCSRFError();
        return Promise.reject(new Error('CSRF token validation failed. Please try again.'));
      }
    }

    // Handle network errors
    if (!error.response) {
      const networkError = new Error('Network error - please check your connection');
      networkError.code = 'NETWORK_ERROR';
      return Promise.reject(networkError);
    }

    // Handle rate limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const retryError = new Error(`Rate limited. Please try again in ${retryAfter || 60} seconds.`);
      retryError.code = 'RATE_LIMITED';
      retryError.retryAfter = retryAfter;
      return Promise.reject(retryError);
    }

    // Enhanced error logging
    const errorDetails = {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data,
      message: error.message
    };

    if (config.isDevelopment) {
      console.error('API Error:', errorDetails);
    }

    // Create user-friendly error message
    const userMessage = getUserFriendlyErrorMessage(error);
    const enhancedError = new Error(userMessage);
    enhancedError.originalError = error;
    enhancedError.details = errorDetails;

    return Promise.reject(enhancedError);
  }
);

// This function is now handled by csrfProtection utility

// Helper function to create user-friendly error messages
function getUserFriendlyErrorMessage(error) {
  const status = error.response?.status;
  const defaultMessage = error.response?.data?.message || error.message;

  switch (status) {
    case 400:
      return 'Invalid request. Please check your input and try again.';
    case 401:
      return 'Your session has expired. Please log in again.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 409:
      return 'This action conflicts with existing data. Please refresh and try again.';
    case 422:
      return defaultMessage || 'Validation error. Please check your input.';
    case 429:
      return 'Too many requests. Please wait a moment before trying again.';
    case 500:
      return 'Server error. Please try again later.';
    case 502:
    case 503:
    case 504:
      return 'Service temporarily unavailable. Please try again later.';
    default:
      return defaultMessage || 'An unexpected error occurred. Please try again.';
  }
}

// Export configured client
export default httpClient;

// Export additional utilities
export { getUserFriendlyErrorMessage };  

// Request timeout utility
export const createTimeoutController = (timeoutMs = config.API_TIMEOUT) => {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeoutMs);
  return controller;
};