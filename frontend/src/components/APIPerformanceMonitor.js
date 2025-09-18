import React, { useState, useEffect } from 'react';
import { Activity, Zap, Database, Clock, TrendingUp, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';

const APIPerformanceMonitor = () => {
  const [overview, setOverview] = useState(null);
  const [cacheStats, setCacheStats] = useState(null);
  const [rateLimitStats, setRateLimitStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPerformanceData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchPerformanceData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      const [overviewRes, cacheRes, rateLimitRes] = await Promise.all([
        fetch('/api/v1/performance/overview'),
        fetch('/api/v1/performance/cache'),
        fetch('/api/v1/performance/rate-limits')
      ]);

      if (overviewRes.ok) {
        const overviewData = await overviewRes.json();
        setOverview(overviewData.overview);
      }

      if (cacheRes.ok) {
        const cacheData = await cacheRes.json();
        setCacheStats(cacheData.cache_stats);
      }

      if (rateLimitRes.ok) {
        const rateLimitData = await rateLimitRes.json();
        setRateLimitStats(rateLimitData.rate_limit_stats);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch performance data');
      console.error('Performance monitoring error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearCache = async (pattern = null) => {
    try {
      const response = await fetch('/api/v1/performance/cache/clear', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pattern })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Cache cleared: ${result.message}`);
        fetchPerformanceData(); // Refresh data
      } else {
        alert('Failed to clear cache');
      }
    } catch (err) {
      console.error('Cache clear error:', err);
      alert('Failed to clear cache');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'excellent':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'good':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'fair':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'poor':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent':
        return 'text-green-600';
      case 'good':
        return 'text-blue-600';
      case 'fair':
        return 'text-yellow-600';
      case 'poor':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Performance Overview */}
      {overview && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              API Performance Overview
            </h3>
            <div className="flex items-center">
              {getStatusIcon(overview.status)}
              <span className={`ml-2 font-medium ${getStatusColor(overview.status)}`}>
                {overview.status.toUpperCase()}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Health Score</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{overview.health_score}/100</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-4 h-4 text-orange-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Issues</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{overview.issues?.length || 0}</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Last Updated</span>
              </div>
              <p className="text-sm text-gray-900">
                {new Date(overview.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>

          {/* Issues List */}
          {overview.issues && overview.issues.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Current Issues:</h4>
              <ul className="space-y-1">
                {overview.issues.map((issue, index) => (
                  <li key={index} className="text-sm text-red-600 flex items-center">
                    <AlertTriangle className="w-3 h-3 mr-2" />
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Cache Performance */}
      {cacheStats && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Cache Performance
            </h3>
            <div className="flex space-x-2">
              <button
                onClick={() => clearCache()}
                className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700"
              >
                Clear All Cache
              </button>
              <button
                onClick={() => clearCache('alerts:*')}
                className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-orange-600 hover:bg-orange-700"
              >
                Clear Alerts Cache
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Status</span>
              </div>
              <p className="text-lg font-bold text-blue-600 capitalize">
                {cacheStats.status || 'Unknown'}
              </p>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Hit Rate</span>
              </div>
              <p className="text-lg font-bold text-green-600">
                {cacheStats.hit_rate?.toFixed(1) || 0}%
              </p>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <Activity className="w-4 h-4 text-purple-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Memory Used</span>
              </div>
              <p className="text-lg font-bold text-purple-600">
                {cacheStats.used_memory || '0B'}
              </p>
            </div>
            
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-orange-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Uptime</span>
              </div>
              <p className="text-lg font-bold text-orange-600">
                {Math.floor((cacheStats.uptime_seconds || 0) / 3600)}h
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Rate Limiting Stats */}
      {rateLimitStats && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2" />
            Rate Limiting
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <Activity className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Status</span>
              </div>
              <p className="text-lg font-bold text-blue-600 capitalize">
                {rateLimitStats.status || 'Unknown'}
              </p>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Total Keys</span>
              </div>
              <p className="text-lg font-bold text-green-600">
                {rateLimitStats.total_keys || 0}
              </p>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="w-4 h-4 text-purple-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Total Requests</span>
              </div>
              <p className="text-lg font-bold text-purple-600">
                {rateLimitStats.global_stats?.total_requests || 0}
              </p>
            </div>
          </div>

          {/* Endpoint Stats */}
          {rateLimitStats.endpoints && Object.keys(rateLimitStats.endpoints).length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Endpoint Statistics:</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Endpoint</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Keys</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Requests</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(rateLimitStats.endpoints).map(([endpoint, stats]) => (
                      <tr key={endpoint}>
                        <td className="px-4 py-2 text-sm text-gray-900">{endpoint}</td>
                        <td className="px-4 py-2 text-sm text-gray-500">{stats.keys || 0}</td>
                        <td className="px-4 py-2 text-sm text-gray-500">{stats.total_requests || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Actions</h3>
        
        <div className="flex space-x-4">
          <button
            onClick={fetchPerformanceData}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </button>
          
          <button
            onClick={() => clearCache()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <Database className="w-4 h-4 mr-2" />
            Clear All Cache
          </button>
        </div>
      </div>
    </div>
  );
};

export default APIPerformanceMonitor;
