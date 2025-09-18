import React, { useState, useEffect, useCallback, useRef } from 'react';

const RealtimeConnection = ({ children, onAlert, onNotification, onError }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/realtime/ws`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        
        // Subscribe to default channels
        subscribeToChannels(['alerts', 'notifications', 'alert_updates']);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          
          switch (message.type) {
            case 'new_alert':
              onAlert && onAlert(message.data);
              break;
            case 'alert_update':
              onAlert && onAlert(message);
              break;
            case 'notification':
              onNotification && onNotification(message.data);
              break;
            case 'connection_established':
              console.log('Connection established:', message);
              break;
            case 'error':
              console.error('WebSocket error:', message.message);
              onError && onError(message);
              break;
            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          setConnectionStatus('reconnecting');
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectDelay * Math.pow(2, reconnectAttempts));
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setConnectionStatus('failed');
          console.error('Max reconnection attempts reached');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        onError && onError({ type: 'websocket_error', error });
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
      onError && onError({ type: 'connection_error', error });
    }
  }, [reconnectAttempts, onAlert, onNotification, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const subscribeToChannels = useCallback((channels) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        channels: channels
      }));
    }
  }, []);

  const unsubscribeFromChannels = useCallback((channels) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        channels: channels
      }));
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const ping = useCallback(() => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Ping to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(ping, 30000); // Ping every 30 seconds
      return () => clearInterval(pingInterval);
    }
  }, [isConnected, ping]);

  const contextValue = {
    isConnected,
    connectionStatus,
    reconnectAttempts,
    lastMessage,
    subscribeToChannels,
    unsubscribeFromChannels,
    sendMessage,
    ping,
    connect,
    disconnect
  };

  return (
    <RealtimeContext.Provider value={contextValue}>
      {children}
    </RealtimeContext.Provider>
  );
};

// Create context
const RealtimeContext = React.createContext();

// Hook to use realtime context
export const useRealtime = () => {
  const context = React.useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeConnection');
  }
  return context;
};

export default RealtimeConnection;
