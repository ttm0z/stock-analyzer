import { useState, useEffect } from 'react';
import { 
  TrendingUp,
  TrendingDown,
  Globe,
  BarChart3,
  Activity,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const MarketOverview = () => {
  const { user, token } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [marketData, setMarketData] = useState({
    indices: [],
    sectors: [],
    currencies: [],
    commodities: []
  });

  useEffect(() => {
    if (user && token) {
      loadMarketData();
    }
  }, [user, token]);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock market data
      setMarketData({
        indices: [
          {
            name: 'S&P 500',
            symbol: 'SPX',
            value: 4756.50,
            change: 23.45,
            changePercent: 0.49
          },
          {
            name: 'NASDAQ',
            symbol: 'IXIC',
            value: 14845.12,
            change: -45.67,
            changePercent: -0.31
          },
          {
            name: 'Dow Jones',
            symbol: 'DJI',
            value: 37689.54,
            change: 156.78,
            changePercent: 0.42
          },
          {
            name: 'Russell 2000',
            symbol: 'RUT',
            value: 2089.23,
            change: -12.34,
            changePercent: -0.59
          }
        ],
        sectors: [
          { name: 'Technology', change: 1.24, performance: 'strong' },
          { name: 'Healthcare', change: 0.87, performance: 'moderate' },
          { name: 'Financials', change: -0.45, performance: 'weak' },
          { name: 'Energy', change: 2.13, performance: 'strong' },
          { name: 'Consumer Discretionary', change: 0.12, performance: 'moderate' },
          { name: 'Industrials', change: -0.78, performance: 'weak' },
          { name: 'Materials', change: 1.45, performance: 'strong' },
          { name: 'Utilities', change: -0.23, performance: 'weak' }
        ],
        currencies: [
          { pair: 'EUR/USD', rate: 1.0875, change: 0.0012 },
          { pair: 'GBP/USD', rate: 1.2634, change: -0.0034 },
          { pair: 'USD/JPY', rate: 148.45, change: 0.23 },
          { pair: 'USD/CAD', rate: 1.3456, change: 0.0023 }
        ],
        commodities: [
          { name: 'Gold', price: 2034.50, change: 12.30 },
          { name: 'Silver', price: 24.78, change: -0.45 },
          { name: 'Crude Oil', price: 78.34, change: 1.23 },
          { name: 'Natural Gas', price: 2.87, change: -0.15 }
        ]
      });
      
    } catch (error) {
      console.error('Failed to load market data:', error);
      setError('Failed to load market data. Please try again.');
    } finally {
      setLoading(false);
    }
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
            onClick={loadMarketData}
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
          <h1 className="text-3xl font-bold text-gray-900">Market Overview</h1>
          <p className="mt-2 text-sm text-gray-600">
            Global market indices, sectors, and economic indicators
          </p>
        </div>

        {/* Major Indices */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Major Indices</h2>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {marketData.indices.map((index) => (
              <div key={index.symbol} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BarChart3 className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {index.name}
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {index.value.toLocaleString(undefined, { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })}
                        </dd>
                        <dd className={`text-sm ${
                          index.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)} ({index.changePercent >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Performance */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Sector Performance</h2>
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {marketData.sectors.map((sector) => (
                <li key={sector.name}>
                  <div className="px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`h-3 w-3 rounded-full mr-3 ${
                        sector.performance === 'strong' ? 'bg-green-500' :
                        sector.performance === 'moderate' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{sector.name}</p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      {sector.change >= 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                      )}
                      <span className={`text-sm font-medium ${
                        sector.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {sector.change >= 0 ? '+' : ''}{sector.change.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Currencies and Commodities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Currencies */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Currency Exchange Rates
              </h3>
              <div className="space-y-4">
                {marketData.currencies.map((currency) => (
                  <div key={currency.pair} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{currency.pair}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {currency.rate.toFixed(4)}
                      </p>
                      <p className={`text-xs ${
                        currency.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {currency.change >= 0 ? '+' : ''}{currency.change.toFixed(4)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Commodities */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Commodities
              </h3>
              <div className="space-y-4">
                {marketData.commodities.map((commodity) => (
                  <div key={commodity.name} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{commodity.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        ${commodity.price.toFixed(2)}
                      </p>
                      <p className={`text-xs ${
                        commodity.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {commodity.change >= 0 ? '+' : ''}{commodity.change.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Market Summary */}
        <div className="mt-8 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Market Summary
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Advancing</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {marketData.indices.filter(i => i.change > 0).length + marketData.sectors.filter(s => s.change > 0).length}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingDown className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Declining</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {marketData.indices.filter(i => i.change < 0).length + marketData.sectors.filter(s => s.change < 0).length}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Activity className="h-6 w-6 text-primary-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Market Volatility</p>
                    <p className="text-lg font-semibold text-gray-900">Moderate</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;