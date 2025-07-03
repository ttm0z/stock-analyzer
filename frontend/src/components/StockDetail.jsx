import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import './StockDetail.css';

function StockDetail() {
  const { symbol } = useParams();
  const [stockData, setStockData] = useState(null);
  const [metaData, setMetaData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStock = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:5000/api/stock/${symbol}`);
        const data = await res.json();

        if (res.ok) {
          setStockData(data);
          setMetaData(data['Meta Data']);
          setError(null);
        } else {
          setError(data.error || 'Failed to fetch stock data');
          setStockData(null);
        }
      } catch (err) {
        console.error(err);
        setError('Network error');
        setStockData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchStock();
  }, [symbol]);

  
  return (
    <div className="stock-detail-container">
      <h1 className="stock-title">Stock Details: {symbol}</h1>

      {loading && <div className="loading">Loading...</div>}

      {error && <div className="error-message">{error}</div>}

      {metaData && (
        <div className="stock-info-card">
          <p><strong>Symbol:</strong> {metaData['2. Symbol'] || 'N/A'}</p>
          <p><strong>Latest Close Price:</strong> ${metaData['4. close'] || 'N/A'}</p>
        </div>
      )}
    </div>
  );
}

export default StockDetail;
