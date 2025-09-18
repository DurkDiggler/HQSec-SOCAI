import React, { useState, useEffect, useCallback } from 'react';
import { useRealtime } from './RealtimeConnection';

const RealtimeNotifications = ({ maxNotifications = 20, autoHide = true, hideDelay = 5000 }) => {
  const { isConnected, connectionStatus } = useRealtime();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleNotification = useCallback((notificationData) => {
    const newNotification = {
      id: Date.now() + Math.random(),
      title: notificationData.title || 'Notification',
      message: notificationData.message || '',
      type: notificationData.type || 'info',
      priority: notificationData.priority || 'normal',
      timestamp: new Date().toISOString(),
      read: false
    };

    setNotifications(prev => [newNotification, ...prev].slice(0, maxNotifications));
    setUnreadCount(prev => prev + 1);

    // Auto-hide notification after delay
    if (autoHide) {
      setTimeout(() => {
        setNotifications(prev => 
          prev.map(notif => 
            notif.id === newNotification.id 
              ? { ...notif, read: true }
              : notif
          )
        );
      }, hideDelay);
    }
  }, [maxNotifications, autoHide, hideDelay]);

  // Set up real-time handlers
  useEffect(() => {
    const handleNotificationMessage = (data) => {
      if (data.type === 'notification') {
        handleNotification(data.data);
      }
    };

    // This would be passed from parent component
    // For now, we'll simulate it
    return () => {};
  }, [handleNotification]);

  const markAsRead = (notificationId) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, read: true }))
    );
    setUnreadCount(0);
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  const getNotificationColor = (type, priority) => {
    if (priority === 'high') {
      return 'border-l-red-500 bg-red-50';
    }
    if (priority === 'critical') {
      return 'border-l-red-600 bg-red-100';
    }
    
    switch (type) {
      case 'success': return 'border-l-green-500 bg-green-50';
      case 'warning': return 'border-l-yellow-500 bg-yellow-50';
      case 'error': return 'border-l-red-500 bg-red-50';
      case 'info': return 'border-l-blue-500 bg-blue-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="realtime-notifications">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Notifications
          {unreadCount > 0 && (
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {unreadCount} unread
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
          
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Mark all read
            </button>
          )}
          
          {notifications.length > 0 && (
            <button
              onClick={clearAll}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🔔</div>
            <p>No notifications yet</p>
            {!isConnected && (
              <p className="text-sm text-red-500 mt-2">
                Connection required for real-time notifications
              </p>
            )}
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`border-l-4 p-3 rounded-r-lg transition-all duration-200 ${
                getNotificationColor(notification.type, notification.priority)
              } ${!notification.read ? 'shadow-sm' : 'opacity-75'}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start space-x-2 flex-1">
                  <span className="text-lg">
                    {getNotificationIcon(notification.type)}
                  </span>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className={`text-sm font-medium ${
                        !notification.read ? 'text-gray-900' : 'text-gray-600'
                      }`}>
                        {notification.title}
                      </h4>
                      
                      {notification.priority === 'high' && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          High
                        </span>
                      )}
                      {notification.priority === 'critical' && (
                        <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-red-200 text-red-900">
                          Critical
                        </span>
                      )}
                    </div>
                    
                    <p className={`text-sm ${
                      !notification.read ? 'text-gray-700' : 'text-gray-500'
                    }`}>
                      {notification.message}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 ml-2">
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(notification.timestamp)}
                  </span>
                  
                  {!notification.read && (
                    <button
                      onClick={() => markAsRead(notification.id)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="mt-4 text-xs text-gray-500 text-center">
          {notifications.filter(n => !n.read).length} unread notifications
        </div>
      )}
    </div>
  );
};

export default RealtimeNotifications;
