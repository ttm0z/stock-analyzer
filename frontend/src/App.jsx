import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import Dashboard from './components/dashboard/Dashboard';
import SendMessage from './components/SendMessage';
import SearchBar from './components/SearchBar';
import Topbar from './components/Topbar';
import Sidebar from './components/Sidebar';
import StockDetail from './components/StockDetail';
import Portfolios from './components/portfolios/Portfolios';
import PortfolioDetail from './components/portfolios/PortfolioDetail';
import Trades from './components/trades/Trades';
import Strategies from './components/strategies/Strategies';
import CreateStrategy from './components/strategies/CreateStrategy';
import StrategyDetail from './components/strategies/StrategyDetail';
import Backtests from './components/backtests/Backtests';
import Research from './components/research/Research';
import MarketOverview from './components/market/MarketOverview';
import Settings from './components/settings/Settings';
import './App.css'
import CreateBacktest from './components/backtests/CreateBacktest';
import BacktestDetail from './components/backtests/BacktestDetail';

function AppLayout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Topbar />
        <div className="page-content">
          <SearchBar />
          {children}
        </div>
      </div>
    </div>
  );
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();
  
  return (
    <Routes>
      {/* Public routes */}
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginForm />} 
      />
      <Route 
        path="/register" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterForm />} 
      />
      
      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <AppLayout>
            <Navigate to="/dashboard" replace />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout>
            <Dashboard />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/stock/:symbol" element={
        <ProtectedRoute>
          <AppLayout>
            <StockDetail />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      {/* Future routes */}
      
      <Route path="/portfolios" element={
        <ProtectedRoute>
          <AppLayout>
            <Portfolios />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/portfolios/:portfolioId" element={
        <ProtectedRoute>
          <AppLayout>
            <PortfolioDetail />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/trades" element={
        <ProtectedRoute>
          <AppLayout>
            <Trades />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/strategies" element={
        <ProtectedRoute>
          <AppLayout>
            <Strategies />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/strategies/new" element={
        <ProtectedRoute>
          <AppLayout>
            <CreateStrategy />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/strategies/:strategyId" element={
        <ProtectedRoute>
          <AppLayout>
            <StrategyDetail />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/backtests" element={
        <ProtectedRoute>
          <AppLayout>
            <Backtests />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/backtests/new" element={
        <ProtectedRoute>
          <AppLayout>
            <CreateBacktest />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/backtests/:backtestId" element={
        <ProtectedRoute>
          <AppLayout>
            <BacktestDetail />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/research" element={
        <ProtectedRoute>
          <AppLayout>
            <Research />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout>
            <Settings />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/market" element={
        <ProtectedRoute>
          <AppLayout>
            <MarketOverview />
          </AppLayout>
        </ProtectedRoute>
      } />
      
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
