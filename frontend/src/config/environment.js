const getEnvVar = (key, fallback = null) => {
  const value = import.meta.env[key];
  if (value === undefined && fallback === null) {
    console.error(`Missing required environment variable: ${key}`);
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value || fallback;
};

export const config = {
  API_BASE_URL: getEnvVar('VITE_API_BASE_URL', 'http://localhost:5000/api'),
  APP_TITLE: getEnvVar('VITE_APP_TITLE', 'Stock Analyzer'),
  APP_ENV: getEnvVar('VITE_APP_ENV', 'development'),
  
  // Security settings
  API_TIMEOUT: parseInt(getEnvVar('VITE_API_TIMEOUT', '30000')),
  CSRF_TOKEN_HEADER: getEnvVar('VITE_CSRF_TOKEN_HEADER', 'X-CSRF-Token'),
  
  // Feature flags
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
  
  // Security headers
  CSP_NONCE: getEnvVar('VITE_CSP_NONCE', null),
};

// Validate critical configuration on app start
export const validateConfig = () => {
  const requiredVars = ['API_BASE_URL'];
  
  for (const varName of requiredVars) {
    if (!config[varName]) {
      throw new Error(`Configuration error: Missing ${varName}`);
    }
  }
  
  // Validate API URL format
  try {
    new URL(config.API_BASE_URL);
  } catch (error) {
    throw new Error(`Configuration error: Invalid API_BASE_URL format`);
  }
  
  if (config.isProduction) {
    console.log('✅ Production configuration validated');
  } else if (config.isDevelopment) {
    console.log('🔧 Development configuration loaded');
  }
};