import { config } from '../config/environment';

class SecureStorage {
  constructor() {
    this.STORAGE_PREFIX = 'stock_analyzer_';
    this.ENCRYPTION_KEY = 'user_session_';
  }

  // XOR-based simple encryption for client-side storage
  // Note: This is NOT cryptographically secure, but provides basic obfuscation
  // Production apps should use server-side session management with httpOnly cookies
  encrypt(text) {
    if (!text) return '';
    const key = this.ENCRYPTION_KEY;
    let result = '';
    for (let i = 0; i < text.length; i++) {
      result += String.fromCharCode(text.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    }
    return btoa(result);
  }

  decrypt(encryptedText) {
    if (!encryptedText) return '';
    try {
      const text = atob(encryptedText);
      const key = this.ENCRYPTION_KEY;
      let result = '';
      for (let i = 0; i < text.length; i++) {
        result += String.fromCharCode(text.charCodeAt(i) ^ key.charCodeAt(i % key.length));
      }
      return result;
    } catch (error) {
      console.error('Failed to decrypt stored data');
      return '';
    }
  }

  // Store data with expiration
  setItem(key, value, expirationMinutes = 60) {
    try {
      const expirationTime = new Date().getTime() + (expirationMinutes * 60 * 1000);
      const dataToStore = {
        value: value,
        expiration: expirationTime,
        timestamp: new Date().getTime()
      };
      
      const encryptedData = this.encrypt(JSON.stringify(dataToStore));
      sessionStorage.setItem(this.STORAGE_PREFIX + key, encryptedData);
      
      if (config.isDevelopment) {
        console.log(`SecureStorage: Stored ${key} with ${expirationMinutes}min expiration`);
      }
    } catch (error) {
      console.error('SecureStorage: Failed to store data', error);
    }
  }

  getItem(key) {
    try {
      const encryptedData = sessionStorage.getItem(this.STORAGE_PREFIX + key);
      if (!encryptedData) return null;

      const decryptedData = this.decrypt(encryptedData);
      if (!decryptedData) return null;

      const parsedData = JSON.parse(decryptedData);
      
      // Check if data has expired
      if (new Date().getTime() > parsedData.expiration) {
        this.removeItem(key);
        if (config.isDevelopment) {
          console.log(`SecureStorage: ${key} expired and removed`);
        }
        return null;
      }

      return parsedData.value;
    } catch (error) {
      console.error('SecureStorage: Failed to retrieve data', error);
      this.removeItem(key); // Clean up corrupted data
      return null;
    }
  }

  removeItem(key) {
    sessionStorage.removeItem(this.STORAGE_PREFIX + key);
    if (config.isDevelopment) {
      console.log(`SecureStorage: Removed ${key}`);
    }
  }

  clear() {
    const keys = Object.keys(sessionStorage);
    keys.forEach(key => {
      if (key.startsWith(this.STORAGE_PREFIX)) {
        sessionStorage.removeItem(key);
      }
    });
    if (config.isDevelopment) {
      console.log('SecureStorage: Cleared all stored data');
    }
  }

  // Check if storage is available
  isAvailable() {
    try {
      const test = 'test';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch (error) {
      console.warn('SecureStorage: SessionStorage not available');
      return false;
    }
  }
}

export const secureStorage = new SecureStorage();

// Token-specific storage utilities
export const tokenStorage = {
  setToken(token, expirationMinutes = 480) {
    if (!token) {
      console.error('TokenStorage: Cannot store empty token');
      return false;
    }
    // Store token with a version to handle expiration changes
    const tokenData = {
      token: token,
      version: '1.0'
    };
    secureStorage.setItem('auth_token', tokenData, expirationMinutes);
    if (config.isDevelopment) {
      console.log(`🔐 Token stored with ${expirationMinutes}min expiration`);
    }
    return true;
  },

  getToken() {
    const tokenData = secureStorage.getItem('auth_token');
    if (!tokenData) {
      if (config.isDevelopment) {
        console.log('🔓 No token found in storage');
      }
      return null;
    }
    
    // Handle old format (string) vs new format (object)
    if (typeof tokenData === 'string') {
      if (config.isDevelopment) {
        console.log('🔑 Retrieved token (old format)');
      }
      return tokenData;
    }
    
    // Return the token from the new format
    const token = tokenData.token || null;
    if (config.isDevelopment) {
      console.log(token ? '🔑 Retrieved token (new format)' : '🔓 Token object exists but no token inside');
    }
    return token;
  },

  removeToken() {
    secureStorage.removeItem('auth_token');
  },

  setRefreshToken(refreshToken, expirationDays = 7) {
    if (!refreshToken) return false;
    secureStorage.setItem('refresh_token', refreshToken, expirationDays * 24 * 60);
    return true;
  },

  getRefreshToken() {
    return secureStorage.getItem('refresh_token');
  },

  removeRefreshToken() {
    secureStorage.removeItem('refresh_token');
  },

  setUser(user) {
    if (!user) return false;
    secureStorage.setItem('user_data', user, 60);
    return true;
  },

  getUser() {
    return secureStorage.getItem('user_data');
  },

  removeUser() {
    secureStorage.removeItem('user_data');
  },

  clearAll() {
    secureStorage.clear();
  },

  isAuthenticated() {
    const token = this.getToken();
    return !!token;
  }
};