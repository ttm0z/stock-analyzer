import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus,
  FileText,
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Download,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import TradingAPI from '../../services/tradingAPI';
import PortfolioAPI from '../../services/portfolioAPI';

const Trades = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState('all');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    if (user && token) {
      loadData();
    }
  }, [user, token]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load portfolios
      const portfoliosResponse = await PortfolioAPI.getPortfolios({
        portfolio_type: 'paper',
        is_active: true
      });
      setPortfolios(portfoliosResponse.portfolios || []);
      
      // Load all transactions
      if (portfoliosResponse.portfolios?.length > 0) {
        const allTransactions = [];
        for (const portfolio of portfoliosResponse.portfolios) {
          try {
            const transactionsResponse = await TradingAPI.getPortfolioTransactions(
              portfolio.id,
              { limit: 100 }
            );
            const portfolioTransactions = (transactionsResponse.transactions || []).map(t => ({
              ...t,
              portfolio_name: portfolio.name
            }));
            allTransactions.push(...portfolioTransactions);
          } catch (error) {
            console.warn(`Failed to load transactions for portfolio ${portfolio.id}:`, error);
          }
        }
        
        // Sort by date (newest first)
        allTransactions.sort((a, b) => new Date(b.executed_at) - new Date(a.executed_at));
        setTransactions(allTransactions);
      }
      
    } catch (error) {
      console.error('Failed to load trades data:', error);
      setError('Failed to load trades data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewTrade = () => {
    if (portfolios.length > 0) {
      navigate(`/trading?portfolio=${portfolios[0].id}`);
    } else {
      navigate('/portfolios/new');
    }
  };

  const filteredTransactions = transactions.filter(transaction => {
    const portfolioMatch = selectedPortfolio === 'all' || transaction.portfolio_id === selectedPortfolio;
    const typeMatch = filterType === 'all' || transaction.side.toLowerCase() === filterType;
    return portfolioMatch && typeMatch;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          <span className="text-lg text-gray-600">Loading trades...</span>
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
            onClick={loadData}
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
            <h1 className="text-3xl font-bold text-gray-900">Trading History</h1>
            <p className="mt-2 text-sm text-gray-600">
              View and manage all your trading transactions
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex space-x-3">
            <button
              onClick={() => {/* TODO: Implement export */}}
              className="inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
            <button
              onClick={handleNewTrade}
              className="inline-flex items-center px-4 py-2 border-2 border-gray-800 text-sm font-medium rounded-md text-black bg-white hover:bg-gray-100 hover:border-gray-900 shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Trade
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label htmlFor="portfolio-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Portfolio
              </label>
              <select
                id="portfolio-filter"
                value={selectedPortfolio}
                onChange={(e) => setSelectedPortfolio(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="all">All Portfolios</option>
                {portfolios.map((portfolio) => (
                  <option key={portfolio.id} value={portfolio.id}>
                    {portfolio.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Type
              </label>
              <select
                id="type-filter"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="all">All Types</option>
                <option value="buy">Buys</option>
                <option value="sell">Sells</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={() => {
                  setSelectedPortfolio('all');
                  setFilterType('all');
                }}
                className="inline-flex items-center px-4 py-2 border-2 border-gray-500 text-sm font-medium rounded-md text-gray-800 bg-gray-100 hover:bg-gray-200 hover:border-gray-600 shadow-md transition-all duration-200 transform hover:scale-105"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Transactions Table */}
        {filteredTransactions.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {transactions.length === 0 ? 'No transactions yet' : 'No transactions match your filters'}
            </h3>
            <p className="text-gray-500 mb-6">
              {transactions.length === 0 
                ? 'Start trading to see your transaction history here'
                : 'Try adjusting your filters to see more results'
              }
            </p>
            {transactions.length === 0 && (
              <button
                onClick={handleNewTrade}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <Plus className="h-5 w-5 mr-2" />
                Make Your First Trade
              </button>
            )}
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredTransactions.map((transaction) => (
                <li key={transaction.id}>
                  <div className="px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center text-white ${
                          transaction.side === 'BUY' ? 'bg-green-500' : 'bg-red-500'
                        }`}>
                          {transaction.side === 'BUY' ? (
                            <TrendingUp className="h-5 w-5" />
                          ) : (
                            <TrendingDown className="h-5 w-5" />
                          )}
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center">
                          <p className="text-sm font-medium text-gray-900">
                            {transaction.side} {transaction.quantity} shares of {transaction.symbol}
                          </p>
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {transaction.portfolio_name}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4" />
                          {new Date(transaction.executed_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <p className="text-sm font-medium text-gray-900">
                        ${(transaction.price || 0).toFixed(2)} per share
                      </p>
                      <p className="text-sm text-gray-500">
                        Total: ${((transaction.price || 0) * (transaction.quantity || 0)).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default Trades;