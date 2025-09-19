import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  AlertTriangle, 
  Clock, 
  User, 
  Mail, 
  Ticket,
  Shield,
  Activity,
  Brain,
  CheckCircle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { useGetAlertQuery, useUpdateAlertStatusMutation, useAnalyzeAlertMutation } from '../store/api';
import { Card, Container } from '../components/layout';
import { Button, LoadingSpinner } from '../components/ui';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import type { Alert } from '../types';

const AlertDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const alertId = parseInt(id || '0');

  const { 
    data: alertData, 
    isLoading, 
    error, 
    refetch 
  } = useGetAlertQuery(alertId);

  const [updateAlertStatus] = useUpdateAlertStatusMutation();
  const [analyzeAlert, { isLoading: isAnalyzing }] = useAnalyzeAlertMutation();

  const alert: Alert | undefined = alertData?.data;

  const handleStatusUpdate = async (status: string, assignedTo?: string, notes?: string) => {
    if (!alert) return;

    try {
      await updateAlertStatus({
        id: alert.id,
        status,
        assigned_to: assignedTo,
        notes
      }).unwrap();
      
      toast.success('Alert status updated successfully');
      refetch();
    } catch (error: any) {
      toast.error(error?.data?.message || 'Failed to update alert status');
    }
  };

  const handleAIAnalysis = async () => {
    if (!alert) return;

    try {
      await analyzeAlert(alert.id).unwrap();
      toast.success('AI analysis completed');
      refetch();
    } catch (error: any) {
      toast.error(error?.data?.message || 'Failed to perform AI analysis');
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
        <LoadingSpinner size="lg" text="Loading alert details..." />
      </div>
    );
  }

  if (error || !alert) {
    return (
      <Container>
        <div className="text-center py-12">
          <XCircle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Alert not found</h3>
          <p className="mt-1 text-sm text-gray-500">
            The alert you're looking for doesn't exist or has been removed.
          </p>
          <div className="mt-6 flex space-x-3 justify-center">
            <Button onClick={() => navigate('/alerts')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Alerts
            </Button>
            <Button variant="secondary" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/alerts')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Alerts
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Alert #{alert.id}
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {alert.event_type || 'Unknown Event'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              variant="secondary"
              onClick={() => refetch()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            
            {alert.status === 'new' && (
              <Button
                onClick={() => handleStatusUpdate('investigating')}
              >
                <Activity className="h-4 w-4 mr-2" />
                Start Investigation
              </Button>
            )}
            
            {alert.status === 'investigating' && (
              <Button
                onClick={() => handleStatusUpdate('resolved')}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Mark Resolved
              </Button>
            )}
          </div>
        </div>

        {/* Alert Overview */}
        <Grid cols={3} gap="md">
          <Card title="Severity" padding="md">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getSeverityColor(alert.severity)}`}>
                  {getSeverityLabel(alert.severity)}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  Score: {alert.final_score || alert.base_score || 0}/10
                </p>
              </div>
            </div>
          </Card>

          <Card title="Status" padding="md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {alert.status === 'resolved' ? (
                  <CheckCircle className="h-8 w-8 text-green-500" />
                ) : alert.status === 'false_positive' ? (
                  <XCircle className="h-8 w-8 text-gray-500" />
                ) : (
                  <Clock className="h-8 w-8 text-yellow-500" />
                )}
              </div>
              <div className="ml-3">
                <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(alert.status)}`}>
                  {alert.status.replace('_', ' ').toUpperCase()}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                  {alert.assigned_to ? `Assigned to ${alert.assigned_to}` : 'Unassigned'}
                </p>
              </div>
            </div>
          </Card>

          <Card title="Timeline" padding="md">
            <div className="space-y-2">
              <div className="flex items-center text-sm">
                <Clock className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-gray-600 dark:text-gray-300">
                  Created: {format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm')}
                </span>
              </div>
              <div className="flex items-center text-sm">
                <RefreshCw className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-gray-600 dark:text-gray-300">
                  Updated: {format(new Date(alert.updated_at), 'MMM dd, yyyy HH:mm')}
                </span>
              </div>
            </div>
          </Card>
        </Grid>

        {/* Alert Details */}
        <Grid cols={2} gap="lg">
          <Card title="Alert Information" padding="lg">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Event Type</label>
                <p className="text-sm text-gray-900 dark:text-white">{alert.event_type || 'Unknown'}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Source</label>
                <p className="text-sm text-gray-900 dark:text-white">{alert.source || 'Unknown'}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Category</label>
                <p className="text-sm text-gray-900 dark:text-white">{alert.category || 'Uncategorized'}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">IP Address</label>
                <p className="text-sm text-gray-900 dark:text-white font-mono">{alert.ip || 'N/A'}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Username</label>
                <p className="text-sm text-gray-900 dark:text-white">{alert.username || 'N/A'}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Message</label>
                <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                  {alert.message || 'No message available'}
                </p>
              </div>
            </div>
          </Card>

          <Card title="Actions & Analysis" padding="lg">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Mail className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-300">Email Sent</span>
                </div>
                <span className={`text-sm ${alert.email_sent ? 'text-green-600' : 'text-gray-400'}`}>
                  {alert.email_sent ? 'Yes' : 'No'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Ticket className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-300">Ticket Created</span>
                </div>
                <span className={`text-sm ${alert.ticket_created ? 'text-green-600' : 'text-gray-400'}`}>
                  {alert.ticket_created ? 'Yes' : 'No'}
                </span>
              </div>
              
              {alert.ticket_id && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Ticket ID</label>
                  <p className="text-sm text-gray-900 dark:text-white font-mono">{alert.ticket_id}</p>
                </div>
              )}
              
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  onClick={handleAIAnalysis}
                  loading={isAnalyzing}
                  className="w-full"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  Run AI Analysis
                </Button>
              </div>
            </div>
          </Card>
        </Grid>

        {/* IOCs and Intelligence Data */}
        {(alert.iocs && Object.keys(alert.iocs).length > 0) && (
          <Card title="Indicators of Compromise (IOCs)" padding="lg">
            <div className="space-y-3">
              {Object.entries(alert.iocs).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400 capitalize">
                    {key.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-gray-900 dark:text-white font-mono">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Notes */}
        {alert.notes && (
          <Card title="Notes" padding="lg">
            <p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
              {alert.notes}
            </p>
          </Card>
        )}
      </div>
    </Container>
  );
};

export default AlertDetail;
