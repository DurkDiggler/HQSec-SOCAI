"""Threat intelligence microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..intel.client import IntelClient
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Intel Service...")
    
    # Create database tables
    create_tables()
    
    # Initialize threat intelligence client
    app.state.intel_client = IntelClient()
    
    logger.info("Intel Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intel Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Intel Service",
    description="Threat intelligence aggregation microservice",
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

@app.post("/api/v1/intel/lookup")
async def lookup_ioc(ioc_data: Dict[str, Any]):
    """Lookup IOC in threat intelligence feeds."""
    try:
        intel_client = getattr(app.state, 'intel_client', None)
        
        if not intel_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Intel client not initialized"
            )
        
        # Perform IOC lookup
        result = await intel_client.lookup_ioc(
            ioc_data.get("value"),
            ioc_data.get("type"),
            ioc_data.get("sources", [])
        )
        
        return {
            "ioc": ioc_data.get("value"),
            "type": ioc_data.get("type"),
            "sources": result.get("sources", []),
            "threat_score": result.get("threat_score", 0),
            "last_seen": result.get("last_seen"),
            "description": result.get("description")
        }
        
    except Exception as e:
        logger.error(f"IOC lookup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IOC lookup failed: {str(e)}"
        )

@app.get("/api/v1/intel/feeds")
async def list_feeds():
    """List available threat intelligence feeds."""
    try:
        intel_client = getattr(app.state, 'intel_client', None)
        
        if not intel_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Intel client not initialized"
            )
        
        feeds = await intel_client.get_available_feeds()
        
        return {
            "feeds": feeds,
            "count": len(feeds)
        }
        
    except Exception as e:
        logger.error(f"Feed listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feed listing failed: {str(e)}"
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
            "service": "intel-service",
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
            # Get IOC lookup counts
            ioc_count = db.execute("SELECT COUNT(*) FROM ioc_lookups").scalar()
            
            # Get recent lookups (last 24 hours)
            recent_lookups = db.execute("""
                SELECT COUNT(*) FROM ioc_lookups 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            return {
                "service": "intel-service",
                "metrics": {
                    "total_ioc_lookups": ioc_count,
                    "recent_lookups_24h": recent_lookups
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "intel-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
