import './Sidebar.css';
import { useState } from 'react';

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <h2>StockApp</h2>
        <button onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '☰' : '✕'}
        </button>
      </div>

      <ul className="sidebar-menu">
        <li>🏠 Dashboard</li>
        <li>📈 Watchlist</li>
        <li>🔍 Search Stocks</li>
        <li>💼 Portfolio</li>
        <li>📝 Trade History</li>
        <li>🌐 Market Overview</li>
        <li>⚙️ Settings</li>
      </ul>
    </div>
  );
}

export default Sidebar;
