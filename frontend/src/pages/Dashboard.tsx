import React from 'react';
import { useAppSelector } from '../store/hooks';
import { useGetDashboardDataQuery, useGetStatisticsQuery } from '../store/api';
import { Card, Grid, Container } from '../components/layout';
import { LineChart, BarChart, PieChart } from '../components/charts';
import { LoadingSpinner } from '../components/ui';
import { 
  AlertTriangle, 
  Shield, 
  Activity, 
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { data: dashboardData, isLoading: isDashboardLoading, error: dashboardError } = useGetDashboardDataQuery({ days: 7 });
  const { data: statistics, isLoading: isStatsLoading, error: statsError } = useGetStatisticsQuery({ days: 7 });

  if (isDashboardLoading || isStatsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    );
  }

  if (dashboardError || statsError) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading dashboard</h3>
        <p className="mt-1 text-sm text-gray-500">
          {dashboardError?.message || statsError?.message || 'Something went wrong'}
        </p>
      </div>
    );
  }

  const stats = statistics?.data || {};
  const dashboard = dashboardData?.data || {};

  // Mock data for demonstration
  const alertTrends = [
    { timestamp: '2024-01-01', value: 45, label: 'High' },
    { timestamp: '2024-01-02', value: 52, label: 'High' },
    { timestamp: '2024-01-03', value: 38, label: 'High' },
    { timestamp: '2024-01-04', value: 61, label: 'High' },
    { timestamp: '2024-01-05', value: 47, label: 'High' },
    { timestamp: '2024-01-06', value: 55, label: 'High' },
    { timestamp: '2024-01-07', value: 42, label: 'High' },
  ];

  const topSources = [
    { name: 'Firewall', value: 45 },
    { name: 'IDS/IPS', value: 32 },
    { name: 'Antivirus', value: 28 },
    { name: 'Email Security', value: 15 },
    { name: 'Web Filter', value: 12 },
  ];

  const severityDistribution = [
    { name: 'Critical', value: 8, color: '#EF4444' },
    { name: 'High', value: 25, color: '#F59E0B' },
    { name: 'Medium', value: 45, color: '#3B82F6' },
    { name: 'Low', value: 22, color: '#10B981' },
  ];

  const statCards = [
    {
      title: 'Total Alerts',
      value: stats.total_alerts || 0,
      change: '+12%',
      changeType: 'positive' as const,
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      title: 'High Severity',
      value: stats.high_severity || 0,
      change: '+8%',
      changeType: 'positive' as const,
      icon: Shield,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      title: 'Resolved',
      value: stats.resolved_alerts || 0,
      change: '+15%',
      changeType: 'positive' as const,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'False Positives',
      value: stats.false_positives || 0,
      change: '-5%',
      changeType: 'negative' as const,
      icon: XCircle,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
  ];

  return (
    <Container>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Security Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Overview of your security posture and recent activity
          </p>
        </div>

        {/* Stats Cards */}
        <Grid cols={4} gap="md">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.title} padding="md">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4 flex-1">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {stat.title}
                    </p>
                    <div className="flex items-baseline">
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                        {stat.value.toLocaleString()}
                      </p>
                      <p className={`ml-2 text-sm font-medium ${
                        stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stat.change}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </Grid>

        {/* Charts Row */}
        <Grid cols={2} gap="lg">
          {/* Alert Trends */}
          <Card title="Alert Trends (7 days)" padding="lg">
            <LineChart
              data={alertTrends}
              height={300}
              lines={[
                { dataKey: 'value', name: 'Alerts', color: '#3B82F6' }
              ]}
            />
          </Card>

          {/* Top Sources */}
          <Card title="Top Alert Sources" padding="lg">
            <BarChart
              data={topSources}
              height={300}
              orientation="horizontal"
              bars={[
                { dataKey: 'value', name: 'Count', color: '#10B981' }
              ]}
            />
          </Card>
        </Grid>

        {/* Severity Distribution */}
        <Card title="Severity Distribution" padding="lg">
          <div className="flex items-center justify-center">
            <PieChart
              data={severityDistribution}
              height={400}
              showLabel
              innerRadius={60}
              outerRadius={120}
            />
          </div>
        </Card>

        {/* Recent Activity */}
        <Card title="Recent Activity" padding="lg">
          <div className="space-y-4">
            {[
              { time: '2 minutes ago', event: 'High severity alert from Firewall', type: 'alert' },
              { time: '5 minutes ago', event: 'User login from new location', type: 'auth' },
              { time: '12 minutes ago', event: 'Malware detected and quarantined', type: 'threat' },
              { time: '18 minutes ago', event: 'System backup completed', type: 'system' },
              { time: '25 minutes ago', event: 'New user account created', type: 'user' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.type === 'alert' ? 'bg-red-500' :
                    activity.type === 'auth' ? 'bg-blue-500' :
                    activity.type === 'threat' ? 'bg-orange-500' :
                    'bg-gray-500'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white">
                    {activity.event}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Container>
  );
};

export default Dashboard;
