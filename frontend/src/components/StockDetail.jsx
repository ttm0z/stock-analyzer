import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import './StockDetail.css';
import StockLineChart from './StockLineChart.jsx';
import { useStockQuote } from '../hooks/useStockAPI.js';

function StockDetail() {
  const { symbol } = useParams();
  const { data, loading, error, refetch } = useStockQuote(symbol);
  
  
  if (loading) return <p>Loading quote...</p>;
  if (error) return <p>Error: {error}</p>;
  if (!data) return <p>No data available</p>;
  
  return (
    <div className="stock-detail-container">
      {data && (
        <div className='stock-head'>
            <h1 className="stock-title">{data['name']}</h1>
            <b>{symbol}<br/>{data['exchange']}</b>
            <p><strong>Price: $</strong>{data['price']}</p>
        </div>
        )
    }
      {data && (
        <div className="stock-info-card">
          <StockLineChart symbol={symbol}/>
        </div>
      )}
    </div>
  );
}

export default StockDetail;

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
