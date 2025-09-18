import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAutoRefresh, useRealtimeData } from '../hooks/useAutoRefresh';
import { VirtualizedList } from './VirtualizedList';
import { OptimizedImage } from './OptimizedImage';
import { RealtimeNotifications } from './RealtimeNotifications';
import { useRealtime } from './RealtimeConnection';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  Users, 
  Shield,
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react';

/**
 * Optimized Dashboard with real-time updates and performance optimizations
 */
const OptimizedDashboard = () => {
  const { isConnected } = useRealtime();
  const [dashboardData, setDashboardData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/dashboard');
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      return await response.json();
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      throw error;
    }
  }, []);

  // Fetch alerts data
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/alerts?limit=50');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      return data.alerts || [];
    } catch (error) {
      console.error('Alerts fetch error:', error);
      throw error;
    }
  }, []);

  // Fetch statistics
  const fetchStatistics = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/statistics');
      if (!response.ok) throw new Error('Failed to fetch statistics');
      return await response.json();
    } catch (error) {
      console.error('Statistics fetch error:', error);
      throw error;
    }
  }, []);

  // Auto-refresh dashboard data
  const {
    data: dashboardData_,
    loading: dashboardLoading,
    error: dashboardError,
    lastUpdated: dashboardLastUpdated,
    refresh: refreshDashboard,
  } = useAutoRefresh({
    fetchFunction: fetchDashboardData,
    interval: 30000, // 30 seconds
    enabled: true,
    onSuccess: (data) => {
      setDashboardData(data);
    },
  });

  // Auto-refresh alerts
  const {
    data: alerts_,
    loading: alertsLoading,
    error: alertsError,
    refresh: refreshAlerts,
  } = useAutoRefresh({
    fetchFunction: fetchAlerts,
    interval: 15000, // 15 seconds
    enabled: true,
    onSuccess: (data) => {
      setAlerts(data);
    },
  });

  // Auto-refresh statistics
  const {
    data: statistics_,
    loading: statisticsLoading,
    error: statisticsError,
    refresh: refreshStatistics,
  } = useAutoRefresh({
    fetchFunction: fetchStatistics,
    interval: 60000, // 1 minute
    enabled: true,
    onSuccess: (data) => {
      setStatistics(data.statistics);
    },
  });

  // Real-time data updates
  const {
    data: realtimeData,
    loading: realtimeLoading,
    refresh: refreshRealtime,
  } = useRealtimeData({
    fetchFunction: fetchDashboardData,
    realtimeChannels: ['alerts', 'dashboard_updates'],
    enabled: isConnected,
    onRealtimeUpdate: (currentData, updateData) => {
      // Handle real-time updates
      if (updateData.type === 'new_alert') {
        setAlerts(prev => [updateData.data, ...prev].slice(0, 50));
      } else if (updateData.type === 'dashboard_update') {
        return { ...currentData, ...updateData.data };
      }
      return currentData;
    },
  });

  // Manual refresh all data
  const refreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refreshDashboard(),
        refreshAlerts(),
        refreshStatistics(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshDashboard, refreshAlerts, refreshStatistics]);

  // Memoized statistics cards
  const statisticsCards = useMemo(() => {
    if (!statistics) return [];

    return [
      {
        title: 'Total Alerts',
        value: statistics.total_alerts || 0,
        icon: AlertTriangle,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        change: '+12%',
        changeType: 'increase',
      },
      {
        title: 'High Severity',
        value: statistics.high_severity || 0,
        icon: Shield,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50',
        change: '+5%',
        changeType: 'increase',
      },
      {
        title: 'Resolved',
        value: statistics.resolved_alerts || 0,
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        change: '+8%',
        changeType: 'increase',
      },
      {
        title: 'Active Users',
        value: statistics.active_users || 0,
        icon: Users,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        change: '+2%',
        changeType: 'increase',
      },
    ];
  }, [statistics]);

  // Memoized recent alerts
  const recentAlerts = useMemo(() => {
    return alerts.slice(0, 10).map(alert => ({
      id: alert.id,
      source: alert.source,
      message: alert.message,
      severity: alert.severity,
      timestamp: alert.timestamp,
      status: alert.status,
    }));
  }, [alerts]);

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  // Get severity color
  const getSeverityColor = (severity) => {
    if (severity >= 7) return 'text-red-600 bg-red-50';
    if (severity >= 4) return 'text-orange-600 bg-orange-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'text-blue-600 bg-blue-50';
      case 'acknowledged': return 'text-yellow-600 bg-yellow-50';
      case 'investigating': return 'text-orange-600 bg-orange-50';
      case 'resolved': return 'text-green-600 bg-green-50';
      case 'false_positive': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="optimized-dashboard">
      {/* Header with connection status and refresh button */}
      <div className="dashboard-header flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Security Dashboard</h1>
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <span className={`text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {dashboardLastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {formatTimestamp(dashboardLastUpdated)}
            </span>
          )}
          <button
            onClick={refreshAll}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statisticsCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                  <div className="flex items-center mt-2">
                    <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                    <span className="text-sm text-green-600">{card.change}</span>
                  </div>
                </div>
                <div className={`p-3 rounded-full ${card.bgColor}`}>
                  <Icon className={`w-6 h-6 ${card.color}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
          </div>
          <div className="p-6">
            {alertsLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-600">Loading alerts...</span>
              </div>
            ) : (
              <VirtualizedList
                items={recentAlerts}
                itemHeight={80}
                height={400}
                renderItem={(alert) => (
                  <div className="flex items-center space-x-4 p-4 hover:bg-gray-50 rounded-lg">
                    <div className={`w-3 h-3 rounded-full ${getSeverityColor(alert.severity).split(' ')[1]}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {alert.source}
                        </p>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(alert.status)}`}>
                          {alert.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 truncate">{alert.message}</p>
                      <p className="text-xs text-gray-500">{formatTimestamp(alert.timestamp)}</p>
                    </div>
                  </div>
                )}
              />
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">System Status</h2>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Status</span>
              <span className="flex items-center text-sm text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Healthy
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <span className="flex items-center text-sm text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Real-time</span>
              <span className={`flex items-center text-sm ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                {isConnected ? (
                  <CheckCircle className="w-4 h-4 mr-1" />
                ) : (
                  <AlertTriangle className="w-4 h-4 mr-1" />
                )}
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Cache</span>
              <span className="flex items-center text-sm text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Active
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Notifications */}
      <RealtimeNotifications
        maxNotifications={20}
        autoClose={true}
        autoCloseDelay={5000}
        enableSound={true}
        enableDesktopNotifications={true}
        className="fixed top-4 right-4 z-50"
      />
    </div>
  );
};

export default OptimizedDashboard;
