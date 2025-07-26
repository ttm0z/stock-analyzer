import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft,
  Save,
  AlertTriangle,
  CheckCircle,
  Info,
  Loader2,
  Settings,
  Target,
  TrendingUp
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import StrategyAPI from '../../services/strategyAPI';

const CreateStrategy = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // Form state
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    strategy_type: '',
    category: 'equity',
    complexity: 'intermediate',
    parameters: {},
    is_active: true
  });

  // Load strategy templates
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setTemplatesLoading(true);
      const response = await StrategyAPI.getStrategyTemplates();
      setTemplates(response.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
      setError('Failed to load strategy templates. Please try again.');
    } finally {
      setTemplatesLoading(false);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setFormData({
      name: '',
      description: template.description,
      strategy_type: template.strategy_type,
      category: template.category,
      complexity: template.complexity,
      parameters: { ...template.default_parameters },
      is_active: true
    });
    setError(null);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleParameterChange = (paramName, value) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramName]: value
      }
    }));
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Strategy name is required');
      return false;
    }
    
    if (formData.name.length < 3) {
      setError('Strategy name must be at least 3 characters long');
      return false;
    }
    
    if (!selectedTemplate) {
      setError('Please select a strategy template');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    try {
      setLoading(true);
      setError(null);
      
      let result;
      if (selectedTemplate) {
        // Create from template
        result = await StrategyAPI.createStrategyFromTemplate(selectedTemplate.id, formData);
      } else {
        // Create directly (fallback)
        result = await StrategyAPI.createUserStrategy(formData);
      }
      
      setSuccess(true);
      
      // Navigate back to strategies list after a short delay
      setTimeout(() => {
        navigate('/strategies');
      }, 2000);
      
    } catch (error) {
      console.error('Failed to create strategy:', error);
      setError(error.message || 'Failed to create strategy. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/strategies');
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full mx-4">
          <div className="text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Strategy Created!</h2>
            <p className="text-gray-600 mb-6">
              Your strategy "{formData.name}" has been created successfully.
            </p>
            <div className="text-sm text-gray-500">
              Redirecting to strategies list...
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <button
              onClick={handleCancel}
              className="inline-flex items-center px-3 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105 mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Strategies
            </button>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900">Create New Strategy</h1>
          <p className="mt-2 text-sm text-gray-600">
            Choose a template and customize your trading strategy parameters
          </p>
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
          {/* Strategy Templates */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Target className="h-5 w-5 mr-2 text-primary-600" />
              Choose Strategy Template
            </h2>
            
            {templatesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary-600 mr-2" />
                <span className="text-gray-600">Loading templates...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 transform hover:scale-105 ${
                      selectedTemplate?.id === template.id
                        ? 'border-primary-500 bg-primary-50 shadow-md'
                        : 'border-gray-300 bg-white hover:border-gray-400 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{template.name}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        template.complexity === 'beginner' 
                          ? 'bg-green-100 text-green-800'
                          : template.complexity === 'intermediate'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {template.complexity}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                    
                    <div className="space-y-1 text-xs text-gray-500">
                      <div>Risk Level: {template.risk_level}</div>
                      <div>Holding Period: {template.typical_holding_period}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Strategy Details */}
          {selectedTemplate && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Settings className="h-5 w-5 mr-2 text-primary-600" />
                Strategy Details
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Basic Information */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Strategy Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="e.g., My Moving Average Strategy"
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-md text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      placeholder="Describe your strategy approach..."
                      rows={3}
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-md text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Category
                    </label>
                    <select
                      value={formData.category}
                      onChange={(e) => handleInputChange('category', e.target.value)}
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                    >
                      <option value="equity">Equity</option>
                      <option value="crypto">Cryptocurrency</option>
                      <option value="forex">Forex</option>
                      <option value="commodities">Commodities</option>
                    </select>
                  </div>
                </div>

                {/* Parameters */}
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-gray-900 flex items-center">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Strategy Parameters
                  </h3>
                  
                  {selectedTemplate.parameter_definitions?.map((param) => (
                    <div key={param.name}>
                      <label className="block text-sm font-medium text-gray-900 mb-1">
                        {param.description || param.name}
                        {param.type === 'integer' && param.min !== undefined && (
                          <span className="text-xs text-gray-500 ml-1">
                            ({param.min}-{param.max})
                          </span>
                        )}
                      </label>
                      
                      {param.type === 'boolean' ? (
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.parameters[param.name] || false}
                            onChange={(e) => handleParameterChange(param.name, e.target.checked)}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-2 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">Enable</span>
                        </div>
                      ) : param.options ? (
                        <select
                          value={formData.parameters[param.name] || ''}
                          onChange={(e) => handleParameterChange(param.name, e.target.value)}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                        >
                          {param.options.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={param.type === 'integer' ? 'number' : param.type === 'float' ? 'number' : 'text'}
                          value={formData.parameters[param.name] || ''}
                          onChange={(e) => {
                            const value = param.type === 'integer' 
                              ? parseInt(e.target.value) || 0
                              : param.type === 'float'
                              ? parseFloat(e.target.value) || 0
                              : e.target.value;
                            handleParameterChange(param.name, value);
                          }}
                          min={param.min}
                          max={param.max}
                          step={param.type === 'float' ? '0.01' : '1'}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Strategy Rules Info */}
              <div className="mt-6 bg-blue-50 border-2 border-blue-200 rounded-md p-4">
                <div className="flex">
                  <Info className="h-5 w-5 text-blue-400 mr-3 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-800 mb-2">Strategy Rules</h4>
                    <div className="text-sm text-blue-700 space-y-1">
                      <div><strong>Entry:</strong> {selectedTemplate.entry_rules?.description}</div>
                      <div><strong>Exit:</strong> {selectedTemplate.exit_rules?.description}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={handleCancel}
              className="px-6 py-3 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
            >
              Cancel
            </button>
            
            <button
              type="submit"
              disabled={loading || !selectedTemplate}
              className="px-6 py-3 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Create Strategy
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateStrategy;