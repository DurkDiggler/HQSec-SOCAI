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
  Ticket
} from 'lucide-react';
import { alertsAPI, statisticsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    severity: '',
    source: '',
    category: ''
  });
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0,
    hasMore: false
  });
  const [availableFilters, setAvailableFilters] = useState({});
  const [updatingStatus, setUpdatingStatus] = useState(null);

  useEffect(() => {
    fetchAlerts();
    fetchAvailableFilters();
    
    // Refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [filters, pagination.skip]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = {
        skip: pagination.skip,
        limit: pagination.limit,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
      };
      
      const data = await alertsAPI.getAlerts(params);
      setAlerts(data.alerts);
      setPagination(prev => ({
        ...prev,
        total: data.pagination.total,
        hasMore: data.pagination.has_more
      }));
      setError(null);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to load alerts');
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableFilters = async () => {
    try {
      const data = await statisticsAPI.getFilters();
      setAvailableFilters(data);
    } catch (err) {
      console.error('Error fetching filters:', err);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const handleStatusUpdate = async (alertId, newStatus) => {
    try {
      setUpdatingStatus(alertId);
      await alertsAPI.updateAlertStatus(alertId, newStatus);
      
      // Update local state
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, status: newStatus }
          : alert
      ));
      
      toast.success('Alert status updated successfully');
    } catch (err) {
      console.error('Error updating alert status:', err);
      toast.error('Failed to update alert status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const loadMore = () => {
    setPagination(prev => ({
      ...prev,
      skip: prev.skip + prev.limit
    }));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'new':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'acknowledged':
        return <AlertTriangle className="h-4 w-4 text-blue-600" />;
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'false_positive':
        return <XCircle className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSeverityBadge = (severity) => {
    if (severity >= 7) {
      return <span className="badge badge-high">High</span>;
    } else if (severity >= 4) {
      return <span className="badge badge-medium">Medium</span>;
    } else {
      return <span className="badge badge-low">Low</span>;
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      new: 'badge-new',
      acknowledged: 'badge-acknowledged',
      investigating: 'badge-investigating',
      resolved: 'badge-resolved',
      false_positive: 'badge-false-positive',
    };
    
    return (
      <span className={`badge ${statusClasses[status] || 'badge-new'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (loading && alerts.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Loading alerts..." />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Security Alerts</h1>
        <p className="text-gray-600 mt-2">
          Monitor and manage security events
        </p>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  className="form-input pl-10"
                  placeholder="Search alerts..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                className="form-select"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="">All Statuses</option>
                {availableFilters.statuses?.map(status => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity
              </label>
              <select
                className="form-select"
                value={filters.severity}
                onChange={(e) => handleFilterChange('severity', e.target.value)}
              >
                <option value="">All Severities</option>
                <option value="7">High (7-10)</option>
                <option value="4">Medium (4-6)</option>
                <option value="0">Low (0-3)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <select
                className="form-select"
                value={filters.source}
                onChange={(e) => handleFilterChange('source', e.target.value)}
              >
                <option value="">All Sources</option>
                {availableFilters.sources?.map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                className="form-select"
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <option value="">All Categories</option>
                {availableFilters.categories?.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-gray-600">
              Showing {alerts.length} of {pagination.total} alerts
            </div>
            <button
              onClick={fetchAlerts}
              className="btn btn-outline btn-sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="card">
        <div className="card-body p-0">
          {alerts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No alerts found</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {alerts.map((alert) => (
                <div key={alert.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusIcon(alert.status)}
                        <Link
                          to={`/alerts/${alert.id}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate"
                        >
                          {alert.event_type || 'Unknown Event'}
                        </Link>
                        {getSeverityBadge(alert.severity)}
                        {getStatusBadge(alert.status)}
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {alert.message || 'No message available'}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Source: {alert.source || 'Unknown'}</span>
                        {alert.ip && <span>IP: {alert.ip}</span>}
                        {alert.username && <span>User: {alert.username}</span>}
                        <span>
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      {alert.email_sent && (
                        <span className="text-green-600" title="Email sent">
                          <Mail className="h-4 w-4" />
                        </span>
                      )}
                      {alert.ticket_created && (
                        <span className="text-blue-600" title="Ticket created">
                          <Ticket className="h-4 w-4" />
                        </span>
                      )}
                      
                      <select
                        className="form-select text-xs"
                        value={alert.status}
                        onChange={(e) => handleStatusUpdate(alert.id, e.target.value)}
                        disabled={updatingStatus === alert.id}
                      >
                        <option value="new">New</option>
                        <option value="acknowledged">Acknowledged</option>
                        <option value="investigating">Investigating</option>
                        <option value="resolved">Resolved</option>
                        <option value="false_positive">False Positive</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Load More */}
      {pagination.hasMore && (
        <div className="mt-6 text-center">
          <button
            onClick={loadMore}
            className="btn btn-outline"
            disabled={loading}
          >
            {loading ? <LoadingSpinner size="sm" text="" /> : 'Load More'}
          </button>
        </div>
      )}
    </div>
  );
};

export default Alerts;
