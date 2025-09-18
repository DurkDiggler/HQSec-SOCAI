"""Automated threat hunting with hypothesis generation."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents

logger = logging.getLogger(__name__)

class ThreatHunter:
    """
    Automated threat hunting system that generates hypotheses
    and conducts systematic searches for advanced threats.
    """

    def __init__(self):
        self.hypothesis_templates = self._load_hypothesis_templates()
        self.hunting_techniques = self._load_hunting_techniques()
        self.ioc_patterns = self._load_ioc_patterns()
        self.attack_indicators = self._load_attack_indicators()

    def _load_hypothesis_templates(self) -> List[Dict[str, Any]]:
        """Loads threat hunting hypothesis templates."""
        return [
            {
                "id": "lateral_movement",
                "name": "Lateral Movement Detection",
                "description": "Detect potential lateral movement through network analysis",
                "indicators": ["unusual_logon_patterns", "privilege_escalation", "network_scanning"],
                "techniques": ["logon_analysis", "network_flow_analysis", "privilege_tracking"],
                "severity": "high"
            },
            {
                "id": "data_exfiltration",
                "name": "Data Exfiltration Attempts",
                "description": "Identify potential data exfiltration activities",
                "indicators": ["large_data_transfers", "unusual_network_connections", "encrypted_tunnels"],
                "techniques": ["network_flow_analysis", "dns_analysis", "file_access_monitoring"],
                "severity": "critical"
            },
            {
                "id": "persistence_mechanisms",
                "name": "Persistence Mechanisms",
                "description": "Find evidence of persistent access mechanisms",
                "indicators": ["scheduled_tasks", "registry_modifications", "service_installations"],
                "techniques": ["registry_analysis", "process_monitoring", "service_analysis"],
                "severity": "high"
            },
            {
                "id": "command_control",
                "name": "Command and Control Communication",
                "description": "Detect C2 communication patterns",
                "indicators": ["dns_tunneling", "beacon_communication", "encrypted_channels"],
                "techniques": ["dns_analysis", "network_flow_analysis", "ssl_analysis"],
                "severity": "high"
            },
            {
                "id": "insider_threat",
                "name": "Insider Threat Activities",
                "description": "Identify potential insider threat behaviors",
                "indicators": ["off_hours_access", "unusual_data_access", "privilege_abuse"],
                "techniques": ["user_behavior_analysis", "access_pattern_analysis", "data_loss_prevention"],
                "severity": "medium"
            },
            {
                "id": "supply_chain_attack",
                "name": "Supply Chain Compromise",
                "description": "Detect supply chain attack indicators",
                "indicators": ["software_tampering", "certificate_anomalies", "update_manipulation"],
                "techniques": ["file_integrity_monitoring", "certificate_analysis", "update_verification"],
                "severity": "critical"
            }
        ]

    def _load_hunting_techniques(self) -> Dict[str, Any]:
        """Loads threat hunting techniques and queries."""
        return {
            "logon_analysis": {
                "description": "Analyze authentication logs for suspicious patterns",
                "queries": [
                    "SELECT * FROM auth_logs WHERE logon_type = '3' AND time > NOW() - INTERVAL '24 hours'",
                    "SELECT user, COUNT(*) as logon_count FROM auth_logs GROUP BY user HAVING COUNT(*) > 100"
                ]
            },
            "network_flow_analysis": {
                "description": "Analyze network flows for anomalies",
                "queries": [
                    "SELECT src_ip, dst_ip, bytes FROM network_flows WHERE bytes > 1000000",
                    "SELECT dst_port, COUNT(*) as connection_count FROM network_flows GROUP BY dst_port"
                ]
            },
            "dns_analysis": {
                "description": "Analyze DNS queries for suspicious patterns",
                "queries": [
                    "SELECT domain, COUNT(*) as query_count FROM dns_logs GROUP BY domain HAVING COUNT(*) > 1000",
                    "SELECT * FROM dns_logs WHERE domain LIKE '%.tk' OR domain LIKE '%.ml'"
                ]
            },
            "process_monitoring": {
                "description": "Monitor process execution for suspicious activities",
                "queries": [
                    "SELECT process_name, COUNT(*) as execution_count FROM process_logs GROUP BY process_name",
                    "SELECT * FROM process_logs WHERE process_name IN ('powershell.exe', 'cmd.exe', 'wscript.exe')"
                ]
            },
            "registry_analysis": {
                "description": "Analyze registry modifications for persistence",
                "queries": [
                    "SELECT * FROM registry_logs WHERE key_path LIKE '%Run%' OR key_path LIKE '%RunOnce%'",
                    "SELECT * FROM registry_logs WHERE operation = 'SET_VALUE' AND time > NOW() - INTERVAL '1 hour'"
                ]
            }
        }

    def _load_ioc_patterns(self) -> Dict[str, List[str]]:
        """Loads IOC (Indicators of Compromise) patterns."""
        return {
            "ip_addresses": [
                r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",  # IPv4
                r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"  # IPv6
            ],
            "domains": [
                r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
            ],
            "file_hashes": [
                r"\b[a-fA-F0-9]{32}\b",  # MD5
                r"\b[a-fA-F0-9]{40}\b",  # SHA1
                r"\b[a-fA-F0-9]{64}\b"   # SHA256
            ],
            "email_addresses": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ],
            "urls": [
                r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?"
            ]
        }

    def _load_attack_indicators(self) -> Dict[str, List[str]]:
        """Loads attack indicators and TTPs."""
        return {
            "lateral_movement": [
                "psexec", "wmi", "smb", "rdp", "winrm", "powershell_remoting"
            ],
            "persistence": [
                "scheduled_task", "service_installation", "registry_run_key", "startup_folder"
            ],
            "privilege_escalation": [
                "uac_bypass", "token_manipulation", "dll_hijacking", "service_abuse"
            ],
            "defense_evasion": [
                "process_hollowing", "dll_injection", "code_injection", "rootkit"
            ],
            "credential_access": [
                "mimikatz", "lsass_dump", "credential_harvesting", "keylogger"
            ],
            "discovery": [
                "network_scanning", "system_info", "process_enumeration", "service_enumeration"
            ]
        }

    async def generate_hypotheses(self, 
                                 time_window_hours: int = 24,
                                 threat_landscape: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Generates threat hunting hypotheses based on current threat landscape.
        
        Args:
            time_window_hours: Time window for analysis
            threat_landscape: Current threat landscape data
            
        Returns:
            List of generated hypotheses
        """
        try:
            logger.info(f"Generating threat hunting hypotheses for {time_window_hours} hour window")
            
            # Get recent security events
            with get_db() as db:
                recent_alerts = get_historical_alerts(db, limit=1000)
                recent_incidents = get_historical_incidents(db, limit=100)
            
            # Analyze threat landscape
            threat_analysis = await self._analyze_threat_landscape(recent_alerts, recent_incidents)
            
            # Generate hypotheses based on analysis
            hypotheses = []
            
            for template in self.hypothesis_templates:
                # Check if hypothesis is relevant based on current data
                relevance_score = await self._calculate_hypothesis_relevance(template, threat_analysis)
                
                if relevance_score > 0.3:  # Threshold for hypothesis generation
                    hypothesis = {
                        **template,
                        "relevance_score": relevance_score,
                        "confidence": min(relevance_score * 1.5, 1.0),
                        "generated_at": datetime.utcnow().isoformat(),
                        "time_window_hours": time_window_hours,
                        "evidence_count": threat_analysis.get(f"{template['id']}_evidence_count", 0),
                        "priority": self._calculate_priority(template, relevance_score, threat_analysis)
                    }
                    hypotheses.append(hypothesis)
            
            # Sort by priority and relevance
            hypotheses.sort(key=lambda x: (x["priority"], x["relevance_score"]), reverse=True)
            
            logger.info(f"Generated {len(hypotheses)} threat hunting hypotheses")
            return hypotheses
            
        except Exception as e:
            logger.error(f"Error generating hypotheses: {e}")
            return []

    async def _analyze_threat_landscape(self, 
                                      alerts: List[Dict[str, Any]], 
                                      incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes the current threat landscape."""
        analysis = {
            "total_alerts": len(alerts),
            "total_incidents": len(incidents),
            "high_severity_alerts": 0,
            "attack_vectors": {},
            "ioc_matches": {},
            "temporal_patterns": {},
            "geographic_distribution": {},
            "asset_impact": {}
        }
        
        # Analyze alert patterns
        for alert in alerts:
            severity = alert.get("severity", "LOW")
            if severity in ["HIGH", "CRITICAL"]:
                analysis["high_severity_alerts"] += 1
            
            # Extract attack vectors
            event_type = alert.get("event_type", "unknown")
            analysis["attack_vectors"][event_type] = analysis["attack_vectors"].get(event_type, 0) + 1
            
            # Extract IOCs
            await self._extract_iocs_from_alert(alert, analysis)
        
        # Analyze incident patterns
        for incident in incidents:
            incident_type = incident.get("incident_type", "unknown")
            analysis["attack_vectors"][incident_type] = analysis["attack_vectors"].get(incident_type, 0) + 1
        
        return analysis

    async def _extract_iocs_from_alert(self, alert: Dict[str, Any], analysis: Dict[str, Any]):
        """Extracts IOCs from alert data."""
        import re
        
        # Extract text content
        text_content = f"{alert.get('message', '')} {alert.get('description', '')}"
        
        for ioc_type, patterns in self.ioc_patterns.items():
            if ioc_type not in analysis["ioc_matches"]:
                analysis["ioc_matches"][ioc_type] = set()
            
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                analysis["ioc_matches"][ioc_type].update(matches)

    async def _calculate_hypothesis_relevance(self, 
                                            template: Dict[str, Any], 
                                            threat_analysis: Dict[str, Any]) -> float:
        """Calculates relevance score for a hypothesis template."""
        relevance_factors = []
        
        # Check for matching attack vectors
        attack_vectors = threat_analysis.get("attack_vectors", {})
        for indicator in template["indicators"]:
            if any(indicator in vector.lower() for vector in attack_vectors.keys()):
                relevance_factors.append(0.3)
        
        # Check for IOC matches
        ioc_matches = threat_analysis.get("ioc_matches", {})
        total_iocs = sum(len(iocs) for iocs in ioc_matches.values())
        if total_iocs > 0:
            relevance_factors.append(min(total_iocs / 100, 0.4))
        
        # Check for high severity alerts
        high_severity_ratio = threat_analysis.get("high_severity_alerts", 0) / max(threat_analysis.get("total_alerts", 1), 1)
        if high_severity_ratio > 0.1:
            relevance_factors.append(0.3)
        
        return sum(relevance_factors) if relevance_factors else 0.0

    def _calculate_priority(self, 
                          template: Dict[str, Any], 
                          relevance_score: float, 
                          threat_analysis: Dict[str, Any]) -> int:
        """Calculates priority score for a hypothesis."""
        priority = 0
        
        # Base priority from template severity
        severity_priority = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        priority += severity_priority.get(template["severity"], 1)
        
        # Relevance score multiplier
        priority += int(relevance_score * 3)
        
        # Evidence count bonus
        evidence_count = threat_analysis.get(f"{template['id']}_evidence_count", 0)
        priority += min(evidence_count, 3)
        
        return min(priority, 10)  # Cap at 10

    async def execute_hypothesis(self, 
                               hypothesis_id: str, 
                               time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Executes a threat hunting hypothesis.
        
        Args:
            hypothesis_id: ID of the hypothesis to execute
            time_window_hours: Time window for hunting
            
        Returns:
            Hunting results and findings
        """
        try:
            # Find hypothesis template
            template = next((t for t in self.hypothesis_templates if t["id"] == hypothesis_id), None)
            if not template:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
            
            logger.info(f"Executing threat hunting hypothesis: {template['name']}")
            
            # Execute hunting techniques
            findings = []
            for technique_name in template["techniques"]:
                technique_results = await self._execute_hunting_technique(
                    technique_name, time_window_hours
                )
                findings.extend(technique_results)
            
            # Analyze findings
            analysis_results = await self._analyze_findings(findings, template)
            
            # Generate hunting report
            hunting_report = {
                "hypothesis_id": hypothesis_id,
                "hypothesis_name": template["name"],
                "execution_time": datetime.utcnow().isoformat(),
                "time_window_hours": time_window_hours,
                "total_findings": len(findings),
                "high_confidence_findings": len([f for f in findings if f.get("confidence", 0) > 0.8]),
                "findings": findings,
                "analysis": analysis_results,
                "recommendations": await self._generate_recommendations(findings, template)
            }
            
            logger.info(f"Threat hunting completed: {len(findings)} findings")
            return hunting_report
            
        except Exception as e:
            logger.error(f"Error executing hypothesis {hypothesis_id}: {e}")
            return {
                "hypothesis_id": hypothesis_id,
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat()
            }

    async def _execute_hunting_technique(self, 
                                       technique_name: str, 
                                       time_window_hours: int) -> List[Dict[str, Any]]:
        """Executes a specific hunting technique."""
        try:
            technique = self.hunting_techniques.get(technique_name)
            if not technique:
                logger.warning(f"Hunting technique {technique_name} not found")
                return []
            
            # This would execute actual queries against the data sources
            # For now, we'll simulate the results
            findings = []
            
            # Simulate query execution
            for query in technique["queries"]:
                # In production, this would execute against actual data sources
                simulated_results = await self._simulate_query_execution(query, time_window_hours)
                findings.extend(simulated_results)
            
            return findings
            
        except Exception as e:
            logger.error(f"Error executing hunting technique {technique_name}: {e}")
            return []

    async def _simulate_query_execution(self, query: str, time_window_hours: int) -> List[Dict[str, Any]]:
        """Simulates query execution (placeholder for actual implementation)."""
        # This would be replaced with actual database queries
        import random
        
        findings = []
        num_results = random.randint(0, 5)  # Simulate 0-5 findings
        
        for i in range(num_results):
            finding = {
                "id": f"finding_{random.randint(1000, 9999)}",
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": random.uniform(0.3, 0.9),
                "severity": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "description": f"Simulated finding from query: {query[:50]}...",
                "data": {
                    "sample_field": f"value_{i}",
                    "score": random.uniform(0.1, 1.0)
                }
            }
            findings.append(finding)
        
        return findings

    async def _analyze_findings(self, 
                              findings: List[Dict[str, Any]], 
                              template: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes hunting findings for patterns and correlations."""
        if not findings:
            return {"patterns": [], "correlations": [], "summary": "No findings"}
        
        analysis = {
            "total_findings": len(findings),
            "severity_distribution": {},
            "confidence_distribution": {},
            "temporal_patterns": [],
            "correlations": [],
            "summary": ""
        }
        
        # Analyze severity distribution
        for finding in findings:
            severity = finding.get("severity", "UNKNOWN")
            analysis["severity_distribution"][severity] = analysis["severity_distribution"].get(severity, 0) + 1
        
        # Analyze confidence distribution
        confidences = [f.get("confidence", 0) for f in findings]
        analysis["confidence_distribution"] = {
            "mean": np.mean(confidences),
            "std": np.std(confidences),
            "min": np.min(confidences),
            "max": np.max(confidences)
        }
        
        # Find high-confidence findings
        high_confidence = [f for f in findings if f.get("confidence", 0) > 0.8]
        analysis["high_confidence_count"] = len(high_confidence)
        
        # Generate summary
        if high_confidence:
            analysis["summary"] = f"Found {len(high_confidence)} high-confidence indicators of {template['name'].lower()}"
        else:
            analysis["summary"] = f"Found {len(findings)} potential indicators, but none with high confidence"
        
        return analysis

    async def _generate_recommendations(self, 
                                      findings: List[Dict[str, Any]], 
                                      template: Dict[str, Any]) -> List[str]:
        """Generates recommendations based on hunting findings."""
        recommendations = []
        
        if not findings:
            recommendations.append("No immediate threats detected. Continue monitoring.")
            return recommendations
        
        high_confidence_findings = [f for f in findings if f.get("confidence", 0) > 0.8]
        
        if high_confidence_findings:
            recommendations.append(f"Immediate investigation required: {len(high_confidence_findings)} high-confidence findings")
            recommendations.append("Consider escalating to incident response team")
            recommendations.append("Implement additional monitoring for affected systems")
        else:
            recommendations.append("Continue monitoring for additional indicators")
            recommendations.append("Review and tune detection rules based on findings")
        
        # Template-specific recommendations
        if template["id"] == "lateral_movement":
            recommendations.append("Review network segmentation and access controls")
            recommendations.append("Implement network monitoring for lateral movement")
        elif template["id"] == "data_exfiltration":
            recommendations.append("Implement data loss prevention (DLP) controls")
            recommendations.append("Monitor large data transfers and unusual network activity")
        elif template["id"] == "persistence_mechanisms":
            recommendations.append("Review system configurations for unauthorized changes")
            recommendations.append("Implement file integrity monitoring")
        
        return recommendations

    async def get_hunting_status(self) -> Dict[str, Any]:
        """Gets the current status of threat hunting activities."""
        return {
            "total_hypotheses": len(self.hypothesis_templates),
            "available_techniques": len(self.hunting_techniques),
            "ioc_patterns": sum(len(patterns) for patterns in self.ioc_patterns.values()),
            "attack_indicators": sum(len(indicators) for indicators in self.attack_indicators.values()),
            "last_updated": datetime.utcnow().isoformat()
        }
