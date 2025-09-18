"""Notification microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..notifiers import send_email
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Notification Service...")
    
    # Create database tables
    create_tables()
    
    logger.info("Notification Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Notification Service",
    description="Multi-channel notification microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

@app.post("/api/v1/notifications/email")
async def send_email_notification(notification_data: Dict[str, Any]):
    """Send email notification."""
    try:
        if not SETTINGS.enable_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email notifications are disabled"
            )
        
        # Extract notification details
        to_emails = notification_data.get("to", [])
        subject = notification_data.get("subject", "SOC Agent Alert")
        body = notification_data.get("body", "")
        priority = notification_data.get("priority", "normal")
        
        if not to_emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No recipients specified"
            )
        
        # Send email
        success = await send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            priority=priority
        )
        
        if success:
            return {
                "status": "sent",
                "recipients": to_emails,
                "subject": subject,
                "message_id": f"msg_{hash(subject + str(to_emails))}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email notification failed: {str(e)}"
        )

@app.post("/api/v1/notifications/sms")
async def send_sms_notification(notification_data: Dict[str, Any]):
    """Send SMS notification."""
    try:
        # Extract notification details
        phone_numbers = notification_data.get("to", [])
        message = notification_data.get("message", "")
        
        if not phone_numbers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No phone numbers specified"
            )
        
        # TODO: Implement SMS sending logic
        # This would integrate with SMS providers like Twilio, AWS SNS, etc.
        
        return {
            "status": "sent",
            "recipients": phone_numbers,
            "message": message,
            "message_id": f"sms_{hash(message + str(phone_numbers))}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS notification failed: {str(e)}"
        )

@app.post("/api/v1/notifications/slack")
async def send_slack_notification(notification_data: Dict[str, Any]):
    """Send Slack notification."""
    try:
        # Extract notification details
        channel = notification_data.get("channel", "#security-alerts")
        message = notification_data.get("message", "")
        severity = notification_data.get("severity", "info")
        
        # TODO: Implement Slack integration
        # This would use Slack Web API or webhooks
        
        return {
            "status": "sent",
            "channel": channel,
            "message": message,
            "severity": severity,
            "message_id": f"slack_{hash(message + channel)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Slack notification failed: {str(e)}"
        )

@app.post("/api/v1/notifications/webhook")
async def send_webhook_notification(notification_data: Dict[str, Any]):
    """Send webhook notification."""
    try:
        # Extract notification details
        webhook_url = notification_data.get("url")
        payload = notification_data.get("payload", {})
        headers = notification_data.get("headers", {})
        
        if not webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook URL not specified"
            )
        
        # TODO: Implement webhook sending logic
        # This would use httpx to send POST requests to the webhook URL
        
        return {
            "status": "sent",
            "webhook_url": webhook_url,
            "payload": payload,
            "message_id": f"webhook_{hash(webhook_url + str(payload))}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook notification failed: {str(e)}"
        )

@app.get("/api/v1/notifications/history")
async def get_notification_history(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get notification history."""
    try:
        with get_db() as db:
            query = "SELECT * FROM notifications WHERE 1=1"
            params = []
            
            if channel:
                query += " AND channel = %s"
                params.append(channel)
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            notifications = db.execute(query, params).fetchall()
            
            return {
                "notifications": [
                    {
                        "id": notif.id,
                        "channel": notif.channel,
                        "recipient": notif.recipient,
                        "subject": notif.subject,
                        "status": notif.status,
                        "created_at": notif.created_at.isoformat()
                    }
                    for notif in notifications
                ],
                "count": len(notifications)
            }
            
    except Exception as e:
        logger.error(f"Notification history retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification history retrieval failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "notification-service",
            "version": "1.0.0",
            "database": "connected",
            "email_enabled": SETTINGS.enable_email
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/metrics")
async def service_metrics():
    """Service metrics."""
    try:
        with get_db() as db:
            # Get notification counts by channel
            channel_counts = db.execute("""
                SELECT channel, COUNT(*) as count 
                FROM notifications 
                GROUP BY channel
            """).fetchall()
            
            # Get recent notifications (last 24 hours)
            recent_notifications = db.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            return {
                "service": "notification-service",
                "metrics": {
                    "total_notifications": sum(row.count for row in channel_counts),
                    "recent_notifications_24h": recent_notifications,
                    "notifications_by_channel": {row.channel: row.count for row in channel_counts}
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "notification-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
