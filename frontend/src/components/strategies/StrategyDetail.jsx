import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft,
  Edit,
  Play,
  Pause,
  Trash2,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  Target,
  Settings,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Download,
  Eye,
  Zap,
  DollarSign,
  Percent,
  Users,
  Clock
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import StrategyAPI from '../../services/strategyAPI';

const StrategyDetail = () => {
  const { strategyId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [strategy, setStrategy] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [signals, setSignals] = useState([]);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [executionLoading, setExecutionLoading] = useState(false);

  useEffect(() => {
    if (strategyId) {
      loadStrategyDetails();
    }
  }, [strategyId]);

  const loadStrategyDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load strategy list to find our strategy
      const strategiesResponse = await StrategyAPI.getUserStrategies();
      const foundStrategy = strategiesResponse.strategies?.find(s => s.id === parseInt(strategyId));
      
      if (!foundStrategy) {
        setError('Strategy not found');
        return;
      }
      
      setStrategy(foundStrategy);
      
      // Load performance data
      try {
        const performanceResponse = await StrategyAPI.getUserStrategyPerformance(strategyId);
        setPerformance(performanceResponse);
      } catch (perfError) {
        console.log('Performance data not available:', perfError);
      }
      
    } catch (error) {
      console.error('Failed to load strategy details:', error);
      setError('Failed to load strategy details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    try {
      setActionLoading(true);
      const newStatus = strategy.status === 'active' ? 'paused' : 'active';
      
      await StrategyAPI.updateUserStrategy(strategyId, { status: newStatus });
      
      setStrategy(prev => ({
        ...prev,
        status: newStatus
      }));
      
    } catch (error) {
      console.error('Failed to toggle strategy status:', error);
      setError('Failed to update strategy status. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecuteStrategy = async () => {
    try {
      setExecutionLoading(true);
      setError(null);
      
      // For demo purposes, use a default universe
      const defaultUniverse = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'];
      
      const response = await StrategyAPI.executeUserStrategy(strategyId, {
        universe: defaultUniverse
      });
      
      setSignals(response.signals || []);
      
      // Show success message
      setError(null);
      
    } catch (error) {
      console.error('Failed to execute strategy:', error);
      setError('Failed to execute strategy. Please try again.');
    } finally {
      setExecutionLoading(false);
    }
  };

  const handleDeleteStrategy = async () => {
    try {
      setActionLoading(true);
      await StrategyAPI.deleteUserStrategy(strategyId);
      navigate('/strategies');
    } catch (error) {
      console.error('Failed to delete strategy:', error);
      setError('Failed to delete strategy. Please try again.');
      setActionLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/strategies');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-600" />
          <span className="text-lg text-gray-600">Loading strategy...</span>
        </div>
      </div>
    );
  }

  if (error && !strategy) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Strategy</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleBack}
            className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Strategies
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handleBack}
              className="inline-flex items-center px-3 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Strategies
            </button>
            
            <div className="flex space-x-3">
              <button
                onClick={handleToggleStatus}
                disabled={actionLoading}
                className={`inline-flex items-center px-4 py-2 border-2 text-sm font-medium rounded-md shadow-md transition-all duration-200 transform hover:scale-105 disabled:opacity-60 disabled:cursor-not-allowed ${
                  strategy?.status === 'active'
                    ? 'text-yellow-800 bg-yellow-50 border-yellow-300 hover:bg-yellow-100 hover:border-yellow-400'
                    : 'text-green-800 bg-green-50 border-green-300 hover:bg-green-100 hover:border-green-400'
                }`}
              >
                {strategy?.status === 'active' ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause Strategy
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Activate Strategy
                  </>
                )}
              </button>
              
              <button
                onClick={handleExecuteStrategy}
                disabled={executionLoading}
                className="inline-flex items-center px-4 py-2 border-2 border-blue-500 text-sm font-medium rounded-md text-blue-800 bg-blue-50 hover:bg-blue-100 hover:border-blue-600 shadow-md transition-all duration-200 transform hover:scale-105 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {executionLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Execute Now
                  </>
                )}
              </button>
              
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="inline-flex items-center px-4 py-2 border-2 border-red-500 text-sm font-medium rounded-md text-red-800 bg-red-50 hover:bg-red-100 hover:border-red-600 shadow-md transition-all duration-200 transform hover:scale-105"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{strategy?.name}</h1>
              <p className="mt-2 text-lg text-gray-600">{strategy?.description}</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                strategy?.status === 'active' 
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {strategy?.status}
              </span>
              
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {strategy?.strategy_type?.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-red-400 mr-3 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Strategy Overview */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2 text-blue-600" />
                Strategy Overview
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Basic Information</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Strategy Type:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {strategy?.strategy_type?.replace('_', ' ') || 'Unknown'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Created:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {strategy?.created_at ? new Date(strategy.created_at).toLocaleDateString() : 'Unknown'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Status:</span>
                      <span className={`text-sm font-medium ${
                        strategy?.status === 'active' ? 'text-green-600' : 'text-yellow-600'
                      }`}>
                        {strategy?.status || 'Unknown'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Performance Metrics</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Return:</span>
                      <span className={`text-sm font-medium ${
                        (strategy?.return_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {strategy?.return_percent !== undefined 
                          ? `${strategy.return_percent >= 0 ? '+' : ''}${strategy.return_percent}%`
                          : 'N/A'
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Trades:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {strategy?.total_trades || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Win Rate:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {strategy?.win_rate ? `${strategy.win_rate}%` : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Parameters */}
            {strategy?.parameters && Object.keys(strategy.parameters).length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Settings className="h-5 w-5 mr-2 text-blue-600" />
                  Strategy Parameters
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(strategy.parameters).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 p-3 rounded-md">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">
                          {key.replace(/_/g, ' ')}:
                        </span>
                        <span className="text-sm text-gray-900 font-semibold">
                          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Results */}
            {signals.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900 flex items-center">
                    <Activity className="h-5 w-5 mr-2 text-blue-600" />
                    Latest Execution Results
                  </h2>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      Generated: {signals.length} signals
                    </span>
                    <span className="text-sm text-gray-600">
                      Buy: {signals.filter(s => s.signal_type === 'BUY').length}
                    </span>
                    <span className="text-sm text-gray-600">
                      Sell: {signals.filter(s => s.signal_type === 'SELL').length}
                    </span>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Symbol
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Signal
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Strength
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Reason
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {signals.map((signal, index) => (
                        <tr key={index}>
                          <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {signal.symbol}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              signal.signal_type === 'BUY' 
                                ? 'bg-green-100 text-green-800'
                                : signal.signal_type === 'SELL'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {signal.signal_type}
                            </span>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                            {(signal.strength * 100).toFixed(1)}%
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                            ${signal.price?.toFixed(2)}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600 max-w-xs truncate">
                            {signal.reason}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* No Signals State */}
            {signals.length === 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Executions</h3>
                  <p className="text-gray-600 mb-6">
                    Execute the strategy to see generated signals and trading recommendations.
                  </p>
                  <button
                    onClick={handleExecuteStrategy}
                    disabled={executionLoading}
                    className="inline-flex items-center px-6 py-3 border-2 border-gray-800 text-base font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {executionLoading ? (
                      <>
                        <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                        Executing Strategy...
                      </>
                    ) : (
                      <>
                        <Zap className="h-5 w-5 mr-2" />
                        Execute Strategy Now
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Strategy Rules */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2 text-blue-600" />
                Strategy Rules
              </h2>
              
              <div className="space-y-4">
                <div className="bg-green-50 border-2 border-green-200 rounded-md p-3">
                  <h4 className="text-sm font-medium text-green-800 mb-1">Entry Rules</h4>
                  <p className="text-sm text-green-700">
                    {strategy?.strategy_type === 'moving_average' 
                      ? 'Buy when fast MA crosses above slow MA'
                      : strategy?.strategy_type === 'momentum'
                      ? 'Buy stocks with highest momentum scores'
                      : strategy?.strategy_type === 'buy_hold'
                      ? 'Buy and hold selected assets'
                      : 'Strategy-specific entry conditions apply'
                    }
                  </p>
                </div>
                
                <div className="bg-red-50 border-2 border-red-200 rounded-md p-3">
                  <h4 className="text-sm font-medium text-red-800 mb-1">Exit Rules</h4>
                  <p className="text-sm text-red-700">
                    {strategy?.strategy_type === 'moving_average' 
                      ? 'Sell when fast MA crosses below slow MA'
                      : strategy?.strategy_type === 'momentum'
                      ? 'Sell stocks that fall out of top momentum rankings'
                      : strategy?.strategy_type === 'buy_hold'
                      ? 'Only sell during rebalancing'
                      : 'Strategy-specific exit conditions apply'
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Performance Summary */}
            {performance && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                  Performance Summary
                </h2>
                
                <div className="space-y-4">
                  <div className="bg-gray-50 p-3 rounded-md">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-600">Success Rate</span>
                      <span className="text-lg font-bold text-blue-600">
                        {performance.success_rate?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {performance.successful_backtests} / {performance.total_backtests} executions
                    </div>
                  </div>
                  
                  {performance.performance_metrics && (
                    <>
                      {performance.performance_metrics.total_return !== null && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Total Return:</span>
                          <span className={`text-sm font-medium ${
                            performance.performance_metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {performance.performance_metrics.total_return >= 0 ? '+' : ''}
                            {performance.performance_metrics.total_return?.toFixed(2)}%
                          </span>
                        </div>
                      )}
                      
                      {performance.performance_metrics.sharpe_ratio !== null && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Sharpe Ratio:</span>
                          <span className="text-sm font-medium text-gray-900">
                            {performance.performance_metrics.sharpe_ratio?.toFixed(2)}
                          </span>
                        </div>
                      )}
                      
                      {performance.performance_metrics.max_drawdown !== null && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Max Drawdown:</span>
                          <span className="text-sm font-medium text-red-600">
                            {performance.performance_metrics.max_drawdown?.toFixed(2)}%
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
              
              <div className="space-y-3">
                <button
                  onClick={() => navigate(`/backtests/new?strategy=${strategyId}`)}
                  className="w-full inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Run Backtest
                </button>
                
                <button
                  onClick={() => {/* TODO: Implement export */}}
                  className="w-full inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Strategy
                </button>
                
                <button
                  onClick={() => {/* TODO: Implement edit */}}
                  className="w-full inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Strategy
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <div className="flex items-center mb-4">
                <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-medium text-gray-900">Delete Strategy</h3>
              </div>
              
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to delete "{strategy?.name}"? This action cannot be undone.
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteStrategy}
                  disabled={actionLoading}
                  className="flex-1 px-4 py-2 border-2 border-red-600 text-sm font-medium rounded-md text-red-800 bg-red-50 hover:bg-red-100 hover:border-red-700 shadow-md transition-all duration-200 transform hover:scale-105 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {actionLoading ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyDetail;