import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Eye, 
  Search, 
  Briefcase, 
  FileText, 
  Globe, 
  Settings,
  BarChart3,
  Activity,
  TrendingUp,
  Menu,
  X
} from 'lucide-react';
import { clsx } from 'clsx';
import './Sidebar.css';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Portfolios', href: '/portfolios', icon: Briefcase },
  { name: 'Trades', href: '/trades', icon: FileText },
  { name: 'Research', href: '/research', icon: Search },
  { name: 'Strategies', href: '/strategies', icon: BarChart3 },
  { name: 'Backtests', href: '/backtests', icon: Activity },
  { name: 'Market Overview', href: '/market', icon: Globe },
  { name: 'Settings', href: '/settings', icon: Settings },
];

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div className={clsx(
      'bg-gray-900 text-white h-screen flex flex-col transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        {!collapsed && (
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-primary-500" />
            <span className="ml-2 text-xl font-bold">StockAnalyzer</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-600"
        >
          {collapsed ? (
            <Menu className="h-5 w-5" />
          ) : (
            <X className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={clsx(
                'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                collapsed ? 'justify-center' : 'justify-start'
              )}
              title={collapsed ? item.name : undefined}
            >
              <item.icon
                className={clsx(
                  'h-5 w-5 flex-shrink-0',
                  isActive ? 'text-white' : 'text-gray-400 group-hover:text-white',
                  !collapsed && 'mr-3'
                )}
              />
              {!collapsed && (
                <span className="truncate">{item.name}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400 text-center">
            Stock Analyzer v1.0
          </div>
        </div>
      )}
    </div>
  );
}

export default Sidebar;
