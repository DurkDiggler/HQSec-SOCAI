import React, { useState, useEffect, useCallback } from 'react';
import { useRealtime } from './RealtimeConnection';

const RealtimeAlerts = ({ maxAlerts = 50, showTimestamp = true, showSource = true }) => {
  const { isConnected, connectionStatus } = useRealtime();
  const [alerts, setAlerts] = useState([]);
  const [newAlertCount, setNewAlertCount] = useState(0);
  const [lastAlertTime, setLastAlertTime] = useState(null);

  const handleNewAlert = useCallback((alertData) => {
    const newAlert = {
      id: alertData.id || Date.now(),
      source: alertData.source,
      event_type: alertData.event_type,
      severity: alertData.severity,
      message: alertData.message,
      timestamp: alertData.timestamp || new Date().toISOString(),
      category: alertData.category,
      iocs: alertData.iocs || [],
      scores: alertData.scores || {},
      recommended_action: alertData.recommended_action,
      status: alertData.status || 'new'
    };

    setAlerts(prevAlerts => {
      const updatedAlerts = [newAlert, ...prevAlerts].slice(0, maxAlerts);
      return updatedAlerts;
    });

    setNewAlertCount(prev => prev + 1);
    setLastAlertTime(new Date());
  }, [maxAlerts]);

  const handleAlertUpdate = useCallback((updateData) => {
    if (updateData.alert_id) {
      setAlerts(prevAlerts => 
        prevAlerts.map(alert => 
          alert.id === updateData.alert_id 
            ? { ...alert, ...updateData.data }
            : alert
        )
      );
    }
  }, []);

  // Set up real-time handlers
  useEffect(() => {
    const handleAlert = (data) => {
      if (data.type === 'new_alert') {
        handleNewAlert(data.data);
      } else if (data.type === 'alert_update') {
        handleAlertUpdate(data);
      }
    };

    // This would be passed from parent component
    // For now, we'll simulate it
    return () => {};
  }, [handleNewAlert, handleAlertUpdate]);

  const getSeverityColor = (severity) => {
    if (severity >= 8) return 'text-red-600 bg-red-100';
    if (severity >= 6) return 'text-orange-600 bg-orange-100';
    if (severity >= 4) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getSeverityLabel = (severity) => {
    if (severity >= 8) return 'Critical';
    if (severity >= 6) return 'High';
    if (severity >= 4) return 'Medium';
    return 'Low';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const clearNewAlertCount = () => {
    setNewAlertCount(0);
  };

  return (
    <div className="realtime-alerts">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Real-time Alerts
          {newAlertCount > 0 && (
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              {newAlertCount} new
            </span>
          )}
        </h3>
        
        <div className="flex items-center space-x-2">
          {/* Connection Status */}
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'reconnecting' ? 'bg-yellow-500' :
              connectionStatus === 'error' ? 'bg-red-500' :
              'bg-gray-500'
            }`}></div>
            <span className="text-sm text-gray-600 capitalize">
              {connectionStatus}
            </span>
          </div>
          
          {newAlertCount > 0 && (
            <button
              onClick={clearNewAlertCount}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📡</div>
            <p>Waiting for real-time alerts...</p>
            {!isConnected && (
              <p className="text-sm text-red-500 mt-2">
                Connection required for real-time updates
              </p>
            )}
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                    {getSeverityLabel(alert.severity)}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {alert.event_type || 'Unknown Event'}
                  </span>
                </div>
                
                {showTimestamp && (
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(alert.timestamp)}
                  </span>
                )}
              </div>

              <div className="mb-2">
                <p className="text-sm text-gray-700">{alert.message}</p>
              </div>

              <div className="flex justify-between items-center text-xs text-gray-500">
                <div className="flex items-center space-x-4">
                  {showSource && alert.source && (
                    <span>Source: {alert.source}</span>
                  )}
                  {alert.category && (
                    <span>Category: {alert.category}</span>
                  )}
                  {alert.scores && alert.scores.final && (
                    <span>Score: {alert.scores.final}</span>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs ${
                    alert.status === 'new' ? 'bg-blue-100 text-blue-800' :
                    alert.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' :
                    alert.status === 'investigating' ? 'bg-orange-100 text-orange-800' :
                    alert.status === 'resolved' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {alert.status}
                  </span>
                </div>
              </div>

              {/* IOCs */}
              {alert.iocs && alert.iocs.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <div className="text-xs text-gray-500 mb-1">IOCs:</div>
                  <div className="flex flex-wrap gap-1">
                    {alert.iocs.slice(0, 5).map((ioc, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                      >
                        {ioc}
                      </span>
                    ))}
                    {alert.iocs.length > 5 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                        +{alert.iocs.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {lastAlertTime && (
        <div className="mt-4 text-xs text-gray-500 text-center">
          Last alert: {formatTimestamp(lastAlertTime)}
        </div>
      )}
    </div>
  );
};

export default RealtimeAlerts;
