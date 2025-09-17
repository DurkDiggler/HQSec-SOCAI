import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  Shield, 
  Target, 
  Zap, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Play,
  Stop,
  RefreshCw
} from 'lucide-react';
import { mcpAPI } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const MCPTools = ({ target, onScanComplete }) => {
  const [mcpStatus, setMcpStatus] = useState(null);
  const [capabilities, setCapabilities] = useState(null);
  const [scanResults, setScanResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMCPStatus();
    fetchCapabilities();
  }, []);

  const fetchMCPStatus = async () => {
    try {
      const data = await mcpAPI.getStatus();
      setMcpStatus(data.mcp_servers);
    } catch (err) {
      console.error('Error fetching MCP status:', err);
      setError('Failed to load MCP server status');
    }
  };

  const fetchCapabilities = async () => {
    try {
      const data = await mcpAPI.getCapabilities();
      setCapabilities(data.capabilities);
    } catch (err) {
      console.error('Error fetching MCP capabilities:', err);
    }
  };

  const runScan = async (scanType = 'basic') => {
    if (!target) {
      toast.error('Please enter a target');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await mcpAPI.scanTarget(target, scanType);
      setScanResults(data);
      if (onScanComplete) {
        onScanComplete(data);
      }
      toast.success('Scan completed successfully');
    } catch (err) {
      console.error('Error running scan:', err);
      setError('Scan failed');
      toast.error('Scan failed');
    } finally {
      setLoading(false);
    }
  };

  const testExploit = async (vulnerability, exploitType = 'basic') => {
    if (!target) {
      toast.error('Please enter a target');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await mcpAPI.testExploit(target, vulnerability, exploitType);
      setScanResults(data);
      toast.success('Exploit test completed');
    } catch (err) {
      console.error('Error testing exploit:', err);
      setError('Exploit test failed');
      toast.error('Exploit test failed');
    } finally {
      setLoading(false);
    }
  };

  const runOffensiveTest = async () => {
    if (!target) {
      toast.error('Please enter a target');
      return;
    }

    const testScenarios = [
      { type: 'port_scan', parameters: { scan_type: 'basic' } },
      { type: 'vulnerability_scan', parameters: { scan_type: 'basic' } },
      { type: 'web_scan', parameters: { scan_type: 'nikto' } }
    ];

    try {
      setLoading(true);
      setError(null);
      const data = await mcpAPI.runOffensiveTest(target, testScenarios);
      setScanResults(data);
      toast.success('Offensive test suite completed');
    } catch (err) {
      console.error('Error running offensive test:', err);
      setError('Offensive test failed');
      toast.error('Offensive test failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* MCP Server Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">MCP Server Status</h3>
          <button
            onClick={fetchMCPStatus}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </button>
        </div>
        
        {mcpStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(mcpStatus).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  {getStatusIcon(status.status)}
                  <span className="ml-2 text-sm font-medium text-gray-900 capitalize">
                    {name.replace('_', ' ')}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  status.status === 'online' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {status.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">
            <LoadingSpinner size="sm" text="Loading server status..." />
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => runScan('basic')}
            disabled={loading}
            className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <Target className="h-5 w-5 text-blue-600 mr-2" />
            <span className="text-sm font-medium">Basic Scan</span>
          </button>
          
          <button
            onClick={() => runScan('aggressive')}
            disabled={loading}
            className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <Zap className="h-5 w-5 text-orange-600 mr-2" />
            <span className="text-sm font-medium">Aggressive Scan</span>
          </button>
          
          <button
            onClick={() => runScan('vulnerability')}
            disabled={loading}
            className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <Shield className="h-5 w-5 text-red-600 mr-2" />
            <span className="text-sm font-medium">Vuln Scan</span>
          </button>
          
          <button
            onClick={runOffensiveTest}
            disabled={loading}
            className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <Terminal className="h-5 w-5 text-purple-600 mr-2" />
            <span className="text-sm font-medium">Full Test Suite</span>
          </button>
        </div>
      </div>

      {/* Scan Results */}
      {scanResults && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Scan Results</h3>
            <button
              onClick={() => setScanResults(null)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>
          
          <div className="space-y-4">
            {scanResults.scan_result && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Scan Output</h4>
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <pre>{scanResults.scan_result.output || 'No output available'}</pre>
                </div>
              </div>
            )}
            
            {scanResults.offensive_test_result && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Test Suite Results</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Total Tests:</span>
                    <span className="font-medium">{scanResults.offensive_test_result.total_tests}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Successful:</span>
                    <span className="font-medium text-green-600">
                      {scanResults.offensive_test_result.successful_tests}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Success Rate:</span>
                    <span className="font-medium">
                      {scanResults.offensive_test_result.success_rate}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Overall Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      scanResults.offensive_test_result.overall_status === 'PASS'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {scanResults.offensive_test_result.overall_status}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-center">
            <LoadingSpinner text="Running security tests..." />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MCPTools;
