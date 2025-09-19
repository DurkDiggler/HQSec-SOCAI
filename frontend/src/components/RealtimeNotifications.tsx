import React, { useEffect, useState } from 'react';
import { X, Bell, AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { markNotificationAsRead, removeNotification } from '../store/slices/uiSlice';
import { useWebSocket } from '../hooks/useWebSocket';
import { Button } from './ui/Button';
import { formatDistanceToNow } from 'date-fns';
import type { Notification } from '../types';

interface RealtimeNotificationsProps {
  maxNotifications?: number;
  autoHide?: boolean;
  autoHideDelay?: number;
}

const RealtimeNotifications: React.FC<RealtimeNotificationsProps> = ({
  maxNotifications = 5,
  autoHide = true,
  autoHideDelay = 5000,
}) => {
  const dispatch = useAppDispatch();
  const { notifications } = useAppSelector((state) => state.ui);
  const [isOpen, setIsOpen] = useState(false);

  const { isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'notification') {
        // Auto-hide notification after delay
        if (autoHide) {
          setTimeout(() => {
            if (message.data?.id) {
              dispatch(removeNotification(message.data.id));
            }
          }, autoHideDelay);
        }
      }
    },
  });

  const unreadNotifications = notifications.filter(n => !n.read);
  const displayNotifications = notifications.slice(0, maxNotifications);

  const handleMarkAsRead = (notificationId: string) => {
    dispatch(markNotificationAsRead(notificationId));
  };

  const handleRemove = (notificationId: string) => {
    dispatch(removeNotification(notificationId));
  };

  const handleMarkAllAsRead = () => {
    unreadNotifications.forEach(notification => {
      dispatch(markNotificationAsRead(notification.id));
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'alert':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'system':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      default:
        return <Bell className="h-4 w-4 text-gray-500" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'alert':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case 'system':
        return 'border-l-green-500 bg-green-50 dark:bg-green-900/20';
      case 'info':
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
      >
        <Bell className="h-5 w-5" />
        {unreadNotifications.length > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadNotifications.length > 99 ? '99+' : unreadNotifications.length}
          </span>
        )}
        {!isConnected && (
          <div className="absolute -bottom-1 -right-1 h-2 w-2 bg-yellow-500 rounded-full" />
        )}
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Notifications
              </h3>
              <div className="flex items-center space-x-2">
                {unreadNotifications.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleMarkAllAsRead}
                  >
                    Mark all read
                  </Button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="flex items-center mt-2 text-sm text-gray-500 dark:text-gray-400">
              <div className={`h-2 w-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`} />
              {isConnected ? 'Connected' : 'Reconnecting...'}
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {displayNotifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {displayNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 border-l-4 ${getNotificationColor(notification.type)} ${
                      !notification.read ? 'font-medium' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        {getNotificationIcon(notification.type)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 dark:text-white">
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                          </p>
                          {notification.link && (
                            <a
                              href={notification.link}
                              className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mt-1 block"
                            >
                              View details →
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 ml-2">
                        {!notification.read && (
                          <button
                            onClick={() => handleMarkAsRead(notification.id)}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                            title="Mark as read"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleRemove(notification.id)}
                          className="text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="Remove"
                        >
                          <XCircle className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {notifications.length > maxNotifications && (
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-center">
              <button className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
                View all notifications ({notifications.length})
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RealtimeNotifications;
