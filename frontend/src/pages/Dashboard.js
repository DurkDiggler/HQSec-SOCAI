import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  XCircle,
  Mail,
  Ticket,
  TrendingUp,
  Activity
} from 'lucide-react';
import { statisticsAPI } from '../services/api';
import StatCard from '../components/StatCard';
import Chart from '../components/Chart';
import RecentAlerts from '../components/RecentAlerts';
import LoadingSpinner from '../components/LoadingSpinner';
import RealtimeAlerts from '../components/RealtimeAlerts';
import RealtimeNotifications from '../components/RealtimeNotifications';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await statisticsAPI.getDashboardData(7);
      setDashboardData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const { statistics, recent_alerts } = dashboardData;

  const statCards = [
    {
      title: 'Total Alerts',
      value: statistics.total_alerts,
      icon: AlertTriangle,
      color: 'blue',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'High Severity',
      value: statistics.high_severity,
      icon: AlertTriangle,
      color: 'red',
      change: '+5%',
      changeType: 'negative'
    },
    {
      title: 'New Alerts',
      value: statistics.new_alerts,
      icon: Clock,
      color: 'yellow',
      change: '+8%',
      changeType: 'neutral'
    },
    {
      title: 'Resolved',
      value: statistics.resolved_alerts,
      icon: CheckCircle,
      color: 'green',
      change: '+15%',
      changeType: 'positive'
    },
    {
      title: 'Emails Sent',
      value: statistics.emails_sent,
      icon: Mail,
      color: 'blue',
      change: '+3%',
      changeType: 'positive'
    },
    {
      title: 'Tickets Created',
      value: statistics.tickets_created,
      icon: Ticket,
      color: 'purple',
      change: '+7%',
      changeType: 'positive'
    }
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Overview of security alerts and system status
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {statCards.map((card, index) => (
          <StatCard key={index} {...card} />
        ))}
      </div>

      {/* Charts and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Alerts Over Time Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Alerts Over Time</h3>
            <p className="text-sm text-gray-600">Last 7 days</p>
          </div>
          <div className="card-body">
            <Chart
              type="line"
              data={[
                { name: 'Mon', alerts: 12 },
                { name: 'Tue', alerts: 19 },
                { name: 'Wed', alerts: 8 },
                { name: 'Thu', alerts: 15 },
                { name: 'Fri', alerts: 22 },
                { name: 'Sat', alerts: 6 },
                { name: 'Sun', alerts: 9 }
              ]}
              xKey="name"
              yKey="alerts"
              color="#2563eb"
            />
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Severity Distribution</h3>
            <p className="text-sm text-gray-600">Current period</p>
          </div>
          <div className="card-body">
            <Chart
              type="pie"
              data={[
                { name: 'High', value: statistics.high_severity, color: '#dc2626' },
                { name: 'Medium', value: statistics.medium_severity, color: '#d97706' },
                { name: 'Low', value: statistics.low_severity, color: '#059669' }
              ]}
              nameKey="name"
              valueKey="value"
            />
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Recent Alerts</h3>
              <p className="text-sm text-gray-600">Latest security events</p>
            </div>
            <Link
              to="/alerts"
              className="btn btn-outline btn-sm"
            >
              View All
            </Link>
          </div>
        </div>
        <div className="card-body p-0">
          <RecentAlerts alerts={recent_alerts} />
        </div>
      </div>

      {/* Real-time Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-time Alerts */}
        <div className="card">
          <div className="card-body">
            <RealtimeAlerts maxAlerts={10} />
          </div>
        </div>

        {/* Real-time Notifications */}
        <div className="card">
          <div className="card-body">
            <RealtimeNotifications maxNotifications={15} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
