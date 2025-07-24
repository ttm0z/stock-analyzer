import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3,
  Eye,
  Edit,
  Trash2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PortfolioAPI from '../../services/portfolioAPI';

const Portfolios = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [portfolios, setPortfolios] = useState([]);

  useEffect(() => {
    if (user && token) {
      loadPortfolios();
    }
  }, [user, token]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await PortfolioAPI.getPortfolios({
        portfolio_type: 'paper',
        is_active: true
      });
      
      setPortfolios(response.portfolios || []);
    } catch (error) {
      console.error('Failed to load portfolios:', error);
      setError('Failed to load portfolios. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePortfolio = () => {
    navigate('/portfolios/new');
  };

  const handleViewPortfolio = (portfolioId) => {
    navigate(`/portfolios/${portfolioId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading portfolios...</span>
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
            onClick={loadPortfolios}
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
        <div className="sm:flex sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Portfolios</h1>
            <p className="mt-2 text-sm text-gray-600">
              Manage and track your investment portfolios
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button
              onClick={handleCreatePortfolio}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Portfolio
            </button>
          </div>
        </div>

        {portfolios.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No portfolios yet</h3>
            <p className="text-gray-500 mb-6">
              Create your first portfolio to start tracking your investments
            </p>
            <button
              onClick={handleCreatePortfolio}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Your First Portfolio
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {portfolios.map((portfolio) => (
              <div key={portfolio.id} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {portfolio.name}
                    </h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleViewPortfolio(portfolio.id)}
                        className="p-1 text-gray-400 hover:text-gray-500"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Value</span>
                      <span className="text-lg font-semibold text-gray-900">
                        ${(portfolio.total_value || 0).toLocaleString(undefined, { 
                          minimumFractionDigits: 2, 
                          maximumFractionDigits: 2 
                        })}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Return</span>
                      <span className={`text-sm font-medium ${
                        (portfolio.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {(portfolio.total_return || 0) >= 0 ? '+' : ''}
                        ${Math.abs(portfolio.total_return || 0).toLocaleString(undefined, { 
                          minimumFractionDigits: 2, 
                          maximumFractionDigits: 2 
                        })}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Positions</span>
                      <span className="text-sm text-gray-900">{portfolio.num_positions || 0}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Cash Balance</span>
                      <span className="text-sm text-gray-900">
                        ${(portfolio.cash_balance || 0).toLocaleString(undefined, { 
                          minimumFractionDigits: 2, 
                          maximumFractionDigits: 2 
                        })}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-6">
                    <button
                      onClick={() => handleViewPortfolio(portfolio.id)}
                      className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Portfolios;