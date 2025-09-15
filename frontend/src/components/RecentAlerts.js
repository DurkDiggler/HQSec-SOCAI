import React from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { AlertTriangle, Clock, CheckCircle, XCircle } from 'lucide-react';

const RecentAlerts = ({ alerts = [] }) => {
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

  if (alerts.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
        <p>No recent alerts</p>
      </div>
    );
  }

  return (
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
                  {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              {alert.email_sent && (
                <span className="text-green-600" title="Email sent">
                  📧
                </span>
              )}
              {alert.ticket_created && (
                <span className="text-blue-600" title="Ticket created">
                  🎫
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RecentAlerts;
