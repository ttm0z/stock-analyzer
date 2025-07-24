import httpClient from './httpClient';
import { tokenStorage } from '../utils/secureStorage';
import { config } from '../config/environment';

// Input sanitization utility
const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  return input
    .replace(/[<>"'&]/g, (match) => {
      const escapeMap = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;'
      };
      return escapeMap[match];
    })
    .trim();
};

// Email validation
const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Password strength validation
const isValidPassword = (password) => {
  // At least 8 chars, 1 uppercase, 1 lowercase, 1 number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
};

class AuthAPI {
  static async login(email, password) {
    // Input validation and sanitization
    const sanitizedEmail = sanitizeInput(email);
    const sanitizedPassword = password; // Don't sanitize password as it may contain special chars
    
    if (!isValidEmail(sanitizedEmail)) {
      throw new Error('Please enter a valid email address');
    }
    
    if (!sanitizedPassword || sanitizedPassword.length < 8) {
      throw new Error('Password must be at least 8 characters long');
    }

    try {
      const response = await httpClient.post('/auth/login', {
        email: sanitizedEmail,
        password: sanitizedPassword,
      });
      
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Login error:', error);
      }
      throw error;
    }
  }

  static async register(email, password, firstName, lastName, username) {
    // Input validation and sanitization
    const sanitizedEmail = sanitizeInput(email);
    const sanitizedFirstName = sanitizeInput(firstName);
    const sanitizedLastName = sanitizeInput(lastName);
    const sanitizedUsername = sanitizeInput(username);
    
    if (!isValidEmail(sanitizedEmail)) {
      throw new Error('Please enter a valid email address');
    }
    
    if (!isValidPassword(password)) {
      throw new Error('Password must be at least 8 characters with uppercase, lowercase, and number');
    }
    
    if (!sanitizedFirstName || sanitizedFirstName.length < 2) {
      throw new Error('First name must be at least 2 characters long');
    }
    
    if (!sanitizedLastName || sanitizedLastName.length < 2) {
      throw new Error('Last name must be at least 2 characters long');
    }
    
    if (!sanitizedUsername || sanitizedUsername.length < 3) {
      throw new Error('Username must be at least 3 characters long');
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(sanitizedUsername)) {
      throw new Error('Username can only contain letters, numbers, and underscores');
    }

    try {
      const response = await httpClient.post('/auth/register', {
        email: sanitizedEmail,
        password: password,
        first_name: sanitizedFirstName,
        last_name: sanitizedLastName,
        username: sanitizedUsername
      });
      
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Registration error:', error);
      }
      throw error;
    }
  }

  static async logout() {
    try {
      // Call logout endpoint if token exists
      const token = tokenStorage.getToken();
      if (token) {
        await httpClient.post('/auth/logout');
      }
    } catch (error) {
      // Don't throw error for logout - just log it
      if (config.isDevelopment) {
        console.error('Logout API error:', error);
      }
    } finally {
      // Always clear local storage
      tokenStorage.clearAll();
    }
  }

  static async getProfile() {
    try {
      const response = await httpClient.get('/auth/profile');
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get profile error:', error);
      }
      throw error;
    }
  }

  static async updateProfile(updates) {
    // Sanitize input data
    const sanitizedUpdates = {};
    for (const [key, value] of Object.entries(updates)) {
      if (typeof value === 'string') {
        sanitizedUpdates[key] = sanitizeInput(value);
      } else {
        sanitizedUpdates[key] = value;
      }
    }
    
    // Validate email if being updated
    if (sanitizedUpdates.email && !isValidEmail(sanitizedUpdates.email)) {
      throw new Error('Please enter a valid email address');
    }

    try {
      const response = await httpClient.put('/auth/profile', sanitizedUpdates);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Update profile error:', error);
      }
      throw error;
    }
  }

  static async refreshToken() {
    const refreshToken = tokenStorage.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await httpClient.post('/auth/refresh', {
        refresh_token: refreshToken
      });
      
      return response.data;
    } catch (error) {
      // Clear tokens if refresh fails
      tokenStorage.clearAll();
      if (config.isDevelopment) {
        console.error('Token refresh error:', error);
      }
      throw error;
    }
  }

  // Token management methods (now use secure storage)
  static getToken() {
    return tokenStorage.getToken();
  }

  static setToken(token, expirationMinutes = 60) {
    return tokenStorage.setToken(token, expirationMinutes);
  }
  
  static setRefreshToken(refreshToken) {
    return tokenStorage.setRefreshToken(refreshToken);
  }

  static isAuthenticated() {
    return tokenStorage.isAuthenticated();
  }
  
  static getUser() {
    return tokenStorage.getUser();
  }
  
  static setUser(user) {
    return tokenStorage.setUser(user);
  }
  
  static clearAll() {
    tokenStorage.clearAll();
  }
}

export default AuthAPI;

// Export utilities for testing
export { sanitizeInput, isValidEmail, isValidPassword };