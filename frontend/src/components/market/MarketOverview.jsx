import { useState, useEffect, useRef } from 'react';
import { 
  TrendingUp,
  TrendingDown,
  Globe,
  BarChart3,
  Activity,
  AlertCircle,
  RefreshCw,
  Search,
  Filter,
  Clock,
  DollarSign,
  Zap,
  Calendar,
  LineChart,
  Eye,
  Star,
  Target,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import StockAPI from '../../services/stockAPI';

const MarketOverview = () => {
  const { user, token } = useAuth();
  const refreshInterval = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  
  const [marketData, setMarketData] = useState({
    indices: [],
    sectors: [],
    currencies: [],
    commodities: [],
    topGainers: [],
    topLosers: [],
    mostActive: [],
    marketSentiment: null,
    economicIndicators: [],
    marketStatus: null
  });

  const [watchlist, setWatchlist] = useState([]);

  useEffect(() => {
    if (user && token) {
      loadMarketData();
      loadWatchlist();
      
      if (autoRefresh) {
        startAutoRefresh();
      }
    }
    
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, [user, token, autoRefresh]);

  const startAutoRefresh = () => {
    if (refreshInterval.current) {
      clearInterval(refreshInterval.current);
    }
    
    refreshInterval.current = setInterval(() => {
      loadMarketData(false); // Silent refresh
    }, 30000); // Refresh every 30 seconds
  };

  const loadMarketData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);
      
      // Simulate API calls with enhanced mock data
      const [indicesData, sectorsData, gainersData, losersData, activeData] = await Promise.all([
        loadIndicesData(),
        loadSectorsData(),
        loadTopGainers(),
        loadTopLosers(),
        loadMostActive()
      ]);
      
      setMarketData({
        indices: indicesData,
        sectors: sectorsData,
        currencies: getCurrencyData(),
        commodities: getCommodityData(),
        topGainers: gainersData,
        topLosers: losersData,
        mostActive: activeData,
        marketSentiment: getMarketSentiment(),
        economicIndicators: getEconomicIndicators(),
        marketStatus: getCurrentMarketStatus()
      });
      
      setLastUpdated(new Date());
      
    } catch (error) {
      console.error('Failed to load market data:', error);
      setError('Failed to load market data. Please try again.');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const loadWatchlist = async () => {
    try {
      // Load user's watchlist (simulate with localStorage for now)
      const saved = localStorage.getItem(`watchlist_${user?.id}`);
      if (saved) {
        setWatchlist(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load watchlist:', error);
    }
  };

  const loadIndicesData = async () => {
    // Enhanced mock data with more realistic fluctuations
    const baseIndices = [
      { name: 'S&P 500', symbol: 'SPX', baseValue: 4756.50 },
      { name: 'NASDAQ', symbol: 'IXIC', baseValue: 14845.12 },
      { name: 'Dow Jones', symbol: 'DJI', baseValue: 37689.54 },
      { name: 'Russell 2000', symbol: 'RUT', baseValue: 2089.23 },
      { name: 'VIX', symbol: 'VIX', baseValue: 18.45 },
      { name: 'FTSE 100', symbol: 'UKX', baseValue: 7420.30 }
    ];
    
    return baseIndices.map(index => {
      const changePercent = (Math.random() - 0.5) * 4; // -2% to +2%
      const change = (index.baseValue * changePercent) / 100;
      const value = index.baseValue + change;
      
      return {
        ...index,
        value: value,
        change: change,
        changePercent: changePercent,
        volume: Math.floor(Math.random() * 1000000000) + 500000000,
        dayHigh: value + Math.abs(change) * 0.5,
        dayLow: value - Math.abs(change) * 0.5
      };
    });
  };

  const loadSectorsData = async () => {
    const sectors = [
      'Technology', 'Healthcare', 'Financials', 'Energy', 
      'Consumer Discretionary', 'Industrials', 'Materials', 
      'Utilities', 'Real Estate', 'Communication Services', 
      'Consumer Staples'
    ];
    
    return sectors.map(name => {
      const change = (Math.random() - 0.5) * 6; // -3% to +3%
      return {
        name,
        change,
        performance: change > 1 ? 'strong' : change > -1 ? 'moderate' : 'weak',
        marketCap: Math.floor(Math.random() * 2000) + 500 + 'B',
        companies: Math.floor(Math.random() * 100) + 50
      };
    });
  };

  const loadTopGainers = async () => {
    const stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'];
    return stocks.map(symbol => ({
      symbol,
      name: `${symbol} Corp`,
      price: Math.random() * 500 + 50,
      change: Math.random() * 20 + 5,
      changePercent: Math.random() * 15 + 2,
      volume: Math.floor(Math.random() * 10000000) + 1000000
    })).sort((a, b) => b.changePercent - a.changePercent).slice(0, 5);
  };

  const loadTopLosers = async () => {
    const stocks = ['F', 'GE', 'BAC', 'WFC', 'C', 'JPM', 'PFE', 'XOM'];
    return stocks.map(symbol => ({
      symbol,
      name: `${symbol} Corp`,
      price: Math.random() * 200 + 20,
      change: -(Math.random() * 15 + 2),
      changePercent: -(Math.random() * 10 + 1),
      volume: Math.floor(Math.random() * 20000000) + 2000000
    })).sort((a, b) => a.changePercent - b.changePercent).slice(0, 5);
  };

  const loadMostActive = async () => {
    const stocks = ['SPY', 'QQQ', 'AMD', 'INTC', 'BABA', 'NIO', 'PLTR', 'SOFI'];
    return stocks.map(symbol => ({
      symbol,
      name: `${symbol} Inc`,
      price: Math.random() * 300 + 30,
      change: (Math.random() - 0.5) * 10,
      changePercent: (Math.random() - 0.5) * 8,
      volume: Math.floor(Math.random() * 50000000) + 10000000
    })).sort((a, b) => b.volume - a.volume).slice(0, 5);
  };

  const getCurrencyData = () => [
    { pair: 'EUR/USD', rate: 1.0875 + (Math.random() - 0.5) * 0.02, change: (Math.random() - 0.5) * 0.01 },
    { pair: 'GBP/USD', rate: 1.2634 + (Math.random() - 0.5) * 0.03, change: (Math.random() - 0.5) * 0.01 },
    { pair: 'USD/JPY', rate: 148.45 + (Math.random() - 0.5) * 2, change: (Math.random() - 0.5) * 1 },
    { pair: 'USD/CAD', rate: 1.3456 + (Math.random() - 0.5) * 0.02, change: (Math.random() - 0.5) * 0.01 },
    { pair: 'AUD/USD', rate: 0.6789 + (Math.random() - 0.5) * 0.02, change: (Math.random() - 0.5) * 0.01 }
  ];

  const getCommodityData = () => [
    { name: 'Gold', price: 2034.50 + (Math.random() - 0.5) * 50, change: (Math.random() - 0.5) * 20, unit: '/oz' },
    { name: 'Silver', price: 24.78 + (Math.random() - 0.5) * 2, change: (Math.random() - 0.5) * 1, unit: '/oz' },
    { name: 'Crude Oil', price: 78.34 + (Math.random() - 0.5) * 5, change: (Math.random() - 0.5) * 3, unit: '/bbl' },
    { name: 'Natural Gas', price: 2.87 + (Math.random() - 0.5) * 0.5, change: (Math.random() - 0.5) * 0.3, unit: '/MMBtu' },
    { name: 'Copper', price: 3.85 + (Math.random() - 0.5) * 0.3, change: (Math.random() - 0.5) * 0.2, unit: '/lb' }
  ];

  const getMarketSentiment = () => {
    const sentiments = ['Bullish', 'Bearish', 'Neutral'];
    const sentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
    return {
      overall: sentiment,
      score: Math.random() * 100,
      fearGreedIndex: Math.floor(Math.random() * 100),
      description: `Market sentiment is currently ${sentiment.toLowerCase()} based on recent trading activity.`
    };
  };

  const getEconomicIndicators = () => [
    { name: 'Unemployment Rate', value: '3.7%', change: -0.1, period: 'Dec 2024' },
    { name: 'Inflation Rate', value: '3.2%', change: 0.2, period: 'Dec 2024' },
    { name: 'GDP Growth', value: '2.4%', change: 0.1, period: 'Q4 2024' },
    { name: 'Federal Funds Rate', value: '5.25%', change: 0, period: 'Current' }
  ];

  const getCurrentMarketStatus = () => {
    const now = new Date();
    const hour = now.getHours();
    const isWeekend = now.getDay() === 0 || now.getDay() === 6;
    
    if (isWeekend) {
      return { status: 'Closed', message: 'Markets closed for weekend', color: 'red' };
    } else if (hour >= 9 && hour < 16) {
      return { status: 'Open', message: 'Markets are open', color: 'green' };
    } else if (hour >= 4 && hour < 9) {
      return { status: 'Pre-Market', message: 'Pre-market trading', color: 'yellow' };
    } else if (hour >= 16 && hour < 20) {
      return { status: 'After-Hours', message: 'After-hours trading', color: 'yellow' };
    } else {
      return { status: 'Closed', message: 'Markets closed', color: 'red' };
    }
  };

  const addToWatchlist = (symbol) => {
    const newWatchlist = [...watchlist, symbol];
    setWatchlist(newWatchlist);
    localStorage.setItem(`watchlist_${user?.id}`, JSON.stringify(newWatchlist));
  };

  const removeFromWatchlist = (symbol) => {
    const newWatchlist = watchlist.filter(s => s !== symbol);
    setWatchlist(newWatchlist);
    localStorage.setItem(`watchlist_${user?.id}`, JSON.stringify(newWatchlist));
  };

  const formatNumber = (num, decimals = 2) => {
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: decimals, 
      maximumFractionDigits: decimals 
    });
  };

  const formatVolume = (volume) => {
    if (volume >= 1e9) return (volume / 1e9).toFixed(1) + 'B';
    if (volume >= 1e6) return (volume / 1e6).toFixed(1) + 'M';
    if (volume >= 1e3) return (volume / 1e3).toFixed(1) + 'K';
    return volume.toString();
  };

  const filteredStocks = () => {
    let stocks = [];
    
    switch (selectedFilter) {
      case 'gainers':
        stocks = marketData.topGainers;
        break;
      case 'losers':
        stocks = marketData.topLosers;
        break;
      case 'active':
        stocks = marketData.mostActive;
        break;
      default:
        stocks = [...marketData.topGainers, ...marketData.topLosers, ...marketData.mostActive];
    }
    
    if (searchQuery) {
      stocks = stocks.filter(stock => 
        stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return stocks;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading market data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => loadMarketData()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Market Overview</h1>
              <div className="flex items-center mt-2 space-x-4">
                <p className="text-sm text-gray-600">
                  Global market indices, sectors, and economic indicators
                </p>
                {lastUpdated && (
                  <div className="flex items-center text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                marketData.marketStatus?.color === 'green' ? 'bg-green-100 text-green-800' :
                marketData.marketStatus?.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  marketData.marketStatus?.color === 'green' ? 'bg-green-500' :
                  marketData.marketStatus?.color === 'yellow' ? 'bg-yellow-500' :
                  'bg-red-500'
                } ${marketData.marketStatus?.status === 'Open' ? 'animate-pulse' : ''}`}></div>
                {marketData.marketStatus?.status}
              </div>
              
              <label className="flex items-center text-sm">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mr-2"
                />
                Auto-refresh
              </label>
              
              <button
                onClick={() => loadMarketData()}
                className="inline-flex items-center px-3 py-2 border-2 border-gray-500 shadow-md text-sm leading-4 font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 transition-all duration-200 transform hover:scale-105"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Market Sentiment Banner */}
        {marketData.marketSentiment && (
          <div className="mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Activity className="h-6 w-6 text-blue-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Market Sentiment: {marketData.marketSentiment.overall}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {marketData.marketSentiment.description}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {Math.round(marketData.marketSentiment.score)}
                </div>
                <div className="text-xs text-gray-500">Fear & Greed: {marketData.marketSentiment.fearGreedIndex}</div>
              </div>
            </div>
          </div>
        )}

        {/* Major Indices */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Major Indices</h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {marketData.indices.map((index) => (
              <div key={index.symbol} className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BarChart3 className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="ml-3 w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-500 truncate">
                            {index.name}
                          </p>
                          <p className="text-lg font-semibold text-gray-900">
                            {formatNumber(index.value)}
                          </p>
                        </div>
                        <button
                          onClick={() => watchlist.includes(index.symbol) ? 
                            removeFromWatchlist(index.symbol) : 
                            addToWatchlist(index.symbol)
                          }
                          className={`p-1 rounded ${
                            watchlist.includes(index.symbol) 
                              ? 'text-yellow-500 hover:text-yellow-600' 
                              : 'text-gray-400 hover:text-gray-500'
                          }`}
                        >
                          <Star className="h-4 w-4" />
                        </button>
                      </div>
                      <div className={`flex items-center text-sm ${
                        index.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {index.change >= 0 ? (
                          <ArrowUp className="h-3 w-3 mr-1" />
                        ) : (
                          <ArrowDown className="h-3 w-3 mr-1" />
                        )}
                        {index.change >= 0 ? '+' : ''}{formatNumber(index.change)} 
                        ({index.changePercent >= 0 ? '+' : ''}{formatNumber(index.changePercent)}%)
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Vol: {formatVolume(index.volume)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Movers Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Top Movers</h2>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search stocks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                className="border border-gray-300 rounded-md text-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All</option>
                <option value="gainers">Top Gainers</option>
                <option value="losers">Top Losers</option>
                <option value="active">Most Active</option>
              </select>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-gray-200">
              {/* Top Gainers */}
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <TrendingUp className="h-5 w-5 text-green-500 mr-2" />
                  Top Gainers
                </h3>
                <div className="space-y-3">
                  {marketData.topGainers.map((stock, index) => (
                    <div key={stock.symbol} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{stock.symbol}</p>
                          <p className="text-xs text-gray-500">${formatNumber(stock.price)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-green-600">
                          +{formatNumber(stock.changePercent)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          Vol: {formatVolume(stock.volume)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Losers */}
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <TrendingDown className="h-5 w-5 text-red-500 mr-2" />
                  Top Losers
                </h3>
                <div className="space-y-3">
                  {marketData.topLosers.map((stock, index) => (
                    <div key={stock.symbol} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{stock.symbol}</p>
                          <p className="text-xs text-gray-500">${formatNumber(stock.price)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-red-600">
                          {formatNumber(stock.changePercent)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          Vol: {formatVolume(stock.volume)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Most Active */}
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Zap className="h-5 w-5 text-blue-500 mr-2" />
                  Most Active
                </h3>
                <div className="space-y-3">
                  {marketData.mostActive.map((stock, index) => (
                    <div key={stock.symbol} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-xs text-gray-500 w-4">{index + 1}</span>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{stock.symbol}</p>
                          <p className="text-xs text-gray-500">${formatNumber(stock.price)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-medium ${
                          stock.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {stock.changePercent >= 0 ? '+' : ''}{formatNumber(stock.changePercent)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          Vol: {formatVolume(stock.volume)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sector Performance */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Sector Performance</h2>
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {marketData.sectors.map((sector) => (
                <li key={sector.name}>
                  <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center">
                      <div className={`h-3 w-3 rounded-full mr-4 ${
                        sector.performance === 'strong' ? 'bg-green-500' :
                        sector.performance === 'moderate' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{sector.name}</p>
                        <p className="text-xs text-gray-500">
                          {sector.companies} companies • {sector.marketCap} market cap
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      {sector.change >= 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-500 mr-2" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500 mr-2" />
                      )}
                      <span className={`text-sm font-medium ${
                        sector.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {sector.change >= 0 ? '+' : ''}{formatNumber(sector.change)}%
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Economic Indicators */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Economic Indicators</h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {marketData.economicIndicators.map((indicator) => (
              <div key={indicator.name} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BarChart3 className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {indicator.name}
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {indicator.value}
                        </dd>
                        <dd className={`text-sm flex items-center ${
                          indicator.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {indicator.change !== 0 && (
                            <>
                              {indicator.change >= 0 ? (
                                <ArrowUp className="h-3 w-3 mr-1" />
                              ) : (
                                <ArrowDown className="h-3 w-3 mr-1" />
                              )}
                              {indicator.change >= 0 ? '+' : ''}{formatNumber(indicator.change, 1)}
                            </>
                          )}
                          <span className="text-xs text-gray-500 ml-2">{indicator.period}</span>
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Currencies and Commodities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Currencies */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-5 border-b border-gray-200">
              <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                <Globe className="h-5 w-5 mr-2" />
                Currency Exchange Rates
              </h3>
            </div>
            <div className="px-6 py-4">
              <div className="space-y-4">
                {marketData.currencies.map((currency) => (
                  <div key={currency.pair} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{currency.pair}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {formatNumber(currency.rate, 4)}
                      </p>
                      <p className={`text-xs flex items-center ${
                        currency.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {currency.change >= 0 ? (
                          <ArrowUp className="h-3 w-3 mr-1" />
                        ) : (
                          <ArrowDown className="h-3 w-3 mr-1" />
                        )}
                        {currency.change >= 0 ? '+' : ''}{formatNumber(currency.change, 4)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Commodities */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-5 border-b border-gray-200">
              <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center">
                <DollarSign className="h-5 w-5 mr-2" />
                Commodities
              </h3>
            </div>
            <div className="px-6 py-4">
              <div className="space-y-4">
                {marketData.commodities.map((commodity) => (
                  <div key={commodity.name} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{commodity.name}</p>
                      <p className="text-xs text-gray-500">{commodity.unit}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        ${formatNumber(commodity.price)}
                      </p>
                      <p className={`text-xs flex items-center ${
                        commodity.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {commodity.change >= 0 ? (
                          <ArrowUp className="h-3 w-3 mr-1" />
                        ) : (
                          <ArrowDown className="h-3 w-3 mr-1" />
                        )}
                        {commodity.change >= 0 ? '+' : ''}{formatNumber(commodity.change)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;