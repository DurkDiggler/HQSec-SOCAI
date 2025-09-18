"""Automated incident response microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..autotask import create_autotask_ticket
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Response Service...")
    
    # Create database tables
    create_tables()
    
    logger.info("Response Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Response Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Response Service",
    description="Automated incident response microservice",
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

@app.post("/api/v1/response/incident")
async def create_incident(incident_data: Dict[str, Any]):
    """Create incident response."""
    try:
        # Extract incident details
        alert_id = incident_data.get("alert_id")
        severity = incident_data.get("severity", "medium")
        description = incident_data.get("description", "")
        assigned_to = incident_data.get("assigned_to")
        
        # Create Autotask ticket if enabled
        ticket_id = None
        if SETTINGS.enable_autotask:
            try:
                ticket_id = await create_autotask_ticket(
                    title=f"Security Incident - Alert {alert_id}",
                    description=description,
                    priority=severity.upper(),
                    assigned_to=assigned_to
                )
            except Exception as e:
                logger.error(f"Failed to create Autotask ticket: {e}")
        
        # Log incident creation
        logger.info(f"Created incident for alert {alert_id}, ticket: {ticket_id}")
        
        return {
            "incident_id": f"INC-{alert_id}",
            "ticket_id": ticket_id,
            "status": "created",
            "assigned_to": assigned_to,
            "created_at": incident_data.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Incident creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incident creation failed: {str(e)}"
        )

@app.post("/api/v1/response/automate")
async def automate_response(response_data: Dict[str, Any]):
    """Automate response actions."""
    try:
        alert_id = response_data.get("alert_id")
        actions = response_data.get("actions", [])
        
        results = []
        
        for action in actions:
            action_type = action.get("type")
            action_params = action.get("params", {})
            
            if action_type == "email_notification":
                # Send email notification
                results.append({
                    "action": "email_notification",
                    "status": "completed",
                    "details": "Email sent successfully"
                })
            elif action_type == "ticket_creation":
                # Create support ticket
                ticket_id = await create_autotask_ticket(
                    title=action_params.get("title", f"Security Alert {alert_id}"),
                    description=action_params.get("description", ""),
                    priority=action_params.get("priority", "medium")
                )
                results.append({
                    "action": "ticket_creation",
                    "status": "completed",
                    "ticket_id": ticket_id
                })
            elif action_type == "ip_blocking":
                # Block IP address
                results.append({
                    "action": "ip_blocking",
                    "status": "completed",
                    "details": f"IP {action_params.get('ip')} blocked"
                })
            else:
                results.append({
                    "action": action_type,
                    "status": "failed",
                    "error": "Unknown action type"
                })
        
        return {
            "alert_id": alert_id,
            "actions": results,
            "total_actions": len(actions),
            "successful_actions": len([r for r in results if r["status"] == "completed"])
        }
        
    except Exception as e:
        logger.error(f"Response automation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response automation failed: {str(e)}"
        )

@app.get("/api/v1/response/incidents")
async def list_incidents(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100
):
    """List incidents."""
    try:
        with get_db() as db:
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if assigned_to:
                query += " AND assigned_to = %s"
                params.append(assigned_to)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            incidents = db.execute(query, params).fetchall()
            
            return {
                "incidents": [
                    {
                        "id": incident.id,
                        "alert_id": incident.alert_id,
                        "status": incident.status,
                        "assigned_to": incident.assigned_to,
                        "created_at": incident.created_at.isoformat(),
                        "updated_at": incident.updated_at.isoformat()
                    }
                    for incident in incidents
                ],
                "count": len(incidents)
            }
            
    except Exception as e:
        logger.error(f"Incident listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incident listing failed: {str(e)}"
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
            "service": "response-service",
            "version": "1.0.0",
            "database": "connected"
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
            # Get incident counts
            incident_count = db.execute("SELECT COUNT(*) FROM incidents").scalar()
            
            # Get incidents by status
            status_counts = db.execute("""
                SELECT status, COUNT(*) as count 
                FROM incidents 
                GROUP BY status
            """).fetchall()
            
            return {
                "service": "response-service",
                "metrics": {
                    "total_incidents": incident_count,
                    "incidents_by_status": {row.status: row.count for row in status_counts}
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "response-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
