"""Authentication microservice for SOC Agent."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..auth import create_default_roles
from ..auth_api import router as auth_router
from ..auth_middleware import auth_middleware
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting Auth Service...")
    
    # Create database tables
    create_tables()
    
    # Initialize default roles
    with get_db() as db:
        create_default_roles(db)
    
    logger.info("Auth Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent Auth Service",
    description="Authentication and authorization microservice",
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

# Add authentication middleware
app.middleware("http")(auth_middleware)

# Include auth router
app.include_router(auth_router)

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "auth-service",
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
            # Get user count
            user_count = db.execute("SELECT COUNT(*) FROM users").scalar()
            
            # Get role count
            role_count = db.execute("SELECT COUNT(*) FROM roles").scalar()
            
            # Get audit log count
            audit_count = db.execute("SELECT COUNT(*) FROM audit_logs").scalar()
            
            return {
                "service": "auth-service",
                "metrics": {
                    "users": user_count,
                    "roles": role_count,
                    "audit_logs": audit_count
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "auth-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
