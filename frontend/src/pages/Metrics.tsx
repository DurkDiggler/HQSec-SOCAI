import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Activity, 
  Clock,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react';
import { useGetStatisticsQuery, useGetTopSourcesQuery, useGetTopEventTypesQuery, useGetTopIPsQuery } from '../store/api';
import { Card, Grid, Container } from '../components/layout';
import { Button, LoadingSpinner } from '../components/ui';
import { Select } from '../components/forms';
import { LineChart, BarChart, PieChart } from '../components/charts';
import type { TimeSeriesData, ChartData } from '../types';

const Metrics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<number>(7);
  
  const { data: statistics, isLoading: isStatsLoading, error: statsError } = useGetStatisticsQuery({ days: timeRange });
  const { data: topSources, isLoading: isSourcesLoading } = useGetTopSourcesQuery({ limit: 10 });
  const { data: topEventTypes, isLoading: isEventTypesLoading } = useGetTopEventTypesQuery({ limit: 10 });
  const { data: topIPs, isLoading: isIPsLoading } = useGetTopIPsQuery({ limit: 10 });

  const stats = statistics?.data || {};
  const sources = topSources?.data || [];
  const eventTypes = topEventTypes?.data || [];
  const ips = topIPs?.data || [];

  // Mock data for demonstration
  const alertTrends: TimeSeriesData[] = [
    { timestamp: '2024-01-01', value: 45, label: 'High' },
    { timestamp: '2024-01-02', value: 52, label: 'High' },
    { timestamp: '2024-01-03', value: 38, label: 'High' },
    { timestamp: '2024-01-04', value: 61, label: 'High' },
    { timestamp: '2024-01-05', value: 47, label: 'High' },
    { timestamp: '2024-01-06', value: 55, label: 'High' },
    { timestamp: '2024-01-07', value: 42, label: 'High' },
  ];

  const severityDistribution: ChartData[] = [
    { name: 'Critical', value: 8, color: '#EF4444' },
    { name: 'High', value: 25, color: '#F59E0B' },
    { name: 'Medium', value: 45, color: '#3B82F6' },
    { name: 'Low', value: 22, color: '#10B981' },
  ];

  const responseTimeData: TimeSeriesData[] = [
    { timestamp: '2024-01-01', value: 2.3, label: 'Avg Response Time' },
    { timestamp: '2024-01-02', value: 1.8, label: 'Avg Response Time' },
    { timestamp: '2024-01-03', value: 2.1, label: 'Avg Response Time' },
    { timestamp: '2024-01-04', value: 1.9, label: 'Avg Response Time' },
    { timestamp: '2024-01-05', value: 2.0, label: 'Avg Response Time' },
    { timestamp: '2024-01-06', value: 1.7, label: 'Avg Response Time' },
    { timestamp: '2024-01-07', value: 2.2, label: 'Avg Response Time' },
  ];

  const isLoading = isStatsLoading || isSourcesLoading || isEventTypesLoading || isIPsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading metrics..." />
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="text-center py-12">
        <Activity className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading metrics</h3>
        <p className="mt-1 text-sm text-gray-500">
          {statsError?.message || 'Something went wrong'}
        </p>
      </div>
    );
  }

  return (
    <Container>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Metrics & Analytics</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Performance metrics and security analytics
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Select
              value={timeRange.toString()}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              options={[
                { value: '1', label: 'Last 24 hours' },
                { value: '7', label: 'Last 7 days' },
                { value: '30', label: 'Last 30 days' },
                { value: '90', label: 'Last 90 days' },
              ]}
            />
            <Button variant="secondary">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="secondary">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <Grid cols={4} gap="md">
          <Card padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
                <BarChart3 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Alerts</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {stats.total_alerts?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-red-100 dark:bg-red-900">
                <TrendingUp className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">High Severity</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {stats.high_severity?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-green-100 dark:bg-green-900">
                <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Resolved</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {stats.resolved_alerts?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </Card>

          <Card padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900">
                <Clock className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Response</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {stats.avg_response_time?.toFixed(1) || 0}s
                </p>
              </div>
            </div>
          </Card>
        </Grid>

        {/* Charts Row 1 */}
        <Grid cols={2} gap="lg">
          <Card title="Alert Trends" padding="lg">
            <LineChart
              data={alertTrends}
              height={300}
              lines={[
                { dataKey: 'value', name: 'Alerts', color: '#3B82F6' }
              ]}
            />
          </Card>

          <Card title="Severity Distribution" padding="lg">
            <PieChart
              data={severityDistribution}
              height={300}
              showLabel
              innerRadius={40}
              outerRadius={80}
            />
          </Card>
        </Grid>

        {/* Charts Row 2 */}
        <Grid cols={2} gap="lg">
          <Card title="Top Alert Sources" padding="lg">
            <BarChart
              data={sources.map(source => ({ name: source.source, value: source.count }))}
              height={300}
              orientation="horizontal"
              bars={[
                { dataKey: 'value', name: 'Count', color: '#10B981' }
              ]}
            />
          </Card>

          <Card title="Response Time Trends" padding="lg">
            <LineChart
              data={responseTimeData}
              height={300}
              lines={[
                { dataKey: 'value', name: 'Response Time (s)', color: '#F59E0B' }
              ]}
            />
          </Card>
        </Grid>

        {/* Top Event Types and IPs */}
        <Grid cols={2} gap="lg">
          <Card title="Top Event Types" padding="lg">
            <div className="space-y-3">
              {eventTypes.map((event, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-3" />
                    <span className="text-sm text-gray-900 dark:text-white">
                      {event.event_type || 'Unknown'}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {event.count}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Top IP Addresses" padding="lg">
            <div className="space-y-3">
              {ips.map((ip, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-red-500 rounded-full mr-3" />
                    <span className="text-sm font-mono text-gray-900 dark:text-white">
                      {ip.ip || 'Unknown'}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {ip.count}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </Grid>

        {/* Performance Metrics */}
        <Card title="System Performance" padding="lg">
          <Grid cols={3} gap="md">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">99.9%</div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Uptime</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">2.1s</div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Avg Response Time</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">1.2k</div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Requests/min</p>
            </div>
          </Grid>
        </Card>
      </div>
    </Container>
  );
};

export default Metrics;
