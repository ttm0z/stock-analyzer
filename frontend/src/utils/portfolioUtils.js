/**
 * Utility functions for portfolio management
 */

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