import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import './StockDetail.css';

function StockDetail() {
  const { symbol } = useParams();
  const [stockData, setStockData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStock = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:5000/api/stock/${symbol}`);
        const data = await res.json();
        console.log(data);  // Good for debugging
        if (res.ok) {
          setStockData(data[0]);  // Grab first object from the array
          setError(null);
        } else {
          setError('No data found');
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
  

//   Array [ {…} ]// ​
// 0: Object { avgVolume: 330235.4, change: 0.03, changesPercentage: 0.72904, … }// ​​
// avgVolume: 330235.4// ​​
// change: 0.03// ​​
// changesPercentage: 0.72904// ​​
// dayHigh: 4.15// ​​
// dayLow: 4.03// ​​
// earningsAnnouncement: "2025-08-07T10:59:00.000+0000"// ​​
// eps: -0.14// ​​
// exchange: "NYSE"// ​​
// marketCap: 181564264// ​​
// name: "FutureFuel Corp."// ​​
// open: 4.12// ​​
// pe: -29.61// ​​
// previousClose: 4.115// ​​
// price: 4.145// ​​
// priceAvg200: 4.8548// ​
// priceAvg50: 4.034// ​​
// sharesOutstanding: 43803200// ​​
// symbol: "FF"
// timestamp: 1751554031
// volume: 29361
// yearHigh: 6.4
// yearLow: 3.77
  return (
    <div className="stock-detail-container">
      {stockData && (
        <div className='stock-head'>
            <h1 className="stock-title">{stockData['name']}</h1>
            <b>{symbol}<br/>{stockData['exchange']}</b>
            <p><strong>Price:</strong> {stockData['price']}</p>
        </div>
        )
    }

      {loading && <div className="loading">Loading...</div>}

      {error && <div className="error-message">{error}</div>}

      {stockData && (
        <div className="stock-info-card">
          
        </div>
      )}
    </div>
  );
}

export default StockDetail;
