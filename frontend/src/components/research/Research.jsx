import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search,
  TrendingUp,
  TrendingDown,
  Eye,
  Star,
  BarChart3,
  Calendar,
  AlertCircle,
  RefreshCw,
  Filter,
  BookOpen
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import StockAPI from '../../services/stockAPI';

const Research = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [marketData, setMarketData] = useState([]);
  const [topMovers, setTopMovers] = useState({ gainers: [], losers: [] });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState('all');

  useEffect(() => {
    if (user && token) {
      loadResearchData();
    }
  }, [user, token]);

  const loadResearchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for research dashboard
      setMarketData([
        {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          price: 175.43,
          change: 2.15,
          changePercent: 1.24,
          volume: 45234567,
          marketCap: 2750000000000,
          sector: 'Technology',
          rating: 'Buy',
          targetPrice: 190.00
        },
        {
          symbol: 'GOOGL',
          name: 'Alphabet Inc.',
          price: 138.21,
          change: -1.87,
          changePercent: -1.33,
          volume: 23456789,
          marketCap: 1800000000000,
          sector: 'Technology',
          rating: 'Hold',
          targetPrice: 145.00
        },
        {
          symbol: 'TSLA',
          name: 'Tesla Inc.',
          price: 248.76,
          change: 12.34,
          changePercent: 5.22,
          volume: 67890123,
          marketCap: 790000000000,
          sector: 'Consumer Discretionary',
          rating: 'Buy',
          targetPrice: 275.00
        },
        {
          symbol: 'MSFT',
          name: 'Microsoft Corporation',
          price: 378.85,
          change: 4.52,
          changePercent: 1.21,
          volume: 34567890,
          marketCap: 2810000000000,
          sector: 'Technology',
          rating: 'Buy',
          targetPrice: 395.00
        },
        {
          symbol: 'AMZN',
          name: 'Amazon.com Inc.',
          price: 152.68,
          change: -2.45,
          changePercent: -1.58,
          volume: 45678901,
          marketCap: 1580000000000,
          sector: 'Consumer Discretionary',
          rating: 'Hold',
          targetPrice: 160.00
        }
      ]);

      setTopMovers({
        gainers: [
          { symbol: 'TSLA', change: 5.22 },
          { symbol: 'NVDA', change: 4.87 },
          { symbol: 'AMD', change: 3.45 }
        ],
        losers: [
          { symbol: 'AMZN', change: -1.58 },
          { symbol: 'GOOGL', change: -1.33 },
          { symbol: 'META', change: -0.95 }
        ]
      });
      
    } catch (error) {
      console.error('Failed to load research data:', error);
      setError('Failed to load research data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewStock = (symbol) => {
    navigate(`/stock/${symbol}`);
  };

  const sectors = ['all', 'Technology', 'Healthcare', 'Financials', 'Consumer Discretionary', 'Energy'];

  const filteredStocks = marketData.filter(stock => {
    const matchesSearch = stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         stock.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = selectedSector === 'all' || stock.sector === selectedSector;
    return matchesSearch && matchesSector;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading market research...</span>
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
            onClick={loadResearchData}
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
          <h1 className="text-3xl font-bold text-gray-900">Market Research</h1>
          <p className="mt-2 text-sm text-gray-600">
            Analyze market trends and discover investment opportunities
          </p>
        </div>

        {/* Top Movers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Top Gainers
              </h3>
              <div className="space-y-3">
                {topMovers.gainers.map((stock, index) => (
                  <div key={stock.symbol} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900 mr-2">
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {stock.symbol}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-sm font-medium text-green-600">
                        +{stock.change}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Top Losers
              </h3>
              <div className="space-y-3">
                {topMovers.losers.map((stock, index) => (
                  <div key={stock.symbol} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900 mr-2">
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {stock.symbol}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                      <span className="text-sm font-medium text-red-600">
                        {stock.change}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search stocks by symbol or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
            
            <div>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                {sectors.map((sector) => (
                  <option key={sector} value={sector}>
                    {sector === 'all' ? 'All Sectors' : sector}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Stocks Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Market Overview
            </h3>
            
            {filteredStocks.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">No stocks found</h4>
                <p className="text-gray-500">
                  Try adjusting your search or filter criteria
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stock
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Change
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Volume
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rating
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Target
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredStocks.map((stock) => (
                      <tr key={stock.symbol} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {stock.symbol}
                            </div>
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {stock.name}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            ${stock.price.toFixed(2)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`flex items-center text-sm font-medium ${
                            stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {stock.change >= 0 ? (
                              <TrendingUp className="h-4 w-4 mr-1" />
                            ) : (
                              <TrendingDown className="h-4 w-4 mr-1" />
                            )}
                            {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {(stock.volume / 1000000).toFixed(1)}M
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            stock.rating === 'Buy' 
                              ? 'bg-green-100 text-green-800'
                              : stock.rating === 'Hold'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {stock.rating}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ${stock.targetPrice.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleViewStock(stock.symbol)}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Research;