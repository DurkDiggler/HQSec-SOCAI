"""ML-specific API endpoints for model inference and management."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .ml.model_manager import ModelManager
from .config import SETTINGS

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ml", tags=["ML"])

# Initialize model manager
model_manager = ModelManager()

# Pydantic models for request/response
class EventData(BaseModel):
    """Event data for ML analysis."""
    message: str = Field(..., description="Event message")
    event_type: str = Field(..., description="Type of event")
    source: str = Field(..., description="Event source")
    severity: str = Field(default="MEDIUM", description="Event severity")
    ip: Optional[str] = Field(None, description="IP address")
    user: Optional[str] = Field(None, description="Username")
    timestamp: Optional[str] = Field(None, description="Event timestamp")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")

class ThreatData(BaseModel):
    """Threat data for risk assessment."""
    threat_type: str = Field(..., description="Type of threat")
    severity: str = Field(default="MEDIUM", description="Threat severity")
    asset_criticality: str = Field(default="MEDIUM", description="Asset criticality")
    business_impact: str = Field(default="MEDIUM", description="Business impact")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional threat data")

class IncidentData(BaseModel):
    """Incident data for classification."""
    message: str = Field(..., description="Incident message")
    event_type: str = Field(..., description="Type of incident")
    source: str = Field(..., description="Incident source")
    severity: str = Field(default="MEDIUM", description="Incident severity")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional incident data")

class AlertData(BaseModel):
    """Alert data for false positive filtering."""
    message: str = Field(..., description="Alert message")
    event_type: str = Field(..., description="Type of alert")
    source: str = Field(..., description="Alert source")
    severity: str = Field(default="MEDIUM", description="Alert severity")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional alert data")

class FeedbackData(BaseModel):
    """Feedback data for model learning."""
    alert_data: Dict[str, Any] = Field(..., description="Alert data")
    is_false_positive: bool = Field(..., description="Whether the alert is a false positive")
    analyst_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Analyst confidence in feedback")

class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis."""
    events: List[EventData] = Field(..., description="List of events to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")

# ML Analysis Endpoints
@router.post("/analyze/anomaly")
async def analyze_anomaly(event_data: EventData):
    """Analyze event for anomalies."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.predict_anomaly(event_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Anomaly analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly analysis failed: {str(e)}"
        )

@router.post("/analyze/risk")
async def analyze_risk(threat_data: ThreatData):
    """Calculate risk score for threat."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.calculate_risk_score(threat_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk analysis failed: {str(e)}"
        )

@router.post("/analyze/classify")
async def classify_incident(incident_data: IncidentData):
    """Classify incident into categories."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.classify_incident(incident_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Incident classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incident classification failed: {str(e)}"
        )

@router.post("/analyze/filter-fp")
async def filter_false_positives(alert_data: AlertData):
    """Filter false positives from alert."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.filter_false_positives(alert_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"False positive filtering failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"False positive filtering failed: {str(e)}"
        )

@router.post("/analyze/patterns")
async def detect_patterns(event_data: EventData):
    """Detect attack patterns in event."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.detect_patterns(event_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern detection failed: {str(e)}"
        )

@router.post("/analyze/comprehensive")
async def comprehensive_analysis(event_data: EventData):
    """Perform comprehensive analysis using all models."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.comprehensive_analysis(event_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive analysis failed: {str(e)}"
        )

@router.post("/analyze/batch")
async def batch_analysis(request: BatchAnalysisRequest):
    """Perform batch analysis on multiple events."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        events = [event.dict() for event in request.events]
        analysis_type = request.analysis_type
        
        if analysis_type == "comprehensive":
            results = []
            for event in events:
                result = await model_manager.comprehensive_analysis(event)
                results.append(result)
        else:
            # Individual analysis for each event
            results = []
            for event in events:
                if analysis_type == "anomaly":
                    result = await model_manager.predict_anomaly(event)
                elif analysis_type == "risk":
                    result = await model_manager.calculate_risk_score(event)
                elif analysis_type == "classify":
                    result = await model_manager.classify_incident(event)
                elif analysis_type == "filter-fp":
                    result = await model_manager.filter_false_positives(event)
                elif analysis_type == "patterns":
                    result = await model_manager.detect_patterns(event)
                else:
                    result = {"error": f"Unknown analysis type: {analysis_type}"}
                
                results.append(result)
        
        return JSONResponse(content={
            "analysis_type": analysis_type,
            "results": results,
            "total_events": len(events),
            "analysis_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )

# Model Management Endpoints
@router.get("/models/status")
async def get_model_status():
    """Get status of all ML models."""
    try:
        status = model_manager.get_model_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )

@router.get("/models/performance")
async def get_model_performance():
    """Get performance metrics for all models."""
    try:
        metrics = model_manager.get_performance_metrics()
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model performance: {str(e)}"
        )

@router.post("/models/load")
async def load_models():
    """Load all trained models from disk."""
    try:
        results = await model_manager.load_all_models()
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load models: {str(e)}"
        )

@router.post("/models/cleanup")
async def cleanup_models(retention_days: int = None):
    """Clean up old model versions."""
    try:
        results = model_manager.cleanup_old_models(retention_days)
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Failed to cleanup models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup models: {str(e)}"
        )

@router.post("/models/export")
async def export_models(export_path: str):
    """Export all models to specified path."""
    try:
        results = model_manager.export_models(export_path)
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Failed to export models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export models: {str(e)}"
        )

@router.post("/models/import")
async def import_models(import_path: str):
    """Import models from specified path."""
    try:
        results = model_manager.import_models(import_path)
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Failed to import models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import models: {str(e)}"
        )

# Learning and Feedback Endpoints
@router.post("/learn/feedback")
async def submit_feedback(feedback_data: FeedbackData):
    """Submit feedback for model learning."""
    try:
        if not SETTINGS.ml_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ML analysis is disabled"
            )
        
        result = await model_manager.models['false_positive_filter'].learn_from_feedback(feedback_data.dict())
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )

# Health Check Endpoint
@router.get("/health")
async def ml_health_check():
    """ML service health check."""
    try:
        status = model_manager.get_model_status()
        
        # Check if any models are trained
        trained_models = sum(1 for model_status in status.values() if model_status.get('is_trained', False))
        total_models = len(status)
        
        health_status = "healthy" if trained_models > 0 else "degraded"
        
        return JSONResponse(content={
            "status": health_status,
            "service": "ml-service",
            "version": "1.0.0",
            "trained_models": trained_models,
            "total_models": total_models,
            "model_status": status
        })
        
    except Exception as e:
        logger.error(f"ML health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service unhealthy: {str(e)}"
        )

# Metrics Endpoint
@router.get("/metrics")
async def get_ml_metrics():
    """Get ML service metrics."""
    try:
        performance_metrics = model_manager.get_performance_metrics()
        model_status = model_manager.get_model_status()
        
        return JSONResponse(content={
            "service": "ml-service",
            "metrics": {
                "performance_metrics": performance_metrics,
                "model_status": model_status,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get ML metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML metrics: {str(e)}"
        )
