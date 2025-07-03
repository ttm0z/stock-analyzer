import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import axios from "axios";


function StockLineChart({ symbol }) {
  const [data, setData] = useState([]);
  const [dateRange, setDateRange] = useState("30d")
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const getFilteredData = () => {
    if (!data) return [];
  
    const now = new Date();
    let cutoffDate;
  
    switch (dateRange) {
      case "30d":
        cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - 30);
        return data.filter(item => new Date(item.date) >= cutoffDate);
  
      case "3m":
        cutoffDate = new Date();
        cutoffDate.setMonth(cutoffDate.getMonth() - 3);
        return data.filter(item => new Date(item.date) >= cutoffDate);
  
      case "6m":
        cutoffDate = new Date();
        cutoffDate.setMonth(cutoffDate.getMonth() - 6);
        return data.filter(item => new Date(item.date) >= cutoffDate);
  
      case "1y":
        cutoffDate = new Date();
        cutoffDate.setFullYear(cutoffDate.getFullYear() - 1);
        return data.filter(item => new Date(item.date) >= cutoffDate);
  
      case "all":
      default:
        if (data.length <= 500) {
          return data;
        } else {
          const sampled = [];
          const step = Math.floor(data.length / 500);
  
          for (let i = 0; i < data.length; i += step) {
            sampled.push(data[i]);
          }
  
          // Ensure last point is included for completeness
          if (sampled[sampled.length - 1] !== data[data.length - 1]) {
            sampled.push(data[data.length - 1]);
          }
  
          return sampled;
        }
    }
  };
  
  useEffect(() => {
    const fetchStockData = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:5000/api/stock-data/${symbol}`);
        const data = await res.json();
        console.log(data);  
        if (res.ok) {
            setData(data.historical.map(item => ({
              date: item.date,
              price: item.close
            })).reverse());  // Grab first object from the array
          setError(null);
        } else {
          setError('No data found');
          setData(null);
        }
      } catch (err) {
        console.error(err);
        setError('Network error');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchStockData();
  }, [symbol]);

  return (<>
    {loading && <div className="loading">Loading...</div>}

    {error && <div className="error-message">{error}</div>}
    <div style={{ marginBottom: '1rem' }}>
  <button onClick={() => setDateRange("30d")}>30D</button>
  <button onClick={() => setDateRange("3m")}>3M</button>
  <button onClick={() => setDateRange("6m")}>6M</button>
  <button onClick={() => setDateRange("1y")}>1Y</button>
  <button onClick={() => setDateRange("all")}>All</button>
</div>

    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={getFilteredData()}>        
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <CartesianGrid stroke="#ccc" />
        <Line type="monotone" dataKey="price" stroke="#84d8" dot={false} />
      </LineChart>
    </ResponsiveContainer>
    
    </>
  );
}
export default StockLineChart;
