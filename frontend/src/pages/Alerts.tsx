import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
  Mail,
  Ticket,
  Eye,
  MoreVertical,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { useGetAlertsQuery, useUpdateAlertStatusMutation } from '../store/api';
import { setFilters, setSelectedAlerts, clearSelection } from '../store/slices/alertsSlice';
import { Card, Grid, Container } from '../components/layout';
import { Button, LoadingSpinner } from '../components/ui';
import { Input, Select, Checkbox } from '../components/forms';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import type { Alert, AlertFilters, Severity } from '../types';

const Alerts: React.FC = () => {
  const dispatch = useAppDispatch();
  const { filters, selectedAlerts, sortField, sortOrder, viewMode } = useAppSelector((state) => state.alerts);
  
  const [localFilters, setLocalFilters] = useState<AlertFilters>({
    search: '',
    status: '',
    severity: undefined,
    source: '',
    category: '',
    skip: 0,
    limit: 50,
  });

  const [showFilters, setShowFilters] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState<number | null>(null);

  const { 
    data: alertsData, 
    isLoading, 
    error, 
    refetch 
  } = useGetAlertsQuery(filters);

  const [updateAlertStatus] = useUpdateAlertStatusMutation();

  const alerts = alertsData?.data || [];
  const pagination = alertsData?.pagination || { skip: 0, limit: 50, total: 0, has_more: false };

  useEffect(() => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      refetch();
    }, 30000);
    return () => clearInterval(interval);
  }, [refetch]);

  const handleFilterChange = (key: keyof AlertFilters, value: any) => {
    const newFilters = { ...localFilters, [key]: value, skip: 0 };
    setLocalFilters(newFilters);
    dispatch(setFilters(newFilters));
  };

  const handleSearch = () => {
    dispatch(setFilters(localFilters));
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      search: '',
      status: '',
      severity: undefined,
      source: '',
      category: '',
      skip: 0,
      limit: 50,
    };
    setLocalFilters(clearedFilters);
    dispatch(setFilters(clearedFilters));
  };

  const handleSelectAlert = (alertId: number) => {
    const newSelection = selectedAlerts.includes(alertId)
      ? selectedAlerts.filter(id => id !== alertId)
      : [...selectedAlerts, alertId];
    dispatch(setSelectedAlerts(newSelection));
  };

  const handleSelectAll = () => {
    if (selectedAlerts.length === alerts.length) {
      dispatch(clearSelection());
    } else {
      dispatch(setSelectedAlerts(alerts.map(alert => alert.id)));
    }
  };

  const handleStatusUpdate = async (alertId: number, status: string) => {
    try {
      setUpdatingStatus(alertId);
      await updateAlertStatus({
        id: alertId,
        status,
        assigned_to: null,
        notes: null
      }).unwrap();
      
      toast.success('Alert status updated successfully');
      refetch();
    } catch (error: any) {
      toast.error(error?.data?.message || 'Failed to update alert status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const getSeverityColor = (severity: number): string => {
    if (severity >= 8) return 'text-red-600 bg-red-100';
    if (severity >= 6) return 'text-orange-600 bg-orange-100';
    if (severity >= 4) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getSeverityLabel = (severity: number): string => {
    if (severity >= 8) return 'Critical';
    if (severity >= 6) return 'High';
    if (severity >= 4) return 'Medium';
    return 'Low';
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'new': return 'text-blue-600 bg-blue-100';
      case 'investigating': return 'text-yellow-600 bg-yellow-100';
      case 'resolved': return 'text-green-600 bg-green-100';
      case 'false_positive': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading alerts..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error loading alerts</h3>
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Security Alerts</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {pagination.total.toLocaleString()} total alerts
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="secondary"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
            <Button
              variant="secondary"
              onClick={() => refetch()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <Card title="Filters" padding="lg">
            <Grid cols={3} gap="md">
              <Input
                label="Search"
                placeholder="Search alerts..."
                value={localFilters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                leftIcon={<Search className="h-4 w-4 text-gray-400" />}
              />
              
              <Select
                label="Status"
                placeholder="All statuses"
                value={localFilters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                options={[
                  { value: '', label: 'All statuses' },
                  { value: 'new', label: 'New' },
                  { value: 'investigating', label: 'Investigating' },
                  { value: 'resolved', label: 'Resolved' },
                  { value: 'false_positive', label: 'False Positive' },
                ]}
              />
              
              <Select
                label="Severity"
                placeholder="All severities"
                value={localFilters.severity?.toString() || ''}
                onChange={(e) => handleFilterChange('severity', e.target.value ? parseInt(e.target.value) : undefined)}
                options={[
                  { value: '', label: 'All severities' },
                  { value: '8', label: 'Critical (8-10)' },
                  { value: '6', label: 'High (6-7)' },
                  { value: '4', label: 'Medium (4-5)' },
                  { value: '2', label: 'Low (2-3)' },
                ]}
              />
            </Grid>
            
            <div className="flex items-center justify-end space-x-3 mt-4">
              <Button variant="ghost" onClick={handleClearFilters}>
                Clear Filters
              </Button>
              <Button onClick={handleSearch}>
                Apply Filters
              </Button>
            </div>
          </Card>
        )}

        {/* Alerts Table */}
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <Checkbox
                      checked={selectedAlerts.length === alerts.length && alerts.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Alert
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {alerts.map((alert: Alert) => (
                  <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Checkbox
                        checked={selectedAlerts.includes(alert.id)}
                        onChange={() => handleSelectAlert(alert.id)}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {alert.event_type || 'Unknown Event'}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                            {alert.message || 'No message available'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(alert.severity)}`}>
                        {getSeverityLabel(alert.severity)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(alert.status)}`}>
                        {alert.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {alert.source || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <Link
                          to={`/alerts/${alert.id}`}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                        
                        {alert.status === 'new' && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleStatusUpdate(alert.id, 'investigating')}
                            loading={updatingStatus === alert.id}
                          >
                            Investigate
                          </Button>
                        )}
                        
                        {alert.status === 'investigating' && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleStatusUpdate(alert.id, 'resolved')}
                            loading={updatingStatus === alert.id}
                          >
                            Resolve
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white dark:bg-gray-900 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <Button
                variant="secondary"
                disabled={pagination.skip === 0}
                onClick={() => handleFilterChange('skip', Math.max(0, pagination.skip - pagination.limit))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={!pagination.has_more}
                onClick={() => handleFilterChange('skip', pagination.skip + pagination.limit)}
              >
                Next
              </Button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  Showing <span className="font-medium">{pagination.skip + 1}</span> to{' '}
                  <span className="font-medium">
                    {Math.min(pagination.skip + pagination.limit, pagination.total)}
                  </span>{' '}
                  of <span className="font-medium">{pagination.total}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={pagination.skip === 0}
                    onClick={() => handleFilterChange('skip', Math.max(0, pagination.skip - pagination.limit))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={!pagination.has_more}
                    onClick={() => handleFilterChange('skip', pagination.skip + pagination.limit)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </nav>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </Container>
  );
};

export default Alerts;
