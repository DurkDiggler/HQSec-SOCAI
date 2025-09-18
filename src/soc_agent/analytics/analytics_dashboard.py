"""Advanced analytics dashboard and visualizations."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents
from .threat_hunting import ThreatHunter
from .attack_attribution import AttackAttributor
from .vulnerability_correlation import VulnerabilityCorrelator
from .business_impact import BusinessImpactAnalyzer
from .threat_intelligence import ThreatIntelligenceFeed

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """
    Advanced analytics dashboard that provides comprehensive
    insights and visualizations for security operations.
    """

    def __init__(self):
        self.threat_hunter = ThreatHunter()
        self.attack_attributor = AttackAttributor()
        self.vulnerability_correlator = VulnerabilityCorrelator()
        self.business_impact_analyzer = BusinessImpactAnalyzer()
        self.threat_intelligence = ThreatIntelligenceFeed()
        self.dashboard_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_dashboard_overview(self, 
                                   time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Gets comprehensive dashboard overview.
        
        Args:
            time_window_hours: Time window for analysis
            
        Returns:
            Dashboard overview data
        """
        try:
            logger.info(f"Generating dashboard overview for {time_window_hours} hours")
            
            # Check cache first
            cache_key = f"dashboard_overview_{time_window_hours}"
            if self._is_cache_valid(cache_key):
                return self.dashboard_cache[cache_key]
            
            # Get time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            # Collect data from all analytics components
            overview_data = {
                "time_window": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": time_window_hours
                },
                "threat_landscape": await self._get_threat_landscape_overview(start_time, end_time),
                "security_metrics": await self._get_security_metrics(start_time, end_time),
                "threat_hunting": await self._get_threat_hunting_overview(),
                "attack_attribution": await self._get_attack_attribution_overview(),
                "vulnerability_analysis": await self._get_vulnerability_analysis_overview(),
                "business_impact": await self._get_business_impact_overview(),
                "threat_intelligence": await self._get_threat_intelligence_overview(),
                "recommendations": await self._generate_dashboard_recommendations(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the results
            self.dashboard_cache[cache_key] = overview_data
            self.dashboard_cache[cache_key]["cached_at"] = datetime.utcnow().isoformat()
            
            logger.info("Dashboard overview generated successfully")
            return overview_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard overview: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }

    async def _get_threat_landscape_overview(self, 
                                           start_time: datetime, 
                                           end_time: datetime) -> Dict[str, Any]:
        """Gets threat landscape overview."""
        try:
            with get_db() as db:
                alerts = get_historical_alerts(db, limit=1000)
                incidents = get_historical_incidents(db, limit=100)
            
            # Filter by time window
            alerts = [a for a in alerts if self._is_within_time_window(a.get("timestamp", ""), start_time, end_time)]
            incidents = [i for i in incidents if self._is_within_time_window(i.get("timestamp", ""), start_time, end_time)]
            
            # Calculate metrics
            total_alerts = len(alerts)
            total_incidents = len(incidents)
            high_severity_alerts = len([a for a in alerts if a.get("severity") in ["HIGH", "CRITICAL"]])
            resolved_incidents = len([i for i in incidents if i.get("status") == "resolved"])
            
            # Calculate trends
            alert_trend = await self._calculate_trend(alerts, "hourly")
            incident_trend = await self._calculate_trend(incidents, "daily")
            
            # Top threat types
            threat_types = {}
            for alert in alerts:
                event_type = alert.get("event_type", "unknown")
                threat_types[event_type] = threat_types.get(event_type, 0) + 1
            
            top_threats = sorted(threat_types.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_alerts": total_alerts,
                "total_incidents": total_incidents,
                "high_severity_alerts": high_severity_alerts,
                "resolved_incidents": resolved_incidents,
                "alert_trend": alert_trend,
                "incident_trend": incident_trend,
                "top_threats": top_threats,
                "threat_level": self._calculate_overall_threat_level(alerts, incidents)
            }
            
        except Exception as e:
            logger.error(f"Error getting threat landscape overview: {e}")
            return {"error": str(e)}

    async def _get_security_metrics(self, 
                                  start_time: datetime, 
                                  end_time: datetime) -> Dict[str, Any]:
        """Gets security metrics overview."""
        try:
            with get_db() as db:
                alerts = get_historical_alerts(db, limit=1000)
                incidents = get_historical_incidents(db, limit=100)
            
            # Filter by time window
            alerts = [a for a in alerts if self._is_within_time_window(a.get("timestamp", ""), start_time, end_time)]
            incidents = [i for i in incidents if self._is_within_time_window(i.get("timestamp", ""), start_time, end_time)]
            
            # Calculate metrics
            metrics = {
                "mean_time_to_detection": await self._calculate_mttd(alerts),
                "mean_time_to_response": await self._calculate_mttr(incidents),
                "false_positive_rate": await self._calculate_false_positive_rate(alerts),
                "incident_resolution_rate": await self._calculate_resolution_rate(incidents),
                "threat_detection_accuracy": await self._calculate_detection_accuracy(alerts),
                "security_operations_efficiency": await self._calculate_operations_efficiency(alerts, incidents)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting security metrics: {e}")
            return {"error": str(e)}

    async def _get_threat_hunting_overview(self) -> Dict[str, Any]:
        """Gets threat hunting overview."""
        try:
            # Get threat hunting status
            hunting_status = await self.threat_hunter.get_hunting_status()
            
            # Generate sample hypotheses
            hypotheses = await self.threat_hunter.generate_hypotheses(time_window_hours=24)
            
            return {
                "status": hunting_status,
                "active_hypotheses": len(hypotheses),
                "high_priority_hypotheses": len([h for h in hypotheses if h.get("priority", 0) >= 8]),
                "hypotheses": hypotheses[:5]  # Top 5 hypotheses
            }
            
        except Exception as e:
            logger.error(f"Error getting threat hunting overview: {e}")
            return {"error": str(e)}

    async def _get_attack_attribution_overview(self) -> Dict[str, Any]:
        """Gets attack attribution overview."""
        try:
            # Get attribution status
            attribution_status = await self.attack_attributor.get_attribution_status()
            
            # Get recent attribution results (simulated)
            recent_attributions = {
                "total_attributions": 15,
                "high_confidence": 8,
                "medium_confidence": 5,
                "low_confidence": 2,
                "top_threat_actors": [
                    {"name": "APT1", "count": 5, "confidence": 0.9},
                    {"name": "Lazarus Group", "count": 3, "confidence": 0.8},
                    {"name": "FIN7", "count": 2, "confidence": 0.7}
                ]
            }
            
            return {
                "status": attribution_status,
                "recent_attributions": recent_attributions
            }
            
        except Exception as e:
            logger.error(f"Error getting attack attribution overview: {e}")
            return {"error": str(e)}

    async def _get_vulnerability_analysis_overview(self) -> Dict[str, Any]:
        """Gets vulnerability analysis overview."""
        try:
            # Get vulnerability correlation status
            vuln_status = await self.vulnerability_correlator.get_correlation_status()
            
            # Get vulnerability trends
            vuln_trends = await self.vulnerability_correlator.get_vulnerability_trends()
            
            return {
                "status": vuln_status,
                "trends": vuln_trends
            }
            
        except Exception as e:
            logger.error(f"Error getting vulnerability analysis overview: {e}")
            return {"error": str(e)}

    async def _get_business_impact_overview(self) -> Dict[str, Any]:
        """Gets business impact analysis overview."""
        try:
            # Get business impact status
            impact_status = await self.business_impact_analyzer.get_business_impact_status()
            
            # Get recent impact assessments (simulated)
            recent_impacts = {
                "total_assessments": 25,
                "critical_impact": 3,
                "high_impact": 8,
                "medium_impact": 10,
                "low_impact": 4,
                "average_impact_score": 0.65
            }
            
            return {
                "status": impact_status,
                "recent_impacts": recent_impacts
            }
            
        except Exception as e:
            logger.error(f"Error getting business impact overview: {e}")
            return {"error": str(e)}

    async def _get_threat_intelligence_overview(self) -> Dict[str, Any]:
        """Gets threat intelligence overview."""
        try:
            # Get threat intelligence status
            ti_status = await self.threat_intelligence.get_threat_intelligence_status()
            
            # Get recent IOC correlations (simulated)
            recent_correlations = {
                "total_correlations": 150,
                "high_confidence": 45,
                "medium_confidence": 60,
                "low_confidence": 45,
                "threat_indicators": 25
            }
            
            return {
                "status": ti_status,
                "recent_correlations": recent_correlations
            }
            
        except Exception as e:
            logger.error(f"Error getting threat intelligence overview: {e}")
            return {"error": str(e)}

    async def _generate_dashboard_recommendations(self) -> List[str]:
        """Generates dashboard recommendations."""
        recommendations = []
        
        # General recommendations
        recommendations.append("Review high-priority threat hunting hypotheses")
        recommendations.append("Monitor critical vulnerabilities for exploitation")
        recommendations.append("Update threat intelligence feeds regularly")
        recommendations.append("Conduct regular security awareness training")
        recommendations.append("Implement continuous security monitoring")
        
        return recommendations

    def _is_within_time_window(self, timestamp_str: str, start_time: datetime, end_time: datetime) -> bool:
        """Checks if a timestamp is within the specified time window."""
        try:
            if not timestamp_str:
                return False
            
            timestamp = datetime.fromisoformat(timestamp_str)
            return start_time <= timestamp <= end_time
        except (ValueError, TypeError):
            return False

    async def _calculate_trend(self, data: List[Dict[str, Any]], granularity: str) -> Dict[str, Any]:
        """Calculates trend data for the given granularity."""
        if not data:
            return {"trend": "stable", "change_percent": 0.0}
        
        # Group data by time period
        time_groups = {}
        for item in data:
            timestamp_str = item.get("timestamp", "")
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if granularity == "hourly":
                    key = timestamp.strftime("%Y-%m-%d %H:00")
                elif granularity == "daily":
                    key = timestamp.strftime("%Y-%m-%d")
                else:
                    key = timestamp.strftime("%Y-%m-%d %H:00")
                
                time_groups[key] = time_groups.get(key, 0) + 1
            except (ValueError, TypeError):
                continue
        
        if len(time_groups) < 2:
            return {"trend": "stable", "change_percent": 0.0}
        
        # Calculate trend
        sorted_groups = sorted(time_groups.items())
        first_half = sum(count for _, count in sorted_groups[:len(sorted_groups)//2])
        second_half = sum(count for _, count in sorted_groups[len(sorted_groups)//2:])
        
        if first_half == 0:
            change_percent = 100.0 if second_half > 0 else 0.0
        else:
            change_percent = ((second_half - first_half) / first_half) * 100
        
        if change_percent > 10:
            trend = "increasing"
        elif change_percent < -10:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_percent": round(change_percent, 2)
        }

    def _calculate_overall_threat_level(self, alerts: List[Dict[str, Any]], incidents: List[Dict[str, Any]]) -> str:
        """Calculates overall threat level."""
        if not alerts and not incidents:
            return "Low"
        
        # Calculate threat score based on alerts and incidents
        threat_score = 0.0
        
        # Alert-based scoring
        for alert in alerts:
            severity = alert.get("severity", "LOW")
            if severity == "CRITICAL":
                threat_score += 4
            elif severity == "HIGH":
                threat_score += 3
            elif severity == "MEDIUM":
                threat_score += 2
            else:
                threat_score += 1
        
        # Incident-based scoring
        for incident in incidents:
            severity = incident.get("severity", "LOW")
            if severity == "CRITICAL":
                threat_score += 8
            elif severity == "HIGH":
                threat_score += 6
            elif severity == "MEDIUM":
                threat_score += 4
            else:
                threat_score += 2
        
        # Normalize score
        total_items = len(alerts) + len(incidents)
        if total_items > 0:
            normalized_score = threat_score / (total_items * 4)  # Max possible score per item
        else:
            normalized_score = 0.0
        
        # Determine threat level
        if normalized_score >= 0.8:
            return "Critical"
        elif normalized_score >= 0.6:
            return "High"
        elif normalized_score >= 0.4:
            return "Medium"
        else:
            return "Low"

    async def _calculate_mttd(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculates Mean Time to Detection (MTTD)."""
        if not alerts:
            return 0.0
        
        # This would typically calculate actual MTTD
        # For now, return a simulated value
        return 15.5  # minutes

    async def _calculate_mttr(self, incidents: List[Dict[str, Any]]) -> float:
        """Calculates Mean Time to Response (MTTR)."""
        if not incidents:
            return 0.0
        
        # This would typically calculate actual MTTR
        # For now, return a simulated value
        return 120.0  # minutes

    async def _calculate_false_positive_rate(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculates false positive rate."""
        if not alerts:
            return 0.0
        
        # This would typically calculate actual false positive rate
        # For now, return a simulated value
        return 0.15  # 15%

    async def _calculate_resolution_rate(self, incidents: List[Dict[str, Any]]) -> float:
        """Calculates incident resolution rate."""
        if not incidents:
            return 0.0
        
        resolved = len([i for i in incidents if i.get("status") == "resolved"])
        return resolved / len(incidents)

    async def _calculate_detection_accuracy(self, alerts: List[Dict[str, Any]]) -> float:
        """Calculates threat detection accuracy."""
        if not alerts:
            return 0.0
        
        # This would typically calculate actual detection accuracy
        # For now, return a simulated value
        return 0.85  # 85%

    async def _calculate_operations_efficiency(self, 
                                             alerts: List[Dict[str, Any]], 
                                             incidents: List[Dict[str, Any]]) -> float:
        """Calculates security operations efficiency."""
        if not alerts and not incidents:
            return 0.0
        
        # This would typically calculate actual operations efficiency
        # For now, return a simulated value
        return 0.75  # 75%

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Checks if cache entry is valid."""
        if cache_key not in self.dashboard_cache:
            return False
        
        cached_at = self.dashboard_cache[cache_key].get("cached_at")
        if not cached_at:
            return False
        
        try:
            cached_time = datetime.fromisoformat(cached_at)
            return (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl
        except (ValueError, TypeError):
            return False

    async def get_dashboard_status(self) -> Dict[str, Any]:
        """Gets the current status of the analytics dashboard."""
        return {
            "cache_size": len(self.dashboard_cache),
            "cache_ttl": self.cache_ttl,
            "components": {
                "threat_hunting": await self.threat_hunter.get_hunting_status(),
                "attack_attribution": await self.attack_attributor.get_attribution_status(),
                "vulnerability_correlation": await self.vulnerability_correlator.get_correlation_status(),
                "business_impact": await self.business_impact_analyzer.get_business_impact_status(),
                "threat_intelligence": await self.threat_intelligence.get_threat_intelligence_status()
            },
            "last_updated": datetime.utcnow().isoformat()
        }
