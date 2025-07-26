import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus,
  BarChart3,
  Play,
  Pause,
  Settings,
  Eye,
  TrendingUp,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import StrategyAPI from '../../services/strategyAPI';

const Strategies = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [strategies, setStrategies] = useState([]);

  useEffect(() => {
    if (user && token) {
      loadStrategies();
    }
  }, [user, token]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load user's created strategies from the database
      const response = await StrategyAPI.getUserStrategies();
      setStrategies(response.strategies || []);
      
    } catch (error) {
      console.error('Failed to load strategies:', error);
      setError('Failed to load strategies. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStrategy = () => {
    navigate('/strategies/new');
  };

  const handleViewStrategy = (strategyId) => {
    navigate(`/strategies/${strategyId}`);
  };

  const handleToggleStrategy = async (strategyId, currentStatus) => {
    try {
      // Update strategy status via API
      const newStatus = currentStatus === 'active' ? 'paused' : 'active';
      await StrategyAPI.updateUserStrategy(strategyId, { 
        status: newStatus 
      });
      
      // Update local state
      setStrategies(strategies.map(strategy => 
        strategy.id === strategyId 
          ? { ...strategy, status: newStatus }
          : strategy
      ));
    } catch (error) {
      console.error('Failed to toggle strategy:', error);
      setError('Failed to update strategy. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading strategies...</span>
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
            onClick={loadStrategies}
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
            <h1 className="text-3xl font-bold text-gray-900">Trading Strategies</h1>
            <p className="mt-2 text-sm text-gray-600">
              Create and manage your automated trading strategies
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={handleCreateStrategy}
              className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Strategy
            </button>
          </div>
        </div>

        {strategies.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No strategies yet</h3>
            <p className="text-gray-500 mb-6">
              Create your first trading strategy to automate your investments
            </p>
            <button
              onClick={handleCreateStrategy}
              className="inline-flex items-center px-6 py-3 border-2 border-gray-800 text-base font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Your First Strategy
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {strategy.name}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        strategy.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {strategy.status}
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-4">
                    {strategy.description}
                  </p>
                  
                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Return</span>
                      <span className={`text-sm font-medium ${
                        strategy.return_percent >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {strategy.return_percent >= 0 ? '+' : ''}{strategy.return_percent}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Trades</span>
                      <span className="text-sm text-gray-900">{strategy.total_trades}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Win Rate</span>
                      <span className="text-sm text-gray-900">{strategy.win_rate}%</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleToggleStrategy(strategy.id, strategy.status)}
                      className={`flex-1 inline-flex justify-center items-center px-3 py-2 border-2 text-sm font-medium rounded-md shadow-sm transition-all duration-200 transform hover:scale-105 ${
                        strategy.status === 'active'
                          ? 'text-yellow-800 bg-yellow-50 border-yellow-300 hover:bg-yellow-100 hover:border-yellow-400 hover:shadow-md'
                          : 'text-green-800 bg-green-50 border-green-300 hover:bg-green-100 hover:border-green-400 hover:shadow-md'
                      }`}
                    >
                      {strategy.status === 'active' ? (
                        <>
                          <Pause className="h-4 w-4 mr-1" />
                          Pause
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-1" />
                          Start
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={() => handleViewStrategy(strategy.id)}
                      className="flex-1 inline-flex justify-center items-center px-3 py-2 border-2 border-gray-400 text-sm font-medium rounded-md text-gray-800 bg-gray-50 hover:bg-gray-100 hover:border-gray-500 shadow-sm transition-all duration-200 transform hover:scale-105 hover:shadow-md"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Performance Summary */}
        {strategies.length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Strategy Performance Summary
              </h3>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BarChart3 className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Total Strategies</p>
                      <p className="text-lg font-semibold text-gray-900">{strategies.length}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Play className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Active Strategies</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {strategies.filter(s => s.status === 'active').length}
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
                        {strategies.length > 0 
                          ? (strategies.reduce((sum, s) => sum + s.return_percent, 0) / strategies.length).toFixed(1)
                          : '0.0'
                        }%
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

export default Strategies;