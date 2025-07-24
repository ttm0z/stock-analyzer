import httpClient from './httpClient';
import { config } from '../config/environment';

// Input sanitization for query parameters
const sanitizeQuery = (query) => {
  if (typeof query !== 'string') return '';
  return query
    .replace(/[^a-zA-Z0-9\s.-]/g, '') // Only allow alphanumeric, spaces, dots, hyphens
    .trim()
    .slice(0, 100); // Limit length
};

// Symbol validation
const isValidSymbol = (symbol) => {
  if (!symbol || typeof symbol !== 'string') return false;
  // Allow 1-5 character stock symbols with optional extensions
  return /^[A-Z]{1,5}(\.[A-Z]{1,2})?$/.test(symbol.toUpperCase());
};

class StockAPI {
  // Search stocks with input validation
  static async searchStocks(query) {
    const sanitizedQuery = sanitizeQuery(query);
    
    if (!sanitizedQuery || sanitizedQuery.length < 1) {
      throw new Error('Search query must be at least 1 character long');
    }
    
    if (sanitizedQuery.length > 50) {
      throw new Error('Search query is too long');
    }

    try {
      const response = await httpClient.get('/search', {
        params: { query: sanitizedQuery }
      });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Search stocks error:', error);
      }
      throw error;
    }
  }

  // Get stock quote with symbol validation
  static async getStockQuote(symbol) {
    const upperSymbol = symbol?.toUpperCase();
    
    if (!isValidSymbol(upperSymbol)) {
      throw new Error('Invalid stock symbol format');
    }

    try {
      const response = await httpClient.get(`/quote/${upperSymbol}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get stock quote error:', error);
      }
      throw error;
    }
  }

  // Get batch quotes with validation
  static async getBatchQuotes(symbols) {
    if (!Array.isArray(symbols) || symbols.length === 0) {
      throw new Error('Symbols must be a non-empty array');
    }
    
    if (symbols.length > 50) {
      throw new Error('Too many symbols requested (max 50)');
    }
    
    // Validate each symbol
    const validSymbols = symbols.map(s => s?.toUpperCase()).filter(isValidSymbol);
    
    if (validSymbols.length === 0) {
      throw new Error('No valid stock symbols provided');
    }

    try {
      const response = await httpClient.get('/quotes', {
        params: { symbols: validSymbols.join(',') }
      });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get batch quotes error:', error);
      }
      throw error;
    }
  }

  // Get company profile
  static async getCompanyProfile(symbol) {
    const upperSymbol = symbol?.toUpperCase();
    
    if (!isValidSymbol(upperSymbol)) {
      throw new Error('Invalid stock symbol format');
    }

    try {
      const response = await httpClient.get(`/profile/${upperSymbol}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get company profile error:', error);
      }
      throw error;
    }
  }

  // Get financial statements
  static async getIncomeStatement(symbol, period = 'annual', limit = 5) {
    const upperSymbol = symbol?.toUpperCase();
    
    if (!isValidSymbol(upperSymbol)) {
      throw new Error('Invalid stock symbol format');
    }
    
    // Validate period
    if (!['annual', 'quarterly'].includes(period)) {
      throw new Error('Period must be "annual" or "quarterly"');
    }
    
    // Validate limit
    const numLimit = parseInt(limit, 10);
    if (isNaN(numLimit) || numLimit < 1 || numLimit > 20) {
      throw new Error('Limit must be between 1 and 20');
    }

    try {
      const response = await httpClient.get(`/financials/${upperSymbol}/income-statement`, {
        params: { period, limit: numLimit }
      });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get income statement error:', error);
      }
      throw error;
    }
  }

  // Get market news
  static async getMarketNews(limit = 50, tickers = null) {
    // Validate limit
    const numLimit = parseInt(limit, 10);
    if (isNaN(numLimit) || numLimit < 1 || numLimit > 100) {
      throw new Error('Limit must be between 1 and 100');
    }
    
    // Validate tickers if provided
    let validTickers = null;
    if (tickers) {
      if (typeof tickers === 'string') {
        validTickers = tickers.split(',').map(t => t.trim().toUpperCase()).filter(isValidSymbol).join(',');
      } else if (Array.isArray(tickers)) {
        validTickers = tickers.map(t => t?.toUpperCase()).filter(isValidSymbol).join(',');
      }
    }

    try {
      const params = { limit: numLimit };
      if (validTickers) {
        params.tickers = validTickers;
      }
      
      const response = await httpClient.get('/news', { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get market news error:', error);
      }
      throw error;
    }
  }

  // Get historical data
  static async getHistoricalData(symbol, fromDate = null, toDate = null) {
    const upperSymbol = symbol?.toUpperCase();
    
    if (!isValidSymbol(upperSymbol)) {
      throw new Error('Invalid stock symbol format');
    }
    
    // Validate dates if provided
    if (fromDate && !isValidDate(fromDate)) {
      throw new Error('Invalid from date format (use YYYY-MM-DD)');
    }
    
    if (toDate && !isValidDate(toDate)) {
      throw new Error('Invalid to date format (use YYYY-MM-DD)');
    }
    
    // Ensure fromDate is before toDate
    if (fromDate && toDate && new Date(fromDate) > new Date(toDate)) {
      throw new Error('From date must be before to date');
    }

    try {
      const params = {};
      if (fromDate) params.from = fromDate;
      if (toDate) params.to = toDate;
      
      const response = await httpClient.get(`/historical/${upperSymbol}`, { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get historical data error:', error);
      }
      throw error;
    }
  }

  // Get cache stats (admin only)
  static async getCacheStats() {
    try {
      const response = await httpClient.get('/admin/cache/stats');
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get cache stats error:', error);
      }
      throw error;
    }
  }
}

// Date validation helper
function isValidDate(dateString) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return false;
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date) && dateString === date.toISOString().split('T')[0];
}

export default StockAPI;

// Export utilities for testing
export { sanitizeQuery, isValidSymbol, isValidDate };