import { useState } from 'react';
import { X, AlertTriangle, Trash2 } from 'lucide-react';
import PortfolioAPI from '../../services/portfolioAPI';

const DeleteConfirmModal = ({ isOpen, portfolio, onClose, onPortfolioDeleted }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confirmationText, setConfirmationText] = useState('');

  const handleDelete = async () => {
    setLoading(true);
    setError(null);

    try {
      await PortfolioAPI.deletePortfolio(portfolio.id);
      onPortfolioDeleted();
    } catch (error) {
      console.error('Delete portfolio error:', error);
      setError(error.response?.data?.error || error.message || 'Failed to delete portfolio');
    } finally {
      setLoading(false);
    }
  };

  const isDeleteEnabled = confirmationText.toLowerCase() === 'delete';

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
              className="text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-1"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Modal content */}
          <div className="pr-10">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">
                Delete Portfolio
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete <strong>"{portfolio?.name}"</strong>? 
                  This action cannot be undone and will permanently remove all portfolio data, 
                  including positions and transaction history.
                </p>
              </div>

              {error && (
                <div className="mt-4 bg-danger-50 border border-danger-200 rounded-md p-4">
                  <div className="flex">
                    <AlertTriangle className="h-5 w-5 text-danger-400" />
                    <div className="ml-3">
                      <p className="text-sm text-danger-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Portfolio Information */}
              <div className="mt-4 bg-gray-50 rounded-md p-4">
                <div className="text-left space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Portfolio Type:</span>
                    <span className="font-medium capitalize">{portfolio?.portfolio_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Current Value:</span>
                    <span className="font-medium">
                      ${(portfolio?.total_value || 0).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Open Positions:</span>
                    <span className="font-medium">{portfolio?.num_positions || 0}</span>
                  </div>
                  {portfolio?.num_positions > 0 && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-xs">
                      <strong>Warning:</strong> This portfolio has open positions. 
                      You may want to close all positions before deleting.
                    </div>
                  )}
                </div>
              </div>

              {/* Confirmation Input */}
              <div className="mt-4">
                <label htmlFor="confirmation" className="block text-sm font-medium text-gray-700 text-left">
                  To confirm deletion, type <strong>"DELETE"</strong> below:
                </label>
                <input
                  type="text"
                  id="confirmation"
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  className="appearance-none block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
                  placeholder="Type DELETE to confirm"
                />
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3 space-y-3 space-y-reverse sm:space-y-0">
            <button
              type="button"
              onClick={onClose}
              className="w-full sm:w-auto px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={loading || !isDeleteEnabled}
              className="w-full sm:w-auto inline-flex justify-center items-center px-4 py-3 border border-transparent rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Portfolio
                </>
              )}
            </button>
          </div>
        </div>
    </div>
  );
};

export default DeleteConfirmModal;