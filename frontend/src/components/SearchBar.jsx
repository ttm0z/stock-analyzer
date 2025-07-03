import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchBar.css';

function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!query) return;

    try {
      const res = await fetch(`http://localhost:5000/api/search/${query}`);
      const data = await res.json();

      if (res.ok && data) {
        setResults(data);
        setError(null);
      } else {
        setResults([]);
        setError(data.error || 'No results found');
      }
    } catch (err) {
      setResults([]);
      setError('Network error');
      console.error(err);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleResultClick = (symbol) => {
    navigate(`/stock/${symbol}`);
    setResults([]);
    setQuery('');
  };

  return (
    <div className="search-bar-container">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="Search for a stock symbol"
        className="search-input"
      />
      <button onClick={handleSearch} className="search-button">
        Search
      </button>

      {results.length > 0 && (
        <ul className="search-results">
          {results.map((result, idx) => (
            <li
              key={idx}
              onClick={() => handleResultClick(result['symbol'])}
            >
              <strong>{result['symbol']}</strong> - {result['name']}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="search-error">
          {error}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
