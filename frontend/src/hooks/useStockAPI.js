// src/hooks/useStockAPI.js - Enhanced version with better debugging
import { useState, useEffect, useCallback } from 'react';
import StockAPI from '../services/stockAPI';

export const useStockSearch = (initialQuery = '') => {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (searchQuery) => {
    console.log('useStockSearch - search called with:', searchQuery);
    
    if (!searchQuery || searchQuery.length < 2) {
      console.log('useStockSearch - Query too short, clearing results');
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const data = await StockAPI.searchStocks(searchQuery);
      console.log('useStockSearch - API returned:', data);
      setResults(data || []);
    } catch (err) {
      console.error('useStockSearch - Error:', err);
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('useStockSearch - Query changed to:', query);
    if (query) {
      const debounceTimer = setTimeout(() => search(query), 300);
      return () => clearTimeout(debounceTimer);
    } else {
      setResults([]);
    }
  }, [query, search]);

  return {
    query,
    setQuery,
    results,
    loading,
    error,
    search
  };
};

export const useStockQuote = (symbol) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchQuote = useCallback(async (stockSymbol) => {
    console.log('useStockQuote - fetchQuote called with:', stockSymbol);
    
    if (!stockSymbol) {
      console.log('useStockQuote - No symbol provided');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const quote = await StockAPI.getStockQuote(stockSymbol);
      console.log('useStockQuote - API returned:', quote);
      setData(quote);
    } catch (err) {
      console.error('useStockQuote - Error:', err);
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('useStockQuote - Symbol changed to:', symbol);
    if (symbol) {
      fetchQuote(symbol);
    }
  }, [symbol, fetchQuote]);

  console.log('useStockQuote - Current state:', { data, loading, error });
  
  return {
    data,
    loading,
    error,
    refetch: () => fetchQuote(symbol)
  };
};

export const useCompanyProfile = (symbol) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('useCompanyProfile - Symbol changed to:', symbol);
    
    if (!symbol) {
      console.log('useCompanyProfile - No symbol provided');
      return;
    }
    
    let cancelled = false;
    
    const fetchProfile = async () => {
      console.log('useCompanyProfile - Fetching profile for:', symbol);
      setLoading(true);
      setError(null);
      
      try {
        const profile = await StockAPI.getCompanyProfile(symbol);
        console.log('useCompanyProfile - API returned:', profile);
        
        if (!cancelled) {
          setData(profile);
        }
      } catch (err) {
        console.error('useCompanyProfile - Error:', err);
        if (!cancelled) {
          setError(err.message);
          setData(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchProfile();
    
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return { data, loading, error };
};

export const useBatchQuotes = (symbols = []) => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBatchQuotes = useCallback(async (symbolList) => {
    console.log('useBatchQuotes - fetchBatchQuotes called with:', symbolList);
    
    if (!symbolList || symbolList.length === 0) {
      console.log('useBatchQuotes - No symbols provided');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const quotes = await StockAPI.getBatchQuotes(symbolList);
      console.log('useBatchQuotes - API returned:', quotes);
      setData(quotes);
    } catch (err) {
      console.error('useBatchQuotes - Error:', err);
      setError(err.message);
      setData({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('useBatchQuotes - Symbols changed to:', symbols);
    if (symbols.length > 0) {
      fetchBatchQuotes(symbols);
    }
  }, [symbols, fetchBatchQuotes]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchBatchQuotes(symbols)
  };
};

export const useIncomeStatement = (symbol, period = 'annual', limit = 5) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('useIncomeStatement - Parameters changed:', { symbol, period, limit });
    
    if (!symbol) {
      console.log('useIncomeStatement - No symbol provided');
      return;
    }
    
    let cancelled = false;
    
    const fetchIncomeStatement = async () => {
      console.log('useIncomeStatement - Fetching for:', symbol);
      setLoading(true);
      setError(null);
      
      try {
        const statements = await StockAPI.getIncomeStatement(symbol, period, limit);
        console.log('useIncomeStatement - API returned:', statements);
        
        if (!cancelled) {
          setData(statements);
        }
      } catch (err) {
        console.error('useIncomeStatement - Error:', err);
        if (!cancelled) {
          setError(err.message);
          setData(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchIncomeStatement();
    
    return () => {
      cancelled = true;
    };
  }, [symbol, period, limit]);

  return { data, loading, error };
};

export const useMarketNews = (limit = 50, tickers = null) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchNews = useCallback(async (newsLimit, newsTickers) => {
    console.log('useMarketNews - fetchNews called with:', { newsLimit, newsTickers });
    
    setLoading(true);
    setError(null);
    
    try {
      const news = await StockAPI.getMarketNews(newsLimit, newsTickers);
      console.log('useMarketNews - API returned:', news);
      setData(news || []);
    } catch (err) {
      console.error('useMarketNews - Error:', err);
      setError(err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('useMarketNews - Parameters changed:', { limit, tickers });
    fetchNews(limit, tickers);
  }, [limit, tickers, fetchNews]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchNews(limit, tickers)
  };
};

export const useHistoricalData = (symbol, fromDate = null, toDate = null) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHistorical = useCallback(async (stockSymbol, from, to) => {
    console.log('useHistoricalData - fetchHistorical called with:', { stockSymbol, from, to });
    
    if (!stockSymbol) {
      console.log('useHistoricalData - No symbol provided');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const historical = await StockAPI.getHistoricalData(stockSymbol, from, to);
      console.log('useHistoricalData - API returned:', historical);
      setData(historical || []);
    } catch (err) {
      console.error('useHistoricalData - Error:', err);
      setError(err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('useHistoricalData - Parameters changed:', { symbol, fromDate, toDate });
    if (symbol) {
      fetchHistorical(symbol, fromDate, toDate);
    }
  }, [symbol, fromDate, toDate, fetchHistorical]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchHistorical(symbol, fromDate, toDate)
  };
};