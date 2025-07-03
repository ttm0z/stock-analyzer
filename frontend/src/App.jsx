import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SendMessage from './components/SendMessage';
import SearchBar from './components/SearchBar';
import Topbar from './components/Topbar';
import Sidebar from './components/Sidebar';
import StockDetail from './components/StockDetail';
import './App.css'


function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Topbar />
          <div className="page-content">
            {/* Optional: Keep SearchBar always visible */}
            <SearchBar />

            <Routes>
              {/* <Route path="/" element={<Dashboard />} /> */}
              {/* <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/trade-history" element={<TradeHistory />} />
              <Route path="/market-overview" element={<MarketOverview />} />
              <Route path="/settings" element={<Settings />} /> */}
              <Route path="/stock/:symbol" element={<StockDetail />} />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
