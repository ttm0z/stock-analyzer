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
  RefreshCw,
  MoreVertical,
  Filter
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PortfolioAPI from '../../services/portfolioAPI';
import CreatePortfolioModal from './CreatePortfolioModal';
import EditPortfolioModal from './EditPortfolioModal';
import DeleteConfirmModal from './DeleteConfirmModal';

const Portfolios = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [portfolios, setPortfolios] = useState([]);
  const [filteredPortfolios, setFilteredPortfolios] = useState([]);
  const [filters, setFilters] = useState({
    portfolio_type: 'all',
    is_active: 'all',
    search: ''
  });
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);

  useEffect(() => {
    if (user && token) {
      console.log("Loading portfolios . . . ");
      loadPortfolios();
    }
  }, [user, token]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await PortfolioAPI.getPortfolios();
      setPortfolios(response.portfolios || []);
    } catch (error) {
      console.error('Failed to load portfolios:', error);
      setError('Failed to load portfolios. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Filter portfolios based on current filters
  useEffect(() => {
    let filtered = [...portfolios];

    // Filter by portfolio type
    if (filters.portfolio_type !== 'all') {
      filtered = filtered.filter(p => p.portfolio_type === filters.portfolio_type);
    }

    // Filter by active status
    if (filters.is_active !== 'all') {
      const isActive = filters.is_active === 'active';
      filtered = filtered.filter(p => p.is_active === isActive);
    }

    // Filter by search term
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(searchTerm) ||
        (p.description && p.description.toLowerCase().includes(searchTerm))
      );
    }

    setFilteredPortfolios(filtered);
  }, [portfolios, filters]);

  const handleCreatePortfolio = () => {
    setShowCreateModal(true);
  };

  const handleEditPortfolio = (portfolio) => {
    setSelectedPortfolio(portfolio);
    setShowEditModal(true);
    setActionMenuOpen(null);
  };

  const handleDeletePortfolio = (portfolio) => {
    setSelectedPortfolio(portfolio);
    setShowDeleteModal(true);
    setActionMenuOpen(null);
  };

  const handlePortfolioCreated = (newPortfolio) => {
    setPortfolios(prev => [newPortfolio.portfolio, ...prev]);
    setShowCreateModal(false);
  };

  const handlePortfolioUpdated = (updatedPortfolio) => {
    setPortfolios(prev => prev.map(p => 
      p.id === updatedPortfolio.portfolio.id ? updatedPortfolio.portfolio : p
    ));
    setShowEditModal(false);
    setSelectedPortfolio(null);
  };

  const handlePortfolioDeleted = () => {
    setPortfolios(prev => prev.filter(p => p.id !== selectedPortfolio.id));
    setShowDeleteModal(false);
    setSelectedPortfolio(null);
  };

  const toggleActionMenu = (portfolioId) => {
    setActionMenuOpen(actionMenuOpen === portfolioId ? null : portfolioId);
  };

  const formatCurrency = (value) => {
    return (value || 0).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const formatPercentage = (value) => {
    const percentage = ((value || 0) / 100);
    return `${percentage >= 0 ? '+' : ''}${(percentage * 100).toFixed(2)}%`;
  };

  const handleViewPortfolio = (portfolio) => {
    navigate(`/portfolios/${portfolio.id}`);
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
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Portfolio
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="sr-only">Search portfolios</label>
              <input
                type="text"
                id="search"
                placeholder="Search portfolios..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label htmlFor="portfolio-type" className="sr-only">Portfolio Type</label>
              <select
                id="portfolio-type"
                value={filters.portfolio_type}
                onChange={(e) => setFilters(prev => ({ ...prev, portfolio_type: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Types</option>
                <option value="paper">Paper Trading</option>
                <option value="live">Live Trading</option>
                <option value="backtest">Backtest</option>
              </select>
            </div>
            <div>
              <label htmlFor="status" className="sr-only">Status</label>
              <select
                id="status"
                value={filters.is_active}
                onChange={(e) => setFilters(prev => ({ ...prev, is_active: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        {filteredPortfolios.length === 0 && portfolios.length > 0 ? (
          <div className="text-center py-12">
            <Filter className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No portfolios match your filters</h3>
            <p className="text-gray-500 mb-6">
              Try adjusting your search or filter criteria
            </p>
            <button
              onClick={() => setFilters({ portfolio_type: 'all', is_active: 'all', search: '' })}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        ) : filteredPortfolios.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No portfolios yet</h3>
            <p className="text-gray-500 mb-6">
              Create your first portfolio to start tracking your investments
            </p>
            <button
              onClick={handleCreatePortfolio}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Your First Portfolio
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredPortfolios.map((portfolio) => (
              <div key={portfolio.id} className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {portfolio.name}
                      </h3>
                      <div className="flex items-center mt-1 space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          portfolio.portfolio_type === 'live' ? 'bg-green-100 text-green-800' :
                          portfolio.portfolio_type === 'paper' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {portfolio.portfolio_type}
                        </span>
                        {!portfolio.is_active && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="relative">
                      <button
                        onClick={() => toggleActionMenu(portfolio.id)}
                        className="p-1 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 rounded"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </button>
                      {actionMenuOpen === portfolio.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                          <div className="py-1">
                            <button
                              onClick={() => handleViewPortfolio(portfolio)}
                              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </button>
                            <button
                              onClick={() => handleEditPortfolio(portfolio)}
                              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Edit Portfolio
                            </button>
                            <button
                              onClick={() => handleDeletePortfolio(portfolio)}
                              className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete Portfolio
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {portfolio.description && (
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {portfolio.description}
                    </p>
                  )}
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Value</span>
                      <span className="text-lg font-semibold text-gray-900">
                        ${formatCurrency(portfolio.total_value)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Total Return</span>
                      <div className="text-right">
                        <div className={`text-sm font-medium ${
                          (portfolio.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {(portfolio.total_return || 0) >= 0 ? '+' : ''}
                          ${formatCurrency(Math.abs(portfolio.total_return || 0))}
                        </div>
                        <div className={`text-xs ${
                          (portfolio.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercentage(portfolio.total_return || 0)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Positions</span>
                      <span className="text-sm text-gray-900">{portfolio.num_positions || 0}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Cash Balance</span>
                      <span className="text-sm text-gray-900">
                        ${formatCurrency(portfolio.cash_balance)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-6">
                    <button
                      onClick={() => handleViewPortfolio(portfolio)}
                      className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Click outside to close action menu */}
        {actionMenuOpen && (
          <div 
            className="fixed inset-0 z-0" 
            onClick={() => setActionMenuOpen(null)}
          />
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreatePortfolioModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onPortfolioCreated={handlePortfolioCreated}
        />
      )}

      {showEditModal && selectedPortfolio && (
        <EditPortfolioModal
          isOpen={showEditModal}
          portfolio={selectedPortfolio}
          onClose={() => {
            setShowEditModal(false);
            setSelectedPortfolio(null);
          }}
          onPortfolioUpdated={handlePortfolioUpdated}
        />
      )}

      {showDeleteModal && selectedPortfolio && (
        <DeleteConfirmModal
          isOpen={showDeleteModal}
          portfolio={selectedPortfolio}
          onClose={() => {
            setShowDeleteModal(false);
            setSelectedPortfolio(null);
          }}
          onPortfolioDeleted={handlePortfolioDeleted}
        />
      )}
    </div>
  );
};

export default Portfolios;