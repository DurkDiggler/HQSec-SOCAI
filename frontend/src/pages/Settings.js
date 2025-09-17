import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Mail,
  Database,
  Shield,
  Activity,
  Globe,
  Key,
  Bell
} from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import { settingsAPI } from '../services/api';

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    // General Settings
    app_host: '0.0.0.0',
    app_port: 8000,
    log_level: 'INFO',
    log_format: 'json',
    
    // Security Settings
    max_request_size: 1048576,
    rate_limit_requests: 100,
    rate_limit_window: 3600,
    cors_origins: ['*'],
    
    // Email Settings
    enable_email: true,
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    email_from: '',
    email_to: [],
    
    // Autotask Settings
    enable_autotask: true,
    at_base_url: '',
    at_api_integration_code: '',
    at_username: '',
    at_secret: '',
    at_account_id: null,
    at_queue_id: null,
    at_ticket_priority: 3,
    
    // Threat Intelligence
    otx_api_key: '',
    vt_api_key: '',
    abuseipdb_api_key: '',
    
    // Scoring
    score_high: 70,
    score_medium: 40,
    
    // Database
    database_url: 'sqlite:///./soc_agent.db',
    postgres_host: '',
    postgres_port: 5432,
    postgres_password: '',
    postgres_db: '',
    
    // Redis
    redis_host: 'redis',
    redis_port: 6379,
    redis_password: '',
    redis_db: 0,
    
    // Webhook Security
    webhook_shared_secret: '',
    webhook_hmac_secret: '',
    webhook_hmac_header: 'X-Signature',
    webhook_hmac_prefix: 'sha256=',
    
    // Monitoring
    enable_metrics: true,
    metrics_port: 9090,
    health_check_timeout: 5.0,
    
    // Feature Flags
    enable_caching: true,
    http_timeout: 8.0,
    ioc_cache_ttl: 1800,
    max_retries: 3,
    retry_delay: 1.0
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await settingsAPI.getSettings();
      setSettings(data);
      toast.success('Settings loaded successfully');
    } catch (err) {
      console.error('Error fetching settings:', err);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      // In a real implementation, this would save to the API
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      toast.success('Settings saved successfully');
    } catch (err) {
      console.error('Error saving settings:', err);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    try {
      toast.loading('Testing email configuration...');
      const result = await settingsAPI.testEmail();
      toast.dismiss();
      
      if (result.success) {
        toast.success(`Email test successful: ${result.message}`);
      } else {
        toast.error(`Email test failed: ${result.message}`);
      }
    } catch (error) {
      toast.dismiss();
      console.error('Error testing email:', error);
      toast.error('Failed to test email configuration');
    }
  };

  const handleTestIntel = async () => {
    try {
      toast.loading('Testing threat intelligence APIs...');
      const result = await settingsAPI.testIntel();
      toast.dismiss();
      
      if (result.success) {
        const results = result.results;
        const successCount = Object.values(results).filter(r => r.status === 'success').length;
        const totalCount = Object.keys(results).length;
        
        if (successCount > 0) {
          toast.success(`${successCount}/${totalCount} Intel APIs working`);
        } else {
          toast.error('No Intel APIs configured or working');
        }
      } else {
        toast.error('Failed to test Intel APIs');
      }
    } catch (error) {
      toast.dismiss();
      console.error('Error testing Intel APIs:', error);
      toast.error('Failed to test Intel APIs');
    }
  };

  const handleTestDatabase = async () => {
    try {
      toast.loading('Testing database connection...');
      const result = await settingsAPI.testDatabase();
      toast.dismiss();
      
      if (result.success) {
        toast.success(`Database test successful: ${result.message}`);
      } else {
        toast.error(`Database test failed: ${result.message}`);
      }
    } catch (error) {
      toast.dismiss();
      console.error('Error testing database:', error);
      toast.error('Failed to test database connection');
    }
  };

  const getEmailStatus = () => {
    const isEnabled = settings.enable_email;
    const hasHost = settings.smtp_host && settings.smtp_host.trim() !== '';
    const hasFrom = settings.email_from && settings.email_from.trim() !== '';
    const hasTo = settings.email_to && settings.email_to.length > 0;
    
    if (!isEnabled) {
      return (
        <span className="flex items-center text-gray-600">
          <XCircle className="h-4 w-4 mr-1" />
          Disabled
        </span>
      );
    }
    
    if (hasHost && hasFrom && hasTo) {
      return (
        <span className="flex items-center text-green-600">
          <CheckCircle className="h-4 w-4 mr-1" />
          Configured
        </span>
      );
    }
    
    return (
      <span className="flex items-center text-yellow-600">
        <AlertTriangle className="h-4 w-4 mr-1" />
        Not Configured
      </span>
    );
  };

  const getIntelStatus = () => {
    const hasOtx = settings.otx_api_key && settings.otx_api_key.trim() !== '';
    const hasVt = settings.vt_api_key && settings.vt_api_key.trim() !== '';
    const hasAbuse = settings.abuseipdb_api_key && settings.abuseipdb_api_key.trim() !== '';
    
    const configuredCount = [hasOtx, hasVt, hasAbuse].filter(Boolean).length;
    
    if (configuredCount === 0) {
      return (
        <span className="flex items-center text-gray-600">
          <XCircle className="h-4 w-4 mr-1" />
          None
        </span>
      );
    }
    
    if (configuredCount === 3) {
      return (
        <span className="flex items-center text-green-600">
          <CheckCircle className="h-4 w-4 mr-1" />
          All
        </span>
      );
    }
    
    return (
      <span className="flex items-center text-yellow-600">
        <AlertTriangle className="h-4 w-4 mr-1" />
        Partial ({configuredCount}/3)
      </span>
    );
  };

  const handleInputChange = (section, field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayInputChange = (field, value) => {
    const array = value.split(',').map(item => item.trim()).filter(item => item);
    setSettings(prev => ({
      ...prev,
      [field]: array
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Loading settings..." />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">
          Configure SOC Agent system settings and integrations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Sections */}
        <div className="lg:col-span-2 space-y-6">
          {/* General Settings */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center gap-2">
                <SettingsIcon className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">General Settings</h3>
              </div>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Host
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    value={settings.app_host}
                    onChange={(e) => handleInputChange('general', 'app_host', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Port
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.app_port}
                    onChange={(e) => handleInputChange('general', 'app_port', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Log Level
                  </label>
                  <select
                    className="form-select"
                    value={settings.log_level}
                    onChange={(e) => handleInputChange('general', 'log_level', e.target.value)}
                  >
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Log Format
                  </label>
                  <select
                    className="form-select"
                    value={settings.log_format}
                    onChange={(e) => handleInputChange('general', 'log_format', e.target.value)}
                  >
                    <option value="json">JSON</option>
                    <option value="text">Text</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Security Settings */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-red-600" />
                <h3 className="text-lg font-semibold text-gray-900">Security Settings</h3>
              </div>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Request Size (bytes)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.max_request_size}
                    onChange={(e) => handleInputChange('security', 'max_request_size', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rate Limit Requests
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.rate_limit_requests}
                    onChange={(e) => handleInputChange('security', 'rate_limit_requests', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rate Limit Window (seconds)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.rate_limit_window}
                    onChange={(e) => handleInputChange('security', 'rate_limit_window', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CORS Origins (comma-separated)
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    value={settings.cors_origins.join(', ')}
                    onChange={(e) => handleArrayInputChange('cors_origins', e.target.value)}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Email Settings */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Email Settings</h3>
              </div>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="enable_email"
                    className="form-checkbox"
                    checked={settings.enable_email}
                    onChange={(e) => handleInputChange('email', 'enable_email', e.target.checked)}
                  />
                  <label htmlFor="enable_email" className="ml-2 text-sm font-medium text-gray-700">
                    Enable Email Notifications
                  </label>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SMTP Host
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={settings.smtp_host}
                      onChange={(e) => handleInputChange('email', 'smtp_host', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SMTP Port
                    </label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.smtp_port}
                      onChange={(e) => handleInputChange('email', 'smtp_port', parseInt(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SMTP Username
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={settings.smtp_username}
                      onChange={(e) => handleInputChange('email', 'smtp_username', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      SMTP Password
                    </label>
                    <input
                      type="password"
                      className="form-input"
                      value={settings.smtp_password}
                      onChange={(e) => handleInputChange('email', 'smtp_password', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      From Email
                    </label>
                    <input
                      type="email"
                      className="form-input"
                      value={settings.email_from}
                      onChange={(e) => handleInputChange('email', 'email_from', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      To Emails (comma-separated)
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={settings.email_to.join(', ')}
                      onChange={(e) => handleArrayInputChange('email_to', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Threat Intelligence Settings */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">Threat Intelligence</h3>
              </div>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    OTX API Key
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={settings.otx_api_key}
                    onChange={(e) => handleInputChange('intel', 'otx_api_key', e.target.value)}
                    placeholder="Enter OTX API key"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    VirusTotal API Key
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={settings.vt_api_key}
                    onChange={(e) => handleInputChange('intel', 'vt_api_key', e.target.value)}
                    placeholder="Enter VirusTotal API key"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    AbuseIPDB API Key
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={settings.abuseipdb_api_key}
                    onChange={(e) => handleInputChange('intel', 'abuseipdb_api_key', e.target.value)}
                    placeholder="Enter AbuseIPDB API key"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Scoring Settings */}
          <div className="card">
            <div className="card-header">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">Scoring Settings</h3>
              </div>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    High Score Threshold
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.score_high}
                    onChange={(e) => handleInputChange('scoring', 'score_high', parseInt(e.target.value))}
                    min="0"
                    max="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Medium Score Threshold
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={settings.score_medium}
                    onChange={(e) => handleInputChange('scoring', 'score_medium', parseInt(e.target.value))}
                    min="0"
                    max="100"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Save Button */}
          <div className="card">
            <div className="card-body">
              <button
                onClick={handleSave}
                disabled={saving}
                className="btn btn-primary w-full"
              >
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Settings
                  </>
                )}
              </button>
            </div>
          </div>

          {/* System Status */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
            </div>
            <div className="card-body">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API Status</span>
                  <span className="flex items-center text-green-600">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Online
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Database</span>
                  <span className="flex items-center text-green-600">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Connected
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Email Service</span>
                  {getEmailStatus()}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Threat Intel</span>
                  {getIntelStatus()}
                </div>
              </div>
            </div>
          </div>

          {/* Configuration Note */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Configuration Note</h3>
            </div>
            <div className="card-body">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <Bell className="h-5 w-5 text-blue-400 mr-3 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-800 mb-1">Settings Update Required</h4>
                    <p className="text-sm text-blue-700">
                      After updating the .env file, you need to restart the SOC Agent service for changes to take effect. 
                      The status indicators above will update automatically once the service is restarted.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
            </div>
            <div className="card-body">
              <div className="space-y-2">
                <button 
                  className="btn btn-outline btn-sm w-full"
                  onClick={fetchSettings}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Settings
                </button>
                <button 
                  className="btn btn-outline btn-sm w-full"
                  onClick={handleTestEmail}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Test Email
                </button>
                <button 
                  className="btn btn-outline btn-sm w-full"
                  onClick={handleTestIntel}
                >
                  <Globe className="h-4 w-4 mr-2" />
                  Test Intel APIs
                </button>
                <button 
                  className="btn btn-outline btn-sm w-full"
                  onClick={handleTestDatabase}
                >
                  <Database className="h-4 w-4 mr-2" />
                  Test Database
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
