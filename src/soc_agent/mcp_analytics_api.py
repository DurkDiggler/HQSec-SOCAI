"""API endpoints for MCP analytics integration and interactive security testing."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import get_db
from .analytics.mcp_analytics_bridge import MCPAnalyticsBridge

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/mcp-analytics", tags=["mcp-analytics"])

# MCP Analytics Endpoints

@router.post("/scan/run", response_model=Dict[str, Any])
async def run_security_scan(
    target: str,
    scan_type: str = "comprehensive",
    options: Dict[str, Any] = None
):
    """Run a security scan using MCP tools with analytics correlation."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            result = await bridge.run_security_scan(
                target=target,
                scan_type=scan_type,
                options=options or {}
            )
            return result
    except Exception as e:
        logger.error(f"Error running security scan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/scan/types", response_model=Dict[str, Any])
async def get_scan_types():
    """Get available scan types and their descriptions."""
    return {
        "scan_types": {
            "nmap": {
                "name": "Nmap Network Scan",
                "description": "Network discovery and port scanning",
                "capabilities": ["port_scan", "service_detection", "os_detection"],
                "estimated_duration": "5-15 minutes"
            },
            "vuln": {
                "name": "Vulnerability Scan",
                "description": "Comprehensive vulnerability assessment",
                "capabilities": ["cve_scanning", "plugin_scanning", "risk_assessment"],
                "estimated_duration": "15-60 minutes"
            },
            "web": {
                "name": "Web Application Scan",
                "description": "Web application security testing",
                "capabilities": ["sql_injection", "xss", "csrf", "directory_traversal"],
                "estimated_duration": "10-30 minutes"
            },
            "network": {
                "name": "Network Discovery Scan",
                "description": "Network device discovery and enumeration",
                "capabilities": ["device_discovery", "mac_resolution", "os_fingerprinting"],
                "estimated_duration": "5-10 minutes"
            },
            "comprehensive": {
                "name": "Comprehensive Security Scan",
                "description": "Combined scan using multiple tools",
                "capabilities": ["all_above"],
                "estimated_duration": "30-90 minutes"
            }
        }
    }

@router.get("/tools/available", response_model=Dict[str, Any])
async def get_available_tools():
    """Get available MCP tools and their capabilities."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            tools = await bridge.get_available_tools()
            return tools
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/tools/status", response_model=Dict[str, Any])
async def get_mcp_status():
    """Get MCP server status and connectivity."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            status = await bridge.get_mcp_status()
            return status
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/scan/history", response_model=List[Dict[str, Any]])
async def get_scan_history(limit: int = 50):
    """Get scan history from the database."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            history = await bridge.get_scan_history(limit=limit)
            return history
    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/scan/quick", response_model=Dict[str, Any])
async def run_quick_scan(
    target: str,
    scan_type: str = "nmap"
):
    """Run a quick security scan for immediate results."""
    try:
        # Quick scan options for faster results
        quick_options = {
            "ports": "1-1000",
            "timing": "T4",
            "service_detection": True,
            "script_scan": False,  # Disable for speed
            "os_detection": False  # Disable for speed
        }
        
        async with MCPAnalyticsBridge() as bridge:
            result = await bridge.run_security_scan(
                target=target,
                scan_type=scan_type,
                options=quick_options
            )
            return result
    except Exception as e:
        logger.error(f"Error running quick scan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/scan/scheduled", response_model=Dict[str, Any])
async def schedule_scan(
    target: str,
    scan_type: str = "comprehensive",
    schedule_time: str = None,
    options: Dict[str, Any] = None
):
    """Schedule a security scan for later execution."""
    try:
        # This would integrate with a task scheduler like Celery
        # For now, we'll just return a confirmation
        return {
            "message": "Scan scheduled successfully",
            "target": target,
            "scan_type": scan_type,
            "schedule_time": schedule_time or "immediate",
            "status": "scheduled"
        }
    except Exception as e:
        logger.error(f"Error scheduling scan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/correlate/{scan_id}", response_model=Dict[str, Any])
async def correlate_scan_analytics(scan_id: str):
    """Correlate scan results with analytics system."""
    try:
        # This would retrieve scan results and correlate with analytics
        # For now, return a placeholder
        return {
            "scan_id": scan_id,
            "correlation_status": "completed",
            "threat_level": "medium",
            "risk_score": 0.65,
            "recommendations": [
                "Review open ports and close unnecessary services",
                "Update vulnerable software components",
                "Implement network segmentation"
            ]
        }
    except Exception as e:
        logger.error(f"Error correlating scan analytics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/dashboard/integration", response_model=Dict[str, Any])
async def get_dashboard_integration():
    """Get MCP integration status for the analytics dashboard."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            mcp_status = await bridge.get_mcp_status()
            tools = await bridge.get_available_tools()
            
            return {
                "mcp_status": mcp_status,
                "available_tools": tools,
                "integration_enabled": True,
                "dashboard_ready": True,
                "last_updated": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting dashboard integration status: {e}")
        return {
            "integration_enabled": False,
            "dashboard_ready": False,
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat()
        }

@router.post("/test/connectivity", response_model=Dict[str, Any])
async def test_mcp_connectivity():
    """Test connectivity to MCP servers."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            status = await bridge.get_mcp_status()
            
            # Test actual connectivity
            connectivity_tests = {
                "kali_mcp": {"status": "unknown", "response_time": 0},
                "vuln_scanner": {"status": "unknown", "response_time": 0}
            }
            
            # Test Kali MCP
            try:
                import time
                start_time = time.time()
                if bridge.session:
                    async with bridge.session.get(f"{bridge.kali_mcp_url}/health") as response:
                        response_time = time.time() - start_time
                        connectivity_tests["kali_mcp"] = {
                            "status": "online" if response.status == 200 else "offline",
                            "response_time": round(response_time, 3)
                        }
            except Exception as e:
                connectivity_tests["kali_mcp"] = {"status": "offline", "error": str(e)}
            
            # Test vulnerability scanner
            try:
                start_time = time.time()
                if bridge.session:
                    async with bridge.session.get(f"{bridge.vuln_scanner_url}/health") as response:
                        response_time = time.time() - start_time
                        connectivity_tests["vuln_scanner"] = {
                            "status": "online" if response.status == 200 else "offline",
                            "response_time": round(response_time, 3)
                        }
            except Exception as e:
                connectivity_tests["vuln_scanner"] = {"status": "offline", "error": str(e)}
            
            return {
                "connectivity_tests": connectivity_tests,
                "overall_status": "healthy" if all(
                    test["status"] == "online" for test in connectivity_tests.values()
                ) else "degraded",
                "test_time": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error testing MCP connectivity: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def mcp_analytics_health_check():
    """Health check for MCP analytics integration."""
    try:
        async with MCPAnalyticsBridge() as bridge:
            mcp_status = await bridge.get_mcp_status()
            
            health_status = {
                "mcp_analytics_bridge": True,
                "kali_mcp": mcp_status.get("kali_mcp", {}).get("status") == "online",
                "vuln_scanner": mcp_status.get("vuln_scanner", {}).get("status") == "online",
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Determine overall status
            if not health_status["kali_mcp"] or not health_status["vuln_scanner"]:
                health_status["overall_status"] = "degraded"
            
            return health_status
            
    except Exception as e:
        logger.error(f"Error in MCP analytics health check: {e}")
        return {
            "mcp_analytics_bridge": False,
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
