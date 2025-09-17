import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  AlertTriangle, 
  Clock, 
  CheckCircle, 
  XCircle,
  Mail,
  Ticket,
  User,
  Globe,
  Calendar,
  MessageSquare,
  Shield,
  Activity,
  Brain,
  Terminal
} from 'lucide-react';
import { alertsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import AIInsights from '../components/AIInsights';
import MCPTools from '../components/MCPTools';
import toast from 'react-hot-toast';

const AlertDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchAlert();
  }, [id]);

  const fetchAlert = async () => {
    try {
      setLoading(true);
      const data = await alertsAPI.getAlert(id);
      setAlert(data.alert);
      setError(null);
    } catch (err) {
      console.error('Error fetching alert:', err);
      setError('Failed to load alert details');
      toast.error('Failed to load alert details');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    try {
      setUpdating(true);
      await alertsAPI.updateAlertStatus(id, newStatus);
      setAlert(prev => ({ ...prev, status: newStatus }));
      toast.success('Alert status updated successfully');
    } catch (err) {
      console.error('Error updating alert status:', err);
      toast.error('Failed to update alert status');
    } finally {
      setUpdating(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'new':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case 'acknowledged':
        return <AlertTriangle className="h-5 w-5 text-blue-600" />;
      case 'resolved':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'false_positive':
        return <XCircle className="h-5 w-5 text-gray-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getSeverityBadge = (severity) => {
    if (severity >= 7) {
      return <span className="badge badge-high">High Severity</span>;
    } else if (severity >= 4) {
      return <span className="badge badge-medium">Medium Severity</span>;
    } else {
      return <span className="badge badge-low">Low Severity</span>;
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Loading alert details..." />
      </div>
    );
  }

  if (error || !alert) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-800">{error || 'Alert not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/alerts')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Alerts
        </button>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Alert #{alert.id}
            </h1>
            <p className="text-gray-600 mt-2">
              {alert.event_type || 'Unknown Event'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {getSeverityBadge(alert.severity)}
            {getStatusBadge(alert.status)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Alert Details */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Alert Details</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-lg">
                    {alert.message || 'No message available'}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Source
                    </label>
                    <p className="text-sm text-gray-900">{alert.source || 'Unknown'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Event Type
                    </label>
                    <p className="text-sm text-gray-900">{alert.event_type || 'Unknown'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      IP Address
                    </label>
                    <p className="text-sm text-gray-900">{alert.ip || 'N/A'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username
                    </label>
                    <p className="text-sm text-gray-900">{alert.username || 'N/A'}</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timestamp
                    </label>
                    <p className="text-sm text-gray-900">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Created
                    </label>
                    <p className="text-sm text-gray-900">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* IOCs */}
          {alert.iocs && (alert.iocs.ips?.length > 0 || alert.iocs.domains?.length > 0) && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Indicators of Compromise</h3>
              </div>
              <div className="card-body">
                {alert.iocs.ips?.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      IP Addresses
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {alert.iocs.ips.map((ip, index) => (
                        <span key={index} className="badge badge-blue">
                          {ip}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {alert.iocs.domains?.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Domains
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {alert.iocs.domains.map((domain, index) => (
                        <span key={index} className="badge badge-blue">
                          {domain}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Intelligence Data */}
          {alert.intel_data && alert.intel_data.ips?.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Threat Intelligence</h3>
              </div>
              <div className="card-body">
                {alert.intel_data.ips.map((intel, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 mb-4 last:mb-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{intel.indicator}</span>
                      <span className="badge badge-blue">Score: {intel.score}</span>
                    </div>
                    {intel.labels?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {intel.labels.map((label, labelIndex) => (
                          <span key={labelIndex} className="badge badge-yellow text-xs">
                            {label}
                          </span>
                        ))}
                      </div>
                    )}
                    {intel.sources && Object.keys(intel.sources).length > 0 && (
                      <div className="text-xs text-gray-600">
                        Sources: {Object.keys(intel.sources).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw Data */}
          {alert.raw_data && Object.keys(alert.raw_data).length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Raw Event Data</h3>
              </div>
              <div className="card-body">
                <pre className="text-xs text-gray-600 bg-gray-50 p-4 rounded-lg overflow-x-auto">
                  {JSON.stringify(alert.raw_data, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Management */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Status Management</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Status
                  </label>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(alert.status)}
                    <span className="text-sm font-medium text-gray-900">
                      {alert.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Update Status
                  </label>
                  <select
                    className="form-select"
                    value={alert.status}
                    onChange={(e) => handleStatusUpdate(e.target.value)}
                    disabled={updating}
                  >
                    <option value="new">New</option>
                    <option value="acknowledged">Acknowledged</option>
                    <option value="investigating">Investigating</option>
                    <option value="resolved">Resolved</option>
                    <option value="false_positive">False Positive</option>
                  </select>
                </div>

                {alert.assigned_to && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assigned To
                    </label>
                    <p className="text-sm text-gray-900">{alert.assigned_to}</p>
                  </div>
                )}

                {alert.notes && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                      {alert.notes}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Scoring */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Scoring</h3>
            </div>
            <div className="card-body">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Base Score</span>
                  <span className="text-sm font-medium">{alert.base_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Intel Score</span>
                  <span className="text-sm font-medium">{alert.intel_score}</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-sm font-medium text-gray-900">Final Score</span>
                  <span className="text-sm font-bold text-gray-900">{alert.final_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Category</span>
                  <span className="text-sm font-medium">{alert.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Recommended Action</span>
                  <span className="text-sm font-medium">{alert.recommended_action}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Actions Taken */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Actions Taken</h3>
            </div>
            <div className="card-body">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-gray-600" />
                    <span className="text-sm text-gray-600">Email Sent</span>
                  </div>
                  <span className={`text-sm font-medium ${alert.email_sent ? 'text-green-600' : 'text-gray-400'}`}>
                    {alert.email_sent ? 'Yes' : 'No'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Ticket className="h-4 w-4 text-gray-600" />
                    <span className="text-sm text-gray-600">Ticket Created</span>
                  </div>
                  <span className={`text-sm font-medium ${alert.ticket_created ? 'text-green-600' : 'text-gray-400'}`}>
                    {alert.ticket_created ? 'Yes' : 'No'}
                  </span>
                </div>

                {alert.ticket_id && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Ticket ID</span>
                    <span className="text-sm font-medium text-blue-600">{alert.ticket_id}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* AI Analysis Section */}
        <div className="lg:col-span-2">
          <AIInsights alertId={parseInt(id)} />
        </div>
      </div>

      {/* MCP Tools Section */}
      <div className="mt-8">
        <div className="flex items-center mb-4">
          <Terminal className="h-5 w-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">Security Testing Tools</h2>
        </div>
        <MCPTools target={alert?.ip || 'localhost'} />
      </div>
    </div>
  );
};

export default AlertDetail;
