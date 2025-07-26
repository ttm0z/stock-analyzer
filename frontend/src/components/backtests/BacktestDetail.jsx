import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Clock,
  DollarSign,
  Percent,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Trash2,
  Download,
  Users,
  Calendar,
  Settings,
  PlayCircle,
  PauseCircle,
  XCircle
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import BacktestAPI from '../../services/backtestAPI';

const BacktestDetail = () => {
  const { backtestId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [backtest, setBacktest] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [statusPolling, setStatusPolling] = useState(false);

  useEffect(() => {
    if (backtestId) {
      loadBacktestDetails();
    }
  }, [backtestId]);

  useEffect(() => {
    // Poll status for running backtests
    let interval;
    if (backtest?.status === 'running' || backtest?.status === 'pending') {
      setStatusPolling(true);
      interval = setInterval(() => {
        loadBacktestStatus();
      }, 5000); // Poll every 5 seconds
    } else {
      setStatusPolling(false);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [backtest?.status]);

  const loadBacktestDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await BacktestAPI.getBacktestResults(backtestId);
      setBacktest(response.backtest);
      setPerformance(response.performance);
      
    } catch (error) {
      console.error('Failed to load backtest details:', error);
      setError('Failed to load backtest details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadBacktestStatus = async () => {
    try {
      const response = await BacktestAPI.getBacktestStatus(backtestId);
      setBacktest(prev => ({ ...prev, ...response }));
      
      // If backtest is completed, reload full details
      if (response.status === 'completed' || response.status === 'failed') {
        loadBacktestDetails();
      }
    } catch (error) {
      console.error('Failed to load backtest status:', error);
    }
  };

  const handleDeleteBacktest = async () => {
    try {
      setActionLoading(true);
      await BacktestAPI.deleteBacktest(backtestId);
      navigate('/backtests');
    } catch (error) {
      console.error('Failed to delete backtest:', error);
      setError('Failed to delete backtest. Please try again.');
      setActionLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/backtests');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'running':
        return <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'pending':
        return <PlayCircle className="h-5 w-5 text-yellow-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Activity className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDuration = (startDate, endDate) => {
    if (!startDate || !endDate) return 'N/A';
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    return `${days} days`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-600" />
          <span className="text-lg text-gray-600">Loading backtest...</span>
        </div>
      </div>
    );
  }

  if (error && !backtest) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Backtest</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleBack}
            className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Backtests
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
              Back to Backtests
            </button>
            
            <div className="flex space-x-3">
              {backtest?.status === 'completed' && (
                <button
                  onClick={() => {/* TODO: Implement export */}}
                  className="inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Results
                </button>
              )}
              
              <button
                onClick={() => setShowDeleteConfirm(true)}
                disabled={backtest?.status === 'running'}
                className="inline-flex items-center px-4 py-2 border-2 border-red-500 text-sm font-medium rounded-md text-red-800 bg-red-50 hover:bg-red-100 hover:border-red-600 shadow-md transition-all duration-200 transform hover:scale-105 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{backtest?.name}</h1>
              <p className="mt-2 text-lg text-gray-600">{backtest?.description}</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(backtest?.status)}`}>
                {getStatusIcon(backtest?.status)}
                <span className="ml-2">{backtest?.status}</span>
              </span>
              
              {statusPolling && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                  Live Updates
                </span>
              )}
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

        {/* Progress Bar for Running Backtests */}
        {(backtest?.status === 'running' || backtest?.status === 'pending') && (
          <div className="mb-6 bg-blue-50 border-2 border-blue-200 rounded-md p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-800">
                {backtest?.status === 'pending' ? 'Initializing...' : 'Running Backtest...'}
              </span>
              <span className="text-sm text-blue-600">
                {backtest?.progress ? `${backtest.progress.toFixed(1)}%` : '0%'}
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${backtest?.progress || 0}%` }}
              ></div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Backtest Overview */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Target className="h-5 w-5 mr-2 text-blue-600" />
                Backtest Overview
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Basic Information</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Date Range:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatDate(backtest?.start_date)} - {formatDate(backtest?.end_date)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Duration:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatDuration(backtest?.start_date, backtest?.end_date)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Initial Capital:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(backtest?.initial_capital)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Benchmark:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {backtest?.benchmark_symbol || 'SPY'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Execution Details</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Started:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {backtest?.started_at ? formatDate(backtest.started_at) : 'Not started'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Completed:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {backtest?.completed_at ? formatDate(backtest.completed_at) : 'Not completed'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Execution Time:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {backtest?.execution_time ? BacktestAPI.formatExecutionTime(backtest.execution_time) : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Universe Size:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {backtest?.universe?.length || 0} symbols
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Performance Results */}
            {backtest?.status === 'completed' && performance && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                  Performance Results
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Returns */}
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Returns</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Return:</span>
                        <span className={`text-sm font-medium ${
                          performance.returns?.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercentage(performance.returns?.total_return)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Annualized:</span>
                        <span className={`text-sm font-medium ${
                          performance.returns?.annualized_return >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercentage(performance.returns?.annualized_return)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Benchmark:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {formatPercentage(performance.returns?.benchmark_return)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Alpha:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {formatPercentage(performance.returns?.alpha)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Risk Metrics */}
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Risk Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Volatility:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {formatPercentage(performance.risk?.volatility)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Max Drawdown:</span>
                        <span className="text-sm font-medium text-red-600">
                          {formatPercentage(performance.risk?.max_drawdown)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Sharpe Ratio:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {performance.risk?.sharpe_ratio?.toFixed(2) || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Beta:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {performance.returns?.beta?.toFixed(2) || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Trading Statistics */}
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Trading Statistics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Trades:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {performance.trades?.total_trades || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Win Rate:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {formatPercentage(performance.trades?.win_rate)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Avg Win:</span>
                        <span className="text-sm font-medium text-green-600">
                          {formatPercentage(performance.trades?.avg_win)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Avg Loss:</span>
                        <span className="text-sm font-medium text-red-600">
                          {formatPercentage(performance.trades?.avg_loss)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Failed Backtest Information */}
            {backtest?.status === 'failed' && (
              <div className="bg-red-50 border-2 border-red-200 rounded-md p-6">
                <div className="flex">
                  <XCircle className="h-6 w-6 text-red-600 mr-3 mt-0.5" />
                  <div>
                    <h3 className="text-lg font-medium text-red-800 mb-2">Backtest Failed</h3>
                    <p className="text-sm text-red-700">
                      {backtest?.error_message || 'The backtest failed to complete. Please try again or contact support.'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Configuration */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Settings className="h-5 w-5 mr-2 text-blue-600" />
                Configuration
              </h2>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Trading Costs</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Commission:</span>
                      <span className="font-medium">{((backtest?.commission_rate || 0) * 100).toFixed(3)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Slippage:</span>
                      <span className="font-medium">{((backtest?.slippage_rate || 0) * 100).toFixed(3)}%</span>
                    </div>
                  </div>
                </div>

                {backtest?.strategy_parameters && Object.keys(backtest.strategy_parameters).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Strategy Parameters</h4>
                    <div className="space-y-1">
                      {Object.entries(backtest.strategy_parameters).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-gray-600">{key.replace(/_/g, ' ')}:</span>
                          <span className="font-medium">
                            {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Stock Universe */}
            {backtest?.universe && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Users className="h-5 w-5 mr-2 text-blue-600" />
                  Stock Universe
                </h2>
                
                <div className="flex flex-wrap gap-2">
                  {backtest.universe.map((symbol, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
              
              <div className="space-y-3">
                <button
                  onClick={() => navigate(`/backtests/new?copy=${backtestId}`)}
                  className="w-full inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Copy Configuration
                </button>
                
                <button
                  onClick={() => navigate('/backtests/compare')}
                  className="w-full inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Compare Backtests
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
                <h3 className="text-lg font-medium text-gray-900">Delete Backtest</h3>
              </div>
              
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to delete "{backtest?.name}"? This action cannot be undone.
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteBacktest}
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

export default BacktestDetail;