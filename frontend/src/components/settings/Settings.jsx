import { useState, useEffect } from 'react';
import { 
  User,
  Settings as SettingsIcon,
  Shield,
  Bell,
  Moon,
  Sun,
  Eye,
  EyeOff,
  Save,
  AlertCircle,
  CheckCircle,
  Key,
  Smartphone,
  Globe,
  Database,
  LogOut,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import AuthAPI from '../../services/authAPI';

const Settings = () => {
  const { user, token, updateProfile, logout } = useAuth();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', content: '' });
  const [showPassword, setShowPassword] = useState(false);
  
  // Profile settings
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: ''
  });
  
  // Preferences
  const [preferences, setPreferences] = useState({
    theme: 'light',
    notifications: {
      email: true,
      push: false,
      portfolio: true,
      alerts: true,
      news: false
    },
    trading: {
      defaultPortfolioType: 'paper',
      confirmTrades: true,
      autoSave: true,
      riskWarnings: true
    },
    display: {
      currency: 'USD',
      dateFormat: 'MM/DD/YYYY',
      timeFormat: '12h',
      language: 'en'
    }
  });
  
  // Security settings
  const [securityData, setSecurityData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    twoFactorEnabled: false,
    apiKeys: []
  });

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        username: user.username || ''
      });
      loadUserPreferences();
      loadSecuritySettings();
    }
  }, [user]);

  const loadUserPreferences = async () => {
    try {
      // Load from localStorage first
      const saved = localStorage.getItem('userPreferences');
      if (saved) {
        setPreferences(prev => ({ ...prev, ...JSON.parse(saved) }));
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  };

  const loadSecuritySettings = async () => {
    try {
      setLoading(true);
      // Load API keys and other security settings
      const response = await fetch('/api/auth/api-keys', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSecurityData(prev => ({
          ...prev,
          apiKeys: data.api_keys || []
        }));
      }
    } catch (error) {
      console.error('Failed to load security settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    try {
      setSaving(true);
      setMessage({ type: '', content: '' });
      
      await updateProfile(profileData);
      
      setMessage({ 
        type: 'success', 
        content: 'Profile updated successfully!' 
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        content: error.message || 'Failed to update profile' 
      });
    } finally {
      setSaving(false);
    }
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      setMessage({ type: '', content: '' });
      
      // Save to localStorage
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      
      // Apply theme
      if (preferences.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      setMessage({ 
        type: 'success', 
        content: 'Preferences saved successfully!' 
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        content: 'Failed to save preferences' 
      });
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async () => {
    try {
      if (securityData.newPassword !== securityData.confirmPassword) {
        setMessage({ type: 'error', content: 'Passwords do not match' });
        return;
      }
      
      if (securityData.newPassword.length < 8) {
        setMessage({ type: 'error', content: 'Password must be at least 8 characters' });
        return;
      }
      
      setSaving(true);
      setMessage({ type: '', content: '' });
      
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: securityData.currentPassword,
          new_password: securityData.newPassword
        })
      });
      
      if (response.ok) {
        setSecurityData(prev => ({
          ...prev,
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        }));
        setMessage({ 
          type: 'success', 
          content: 'Password changed successfully!' 
        });
      } else {
        const error = await response.json();
        setMessage({ 
          type: 'error', 
          content: error.error || 'Failed to change password' 
        });
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        content: error.message || 'Failed to change password' 
      });
    } finally {
      setSaving(false);
    }
  };

  const createAPIKey = async () => {
    try {
      const name = prompt('Enter a name for this API key:');
      if (!name) return;
      
      setSaving(true);
      const response = await fetch('/api/auth/api-keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`API Key created: ${data.api_key.key}\n\nPlease save this key securely. You won't be able to see it again.`);
        loadSecuritySettings();
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        content: 'Failed to create API key' 
      });
    } finally {
      setSaving(false);
    }
  };

  const deleteAPIKey = async (keyId) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
      setSaving(true);
      const response = await fetch(`/api/auth/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        loadSecuritySettings();
        setMessage({ 
          type: 'success', 
          content: 'API key deleted successfully' 
        });
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        content: 'Failed to delete API key' 
      });
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'preferences', name: 'Preferences', icon: SettingsIcon },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'notifications', name: 'Notifications', icon: Bell }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Message Display */}
        {message.content && (
          <div className={`mb-6 p-4 rounded-md ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            <div className="flex">
              {message.type === 'success' ? (
                <CheckCircle className="h-5 w-5 mr-2" />
              ) : (
                <AlertCircle className="h-5 w-5 mr-2" />
              )}
              <span>{message.content}</span>
            </div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`${
                      activeTab === tab.id
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
                  <p className="text-sm text-gray-500">Update your personal information.</p>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={profileData.first_name}
                      onChange={(e) => setProfileData(prev => ({ ...prev, first_name: e.target.value }))}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={profileData.last_name}
                      onChange={(e) => setProfileData(prev => ({ ...prev, last_name: e.target.value }))}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Email
                    </label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Username
                    </label>
                    <input
                      type="text"
                      value={profileData.username}
                      disabled
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={saveProfile}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                  >
                    {saving ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Preferences</h3>
                  <p className="text-sm text-gray-500">Customize your experience.</p>
                </div>

                {/* Theme */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Theme</h4>
                  <div className="flex space-x-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="theme"
                        value="light"
                        checked={preferences.theme === 'light'}
                        onChange={(e) => setPreferences(prev => ({ ...prev, theme: e.target.value }))}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <Sun className="h-4 w-4 ml-2 mr-1" />
                      <span className="text-sm text-gray-700">Light</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="theme"
                        value="dark"
                        checked={preferences.theme === 'dark'}
                        onChange={(e) => setPreferences(prev => ({ ...prev, theme: e.target.value }))}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <Moon className="h-4 w-4 ml-2 mr-1" />
                      <span className="text-sm text-gray-700">Dark</span>
                    </label>
                  </div>
                </div>

                {/* Trading Preferences */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Trading</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Default Portfolio Type
                      </label>
                      <select
                        value={preferences.trading.defaultPortfolioType}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          trading: { ...prev.trading, defaultPortfolioType: e.target.value }
                        }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="paper">Paper Trading</option>
                        <option value="live">Live Trading</option>
                      </select>
                    </div>

                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.trading.confirmTrades}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            trading: { ...prev.trading, confirmTrades: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Confirm trades before execution</span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.trading.autoSave}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            trading: { ...prev.trading, autoSave: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Auto-save strategies</span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.trading.riskWarnings}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            trading: { ...prev.trading, riskWarnings: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Show risk warnings</span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Display Preferences */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Display</h4>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Currency
                      </label>
                      <select
                        value={preferences.display.currency}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          display: { ...prev.display, currency: e.target.value }
                        }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="USD">USD ($)</option>
                        <option value="EUR">EUR (€)</option>
                        <option value="GBP">GBP (£)</option>
                        <option value="JPY">JPY (¥)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Date Format
                      </label>
                      <select
                        value={preferences.display.dateFormat}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          display: { ...prev.display, dateFormat: e.target.value }
                        }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                        <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                        <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={savePreferences}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                  >
                    {saving ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Preferences
                  </button>
                </div>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Security Settings</h3>
                  <p className="text-sm text-gray-500">Manage your account security.</p>
                </div>

                {/* Change Password */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Change Password</h4>
                  <div className="space-y-4 max-w-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Current Password
                      </label>
                      <div className="mt-1 relative">
                        <input
                          type={showPassword ? "text" : "password"}
                          value={securityData.currentPassword}
                          onChange={(e) => setSecurityData(prev => ({ ...prev, currentPassword: e.target.value }))}
                          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-gray-400" />
                          ) : (
                            <Eye className="h-4 w-4 text-gray-400" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={securityData.newPassword}
                        onChange={(e) => setSecurityData(prev => ({ ...prev, newPassword: e.target.value }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={securityData.confirmPassword}
                        onChange={(e) => setSecurityData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>

                    <button
                      onClick={changePassword}
                      disabled={saving || !securityData.currentPassword || !securityData.newPassword || !securityData.confirmPassword}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                    >
                      {saving ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Key className="h-4 w-4 mr-2" />
                      )}
                      Change Password
                    </button>
                  </div>
                </div>

                {/* API Keys */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-900">API Keys</h4>
                    <button
                      onClick={createAPIKey}
                      disabled={saving}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-primary-700 bg-primary-100 hover:bg-primary-200"
                    >
                      <Key className="h-3 w-3 mr-1" />
                      Create New Key
                    </button>
                  </div>

                  {securityData.apiKeys.length === 0 ? (
                    <p className="text-sm text-gray-500">No API keys created yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {securityData.apiKeys.map((key) => (
                        <div key={key.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{key.name}</p>
                            <p className="text-xs text-gray-500">
                              Created: {new Date(key.created_at).toLocaleDateString()}
                              {key.last_used && ` • Last used: ${new Date(key.last_used).toLocaleDateString()}`}
                            </p>
                          </div>
                          <button
                            onClick={() => deleteAPIKey(key.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Session Management */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Session Management</h4>
                  <div className="bg-gray-50 rounded-md p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Current Session</p>
                        <p className="text-xs text-gray-500">
                          Logged in as {user?.email}
                        </p>
                      </div>
                      <button
                        onClick={logout}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                      >
                        <LogOut className="h-3 w-3 mr-1" />
                        Sign Out
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Notification Settings</h3>
                  <p className="text-sm text-gray-500">Choose what notifications you'd like to receive.</p>
                </div>

                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Email Notifications</h4>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.notifications.email}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, email: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Enable email notifications</span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.notifications.portfolio}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, portfolio: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Portfolio updates</span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.notifications.alerts}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, alerts: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Price alerts</span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.notifications.news}
                          onChange={(e) => setPreferences(prev => ({
                            ...prev,
                            notifications: { ...prev.notifications, news: e.target.checked }
                          }))}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">Market news and updates</span>
                      </label>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Push Notifications</h4>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.notifications.push}
                        onChange={(e) => setPreferences(prev => ({
                          ...prev,
                          notifications: { ...prev.notifications, push: e.target.checked }
                        }))}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">Enable push notifications</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={savePreferences}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                  >
                    {saving ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Notification Settings
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;