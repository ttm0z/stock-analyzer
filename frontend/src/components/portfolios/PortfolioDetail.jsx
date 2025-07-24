import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft,
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3,
  Plus,
  AlertCircle,
  RefreshCw,
  Calendar,
  Activity
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PortfolioAPI from '../../services/portfolioAPI';
import TradingAPI from '../../services/tradingAPI';

const PortfolioDetail = () => {
  const { id } = useParams();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    if (user && token && id) {
      loadPortfolioData();
    }
  }, [user, token, id]);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load portfolio details
      const portfolioResponse = await PortfolioAPI.getPortfolioDetails(id);
      setPortfolio(portfolioResponse.portfolio);
      setPositions(portfolioResponse.positions || []);
      
      // Load recent transactions
      const transactionsResponse = await TradingAPI.getPortfolioTransactions(id, { limit: 10 });
      setTransactions(transactionsResponse.transactions || []);
      
    } catch (error) {
      console.error('Failed to load portfolio data:', error);
      setError('Failed to load portfolio data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewTrade = () => {
    navigate(`/trading?portfolio=${id}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading portfolio...</span>
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
            onClick={loadPortfolioData}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Portfolio not found</h2>
          <Link
            to="/portfolios"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Portfolios
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={() => navigate('/portfolios')}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
              <p className="mt-2 text-sm text-gray-600">
                Created on {new Date(portfolio.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={handleNewTrade}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Trade
            </button>
          </div>
        </div>

        {/* Portfolio Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DollarSign className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Value</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      ${(portfolio.total_value || 0).toLocaleString(undefined, { 
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
                  {(portfolio.total_return || 0) >= 0 ? (
                    <TrendingUp className="h-6 w-6 text-green-500" />
                  ) : (
                    <TrendingDown className="h-6 w-6 text-red-500" />
                  )}
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Return</dt>
                    <dd className={`text-lg font-medium ${
                      (portfolio.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {(portfolio.total_return || 0) >= 0 ? '+' : ''}
                      ${Math.abs(portfolio.total_return || 0).toLocaleString(undefined, { 
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
                  <BarChart3 className="h-6 w-6 text-primary-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Positions</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {portfolio.num_positions || 0}
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
                  <DollarSign className="h-6 w-6 text-primary-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Cash Balance</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      ${(portfolio.cash_balance || 0).toLocaleString(undefined, { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                      })}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Positions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Current Positions
                </h3>
              </div>
              
              <div className="flow-root">
                {positions.length > 0 ? (
                  <ul className="-my-5 divide-y divide-gray-200">
                    {positions.map((position) => (
                      <li key={position.symbol} className="py-4">
                        <div className="flex items-center space-x-4">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {position.symbol}
                            </p>
                            <p className="text-sm text-gray-500">
                              {position.quantity} shares at ${position.avg_cost?.toFixed(2) || '0.00'}
                            </p>
                          </div>
                          <div className="flex flex-col items-end">
                            <p className="text-sm font-medium text-gray-900">
                              ${(position.market_value || 0).toFixed(2)}
                            </p>
                            <p className={`text-xs ${
                              (position.unrealized_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {(position.unrealized_pnl || 0) >= 0 ? '+' : ''}
                              ${Math.abs(position.unrealized_pnl || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-center py-8">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No Positions</h4>
                    <p className="text-sm text-gray-500 mb-4">
                      Start trading to see your positions here
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

          {/* Recent Transactions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Recent Transactions
                </h3>
                <Link 
                  to="/trades"
                  className="text-sm text-primary-600 hover:text-primary-500"
                >
                  View all
                </Link>
              </div>
              
              <div className="flow-root">
                {transactions.length > 0 ? (
                  <ul className="-my-5 divide-y divide-gray-200">
                    {transactions.map((transaction) => (
                      <li key={transaction.id} className="py-4">
                        <div className="flex items-center space-x-4">
                          <div className="flex-shrink-0">
                            <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-medium text-white ${
                              transaction.side === 'BUY' ? 'bg-green-500' : 'bg-red-500'
                            }`}>
                              {transaction.side === 'BUY' ? 'B' : 'S'}
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">
                              {transaction.side} {transaction.quantity} shares of {transaction.symbol}
                            </p>
                            <p className="text-sm text-gray-500">
                              at ${transaction.price?.toFixed(2) || '0.00'} per share
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
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No Transactions</h4>
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
      </div>
    </div>
  );
};

export default PortfolioDetail;