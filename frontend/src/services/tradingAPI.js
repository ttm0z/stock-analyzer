import httpClient from './httpClient';
import { config } from '../config/environment';

// Symbol validation
const isValidSymbol = (symbol) => {
  if (!symbol || typeof symbol !== 'string') return false;
  return /^[A-Z]{1,5}(\.[A-Z]{1,2})?$/.test(symbol.toUpperCase());
};

class TradingAPI {
  // Execute a trade
  static async executeTrade(tradeData) {
    try {
      const sanitizedData = {
        portfolio_id: parseInt(tradeData.portfolio_id),
        symbol: tradeData.symbol.trim().toUpperCase(),
        side: tradeData.side.toUpperCase(),
        quantity: parseFloat(tradeData.quantity),
        order_type: (tradeData.order_type || 'MARKET').toUpperCase(),
        limit_price: tradeData.limit_price ? parseFloat(tradeData.limit_price) : undefined
      };

      // Validation
      if (!sanitizedData.portfolio_id || sanitizedData.portfolio_id <= 0) {
        throw new Error('Valid portfolio ID is required');
      }

      if (!isValidSymbol(sanitizedData.symbol)) {
        throw new Error('Invalid stock symbol');
      }

      if (!['BUY', 'SELL'].includes(sanitizedData.side)) {
        throw new Error('Side must be BUY or SELL');
      }

      if (sanitizedData.quantity <= 0) {
        throw new Error('Quantity must be positive');
      }

      if (!['MARKET', 'LIMIT'].includes(sanitizedData.order_type)) {
        throw new Error('Order type must be MARKET or LIMIT');
      }

      if (sanitizedData.order_type === 'LIMIT' && !sanitizedData.limit_price) {
        throw new Error('Limit price is required for limit orders');
      }

      // Remove undefined values
      Object.keys(sanitizedData).forEach(key => {
        if (sanitizedData[key] === undefined) {
          delete sanitizedData[key];
        }
      });

      const response = await httpClient.post('/trading/trade', sanitizedData);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Execute trade error:', error);
      }
      throw error;
    }
  }

  // Get trading quote
  static async getTradingQuote(symbol) {
    try {
      const upperSymbol = symbol.toUpperCase();
      
      if (!isValidSymbol(upperSymbol)) {
        throw new Error('Invalid stock symbol');
      }

      const response = await httpClient.get(`/trading/quote/${upperSymbol}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get trading quote error:', error);
      }
      throw error;
    }
  }

  // Get portfolio transactions
  static async getPortfolioTransactions(portfolioId, filters = {}) {
    try {
      const params = {};
      
      if (filters.symbol) params.symbol = filters.symbol.toUpperCase();
      if (filters.side) params.side = filters.side.toUpperCase();
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;

      const response = await httpClient.get(`/trading/portfolios/${portfolioId}/transactions`, { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolio transactions error:', error);
      }
      throw error;
    }
  }

  // Get portfolio orders
  static async getPortfolioOrders(portfolioId, filters = {}) {
    try {
      const params = {};
      
      if (filters.status) params.status = filters.status.toUpperCase();
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;

      const response = await httpClient.get(`/trading/portfolios/${portfolioId}/orders`, { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolio orders error:', error);
      }
      throw error;
    }
  }

  // Get buying power
  static async getBuyingPower(portfolioId) {
    try {
      const response = await httpClient.get(`/trading/portfolios/${portfolioId}/buying-power`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get buying power error:', error);
      }
      throw error;
    }
  }

  // Calculate trade preview (client-side estimation)
  static calculateTradePreview(quantity, price, side, commissionRate = 0.001) {
    try {
      const tradeValue = quantity * price;
      const commission = tradeValue * commissionRate;
      const netAmount = side === 'BUY' ? tradeValue + commission : tradeValue - commission;

      return {
        quantity,
        price,
        trade_value: tradeValue,
        commission,
        net_amount: netAmount,
        side
      };
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Calculate trade preview error:', error);
      }
      throw error;
    }
  }

  // Validate trade before execution
  static validateTrade(tradeData, portfolio, quote) {
    const errors = [];

    if (!tradeData.portfolio_id) {
      errors.push('Portfolio is required');
    }

    if (!tradeData.symbol) {
      errors.push('Stock symbol is required');
    }

    if (!tradeData.side || !['BUY', 'SELL'].includes(tradeData.side.toUpperCase())) {
      errors.push('Valid trade side (BUY/SELL) is required');
    }

    if (!tradeData.quantity || tradeData.quantity <= 0) {
      errors.push('Valid quantity is required');
    }

    if (tradeData.order_type === 'LIMIT' && (!tradeData.limit_price || tradeData.limit_price <= 0)) {
      errors.push('Valid limit price is required for limit orders');
    }

    // Check buying power for BUY orders
    if (tradeData.side === 'BUY' && portfolio && quote) {
      const price = tradeData.order_type === 'LIMIT' ? tradeData.limit_price : quote.price;
      const tradePreview = this.calculateTradePreview(tradeData.quantity, price, 'BUY');
      
      if (portfolio.cash_balance < tradePreview.net_amount) {
        errors.push(`Insufficient funds. Required: $${tradePreview.net_amount.toFixed(2)}, Available: $${portfolio.cash_balance.toFixed(2)}`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

export default TradingAPI;