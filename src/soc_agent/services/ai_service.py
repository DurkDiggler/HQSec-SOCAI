"""AI/ML microservice for SOC Agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..ai.llm_client import LLMClient
from ..ai.risk_assessor import RiskAssessor
from ..ai.threat_analyzer import ThreatAnalyzer
from ..config import SETTINGS
from ..database import create_tables, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifespan management."""
    # Startup
    logger.info("Starting AI Service...")
    
    # Create database tables
    create_tables()
    
    # Initialize AI components
    if SETTINGS.enable_ai_analysis:
        app.state.llm_client = LLMClient()
        app.state.risk_assessor = RiskAssessor()
        app.state.threat_analyzer = ThreatAnalyzer()
    
    logger.info("AI Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Service...")

# Create FastAPI app
app = FastAPI(
    title="SOC Agent AI Service",
    description="AI/ML threat analysis microservice",
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

@app.post("/api/v1/ai/analyze")
async def analyze_alert(alert_data: Dict[str, Any]):
    """Analyze alert with AI."""
    if not SETTINGS.enable_ai_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI analysis is disabled"
        )
    
    try:
        # Get AI components
        llm_client = getattr(app.state, 'llm_client', None)
        threat_analyzer = getattr(app.state, 'threat_analyzer', None)
        
        if not llm_client or not threat_analyzer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI components not initialized"
            )
        
        # Perform analysis
        analysis_result = await threat_analyzer.analyze_threat(alert_data)
        
        return {
            "analysis_id": analysis_result.get("id"),
            "threat_level": analysis_result.get("threat_level"),
            "confidence": analysis_result.get("confidence"),
            "recommendations": analysis_result.get("recommendations"),
            "iocs": analysis_result.get("iocs", []),
            "summary": analysis_result.get("summary")
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/v1/ai/risk-assessment")
async def assess_risk(threat_data: Dict[str, Any]):
    """Perform risk assessment."""
    if not SETTINGS.enable_ai_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI analysis is disabled"
        )
    
    try:
        # Get risk assessor
        risk_assessor = getattr(app.state, 'risk_assessor', None)
        
        if not risk_assessor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Risk assessor not initialized"
            )
        
        # Perform risk assessment
        risk_score = await risk_assessor.assess_risk(threat_data)
        
        return {
            "risk_score": risk_score,
            "risk_level": "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW",
            "factors": threat_data.get("factors", []),
            "recommendations": threat_data.get("recommendations", [])
        }
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}"
        )

@app.post("/api/v1/ai/correlate-threats")
async def correlate_threats(threat_data: List[Dict[str, Any]]):
    """Correlate multiple threats."""
    if not SETTINGS.enable_ai_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI analysis is disabled"
        )
    
    try:
        # Get threat analyzer
        threat_analyzer = getattr(app.state, 'threat_analyzer', None)
        
        if not threat_analyzer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Threat analyzer not initialized"
            )
        
        # Perform correlation
        correlation_result = await threat_analyzer.correlate_threats(threat_data)
        
        return {
            "correlation_id": correlation_result.get("id"),
            "confidence": correlation_result.get("confidence"),
            "threat_actors": correlation_result.get("threat_actors", []),
            "attack_techniques": correlation_result.get("attack_techniques", []),
            "timeline": correlation_result.get("timeline", []),
            "summary": correlation_result.get("summary")
        }
        
    except Exception as e:
        logger.error(f"Threat correlation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat correlation failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Service health check."""
    try:
        # Check database connection
        with get_db() as db:
            db.execute("SELECT 1")
        
        # Check AI components
        ai_status = "connected" if SETTINGS.enable_ai_analysis else "disabled"
        
        return {
            "status": "healthy",
            "service": "ai-service",
            "version": "1.0.0",
            "database": "connected",
            "ai_analysis": ai_status
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
            # Get AI analysis counts
            analysis_count = db.execute("SELECT COUNT(*) FROM ai_analyses").scalar()
            
            # Get recent analyses (last 24 hours)
            recent_analyses = db.execute("""
                SELECT COUNT(*) FROM ai_analyses 
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """).scalar()
            
            # Get threat correlations
            correlation_count = db.execute("SELECT COUNT(*) FROM threat_correlations").scalar()
            
            return {
                "service": "ai-service",
                "metrics": {
                    "total_analyses": analysis_count,
                    "recent_analyses_24h": recent_analyses,
                    "threat_correlations": correlation_count
                }
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "ai-service",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
