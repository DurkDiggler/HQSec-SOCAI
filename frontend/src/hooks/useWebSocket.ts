import { useEffect, useRef, useState, useCallback } from 'react';
import { websocketManager, WebSocketMessage } from '../services/websocket';

export interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  autoConnect?: boolean;
  reconnectOnMount?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connectionState: number;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (message: WebSocketMessage) => void;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  lastMessage: WebSocketMessage | null;
  error: string | null;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    autoConnect = true,
    reconnectOnMount = true,
  } = options;

  const [isConnected, setIsConnected] = useState(websocketManager.isConnected);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messageHandlerRef = useRef<((message: WebSocketMessage) => void) | null>(null);

  const connect = useCallback(async () => {
    try {
      setError(null);
      await websocketManager.connect();
      setIsConnected(true);
      onConnect?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMessage);
      onError?.(err as Event);
    }
  }, [onConnect, onError]);

  const disconnect = useCallback(() => {
    websocketManager.disconnect();
    setIsConnected(false);
    onDisconnect?.();
  }, [onDisconnect]);

  const send = useCallback((message: WebSocketMessage) => {
    websocketManager.send(message);
  }, []);

  const subscribe = useCallback((channel: string) => {
    websocketManager.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    websocketManager.unsubscribe(channel);
  }, []);

  // Set up message handler
  useEffect(() => {
    messageHandlerRef.current = (message: WebSocketMessage) => {
      setLastMessage(message);
      onMessage?.(message);
    };

    // Override the websocket manager's message handler to include our callback
    const originalHandleMessage = (websocketManager as any).handleMessage;
    (websocketManager as any).handleMessage = (message: WebSocketMessage) => {
      originalHandleMessage.call(websocketManager, message);
      messageHandlerRef.current?.(message);
    };

    return () => {
      // Restore original handler
      (websocketManager as any).handleMessage = originalHandleMessage;
    };
  }, [onMessage]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connect();
    }
  }, [autoConnect, connect, isConnected]);

  // Reconnect on mount if needed
  useEffect(() => {
    if (reconnectOnMount && !isConnected) {
      connect();
    }
  }, [reconnectOnMount, connect, isConnected]);

  // Monitor connection state
  useEffect(() => {
    const checkConnection = () => {
      const connected = websocketManager.isConnected;
      if (connected !== isConnected) {
        setIsConnected(connected);
        if (connected) {
          onConnect?.();
        } else {
          onDisconnect?.();
        }
      }
    };

    const interval = setInterval(checkConnection, 1000);
    return () => clearInterval(interval);
  }, [isConnected, onConnect, onDisconnect]);

  return {
    isConnected,
    connectionState: websocketManager.connectionState,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    lastMessage,
    error,
  };
};

export default useWebSocket;
