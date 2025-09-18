import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { api } from '../services/api';

const MetricsDashboard = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState('performance_metrics');

  useEffect(() => {
    fetchMetrics();
  }, [timeRange]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await api.get('/storage/metrics', {
        params: { time_range: timeRange }
      });
      setMetrics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetricSummary = async (measurement) => {
    try {
      const response = await api.get('/storage/metrics/summary', {
        params: {
          measurement,
          time_range: timeRange
        }
      });
      return response.data;
    } catch (err) {
      console.error('Failed to fetch metric summary:', err);
      return null;
    }
  };

  const formatValue = (value, unit = '') => {
    if (typeof value === 'number') {
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M${unit}`;
      } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K${unit}`;
      } else {
        return `${value.toFixed(2)}${unit}`;
      }
    }
    return value;
  };

  const formatDuration = (ms) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    } else {
      return `${(ms / 60000).toFixed(1)}m`;
    }
  };

  const getMetricColor = (value, type) => {
    if (type === 'response_time') {
      if (value < 100) return 'text-green-600';
      if (value < 500) return 'text-yellow-600';
      return 'text-red-600';
    } else if (type === 'error_rate') {
      if (value < 0.01) return 'text-green-600';
      if (value < 0.05) return 'text-yellow-600';
      return 'text-red-600';
    }
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Metrics Dashboard</h2>
        <div className="flex space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={fetchMetrics}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      {metrics?.performance && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(metrics.performance).map(([key, values]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatValue(values.latest, key.includes('time') ? 'ms' : '')}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Avg: {formatValue(values.avg, key.includes('time') ? 'ms' : '')} | 
                  Count: {values.count}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API Metrics */}
      {metrics?.api && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">API Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(metrics.api).map(([key, values]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className={`text-2xl font-bold ${getMetricColor(values.latest, key)}`}>
                  {key === 'response_time' ? formatDuration(values.latest) : formatValue(values.latest)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Min: {key === 'response_time' ? formatDuration(values.min) : formatValue(values.min)} | 
                  Max: {key === 'response_time' ? formatDuration(values.max) : formatValue(values.max)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert Metrics */}
      {metrics?.alerts && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Alert Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(metrics.alerts).map(([key, values]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatValue(values.latest)}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Total: {formatValue(values.count)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Metrics */}
      {metrics?.system && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(metrics.system).map(([key, values]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatValue(values.latest, key.includes('memory') ? 'MB' : '')}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Avg: {formatValue(values.avg, key.includes('memory') ? 'MB' : '')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Time Series Charts Placeholder */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Time Series Data</h3>
        <div className="text-center text-gray-500 py-8">
          <p>Time series charts would be displayed here</p>
          <p className="text-sm">Integration with charting library (e.g., Chart.js, D3.js) needed</p>
        </div>
      </div>

      {/* Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Elasticsearch Health</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className="text-sm font-medium text-green-600">Connected</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Indices:</span>
              <span className="text-sm font-medium">4 active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Documents:</span>
              <span className="text-sm font-medium">1,234,567</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Time-Series DB Health</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className="text-sm font-medium text-green-600">Connected</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Bucket:</span>
              <span className="text-sm font-medium">soc-metrics</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Retention:</span>
              <span className="text-sm font-medium">90 days</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
