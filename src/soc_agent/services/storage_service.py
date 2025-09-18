"""Storage and search microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..storage_api import router as storage_router
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Storage Service...")
    
    # Create database tables
    create_tables()
    
    logger.info("Storage Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Storage Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Storage Service",
    description="Storage, search, and metrics microservice",
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

# Include storage router
app.include_router(storage_router)

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "storage-service",
            "version": "1.0.0",
            "database": "connected",
            "storage_enabled": SETTINGS.storage_enabled,
            "elasticsearch_enabled": SETTINGS.elasticsearch_enabled,
            "timeseries_enabled": SETTINGS.timeseries_enabled
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
            # Get storage file counts
            file_count = db.execute("SELECT COUNT(*) FROM storage_files").scalar()
            
            # Get file counts by folder
            folder_counts = db.execute("""
                SELECT folder, COUNT(*) as count 
                FROM storage_files 
                GROUP BY folder
            """).fetchall()
            
            # Get recent files (last 24 hours)
            recent_files = db.execute("""
                SELECT COUNT(*) FROM storage_files 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            return {
                "service": "storage-service",
                "metrics": {
                    "total_files": file_count,
                    "recent_files_24h": recent_files,
                    "files_by_folder": {row.folder: row.count for row in folder_counts}
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "storage-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
