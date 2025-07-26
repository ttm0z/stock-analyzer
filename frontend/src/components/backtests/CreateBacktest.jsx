import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  Target,
  Settings,
  Play,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  TrendingUp,
  BarChart3,
  Users,
  Plus,
  X,
  Info
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import BacktestAPI from '../../services/backtestAPI';
import StrategyAPI from '../../services/strategyAPI';

const CreateBacktest = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preSelectedStrategy = searchParams.get('strategy');

  const [loading, setLoading] = useState(false);
  const [strategiesLoading, setStrategiesLoading] = useState(true);
  const [strategies, setStrategies] = useState([]);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    strategy_id: preSelectedStrategy || '',
    start_date: '',
    end_date: '',
    initial_capital: 10000,
    universe: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
    strategy_parameters: {},
    commission_rate: 0.001,
    slippage_rate: 0.0005,
    benchmark_symbol: 'SPY'
  });

  const [newSymbol, setNewSymbol] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState(null);

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    if (preSelectedStrategy && strategies.length > 0) {
      const strategy = strategies.find(s => s.id === parseInt(preSelectedStrategy));
      if (strategy) {
        setSelectedStrategy(strategy);
        setFormData(prev => ({
          ...prev,
          strategy_id: strategy.id.toString(),
          strategy_parameters: strategy.parameters || {}
        }));
      }
    }
  }, [preSelectedStrategy, strategies]);

  useEffect(() => {
    // Set default date range (1 year ago to today)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 1);

    setFormData(prev => ({
      ...prev,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    }));
  }, []);

  const loadStrategies = async () => {
    try {
      setStrategiesLoading(true);
      const response = await StrategyAPI.getUserStrategies();
      setStrategies(response.strategies || []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      setError('Failed to load strategies. Please try again.');
    } finally {
      setStrategiesLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    const newValue = type === 'number' ? parseFloat(value) || 0 : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleStrategyChange = (e) => {
    const strategyId = e.target.value;
    const strategy = strategies.find(s => s.id === parseInt(strategyId));
    
    setSelectedStrategy(strategy);
    setFormData(prev => ({
      ...prev,
      strategy_id: strategyId,
      strategy_parameters: strategy?.parameters || {}
    }));
  };

  const handleParameterChange = (paramName, value) => {
    setFormData(prev => ({
      ...prev,
      strategy_parameters: {
        ...prev.strategy_parameters,
        [paramName]: value
      }
    }));
  };

  const addSymbol = () => {
    const symbol = newSymbol.trim().toUpperCase();
    if (symbol && !formData.universe.includes(symbol)) {
      setFormData(prev => ({
        ...prev,
        universe: [...prev.universe, symbol]
      }));
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbolToRemove) => {
    setFormData(prev => ({
      ...prev,
      universe: prev.universe.filter(symbol => symbol !== symbolToRemove)
    }));
  };

  const validateForm = () => {
    const validation = BacktestAPI.validateBacktestParams(formData);
    setValidationErrors(validation.errors.reduce((acc, error) => {
      const field = error.toLowerCase().includes('name') ? 'name' :
                   error.toLowerCase().includes('strategy') ? 'strategy_id' :
                   error.toLowerCase().includes('start date') ? 'start_date' :
                   error.toLowerCase().includes('end date') ? 'end_date' :
                   error.toLowerCase().includes('capital') ? 'initial_capital' :
                   error.toLowerCase().includes('symbol') ? 'universe' : 'general';
      acc[field] = error;
      return acc;
    }, {}));
    
    return validation.isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await BacktestAPI.createBacktest(formData);
      
      // Navigate to backtest detail page
      navigate(`/backtests/${response.backtest.id}`);
      
    } catch (error) {
      console.error('Failed to create backtest:', error);
      setError(error.message || 'Failed to create backtest. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/backtests');
  };

  const strategyTypes = {
    'moving_average': 'Moving Average Crossover',
    'momentum': 'Momentum Strategy',
    'buy_hold': 'Buy and Hold'
  };

  const getStrategyTypeDisplay = (strategyType) => {
    return strategyTypes[strategyType] || strategyType;
  };

  const renderStrategyParameters = () => {
    if (!selectedStrategy || !selectedStrategy.parameters) {
      return null;
    }

    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Settings className="h-5 w-5 mr-2 text-blue-600" />
          Strategy Parameters
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(selectedStrategy.parameters).map(([paramName, defaultValue]) => (
            <div key={paramName}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {paramName.replace(/_/g, ' ')}
              </label>
              <input
                type={typeof defaultValue === 'number' ? 'number' : 'text'}
                value={formData.strategy_parameters[paramName] || defaultValue}
                onChange={(e) => handleParameterChange(paramName, 
                  typeof defaultValue === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
                )}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                step={typeof defaultValue === 'number' ? "0.01" : undefined}
              />
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={handleBack}
            className="inline-flex items-center px-3 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Create New Backtest</h1>
              <p className="mt-2 text-lg text-gray-600">
                Configure and run a backtest to evaluate your trading strategy
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-blue-600" />
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

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Information */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Info className="h-5 w-5 mr-2 text-blue-600" />
              Basic Information
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Backtest Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter backtest name"
                  required
                />
                {validationErrors.name && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
                )}
              </div>

              <div>
                <label htmlFor="strategy_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Strategy *
                </label>
                {strategiesLoading ? (
                  <div className="flex items-center py-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-gray-400 mr-2" />
                    <span className="text-sm text-gray-500">Loading strategies...</span>
                  </div>
                ) : (
                  <select
                    id="strategy_id"
                    name="strategy_id"
                    value={formData.strategy_id}
                    onChange={handleStrategyChange}
                    className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      validationErrors.strategy_id ? 'border-red-300' : 'border-gray-300'
                    }`}
                    required
                  >
                    <option value="">Select a strategy</option>
                    {strategies.map(strategy => (
                      <option key={strategy.id} value={strategy.id}>
                        {strategy.name} ({getStrategyTypeDisplay(strategy.strategy_type)})
                      </option>
                    ))}
                  </select>
                )}
                {validationErrors.strategy_id && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.strategy_id}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={3}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Optional description of this backtest"
                />
              </div>
            </div>
          </div>

          {/* Date Range and Capital */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-blue-600" />
              Date Range & Capital
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date *
                </label>
                <input
                  type="date"
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleInputChange}
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.start_date ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {validationErrors.start_date && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.start_date}</p>
                )}
              </div>

              <div>
                <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-1">
                  End Date *
                </label>
                <input
                  type="date"
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleInputChange}
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.end_date ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {validationErrors.end_date && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.end_date}</p>
                )}
              </div>

              <div>
                <label htmlFor="initial_capital" className="block text-sm font-medium text-gray-700 mb-1">
                  Initial Capital ($) *
                </label>
                <input
                  type="number"
                  id="initial_capital"
                  name="initial_capital"
                  value={formData.initial_capital}
                  onChange={handleInputChange}
                  min="1"
                  step="1"
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.initial_capital ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {validationErrors.initial_capital && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.initial_capital}</p>
                )}
              </div>
            </div>
          </div>

          {/* Stock Universe */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Target className="h-5 w-5 mr-2 text-blue-600" />
              Stock Universe
            </h3>
            
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSymbol())}
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <button
                  type="button"
                  onClick={addSymbol}
                  className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </button>
              </div>

              <div className="flex flex-wrap gap-2">
                {formData.universe.map((symbol, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                  >
                    {symbol}
                    <button
                      type="button"
                      onClick={() => removeSymbol(symbol)}
                      className="ml-2 inline-flex items-center p-0.5 rounded-full text-blue-600 hover:text-blue-800 hover:bg-blue-200"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>

              {validationErrors.universe && (
                <p className="text-sm text-red-600">{validationErrors.universe}</p>
              )}
            </div>
          </div>

          {/* Strategy Parameters */}
          {renderStrategyParameters()}

          {/* Advanced Settings */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2 text-blue-600" />
              Advanced Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label htmlFor="commission_rate" className="block text-sm font-medium text-gray-700 mb-1">
                  Commission Rate (%)
                </label>
                <input
                  type="number"
                  id="commission_rate"
                  name="commission_rate"
                  value={formData.commission_rate * 100}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    commission_rate: parseFloat(e.target.value) / 100 || 0.001
                  }))}
                  min="0"
                  step="0.01"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="slippage_rate" className="block text-sm font-medium text-gray-700 mb-1">
                  Slippage Rate (%)
                </label>
                <input
                  type="number"
                  id="slippage_rate"
                  name="slippage_rate"
                  value={formData.slippage_rate * 100}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    slippage_rate: parseFloat(e.target.value) / 100 || 0.0005
                  }))}
                  min="0"
                  step="0.01"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="benchmark_symbol" className="block text-sm font-medium text-gray-700 mb-1">
                  Benchmark Symbol
                </label>
                <input
                  type="text"
                  id="benchmark_symbol"
                  name="benchmark_symbol"
                  value={formData.benchmark_symbol}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    benchmark_symbol: e.target.value.toUpperCase()
                  }))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="SPY"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleBack}
              className="px-6 py-3 border-2 border-gray-500 text-base font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-6 py-3 border-2 border-gray-800 text-base font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                  Creating Backtest...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 mr-2" />
                  Create
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateBacktest;