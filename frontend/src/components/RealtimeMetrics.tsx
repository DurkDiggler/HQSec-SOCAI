import React, { useEffect, useState } from 'react';
import { Activity, TrendingUp, AlertTriangle, Clock } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Card } from './layout/Card';
import { LineChart } from './charts/LineChart';
import type { TimeSeriesData } from '../types';

interface RealtimeMetricsProps {
  className?: string;
}

interface MetricsData {
  alertsPerMinute: number;
  avgResponseTime: number;
  activeAlerts: number;
  resolvedToday: number;
  trends: TimeSeriesData[];
}

const RealtimeMetrics: React.FC<RealtimeMetricsProps> = ({ className }) => {
  const [metrics, setMetrics] = useState<MetricsData>({
    alertsPerMinute: 0,
    avgResponseTime: 0,
    activeAlerts: 0,
    resolvedToday: 0,
    trends: [],
  });

  const [isLive, setIsLive] = useState(false);

  const { isConnected, lastMessage } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'metrics_update') {
        setMetrics(prev => ({
          ...prev,
          ...message.data,
        }));
        setIsLive(true);
        
        // Reset live indicator after 2 seconds
        setTimeout(() => setIsLive(false), 2000);
      }
    },
  });

  // Mock data for demonstration
  useEffect(() => {
    if (!isConnected) {
      // Generate mock data when not connected
      const mockMetrics: MetricsData = {
        alertsPerMinute: Math.floor(Math.random() * 10) + 1,
        avgResponseTime: Math.random() * 2 + 0.5,
        activeAlerts: Math.floor(Math.random() * 50) + 10,
        resolvedToday: Math.floor(Math.random() * 100) + 20,
        trends: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - (9 - i) * 60000).toISOString(),
          value: Math.floor(Math.random() * 20) + 5,
          label: 'Alerts',
        })),
      };
      setMetrics(mockMetrics);
    }
  }, [isConnected]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)}ms`;
    }
    return `${seconds.toFixed(1)}s`;
  };

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Real-time Metrics
        </h3>
        <div className="flex items-center space-x-2">
          <div className={`h-2 w-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {isLive ? 'Live' : 'Static'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card padding="md">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <Activity className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Alerts/min
              </p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {metrics.alertsPerMinute}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-2 rounded-lg bg-green-100 dark:bg-green-900">
              <Clock className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Avg Response
              </p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {formatTime(metrics.avgResponseTime)}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-2 rounded-lg bg-yellow-100 dark:bg-yellow-900">
              <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Active Alerts
              </p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {formatNumber(metrics.activeAlerts)}
              </p>
            </div>
          </div>
        </Card>

        <Card padding="md">
          <div className="flex items-center">
            <div className="flex-shrink-0 p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <TrendingUp className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Resolved Today
              </p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {formatNumber(metrics.resolvedToday)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {metrics.trends.length > 0 && (
        <Card title="Alert Trends (Last 10 minutes)" padding="lg">
          <LineChart
            data={metrics.trends}
            height={200}
            lines={[
              { dataKey: 'value', name: 'Alerts', color: '#3B82F6' }
            ]}
            showGrid
            showTooltip
          />
        </Card>
      )}
    </div>
  );
};

export default RealtimeMetrics;
