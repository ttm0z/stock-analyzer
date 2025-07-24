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
  Activity,
  Edit,
  Trash2,
  Search,
  ShoppingCart,
  TrendingDown as SellIcon,
  MoreVertical,
  Settings,
  PieChart
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import PortfolioAPI from '../../services/portfolioAPI';
import TradingAPI from '../../services/tradingAPI';
import StockAPI from '../../services/stockAPI';
import EditPortfolioModal from './EditPortfolioModal';
import DeleteConfirmModal from './DeleteConfirmModal';
import { 
  parsePortfolioUrl, 
  canAccessPortfolio, 
  findPortfolioByName,
  formatCurrency,
  formatPercentage,
  calculatePortfolioMetrics,
  generatePortfolioUrl
} from '../../utils/portfolioUtils';

const PortfolioDetailEnhanced = () => {
  const { username, portfolioSlug } = useParams();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [transactions, setTransactions] = useState([]);
  
  // UI State
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showTradingPanel, setShowTradingPanel] = useState(false);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  
  // Trading State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [tradeForm, setTradeForm] = useState({
    side: 'BUY',
    quantity: '',
    orderType: 'MARKET',
    limitPrice: ''
  });
  const [tradingLoading, setTradingLoading] = useState(false);

  useEffect(() => {
    if (user && token && username && portfolioSlug) {
      // Check if user can access this portfolio
      if (!canAccessPortfolio(user, username)) {
        navigate('/portfolios');
        return;
      }
      
      loadPortfolioData();
    }
  }, [user, token, username, portfolioSlug]);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { portfolioName } = parsePortfolioUrl(username, portfolioSlug);
      
      // Get all user portfolios to find the matching one
      const response = await PortfolioAPI.getPortfolios();
      const userPortfolios = response.portfolios || [];
      
      // Find portfolio by name
      const foundPortfolio = findPortfolioByName(userPortfolios, portfolioName);
      
      if (!foundPortfolio) {
        setError('Portfolio not found');
        return;
      }
      
      // Load detailed portfolio data
      const portfolioResponse = await PortfolioAPI.getPortfolioDetails(foundPortfolio.id);
      setPortfolio(portfolioResponse.portfolio);
      setPositions(portfolioResponse.positions || []);
      
      // Load recent transactions
      try {
        const transactionsResponse = await TradingAPI.getPortfolioTransactions(foundPortfolio.id, { limit: 10 });
        setTransactions(transactionsResponse.transactions || []);
      } catch (transError) {
        console.warn('Failed to load transactions:', transError);
        setTransactions([]);
      }
      
    } catch (error) {
      console.error('Failed to load portfolio data:', error);
      setError('Failed to load portfolio data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleStockSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const results = await StockAPI.searchStocks(query);
      setSearchResults(results.slice(0, 5)); // Limit to 5 results
    } catch (error) {
      console.error('Stock search error:', error);
      setSearchResults([]);
    }
  };

  const handleSelectStock = async (stock) => {
    setSelectedStock(stock);
    setSearchResults([]);
    setSearchQuery(stock.symbol);
  };

  const handleTrade = async () => {
    if (!selectedStock || !portfolio) return;
    
    try {
      setTradingLoading(true);
      
      const tradeData = {
        portfolio_id: portfolio.id,
        symbol: selectedStock.symbol,
        side: tradeForm.side,
        quantity: parseFloat(tradeForm.quantity),
        order_type: tradeForm.orderType,
        limit_price: tradeForm.orderType === 'LIMIT' ? parseFloat(tradeForm.limitPrice) : undefined
      };
      
      await TradingAPI.executeTrade(tradeData);
      
      // Reload portfolio data
      await loadPortfolioData();
      
      // Reset form
      setTradeForm({
        side: 'BUY',
        quantity: '',
        orderType: 'MARKET',
        limitPrice: ''
      });
      setSelectedStock(null);
      setSearchQuery('');
      setShowTradingPanel(false);
      
    } catch (error) {
      console.error('Trade execution error:', error);
      setError(error.message || 'Failed to execute trade');
    } finally {
      setTradingLoading(false);
    }
  };

  const handleEditPortfolio = () => {
    setShowEditModal(true);
    setActionMenuOpen(null);
  };

  const handleDeletePortfolio = () => {
    setShowDeleteModal(true);
    setActionMenuOpen(null);
  };

  const handlePortfolioUpdated = (updatedPortfolio) => {
    setPortfolio(updatedPortfolio.portfolio);
    setShowEditModal(false);
    
    // Update URL if name changed
    const newUrl = generatePortfolioUrl(user.username, updatedPortfolio.portfolio.name);
    navigate(newUrl, { replace: true });
  };

  const handlePortfolioDeleted = () => {
    navigate('/portfolios');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
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
          <div className="space-x-4">
            <button
              onClick={loadPortfolioData}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </button>
            <button
              onClick={() => navigate('/portfolios')}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Portfolios
            </button>
          </div>
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
          <button
            onClick={() => navigate('/portfolios')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Portfolios
          </button>
        </div>
      </div>
    );
  }

  const metrics = calculatePortfolioMetrics(portfolio);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/portfolios')}
                className="mr-4 p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
                <div className="flex items-center mt-2 space-x-4 text-sm text-gray-600">
                  <span>@{username}</span>
                  <span>•</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    portfolio.portfolio_type === 'live' ? 'bg-green-100 text-green-800' :
                    portfolio.portfolio_type === 'paper' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {portfolio.portfolio_type}
                  </span>
                  <span>•</span>
                  <span>Created {new Date(portfolio.created_at).toLocaleDateString()}</span>
                </div>
                {portfolio.description && (
                  <p className="mt-2 text-gray-600">{portfolio.description}</p>
                )}
              </div>
            </div>
            
            {/* Action Menu */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowTradingPanel(!showTradingPanel)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Trade
              </button>
              
              <div className="relative">
                <button
                  onClick={() => setActionMenuOpen(actionMenuOpen ? null : 'portfolio')}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                >
                  <MoreVertical className="h-5 w-5" />
                </button>
                
                {actionMenuOpen === 'portfolio' && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                    <div className="py-1">
                      <button
                        onClick={handleEditPortfolio}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Portfolio
                      </button>
                      <button
                        onClick={handleDeletePortfolio}
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
                      {formatCurrency(metrics.currentValue)}
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
                  {metrics.totalReturn >= 0 ? (
                    <TrendingUp className="h-6 w-6 text-green-500" />
                  ) : (
                    <TrendingDown className="h-6 w-6 text-red-500" />
                  )}
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Return</dt>
                    <dd className={`text-lg font-medium ${
                      metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(metrics.totalReturn)}
                      <div className="text-sm">
                        {formatPercentage(metrics.returnPercentage)}
                      </div>
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
                  <BarChart3 className="h-6 w-6 text-blue-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Positions</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {positions.length}
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
                  <DollarSign className="h-6 w-6 text-green-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Cash Balance</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {formatCurrency(metrics.cashBalance)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trading Panel */}
        {showTradingPanel && (
          <div className="bg-white shadow rounded-lg mb-8 p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Trade Stocks
            </h3>
            
            {/* Stock Search */}
            <div className="mb-4">
              <label htmlFor="stock-search" className="block text-sm font-medium text-gray-700 mb-2">
                Search Stocks
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="stock-search"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    handleStockSearch(e.target.value);
                  }}
                  className="appearance-none block w-full px-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Search for stocks (e.g., AAPL, TSLA, AMZN)"
                />
              </div>
              
              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
                  {searchResults.map((stock) => (
                    <button
                      key={stock.symbol}
                      onClick={() => handleSelectStock(stock)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-medium">{stock.symbol}</div>
                        <div className="text-sm text-gray-500">{stock.name}</div>
                      </div>
                      <div className="text-sm text-gray-900">
                        ${stock.price?.toFixed(2) || 'N/A'}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedStock && (
              <div className="border-t pt-4">
                <div className="bg-gray-50 rounded-md p-4 mb-4">
                  <h4 className="font-medium text-gray-900">{selectedStock.name}</h4>
                  <p className="text-sm text-gray-600">{selectedStock.symbol}</p>
                  <p className="text-lg font-semibold text-gray-900">
                    ${selectedStock.price?.toFixed(2) || 'N/A'}
                  </p>
                </div>

                {/* Trade Form */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Side
                    </label>
                    <select
                      value={tradeForm.side}
                      onChange={(e) => setTradeForm(prev => ({ ...prev, side: e.target.value }))}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="BUY">Buy</option>
                      <option value="SELL">Sell</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      value={tradeForm.quantity}
                      onChange={(e) => setTradeForm(prev => ({ ...prev, quantity: e.target.value }))}
                      min="1"
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Order Type
                    </label>
                    <select
                      value={tradeForm.orderType}
                      onChange={(e) => setTradeForm(prev => ({ ...prev, orderType: e.target.value }))}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="MARKET">Market</option>
                      <option value="LIMIT">Limit</option>
                    </select>
                  </div>

                  {tradeForm.orderType === 'LIMIT' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Limit Price
                      </label>
                      <input
                        type="number"
                        value={tradeForm.limitPrice}
                        onChange={(e) => setTradeForm(prev => ({ ...prev, limitPrice: e.target.value }))}
                        step="0.01"
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="0.00"
                      />
                    </div>
                  )}
                </div>

                <div className="mt-4 flex justify-end space-x-3">
                  <button
                    onClick={() => setShowTradingPanel(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTrade}
                    disabled={!tradeForm.quantity || tradingLoading}
                    className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {tradingLoading ? 'Processing...' : `${tradeForm.side} ${selectedStock.symbol}`}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

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
                              {position.quantity} shares at {formatCurrency(position.avg_entry_price)}
                            </p>
                          </div>
                          <div className="flex flex-col items-end">
                            <p className="text-sm font-medium text-gray-900">
                              {formatCurrency(position.market_value)}
                            </p>
                            <p className={`text-xs ${
                              (position.unrealized_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {formatCurrency(position.unrealized_pnl || 0)}
                              <span className="ml-1">
                                ({formatPercentage(position.unrealized_pnl_pct || 0)})
                              </span>
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
                      onClick={() => setShowTradingPanel(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
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
                  className="text-sm text-blue-600 hover:text-blue-500"
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
                              at {formatCurrency(transaction.price)} per share
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
                      onClick={() => setShowTradingPanel(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
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

      {/* Click outside to close action menu */}
      {actionMenuOpen && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setActionMenuOpen(null)}
        />
      )}

      {/* Modals */}
      {showEditModal && portfolio && (
        <EditPortfolioModal
          isOpen={showEditModal}
          portfolio={portfolio}
          onClose={() => setShowEditModal(false)}
          onPortfolioUpdated={handlePortfolioUpdated}
        />
      )}

      {showDeleteModal && portfolio && (
        <DeleteConfirmModal
          isOpen={showDeleteModal}
          portfolio={portfolio}
          onClose={() => setShowDeleteModal(false)}
          onPortfolioDeleted={handlePortfolioDeleted}
        />
      )}
    </div>
  );
};

export default PortfolioDetailEnhanced;