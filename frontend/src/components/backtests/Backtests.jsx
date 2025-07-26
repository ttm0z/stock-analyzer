import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus,
  Activity,
  Play,
  Eye,
  Calendar,
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import BacktestAPI from '../../services/backtestAPI';

const Backtests = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backtests, setBacktests] = useState([]);

  useEffect(() => {
    if (user && token) {
      loadBacktests();
    }
  }, [user, token]);

  const loadBacktests = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load user's backtests from the database
      const response = await BacktestAPI.getBacktests();
      setBacktests(response.backtests || []);
      
    } catch (error) {
      console.error('Failed to load backtests:', error);
      setError('Failed to load backtests. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBacktest = () => {
    navigate('/backtests/new');
  };

  const handleViewBacktest = (backtestId) => {
    navigate(`/backtests/${backtestId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading backtests...</span>
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
            onClick={loadBacktests}
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
        <div className="sm:flex sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Backtests</h1>
            <p className="mt-2 text-sm text-gray-600">
              Test your trading strategies against historical data
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={handleCreateBacktest}
              className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Backtest
            </button>
          </div>
        </div>

        {backtests.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No backtests yet</h3>
            <p className="text-gray-500 mb-6">
              Run your first backtest to validate your trading strategies
            </p>
            <button
              onClick={handleCreateBacktest}
              className="inline-flex items-center px-6 py-3 border-2 border-gray-800 text-base font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
            >
              <Plus className="h-5 w-5 mr-2" />
              Run Your First Backtest
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {backtests.map((backtest) => (
              <div key={backtest.id} className="bg-white shadow rounded-lg">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {backtest.name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Strategy: {backtest.strategy_name} • Symbol: {backtest.symbol}
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        backtest.status === 'completed' 
                          ? 'bg-green-100 text-green-800'
                          : backtest.status === 'running'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {backtest.status}
                      </span>
                      <button
                        onClick={() => handleViewBacktest(backtest.id)}
                        className="inline-flex items-center p-2 border-2 border-gray-800 rounded-full shadow-lg text-black bg-white hover:bg-gray-100 hover:border-gray-900 transition-all duration-200 transform hover:scale-110 hover:shadow-xl"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  {backtest.status === 'completed' ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                      <div>
                        <p className="text-xs text-gray-500">Period</p>
                        <p className="text-sm font-medium text-gray-900">
                          {new Date(backtest.start_date).toLocaleDateString()} - {new Date(backtest.end_date).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Initial Capital</p>
                        <p className="text-sm font-medium text-gray-900">
                          ${backtest.initial_capital?.toLocaleString()}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Final Value</p>
                        <p className="text-sm font-medium text-gray-900">
                          ${backtest.final_value?.toLocaleString()}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Total Return</p>
                        <p className={`text-sm font-medium ${
                          backtest.return_percent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {backtest.return_percent >= 0 ? '+' : ''}{backtest.return_percent}%
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Win Rate</p>
                        <p className="text-sm font-medium text-gray-900">
                          {backtest.win_rate}%
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-500">Sharpe Ratio</p>
                        <p className="text-sm font-medium text-gray-900">
                          {backtest.sharpe_ratio}
                        </p>
                      </div>
                    </div>
                  ) : backtest.status === 'running' ? (
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center">
                        <RefreshCw className="h-4 w-4 animate-spin text-primary-600 mr-2" />
                        <span className="text-sm text-gray-600">Running backtest...</span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Started: {new Date(backtest.created_at).toLocaleString()}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-600">Backtest pending</span>
                      <div className="text-sm text-gray-500">
                        Created: {new Date(backtest.created_at).toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Performance Summary */}
        {backtests.filter(b => b.status === 'completed').length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Backtest Performance Summary
              </h3>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Activity className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Total Backtests</p>
                      <p className="text-lg font-semibold text-gray-900">{backtests.length}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BarChart3 className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Completed</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {backtests.filter(b => b.status === 'completed').length}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Avg Return</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {(() => {
                          const completed = backtests.filter(b => b.status === 'completed' && b.return_percent !== undefined);
                          return completed.length > 0 
                            ? (completed.reduce((sum, b) => sum + b.return_percent, 0) / completed.length).toFixed(1)
                            : '0.0';
                        })()}%
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Calendar className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Running</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {backtests.filter(b => b.status === 'running').length}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Backtests;