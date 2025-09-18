import React, { useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { useRealtime } from './RealtimeConnection';
import { Bell, AlertTriangle, CheckCircle, Info, X, Volume2, VolumeX } from 'lucide-react';

/**
 * Real-time notification system with sound, persistence, and management
 */
const RealtimeNotifications = ({
  maxNotifications = 50,
  autoClose = true,
  autoCloseDelay = 5000,
  enableSound = true,
  enableDesktopNotifications = true,
  position = 'top-right',
  className = '',
}) => {
  const { isConnected, lastMessage } = useRealtime();
  const [notifications, setNotifications] = useState([]);
  const [isMuted, setIsMuted] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const audioRef = useRef(null);
  const notificationTimeoutRefs = useRef(new Map());

  // Request notification permission
  useEffect(() => {
    if (enableDesktopNotifications && 'Notification' in window) {
      Notification.requestPermission();
    }
  }, [enableDesktopNotifications]);

  // Load notifications from localStorage
  useEffect(() => {
    const savedNotifications = localStorage.getItem('soc-agent-notifications');
    if (savedNotifications) {
      try {
        const parsed = JSON.parse(savedNotifications);
        setNotifications(parsed);
        setUnreadCount(parsed.filter(n => !n.read).length);
      } catch (error) {
        console.error('Failed to load notifications:', error);
      }
    }
  }, []);

  // Save notifications to localStorage
  const saveNotifications = useCallback((newNotifications) => {
    setNotifications(newNotifications);
    localStorage.setItem('soc-agent-notifications', JSON.stringify(newNotifications));
    setUnreadCount(newNotifications.filter(n => !n.read).length);
  }, []);

  // Play notification sound
  const playNotificationSound = useCallback(() => {
    if (!enableSound || isMuted || !audioRef.current) return;
    
    try {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(error => {
        console.warn('Failed to play notification sound:', error);
      });
    } catch (error) {
      console.warn('Audio playback error:', error);
    }
  }, [enableSound, isMuted]);

  // Show desktop notification
  const showDesktopNotification = useCallback((notification) => {
    if (!enableDesktopNotifications || !('Notification' in window) || Notification.permission !== 'granted') {
      return;
    }

    try {
      const desktopNotification = new Notification(notification.title, {
        body: notification.message,
        icon: notification.icon || '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.id,
        requireInteraction: notification.priority === 'high',
        silent: isMuted,
      });

      desktopNotification.onclick = () => {
        window.focus();
        desktopNotification.close();
        // Handle notification click (e.g., navigate to relevant page)
        if (notification.action) {
          notification.action();
        }
      };

      // Auto-close desktop notification
      if (autoClose && notification.priority !== 'high') {
        setTimeout(() => {
          desktopNotification.close();
        }, autoCloseDelay);
      }
    } catch (error) {
      console.warn('Failed to show desktop notification:', error);
    }
  }, [enableDesktopNotifications, autoClose, autoCloseDelay, isMuted]);

  // Add new notification
  const addNotification = useCallback((notificationData) => {
    const notification = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      type: notificationData.type || 'info',
      priority: notificationData.priority || 'normal',
      title: notificationData.title || 'New Notification',
      message: notificationData.message || '',
      icon: notificationData.icon,
      action: notificationData.action,
      read: false,
      persistent: notificationData.persistent || false,
    };

    // Add to notifications list
    setNotifications(prev => {
      const newNotifications = [notification, ...prev].slice(0, maxNotifications);
      saveNotifications(newNotifications);
      return newNotifications;
    });

    // Show toast notification
    const toastOptions = {
      duration: notification.priority === 'high' ? 0 : autoCloseDelay,
      position: position,
      style: {
        background: getNotificationColor(notification.type),
        color: '#fff',
        border: `1px solid ${getNotificationBorderColor(notification.type)}`,
      },
      icon: getNotificationIcon(notification.type),
    };

    toast(notification.message, toastOptions);

    // Play sound
    playNotificationSound();

    // Show desktop notification
    showDesktopNotification(notification);

    // Auto-close if not persistent
    if (!notification.persistent && autoClose) {
      const timeoutId = setTimeout(() => {
        markAsRead(notification.id);
      }, autoCloseDelay);
      notificationTimeoutRefs.current.set(notification.id, timeoutId);
    }

    return notification;
  }, [maxNotifications, saveNotifications, autoClose, autoCloseDelay, position, playNotificationSound, showDesktopNotification]);

  // Mark notification as read
  const markAsRead = useCallback((notificationId) => {
    setNotifications(prev => {
      const newNotifications = prev.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      );
      saveNotifications(newNotifications);
      return newNotifications;
    });

    // Clear timeout if exists
    const timeoutId = notificationTimeoutRefs.current.get(notificationId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      notificationTimeoutRefs.current.delete(notificationId);
    }
  }, [saveNotifications]);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => {
      const newNotifications = prev.map(n => ({ ...n, read: true }));
      saveNotifications(newNotifications);
      return newNotifications;
    });
  }, [saveNotifications]);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
    saveNotifications([]);
    
    // Clear all timeouts
    notificationTimeoutRefs.current.forEach(timeoutId => clearTimeout(timeoutId));
    notificationTimeoutRefs.current.clear();
  }, [saveNotifications]);

  // Remove specific notification
  const removeNotification = useCallback((notificationId) => {
    setNotifications(prev => {
      const newNotifications = prev.filter(n => n.id !== notificationId);
      saveNotifications(newNotifications);
      return newNotifications;
    });

    // Clear timeout if exists
    const timeoutId = notificationTimeoutRefs.current.get(notificationId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      notificationTimeoutRefs.current.delete(notificationId);
    }
  }, [saveNotifications]);

  // Handle real-time messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'new_alert':
        addNotification({
          type: 'alert',
          priority: 'high',
          title: 'New Security Alert',
          message: `Alert from ${lastMessage.data?.source || 'Unknown'}: ${lastMessage.data?.message || 'Security event detected'}`,
          icon: '🚨',
          action: () => {
            // Navigate to alerts page
            window.location.href = '/alerts';
          },
        });
        break;

      case 'alert_update':
        addNotification({
          type: 'info',
          priority: 'normal',
          title: 'Alert Updated',
          message: `Alert ${lastMessage.data?.id} status updated`,
          icon: '📝',
        });
        break;

      case 'notification':
        addNotification({
          type: lastMessage.data?.type || 'info',
          priority: lastMessage.data?.priority || 'normal',
          title: lastMessage.data?.title || 'Notification',
          message: lastMessage.data?.message || '',
          icon: lastMessage.data?.icon,
          action: lastMessage.data?.action,
        });
        break;

      case 'system_status':
        addNotification({
          type: lastMessage.data?.status === 'error' ? 'error' : 'info',
          priority: lastMessage.data?.status === 'error' ? 'high' : 'normal',
          title: 'System Status',
          message: lastMessage.data?.message || 'System status update',
          icon: lastMessage.data?.status === 'error' ? '⚠️' : '✅',
        });
        break;

      default:
        // Handle other message types
        break;
    }
  }, [lastMessage, addNotification]);

  // Get notification color based on type
  const getNotificationColor = (type) => {
    switch (type) {
      case 'error': return '#ef4444';
      case 'warning': return '#f59e0b';
      case 'success': return '#10b981';
      case 'alert': return '#dc2626';
      case 'info':
      default: return '#3b82f6';
    }
  };

  const getNotificationBorderColor = (type) => {
    switch (type) {
      case 'error': return '#dc2626';
      case 'warning': return '#d97706';
      case 'success': return '#059669';
      case 'alert': return '#b91c1c';
      case 'info':
      default: return '#2563eb';
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      case 'alert': return '🚨';
      case 'info':
      default: return 'ℹ️';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`realtime-notifications ${className}`}>
      {/* Audio element for notification sounds */}
      <audio
        ref={audioRef}
        preload="auto"
        style={{ display: 'none' }}
      >
        <source src="/notification.mp3" type="audio/mpeg" />
        <source src="/notification.wav" type="audio/wav" />
      </audio>

      {/* Notification Bell Icon */}
      <div className="notification-bell" style={{ position: 'relative' }}>
        <Bell 
          size={24} 
          className="cursor-pointer hover:text-blue-600 transition-colors"
          onClick={() => setIsMuted(!isMuted)}
        />
        {unreadCount > 0 && (
          <span 
            className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center"
            style={{ fontSize: '10px' }}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        {isMuted && (
          <VolumeX 
            size={16} 
            className="absolute -bottom-1 -right-1 text-red-500"
          />
        )}
      </div>

      {/* Notifications Panel */}
      <div className="notifications-panel" style={{ display: 'none' }}>
        <div className="notifications-header">
          <h3>Notifications</h3>
          <div className="notification-actions">
            <button onClick={markAllAsRead} disabled={unreadCount === 0}>
              Mark all read
            </button>
            <button onClick={clearAll}>
              Clear all
            </button>
          </div>
        </div>
        
        <div className="notifications-list">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`notification-item ${notification.read ? 'read' : 'unread'}`}
              onClick={() => markAsRead(notification.id)}
            >
              <div className="notification-icon">
                {getNotificationIcon(notification.type)}
              </div>
              <div className="notification-content">
                <div className="notification-title">{notification.title}</div>
                <div className="notification-message">{notification.message}</div>
                <div className="notification-timestamp">
                  {formatTimestamp(notification.timestamp)}
                </div>
              </div>
              <button
                className="notification-close"
                onClick={(e) => {
                  e.stopPropagation();
                  removeNotification(notification.id);
                }}
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RealtimeNotifications;