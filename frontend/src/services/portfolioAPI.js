import httpClient from './httpClient';
import { config } from '../config/environment';

// Input sanitization utility
const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  return input.trim();
};

class PortfolioAPI {
  // Create a new portfolio
  static async createPortfolio(portfolioData) {
    try {
      const sanitizedData = {
        name: sanitizeInput(portfolioData.name),
        description: portfolioData.description ? sanitizeInput(portfolioData.description) : null,
        initial_capital: parseFloat(portfolioData.initial_capital),
        portfolio_type: portfolioData.portfolio_type || 'paper',
        currency: portfolioData.currency || 'USD'
      };

      // Validation
      if (!sanitizedData.name || sanitizedData.name.length < 1) {
        throw new Error('Portfolio name is required');
      }

      if (sanitizedData.initial_capital <= 0) {
        throw new Error('Initial capital must be positive');
      }

      const response = await httpClient.post('/portfolios', sanitizedData);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Create portfolio error:', error);
      }
      throw error;
    }
  }

  // Get user portfolios
  static async getPortfolios(filters = {}) {
    try {
      const params = {};
      
      if (filters.portfolio_type) params.portfolio_type = filters.portfolio_type;
      if (filters.is_active !== undefined) params.is_active = filters.is_active;
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;

      const response = await httpClient.get('/portfolios', { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolios error:', error);
      }
      throw error;
    }
  }

  // Get portfolio details with positions
  static async getPortfolioDetails(portfolioId) {
    try {
      const response = await httpClient.get(`/portfolios/${portfolioId}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolio details error:', error);
      }
      throw error;
    }
  }

  // Update portfolio
  static async updatePortfolio(portfolioId, updates) {
    try {
      const sanitizedUpdates = {};
      
      if (updates.name) sanitizedUpdates.name = sanitizeInput(updates.name);
      if (updates.description !== undefined) {
        sanitizedUpdates.description = updates.description ? sanitizeInput(updates.description) : null;
      }
      if (updates.is_active !== undefined) sanitizedUpdates.is_active = updates.is_active;

      const response = await httpClient.put(`/portfolios/${portfolioId}`, sanitizedUpdates);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Update portfolio error:', error);
      }
      throw error;
    }
  }

  // Delete portfolio
  static async deletePortfolio(portfolioId) {
    try {
      const response = await httpClient.delete(`/portfolios/${portfolioId}`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Delete portfolio error:', error);
      }
      throw error;
    }
  }

  // Get portfolio positions
  static async getPortfolioPositions(portfolioId, includeClosed = false) {
    try {
      const params = { include_closed: includeClosed };
      const response = await httpClient.get(`/portfolios/${portfolioId}/positions`, { params });
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolio positions error:', error);
      }
      throw error;
    }
  }

  // Get portfolio performance
  static async getPortfolioPerformance(portfolioId) {
    try {
      const response = await httpClient.get(`/portfolios/${portfolioId}/performance`);
      return response.data;
    } catch (error) {
      if (config.isDevelopment) {
        console.error('Get portfolio performance error:', error);
      }
      throw error;
    }
  }
}

export default PortfolioAPI;