"""AI-powered risk assessment for SOC Agent."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class AIRiskAssessor:
    """AI-powered risk assessment engine."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.risk_factors = self._load_risk_factors()
        self.impact_weights = self._load_impact_weights()
    
    async def assess_risk(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive AI risk assessment."""
        try:
            # Get AI risk assessment
            ai_assessment = await self.llm_client.assess_risk(threat_data)
            
            # Calculate quantitative risk score
            quantitative_score = self._calculate_quantitative_risk(threat_data)
            
            # Assess business impact
            business_impact = self._assess_business_impact(threat_data)
            
            # Combine assessments
            combined_assessment = self._combine_assessments(
                ai_assessment, quantitative_score, business_impact
            )
            
            return combined_assessment
            
        except Exception as e:
            logger.error(f"AI risk assessment failed: {e}")
            return self._get_fallback_assessment(threat_data)
    
    async def assess_portfolio_risk(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall portfolio risk from multiple threats."""
        try:
            # Assess each threat individually
            individual_assessments = []
            for threat in threats:
                assessment = await self.assess_risk(threat)
                individual_assessments.append(assessment)
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(individual_assessments)
            
            # Identify risk clusters
            risk_clusters = self._identify_risk_clusters(individual_assessments)
            
            # Generate portfolio recommendations
            recommendations = self._generate_portfolio_recommendations(
                portfolio_metrics, risk_clusters
            )
            
            return {
                "portfolio_risk_score": portfolio_metrics["overall_risk"],
                "risk_level": portfolio_metrics["risk_level"],
                "individual_assessments": individual_assessments,
                "risk_clusters": risk_clusters,
                "recommendations": recommendations,
                "metrics": portfolio_metrics
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk assessment failed: {e}")
            return {"portfolio_risk_score": 50, "risk_level": "MEDIUM", "error": str(e)}
    
    def _load_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Load risk factors and their weights."""
        return {
            "threat_severity": {
                "weights": {"LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 10},
                "description": "Severity of the threat"
            },
            "asset_criticality": {
                "weights": {"LOW": 1, "MEDIUM": 2, "HIGH": 5, "CRITICAL": 10},
                "description": "Criticality of affected assets"
            },
            "vulnerability_exploitability": {
                "weights": {"LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 10},
                "description": "Ease of exploiting the vulnerability"
            },
            "business_impact": {
                "weights": {"LOW": 1, "MEDIUM": 3, "HIGH": 7, "CRITICAL": 10},
                "description": "Potential business impact"
            },
            "detection_difficulty": {
                "weights": {"LOW": 10, "MEDIUM": 7, "HIGH": 3, "CRITICAL": 1},
                "description": "Difficulty of detecting the threat"
            }
        }
    
    def _load_impact_weights(self) -> Dict[str, float]:
        """Load impact category weights."""
        return {
            "confidentiality": 0.4,  # Data breach impact
            "integrity": 0.3,        # Data corruption impact
            "availability": 0.3      # Service disruption impact
        }
    
    def _calculate_quantitative_risk(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quantitative risk score."""
        risk_score = 0
        risk_factors = {}
        
        # Calculate each risk factor
        for factor, config in self.risk_factors.items():
            value = threat_data.get(factor, "MEDIUM")
            weight = config["weights"].get(value, 5)
            risk_factors[factor] = {
                "value": value,
                "weight": weight,
                "description": config["description"]
            }
            risk_score += weight
        
        # Normalize to 0-100 scale
        max_possible = sum(max(config["weights"].values()) for config in self.risk_factors.values())
        normalized_score = (risk_score / max_possible) * 100
        
        return {
            "risk_score": round(normalized_score, 2),
            "risk_factors": risk_factors,
            "calculation_method": "weighted_sum"
        }
    
    def _assess_business_impact(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business impact of the threat."""
        impact_scores = {}
        total_impact = 0
        
        # Assess each impact category
        for category, weight in self.impact_weights.items():
            impact_level = threat_data.get(f"{category}_impact", "MEDIUM")
            impact_score = self._get_impact_score(impact_level)
            impact_scores[category] = {
                "level": impact_level,
                "score": impact_score,
                "weighted_score": impact_score * weight
            }
            total_impact += impact_score * weight
        
        # Determine overall impact level
        if total_impact >= 8:
            impact_level = "CRITICAL"
        elif total_impact >= 6:
            impact_level = "HIGH"
        elif total_impact >= 4:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"
        
        return {
            "overall_impact": impact_level,
            "impact_score": round(total_impact, 2),
            "category_scores": impact_scores,
            "business_continuity_risk": self._assess_business_continuity_risk(total_impact)
        }
    
    def _get_impact_score(self, impact_level: str) -> int:
        """Get numeric score for impact level."""
        scores = {"LOW": 2, "MEDIUM": 5, "HIGH": 8, "CRITICAL": 10}
        return scores.get(impact_level.upper(), 5)
    
    def _assess_business_continuity_risk(self, impact_score: float) -> str:
        """Assess business continuity risk."""
        if impact_score >= 8:
            return "HIGH - Potential service disruption"
        elif impact_score >= 6:
            return "MEDIUM - Limited service impact"
        elif impact_score >= 4:
            return "LOW - Minimal service impact"
        else:
            return "VERY_LOW - No service impact"
    
    def _combine_assessments(
        self, 
        ai_assessment: Dict[str, Any], 
        quantitative_score: Dict[str, Any], 
        business_impact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine all assessment components."""
        # Calculate weighted average of risk scores
        ai_score = ai_assessment.get("risk_score", 50)
        quant_score = quantitative_score.get("risk_score", 50)
        
        # Weight AI assessment more heavily
        combined_score = (ai_score * 0.6) + (quant_score * 0.4)
        
        # Determine risk level
        if combined_score >= 80:
            risk_level = "CRITICAL"
        elif combined_score >= 60:
            risk_level = "HIGH"
        elif combined_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "overall_risk_score": round(combined_score, 2),
            "risk_level": risk_level,
            "ai_assessment": ai_assessment,
            "quantitative_assessment": quantitative_score,
            "business_impact": business_impact,
            "confidence": self._calculate_assessment_confidence(ai_assessment, quantitative_score),
            "recommendations": self._generate_risk_recommendations(risk_level, business_impact)
        }
    
    def _calculate_assessment_confidence(
        self, 
        ai_assessment: Dict[str, Any], 
        quantitative_score: Dict[str, Any]
    ) -> int:
        """Calculate confidence in the risk assessment."""
        # Base confidence on consistency between AI and quantitative scores
        ai_score = ai_assessment.get("risk_score", 50)
        quant_score = quantitative_score.get("risk_score", 50)
        
        # Calculate difference
        score_diff = abs(ai_score - quant_score)
        
        # Higher confidence for smaller differences
        if score_diff <= 10:
            return 90
        elif score_diff <= 20:
            return 75
        elif score_diff <= 30:
            return 60
        else:
            return 45
    
    def _generate_risk_recommendations(
        self, 
        risk_level: str, 
        business_impact: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate risk-based recommendations."""
        recommendations = []
        
        if risk_level == "CRITICAL":
            recommendations.extend([
                {
                    "priority": "IMMEDIATE",
                    "action": "Isolate affected systems",
                    "description": "Immediately isolate systems to prevent further compromise"
                },
                {
                    "priority": "IMMEDIATE",
                    "action": "Activate incident response team",
                    "description": "Engage full incident response team"
                },
                {
                    "priority": "HIGH",
                    "action": "Notify stakeholders",
                    "description": "Notify executive team and relevant stakeholders"
                }
            ])
        elif risk_level == "HIGH":
            recommendations.extend([
                {
                    "priority": "HIGH",
                    "action": "Implement additional monitoring",
                    "description": "Increase monitoring and alerting for affected systems"
                },
                {
                    "priority": "HIGH",
                    "action": "Review access controls",
                    "description": "Review and tighten access controls"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Update security policies",
                    "description": "Review and update security policies as needed"
                }
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                {
                    "priority": "MEDIUM",
                    "action": "Monitor closely",
                    "description": "Monitor the situation closely for escalation"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Document findings",
                    "description": "Document findings and lessons learned"
                }
            ])
        else:
            recommendations.append({
                "priority": "LOW",
                "action": "Continue monitoring",
                "description": "Continue normal monitoring procedures"
            })
        
        return recommendations
    
    def _calculate_portfolio_metrics(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics."""
        if not assessments:
            return {"overall_risk": 0, "risk_level": "LOW"}
        
        # Calculate average risk score
        risk_scores = [a.get("overall_risk_score", 0) for a in assessments]
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        # Calculate risk distribution
        risk_levels = [a.get("risk_level", "LOW") for a in assessments]
        risk_distribution = {}
        for level in risk_levels:
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        # Determine overall portfolio risk level
        if avg_risk >= 80:
            portfolio_level = "CRITICAL"
        elif avg_risk >= 60:
            portfolio_level = "HIGH"
        elif avg_risk >= 40:
            portfolio_level = "MEDIUM"
        else:
            portfolio_level = "LOW"
        
        return {
            "overall_risk": round(avg_risk, 2),
            "risk_level": portfolio_level,
            "risk_distribution": risk_distribution,
            "threat_count": len(assessments),
            "high_risk_count": len([a for a in assessments if a.get("risk_level") in ["HIGH", "CRITICAL"]])
        }
    
    def _identify_risk_clusters(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify clusters of related risks."""
        clusters = []
        
        # Group by threat categories
        category_groups = {}
        for i, assessment in enumerate(assessments):
            categories = assessment.get("ai_assessment", {}).get("threat_categories", [])
            for category in categories:
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(i)
        
        # Create clusters
        for category, indices in category_groups.items():
            if len(indices) > 1:
                cluster_risks = [assessments[i] for i in indices]
                avg_risk = sum(r.get("overall_risk_score", 0) for r in cluster_risks) / len(cluster_risks)
                
                clusters.append({
                    "category": category,
                    "threat_count": len(indices),
                    "average_risk": round(avg_risk, 2),
                    "threat_indices": indices,
                    "description": f"Multiple {category} threats detected"
                })
        
        return clusters
    
    def _generate_portfolio_recommendations(
        self, 
        metrics: Dict[str, Any], 
        clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate portfolio-level recommendations."""
        recommendations = []
        
        # High-level portfolio recommendations
        if metrics["risk_level"] in ["HIGH", "CRITICAL"]:
            recommendations.append({
                "priority": "HIGH",
                "action": "Portfolio-wide security review",
                "description": "Conduct comprehensive security review of all systems"
            })
        
        # Cluster-specific recommendations
        for cluster in clusters:
            if cluster["average_risk"] >= 70:
                recommendations.append({
                    "priority": "HIGH",
                    "action": f"Address {cluster['category']} threats",
                    "description": f"Focus on {cluster['category']} threat category with {cluster['threat_count']} active threats"
                })
        
        # Resource allocation recommendations
        if metrics["high_risk_count"] > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Increase security resources",
                "description": f"Consider increasing security team resources for {metrics['high_risk_count']} high-risk threats"
            })
        
        return recommendations
    
    def _get_fallback_assessment(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback assessment when AI fails."""
        return {
            "overall_risk_score": 50,
            "risk_level": "MEDIUM",
            "ai_assessment": {"risk_score": 50, "risk_level": "MEDIUM"},
            "quantitative_assessment": {"risk_score": 50, "risk_factors": {}},
            "business_impact": {"overall_impact": "MEDIUM", "impact_score": 5},
            "confidence": 30,
            "recommendations": [{"priority": "LOW", "action": "Manual review required", "description": "AI assessment failed, manual review needed"}]
        }
