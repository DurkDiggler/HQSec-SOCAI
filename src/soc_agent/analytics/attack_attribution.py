"""Attack attribution system for threat actor identification."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents

logger = logging.getLogger(__name__)

class AttackAttributor:
    """
    Attack attribution system that identifies threat actors
    based on TTPs, IOCs, and attack patterns.
    """

    def __init__(self):
        self.threat_actors = self._load_threat_actors()
        self.ttp_database = self._load_ttp_database()
        self.ioc_database = self._load_ioc_database()
        self.attack_patterns = self._load_attack_patterns()
        self.attribution_models = {}

    def _load_threat_actors(self) -> List[Dict[str, Any]]:
        """Loads threat actor profiles and characteristics."""
        return [
            {
                "id": "apt1",
                "name": "APT1 (Comment Crew)",
                "aliases": ["Comment Crew", "Comment Group", "Byzantine Candor"],
                "country": "China",
                "motivation": "Espionage",
                "targets": ["Government", "Defense", "Technology", "Finance"],
                "ttps": [
                    "T1055", "T1059", "T1071", "T1083", "T1105", "T1112", "T1135", "T1140"
                ],
                "tools": ["Poison Ivy", "Gh0st RAT", "HTRAN", "Cobalt Strike"],
                "iocs": {
                    "domains": ["*.commentcrew.com", "*.byzantinecandor.com"],
                    "ip_ranges": ["1.2.3.0/24", "5.6.7.0/24"],
                    "file_hashes": ["a1b2c3d4e5f6..."],
                    "email_addresses": ["fake@commentcrew.com"]
                },
                "attack_phases": ["Reconnaissance", "Initial Access", "Persistence", "Lateral Movement", "Data Exfiltration"],
                "confidence_level": "high"
            },
            {
                "id": "lazarus",
                "name": "Lazarus Group",
                "aliases": ["Hidden Cobra", "Guardians of Peace", "ZINC"],
                "country": "North Korea",
                "motivation": "Financial",
                "targets": ["Cryptocurrency", "Banking", "Government", "Media"],
                "ttps": [
                    "T1055", "T1059", "T1071", "T1083", "T1105", "T1112", "T1135", "T1140", "T1566"
                ],
                "tools": ["Dacls", "Fallchill", "Joanap", "Brambul", "DeltaCharlie"],
                "iocs": {
                    "domains": ["*.lazarus.com", "*.hiddencobra.com"],
                    "ip_ranges": ["10.20.30.0/24", "40.50.60.0/24"],
                    "file_hashes": ["b2c3d4e5f6a1..."],
                    "email_addresses": ["fake@lazarus.com"]
                },
                "attack_phases": ["Reconnaissance", "Initial Access", "Persistence", "Lateral Movement", "Data Exfiltration", "Impact"],
                "confidence_level": "high"
            },
            {
                "id": "fin7",
                "name": "FIN7",
                "aliases": ["Carbanak", "Navigator Group", "Anunak"],
                "country": "Unknown",
                "motivation": "Financial",
                "targets": ["Retail", "Hospitality", "Restaurants", "Point of Sale"],
                "ttps": [
                    "T1055", "T1059", "T1071", "T1083", "T1105", "T1112", "T1135", "T1140", "T1566", "T1078"
                ],
                "tools": ["Carbanak", "Cobalt Strike", "PowerShell", "Mimikatz"],
                "iocs": {
                    "domains": ["*.fin7.com", "*.carbanak.com"],
                    "ip_ranges": ["100.200.300.0/24"],
                    "file_hashes": ["c3d4e5f6a1b2..."],
                    "email_addresses": ["fake@fin7.com"]
                },
                "attack_phases": ["Reconnaissance", "Initial Access", "Persistence", "Lateral Movement", "Data Exfiltration"],
                "confidence_level": "medium"
            },
            {
                "id": "ryuk",
                "name": "Ryuk Ransomware Group",
                "aliases": ["Wizard Spider", "Grim Spider"],
                "country": "Russia",
                "motivation": "Financial",
                "targets": ["Healthcare", "Government", "Education", "Critical Infrastructure"],
                "ttps": [
                    "T1055", "T1059", "T1071", "T1083", "T1105", "T1112", "T1135", "T1140", "T1566", "T1078", "T1486"
                ],
                "tools": ["Ryuk", "Trickbot", "Emotet", "Cobalt Strike", "Mimikatz"],
                "iocs": {
                    "domains": ["*.ryuk.com", "*.wizardspider.com"],
                    "ip_ranges": ["200.300.400.0/24"],
                    "file_hashes": ["d4e5f6a1b2c3..."],
                    "email_addresses": ["fake@ryuk.com"]
                },
                "attack_phases": ["Reconnaissance", "Initial Access", "Persistence", "Lateral Movement", "Data Exfiltration", "Impact"],
                "confidence_level": "high"
            }
        ]

    def _load_ttp_database(self) -> Dict[str, Dict[str, Any]]:
        """Loads MITRE ATT&CK TTP database."""
        return {
            "T1055": {
                "name": "Process Injection",
                "description": "Adversaries may inject code into processes in order to evade process-based defenses",
                "tactics": ["Defense Evasion", "Privilege Escalation"],
                "techniques": ["DLL Injection", "Process Hollowing", "Process Doppelgänging"]
            },
            "T1059": {
                "name": "Command and Scripting Interpreter",
                "description": "Adversaries may abuse command and script interpreters to execute commands",
                "tactics": ["Execution"],
                "techniques": ["PowerShell", "Command Prompt", "JavaScript", "Python"]
            },
            "T1071": {
                "name": "Application Layer Protocol",
                "description": "Adversaries may communicate using application layer protocols",
                "tactics": ["Command and Control"],
                "techniques": ["HTTP", "HTTPS", "DNS", "SMTP", "FTP"]
            },
            "T1083": {
                "name": "File and Directory Discovery",
                "description": "Adversaries may enumerate files and directories",
                "tactics": ["Discovery"],
                "techniques": ["dir", "ls", "find", "locate"]
            },
            "T1105": {
                "name": "Ingress Tool Transfer",
                "description": "Adversaries may transfer tools or other files",
                "tactics": ["Command and Control"],
                "techniques": ["HTTP", "HTTPS", "FTP", "SMB", "TFTP"]
            },
            "T1112": {
                "name": "Modify Registry",
                "description": "Adversaries may interact with the Windows Registry",
                "tactics": ["Defense Evasion"],
                "techniques": ["Registry Run Keys", "Service Registry Keys", "Winlogon Helper DLL"]
            },
            "T1135": {
                "name": "Network Share Discovery",
                "description": "Adversaries may look for folders and drives accessible",
                "tactics": ["Discovery"],
                "techniques": ["net view", "net share", "net use"]
            },
            "T1140": {
                "name": "Deobfuscate/Decode Files or Information",
                "description": "Adversaries may use obfuscated files or information",
                "tactics": ["Defense Evasion"],
                "techniques": ["Base64", "XOR", "ROT13", "Custom Encoding"]
            },
            "T1566": {
                "name": "Phishing",
                "description": "Adversaries may send phishing messages",
                "tactics": ["Initial Access"],
                "techniques": ["Spearphishing Attachment", "Spearphishing Link", "Spearphishing via Service"]
            },
            "T1078": {
                "name": "Valid Accounts",
                "description": "Adversaries may obtain and abuse credentials",
                "tactics": ["Defense Evasion", "Persistence", "Privilege Escalation", "Initial Access"],
                "techniques": ["Default Accounts", "Domain Accounts", "Local Accounts", "Cloud Accounts"]
            },
            "T1486": {
                "name": "Data Encrypted for Impact",
                "description": "Adversaries may encrypt data on target systems",
                "tactics": ["Impact"],
                "techniques": ["Symmetric Cryptography", "Asymmetric Cryptography", "Hybrid Cryptography"]
            }
        }

    def _load_ioc_database(self) -> Dict[str, List[str]]:
        """Loads IOC database for attribution."""
        return {
            "domains": [
                "commentcrew.com", "byzantinecandor.com", "lazarus.com", "hiddencobra.com",
                "fin7.com", "carbanak.com", "ryuk.com", "wizardspider.com"
            ],
            "ip_ranges": [
                "1.2.3.0/24", "5.6.7.0/24", "10.20.30.0/24", "40.50.60.0/24",
                "100.200.300.0/24", "200.300.400.0/24"
            ],
            "file_hashes": [
                "a1b2c3d4e5f6...", "b2c3d4e5f6a1...", "c3d4e5f6a1b2...", "d4e5f6a1b2c3..."
            ],
            "email_addresses": [
                "fake@commentcrew.com", "fake@lazarus.com", "fake@fin7.com", "fake@ryuk.com"
            ]
        }

    def _load_attack_patterns(self) -> Dict[str, List[str]]:
        """Loads attack patterns for attribution."""
        return {
            "reconnaissance": [
                "network_scanning", "port_scanning", "vulnerability_scanning", "osint_gathering"
            ],
            "initial_access": [
                "phishing", "exploit_public_facing", "supply_chain_compromise", "trusted_relationship"
            ],
            "execution": [
                "command_and_scripting", "user_execution", "scheduled_task", "system_services"
            ],
            "persistence": [
                "scheduled_task", "service_registration", "registry_run_keys", "startup_folder"
            ],
            "privilege_escalation": [
                "exploit_vulnerability", "access_token_manipulation", "process_injection", "dll_hijacking"
            ],
            "defense_evasion": [
                "process_injection", "dll_injection", "rootkit", "file_deletion", "timestomp"
            ],
            "credential_access": [
                "credential_dumping", "keylogging", "credential_harvesting", "brute_force"
            ],
            "discovery": [
                "system_information_discovery", "network_service_scanning", "process_discovery", "system_network_configuration"
            ],
            "lateral_movement": [
                "remote_services", "taint_shared_content", "remote_file_copy", "pass_the_hash"
            ],
            "collection": [
                "data_from_local_system", "data_from_network_shared_drive", "data_from_removable_media", "screen_capture"
            ],
            "command_and_control": [
                "remote_access_software", "data_encoding", "data_obfuscation", "encrypted_channel"
            ],
            "exfiltration": [
                "automated_exfiltration", "data_compression", "data_encryption", "exfiltration_over_web_service"
            ],
            "impact": [
                "data_encrypted_for_impact", "data_destruction", "service_stop", "system_shutdown"
            ]
        }

    async def attribute_attack(self, 
                             attack_data: Dict[str, Any], 
                             confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Attributes an attack to a threat actor based on TTPs and IOCs.
        
        Args:
            attack_data: Attack data including TTPs, IOCs, and patterns
            confidence_threshold: Minimum confidence for attribution
            
        Returns:
            Attribution results with confidence scores
        """
        try:
            logger.info("Starting attack attribution analysis")
            
            # Extract attack characteristics
            attack_characteristics = await self._extract_attack_characteristics(attack_data)
            
            # Calculate attribution scores for each threat actor
            attribution_scores = []
            
            for threat_actor in self.threat_actors:
                score = await self._calculate_attribution_score(
                    threat_actor, attack_characteristics
                )
                
                if score["total_score"] >= confidence_threshold:
                    attribution_scores.append({
                        "threat_actor": threat_actor,
                        "score": score,
                        "confidence": score["total_score"]
                    })
            
            # Sort by confidence score
            attribution_scores.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Generate attribution report
            attribution_report = {
                "attack_id": attack_data.get("id", "unknown"),
                "analysis_time": datetime.utcnow().isoformat(),
                "confidence_threshold": confidence_threshold,
                "total_candidates": len(attribution_scores),
                "high_confidence_attributions": [a for a in attribution_scores if a["confidence"] >= 0.8],
                "medium_confidence_attributions": [a for a in attribution_scores if 0.6 <= a["confidence"] < 0.8],
                "low_confidence_attributions": [a for a in attribution_scores if 0.4 <= a["confidence"] < 0.6],
                "attack_characteristics": attack_characteristics,
                "recommendations": await self._generate_attribution_recommendations(attribution_scores)
            }
            
            logger.info(f"Attack attribution completed: {len(attribution_scores)} candidates found")
            return attribution_report
            
        except Exception as e:
            logger.error(f"Error in attack attribution: {e}")
            return {
                "error": str(e),
                "analysis_time": datetime.utcnow().isoformat()
            }

    async def _extract_attack_characteristics(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts characteristics from attack data."""
        characteristics = {
            "ttps": [],
            "tools": [],
            "iocs": {
                "domains": [],
                "ip_addresses": [],
                "file_hashes": [],
                "email_addresses": []
            },
            "attack_phases": [],
            "targets": [],
            "motivation": "unknown",
            "geographic_indicators": [],
            "temporal_patterns": []
        }
        
        # Extract TTPs
        if "ttps" in attack_data:
            characteristics["ttps"] = attack_data["ttps"]
        
        # Extract tools
        if "tools" in attack_data:
            characteristics["tools"] = attack_data["tools"]
        
        # Extract IOCs
        if "iocs" in attack_data:
            for ioc_type, ioc_list in attack_data["iocs"].items():
                if ioc_type in characteristics["iocs"]:
                    characteristics["iocs"][ioc_type] = ioc_list
        
        # Extract attack phases
        if "attack_phases" in attack_data:
            characteristics["attack_phases"] = attack_data["attack_phases"]
        
        # Extract targets
        if "targets" in attack_data:
            characteristics["targets"] = attack_data["targets"]
        
        # Extract motivation
        if "motivation" in attack_data:
            characteristics["motivation"] = attack_data["motivation"]
        
        return characteristics

    async def _calculate_attribution_score(self, 
                                         threat_actor: Dict[str, Any], 
                                         attack_characteristics: Dict[str, Any]) -> Dict[str, float]:
        """Calculates attribution score for a threat actor."""
        scores = {
            "ttp_match": 0.0,
            "tool_match": 0.0,
            "ioc_match": 0.0,
            "phase_match": 0.0,
            "target_match": 0.0,
            "motivation_match": 0.0,
            "total_score": 0.0
        }
        
        # TTP matching
        threat_actor_ttps = set(threat_actor.get("ttps", []))
        attack_ttps = set(attack_characteristics.get("ttps", []))
        
        if threat_actor_ttps and attack_ttps:
            ttp_intersection = threat_actor_ttps.intersection(attack_ttps)
            scores["ttp_match"] = len(ttp_intersection) / len(threat_actor_ttps)
        
        # Tool matching
        threat_actor_tools = set(threat_actor.get("tools", []))
        attack_tools = set(attack_characteristics.get("tools", []))
        
        if threat_actor_tools and attack_tools:
            tool_intersection = threat_actor_tools.intersection(attack_tools)
            scores["tool_match"] = len(tool_intersection) / len(threat_actor_tools)
        
        # IOC matching
        ioc_matches = 0
        total_iocs = 0
        
        for ioc_type in ["domains", "ip_addresses", "file_hashes", "email_addresses"]:
            threat_actor_iocs = set(threat_actor.get("iocs", {}).get(ioc_type, []))
            attack_iocs = set(attack_characteristics.get("iocs", {}).get(ioc_type, []))
            
            if threat_actor_iocs and attack_iocs:
                ioc_intersection = threat_actor_iocs.intersection(attack_iocs)
                ioc_matches += len(ioc_intersection)
                total_iocs += len(threat_actor_iocs)
        
        if total_iocs > 0:
            scores["ioc_match"] = ioc_matches / total_iocs
        
        # Attack phase matching
        threat_actor_phases = set(threat_actor.get("attack_phases", []))
        attack_phases = set(attack_characteristics.get("attack_phases", []))
        
        if threat_actor_phases and attack_phases:
            phase_intersection = threat_actor_phases.intersection(attack_phases)
            scores["phase_match"] = len(phase_intersection) / len(threat_actor_phases)
        
        # Target matching
        threat_actor_targets = set(threat_actor.get("targets", []))
        attack_targets = set(attack_characteristics.get("targets", []))
        
        if threat_actor_targets and attack_targets:
            target_intersection = threat_actor_targets.intersection(attack_targets)
            scores["target_match"] = len(target_intersection) / len(threat_actor_targets)
        
        # Motivation matching
        threat_actor_motivation = threat_actor.get("motivation", "").lower()
        attack_motivation = attack_characteristics.get("motivation", "").lower()
        
        if threat_actor_motivation and attack_motivation:
            if threat_actor_motivation == attack_motivation:
                scores["motivation_match"] = 1.0
            elif threat_actor_motivation in attack_motivation or attack_motivation in threat_actor_motivation:
                scores["motivation_match"] = 0.5
        
        # Calculate total score (weighted average)
        weights = {
            "ttp_match": 0.3,
            "tool_match": 0.2,
            "ioc_match": 0.25,
            "phase_match": 0.1,
            "target_match": 0.1,
            "motivation_match": 0.05
        }
        
        scores["total_score"] = sum(
            scores[key] * weights[key] for key in weights.keys()
        )
        
        return scores

    async def _generate_attribution_recommendations(self, 
                                                  attribution_scores: List[Dict[str, Any]]) -> List[str]:
        """Generates recommendations based on attribution results."""
        recommendations = []
        
        if not attribution_scores:
            recommendations.append("No clear attribution found. Consider additional intelligence gathering.")
            return recommendations
        
        top_attribution = attribution_scores[0]
        confidence = top_attribution["confidence"]
        threat_actor = top_attribution["threat_actor"]
        
        if confidence >= 0.8:
            recommendations.append(f"High confidence attribution to {threat_actor['name']}")
            recommendations.append(f"Country of origin: {threat_actor['country']}")
            recommendations.append(f"Primary motivation: {threat_actor['motivation']}")
            recommendations.append("Consider sharing intelligence with relevant authorities")
        elif confidence >= 0.6:
            recommendations.append(f"Medium confidence attribution to {threat_actor['name']}")
            recommendations.append("Gather additional evidence to confirm attribution")
            recommendations.append("Monitor for additional TTPs and IOCs")
        else:
            recommendations.append("Low confidence attribution. Consider alternative threat actors")
            recommendations.append("Review attack characteristics for additional indicators")
        
        # Add threat actor specific recommendations
        if threat_actor["id"] == "apt1":
            recommendations.append("Focus on espionage-related activities and data exfiltration")
            recommendations.append("Monitor for Chinese language artifacts and timezone patterns")
        elif threat_actor["id"] == "lazarus":
            recommendations.append("Focus on financial motivation and cryptocurrency-related activities")
            recommendations.append("Monitor for North Korean language artifacts and timezone patterns")
        elif threat_actor["id"] == "fin7":
            recommendations.append("Focus on point-of-sale and payment card related activities")
            recommendations.append("Monitor for retail and hospitality sector targeting")
        elif threat_actor["id"] == "ryuk":
            recommendations.append("Focus on ransomware activities and critical infrastructure targeting")
            recommendations.append("Monitor for encryption activities and ransom demands")
        
        return recommendations

    async def analyze_campaign(self, 
                             campaign_data: List[Dict[str, Any]], 
                             time_window_days: int = 30) -> Dict[str, Any]:
        """
        Analyzes a campaign for threat actor attribution.
        
        Args:
            campaign_data: List of attack events in the campaign
            time_window_days: Time window for analysis
            
        Returns:
            Campaign analysis results
        """
        try:
            logger.info(f"Analyzing campaign with {len(campaign_data)} events")
            
            # Aggregate campaign characteristics
            campaign_characteristics = await self._aggregate_campaign_characteristics(campaign_data)
            
            # Analyze temporal patterns
            temporal_analysis = await self._analyze_temporal_patterns(campaign_data)
            
            # Analyze geographic patterns
            geographic_analysis = await self._analyze_geographic_patterns(campaign_data)
            
            # Perform attribution analysis
            attribution_results = await self.attribute_attack(campaign_characteristics)
            
            # Generate campaign report
            campaign_report = {
                "campaign_id": f"campaign_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "analysis_time": datetime.utcnow().isoformat(),
                "time_window_days": time_window_days,
                "total_events": len(campaign_data),
                "campaign_characteristics": campaign_characteristics,
                "temporal_analysis": temporal_analysis,
                "geographic_analysis": geographic_analysis,
                "attribution_results": attribution_results,
                "campaign_summary": await self._generate_campaign_summary(campaign_characteristics, attribution_results)
            }
            
            logger.info("Campaign analysis completed")
            return campaign_report
            
        except Exception as e:
            logger.error(f"Error analyzing campaign: {e}")
            return {
                "error": str(e),
                "analysis_time": datetime.utcnow().isoformat()
            }

    async def _aggregate_campaign_characteristics(self, campaign_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates characteristics across campaign events."""
        aggregated = {
            "ttps": set(),
            "tools": set(),
            "iocs": {
                "domains": set(),
                "ip_addresses": set(),
                "file_hashes": set(),
                "email_addresses": set()
            },
            "attack_phases": set(),
            "targets": set(),
            "motivations": set(),
            "severity_levels": set(),
            "event_types": set()
        }
        
        for event in campaign_data:
            # Aggregate TTPs
            if "ttps" in event:
                aggregated["ttps"].update(event["ttps"])
            
            # Aggregate tools
            if "tools" in event:
                aggregated["tools"].update(event["tools"])
            
            # Aggregate IOCs
            if "iocs" in event:
                for ioc_type, ioc_list in event["iocs"].items():
                    if ioc_type in aggregated["iocs"]:
                        aggregated["iocs"][ioc_type].update(ioc_list)
            
            # Aggregate other characteristics
            for field in ["attack_phases", "targets", "motivations", "severity_levels", "event_types"]:
                if field in event:
                    if isinstance(event[field], list):
                        aggregated[field].update(event[field])
                    else:
                        aggregated[field].add(event[field])
        
        # Convert sets to lists for JSON serialization
        for key, value in aggregated.items():
            if isinstance(value, set):
                aggregated[key] = list(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, set):
                        aggregated[key][sub_key] = list(sub_value)
        
        return aggregated

    async def _analyze_temporal_patterns(self, campaign_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes temporal patterns in campaign data."""
        if not campaign_data:
            return {"patterns": [], "summary": "No temporal data available"}
        
        # Extract timestamps
        timestamps = []
        for event in campaign_data:
            if "timestamp" in event:
                try:
                    timestamp = datetime.fromisoformat(event["timestamp"])
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue
        
        if not timestamps:
            return {"patterns": [], "summary": "No valid timestamps found"}
        
        # Analyze patterns
        timestamps.sort()
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 for i in range(len(timestamps)-1)]
        
        analysis = {
            "total_events": len(timestamps),
            "time_span_hours": (timestamps[-1] - timestamps[0]).total_seconds() / 3600,
            "average_interval_hours": np.mean(time_diffs) if time_diffs else 0,
            "median_interval_hours": np.median(time_diffs) if time_diffs else 0,
            "patterns": []
        }
        
        # Detect patterns
        if analysis["average_interval_hours"] < 1:
            analysis["patterns"].append("High frequency attacks (sub-hourly)")
        elif analysis["average_interval_hours"] < 24:
            analysis["patterns"].append("Daily attack pattern")
        elif analysis["average_interval_hours"] < 168:  # 1 week
            analysis["patterns"].append("Weekly attack pattern")
        else:
            analysis["patterns"].append("Sporadic attack pattern")
        
        # Analyze time of day patterns
        hours = [t.hour for t in timestamps]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
        analysis["most_active_hour"] = most_active_hour
        
        if 9 <= most_active_hour <= 17:
            analysis["patterns"].append("Business hours activity")
        elif 18 <= most_active_hour <= 23 or 0 <= most_active_hour <= 6:
            analysis["patterns"].append("Off-hours activity")
        
        return analysis

    async def _analyze_geographic_patterns(self, campaign_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes geographic patterns in campaign data."""
        if not campaign_data:
            return {"patterns": [], "summary": "No geographic data available"}
        
        # Extract geographic indicators
        countries = []
        regions = []
        ip_ranges = []
        
        for event in campaign_data:
            if "source_country" in event:
                countries.append(event["source_country"])
            if "source_region" in event:
                regions.append(event["source_region"])
            if "source_ip" in event:
                ip_ranges.append(event["source_ip"])
        
        analysis = {
            "total_events": len(campaign_data),
            "countries": list(set(countries)),
            "regions": list(set(regions)),
            "ip_ranges": list(set(ip_ranges)),
            "patterns": []
        }
        
        # Analyze patterns
        if len(set(countries)) == 1:
            analysis["patterns"].append("Single country origin")
        elif len(set(countries)) <= 3:
            analysis["patterns"].append("Limited geographic spread")
        else:
            analysis["patterns"].append("Wide geographic spread")
        
        if "China" in countries:
            analysis["patterns"].append("Chinese origin indicators")
        if "Russia" in countries:
            analysis["patterns"].append("Russian origin indicators")
        if "North Korea" in countries:
            analysis["patterns"].append("North Korean origin indicators")
        
        return analysis

    async def _generate_campaign_summary(self, 
                                       characteristics: Dict[str, Any], 
                                       attribution_results: Dict[str, Any]) -> str:
        """Generates a summary of the campaign analysis."""
        summary_parts = []
        
        # Event count
        total_events = characteristics.get("total_events", 0)
        summary_parts.append(f"Campaign involving {total_events} events")
        
        # Attribution
        if attribution_results.get("high_confidence_attributions"):
            top_attribution = attribution_results["high_confidence_attributions"][0]
            threat_actor = top_attribution["threat_actor"]
            summary_parts.append(f"High confidence attribution to {threat_actor['name']}")
        elif attribution_results.get("medium_confidence_attributions"):
            top_attribution = attribution_results["medium_confidence_attributions"][0]
            threat_actor = top_attribution["threat_actor"]
            summary_parts.append(f"Medium confidence attribution to {threat_actor['name']}")
        else:
            summary_parts.append("No clear attribution identified")
        
        # TTPs
        ttps = characteristics.get("ttps", [])
        if ttps:
            summary_parts.append(f"Utilizing {len(ttps)} TTPs")
        
        # Targets
        targets = characteristics.get("targets", [])
        if targets:
            summary_parts.append(f"Targeting {', '.join(targets[:3])}{'...' if len(targets) > 3 else ''}")
        
        return ". ".join(summary_parts) + "."

    async def get_attribution_status(self) -> Dict[str, Any]:
        """Gets the current status of the attribution system."""
        return {
            "threat_actors": len(self.threat_actors),
            "ttp_database": len(self.ttp_database),
            "ioc_database": sum(len(iocs) for iocs in self.ioc_database.values()),
            "attack_patterns": sum(len(patterns) for patterns in self.attack_patterns.values()),
            "last_updated": datetime.utcnow().isoformat()
        }
