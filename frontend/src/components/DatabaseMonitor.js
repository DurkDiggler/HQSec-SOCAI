import React, { useState, useEffect } from 'react';
import { Activity, Database, TrendingUp, AlertTriangle, CheckCircle, Clock, BarChart3 } from 'lucide-react';

const DatabaseMonitor = () => {
  const [metrics, setMetrics] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDatabaseData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDatabaseData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDatabaseData = async () => {
    try {
      setLoading(true);
      const [metricsRes, statsRes, healthRes] = await Promise.all([
        fetch('/api/v1/database/metrics'),
        fetch('/api/v1/database/statistics'),
        fetch('/api/v1/database/health')
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData.database_metrics);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStatistics(statsData.table_statistics);
      }

      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealth(healthData);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch database data');
      console.error('Database monitoring error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
    }
  };

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'warning':
        return 'text-orange-600';
      default:
        return 'text-red-600';
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
      {/* Health Status */}
      {health && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Database Health
            </h3>
            <div className="flex items-center">
              {getHealthIcon(health.status)}
              <span className={`ml-2 font-medium ${getHealthColor(health.status)}`}>
                {health.status.toUpperCase()}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <Activity className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Total Alerts</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{health.alert_count?.toLocaleString() || 0}</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Pool Utilization</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {health.connection_pool_utilization?.toFixed(1) || 0}%
              </p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-4 h-4 text-red-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Slow Queries</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {health.slow_queries_detected ? 'Yes' : 'No'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Performance Metrics
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <Clock className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Query Count</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">{metrics.query_count?.toLocaleString() || 0}</p>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <TrendingUp className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Avg Query Time</span>
              </div>
              <p className="text-2xl font-bold text-green-600">
                {metrics.avg_query_time?.toFixed(3) || 0}ms
              </p>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="w-4 h-4 text-purple-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Pool Size</span>
              </div>
              <p className="text-2xl font-bold text-purple-600">
                {metrics.connection_pool_stats?.pool_size || 0}
              </p>
            </div>
            
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center">
                <Activity className="w-4 h-4 text-orange-500 mr-2" />
                <span className="text-sm font-medium text-gray-600">Checked Out</span>
              </div>
              <p className="text-2xl font-bold text-orange-600">
                {metrics.connection_pool_stats?.checked_out || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Table Statistics */}
      {statistics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Table Statistics
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Table
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rows
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Inserts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Updates
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Deletes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(statistics).map(([tableName, stats]) => (
                  <tr key={tableName}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {tableName}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.live_rows?.toLocaleString() || stats.row_count?.toLocaleString() || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.inserts?.toLocaleString() || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.updates?.toLocaleString() || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {stats.deletes?.toLocaleString() || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slow Queries */}
      {metrics?.slow_queries && metrics.slow_queries.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
            Slow Queries
          </h3>
          
          <div className="space-y-3">
            {metrics.slow_queries.slice(0, 5).map((query, index) => (
              <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="text-sm text-gray-700 font-mono">
                      {query.query}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Executed at: {new Date(query.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="ml-4 text-right">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      {query.execution_time.toFixed(3)}s
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Actions</h3>
        
        <div className="flex space-x-4">
          <button
            onClick={fetchDatabaseData}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Activity className="w-4 h-4 mr-2" />
            Refresh Data
          </button>
          
          <button
            onClick={async () => {
              try {
                const response = await fetch('/api/v1/database/optimize', { method: 'POST' });
                if (response.ok) {
                  alert('Database optimization completed successfully!');
                  fetchDatabaseData();
                } else {
                  alert('Database optimization failed');
                }
              } catch (err) {
                alert('Failed to run database optimization');
              }
            }}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            Optimize Database
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatabaseMonitor;
