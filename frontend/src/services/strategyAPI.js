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

class StrategyAPI {
  // Get available strategies
  static async getAvailableStrategies() {
    try {
      const response = await httpClient.get('/strategies');
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get available strategies error:', error);
      }
      throw error;
    }
  }

  // Run a strategy
  static async runStrategy(strategyData) {
    try {
      const sanitizedData = {
        strategy_id: sanitizeInput(strategyData.strategy_id),
        universe: strategyData.universe.map(symbol => symbol.trim().toUpperCase()),
        parameters: strategyData.parameters || {},
        portfolio_id: strategyData.portfolio_id ? parseInt(strategyData.portfolio_id) : undefined
      };

      // Validation
      if (!sanitizedData.strategy_id) {
        throw new Error('Strategy ID is required');
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

      const response = await httpClient.post('/strategies/run', sanitizedData);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Run strategy error:', error);
      }
      throw error;
    }
  }

  // Get strategy signals
  static async getStrategySignals(strategyId, filters = {}) {
    try {
      const params = {};
      
      if (filters.symbols && Array.isArray(filters.symbols)) {
        params.symbols = filters.symbols.map(s => s.toUpperCase()).join(',');
      }
      if (filters.lookback_days) params.lookback_days = filters.lookback_days;

      const response = await httpClient.get(`/strategies/${strategyId}/signals`, { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get strategy signals error:', error);
      }
      throw error;
    }
  }

  // Validate strategy parameters
  static async validateStrategyParameters(strategyId, parameters) {
    try {
      const response = await httpClient.post(`/strategies/${strategyId}/validate`, {
        parameters
      });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Validate strategy parameters error:', error);
      }
      throw error;
    }
  }

  // Get strategy details by ID
  static async getStrategyDetails(strategyId) {
    try {
      const strategiesResponse = await this.getAvailableStrategies();
      const strategy = strategiesResponse.strategies.find(s => s.id === strategyId);
      
      if (!strategy) {
        throw new Error(`Strategy ${strategyId} not found`);
      }

      return strategy;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get strategy details error:', error);
      }
      throw error;
    }
  }

  // Create strategy configuration object
  static createStrategyConfig(strategyId, parameters, universe) {
    const config = {
      strategy_id: strategyId,
      parameters: parameters || {},
      universe: universe.map(symbol => symbol.toUpperCase())
    };

    // Add default parameters based on strategy type
    switch (strategyId) {
      case 'moving_average':
        config.parameters = {
          fast_period: 20,
          slow_period: 50,
          position_size: 0.1,
          min_volume: 100000,
          ...config.parameters
        };
        break;
      
      case 'momentum':
        config.parameters = {
          lookback_period: 20,
          top_n_stocks: 10,
          rebalance_frequency: 'monthly',
          ...config.parameters
        };
        break;
      
      case 'buy_hold':
        config.parameters = {
          rebalance_frequency: 'quarterly',
          equal_weight: true,
          ...config.parameters
        };
        break;
    }

    return config;
  }

  // Parse strategy signals for display
  static parseSignalsForDisplay(signals) {
    return signals.map(signal => ({
      ...signal,
      strength_percentage: Math.round(signal.strength * 100),
      signal_color: signal.signal_type === 'BUY' ? 'green' : 
                   signal.signal_type === 'SELL' ? 'red' : 'gray',
      formatted_price: `$${signal.price.toFixed(2)}`,
      formatted_timestamp: new Date(signal.timestamp).toLocaleString()
    }));
  }

  // Calculate strategy performance metrics (client-side)
  static calculateStrategyMetrics(signals, portfolioValue) {
    if (!signals || signals.length === 0) {
      return {
        total_signals: 0,
        buy_signals: 0,
        sell_signals: 0,
        avg_strength: 0,
        estimated_trades: 0
      };
    }

    const buySignals = signals.filter(s => s.signal_type === 'BUY');
    const sellSignals = signals.filter(s => s.signal_type === 'SELL');
    const avgStrength = signals.reduce((sum, s) => sum + s.strength, 0) / signals.length;

    return {
      total_signals: signals.length,
      buy_signals: buySignals.length,
      sell_signals: sellSignals.length,
      avg_strength: avgStrength,
      avg_strength_percentage: Math.round(avgStrength * 100),
      estimated_trades: buySignals.length, // Assume each buy signal results in a trade
      potential_investment: buySignals.reduce((sum, s) => sum + (s.quantity * s.price), 0)
    };
  }
}

export default StrategyAPI;