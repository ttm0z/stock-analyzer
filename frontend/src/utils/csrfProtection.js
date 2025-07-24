import { config } from '../config/environment';

class CSRFProtection {
  constructor() {
    this.token = null;
    this.tokenExpiry = null;
  }

  // Initialize CSRF protection on app start
  async initialize() {
    await this.refreshToken();
    
    // Set up periodic token refresh (every 30 minutes)
    setInterval(() => {
      this.refreshToken();
    }, 30 * 60 * 1000);
  }

  // Get CSRF token from various sources
  getToken() {
    // 1. Check if we have a valid cached token
    if (this.token && this.tokenExpiry && Date.now() < this.tokenExpiry) {
      return this.token;
    }

    // 2. Try to get token from meta tag (set by server)
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (metaToken) {
      this.token = metaToken;
      this.tokenExpiry = Date.now() + (30 * 60 * 1000); // 30 minutes
      return metaToken;
    }

    // 3. Try to get token from cookie
    const cookieToken = this.getTokenFromCookie();
    if (cookieToken) {
      this.token = cookieToken;
      this.tokenExpiry = Date.now() + (30 * 60 * 1000);
      return cookieToken;
    }

    // 4. No token available
    return null;
  }

  // Extract CSRF token from cookies
  getTokenFromCookie() {
    const match = document.cookie.match(/csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  // Refresh CSRF token from server
  async refreshToken() {
    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/csrf-token`, {
        method: 'GET',
        credentials: 'include', // Include cookies
        headers: {
          'Accept': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.csrf_token) {
          this.token = data.csrf_token;
          this.tokenExpiry = Date.now() + (30 * 60 * 1000); // 30 minutes
          
          // Update meta tag for other parts of the app
          let metaTag = document.querySelector('meta[name="csrf-token"]');
          if (!metaTag) {
            metaTag = document.createElement('meta');
            metaTag.name = 'csrf-token';
            document.head.appendChild(metaTag);
          }
          metaTag.content = this.token;
          
          if (config.isDevelopment) {
            console.log('🛡️ CSRF token refreshed');
          }
        }
      }
    } catch (error) {
      console.error('Failed to refresh CSRF token:', error);
    }
  }

  // Validate CSRF token format
  isValidToken(token) {
    // Basic validation - should be a reasonable length and contain valid characters
    return token && 
           typeof token === 'string' && 
           token.length >= 16 && 
           token.length <= 256 &&
           /^[a-zA-Z0-9+/=_-]+$/.test(token);
  }

  // Add CSRF protection to form data
  addToFormData(formData) {
    const token = this.getToken();
    if (token && this.isValidToken(token)) {
      formData.append('_token', token);
    }
    return formData;
  }

  // Add CSRF protection to headers
  addToHeaders(headers = {}) {
    const token = this.getToken();
    if (token && this.isValidToken(token)) {
      headers[config.CSRF_TOKEN_HEADER] = token;
    }
    return headers;
  }

  // Create a CSRF-protected form
  createProtectedForm(action, method = 'POST') {
    const form = document.createElement('form');
    form.action = action;
    form.method = method;

    const token = this.getToken();
    if (token && this.isValidToken(token)) {
      const tokenInput = document.createElement('input');
      tokenInput.type = 'hidden';
      tokenInput.name = '_token';
      tokenInput.value = token;
      form.appendChild(tokenInput);
    }

    return form;
  }

  // Handle CSRF token mismatch errors
  handleCSRFError() {
    console.warn('CSRF token mismatch - refreshing token');
    this.token = null;
    this.tokenExpiry = null;
    
    // Try to refresh the token
    this.refreshToken().then(() => {
      // Optionally reload the page if token refresh fails
      if (!this.getToken()) {
        console.warn('Failed to refresh CSRF token - reloading page');
        window.location.reload();
      }
    });
  }
}

// Create singleton instance
export const csrfProtection = new CSRFProtection();

// Utility functions
export const getCSRFToken = () => csrfProtection.getToken();
export const addCSRFToHeaders = (headers) => csrfProtection.addToHeaders(headers);
export const addCSRFToFormData = (formData) => csrfProtection.addToFormData(formData);
export const createProtectedForm = (action, method) => csrfProtection.createProtectedForm(action, method);

// Initialize CSRF protection when module is imported
if (typeof window !== 'undefined') {
  // Initialize after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      csrfProtection.initialize();
    });
  } else {
    csrfProtection.initialize();
  }
}