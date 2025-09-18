"""Real-time API endpoints for WebSocket and Server-Sent Events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import get_db, get_alert_by_id
from .realtime import (
    alert_streamer,
    connection_manager,
    initialize_realtime,
    sse_handler
)

logger = logging.getLogger(__name__)

# Create real-time API router
realtime_router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


@realtime_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """WebSocket endpoint for real-time updates."""
    if not SETTINGS.enable_realtime:
        await websocket.close(code=1003, reason="Real-time features disabled")
        return
    
    # Check connection limit
    if len(connection_manager.active_connections) >= SETTINGS.max_websocket_connections:
        await websocket.close(code=1013, reason="Server overloaded")
        return
    
    client_id = await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(client_id, message)
            except json.JSONDecodeError:
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, client_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await connection_manager.send_personal_message({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }, client_id)
                
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await connection_manager.disconnect(client_id)


async def handle_websocket_message(client_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to channels
        channels = message.get("channels", [])
        for channel in channels:
            await connection_manager.subscribe_to_channel(client_id, channel)
        
        await connection_manager.send_personal_message({
            "type": "subscription_confirmed",
            "channels": channels,
            "message": f"Subscribed to {len(channels)} channels"
        }, client_id)
        
    elif message_type == "unsubscribe":
        # Unsubscribe from channels
        channels = message.get("channels", [])
        for channel in channels:
            await connection_manager.unsubscribe_from_channel(client_id, channel)
        
        await connection_manager.send_personal_message({
            "type": "unsubscription_confirmed",
            "channels": channels,
            "message": f"Unsubscribed from {len(channels)} channels"
        }, client_id)
        
    elif message_type == "ping":
        # Respond to ping with pong
        await connection_manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }, client_id)
        
    elif message_type == "get_stats":
        # Send connection statistics
        stats = await connection_manager.get_connection_stats()
        await connection_manager.send_personal_message({
            "type": "connection_stats",
            "data": stats
        }, client_id)
        
    else:
        await connection_manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, client_id)


@realtime_router.get("/events")
async def server_sent_events(
    client_id: Optional[str] = Query(None, description="Client ID for the event stream")
):
    """Server-Sent Events endpoint for real-time notifications."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    if not client_id:
        client_id = f"sse_{asyncio.get_event_loop().time()}"
    
    async def event_generator():
        try:
            async for event in sse_handler.stream_events(client_id):
                yield event
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@realtime_router.post("/alerts/stream")
async def stream_alert(
    alert_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Manually trigger alert streaming (for testing)."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    try:
        await alert_streamer.stream_alert(alert_data)
        return {"message": "Alert streamed successfully", "timestamp": alert_data.get("timestamp")}
    except Exception as e:
        logger.error(f"Failed to stream alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream alert: {e}")


@realtime_router.post("/alerts/{alert_id}/stream-update")
async def stream_alert_update(
    alert_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Stream an alert update."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    # Verify alert exists
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        await alert_streamer.stream_alert_update(alert_id, update_data)
        return {"message": "Alert update streamed successfully", "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Failed to stream alert update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream alert update: {e}")


@realtime_router.post("/notifications/stream")
async def stream_notification(
    notification_data: Dict[str, Any]
):
    """Stream a notification to all connected clients."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    try:
        await alert_streamer.stream_notification(notification_data)
        return {"message": "Notification streamed successfully"}
    except Exception as e:
        logger.error(f"Failed to stream notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream notification: {e}")


@realtime_router.get("/status")
async def get_realtime_status():
    """Get real-time system status."""
    if not SETTINGS.enable_realtime:
        return {
            "enabled": False,
            "message": "Real-time features disabled"
        }
    
    try:
        connection_stats = await connection_manager.get_connection_stats()
        
        return {
            "enabled": True,
            "websocket_connections": connection_stats["total_connections"],
            "active_clients": connection_stats["active_clients"],
            "subscription_stats": connection_stats["subscription_stats"],
            "alert_streamer_running": alert_streamer.is_running,
            "redis_connected": alert_streamer.redis_client is not None,
            "sse_streams": len(sse_handler.event_streams)
        }
    except Exception as e:
        logger.error(f"Failed to get real-time status: {e}")
        return {
            "enabled": True,
            "error": str(e)
        }


@realtime_router.get("/channels")
async def get_available_channels():
    """Get list of available subscription channels."""
    return {
        "channels": [
            {
                "name": "alerts",
                "description": "All new alerts and alert updates",
                "type": "broadcast"
            },
            {
                "name": "notifications",
                "description": "System notifications and status updates",
                "type": "broadcast"
            },
            {
                "name": "alert_updates",
                "description": "Alert status and data updates",
                "type": "broadcast"
            },
            {
                "name": "alert_{alert_id}",
                "description": "Updates for a specific alert",
                "type": "targeted",
                "example": "alert_123"
            }
        ]
    }


@realtime_router.post("/test/alert")
async def test_alert_streaming():
    """Test alert streaming with a sample alert."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    test_alert = {
        "id": "test_alert_001",
        "source": "test_system",
        "event_type": "test_event",
        "severity": 5,
        "message": "This is a test alert for real-time streaming",
        "timestamp": "2024-01-01T12:00:00Z",
        "category": "test",
        "iocs": ["192.168.1.100", "test@example.com"],
        "scores": {
            "base": 50,
            "intel": 20,
            "final": 70
        }
    }
    
    try:
        await alert_streamer.stream_alert(test_alert)
        return {
            "message": "Test alert streamed successfully",
            "alert": test_alert
        }
    except Exception as e:
        logger.error(f"Failed to stream test alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream test alert: {e}")


@realtime_router.post("/test/notification")
async def test_notification_streaming():
    """Test notification streaming."""
    if not SETTINGS.enable_realtime:
        raise HTTPException(status_code=403, detail="Real-time features disabled")
    
    test_notification = {
        "title": "Test Notification",
        "message": "This is a test notification for real-time streaming",
        "type": "info",
        "priority": "normal"
    }
    
    try:
        await alert_streamer.stream_notification(test_notification)
        return {
            "message": "Test notification streamed successfully",
            "notification": test_notification
        }
    except Exception as e:
        logger.error(f"Failed to stream test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream test notification: {e}")


# Initialize real-time capabilities on startup
@realtime_router.on_event("startup")
async def startup_realtime():
    """Initialize real-time capabilities on startup."""
    if SETTINGS.enable_realtime:
        await initialize_realtime()
        logger.info("Real-time capabilities initialized")
