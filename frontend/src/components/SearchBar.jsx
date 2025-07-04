import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchBar.css';
import { useStockSearch } from '../hooks/useStockAPI';

function SearchBar() {
  const { query, setQuery, results, loading, error, search } = useStockSearch();
  const navigate = useNavigate();

  const handleSearch = () => {
    if (query.trim()) {
      search(query.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleResultClick = (symbol) => {
    navigate(`/stock/${symbol}`);
    // Clear results and query after selection
    setQuery('');
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
  };

  return (
    <div className="search-bar-container">
      <div className="search-input-container">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          placeholder="Search for a stock symbol (e.g., AAPL, Tesla)"
          className="search-input"
          disabled={loading}
        />
        <button 
          onClick={handleSearch} 
          className="search-button"
          disabled={loading || !query.trim()}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {loading && (
        <div className="search-loading">
          <div className="loading-spinner"></div>
          Searching for stocks...
        </div>
      )}

      {results.length > 0 && (
        <ul className="search-results">
          {results.map((result, idx) => (
            <li
              key={result.symbol || idx}
              onClick={() => handleResultClick(result.symbol)}
              className="search-result-item"
            >
              <div className="result-symbol">
                <strong>{result.symbol}</strong>
              </div>
              <div className="result-name">
                {result.name}
              </div>
              {result.exchange && (
                <div className="result-exchange">
                  {result.exchange}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="search-error">
          <span className="error-icon">⚠️</span>
          {error}
          <button 
            onClick={handleSearch} 
            className="retry-button"
          >
            Try Again
          </button>
        </div>
      )}

      {query.length > 0 && results.length === 0 && !loading && !error && (
        <div className="no-results">
          No stocks found for "{query}"
        </div>
      )}
    </div>
  );
}

export default SearchBar;