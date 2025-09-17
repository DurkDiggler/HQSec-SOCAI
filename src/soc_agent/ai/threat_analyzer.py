"""AI-powered threat analyzer for SOC Agent."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class AIThreatAnalyzer:
    """AI-powered threat analysis engine."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.threat_patterns = self._load_threat_patterns()
        self.attack_vectors = self._load_attack_vectors()
    
    async def analyze_threat(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive AI threat analysis."""
        try:
            # Get AI analysis from LLM
            ai_analysis = await self.llm_client.analyze_threat(event_data)
            
            # Enhance with pattern matching
            pattern_analysis = self._analyze_threat_patterns(event_data)
            
            # Combine analyses
            combined_analysis = self._combine_analyses(ai_analysis, pattern_analysis)
            
            # Add confidence scoring
            combined_analysis["confidence_score"] = self._calculate_confidence(combined_analysis)
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"AI threat analysis failed: {e}")
            return self._get_fallback_analysis(event_data)
    
    async def generate_attack_scenario(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic attack scenario for testing."""
        try:
            # Get AI-generated test scenario
            ai_scenario = await self.llm_client.generate_test_scenario(target_info)
            
            # Enhance with known attack patterns
            enhanced_scenario = self._enhance_test_scenario(ai_scenario, target_info)
            
            return enhanced_scenario
            
        except Exception as e:
            logger.error(f"Attack scenario generation failed: {e}")
            return self._get_fallback_scenario(target_info)
    
    async def correlate_threats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Correlate multiple events to identify attack campaigns."""
        try:
            # Analyze each event
            analyses = []
            for event in events:
                analysis = await self.analyze_threat(event)
                analyses.append(analysis)
            
            # Find correlations
            correlations = self._find_correlations(analyses)
            
            # Generate campaign analysis
            campaign_analysis = self._analyze_campaign(correlations, events)
            
            return campaign_analysis
            
        except Exception as e:
            logger.error(f"Threat correlation failed: {e}")
            return {"correlations": [], "campaign_analysis": {}}
    
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load known threat patterns."""
        return {
            "malware": [
                "powershell", "cmd", "wscript", "rundll32", "regsvr32",
                "certutil", "bitsadmin", "wmic", "schtasks"
            ],
            "lateral_movement": [
                "psexec", "wmi", "smb", "rdp", "winrm", "ldap",
                "kerberos", "golden_ticket", "pass_the_hash"
            ],
            "persistence": [
                "registry", "scheduled_task", "service", "startup",
                "wmi_event", "logon_script", "dll_hijack"
            ],
            "exfiltration": [
                "ftp", "http", "https", "dns", "icmp", "smtp",
                "cloud_storage", "tor", "vpn"
            ],
            "reconnaissance": [
                "nmap", "port_scan", "service_scan", "os_detection",
                "vulnerability_scan", "directory_enum", "subdomain_enum"
            ]
        }
    
    def _load_attack_vectors(self) -> Dict[str, Dict[str, Any]]:
        """Load known attack vectors."""
        return {
            "web_application": {
                "tools": ["sqlmap", "nikto", "wpscan", "gobuster"],
                "techniques": ["sql_injection", "xss", "csrf", "directory_traversal"]
            },
            "network": {
                "tools": ["nmap", "masscan", "zmap", "netcat"],
                "techniques": ["port_scanning", "service_enumeration", "os_fingerprinting"]
            },
            "authentication": {
                "tools": ["hydra", "john", "hashcat", "medusa"],
                "techniques": ["brute_force", "dictionary_attack", "rainbow_table"]
            },
            "exploitation": {
                "tools": ["metasploit", "exploitdb", "custom_exploits"],
                "techniques": ["buffer_overflow", "rop_chain", "ret2libc"]
            }
        }
    
    def _analyze_threat_patterns(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze event against known threat patterns."""
        message = (event_data.get("message", "") or "").lower()
        event_type = (event_data.get("event_type", "") or "").lower()
        
        pattern_matches = {}
        for category, patterns in self.threat_patterns.items():
            matches = [pattern for pattern in patterns if pattern in message or pattern in event_type]
            if matches:
                pattern_matches[category] = matches
        
        return {
            "pattern_matches": pattern_matches,
            "threat_categories": list(pattern_matches.keys()),
            "confidence": len(pattern_matches) * 20  # 20% per category match
        }
    
    def _combine_analyses(self, ai_analysis: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine AI analysis with pattern analysis."""
        combined = ai_analysis.copy()
        
        # Add pattern analysis results
        combined["pattern_analysis"] = pattern_analysis
        
        # Adjust confidence based on pattern matches
        if pattern_analysis.get("pattern_matches"):
            pattern_confidence = pattern_analysis.get("confidence", 0)
            ai_confidence = ai_analysis.get("confidence_score", 0)
            combined["confidence_score"] = min(100, ai_confidence + pattern_confidence)
        
        # Add threat categories from pattern analysis
        if pattern_analysis.get("threat_categories"):
            combined["threat_categories"] = pattern_analysis["threat_categories"]
        
        return combined
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> int:
        """Calculate overall confidence score."""
        base_confidence = analysis.get("confidence_score", 50)
        
        # Boost confidence for pattern matches
        if analysis.get("pattern_analysis", {}).get("pattern_matches"):
            base_confidence += 20
        
        # Boost confidence for specific threat indicators
        if analysis.get("threat_categories"):
            base_confidence += len(analysis["threat_categories"]) * 10
        
        return min(100, base_confidence)
    
    def _enhance_test_scenario(self, ai_scenario: Dict[str, Any], target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance AI test scenario with specific tools and techniques."""
        enhanced = ai_scenario.copy()
        
        # Add specific tools based on target type
        target_type = self._identify_target_type(target_info)
        if target_type in self.attack_vectors:
            enhanced["recommended_tools"] = self.attack_vectors[target_type]["tools"]
            enhanced["techniques"] = self.attack_vectors[target_type]["techniques"]
        
        # Add MCP server commands
        enhanced["mcp_commands"] = self._generate_mcp_commands(target_info, enhanced)
        
        return enhanced
    
    def _identify_target_type(self, target_info: Dict[str, Any]) -> str:
        """Identify target type for appropriate tool selection."""
        ip = target_info.get("ip", "")
        ports = target_info.get("ports", [])
        services = target_info.get("services", [])
        
        # Check for web services
        web_ports = [80, 443, 8080, 8443, 8000, 3000]
        if any(port in web_ports for port in ports):
            return "web_application"
        
        # Check for database services
        db_ports = [3306, 5432, 1433, 1521, 27017]
        if any(port in db_ports for port in ports):
            return "database"
        
        # Check for authentication services
        auth_ports = [22, 23, 21, 25, 110, 143]
        if any(port in auth_ports for port in ports):
            return "authentication"
        
        return "network"
    
    def _generate_mcp_commands(self, target_info: Dict[str, Any], scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate MCP server commands for the test scenario."""
        commands = []
        target_ip = target_info.get("ip", "unknown")
        
        # Basic reconnaissance
        commands.append({
            "name": "nmap_scan",
            "description": "Basic port scan",
            "command": f"nmap -sS -O {target_ip}",
            "risk_level": "LOW"
        })
        
        # Service enumeration
        commands.append({
            "name": "service_scan",
            "description": "Service version detection",
            "command": f"nmap -sV -sC {target_ip}",
            "risk_level": "LOW"
        })
        
        # Vulnerability scan if web services detected
        if "web_application" in scenario.get("recommended_tools", []):
            commands.append({
                "name": "web_vuln_scan",
                "description": "Web vulnerability scan",
                "command": f"nikto -h http://{target_ip}",
                "risk_level": "MEDIUM"
            })
        
        return commands
    
    def _find_correlations(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find correlations between multiple threat analyses."""
        correlations = []
        
        # Group by threat categories
        category_groups = {}
        for i, analysis in enumerate(analyses):
            categories = analysis.get("threat_categories", [])
            for category in categories:
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(i)
        
        # Find correlations
        for category, indices in category_groups.items():
            if len(indices) > 1:
                correlations.append({
                    "category": category,
                    "event_indices": indices,
                    "correlation_strength": len(indices) / len(analyses),
                    "description": f"Multiple events show {category} patterns"
                })
        
        return correlations
    
    def _analyze_campaign(self, correlations: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze attack campaign based on correlations."""
        if not correlations:
            return {"campaign_detected": False}
        
        # Calculate campaign confidence
        max_correlation = max(correlations, key=lambda x: x["correlation_strength"])
        campaign_confidence = max_correlation["correlation_strength"] * 100
        
        # Identify attack progression
        attack_stages = self._identify_attack_stages(events)
        
        return {
            "campaign_detected": True,
            "campaign_confidence": campaign_confidence,
            "correlations": correlations,
            "attack_stages": attack_stages,
            "threat_level": "HIGH" if campaign_confidence > 70 else "MEDIUM"
        }
    
    def _identify_attack_stages(self, events: List[Dict[str, Any]]) -> List[str]:
        """Identify attack stages based on event sequence."""
        stages = []
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
        
        for event in sorted_events:
            event_type = event.get("event_type", "").lower()
            if "recon" in event_type or "scan" in event_type:
                stages.append("reconnaissance")
            elif "auth" in event_type or "login" in event_type:
                stages.append("initial_access")
            elif "lateral" in event_type or "movement" in event_type:
                stages.append("lateral_movement")
            elif "exfil" in event_type or "data" in event_type:
                stages.append("exfiltration")
        
        return list(set(stages))  # Remove duplicates
    
    def _get_fallback_analysis(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI fails."""
        return {
            "threat_classification": "Unknown",
            "confidence_score": 30,
            "risk_level": "MEDIUM",
            "recommendations": ["Manual investigation required"],
            "attack_vectors": [],
            "iocs": [],
            "mitigation_strategies": ["Monitor and investigate"],
            "pattern_analysis": {},
            "threat_categories": []
        }
    
    def _get_fallback_scenario(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback test scenario when AI fails."""
        return {
            "test_objectives": ["Basic security assessment"],
            "attack_vectors": ["Port scanning"],
            "recommended_tools": ["nmap"],
            "techniques": ["port_scanning"],
            "expected_outcomes": ["Service discovery"],
            "risk_assessment": "LOW",
            "authorization_required": True,
            "mcp_commands": [
                {
                    "name": "basic_scan",
                    "description": "Basic port scan",
                    "command": f"nmap {target_info.get('ip', 'unknown')}",
                    "risk_level": "LOW"
                }
            ]
        }
