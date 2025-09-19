import { store } from '../store';
import { addAlert, updateAlert } from '../store/slices/alertsSlice';
import { addNotification } from '../store/slices/uiSlice';
import type { Alert, Notification } from '../types';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  client_id?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isManualDisconnect = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config,
    };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.isManualDisconnect = false;

      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          
          if (!this.isManualDisconnect && this.reconnectAttempts < this.config.maxReconnectAttempts!) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.isManualDisconnect = true;
    this.stopHeartbeat();
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  subscribe(channel: string): void {
    this.send({
      type: 'subscribe',
      data: { channel },
    });
  }

  unsubscribe(channel: string): void {
    this.send({
      type: 'unsubscribe',
      data: { channel },
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket connection established:', message.client_id);
        // Subscribe to default channels
        this.subscribe('alerts');
        this.subscribe('notifications');
        this.subscribe('metrics');
        break;

      case 'alert_created':
        this.handleAlertCreated(message.data);
        break;

      case 'alert_updated':
        this.handleAlertUpdated(message.data);
        break;

      case 'notification':
        this.handleNotification(message.data);
        break;

      case 'metrics_update':
        this.handleMetricsUpdate(message.data);
        break;

      case 'heartbeat':
        // Heartbeat received, connection is alive
        break;

      case 'error':
        console.error('WebSocket error:', message.data);
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }

  private handleAlertCreated(alertData: Alert): void {
    store.dispatch(addAlert(alertData));
    
    // Show notification for high severity alerts
    if (alertData.severity >= 6) {
      const notification: Notification = {
        id: `alert-${alertData.id}`,
        type: 'alert',
        message: `New ${alertData.severity >= 8 ? 'Critical' : 'High'} severity alert: ${alertData.event_type}`,
        timestamp: new Date().toISOString(),
        read: false,
        link: `/alerts/${alertData.id}`,
      };
      store.dispatch(addNotification(notification));
    }
  }

  private handleAlertUpdated(alertData: Alert): void {
    store.dispatch(updateAlert(alertData));
  }

  private handleNotification(notificationData: Notification): void {
    store.dispatch(addNotification(notificationData));
  }

  private handleMetricsUpdate(metricsData: any): void {
    // Handle real-time metrics updates
    // This could trigger dashboard refreshes or specific metric updates
    console.log('Metrics update received:', metricsData);
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})...`);
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, this.config.reconnectInterval);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get connectionState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// Create singleton instance
const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
export const websocketManager = new WebSocketManager({ url: wsUrl });

export default websocketManager;
