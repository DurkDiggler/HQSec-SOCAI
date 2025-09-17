"""API endpoints for SOC Agent web interface."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import (
    Alert,
    get_alerts,
    get_alert_by_id,
    get_alert_statistics,
    get_db,
    get_top_event_types,
    get_top_ips,
    get_top_sources,
    update_alert_status,
)
from .ai.threat_analyzer import AIThreatAnalyzer
from .ai.risk_assessor import AIRiskAssessor
from .mcp.server_registry import MCPServerRegistry

logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api/v1", tags=["alerts"])


@api_router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts_endpoint(
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[int] = Query(None, ge=0, le=10, description="Filter by severity"),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in message, IP, username, or event type"),
    db: Session = Depends(get_db)
):
    """Get alerts with filtering and pagination."""
    try:
        # Validate parameters
        if skip < 0:
            skip = 0
        if limit < 1 or limit > 1000:
            limit = 100
            
        alerts = get_alerts(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            severity=severity,
            source=source,
            category=category,
            search=search
        )
        
        # Get total count for pagination
        total_count = db.query(Alert).count()
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": skip + limit < total_count
            }
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@api_router.get("/alerts/{alert_id}", response_model=Dict[str, Any])
async def get_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert by ID."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"alert": alert.to_dict()}


@api_router.patch("/alerts/{alert_id}/status")
async def update_alert_status_endpoint(
    alert_id: int,
    status: str = Query(..., description="New status"),
    assigned_to: Optional[str] = Query(None, description="Assign to user"),
    notes: Optional[str] = Query(None, description="Add notes"),
    db: Session = Depends(get_db)
):
    """Update alert status."""
    valid_statuses = ["new", "acknowledged", "investigating", "resolved", "false_positive"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    alert = update_alert_status(db, alert_id, status, assigned_to, notes)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert status updated successfully", "alert": alert.to_dict()}


@api_router.get("/alerts/{alert_id}/iocs")
async def get_alert_iocs_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get IOCs for a specific alert."""
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "alert_id": alert_id,
        "iocs": alert.iocs,
        "intel_data": alert.intel_data
    }


@api_router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics_endpoint(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """Get alert statistics for dashboard."""
    try:
        stats = get_alert_statistics(db, days)
        return {"statistics": stats}
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@api_router.get("/statistics/sources")
async def get_top_sources_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top sources to return"),
    db: Session = Depends(get_db)
):
    """Get top alert sources."""
    try:
        sources = get_top_sources(db, limit)
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error fetching top sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top sources")


@api_router.get("/statistics/event-types")
async def get_top_event_types_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top event types to return"),
    db: Session = Depends(get_db)
):
    """Get top event types."""
    try:
        event_types = get_top_event_types(db, limit)
        return {"event_types": event_types}
    except Exception as e:
        logger.error(f"Error fetching top event types: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top event types")


@api_router.get("/statistics/ips")
async def get_top_ips_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top IPs to return"),
    db: Session = Depends(get_db)
):
    """Get top IP addresses."""
    try:
        ips = get_top_ips(db, limit)
        return {"ips": ips}
    except Exception as e:
        logger.error(f"Error fetching top IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top IPs")


@api_router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data_endpoint(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data."""
    try:
        # Get statistics
        stats = get_alert_statistics(db, days)
        
        # Get top sources
        sources = get_top_sources(db, 10)
        
        # Get top event types
        event_types = get_top_event_types(db, 10)
        
        # Get top IPs
        ips = get_top_ips(db, 10)
        
        # Get recent alerts (last 24 hours)
        recent_alerts = get_alerts(db, skip=0, limit=10)
        
        return {
            "statistics": stats,
            "top_sources": sources,
            "top_event_types": event_types,
            "top_ips": ips,
            "recent_alerts": [alert.to_dict() for alert in recent_alerts],
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")


@api_router.get("/health")
async def health_check_endpoint():
    """Health check for API."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@api_router.get("/filters")
async def get_available_filters_endpoint(db: Session = Depends(get_db)):
    """Get available filter options."""
    try:
        # Get unique values for filters
        sources = db.query(Alert.source).filter(Alert.source.isnot(None)).distinct().all()
        event_types = db.query(Alert.event_type).filter(Alert.event_type.isnot(None)).distinct().all()
        categories = db.query(Alert.category).filter(Alert.category.isnot(None)).distinct().all()
        statuses = db.query(Alert.status).distinct().all()
        
        return {
            "sources": [row[0] for row in sources],
            "event_types": [row[0] for row in event_types],
            "categories": [row[0] for row in categories],
            "statuses": [row[0] for row in statuses],
            "severity_levels": list(range(0, 11))
        }
    except Exception as e:
        logger.error(f"Error fetching filter options: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch filter options")


# Settings API endpoints
@api_router.get("/settings", response_model=Dict[str, Any])
async def get_settings_endpoint():
    """Get current system settings."""
    try:
        # Convert settings to dict, excluding sensitive data
        settings_dict = {
            # General Settings
            "app_host": SETTINGS.app_host,
            "app_port": SETTINGS.app_port,
            "log_level": SETTINGS.log_level,
            "log_format": SETTINGS.log_format,
            
            # Security Settings
            "max_request_size": SETTINGS.max_request_size,
            "rate_limit_requests": SETTINGS.rate_limit_requests,
            "rate_limit_window": SETTINGS.rate_limit_window,
            "cors_origins": SETTINGS.cors_origins,
            
            # Email Settings
            "enable_email": SETTINGS.enable_email,
            "smtp_host": SETTINGS.smtp_host or "",
            "smtp_port": SETTINGS.smtp_port,
            "smtp_username": SETTINGS.smtp_username or "",
            "smtp_password": "***" if SETTINGS.smtp_password else "",
            "email_from": SETTINGS.email_from or "",
            "email_to": SETTINGS.email_to,
            
            # Autotask Settings
            "enable_autotask": SETTINGS.enable_autotask,
            "at_base_url": SETTINGS.at_base_url or "",
            "at_api_integration_code": SETTINGS.at_api_integration_code or "",
            "at_username": SETTINGS.at_username or "",
            "at_secret": "***" if SETTINGS.at_secret else "",
            "at_account_id": SETTINGS.at_account_id,
            "at_queue_id": SETTINGS.at_queue_id,
            "at_ticket_priority": SETTINGS.at_ticket_priority,
            
            # Threat Intelligence
            "otx_api_key": "***" if SETTINGS.otx_api_key else "",
            "vt_api_key": "***" if SETTINGS.vt_api_key else "",
            "abuseipdb_api_key": "***" if SETTINGS.abuseipdb_api_key else "",
            
            # Scoring
            "score_high": SETTINGS.score_high,
            "score_medium": SETTINGS.score_medium,
            
            # Database
            "database_url": SETTINGS.database_url,
            "postgres_host": SETTINGS.postgres_host or "",
            "postgres_port": SETTINGS.postgres_port,
            "postgres_user": SETTINGS.postgres_user or "",
            "postgres_password": "***" if SETTINGS.postgres_password else "",
            "postgres_db": SETTINGS.postgres_db or "",
            
            # Redis
            "redis_host": SETTINGS.redis_host,
            "redis_port": SETTINGS.redis_port,
            "redis_password": "***" if SETTINGS.redis_password else "",
            "redis_db": SETTINGS.redis_db,
            
            # Webhook Security
            "webhook_shared_secret": "***" if SETTINGS.webhook_shared_secret else "",
            "webhook_hmac_secret": "***" if SETTINGS.webhook_hmac_secret else "",
            "webhook_hmac_header": SETTINGS.webhook_hmac_header,
            "webhook_hmac_prefix": SETTINGS.webhook_hmac_prefix,
            
            # Monitoring
            "enable_metrics": SETTINGS.enable_metrics,
            "metrics_port": SETTINGS.metrics_port,
            "health_check_timeout": SETTINGS.health_check_timeout,
            
            # Feature Flags
            "enable_caching": SETTINGS.enable_caching,
            "http_timeout": SETTINGS.http_timeout,
            "ioc_cache_ttl": SETTINGS.ioc_cache_ttl,
            "max_retries": SETTINGS.max_retries,
            "retry_delay": SETTINGS.retry_delay,
        }
        
        return settings_dict
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@api_router.post("/settings/test-email", response_model=Dict[str, Any])
async def test_email_endpoint():
    """Test email configuration by sending a test email."""
    try:
        from .notifiers import send_email
        
        # Send test email
        success, message = send_email(
            subject="SOC Agent - Test Email",
            body="This is a test email from SOC Agent. If you receive this, email configuration is working correctly.",
            subtype="plain"
        )
        
        return {
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing email: {e}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {e}")


@api_router.post("/settings/test-intel", response_model=Dict[str, Any])
async def test_intel_endpoint():
    """Test threat intelligence API configuration."""
    try:
        from .intel.client import IntelClient
        
        intel_client = IntelClient()
        results = {}
        
        # Test OTX
        if SETTINGS.otx_api_key:
            try:
                test_result = await intel_client.check_ip("8.8.8.8", "otx")
                results["otx"] = {"status": "success", "message": "OTX API working"}
            except Exception as e:
                results["otx"] = {"status": "error", "message": str(e)}
        else:
            results["otx"] = {"status": "disabled", "message": "OTX API key not configured"}
        
        # Test VirusTotal
        if SETTINGS.vt_api_key:
            try:
                test_result = await intel_client.check_ip("8.8.8.8", "virustotal")
                results["virustotal"] = {"status": "success", "message": "VirusTotal API working"}
            except Exception as e:
                results["virustotal"] = {"status": "error", "message": str(e)}
        else:
            results["virustotal"] = {"status": "disabled", "message": "VirusTotal API key not configured"}
        
        # Test AbuseIPDB
        if SETTINGS.abuseipdb_api_key:
            try:
                test_result = await intel_client.check_ip("8.8.8.8", "abuseipdb")
                results["abuseipdb"] = {"status": "success", "message": "AbuseIPDB API working"}
            except Exception as e:
                results["abuseipdb"] = {"status": "error", "message": str(e)}
        else:
            results["abuseipdb"] = {"status": "disabled", "message": "AbuseIPDB API key not configured"}
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing intel APIs: {e}")
        raise HTTPException(status_code=500, detail=f"Intel API test failed: {e}")


@api_router.post("/settings/test-database", response_model=Dict[str, Any])
async def test_database_endpoint(db: Session = Depends(get_db)):
    """Test database connection."""
    try:
        # Simple database test
        alert_count = db.query(Alert).count()
        
        return {
            "success": True,
            "message": f"Database connection successful. Found {alert_count} alerts.",
            "alert_count": alert_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing database: {e}")
        raise HTTPException(status_code=500, detail=f"Database test failed: {e}")


# AI Analysis Endpoints
@api_router.post("/ai/analyze/{alert_id}", response_model=Dict[str, Any])
async def ai_analyze_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Perform AI analysis on a specific alert."""
    try:
        alert = get_alert_by_id(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Convert alert to event data
        event_data = {
            "source": alert.source,
            "event_type": alert.event_type,
            "severity": alert.severity,
            "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
            "message": alert.message,
            "ip": alert.ip,
            "username": alert.username,
            "raw": alert.raw_data
        }
        
        # Perform AI analysis
        ai_analyzer = AIThreatAnalyzer()
        ai_analysis = await ai_analyzer.analyze_threat(event_data)
        
        return {
            "alert_id": alert_id,
            "ai_analysis": ai_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed for alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")


@api_router.post("/ai/risk-assessment", response_model=Dict[str, Any])
async def ai_risk_assessment_endpoint(
    threat_data: Dict[str, Any]
):
    """Perform AI risk assessment."""
    try:
        risk_assessor = AIRiskAssessor()
        risk_assessment = await risk_assessor.assess_risk(threat_data)
        
        return {
            "risk_assessment": risk_assessment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {e}")


@api_router.post("/ai/correlate-threats", response_model=Dict[str, Any])
async def ai_correlate_threats_endpoint(
    event_ids: List[int],
    db: Session = Depends(get_db)
):
    """Correlate multiple threats using AI."""
    try:
        # Get alerts
        events = []
        for event_id in event_ids:
            alert = get_alert_by_id(db, event_id)
            if alert:
                event_data = {
                    "source": alert.source,
                    "event_type": alert.event_type,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
                    "message": alert.message,
                    "ip": alert.ip,
                    "username": alert.username,
                    "raw": alert.raw_data
                }
                events.append(event_data)
        
        if not events:
            raise HTTPException(status_code=404, detail="No valid alerts found")
        
        # Perform correlation analysis
        ai_analyzer = AIThreatAnalyzer()
        correlation_analysis = await ai_analyzer.correlate_threats(events)
        
        return {
            "correlation_analysis": correlation_analysis,
            "event_count": len(events),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI threat correlation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Threat correlation failed: {e}")


# MCP Server Endpoints
@api_router.post("/mcp/scan", response_model=Dict[str, Any])
async def mcp_scan_endpoint(
    target: str = Query(..., description="Target to scan"),
    scan_type: str = Query("basic", description="Type of scan to perform")
):
    """Perform scan using MCP servers."""
    try:
        async with MCPServerRegistry() as mcp_registry:
            result = await mcp_registry.scan_target(target, scan_type)
            
            return {
                "scan_result": result,
                "target": target,
                "scan_type": scan_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"MCP scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")


@api_router.post("/mcp/test-exploit", response_model=Dict[str, Any])
async def mcp_test_exploit_endpoint(
    target: str = Query(..., description="Target to test"),
    vulnerability: str = Query(..., description="Vulnerability to test"),
    exploit_type: str = Query("basic", description="Type of exploit test")
):
    """Test exploit using MCP servers."""
    try:
        async with MCPServerRegistry() as mcp_registry:
            result = await mcp_registry.test_exploit(target, vulnerability, exploit_type)
            
            return {
                "exploit_test_result": result,
                "target": target,
                "vulnerability": vulnerability,
                "exploit_type": exploit_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"MCP exploit test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Exploit test failed: {e}")


@api_router.post("/mcp/offensive-test", response_model=Dict[str, Any])
async def mcp_offensive_test_endpoint(
    target: str = Query(..., description="Target for offensive testing"),
    test_scenarios: List[Dict[str, Any]] = Query(..., description="Test scenarios to run")
):
    """Run offensive test suite using MCP servers."""
    try:
        if not SETTINGS.enable_offensive_testing:
            raise HTTPException(status_code=403, detail="Offensive testing is disabled")
        
        async with MCPServerRegistry() as mcp_registry:
            result = await mcp_registry.run_offensive_test_suite(target, test_scenarios)
            
            return {
                "offensive_test_result": result,
                "target": target,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"MCP offensive test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Offensive test failed: {e}")


@api_router.get("/mcp/status", response_model=Dict[str, Any])
async def mcp_status_endpoint():
    """Get status of all MCP servers."""
    try:
        async with MCPServerRegistry() as mcp_registry:
            status = await mcp_registry.get_server_status()
            
            return {
                "mcp_servers": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"MCP status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")


@api_router.get("/mcp/capabilities", response_model=Dict[str, Any])
async def mcp_capabilities_endpoint():
    """Get capabilities of all MCP servers."""
    try:
        mcp_registry = MCPServerRegistry()
        capabilities = mcp_registry.get_server_capabilities()
        
        return {
            "capabilities": capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"MCP capabilities check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Capabilities check failed: {e}")
