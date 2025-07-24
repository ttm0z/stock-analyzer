import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, TrendingUp, Building2 } from 'lucide-react';
import { useStockSearch } from '../hooks/useStockAPI';

function SearchBar() {
  const { query, setQuery, results, loading, error } = useStockSearch();
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const searchRef = useRef(null);

  const handleResultClick = (symbol) => {
    navigate(`/stock/${symbol}`);
    setQuery('');
    setIsOpen(false);
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setIsOpen(e.target.value.length > 0);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && results.length > 0) {
      handleResultClick(results[0].symbol);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setQuery('');
    }
  };

  const clearSearch = () => {
    setQuery('');
    setIsOpen(false);
    searchRef.current?.focus();
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div ref={searchRef} className="relative w-full max-w-lg mx-4">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          onFocus={() => query.length > 0 && setIsOpen(true)}
          placeholder="Search stocks (e.g., AAPL, Tesla, Apple Inc.)"
          className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-sm"
        />
        {query && (
          <button
            onClick={clearSearch}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (query.length > 0) && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-96 overflow-y-auto">
          {loading && (
            <div className="px-4 py-3 text-sm text-gray-500 flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
              Searching...
            </div>
          )}

          {error && (
            <div className="px-4 py-3 text-sm text-red-600 bg-red-50">
              <div className="flex items-center">
                <span className="mr-2">⚠️</span>
                {error}
              </div>
            </div>
          )}

          {results.length > 0 && !loading && (
            <ul className="py-1">
              {results.slice(0, 10).map((result, idx) => (
                <li
                  key={result.symbol || idx}
                  onClick={() => handleResultClick(result.symbol)}
                  className="px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 flex items-center justify-between"
                >
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 mr-3">
                      <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <TrendingUp className="h-4 w-4 text-primary-600" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center">
                        <span className="font-medium text-gray-900 mr-2">
                          {result.symbol}
                        </span>
                        {result.exchange && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            {result.exchange}
                          </span>
                        )}
                      </div>
                      {result.name && (
                        <div className="text-gray-500 truncate text-xs">
                          {result.name}
                        </div>
                      )}
                    </div>
                  </div>
                  {result.type && (
                    <div className="flex-shrink-0 ml-2">
                      <Building2 className="h-4 w-4 text-gray-400" />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          {query.length > 1 && results.length === 0 && !loading && !error && (
            <div className="px-4 py-3 text-sm text-gray-500">
              No stocks found for "{query}"
            </div>
          )}

          {query.length > 0 && (
            <div className="border-t border-gray-100 px-4 py-2 text-xs text-gray-400">
              Press Enter to select first result • ESC to close
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchBar;