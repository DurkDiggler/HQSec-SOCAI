"""Business impact analysis with asset criticality scoring."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents

logger = logging.getLogger(__name__)

class BusinessImpactAnalyzer:
    """
    Business impact analysis system that calculates asset criticality,
    business impact scores, and risk assessments.
    """

    def __init__(self):
        self.asset_criticality_factors = self._load_asset_criticality_factors()
        self.business_functions = self._load_business_functions()
        self.impact_categories = self._load_impact_categories()
        self.risk_tolerance_levels = self._load_risk_tolerance_levels()

    def _load_asset_criticality_factors(self) -> Dict[str, Dict[str, float]]:
        """Loads asset criticality scoring factors."""
        return {
            "business_function": {
                "customer_facing": 1.0,
                "internal_operations": 0.8,
                "supporting": 0.6,
                "development": 0.4,
                "testing": 0.2
            },
            "data_classification": {
                "public": 0.2,
                "internal": 0.4,
                "confidential": 0.7,
                "restricted": 1.0
            },
            "availability_requirements": {
                "24x7": 1.0,
                "business_hours": 0.8,
                "extended_hours": 0.6,
                "standard_hours": 0.4,
                "on_demand": 0.2
            },
            "recovery_time_objective": {
                "immediate": 1.0,
                "1_hour": 0.9,
                "4_hours": 0.8,
                "24_hours": 0.6,
                "72_hours": 0.4,
                "1_week": 0.2
            },
            "recovery_point_objective": {
                "zero_data_loss": 1.0,
                "1_hour": 0.9,
                "4_hours": 0.8,
                "24_hours": 0.6,
                "72_hours": 0.4,
                "1_week": 0.2
            },
            "regulatory_compliance": {
                "pci_dss": 1.0,
                "hipaa": 0.9,
                "sox": 0.8,
                "gdpr": 0.9,
                "iso27001": 0.7,
                "none": 0.0
            },
            "financial_impact": {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4,
                "minimal": 0.2
            }
        }

    def _load_business_functions(self) -> Dict[str, Dict[str, Any]]:
        """Loads business function definitions and dependencies."""
        return {
            "customer_portal": {
                "name": "Customer Portal",
                "description": "Web-based customer self-service portal",
                "dependencies": ["web_server", "database", "authentication_service"],
                "business_value": "High",
                "revenue_impact": "Direct",
                "customer_impact": "High",
                "regulatory_requirements": ["PCI-DSS"],
                "sla_requirements": {
                    "availability": "99.9%",
                    "response_time": "2 seconds",
                    "uptime": "24x7"
                }
            },
            "payment_processing": {
                "name": "Payment Processing",
                "description": "Credit card and payment processing system",
                "dependencies": ["payment_gateway", "database", "encryption_service"],
                "business_value": "Critical",
                "revenue_impact": "Direct",
                "customer_impact": "Critical",
                "regulatory_requirements": ["PCI-DSS", "SOX"],
                "sla_requirements": {
                    "availability": "99.99%",
                    "response_time": "1 second",
                    "uptime": "24x7"
                }
            },
            "inventory_management": {
                "name": "Inventory Management",
                "description": "Warehouse and inventory tracking system",
                "dependencies": ["database", "barcode_scanner", "rfid_system"],
                "business_value": "High",
                "revenue_impact": "Indirect",
                "customer_impact": "Medium",
                "regulatory_requirements": ["SOX"],
                "sla_requirements": {
                    "availability": "99.5%",
                    "response_time": "5 seconds",
                    "uptime": "Business Hours"
                }
            },
            "hr_system": {
                "name": "Human Resources System",
                "description": "Employee management and payroll system",
                "dependencies": ["database", "ldap", "email_system"],
                "business_value": "Medium",
                "revenue_impact": "Indirect",
                "customer_impact": "Low",
                "regulatory_requirements": ["HIPAA", "SOX"],
                "sla_requirements": {
                    "availability": "99.0%",
                    "response_time": "10 seconds",
                    "uptime": "Business Hours"
                }
            },
            "development_environment": {
                "name": "Development Environment",
                "description": "Software development and testing environment",
                "dependencies": ["version_control", "build_server", "test_database"],
                "business_value": "Low",
                "revenue_impact": "Indirect",
                "customer_impact": "None",
                "regulatory_requirements": [],
                "sla_requirements": {
                    "availability": "95.0%",
                    "response_time": "30 seconds",
                    "uptime": "Business Hours"
                }
            }
        }

    def _load_impact_categories(self) -> Dict[str, Dict[str, Any]]:
        """Loads business impact categories and scoring."""
        return {
            "financial": {
                "name": "Financial Impact",
                "description": "Direct and indirect financial losses",
                "factors": [
                    "revenue_loss",
                    "remediation_costs",
                    "regulatory_fines",
                    "reputation_damage",
                    "customer_compensation"
                ],
                "scoring": {
                    "critical": {"min": 1000000, "max": float('inf')},
                    "high": {"min": 100000, "max": 999999},
                    "medium": {"min": 10000, "max": 99999},
                    "low": {"min": 1000, "max": 9999},
                    "minimal": {"min": 0, "max": 999}
                }
            },
            "operational": {
                "name": "Operational Impact",
                "description": "Impact on business operations and processes",
                "factors": [
                    "service_disruption",
                    "productivity_loss",
                    "process_interruption",
                    "resource_redirection",
                    "recovery_time"
                ],
                "scoring": {
                    "critical": {"min": 0.9, "max": 1.0},
                    "high": {"min": 0.7, "max": 0.89},
                    "medium": {"min": 0.5, "max": 0.69},
                    "low": {"min": 0.3, "max": 0.49},
                    "minimal": {"min": 0.0, "max": 0.29}
                }
            },
            "reputational": {
                "name": "Reputational Impact",
                "description": "Impact on brand reputation and customer trust",
                "factors": [
                    "public_disclosure",
                    "media_coverage",
                    "customer_trust",
                    "brand_damage",
                    "market_position"
                ],
                "scoring": {
                    "critical": {"min": 0.9, "max": 1.0},
                    "high": {"min": 0.7, "max": 0.89},
                    "medium": {"min": 0.5, "max": 0.69},
                    "low": {"min": 0.3, "max": 0.49},
                    "minimal": {"min": 0.0, "max": 0.29}
                }
            },
            "regulatory": {
                "name": "Regulatory Impact",
                "description": "Impact on regulatory compliance and legal obligations",
                "factors": [
                    "compliance_violations",
                    "regulatory_fines",
                    "audit_findings",
                    "legal_liability",
                    "reporting_requirements"
                ],
                "scoring": {
                    "critical": {"min": 0.9, "max": 1.0},
                    "high": {"min": 0.7, "max": 0.89},
                    "medium": {"min": 0.5, "max": 0.69},
                    "low": {"min": 0.3, "max": 0.49},
                    "minimal": {"min": 0.0, "max": 0.29}
                }
            }
        }

    def _load_risk_tolerance_levels(self) -> Dict[str, Dict[str, Any]]:
        """Loads risk tolerance levels for different business functions."""
        return {
            "critical": {
                "name": "Critical Risk Tolerance",
                "description": "Zero tolerance for risk",
                "max_acceptable_risk": 0.1,
                "response_time": "Immediate",
                "approval_required": "C-Level"
            },
            "high": {
                "name": "High Risk Tolerance",
                "description": "Very low tolerance for risk",
                "max_acceptable_risk": 0.3,
                "response_time": "4 hours",
                "approval_required": "VP Level"
            },
            "medium": {
                "name": "Medium Risk Tolerance",
                "description": "Moderate tolerance for risk",
                "max_acceptable_risk": 0.5,
                "response_time": "24 hours",
                "approval_required": "Director Level"
            },
            "low": {
                "name": "Low Risk Tolerance",
                "description": "Higher tolerance for risk",
                "max_acceptable_risk": 0.7,
                "response_time": "72 hours",
                "approval_required": "Manager Level"
            }
        }

    async def analyze_business_impact(self, 
                                    incident_data: Dict[str, Any],
                                    asset_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyzes business impact of a security incident.
        
        Args:
            incident_data: Security incident data
            asset_data: Affected asset data
            
        Returns:
            Business impact analysis results
        """
        try:
            logger.info("Starting business impact analysis")
            
            # Calculate asset criticality
            asset_criticality = await self._calculate_asset_criticality(asset_data or {})
            
            # Calculate business impact scores
            impact_scores = await self._calculate_impact_scores(incident_data, asset_data or {})
            
            # Calculate financial impact
            financial_impact = await self._calculate_financial_impact(incident_data, asset_criticality)
            
            # Calculate operational impact
            operational_impact = await self._calculate_operational_impact(incident_data, asset_criticality)
            
            # Calculate reputational impact
            reputational_impact = await self._calculate_reputational_impact(incident_data, asset_criticality)
            
            # Calculate regulatory impact
            regulatory_impact = await self._calculate_regulatory_impact(incident_data, asset_criticality)
            
            # Calculate overall business impact score
            overall_impact = await self._calculate_overall_impact(
                financial_impact, operational_impact, reputational_impact, regulatory_impact
            )
            
            # Generate recommendations
            recommendations = await self._generate_business_impact_recommendations(
                overall_impact, asset_criticality, impact_scores
            )
            
            # Generate impact report
            impact_report = {
                "incident_id": incident_data.get("id", "unknown"),
                "analysis_time": datetime.utcnow().isoformat(),
                "asset_criticality": asset_criticality,
                "impact_scores": impact_scores,
                "financial_impact": financial_impact,
                "operational_impact": operational_impact,
                "reputational_impact": reputational_impact,
                "regulatory_impact": regulatory_impact,
                "overall_impact": overall_impact,
                "recommendations": recommendations,
                "risk_tolerance": await self._assess_risk_tolerance(overall_impact["score"]),
                "escalation_required": overall_impact["score"] > 0.7
            }
            
            logger.info(f"Business impact analysis completed: {overall_impact['level']} impact")
            return impact_report
            
        except Exception as e:
            logger.error(f"Error in business impact analysis: {e}")
            return {
                "error": str(e),
                "analysis_time": datetime.utcnow().isoformat()
            }

    async def _calculate_asset_criticality(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates asset criticality score."""
        if not asset_data:
            return {"score": 0.0, "level": "Unknown", "factors": {}}
        
        factors = self.asset_criticality_factors
        criticality_score = 0.0
        factor_scores = {}
        
        # Business function factor
        business_function = asset_data.get("business_function", "supporting")
        business_function_score = factors["business_function"].get(business_function, 0.5)
        criticality_score += business_function_score * 0.25
        factor_scores["business_function"] = business_function_score
        
        # Data classification factor
        data_classification = asset_data.get("data_classification", "internal")
        data_classification_score = factors["data_classification"].get(data_classification, 0.5)
        criticality_score += data_classification_score * 0.20
        factor_scores["data_classification"] = data_classification_score
        
        # Availability requirements factor
        availability_requirements = asset_data.get("availability_requirements", "standard_hours")
        availability_score = factors["availability_requirements"].get(availability_requirements, 0.5)
        criticality_score += availability_score * 0.20
        factor_scores["availability_requirements"] = availability_score
        
        # Recovery time objective factor
        rto = asset_data.get("recovery_time_objective", "24_hours")
        rto_score = factors["recovery_time_objective"].get(rto, 0.5)
        criticality_score += rto_score * 0.15
        factor_scores["recovery_time_objective"] = rto_score
        
        # Recovery point objective factor
        rpo = asset_data.get("recovery_point_objective", "24_hours")
        rpo_score = factors["recovery_point_objective"].get(rpo, 0.5)
        criticality_score += rpo_score * 0.10
        factor_scores["recovery_point_objective"] = rpo_score
        
        # Regulatory compliance factor
        regulatory_compliance = asset_data.get("regulatory_compliance", "none")
        regulatory_score = factors["regulatory_compliance"].get(regulatory_compliance, 0.0)
        criticality_score += regulatory_score * 0.10
        factor_scores["regulatory_compliance"] = regulatory_score
        
        # Determine criticality level
        if criticality_score >= 0.8:
            level = "Critical"
        elif criticality_score >= 0.6:
            level = "High"
        elif criticality_score >= 0.4:
            level = "Medium"
        elif criticality_score >= 0.2:
            level = "Low"
        else:
            level = "Minimal"
        
        return {
            "score": criticality_score,
            "level": level,
            "factors": factor_scores
        }

    async def _calculate_impact_scores(self, 
                                     incident_data: Dict[str, Any], 
                                     asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates impact scores for different categories."""
        impact_scores = {}
        
        # Financial impact score
        financial_score = await self._calculate_financial_impact_score(incident_data, asset_data)
        impact_scores["financial"] = financial_score
        
        # Operational impact score
        operational_score = await self._calculate_operational_impact_score(incident_data, asset_data)
        impact_scores["operational"] = operational_score
        
        # Reputational impact score
        reputational_score = await self._calculate_reputational_impact_score(incident_data, asset_data)
        impact_scores["reputational"] = reputational_score
        
        # Regulatory impact score
        regulatory_score = await self._calculate_regulatory_impact_score(incident_data, asset_data)
        impact_scores["regulatory"] = regulatory_score
        
        return impact_scores

    async def _calculate_financial_impact(self, 
                                        incident_data: Dict[str, Any], 
                                        asset_criticality: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates financial impact of the incident."""
        # Base financial impact from incident data
        base_financial_impact = incident_data.get("financial_impact", 0)
        
        # Calculate impact based on asset criticality
        criticality_multiplier = asset_criticality.get("score", 0.5)
        
        # Calculate potential revenue loss
        revenue_loss = base_financial_impact * criticality_multiplier
        
        # Calculate remediation costs
        remediation_costs = base_financial_impact * 0.3  # Assume 30% of base impact
        
        # Calculate regulatory fines (if applicable)
        regulatory_fines = 0
        if asset_criticality.get("factors", {}).get("regulatory_compliance", 0) > 0.5:
            regulatory_fines = base_financial_impact * 0.1  # Assume 10% of base impact
        
        # Calculate total financial impact
        total_financial_impact = revenue_loss + remediation_costs + regulatory_fines
        
        # Determine impact level
        impact_level = self._determine_impact_level(total_financial_impact, "financial")
        
        return {
            "revenue_loss": revenue_loss,
            "remediation_costs": remediation_costs,
            "regulatory_fines": regulatory_fines,
            "total_impact": total_financial_impact,
            "level": impact_level,
            "currency": "USD"
        }

    async def _calculate_operational_impact(self, 
                                          incident_data: Dict[str, Any], 
                                          asset_criticality: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates operational impact of the incident."""
        # Base operational impact from incident data
        base_operational_impact = incident_data.get("operational_impact", 0.5)
        
        # Calculate impact based on asset criticality
        criticality_multiplier = asset_criticality.get("score", 0.5)
        
        # Calculate service disruption
        service_disruption = base_operational_impact * criticality_multiplier
        
        # Calculate productivity loss
        productivity_loss = base_operational_impact * 0.8
        
        # Calculate process interruption
        process_interruption = base_operational_impact * 0.6
        
        # Calculate recovery time impact
        recovery_time = incident_data.get("recovery_time_hours", 24)
        recovery_time_impact = min(recovery_time / 168, 1.0)  # Normalize to 1 week
        
        # Calculate overall operational impact
        overall_operational_impact = (
            service_disruption * 0.4 +
            productivity_loss * 0.3 +
            process_interruption * 0.2 +
            recovery_time_impact * 0.1
        )
        
        # Determine impact level
        impact_level = self._determine_impact_level(overall_operational_impact, "operational")
        
        return {
            "service_disruption": service_disruption,
            "productivity_loss": productivity_loss,
            "process_interruption": process_interruption,
            "recovery_time_impact": recovery_time_impact,
            "overall_impact": overall_operational_impact,
            "level": impact_level
        }

    async def _calculate_reputational_impact(self, 
                                           incident_data: Dict[str, Any], 
                                           asset_criticality: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates reputational impact of the incident."""
        # Base reputational impact from incident data
        base_reputational_impact = incident_data.get("reputational_impact", 0.5)
        
        # Calculate impact based on asset criticality
        criticality_multiplier = asset_criticality.get("score", 0.5)
        
        # Calculate public disclosure impact
        public_disclosure = incident_data.get("public_disclosure", False)
        public_disclosure_impact = 0.8 if public_disclosure else 0.2
        
        # Calculate media coverage impact
        media_coverage = incident_data.get("media_coverage", False)
        media_coverage_impact = 0.9 if media_coverage else 0.1
        
        # Calculate customer trust impact
        customer_trust_impact = base_reputational_impact * criticality_multiplier
        
        # Calculate brand damage impact
        brand_damage_impact = base_reputational_impact * 0.7
        
        # Calculate overall reputational impact
        overall_reputational_impact = (
            public_disclosure_impact * 0.3 +
            media_coverage_impact * 0.3 +
            customer_trust_impact * 0.2 +
            brand_damage_impact * 0.2
        )
        
        # Determine impact level
        impact_level = self._determine_impact_level(overall_reputational_impact, "reputational")
        
        return {
            "public_disclosure_impact": public_disclosure_impact,
            "media_coverage_impact": media_coverage_impact,
            "customer_trust_impact": customer_trust_impact,
            "brand_damage_impact": brand_damage_impact,
            "overall_impact": overall_reputational_impact,
            "level": impact_level
        }

    async def _calculate_regulatory_impact(self, 
                                         incident_data: Dict[str, Any], 
                                         asset_criticality: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates regulatory impact of the incident."""
        # Base regulatory impact from incident data
        base_regulatory_impact = incident_data.get("regulatory_impact", 0.5)
        
        # Calculate impact based on asset criticality
        criticality_multiplier = asset_criticality.get("score", 0.5)
        
        # Calculate compliance violations
        compliance_violations = base_regulatory_impact * criticality_multiplier
        
        # Calculate regulatory fines
        regulatory_fines = base_regulatory_impact * 0.8
        
        # Calculate audit findings
        audit_findings = base_regulatory_impact * 0.6
        
        # Calculate legal liability
        legal_liability = base_regulatory_impact * 0.7
        
        # Calculate reporting requirements
        reporting_requirements = base_regulatory_impact * 0.5
        
        # Calculate overall regulatory impact
        overall_regulatory_impact = (
            compliance_violations * 0.3 +
            regulatory_fines * 0.25 +
            audit_findings * 0.2 +
            legal_liability * 0.15 +
            reporting_requirements * 0.1
        )
        
        # Determine impact level
        impact_level = self._determine_impact_level(overall_regulatory_impact, "regulatory")
        
        return {
            "compliance_violations": compliance_violations,
            "regulatory_fines": regulatory_fines,
            "audit_findings": audit_findings,
            "legal_liability": legal_liability,
            "reporting_requirements": reporting_requirements,
            "overall_impact": overall_regulatory_impact,
            "level": impact_level
        }

    async def _calculate_overall_impact(self, 
                                      financial_impact: Dict[str, Any],
                                      operational_impact: Dict[str, Any],
                                      reputational_impact: Dict[str, Any],
                                      regulatory_impact: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates overall business impact score."""
        # Weighted average of impact scores
        weights = {
            "financial": 0.4,
            "operational": 0.3,
            "reputational": 0.2,
            "regulatory": 0.1
        }
        
        overall_score = (
            financial_impact["overall_impact"] * weights["financial"] +
            operational_impact["overall_impact"] * weights["operational"] +
            reputational_impact["overall_impact"] * weights["reputational"] +
            regulatory_impact["overall_impact"] * weights["regulatory"]
        )
        
        # Determine overall impact level
        if overall_score >= 0.8:
            level = "Critical"
        elif overall_score >= 0.6:
            level = "High"
        elif overall_score >= 0.4:
            level = "Medium"
        elif overall_score >= 0.2:
            level = "Low"
        else:
            level = "Minimal"
        
        return {
            "score": overall_score,
            "level": level,
            "weights": weights
        }

    def _determine_impact_level(self, score: float, category: str) -> str:
        """Determines impact level based on score and category."""
        if category == "financial":
            if score >= 1000000:
                return "Critical"
            elif score >= 100000:
                return "High"
            elif score >= 10000:
                return "Medium"
            elif score >= 1000:
                return "Low"
            else:
                return "Minimal"
        else:
            if score >= 0.8:
                return "Critical"
            elif score >= 0.6:
                return "High"
            elif score >= 0.4:
                return "Medium"
            elif score >= 0.2:
                return "Low"
            else:
                return "Minimal"

    async def _assess_risk_tolerance(self, impact_score: float) -> Dict[str, Any]:
        """Assesses risk tolerance based on impact score."""
        if impact_score >= 0.8:
            return self.risk_tolerance_levels["critical"]
        elif impact_score >= 0.6:
            return self.risk_tolerance_levels["high"]
        elif impact_score >= 0.4:
            return self.risk_tolerance_levels["medium"]
        else:
            return self.risk_tolerance_levels["low"]

    async def _generate_business_impact_recommendations(self, 
                                                      overall_impact: Dict[str, Any],
                                                      asset_criticality: Dict[str, Any],
                                                      impact_scores: Dict[str, Any]) -> List[str]:
        """Generates recommendations based on business impact analysis."""
        recommendations = []
        
        impact_level = overall_impact["level"]
        impact_score = overall_impact["score"]
        
        # General recommendations based on impact level
        if impact_level == "Critical":
            recommendations.append("Immediate escalation to C-Level executives required")
            recommendations.append("Activate crisis management team")
            recommendations.append("Implement emergency response procedures")
        elif impact_level == "High":
            recommendations.append("Escalate to VP level management")
            recommendations.append("Implement enhanced monitoring and response")
            recommendations.append("Consider business continuity measures")
        elif impact_level == "Medium":
            recommendations.append("Notify department heads and stakeholders")
            recommendations.append("Implement standard response procedures")
            recommendations.append("Monitor for escalation indicators")
        else:
            recommendations.append("Standard incident response procedures")
            recommendations.append("Document lessons learned")
            recommendations.append("Consider preventive measures")
        
        # Asset-specific recommendations
        if asset_criticality["level"] == "Critical":
            recommendations.append("Critical asset affected - prioritize recovery")
            recommendations.append("Implement additional security controls")
            recommendations.append("Consider redundancy and failover systems")
        
        # Category-specific recommendations
        if impact_scores["financial"]["level"] in ["Critical", "High"]:
            recommendations.append("Financial impact significant - involve finance team")
            recommendations.append("Consider insurance claims and legal consultation")
        
        if impact_scores["operational"]["level"] in ["Critical", "High"]:
            recommendations.append("Operational impact significant - involve operations team")
            recommendations.append("Implement business continuity measures")
        
        if impact_scores["reputational"]["level"] in ["Critical", "High"]:
            recommendations.append("Reputational impact significant - involve PR/communications team")
            recommendations.append("Prepare public statements and customer communications")
        
        if impact_scores["regulatory"]["level"] in ["Critical", "High"]:
            recommendations.append("Regulatory impact significant - involve legal and compliance teams")
            recommendations.append("Prepare regulatory notifications and reports")
        
        return recommendations

    async def get_business_impact_status(self) -> Dict[str, Any]:
        """Gets the current status of the business impact analysis system."""
        return {
            "asset_criticality_factors": len(self.asset_criticality_factors),
            "business_functions": len(self.business_functions),
            "impact_categories": len(self.impact_categories),
            "risk_tolerance_levels": len(self.risk_tolerance_levels),
            "last_updated": datetime.utcnow().isoformat()
        }
