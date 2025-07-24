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
  Users,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PortfolioAPI from '../../services/portfolioAPI';
import TradingAPI from '../../services/tradingAPI';
import StockAPI from '../../services/stockAPI';
import { Link, useNavigate } from 'react-router-dom';
import { config } from '../../config/environment';

const Dashboard = () => {
  const { user, token, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [portfolios, setPortfolios] = useState([]);
  const [portfolioStats, setPortfolioStats] = useState({
    totalValue: 0,
    dailyChange: 0,
    dailyChangePercent: 0,
    totalReturn: 0,
    totalReturnPercent: 0,
    activePositions: 0,
    cashBalance: 0
  });
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [watchlistStocks, setWatchlistStocks] = useState([]);

  useEffect(() => {
    // Wait for auth to finish loading before deciding what to do
    if (authLoading) {
      if (config.isDevelopment) {
        console.log('⏳ Dashboard waiting for auth to finish loading');
      }
      return;
    }

    // Load dashboard data if user is authenticated
    if (user && token) {
      if (config.isDevelopment) {
        console.log('🏠 Dashboard loading data for authenticated user');
      }
      loadDashboardData();
    } else {
      // Show empty dashboard for new/unauthenticated users
      if (config.isDevelopment) {
        console.log('🏠 Dashboard showing empty state for new user');
      }
      setLoading(false);
    }
  }, [user, token, authLoading]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load portfolios
      const portfoliosResponse = await PortfolioAPI.getPortfolios({
        portfolio_type: 'paper',
        is_active: true,
        limit: 10
      });

      const userPortfolios = portfoliosResponse.portfolios || [];
      setPortfolios(userPortfolios);

      // Calculate aggregate portfolio stats
      const stats = calculateAggregateStats(userPortfolios);
      setPortfolioStats(stats);

      // Load recent transactions from the first portfolio if available
      if (userPortfolios.length > 0) {
        const transactionsResponse = await TradingAPI.getPortfolioTransactions(
          userPortfolios[0].id,
          { limit: 5 }
        );
        setRecentTransactions(transactionsResponse.transactions || []);
      }

      // Load watchlist - for now we'll show empty state to demonstrate the UI
      // In a real app, this would load user-specific watchlist from the API
      // await loadWatchlistData();

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      
      // Handle authentication errors specifically
      if (error.message?.includes('token') || error.message?.includes('Session expired')) {
        setError('Your session has expired. Please log in again.');
        // The httpClient will already dispatch the token-expired event
      } else {
        setError('Failed to load dashboard data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadWatchlistData = async () => {
    const symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT'];
    const watchlistData = [];

    for (const symbol of symbols) {
      try {
        const quote = await StockAPI.getStockQuote(symbol);
        watchlistData.push({
          symbol,
          price: quote.price || 0,
          change: quote.change || 0,
          changePercent: quote.change_percent || 0
        });
      } catch (error) {
        console.warn(`Failed to load quote for ${symbol}:`, error);
      }
    }

    setWatchlistStocks(watchlistData);
  };

  const calculateAggregateStats = (portfolios) => {
    if (!portfolios.length) {
      return {
        totalValue: 0,
        dailyChange: 0,
        dailyChangePercent: 0,
        totalReturn: 0,
        totalReturnPercent: 0,
        activePositions: 0,
        cashBalance: 0
      };
    }

    const totalValue = portfolios.reduce((sum, p) => sum + (p.total_value || 0), 0);
    const totalReturn = portfolios.reduce((sum, p) => sum + (p.total_return || 0), 0);
    const initialCapital = portfolios.reduce((sum, p) => sum + (p.initial_capital || 0), 0);
    const activePositions = portfolios.reduce((sum, p) => sum + (p.num_positions || 0), 0);
    const cashBalance = portfolios.reduce((sum, p) => sum + (p.cash_balance || 0), 0);

    const totalReturnPercent = initialCapital > 0 ? (totalReturn / initialCapital) * 100 : 0;
    
    // For daily change, we'll use a simplified calculation
    // In a real app, you'd track daily snapshots
    const dailyChange = totalReturn * 0.02; // Assume 2% of total return is today's change
    const dailyChangePercent = totalValue > 0 ? (dailyChange / totalValue) * 100 : 0;

    return {
      totalValue,
      dailyChange,
      dailyChangePercent,
      totalReturn,
      totalReturnPercent,
      activePositions,
      cashBalance
    };
  };

  const handleCreatePortfolio = () => {
    navigate('/portfolios/new');
  };

  const handleNewTrade = () => {
    if (portfolios.length > 0) {
      navigate(`/trading?portfolio=${portfolios[0].id}`);
    } else {
      // Create a portfolio first
      handleCreatePortfolio();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading your dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadDashboardData}
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || 'Trader'}!
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {portfolios.length > 0 
              ? "Here's what's happening with your investments today."
              : "Let's get started by creating your first portfolio."
            }
          </p>
        </div>

        {/* Always show the full dashboard layout */}
        <>
            {/* Portfolio Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {portfolios.length > 0 ? (
                <>
                  {/* Stats cards when user has portfolios */}
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
                          ${portfolioStats.totalValue.toLocaleString(undefined, { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })}
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
                          {portfolioStats.dailyChange >= 0 ? '+' : ''}${Math.abs(portfolioStats.dailyChange).toLocaleString(undefined, { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })} 
                          ({portfolioStats.dailyChangePercent >= 0 ? '+' : ''}{portfolioStats.dailyChangePercent.toFixed(2)}%)
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
                        <dd className={`text-lg font-medium ${
                          portfolioStats.totalReturn >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}>
                          {portfolioStats.totalReturn >= 0 ? '+' : ''}${Math.abs(portfolioStats.totalReturn).toLocaleString(undefined, { 
                            minimumFractionDigits: 2, 
                            maximumFractionDigits: 2 
                          })} 
                          ({portfolioStats.totalReturnPercent >= 0 ? '+' : ''}{portfolioStats.totalReturnPercent.toFixed(2)}%)
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
                          {portfolioStats.activePositions}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
                </>
              ) : (
                <>
                  {/* Empty state cards when user has no portfolios */}
                  <div className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <PieChart className="h-6 w-6 text-gray-400" />
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Total Portfolio Value
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                              $0.00
                            </dd>
                            <dd className="text-sm text-gray-400">
                              Create a portfolio to start
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
                          <TrendingUp className="h-6 w-6 text-gray-400" />
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Today's Change
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                              $0.00 (0.00%)
                            </dd>
                            <dd className="text-sm text-gray-400">
                              No positions yet
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
                          <Activity className="h-6 w-6 text-gray-400" />
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Total Return
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                              $0.00 (0.00%)
                            </dd>
                            <dd className="text-sm text-gray-400">
                              Start trading to see returns
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
                          <BarChart3 className="h-6 w-6 text-gray-400" />
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              Active Positions
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                              0
                            </dd>
                            <dd className="text-sm text-gray-400">
                              No positions held
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Watchlist */}
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Market Watchlist
                    </h3>
                    <button 
                      onClick={() => navigate('/watchlist')}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Manage
                    </button>
                  </div>
                  
                  <div className="flow-root">
                    {watchlistStocks.length > 0 ? (
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
                                <button 
                                  onClick={() => navigate(`/stocks/${stock.symbol}`)}
                                  className="inline-flex items-center p-1 border border-transparent rounded-full shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                >
                                  <Eye className="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-center py-8">
                        <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-gray-900 mb-2">No Watchlist</h4>
                        <p className="text-sm text-gray-500 mb-4">
                          Add stocks to your watchlist to track market movements
                        </p>
                        <button 
                          onClick={() => navigate('/watchlist')}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Add Stocks to Watch
                        </button>
                      </div>
                    )}
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
                    <Link 
                      to="/trading/history"
                      className="text-sm text-primary-600 hover:text-primary-500"
                    >
                      View all
                    </Link>
                  </div>
                  
                  <div className="flow-root">
                    {recentTransactions.length > 0 ? (
                      <ul className="-my-5 divide-y divide-gray-200">
                        {recentTransactions.map((transaction) => (
                          <li key={transaction.id} className="py-4">
                            <div className="flex items-center space-x-4">
                              <div className="flex-shrink-0">
                                <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-medium text-white ${
                                  transaction.side === 'BUY' ? 'bg-success-500' : 'bg-danger-500'
                                }`}>
                                  {transaction.side === 'BUY' ? 'B' : 'S'}
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900">
                                  {transaction.side} {transaction.quantity} shares of {transaction.symbol}
                                </p>
                                <p className="text-sm text-gray-500">
                                  at ${transaction.price.toFixed(2)} per share
                                </p>
                              </div>
                              <div className="text-sm text-gray-500">
                                {new Date(transaction.executed_at).toLocaleDateString()}
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-center py-8">
                        <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-gray-900 mb-2">No Trading Activity</h4>
                        <p className="text-sm text-gray-500 mb-4">
                          Start trading to see your transaction history here
                        </p>
                        <button
                          onClick={handleNewTrade}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Make Your First Trade
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>

        {/* Quick Actions */}
        <div className="mt-8">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button 
              onClick={handleNewTrade}
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center"
            >
              <Plus className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">New Trade</span>
            </button>
            
            <button 
              onClick={() => portfolios.length > 0 ? navigate('/portfolios') : handleCreatePortfolio()}
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center"
            >
              <PieChart className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">
                {portfolios.length > 0 ? 'Portfolios' : 'Create Portfolio'}
              </span>
            </button>
            
            <button 
              onClick={() => navigate('/strategies/new')}
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center"
            >
              <BarChart3 className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Create Strategy</span>
            </button>
            
            <button 
              onClick={() => navigate('/backtests/new')}
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow duration-200 flex flex-col items-center"
            >
              <Activity className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Run Backtest</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;