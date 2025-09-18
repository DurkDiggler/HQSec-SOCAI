# Real-time Capabilities - SOC Agent

## 🚀 **Overview**

Your SOC Agent platform now includes comprehensive real-time capabilities that provide instant updates, live alert streaming, and real-time notifications. This enterprise-level feature set enables your security team to respond to threats as they happen.

## 📊 **What Was Implemented**

### **Backend Real-time Infrastructure**

#### **1. WebSocket Server (`src/soc_agent/realtime.py`)**
- **Connection Management**: Handles multiple WebSocket connections with automatic reconnection
- **Channel Subscriptions**: Clients can subscribe to specific alert channels
- **Message Broadcasting**: Real-time message distribution to all connected clients
- **Connection Statistics**: Monitor active connections and subscription patterns
- **Redis Integration**: Cross-instance communication for distributed deployments

#### **2. Server-Sent Events (`src/soc_agent/realtime_api.py`)**
- **SSE Endpoint**: `/api/v1/realtime/events` for browser-based real-time updates
- **Event Streaming**: Continuous event stream with keepalive mechanism
- **Client Management**: Individual event streams per client
- **Automatic Cleanup**: Resource management for disconnected clients

#### **3. Alert Streaming System**
- **Real-time Alert Broadcasting**: New alerts streamed instantly to all connected clients
- **Alert Updates**: Status changes, assignments, and modifications streamed in real-time
- **Notification System**: System notifications and status updates
- **Queue Management**: Buffered alert processing with configurable limits

#### **4. API Endpoints**
- **WebSocket**: `ws://localhost:8000/api/v1/realtime/ws`
- **SSE**: `GET /api/v1/realtime/events`
- **Status**: `GET /api/v1/realtime/status`
- **Channels**: `GET /api/v1/realtime/channels`
- **Test Endpoints**: Alert and notification testing capabilities

### **Frontend Real-time Components**

#### **1. RealtimeConnection (`frontend/src/components/RealtimeConnection.js`)**
- **WebSocket Management**: Automatic connection, reconnection, and error handling
- **Context Provider**: React context for real-time state management
- **Channel Subscriptions**: Subscribe/unsubscribe to specific alert channels
- **Connection Status**: Visual indicators for connection health
- **Message Handling**: Centralized message processing and routing

#### **2. RealtimeAlerts (`frontend/src/components/RealtimeAlerts.js`)**
- **Live Alert Display**: Real-time alert feed with configurable limits
- **Alert Updates**: Live updates for alert status changes
- **Severity Indicators**: Color-coded severity levels and status badges
- **IOC Display**: Indicators of Compromise with truncation for large lists
- **Timestamp Management**: Relative and absolute timestamp display

#### **3. RealtimeNotifications (`frontend/src/components/RealtimeNotifications.js`)**
- **Notification Feed**: Real-time system notifications
- **Priority Handling**: Critical, high, normal priority notifications
- **Auto-hide**: Configurable auto-hide for non-critical notifications
- **Read/Unread Management**: Mark notifications as read or clear all
- **Type Indicators**: Visual icons for different notification types

### **Configuration Options**

#### **Real-time Settings (`.env`)**
```env
# Real-time Capabilities
ENABLE_REALTIME=true
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10
MAX_WEBSOCKET_CONNECTIONS=100
SSE_KEEPALIVE_INTERVAL=30
ALERT_STREAM_BUFFER_SIZE=1000
```

#### **Nginx Configuration**
- **WebSocket Proxy**: Proper WebSocket upgrade handling
- **SSE Support**: Server-Sent Events with buffering disabled
- **Timeout Settings**: Extended timeouts for long-lived connections
- **Security Headers**: CSP updates for WebSocket connections

## 🎯 **Key Features**

### **1. Real-time Alert Streaming**
- **Instant Notifications**: New alerts appear immediately in the dashboard
- **Live Updates**: Alert status changes streamed in real-time
- **Multi-client Support**: Multiple users see updates simultaneously
- **Channel Filtering**: Subscribe to specific alert types or sources

### **2. WebSocket Communication**
- **Bidirectional**: Send commands and receive updates
- **Auto-reconnection**: Handles network interruptions gracefully
- **Connection Limits**: Configurable maximum connections
- **Ping/Pong**: Keep-alive mechanism for connection health

### **3. Server-Sent Events**
- **Browser Native**: Works without WebSocket support
- **Event Types**: Structured event types for different data
- **Keepalive**: Automatic keepalive to prevent timeouts
- **Client Management**: Individual streams per client

### **4. Notification System**
- **Priority Levels**: Critical, high, normal priority notifications
- **Auto-hide**: Configurable auto-hide for non-critical items
- **Read Management**: Mark as read, clear all functionality
- **Visual Indicators**: Icons and colors for different types

## 🔧 **Usage Examples**

### **WebSocket Client Connection**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws');

ws.onopen = () => {
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['alerts', 'notifications', 'alert_updates']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Real-time update:', message);
};
```

### **Server-Sent Events**
```javascript
const eventSource = new EventSource('/api/v1/realtime/events');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('SSE update:', data);
};

eventSource.addEventListener('alert', (event) => {
  const alert = JSON.parse(event.data);
  console.log('New alert:', alert);
});
```

### **React Component Usage**
```jsx
import { useRealtime } from './components/RealtimeConnection';

function MyComponent() {
  const { isConnected, subscribeToChannels, sendMessage } = useRealtime();
  
  useEffect(() => {
    if (isConnected) {
      subscribeToChannels(['alerts']);
    }
  }, [isConnected, subscribeToChannels]);
  
  return (
    <div>
      Status: {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  );
}
```

## 📈 **Performance Characteristics**

### **Scalability**
- **Connection Limits**: Configurable maximum WebSocket connections (default: 100)
- **Redis Integration**: Cross-instance communication for horizontal scaling
- **Queue Management**: Buffered processing prevents memory issues
- **Resource Cleanup**: Automatic cleanup of disconnected clients

### **Reliability**
- **Auto-reconnection**: Client-side reconnection with exponential backoff
- **Error Handling**: Comprehensive error handling and logging
- **Graceful Degradation**: Falls back to polling if real-time fails
- **Connection Health**: Ping/pong mechanism for connection monitoring

### **Security**
- **CORS Support**: Proper CORS headers for cross-origin requests
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Input Validation**: Message validation and sanitization
- **Connection Limits**: Prevents resource exhaustion attacks

## 🚀 **Getting Started**

### **1. Enable Real-time Features**
```bash
# In your .env file
ENABLE_REALTIME=true
```

### **2. Start the Services**
```bash
# Using Docker Compose
docker-compose up --build

# Or manually
python -m uvicorn src.soc_agent.webapp:app --host 0.0.0.0 --port 8000
```

### **3. Access Real-time Features**
- **WebSocket**: `ws://localhost:8000/api/v1/realtime/ws`
- **SSE**: `http://localhost:8000/api/v1/realtime/events`
- **Status**: `http://localhost:8000/api/v1/realtime/status`

### **4. Test Real-time Capabilities**
```bash
# Test alert streaming
curl -X POST http://localhost:8000/api/v1/realtime/test/alert

# Test notification streaming
curl -X POST http://localhost:8000/api/v1/realtime/test/notification

# Check real-time status
curl http://localhost:8000/api/v1/realtime/status
```

## 🔍 **Monitoring and Debugging**

### **Connection Statistics**
```bash
curl http://localhost:8000/api/v1/realtime/status
```

### **Available Channels**
```bash
curl http://localhost:8000/api/v1/realtime/channels
```

### **WebSocket Testing**
Use browser developer tools or WebSocket testing tools:
- **Chrome DevTools**: Network tab → WS filter
- **WebSocket King**: External WebSocket testing tool
- **wscat**: Command-line WebSocket client

## 🎯 **Business Value**

### **Operational Benefits**
- **Faster Response Times**: Instant alert notifications reduce MTTR
- **Improved Situational Awareness**: Real-time dashboard updates
- **Better Collaboration**: Multiple analysts see updates simultaneously
- **Reduced Alert Fatigue**: Smart filtering and prioritization

### **Technical Advantages**
- **Modern Architecture**: WebSocket and SSE for real-time communication
- **Scalable Design**: Redis integration for horizontal scaling
- **Enterprise Ready**: Connection limits, monitoring, and error handling
- **Developer Friendly**: React hooks and context for easy integration

### **Security Benefits**
- **Immediate Threat Detection**: Real-time alert streaming
- **Live Status Updates**: Instant visibility into system health
- **Collaborative Response**: Multiple team members can coordinate
- **Audit Trail**: Complete real-time activity logging

## 🔮 **Future Enhancements**

### **Planned Features**
- **Alert Correlation**: Real-time correlation of related alerts
- **Custom Dashboards**: User-configurable real-time dashboards
- **Mobile Notifications**: Push notifications for mobile devices
- **Advanced Filtering**: Complex alert filtering and routing

### **Integration Opportunities**
- **Slack Integration**: Real-time Slack notifications
- **Microsoft Teams**: Teams integration for notifications
- **Mobile Apps**: Native mobile app with real-time updates
- **Third-party SIEMs**: Integration with external SIEM platforms

## 🆘 **Troubleshooting**

### **Common Issues**

#### **WebSocket Connection Failed**
- Check if `ENABLE_REALTIME=true` in `.env`
- Verify nginx configuration for WebSocket support
- Check firewall settings for WebSocket ports

#### **SSE Not Working**
- Ensure `proxy_buffering off` in nginx config
- Check browser console for CORS errors
- Verify SSE endpoint is accessible

#### **High Memory Usage**
- Reduce `ALERT_STREAM_BUFFER_SIZE` in configuration
- Check for memory leaks in client connections
- Monitor Redis memory usage

#### **Connection Drops**
- Increase `WEBSOCKET_PING_INTERVAL` for unstable networks
- Check nginx timeout settings
- Verify client reconnection logic

### **Debug Commands**
```bash
# Check real-time status
curl http://localhost:8000/api/v1/realtime/status

# Test WebSocket connection
wscat -c ws://localhost:8000/api/v1/realtime/ws

# Monitor Redis
redis-cli monitor

# Check nginx logs
docker logs nginx
```

## 🏆 **Conclusion**

Your SOC Agent platform now includes enterprise-level real-time capabilities that provide:

- **Instant Alert Streaming**: Real-time security event processing
- **Live Notifications**: Immediate system status updates
- **WebSocket Communication**: Bidirectional real-time communication
- **Server-Sent Events**: Browser-native real-time updates
- **Scalable Architecture**: Redis-backed distributed communication
- **Modern Frontend**: React components with real-time context

This real-time infrastructure positions your platform as a leading enterprise SOC solution, providing the speed and responsiveness needed for effective security operations in today's fast-paced threat landscape.

---

**Ready to test?** Start your services and visit the dashboard to see real-time alerts and notifications in action!
