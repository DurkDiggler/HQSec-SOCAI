"""LLM client for AI-powered threat analysis."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with Large Language Models."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=SETTINGS.openai_api_key)
        self.model = getattr(SETTINGS, 'openai_model', 'gpt-4')
        self.max_tokens = getattr(SETTINGS, 'openai_max_tokens', 2000)
        self.temperature = getattr(SETTINGS, 'openai_temperature', 0.1)
    
    async def analyze_threat(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze threat using AI."""
        try:
            prompt = self._build_threat_analysis_prompt(event_data)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert analyzing security events. Provide detailed threat analysis with confidence scores and recommendations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            return self._parse_ai_response(content)
            
        except Exception as e:
            logger.error(f"AI threat analysis failed: {e}")
            return self._get_fallback_analysis(event_data)
    
    async def generate_test_scenario(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate penetration testing scenario using AI."""
        try:
            prompt = self._build_test_scenario_prompt(target_info)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a penetration testing expert. Generate comprehensive test scenarios based on target information."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            return self._parse_test_scenario_response(content)
            
        except Exception as e:
            logger.error(f"AI test scenario generation failed: {e}")
            return self._get_fallback_test_scenario(target_info)
    
    async def assess_risk(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk using AI."""
        try:
            prompt = self._build_risk_assessment_prompt(threat_data)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a risk assessment expert. Analyze threats and provide risk scores with detailed explanations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            return self._parse_risk_response(content)
            
        except Exception as e:
            logger.error(f"AI risk assessment failed: {e}")
            return self._get_fallback_risk_assessment(threat_data)
    
    def _build_threat_analysis_prompt(self, event_data: Dict[str, Any]) -> str:
        """Build prompt for threat analysis."""
        return f"""
        Analyze this security event and provide detailed threat analysis:
        
        Event Data:
        - Source: {event_data.get('source', 'Unknown')}
        - Event Type: {event_data.get('event_type', 'Unknown')}
        - Severity: {event_data.get('severity', 'Unknown')}
        - Message: {event_data.get('message', 'No message')}
        - IP Address: {event_data.get('ip', 'Unknown')}
        - Username: {event_data.get('username', 'Unknown')}
        - Timestamp: {event_data.get('timestamp', 'Unknown')}
        
        Please provide:
        1. Threat classification (malware, intrusion, data breach, etc.)
        2. Confidence score (0-100)
        3. Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        4. Recommended immediate actions
        5. Potential attack vectors
        6. Indicators of compromise (IOCs)
        7. Mitigation strategies
        
        Respond in JSON format.
        """
    
    def _build_test_scenario_prompt(self, target_info: Dict[str, Any]) -> str:
        """Build prompt for test scenario generation."""
        return f"""
        Generate penetration testing scenarios for this target:
        
        Target Information:
        - IP Address: {target_info.get('ip', 'Unknown')}
        - Ports: {target_info.get('ports', 'Unknown')}
        - Services: {target_info.get('services', 'Unknown')}
        - OS: {target_info.get('os', 'Unknown')}
        - Vulnerabilities: {target_info.get('vulnerabilities', 'Unknown')}
        
        Please provide:
        1. Test objectives
        2. Attack vectors to test
        3. Tools and techniques to use
        4. Expected outcomes
        5. Risk assessment
        6. Authorization requirements
        
        Respond in JSON format.
        """
    
    def _build_risk_assessment_prompt(self, threat_data: Dict[str, Any]) -> str:
        """Build prompt for risk assessment."""
        return f"""
        Assess the risk of this threat:
        
        Threat Data:
        - Threat Type: {threat_data.get('threat_type', 'Unknown')}
        - Severity: {threat_data.get('severity', 'Unknown')}
        - Impact: {threat_data.get('impact', 'Unknown')}
        - Likelihood: {threat_data.get('likelihood', 'Unknown')}
        - Affected Assets: {threat_data.get('affected_assets', 'Unknown')}
        
        Please provide:
        1. Overall risk score (0-100)
        2. Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        3. Impact assessment
        4. Likelihood assessment
        5. Risk factors
        6. Mitigation priorities
        7. Business impact
        
        Respond in JSON format.
        """
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return {
                "threat_classification": "Unknown",
                "confidence_score": 50,
                "risk_level": "MEDIUM",
                "recommendations": [content],
                "attack_vectors": [],
                "iocs": [],
                "mitigation_strategies": []
            }
    
    def _parse_test_scenario_response(self, content: str) -> Dict[str, Any]:
        """Parse test scenario response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "test_objectives": ["Basic security assessment"],
                "attack_vectors": ["Port scanning", "Service enumeration"],
                "tools": ["nmap", "nmap"],
                "expected_outcomes": ["Service discovery"],
                "risk_assessment": "LOW",
                "authorization_required": True
            }
    
    def _parse_risk_response(self, content: str) -> Dict[str, Any]:
        """Parse risk assessment response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "risk_score": 50,
                "risk_level": "MEDIUM",
                "impact_assessment": "Moderate",
                "likelihood_assessment": "Medium",
                "risk_factors": ["Unknown threat"],
                "mitigation_priorities": ["Monitor"],
                "business_impact": "Moderate"
            }
    
    def _get_fallback_analysis(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI fails."""
        return {
            "threat_classification": "Unknown",
            "confidence_score": 30,
            "risk_level": "MEDIUM",
            "recommendations": ["Manual investigation required"],
            "attack_vectors": [],
            "iocs": [],
            "mitigation_strategies": ["Monitor and investigate"]
        }
    
    def _get_fallback_test_scenario(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback test scenario when AI fails."""
        return {
            "test_objectives": ["Basic port scan"],
            "attack_vectors": ["Port scanning"],
            "tools": ["nmap"],
            "expected_outcomes": ["Service discovery"],
            "risk_assessment": "LOW",
            "authorization_required": True
        }
    
    def _get_fallback_risk_assessment(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback risk assessment when AI fails."""
        return {
            "risk_score": 50,
            "risk_level": "MEDIUM",
            "impact_assessment": "Unknown",
            "likelihood_assessment": "Unknown",
            "risk_factors": ["Insufficient data"],
            "mitigation_priorities": ["Investigate further"],
            "business_impact": "Unknown"
        }
