"""API endpoints for advanced analytics and threat intelligence."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .config import SETTINGS
from .database import get_db
from .analytics.threat_hunting import ThreatHunter
from .analytics.attack_attribution import AttackAttributor
from .analytics.vulnerability_correlation import VulnerabilityCorrelator
from .analytics.business_impact import BusinessImpactAnalyzer
from .analytics.threat_intelligence import ThreatIntelligenceFeed
from .analytics.analytics_dashboard import AnalyticsDashboard

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Initialize analytics components
threat_hunter = ThreatHunter()
attack_attributor = AttackAttributor()
vulnerability_correlator = VulnerabilityCorrelator()
business_impact_analyzer = BusinessImpactAnalyzer()
threat_intelligence = ThreatIntelligenceFeed()
analytics_dashboard = AnalyticsDashboard()

# Threat Hunting Endpoints

@router.post("/threat-hunting/hypotheses", response_model=Dict[str, Any])
async def generate_threat_hypotheses(
    time_window_hours: int = 24,
    threat_landscape: Dict[str, Any] = None
):
    """Generate threat hunting hypotheses."""
    try:
        hypotheses = await threat_hunter.generate_hypotheses(
            time_window_hours=time_window_hours,
            threat_landscape=threat_landscape
        )
        return {
            "hypotheses": hypotheses,
            "count": len(hypotheses),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating threat hypotheses: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/threat-hunting/execute/{hypothesis_id}", response_model=Dict[str, Any])
async def execute_threat_hypothesis(
    hypothesis_id: str,
    time_window_hours: int = 24
):
    """Execute a threat hunting hypothesis."""
    try:
        result = await threat_hunter.execute_hypothesis(
            hypothesis_id=hypothesis_id,
            time_window_hours=time_window_hours
        )
        return result
    except Exception as e:
        logger.error(f"Error executing threat hypothesis: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/threat-hunting/status", response_model=Dict[str, Any])
async def get_threat_hunting_status():
    """Get threat hunting system status."""
    try:
        status = await threat_hunter.get_hunting_status()
        return status
    except Exception as e:
        logger.error(f"Error getting threat hunting status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Attack Attribution Endpoints

@router.post("/attack-attribution/analyze", response_model=Dict[str, Any])
async def analyze_attack_attribution(
    attack_data: Dict[str, Any],
    confidence_threshold: float = 0.7
):
    """Analyze attack attribution."""
    try:
        result = await attack_attributor.attribute_attack(
            attack_data=attack_data,
            confidence_threshold=confidence_threshold
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing attack attribution: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/attack-attribution/campaign", response_model=Dict[str, Any])
async def analyze_campaign_attribution(
    campaign_data: List[Dict[str, Any]],
    time_window_days: int = 30
):
    """Analyze campaign attribution."""
    try:
        result = await attack_attributor.analyze_campaign(
            campaign_data=campaign_data,
            time_window_days=time_window_days
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing campaign attribution: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/attack-attribution/status", response_model=Dict[str, Any])
async def get_attack_attribution_status():
    """Get attack attribution system status."""
    try:
        status = await attack_attributor.get_attribution_status()
        return status
    except Exception as e:
        logger.error(f"Error getting attack attribution status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Vulnerability Correlation Endpoints

@router.post("/vulnerability-correlation/analyze", response_model=Dict[str, Any])
async def analyze_vulnerability_correlation(
    asset_id: str = None,
    time_window_days: int = 30
):
    """Analyze vulnerability correlation."""
    try:
        result = await vulnerability_correlator.correlate_vulnerabilities(
            asset_id=asset_id,
            time_window_days=time_window_days
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing vulnerability correlation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/vulnerability-correlation/trends", response_model=Dict[str, Any])
async def get_vulnerability_trends(time_window_days: int = 90):
    """Get vulnerability trends."""
    try:
        result = await vulnerability_correlator.get_vulnerability_trends(
            time_window_days=time_window_days
        )
        return result
    except Exception as e:
        logger.error(f"Error getting vulnerability trends: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/vulnerability-correlation/status", response_model=Dict[str, Any])
async def get_vulnerability_correlation_status():
    """Get vulnerability correlation system status."""
    try:
        status = await vulnerability_correlator.get_correlation_status()
        return status
    except Exception as e:
        logger.error(f"Error getting vulnerability correlation status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Business Impact Analysis Endpoints

@router.post("/business-impact/analyze", response_model=Dict[str, Any])
async def analyze_business_impact(
    incident_data: Dict[str, Any],
    asset_data: Dict[str, Any] = None
):
    """Analyze business impact of an incident."""
    try:
        result = await business_impact_analyzer.analyze_business_impact(
            incident_data=incident_data,
            asset_data=asset_data
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing business impact: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/business-impact/status", response_model=Dict[str, Any])
async def get_business_impact_status():
    """Get business impact analysis system status."""
    try:
        status = await business_impact_analyzer.get_business_impact_status()
        return status
    except Exception as e:
        logger.error(f"Error getting business impact status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Threat Intelligence Endpoints

@router.post("/threat-intelligence/collect", response_model=Dict[str, Any])
async def collect_threat_intelligence(
    feed_names: List[str] = None,
    force_update: bool = False
):
    """Collect threat intelligence from feeds."""
    try:
        result = await threat_intelligence.collect_threat_intelligence(
            feed_names=feed_names,
            force_update=force_update
        )
        return result
    except Exception as e:
        logger.error(f"Error collecting threat intelligence: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/threat-intelligence/correlate", response_model=Dict[str, Any])
async def correlate_threat_intelligence(
    event_data: Dict[str, Any],
    confidence_threshold: float = 0.7
):
    """Correlate IOCs with threat intelligence."""
    try:
        result = await threat_intelligence.correlate_iocs(
            event_data=event_data,
            confidence_threshold=confidence_threshold
        )
        return result
    except Exception as e:
        logger.error(f"Error correlating threat intelligence: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/threat-intelligence/status", response_model=Dict[str, Any])
async def get_threat_intelligence_status():
    """Get threat intelligence system status."""
    try:
        status = await threat_intelligence.get_threat_intelligence_status()
        return status
    except Exception as e:
        logger.error(f"Error getting threat intelligence status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Analytics Dashboard Endpoints

@router.get("/dashboard/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(time_window_hours: int = 24):
    """Get comprehensive dashboard overview."""
    try:
        result = await analytics_dashboard.get_dashboard_overview(
            time_window_hours=time_window_hours
        )
        return result
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/dashboard/status", response_model=Dict[str, Any])
async def get_dashboard_status():
    """Get analytics dashboard status."""
    try:
        status = await analytics_dashboard.get_dashboard_status()
        return status
    except Exception as e:
        logger.error(f"Error getting dashboard status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Combined Analytics Endpoints

@router.post("/analyze/incident", response_model=Dict[str, Any])
async def analyze_incident_comprehensive(
    incident_data: Dict[str, Any],
    asset_data: Dict[str, Any] = None,
    include_attribution: bool = True,
    include_business_impact: bool = True,
    include_vulnerability_correlation: bool = True
):
    """Perform comprehensive incident analysis."""
    try:
        analysis_results = {
            "incident_id": incident_data.get("id", "unknown"),
            "analysis_time": datetime.utcnow().isoformat(),
            "threat_hunting": None,
            "attack_attribution": None,
            "business_impact": None,
            "vulnerability_correlation": None,
            "threat_intelligence": None
        }
        
        # Threat hunting analysis
        if incident_data.get("event_type") in ["malware", "intrusion", "data_breach"]:
            hypotheses = await threat_hunter.generate_hypotheses(time_window_hours=24)
            analysis_results["threat_hunting"] = {
                "hypotheses_generated": len(hypotheses),
                "high_priority_hypotheses": len([h for h in hypotheses if h.get("priority", 0) >= 8])
            }
        
        # Attack attribution analysis
        if include_attribution:
            attribution_result = await attack_attributor.attribute_attack(incident_data)
            analysis_results["attack_attribution"] = attribution_result
        
        # Business impact analysis
        if include_business_impact:
            impact_result = await business_impact_analyzer.analyze_business_impact(
                incident_data, asset_data
            )
            analysis_results["business_impact"] = impact_result
        
        # Vulnerability correlation analysis
        if include_vulnerability_correlation and asset_data:
            vuln_result = await vulnerability_correlator.correlate_vulnerabilities(
                asset_id=asset_data.get("id")
            )
            analysis_results["vulnerability_correlation"] = vuln_result
        
        # Threat intelligence correlation
        ti_result = await threat_intelligence.correlate_iocs(incident_data)
        analysis_results["threat_intelligence"] = ti_result
        
        # Generate overall recommendations
        recommendations = []
        if analysis_results["attack_attribution"] and analysis_results["attack_attribution"].get("high_confidence_attributions"):
            recommendations.append("High confidence attribution found - investigate threat actor TTPs")
        
        if analysis_results["business_impact"] and analysis_results["business_impact"].get("overall_impact", {}).get("level") in ["Critical", "High"]:
            recommendations.append("High business impact - escalate to management")
        
        if analysis_results["threat_intelligence"] and analysis_results["threat_intelligence"].get("overall_threat_level") in ["Critical", "High"]:
            recommendations.append("High threat intelligence correlation - implement additional monitoring")
        
        analysis_results["recommendations"] = recommendations
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error in comprehensive incident analysis: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def analytics_health_check():
    """Health check for analytics components."""
    try:
        health_status = {
            "threat_hunting": True,
            "attack_attribution": True,
            "vulnerability_correlation": True,
            "business_impact": True,
            "threat_intelligence": True,
            "analytics_dashboard": True,
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check individual components
        try:
            await threat_hunter.get_hunting_status()
        except:
            health_status["threat_hunting"] = False
        
        try:
            await attack_attributor.get_attribution_status()
        except:
            health_status["attack_attribution"] = False
        
        try:
            await vulnerability_correlator.get_correlation_status()
        except:
            health_status["vulnerability_correlation"] = False
        
        try:
            await business_impact_analyzer.get_business_impact_status()
        except:
            health_status["business_impact"] = False
        
        try:
            await threat_intelligence.get_threat_intelligence_status()
        except:
            health_status["threat_intelligence"] = False
        
        try:
            await analytics_dashboard.get_dashboard_status()
        except:
            health_status["analytics_dashboard"] = False
        
        # Determine overall status
        if not all(health_status[key] for key in health_status if key not in ["overall_status", "timestamp"]):
            health_status["overall_status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in analytics health check: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
