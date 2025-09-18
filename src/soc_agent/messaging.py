"""Inter-service communication and message queuing for SOC Agent."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

import redis
from pydantic import BaseModel

from .config import SETTINGS

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """Message types for inter-service communication."""
    ALERT_CREATED = "alert.created"
    ALERT_UPDATED = "alert.updated"
    ALERT_RESOLVED = "alert.resolved"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    ANALYSIS_COMPLETED = "analysis.completed"
    NOTIFICATION_SENT = "notification.sent"
    METRIC_RECORDED = "metric.recorded"

class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class Message(BaseModel):
    """Message model for inter-service communication."""
    id: str
    type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    source_service: str
    target_service: Optional[str] = None
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class MessageQueue:
    """Redis-based message queue for inter-service communication."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=SETTINGS.redis_host,
            port=SETTINGS.redis_port,
            password=SETTINGS.redis_password,
            db=SETTINGS.redis_db,
            decode_responses=True
        )
        self.subscribers = {}
        self.running = False
    
    async def publish(self, message: Message) -> bool:
        """Publish a message to the queue."""
        try:
            # Serialize message
            message_data = message.model_dump_json()
            
            # Publish to Redis
            if message.target_service:
                # Direct message to specific service
                channel = f"service:{message.target_service}"
            else:
                # Broadcast message
                channel = f"message:{message.type.value}"
            
            result = self.redis_client.publish(channel, message_data)
            
            if result > 0:
                logger.info(f"Published message {message.id} to {channel}")
                return True
            else:
                logger.warning(f"No subscribers for message {message.id} on {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to publish message {message.id}: {e}")
            return False
    
    async def subscribe(self, service_name: str, message_types: List[MessageType], 
                       handler: Callable[[Message], None]):
        """Subscribe to messages for a service."""
        try:
            # Create subscriber
            subscriber = self.redis_client.pubsub()
            
            # Subscribe to service-specific channel
            service_channel = f"service:{service_name}"
            subscriber.subscribe(service_channel)
            
            # Subscribe to message type channels
            for message_type in message_types:
                type_channel = f"message:{message_type.value}"
                subscriber.subscribe(type_channel)
            
            # Store subscriber
            self.subscribers[service_name] = {
                "subscriber": subscriber,
                "handler": handler,
                "message_types": message_types
            }
            
            logger.info(f"Service {service_name} subscribed to {len(message_types)} message types")
            
        except Exception as e:
            logger.error(f"Failed to subscribe service {service_name}: {e}")
    
    async def start_consuming(self, service_name: str):
        """Start consuming messages for a service."""
        if service_name not in self.subscribers:
            logger.error(f"No subscription found for service {service_name}")
            return
        
        subscriber_info = self.subscribers[service_name]
        subscriber = subscriber_info["subscriber"]
        handler = subscriber_info["handler"]
        
        self.running = True
        logger.info(f"Starting message consumption for service {service_name}")
        
        try:
            while self.running:
                message = subscriber.get_message(timeout=1.0)
                
                if message and message["type"] == "message":
                    try:
                        # Parse message
                        message_data = json.loads(message["data"])
                        msg = Message(**message_data)
                        
                        # Process message
                        await handler(msg)
                        
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
                        
        except Exception as e:
            logger.error(f"Message consumption failed for service {service_name}: {e}")
        finally:
            subscriber.close()
            logger.info(f"Stopped message consumption for service {service_name}")
    
    async def stop_consuming(self):
        """Stop consuming messages."""
        self.running = False
        
        # Close all subscribers
        for service_name, subscriber_info in self.subscribers.items():
            try:
                subscriber_info["subscriber"].close()
            except Exception as e:
                logger.error(f"Failed to close subscriber for {service_name}: {e}")
        
        self.subscribers.clear()
        logger.info("Stopped all message consumption")

class EventBus:
    """Event bus for service communication."""
    
    def __init__(self):
        self.message_queue = MessageQueue()
        self.event_handlers = {}
    
    async def publish_event(self, event_type: MessageType, payload: Dict[str, Any], 
                          source_service: str, target_service: Optional[str] = None,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None) -> bool:
        """Publish an event."""
        message = Message(
            id=str(uuid.uuid4()),
            type=event_type,
            priority=priority,
            source_service=source_service,
            target_service=target_service,
            payload=payload,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        return await self.message_queue.publish(message)
    
    async def subscribe_to_events(self, service_name: str, event_types: List[MessageType], 
                                 handler: Callable[[Message], None]):
        """Subscribe to events."""
        await self.message_queue.subscribe(service_name, event_types, handler)
    
    async def start_event_consumption(self, service_name: str):
        """Start consuming events for a service."""
        await self.message_queue.start_consuming(service_name)
    
    async def stop_event_consumption(self):
        """Stop consuming events."""
        await self.message_queue.stop_consuming()

class ServiceClient:
    """HTTP client for inter-service communication."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.base_url = f"http://{service_name}:800{self._get_service_port()}"
    
    def _get_service_port(self) -> int:
        """Get port number for service."""
        port_mapping = {
            "auth-service": 1,
            "alert-service": 2,
            "ai-service": 3,
            "intel-service": 4,
            "response-service": 5,
            "analytics-service": 6,
            "notification-service": 7,
            "storage-service": 8
        }
        return port_mapping.get(self.service_name, 0)
    
    async def call_service(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Call another service."""
        import httpx
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Service call failed: {e}")
            raise Exception(f"Service call failed: {str(e)}")

# Global instances
event_bus = EventBus()

# Service clients
auth_client = ServiceClient("auth-service")
alert_client = ServiceClient("alert-service")
ai_client = ServiceClient("ai-service")
intel_client = ServiceClient("intel-service")
response_client = ServiceClient("response-service")
analytics_client = ServiceClient("analytics-service")
notification_client = ServiceClient("notification-service")
storage_client = ServiceClient("storage-service")

# Event handlers
async def handle_alert_created(message: Message):
    """Handle alert created event."""
    logger.info(f"Processing alert created event: {message.id}")
    
    # Notify AI service for analysis
    await event_bus.publish_event(
        event_type=MessageType.ANALYSIS_COMPLETED,
        payload=message.payload,
        source_service="alert-service",
        target_service="ai-service"
    )
    
    # Notify notification service
    await event_bus.publish_event(
        event_type=MessageType.NOTIFICATION_SENT,
        payload=message.payload,
        source_service="alert-service",
        target_service="notification-service"
    )

async def handle_analysis_completed(message: Message):
    """Handle analysis completed event."""
    logger.info(f"Processing analysis completed event: {message.id}")
    
    # Update alert with analysis results
    await alert_client.call_service(
        endpoint="/api/v1/alerts/update-analysis",
        method="POST",
        data=message.payload
    )

async def handle_incident_created(message: Message):
    """Handle incident created event."""
    logger.info(f"Processing incident created event: {message.id}")
    
    # Notify notification service
    await event_bus.publish_event(
        event_type=MessageType.NOTIFICATION_SENT,
        payload=message.payload,
        source_service="response-service",
        target_service="notification-service"
    )

async def handle_metric_recorded(message: Message):
    """Handle metric recorded event."""
    logger.info(f"Processing metric recorded event: {message.id}")
    
    # Store metric in time-series database
    await storage_client.call_service(
        endpoint="/api/v1/metrics/record",
        method="POST",
        data=message.payload
    )
