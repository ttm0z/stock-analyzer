// frontend/src/services/stockAPI.js
const API_BASE_URL = 'http://localhost:5000/api';

class StockAPI {
  // Your existing search (now cached on backend)
  static async searchStocks(query) {
    const response = await fetch(`${API_BASE_URL}/search?query=${query}`);
    return response.json();
  }

  // Your existing quote (now cached on backend)
  static async getStockQuote(symbol) {
    const response = await fetch(`${API_BASE_URL}/quote/${symbol}`);
    return response.json();
  }

  // NEW: Efficient batch quotes
  static async getBatchQuotes(symbols) {
    const symbolString = symbols.join(',');
    const response = await fetch(`${API_BASE_URL}/quotes?symbols=${symbolString}`);
    return response.json();
  }

  // NEW: Company profile
  static async getCompanyProfile(symbol) {
    const response = await fetch(`${API_BASE_URL}/profile/${symbol}`);
    return response.json();
  }

  // NEW: Financial statements
  static async getIncomeStatement(symbol, period = 'annual', limit = 5) {
    const response = await fetch(
      `${API_BASE_URL}/financials/${symbol}/income-statement?period=${period}&limit=${limit}`
    );
    return response.json();
  }

  // NEW: Market news
  static async getMarketNews(limit = 50, tickers = null) {
    let url = `${API_BASE_URL}/news?limit=${limit}`;
    if (tickers) url += `&tickers=${tickers}`;
    
    const response = await fetch(url);
    return response.json();
  }

  // Your existing historical (now cached on backend)
  static async getHistoricalData(symbol, fromDate = null, toDate = null) {
    let url = `${API_BASE_URL}/historical/${symbol}`;
    const params = new URLSearchParams();
    
    if (fromDate) params.append('from', fromDate);
    if (toDate) params.append('to', toDate);
    
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    return response.json();
  }

  // NEW: Cache management (for admin/dev)
  static async getCacheStats() {
    const response = await fetch(`${API_BASE_URL}/admin/cache/stats`);
    return response.json();
  }
}

export default StockAPI;