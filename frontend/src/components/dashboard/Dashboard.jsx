import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Eye,
  Plus,
  BarChart3,
  PieChart,
  Users
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Dashboard = () => {
  const { user } = useAuth();
  const [portfolioStats, setPortfolioStats] = useState({
    totalValue: 125420.50,
    dailyChange: 2345.67,
    dailyChangePercent: 1.91,
    totalReturn: 15420.50,
    totalReturnPercent: 14.05
  });

  const [watchlistStocks] = useState([
    { symbol: 'AAPL', price: 175.43, change: 2.34, changePercent: 1.35 },
    { symbol: 'GOOGL', price: 142.56, change: -1.23, changePercent: -0.85 },
    { symbol: 'TSLA', price: 234.67, change: 5.67, changePercent: 2.48 },
    { symbol: 'MSFT', price: 367.89, change: 1.23, changePercent: 0.34 },
  ]);

  const [recentTrades] = useState([
    { symbol: 'AAPL', type: 'BUY', quantity: 50, price: 173.09, timestamp: '2025-01-23 10:30:00' },
    { symbol: 'GOOGL', type: 'SELL', quantity: 25, price: 143.79, timestamp: '2025-01-22 14:45:00' },
    { symbol: 'TSLA', type: 'BUY', quantity: 100, price: 229.00, timestamp: '2025-01-22 09:15:00' },
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || 'Trader'}!
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Here's what's happening with your investments today.
          </p>
        </div>

        {/* Portfolio Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DollarSign className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Portfolio Value
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      ${portfolioStats.totalValue.toLocaleString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {portfolioStats.dailyChange >= 0 ? (
                    <TrendingUp className="h-6 w-6 text-success-500" />
                  ) : (
                    <TrendingDown className="h-6 w-6 text-danger-500" />
                  )}
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Today's Change
                    </dt>
                    <dd className={`text-lg font-medium ${
                      portfolioStats.dailyChange >= 0 ? 'text-success-600' : 'text-danger-600'
                    }`}>
                      {portfolioStats.dailyChange >= 0 ? '+' : ''}${portfolioStats.dailyChange.toLocaleString()} 
                      ({portfolioStats.dailyChangePercent >= 0 ? '+' : ''}{portfolioStats.dailyChangePercent}%)
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Activity className="h-6 w-6 text-primary-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Return
                    </dt>
                    <dd className="text-lg font-medium text-success-600">
                      +${portfolioStats.totalReturn.toLocaleString()} 
                      (+{portfolioStats.totalReturnPercent}%)
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BarChart3 className="h-6 w-6 text-primary-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Positions
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      12
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Watchlist */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Watchlist
                </h3>
                <button className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                  <Plus className="h-4 w-4 mr-1" />
                  Add Stock
                </button>
              </div>
              
              <div className="flow-root">
                <ul className="-my-5 divide-y divide-gray-200">
                  {watchlistStocks.map((stock) => (
                    <li key={stock.symbol} className="py-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {stock.symbol}
                          </p>
                          <p className="text-sm text-gray-500">
                            ${stock.price.toFixed(2)}
                          </p>
                        </div>
                        <div className="flex flex-col items-end">
                          <p className={`text-sm font-medium ${
                            stock.change >= 0 ? 'text-success-600' : 'text-danger-600'
                          }`}>
                            {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
                          </p>
                          <p className={`text-xs ${
                            stock.changePercent >= 0 ? 'text-success-500' : 'text-danger-500'
                          }`}>
                            {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                          </p>
                        </div>
                        <div>
                          <button className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                            <Eye className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Recent Activity
                </h3>
                <button className="text-sm text-primary-600 hover:text-primary-500">
                  View all
                </button>
              </div>
              
              <div className="flow-root">
                <ul className="-my-5 divide-y divide-gray-200">
                  {recentTrades.map((trade, index) => (
                    <li key={index} className="py-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-medium text-white ${
                            trade.type === 'BUY' ? 'bg-success-500' : 'bg-danger-500'
                          }`}>
                            {trade.type === 'BUY' ? 'B' : 'S'}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {trade.type} {trade.quantity} shares of {trade.symbol}
                          </p>
                          <p className="text-sm text-gray-500">
                            at ${trade.price.toFixed(2)} per share
                          </p>
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(trade.timestamp).toLocaleDateString()}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center">
              <Plus className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">New Trade</span>
            </button>
            
            <button className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center">
              <PieChart className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Portfolio</span>
            </button>
            
            <button className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center">
              <BarChart3 className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Strategies</span>
            </button>
            
            <button className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center">
              <Activity className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Backtest</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;