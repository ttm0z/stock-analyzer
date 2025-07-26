import { useState } from 'react';
import { X, AlertCircle, DollarSign, FileText, Settings } from 'lucide-react';
import PortfolioAPI from '../../services/portfolioAPI';

const CreatePortfolioModal = ({ isOpen, onClose, onPortfolioCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    initial_capital: '',
    portfolio_type: 'paper',
    currency: 'USD'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate form
      if (!formData.name.trim()) {
        throw new Error('Portfolio name is required');
      }
      
      const initialCapital = parseFloat(formData.initial_capital);
      if (isNaN(initialCapital) || initialCapital <= 0) {
        throw new Error('Initial capital must be a positive number');
      }

      const response = await PortfolioAPI.createPortfolio({
        ...formData,
        initial_capital: initialCapital
      });

      onPortfolioCreated(response);
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        initial_capital: '',
        portfolio_type: 'paper',
        currency: 'USD'
      });
    } catch (error) {
      console.error('Create portfolio error:', error);
      setError(error.response?.data?.error || error.message || 'Failed to create portfolio');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50" 
        onClick={onClose}
      />

      {/* Modal panel */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full max-h-screen overflow-y-auto p-6"
           style={{ zIndex: 100 }}>
          {/* Close button */}
          <div className="absolute top-4 right-4">
            <button
              type="button"
              className="text-gray-600 bg-gray-100 border-2 border-gray-300 hover:text-gray-800 hover:bg-gray-200 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-2 transition-all duration-200 transform hover:scale-105"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Modal content */}
          <div className="pr-10">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
              Create New Portfolio
            </h3>

              {error && (
                <div className="mb-4 bg-danger-50 border border-danger-200 rounded-md p-4">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-danger-400" />
                    <div className="ml-3">
                      <p className="text-sm text-danger-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Portfolio Name *
                  </label>
                  <div className="mt-1 relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <FileText className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                      className="appearance-none block w-full px-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      placeholder="e.g., My Growth Portfolio"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows={3}
                    className="appearance-none block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder="Optional description of your portfolio strategy"
                  />
                </div>

                <div>
                  <label htmlFor="portfolio_type" className="block text-sm font-medium text-gray-700">
                    Portfolio Type *
                  </label>
                  <div className="mt-1 relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Settings className="h-5 w-5 text-gray-400" />
                    </div>
                    <select
                      id="portfolio_type"
                      name="portfolio_type"
                      value={formData.portfolio_type}
                      onChange={handleInputChange}
                      className="appearance-none block w-full px-10 py-3 border border-gray-300 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option value="paper">Paper Trading</option>
                      <option value="live">Live Trading</option>
                      <option value="backtest">Backtest</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor="initial_capital" className="block text-sm font-medium text-gray-700">
                    Initial Capital *
                  </label>
                  <div className="mt-1 relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <DollarSign className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="number"
                      id="initial_capital"
                      name="initial_capital"
                      value={formData.initial_capital}
                      onChange={handleInputChange}
                      required
                      min="0.01"
                      step="0.01"
                      className="appearance-none block w-full px-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      placeholder="10000.00"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="currency" className="block text-sm font-medium text-gray-700">
                    Currency
                  </label>
                  <select
                    id="currency"
                    name="currency"
                    value={formData.currency}
                    onChange={handleInputChange}
                    className="appearance-none block w-full px-3 py-3 border border-gray-300 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="GBP">GBP - British Pound</option>
                    <option value="CAD">CAD - Canadian Dollar</option>
                    <option value="AUD">AUD - Australian Dollar</option>
                  </select>
                </div>

                <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3 space-y-3 space-y-reverse sm:space-y-0">
                  <button
                    type="button"
                    onClick={onClose}
                    className="w-full sm:w-auto px-4 py-3 border-2 border-gray-500 rounded-md text-sm font-medium text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-md transition-all duration-200 transform hover:scale-105"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full sm:w-auto px-4 py-3 border-2 border-gray-800 rounded-md text-sm font-medium text-black bg-white hover:bg-gray-100 hover:border-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-60 disabled:cursor-not-allowed shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
                  >
                    {loading ? 'Creating...' : 'Create Portfolio'}
                  </button>
                </div>
              </form>
          </div>
        </div>
    </div>
  );
};

export default CreatePortfolioModal;