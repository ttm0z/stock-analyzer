import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import axios from "axios";
import { useHistoricalData } from "../hooks/useStockAPI";


function StockLineChart({ symbol }) {
  const {data, loading, error} = useHistoricalData(symbol);
  
  const [dateRange, setDateRange] = useState("30d")
  
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
