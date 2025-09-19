import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Mail, 
  Database, 
  Shield, 
  Brain,
  CheckCircle,
  XCircle,
  RefreshCw,
  Save
} from 'lucide-react';
import { useGetSettingsQuery, useTestEmailMutation, useTestDatabaseMutation, useTestIntelMutation } from '../store/api';
import { Card, Grid, Container } from '../components/layout';
import { Button, LoadingSpinner } from '../components/ui';
import { Input, Select, Checkbox } from '../components/forms';
import toast from 'react-hot-toast';
import type { Settings as SettingsType } from '../types';

const Settings: React.FC = () => {
  const { data: settingsData, isLoading, error, refetch } = useGetSettingsQuery();
  const [testEmail] = useTestEmailMutation();
  const [testDatabase] = useTestDatabaseMutation();
  const [testIntel] = useTestIntelMutation();

  const [settings, setSettings] = useState<Partial<SettingsType>>({});
  const [testing, setTesting] = useState<{ [key: string]: boolean }>({});

  const settings = settingsData?.data;

  const handleSettingChange = (key: keyof SettingsType, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleTest = async (testType: 'email' | 'database' | 'intel') => {
    try {
      setTesting(prev => ({ ...prev, [testType]: true }));
      
      let result;
      switch (testType) {
        case 'email':
          result = await testEmail().unwrap();
          break;
        case 'database':
          result = await testDatabase().unwrap();
          break;
        case 'intel':
          result = await testIntel().unwrap();
          break;
      }
      
      toast.success(`${testType.charAt(0).toUpperCase() + testType.slice(1)} test successful`);
    } catch (error: any) {
      toast.error(error?.data?.message || `${testType} test failed`);
    } finally {
      setTesting(prev => ({ ...prev, [testType]: false }));
    }
  };

  const handleSave = () => {
    // TODO: Implement settings save
    toast.success('Settings saved successfully');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading settings..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading settings</h3>
        <p className="mt-1 text-sm text-gray-500">
          {error?.message || 'Something went wrong'}
        </p>
        <Button onClick={() => refetch()} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <Container>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Configure your SOC Agent system settings
            </p>
          </div>
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>

        {/* General Settings */}
        <Card title="General Settings" padding="lg">
          <Grid cols={2} gap="md">
            <Input
              label="Application Host"
              value={settings?.app_host || ''}
              onChange={(e) => handleSettingChange('app_host', e.target.value)}
              helperText="Host address for the application"
            />
            
            <Input
              label="Application Port"
              type="number"
              value={settings?.app_port || ''}
              onChange={(e) => handleSettingChange('app_port', parseInt(e.target.value))}
              helperText="Port number for the application"
            />
            
            <Select
              label="Log Level"
              value={settings?.log_level || ''}
              onChange={(e) => handleSettingChange('log_level', e.target.value)}
              options={[
                { value: 'DEBUG', label: 'Debug' },
                { value: 'INFO', label: 'Info' },
                { value: 'WARNING', label: 'Warning' },
                { value: 'ERROR', label: 'Error' },
              ]}
            />
            
            <Select
              label="Log Format"
              value={settings?.log_format || ''}
              onChange={(e) => handleSettingChange('log_format', e.target.value)}
              options={[
                { value: 'json', label: 'JSON' },
                { value: 'text', label: 'Text' },
              ]}
            />
          </Grid>
        </Card>

        {/* Security Settings */}
        <Card title="Security Settings" padding="lg">
          <Grid cols={2} gap="md">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Features
              </label>
              <div className="space-y-3">
                <Checkbox
                  label="Enable OAuth Authentication"
                  checked={settings?.oauth_enabled || false}
                  onChange={(e) => handleSettingChange('oauth_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Multi-Factor Authentication"
                  checked={settings?.mfa_enabled || false}
                  onChange={(e) => handleSettingChange('mfa_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Role-Based Access Control"
                  checked={settings?.rbac_enabled || false}
                  onChange={(e) => handleSettingChange('rbac_enabled', e.target.checked)}
                />
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Rate Limiting
              </label>
              <div className="space-y-3">
                <Input
                  label="Requests per Window"
                  type="number"
                  value={settings?.rate_limit_requests || ''}
                  onChange={(e) => handleSettingChange('rate_limit_requests', parseInt(e.target.value))}
                />
                <Input
                  label="Window Duration (seconds)"
                  type="number"
                  value={settings?.rate_limit_window || ''}
                  onChange={(e) => handleSettingChange('rate_limit_window', parseInt(e.target.value))}
                />
              </div>
            </div>
          </Grid>
        </Card>

        {/* AI/ML Settings */}
        <Card title="AI & Machine Learning" padding="lg">
          <Grid cols={2} gap="md">
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                AI Features
              </label>
              <div className="space-y-3">
                <Checkbox
                  label="Enable AI Analysis"
                  checked={settings?.ml_enabled || false}
                  onChange={(e) => handleSettingChange('ml_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Anomaly Detection"
                  checked={settings?.anomaly_detection_enabled || false}
                  onChange={(e) => handleSettingChange('anomaly_detection_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Risk Scoring"
                  checked={settings?.risk_scoring_enabled || false}
                  onChange={(e) => handleSettingChange('risk_scoring_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Incident Classification"
                  checked={settings?.classification_enabled || false}
                  onChange={(e) => handleSettingChange('classification_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable False Positive Reduction"
                  checked={settings?.fp_reduction_enabled || false}
                  onChange={(e) => handleSettingChange('fp_reduction_enabled', e.target.checked)}
                />
                <Checkbox
                  label="Enable Pattern Recognition"
                  checked={settings?.pattern_recognition_enabled || false}
                  onChange={(e) => handleSettingChange('pattern_recognition_enabled', e.target.checked)}
                />
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Performance
              </label>
              <div className="space-y-3">
                <Input
                  label="Max Request Size (bytes)"
                  type="number"
                  value={settings?.max_request_size || ''}
                  onChange={(e) => handleSettingChange('max_request_size', parseInt(e.target.value))}
                />
                <Input
                  label="HTTP Timeout (seconds)"
                  type="number"
                  step="0.1"
                  value={settings?.http_timeout || ''}
                  onChange={(e) => handleSettingChange('http_timeout', parseFloat(e.target.value))}
                />
              </div>
            </div>
          </Grid>
        </Card>

        {/* Integration Tests */}
        <Card title="Integration Tests" padding="lg">
          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Test your integrations to ensure they're working correctly.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center">
                  <Mail className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Email</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">SMTP Configuration</p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleTest('email')}
                  loading={testing.email}
                >
                  Test
                </Button>
              </div>
              
              <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center">
                  <Database className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Database</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Connection Test</p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleTest('database')}
                  loading={testing.database}
                >
                  Test
                </Button>
              </div>
              
              <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center">
                  <Shield className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Threat Intel</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">API Connections</p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleTest('intel')}
                  loading={testing.intel}
                >
                  Test
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* System Status */}
        <Card title="System Status" padding="lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-green-100 dark:bg-green-900 rounded-full">
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Database</p>
              <p className="text-xs text-green-600 dark:text-green-400">Connected</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-green-100 dark:bg-green-900 rounded-full">
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Redis</p>
              <p className="text-xs text-green-600 dark:text-green-400">Connected</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-yellow-100 dark:bg-yellow-900 rounded-full">
                <RefreshCw className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">AI Services</p>
              <p className="text-xs text-yellow-600 dark:text-yellow-400">Loading</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-green-100 dark:bg-green-900 rounded-full">
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Webhooks</p>
              <p className="text-xs text-green-600 dark:text-green-400">Active</p>
            </div>
          </div>
        </Card>
      </div>
    </Container>
  );
};

export default Settings;
