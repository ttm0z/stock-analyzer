import httpClient from './httpClient';
import { config } from '../config/environment';

// Input sanitization utility
const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  return input.trim();
};

// Symbol validation
const isValidSymbol = (symbol) => {
  if (!symbol || typeof symbol !== 'string') return false;
  return /^[A-Z]{1,5}(\.[A-Z]{1,2})?$/.test(symbol.toUpperCase());
};

// Date validation
const isValidDate = (dateString) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return false;
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date) && dateString === date.toISOString().split('T')[0];
};

class BacktestAPI {
  // Create and run a new backtest
  static async createBacktest(backtestData) {
    try {
      const sanitizedData = {
        name: sanitizeInput(backtestData.name),
        description: backtestData.description ? sanitizeInput(backtestData.description) : undefined,
        strategy_id: sanitizeInput(backtestData.strategy_id),
        start_date: backtestData.start_date,
        end_date: backtestData.end_date,
        initial_capital: parseFloat(backtestData.initial_capital),
        universe: backtestData.universe.map(symbol => symbol.trim().toUpperCase()),
        strategy_parameters: backtestData.strategy_parameters || {},
        commission_rate: backtestData.commission_rate ? parseFloat(backtestData.commission_rate) : 0.001,
        slippage_rate: backtestData.slippage_rate ? parseFloat(backtestData.slippage_rate) : 0.0005,
        benchmark_symbol: backtestData.benchmark_symbol ? sanitizeInput(backtestData.benchmark_symbol).toUpperCase() : 'SPY'
      };

      // Validation
      if (!sanitizedData.name || sanitizedData.name.length < 1) {
        throw new Error('Backtest name is required');
      }

      if (!sanitizedData.strategy_id) {
        throw new Error('Strategy ID is required');
      }

      if (!isValidDate(sanitizedData.start_date)) {
        throw new Error('Valid start date is required (YYYY-MM-DD format)');
      }

      if (!isValidDate(sanitizedData.end_date)) {
        throw new Error('Valid end date is required (YYYY-MM-DD format)');
      }

      if (new Date(sanitizedData.start_date) >= new Date(sanitizedData.end_date)) {
        throw new Error('Start date must be before end date');
      }

      if (new Date(sanitizedData.end_date) > new Date()) {
        throw new Error('End date cannot be in the future');
      }

      if (sanitizedData.initial_capital <= 0) {
        throw new Error('Initial capital must be positive');
      }

      if (!Array.isArray(sanitizedData.universe) || sanitizedData.universe.length === 0) {
        throw new Error('Universe must be a non-empty array of stock symbols');
      }

      // Validate all symbols
      for (const symbol of sanitizedData.universe) {
        if (!isValidSymbol(symbol)) {
          throw new Error(`Invalid symbol: ${symbol}`);
        }
      }

      // Remove undefined values
      Object.keys(sanitizedData).forEach(key => {
        if (sanitizedData[key] === undefined) {
          delete sanitizedData[key];
        }
      });

      const response = await httpClient.post('/backtests', sanitizedData);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Create backtest error:', error);
      }
      throw error;
    }
  }

  // Get user backtests
  static async getBacktests(filters = {}) {
    try {
      const params = {};
      
      if (filters.status) params.status = filters.status;
      if (filters.strategy_id) params.strategy_id = filters.strategy_id;
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;

      const response = await httpClient.get('/backtests', { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get backtests error:', error);
      }
      throw error;
    }
  }

  // Get backtest results and details
  static async getBacktestResults(backtestId) {
    try {
      const response = await httpClient.get(`/backtests/${backtestId}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get backtest results error:', error);
      }
      throw error;
    }
  }

  // Get backtest status and progress
  static async getBacktestStatus(backtestId) {
    try {
      const response = await httpClient.get(`/backtests/${backtestId}/status`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get backtest status error:', error);
      }
      throw error;
    }
  }

  // Delete a backtest
  static async deleteBacktest(backtestId) {
    try {
      const response = await httpClient.delete(`/backtests/${backtestId}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Delete backtest error:', error);
      }
      throw error;
    }
  }

  // Compare multiple backtests
  static async compareBacktests(backtestIds) {
    try {
      if (!Array.isArray(backtestIds) || backtestIds.length < 2) {
        throw new Error('Must provide at least 2 backtest IDs for comparison');
      }

      const response = await httpClient.post('/backtests/compare', {
        backtest_ids: backtestIds
      });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Compare backtests error:', error);
      }
      throw error;
    }
  }

  // Format backtest results for display
  static formatBacktestResults(backtest) {
    if (!backtest) return null;

    return {
      ...backtest,
      formatted_total_return: `${(backtest.total_return || 0).toFixed(2)}%`,
      formatted_annualized_return: `${(backtest.annualized_return || 0).toFixed(2)}%`,
      formatted_max_drawdown: `${Math.abs(backtest.max_drawdown || 0).toFixed(2)}%`,
      formatted_sharpe_ratio: (backtest.sharpe_ratio || 0).toFixed(2),
      formatted_execution_time: this.formatExecutionTime(backtest.execution_time),
      status_color: this.getStatusColor(backtest.status),
      duration_days: this.calculateBacktestDuration(backtest.start_date, backtest.end_date)
    };
  }

  // Format execution time
  static formatExecutionTime(seconds) {
    if (!seconds) return 'N/A';
    
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
      return `${(seconds / 60).toFixed(1)}m`;
    } else {
      return `${(seconds / 3600).toFixed(1)}h`;
    }
  }

  // Get status color for UI
  static getStatusColor(status) {
    switch (status) {
      case 'completed':
        return 'green';
      case 'running':
        return 'blue';
      case 'pending':
        return 'yellow';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  }

  // Calculate backtest duration in days
  static calculateBacktestDuration(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const timeDiff = end.getTime() - start.getTime();
    return Math.ceil(timeDiff / (1000 * 3600 * 24));
  }

  // Create backtest configuration object
  static createBacktestConfig(strategyId, parameters = {}) {
    const config = {
      strategy_id: strategyId,
      strategy_parameters: parameters,
      commission_rate: 0.001,
      slippage_rate: 0.0005,
      benchmark_symbol: 'SPY'
    };

    // Add strategy-specific defaults
    switch (strategyId) {
      case 'moving_average':
        config.strategy_parameters = {
          fast_period: 20,
          slow_period: 50,
          position_size: 0.1,
          min_volume: 100000,
          ...parameters
        };
        break;
      
      case 'momentum':
        config.strategy_parameters = {
          lookback_period: 20,
          top_n_stocks: 10,
          rebalance_frequency: 'monthly',
          ...parameters
        };
        break;
      
      case 'buy_hold':
        config.strategy_parameters = {
          rebalance_frequency: 'quarterly',
          equal_weight: true,
          ...parameters
        };
        break;
    }

    return config;
  }

  // Calculate performance metrics for comparison
  static calculatePerformanceScore(backtest) {
    if (!backtest || !backtest.sharpe_ratio) return 0;
    
    // Simple scoring based on Sharpe ratio, return, and max drawdown
    const sharpeScore = (backtest.sharpe_ratio || 0) * 30;
    const returnScore = (backtest.total_return || 0) * 0.5;
    const drawdownPenalty = Math.abs(backtest.max_drawdown || 0) * 0.3;
    
    return Math.max(0, sharpeScore + returnScore - drawdownPenalty);
  }

  // Validate backtest parameters
  static validateBacktestParams(params) {
    const errors = [];

    if (!params.name || params.name.trim().length === 0) {
      errors.push('Backtest name is required');
    }

    if (!params.strategy_id) {
      errors.push('Strategy is required');
    }

    if (!params.start_date || !isValidDate(params.start_date)) {
      errors.push('Valid start date is required');
    }

    if (!params.end_date || !isValidDate(params.end_date)) {
      errors.push('Valid end date is required');
    }

    if (params.start_date && params.end_date && new Date(params.start_date) >= new Date(params.end_date)) {
      errors.push('Start date must be before end date');
    }

    if (!params.initial_capital || params.initial_capital <= 0) {
      errors.push('Initial capital must be positive');
    }

    if (!params.universe || !Array.isArray(params.universe) || params.universe.length === 0) {
      errors.push('At least one stock symbol is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

export default BacktestAPI;