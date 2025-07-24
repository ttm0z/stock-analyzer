/**
 * Utility functions for portfolio URL handling and management
 */

/**
 * Converts a portfolio name to a URL-safe slug
 * @param {string} name - Portfolio name
 * @returns {string} URL-safe slug
 */
export const portfolioNameToSlug = (name) => {
  if (!name || typeof name !== 'string') return '';
  
  return name
    .toLowerCase()
    .trim()
    // Replace spaces and special characters with hyphens
    .replace(/[^a-z0-9]+/g, '-')
    // Remove leading/trailing hyphens
    .replace(/^-+|-+$/g, '')
    // Limit length
    .slice(0, 50);
};

/**
 * Converts a URL slug back to a readable portfolio name format
 * @param {string} slug - URL slug
 * @returns {string} Readable name
 */
export const slugToPortfolioName = (slug) => {
  if (!slug || typeof slug !== 'string') return '';
  
  return slug
    .replace(/-/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Generates portfolio detail URL
 * @param {string} username - User's username
 * @param {string} portfolioName - Portfolio name
 * @returns {string} Portfolio detail URL
 */
export const generatePortfolioUrl = (username, portfolioName) => {
  if (!username || !portfolioName) return '/portfolios';
  
  const slug = portfolioNameToSlug(portfolioName);
  return `/portfolios/${username}/${slug}`;
};

/**
 * Parses portfolio URL parameters
 * @param {string} username - Username from URL
 * @param {string} portfolioSlug - Portfolio slug from URL
 * @returns {object} Parsed parameters
 */
export const parsePortfolioUrl = (username, portfolioSlug) => {
  return {
    username: username || '',
    portfolioSlug: portfolioSlug || '',
    portfolioName: slugToPortfolioName(portfolioSlug)
  };
};

/**
 * Validates if user can access portfolio
 * @param {object} currentUser - Current user object
 * @param {string} urlUsername - Username from URL
 * @returns {boolean} Can access portfolio
 */
export const canAccessPortfolio = (currentUser, urlUsername) => {
  if (!currentUser || !urlUsername) return false;
  return currentUser.username === urlUsername;
};

/**
 * Finds portfolio by name (case-insensitive)
 * @param {Array} portfolios - Array of portfolio objects
 * @param {string} portfolioName - Portfolio name to find
 * @returns {object|null} Found portfolio or null
 */
export const findPortfolioByName = (portfolios, portfolioName) => {
  if (!portfolios || !Array.isArray(portfolios) || !portfolioName) return null;
  
  const normalizedName = portfolioName.toLowerCase().trim();
  
  return portfolios.find(portfolio => 
    portfolio.name && portfolio.name.toLowerCase().trim() === normalizedName
  ) || null;
};

/**
 * Formats currency value
 * @param {number} value - Numeric value
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, currency = 'USD') => {
  if (typeof value !== 'number' || isNaN(value)) return '$0.00';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(value);
};

/**
 * Formats percentage value
 * @param {number} value - Percentage value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 2) => {
  if (typeof value !== 'number' || isNaN(value)) return '0.00%';
  
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
};

/**
 * Calculates portfolio performance metrics
 * @param {object} portfolio - Portfolio object
 * @returns {object} Performance metrics
 */
export const calculatePortfolioMetrics = (portfolio) => {
  if (!portfolio) return {};
  
  const initialCapital = portfolio.initial_capital || 0;
  const currentValue = portfolio.total_value || 0;
  const totalReturn = currentValue - initialCapital;
  const returnPercentage = initialCapital > 0 ? (totalReturn / initialCapital) * 100 : 0;
  
  return {
    initialCapital,
    currentValue,
    totalReturn,
    returnPercentage,
    cashBalance: portfolio.cash_balance || 0,
    investedValue: portfolio.invested_value || 0,
    unrealizedPnL: portfolio.unrealized_pnl || 0,
    realizedPnL: portfolio.realized_pnl || 0
  };
};