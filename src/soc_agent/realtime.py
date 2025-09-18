"""Real-time capabilities for SOC Agent including WebSocket and SSE support."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from .config import SETTINGS

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        
    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        if not client_id:
            client_id = str(uuid4())
            
        self.active_connections[client_id] = websocket
        self.connection_subscriptions[client_id] = set()
        
        logger.info(f"WebSocket client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to SOC Agent real-time updates"
        }, client_id)
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_subscriptions:
            del self.connection_subscriptions[client_id]
            
        logger.info(f"WebSocket client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude_client: str = None):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
                
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send broadcast to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def subscribe_to_channel(self, client_id: str, channel: str):
        """Subscribe a client to a specific channel."""
        if client_id in self.connection_subscriptions:
            self.connection_subscriptions[client_id].add(channel)
            logger.info(f"Client {client_id} subscribed to channel: {channel}")
    
    async def unsubscribe_from_channel(self, client_id: str, channel: str):
        """Unsubscribe a client from a specific channel."""
        if client_id in self.connection_subscriptions:
            self.connection_subscriptions[client_id].discard(channel)
            logger.info(f"Client {client_id} unsubscribed from channel: {channel}")
    
    async def send_to_channel(self, channel: str, message: Dict[str, Any]):
        """Send a message to all clients subscribed to a specific channel."""
        for client_id, subscriptions in self.connection_subscriptions.items():
            if channel in subscriptions:
                await self.send_personal_message(message, client_id)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections."""
        return {
            "total_connections": len(self.active_connections),
            "active_clients": list(self.active_connections.keys()),
            "subscription_stats": {
                client_id: list(subscriptions) 
                for client_id, subscriptions in self.connection_subscriptions.items()
            }
        }


class AlertStreamer:
    """Handles real-time alert streaming and notifications."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.redis_client: Optional[aioredis.Redis] = None
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub."""
        try:
            self.redis_client = aioredis.from_url(
                f"redis://{SETTINGS.redis_host}:{SETTINGS.redis_port}/{SETTINGS.redis_db}",
                password=SETTINGS.redis_password if SETTINGS.redis_password else None,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established for real-time streaming")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def start_streaming(self):
        """Start the alert streaming process."""
        if self.is_running:
            return
            
        self.is_running = True
        await self.initialize_redis()
        
        # Start background tasks
        asyncio.create_task(self._process_alert_queue())
        asyncio.create_task(self._redis_subscriber())
        
        logger.info("Alert streaming started")
    
    async def stop_streaming(self):
        """Stop the alert streaming process."""
        self.is_running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Alert streaming stopped")
    
    async def stream_alert(self, alert_data: Dict[str, Any]):
        """Stream a new alert to all connected clients."""
        message = {
            "type": "new_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add to queue for processing
        await self.alert_queue.put(message)
        
        # Broadcast immediately to WebSocket clients
        await self.connection_manager.broadcast(message)
        
        # Publish to Redis for other instances
        if self.redis_client:
            try:
                await self.redis_client.publish("alerts", json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to publish alert to Redis: {e}")
    
    async def stream_alert_update(self, alert_id: int, update_data: Dict[str, Any]):
        """Stream an alert update to subscribed clients."""
        message = {
            "type": "alert_update",
            "alert_id": alert_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to clients subscribed to this specific alert
        await self.connection_manager.send_to_channel(f"alert_{alert_id}", message)
        
        # Also broadcast to general alert channel
        await self.connection_manager.send_to_channel("alerts", message)
        
        # Publish to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish("alert_updates", json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to publish alert update to Redis: {e}")
    
    async def stream_notification(self, notification_data: Dict[str, Any]):
        """Stream a notification to all connected clients."""
        message = {
            "type": "notification",
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.broadcast(message)
        
        # Publish to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish("notifications", json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to publish notification to Redis: {e}")
    
    async def _process_alert_queue(self):
        """Process alerts from the queue."""
        while self.is_running:
            try:
                # Wait for alerts with timeout
                message = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                
                # Process the alert (could add filtering, rate limiting, etc.)
                logger.debug(f"Processing alert: {message['type']}")
                
                # Mark task as done
                self.alert_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing alert queue: {e}")
    
    async def _redis_subscriber(self):
        """Subscribe to Redis channels for cross-instance communication."""
        if not self.redis_client:
            return
            
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("alerts", "alert_updates", "notifications")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"]
                        
                        # Broadcast to WebSocket clients
                        if channel == "alerts":
                            await self.connection_manager.broadcast(data)
                        elif channel == "alert_updates":
                            await self.connection_manager.broadcast(data)
                        elif channel == "notifications":
                            await self.connection_manager.broadcast(data)
                            
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}")


class ServerSentEvents:
    """Handles Server-Sent Events for notifications."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.event_streams: Dict[str, asyncio.Queue] = {}
    
    async def create_event_stream(self, client_id: str) -> asyncio.Queue:
        """Create a new event stream for a client."""
        if client_id not in self.event_streams:
            self.event_streams[client_id] = asyncio.Queue()
        return self.event_streams[client_id]
    
    async def send_event(self, client_id: str, event_type: str, data: Dict[str, Any]):
        """Send an event to a specific client's stream."""
        if client_id in self.event_streams:
            event = {
                "id": str(uuid4()),
                "event": event_type,
                "data": json.dumps(data),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.event_streams[client_id].put(event)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected SSE clients."""
        for client_id in self.event_streams:
            await self.send_event(client_id, event_type, data)
    
    async def stream_events(self, client_id: str):
        """Generate SSE stream for a client."""
        if client_id not in self.event_streams:
            await self.create_event_stream(client_id)
        
        queue = self.event_streams[client_id]
        
        try:
            while True:
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Format as SSE
                    sse_data = f"id: {event['id']}\n"
                    sse_data += f"event: {event['event']}\n"
                    sse_data += f"data: {event['data']}\n"
                    sse_data += f"timestamp: {event['timestamp']}\n\n"
                    
                    yield sse_data
                    
                    # Mark task as done
                    queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE stream error for client {client_id}: {e}")
        finally:
            # Clean up
            if client_id in self.event_streams:
                del self.event_streams[client_id]


# Global instances
connection_manager = ConnectionManager()
alert_streamer = AlertStreamer(connection_manager)
sse_handler = ServerSentEvents(connection_manager)


async def initialize_realtime():
    """Initialize real-time capabilities."""
    await alert_streamer.start_streaming()
    logger.info("Real-time capabilities initialized")


async def cleanup_realtime():
    """Cleanup real-time resources."""
    await alert_streamer.stop_streaming()
    logger.info("Real-time capabilities cleaned up")
