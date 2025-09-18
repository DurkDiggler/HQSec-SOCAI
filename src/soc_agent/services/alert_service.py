"""Alert processing microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..api import api_router
from ..config import SETTINGS
from ..database import create_tables, get_db
from ..realtime import alert_streamer, initialize_realtime, cleanup_realtime

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Alert Service...")
    
    # Create database tables
    create_tables()
    
    # Initialize real-time capabilities
    if SETTINGS.enable_realtime:
        await initialize_realtime()
    
    logger.info("Alert Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Alert Service...")
    
    # Cleanup real-time capabilities
    if SETTINGS.enable_realtime:
        await cleanup_realtime()

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Alert Service",
    description="Alert processing and management microservice",
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

# Include API router
app.include_router(api_router)

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        # Check real-time capabilities
        realtime_status = "connected" if SETTINGS.enable_realtime else "disabled"
        
        return {
            "status": "healthy",
            "service": "alert-service",
            "version": "1.0.0",
            "database": "connected",
            "realtime": realtime_status
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
            # Get alert counts by status
            alert_counts = db.execute("""
                SELECT status, COUNT(*) as count 
                FROM alerts 
                GROUP BY status
            """).fetchall()
            
            # Get total alerts
            total_alerts = db.execute("SELECT COUNT(*) FROM alerts").scalar()
            
            # Get recent alerts (last 24 hours)
            recent_alerts = db.execute("""
                SELECT COUNT(*) FROM alerts 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            return {
                "service": "alert-service",
                "metrics": {
                    "total_alerts": total_alerts,
                    "recent_alerts_24h": recent_alerts,
                    "alerts_by_status": {row.status: row.count for row in alert_counts}
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "alert-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
