"""Threat intelligence feed integration and IOC management."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..config import SETTINGS
from ..database import get_db, get_historical_alerts, get_historical_incidents

logger = logging.getLogger(__name__)

class ThreatIntelligenceFeed:
    """
    Threat intelligence feed integration system that collects,
    processes, and correlates threat intelligence data.
    """

    def __init__(self):
        self.feeds = self._load_threat_intelligence_feeds()
        self.ioc_database = {}
        self.threat_actors = {}
        self.attack_patterns = {}
        self.last_update = {}

    def _load_threat_intelligence_feeds(self) -> Dict[str, Dict[str, Any]]:
        """Loads threat intelligence feed configurations."""
        return {
            "mitre_attack": {
                "name": "MITRE ATT&CK",
                "url": "https://attack.mitre.org/",
                "type": "tactics_techniques",
                "update_frequency": "daily",
                "enabled": True,
                "api_key": None,
                "description": "MITRE ATT&CK framework for tactics and techniques"
            },
            "nvd": {
                "name": "National Vulnerability Database",
                "url": "https://nvd.nist.gov/",
                "type": "vulnerabilities",
                "update_frequency": "daily",
                "enabled": True,
                "api_key": None,
                "description": "NIST National Vulnerability Database"
            },
            "virustotal": {
                "name": "VirusTotal",
                "url": "https://www.virustotal.com/",
                "type": "iocs",
                "update_frequency": "hourly",
                "enabled": True,
                "api_key": SETTINGS.virustotal_api_key,
                "description": "VirusTotal threat intelligence"
            },
            "abuse_ch": {
                "name": "Abuse.ch",
                "url": "https://abuse.ch/",
                "type": "malware_iocs",
                "update_frequency": "hourly",
                "enabled": True,
                "api_key": None,
                "description": "Abuse.ch malware and botnet intelligence"
            },
            "misp": {
                "name": "MISP",
                "url": SETTINGS.misp_url,
                "type": "iocs",
                "update_frequency": "hourly",
                "enabled": True,
                "api_key": SETTINGS.misp_api_key,
                "description": "MISP threat intelligence sharing platform"
            },
            "opencti": {
                "name": "OpenCTI",
                "url": SETTINGS.opencti_url,
                "type": "threat_intelligence",
                "update_frequency": "hourly",
                "enabled": True,
                "api_key": SETTINGS.opencti_api_key,
                "description": "OpenCTI threat intelligence platform"
            }
        }

    async def collect_threat_intelligence(self, 
                                        feed_names: List[str] = None,
                                        force_update: bool = False) -> Dict[str, Any]:
        """
        Collects threat intelligence from configured feeds.
        
        Args:
            feed_names: Specific feeds to collect from (all if None)
            force_update: Force update even if recently updated
            
        Returns:
            Collection results and statistics
        """
        try:
            logger.info("Starting threat intelligence collection")
            
            if feed_names is None:
                feed_names = list(self.feeds.keys())
            
            collection_results = {
                "collection_time": datetime.utcnow().isoformat(),
                "feeds_processed": 0,
                "feeds_successful": 0,
                "feeds_failed": 0,
                "total_iocs": 0,
                "total_threat_actors": 0,
                "total_attack_patterns": 0,
                "feed_results": {}
            }
            
            for feed_name in feed_names:
                if feed_name not in self.feeds:
                    logger.warning(f"Unknown feed: {feed_name}")
                    continue
                
                feed_config = self.feeds[feed_name]
                if not feed_config.get("enabled", False):
                    logger.info(f"Feed {feed_name} is disabled, skipping")
                    continue
                
                # Check if update is needed
                if not force_update and self._is_recently_updated(feed_name):
                    logger.info(f"Feed {feed_name} recently updated, skipping")
                    continue
                
                collection_results["feeds_processed"] += 1
                
                try:
                    feed_result = await self._collect_from_feed(feed_name, feed_config)
                    collection_results["feed_results"][feed_name] = feed_result
                    
                    if feed_result["success"]:
                        collection_results["feeds_successful"] += 1
                        collection_results["total_iocs"] += feed_result.get("iocs_collected", 0)
                        collection_results["total_threat_actors"] += feed_result.get("threat_actors_collected", 0)
                        collection_results["total_attack_patterns"] += feed_result.get("attack_patterns_collected", 0)
                    else:
                        collection_results["feeds_failed"] += 1
                    
                    # Update last update time
                    self.last_update[feed_name] = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Error collecting from feed {feed_name}: {e}")
                    collection_results["feeds_failed"] += 1
                    collection_results["feed_results"][feed_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            logger.info(f"Threat intelligence collection completed: {collection_results['feeds_successful']}/{collection_results['feeds_processed']} successful")
            return collection_results
            
        except Exception as e:
            logger.error(f"Error in threat intelligence collection: {e}")
            return {
                "error": str(e),
                "collection_time": datetime.utcnow().isoformat()
            }

    def _is_recently_updated(self, feed_name: str) -> bool:
        """Checks if a feed was recently updated."""
        if feed_name not in self.last_update:
            return False
        
        last_update = self.last_update[feed_name]
        update_frequency = self.feeds[feed_name].get("update_frequency", "daily")
        
        # Convert frequency to hours
        frequency_hours = {
            "hourly": 1,
            "daily": 24,
            "weekly": 168
        }.get(update_frequency, 24)
        
        time_since_update = datetime.utcnow() - last_update
        return time_since_update.total_seconds() < (frequency_hours * 3600)

    async def _collect_from_feed(self, feed_name: str, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects data from a specific threat intelligence feed."""
        try:
            feed_type = feed_config["type"]
            
            if feed_type == "tactics_techniques":
                return await self._collect_mitre_attack(feed_config)
            elif feed_type == "vulnerabilities":
                return await self._collect_nvd(feed_config)
            elif feed_type == "iocs":
                return await self._collect_iocs(feed_config)
            elif feed_type == "malware_iocs":
                return await self._collect_malware_iocs(feed_config)
            elif feed_type == "threat_intelligence":
                return await self._collect_threat_intelligence(feed_config)
            else:
                return {"success": False, "error": f"Unknown feed type: {feed_type}"}
                
        except Exception as e:
            logger.error(f"Error collecting from feed {feed_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _collect_mitre_attack(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects MITRE ATT&CK data."""
        try:
            # This would typically use the MITRE ATT&CK API
            # For now, we'll simulate the collection
            attack_patterns = {
                "T1055": {
                    "id": "T1055",
                    "name": "Process Injection",
                    "description": "Adversaries may inject code into processes",
                    "tactics": ["Defense Evasion", "Privilege Escalation"],
                    "techniques": ["DLL Injection", "Process Hollowing"]
                },
                "T1059": {
                    "id": "T1059",
                    "name": "Command and Scripting Interpreter",
                    "description": "Adversaries may abuse command and script interpreters",
                    "tactics": ["Execution"],
                    "techniques": ["PowerShell", "Command Prompt"]
                }
            }
            
            self.attack_patterns.update(attack_patterns)
            
            return {
                "success": True,
                "attack_patterns_collected": len(attack_patterns),
                "message": "MITRE ATT&CK data collected successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _collect_nvd(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects NVD vulnerability data."""
        try:
            # This would typically use the NVD API
            # For now, we'll simulate the collection
            vulnerabilities = {
                "CVE-2021-44228": {
                    "id": "CVE-2021-44228",
                    "name": "Apache Log4j Remote Code Execution",
                    "severity": "CRITICAL",
                    "cvss_score": 10.0,
                    "published_date": "2021-12-10"
                }
            }
            
            return {
                "success": True,
                "vulnerabilities_collected": len(vulnerabilities),
                "message": "NVD data collected successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _collect_iocs(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects IOC data from feeds."""
        try:
            # This would typically use the feed's API
            # For now, we'll simulate the collection
            iocs = {
                "domains": ["malicious1.com", "malicious2.com"],
                "ip_addresses": ["1.2.3.4", "5.6.7.8"],
                "file_hashes": ["a1b2c3d4e5f6...", "b2c3d4e5f6a1..."],
                "email_addresses": ["fake@malicious.com"]
            }
            
            # Update IOC database
            for ioc_type, ioc_list in iocs.items():
                if ioc_type not in self.ioc_database:
                    self.ioc_database[ioc_type] = set()
                self.ioc_database[ioc_type].update(ioc_list)
            
            return {
                "success": True,
                "iocs_collected": sum(len(ioc_list) for ioc_list in iocs.values()),
                "message": "IOC data collected successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _collect_malware_iocs(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects malware IOC data."""
        try:
            # This would typically use the feed's API
            # For now, we'll simulate the collection
            malware_iocs = {
                "domains": ["botnet1.com", "botnet2.com"],
                "ip_addresses": ["10.20.30.40", "50.60.70.80"],
                "file_hashes": ["c3d4e5f6a1b2...", "d4e5f6a1b2c3..."]
            }
            
            # Update IOC database
            for ioc_type, ioc_list in malware_iocs.items():
                if ioc_type not in self.ioc_database:
                    self.ioc_database[ioc_type] = set()
                self.ioc_database[ioc_type].update(ioc_list)
            
            return {
                "success": True,
                "iocs_collected": sum(len(ioc_list) for ioc_list in malware_iocs.values()),
                "message": "Malware IOC data collected successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _collect_threat_intelligence(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collects general threat intelligence data."""
        try:
            # This would typically use the feed's API
            # For now, we'll simulate the collection
            threat_actors = {
                "apt1": {
                    "id": "apt1",
                    "name": "APT1",
                    "aliases": ["Comment Crew"],
                    "country": "China",
                    "motivation": "Espionage"
                }
            }
            
            self.threat_actors.update(threat_actors)
            
            return {
                "success": True,
                "threat_actors_collected": len(threat_actors),
                "message": "Threat intelligence data collected successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def correlate_iocs(self, 
                           event_data: Dict[str, Any],
                           confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Correlates IOCs in event data with threat intelligence.
        
        Args:
            event_data: Event data to analyze
            confidence_threshold: Minimum confidence for correlation
            
        Returns:
            IOC correlation results
        """
        try:
            logger.info("Starting IOC correlation analysis")
            
            # Extract IOCs from event data
            event_iocs = await self._extract_iocs_from_event(event_data)
            
            # Correlate with threat intelligence
            correlation_results = {
                "event_id": event_data.get("id", "unknown"),
                "analysis_time": datetime.utcnow().isoformat(),
                "event_iocs": event_iocs,
                "correlations": [],
                "threat_indicators": [],
                "confidence_scores": {},
                "recommendations": []
            }
            
            # Check each IOC type
            for ioc_type, ioc_list in event_iocs.items():
                for ioc in ioc_list:
                    correlation = await self._correlate_single_ioc(ioc, ioc_type)
                    if correlation["confidence"] >= confidence_threshold:
                        correlation_results["correlations"].append(correlation)
                        correlation_results["threat_indicators"].append({
                            "ioc": ioc,
                            "type": ioc_type,
                            "threat_level": correlation["threat_level"],
                            "confidence": correlation["confidence"]
                        })
            
            # Calculate overall threat score
            if correlation_results["correlations"]:
                avg_confidence = np.mean([c["confidence"] for c in correlation_results["correlations"]])
                max_threat_level = max([c["threat_level"] for c in correlation_results["correlations"]])
                
                correlation_results["overall_threat_score"] = avg_confidence
                correlation_results["overall_threat_level"] = max_threat_level
            else:
                correlation_results["overall_threat_score"] = 0.0
                correlation_results["overall_threat_level"] = "Low"
            
            # Generate recommendations
            correlation_results["recommendations"] = await self._generate_ioc_recommendations(
                correlation_results["correlations"]
            )
            
            logger.info(f"IOC correlation completed: {len(correlation_results['correlations'])} correlations found")
            return correlation_results
            
        except Exception as e:
            logger.error(f"Error in IOC correlation: {e}")
            return {
                "error": str(e),
                "analysis_time": datetime.utcnow().isoformat()
            }

    async def _extract_iocs_from_event(self, event_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extracts IOCs from event data."""
        import re
        
        iocs = {
            "domains": [],
            "ip_addresses": [],
            "file_hashes": [],
            "email_addresses": [],
            "urls": []
        }
        
        # Extract text content
        text_content = f"{event_data.get('message', '')} {event_data.get('description', '')}"
        
        # Domain pattern
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, text_content)
        iocs["domains"] = list(set(domains))
        
        # IP address pattern
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text_content)
        iocs["ip_addresses"] = list(set(ips))
        
        # File hash patterns
        md5_pattern = r'\b[a-fA-F0-9]{32}\b'
        sha1_pattern = r'\b[a-fA-F0-9]{40}\b'
        sha256_pattern = r'\b[a-fA-F0-9]{64}\b'
        
        md5_hashes = re.findall(md5_pattern, text_content)
        sha1_hashes = re.findall(sha1_pattern, text_content)
        sha256_hashes = re.findall(sha256_pattern, text_content)
        
        iocs["file_hashes"] = list(set(md5_hashes + sha1_hashes + sha256_hashes))
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        iocs["email_addresses"] = list(set(emails))
        
        # URL pattern
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, text_content)
        iocs["urls"] = list(set(urls))
        
        return iocs

    async def _correlate_single_ioc(self, ioc: str, ioc_type: str) -> Dict[str, Any]:
        """Correlates a single IOC with threat intelligence."""
        correlation = {
            "ioc": ioc,
            "type": ioc_type,
            "confidence": 0.0,
            "threat_level": "Low",
            "sources": [],
            "threat_actors": [],
            "attack_patterns": [],
            "last_seen": None
        }
        
        # Check against IOC database
        if ioc_type in self.ioc_database and ioc in self.ioc_database[ioc_type]:
            correlation["confidence"] = 0.8
            correlation["threat_level"] = "High"
            correlation["sources"].append("Threat Intelligence Feed")
        
        # Check against threat actors
        for threat_actor_id, threat_actor in self.threat_actors.items():
            if ioc_type in threat_actor.get("iocs", {}):
                if ioc in threat_actor["iocs"][ioc_type]:
                    correlation["confidence"] = max(correlation["confidence"], 0.9)
                    correlation["threat_level"] = "Critical"
                    correlation["threat_actors"].append(threat_actor_id)
                    correlation["sources"].append(f"Threat Actor: {threat_actor['name']}")
        
        # Check against attack patterns
        for pattern_id, pattern in self.attack_patterns.items():
            if ioc_type in pattern.get("iocs", {}):
                if ioc in pattern["iocs"][ioc_type]:
                    correlation["confidence"] = max(correlation["confidence"], 0.7)
                    correlation["threat_level"] = "High"
                    correlation["attack_patterns"].append(pattern_id)
                    correlation["sources"].append(f"Attack Pattern: {pattern['name']}")
        
        return correlation

    async def _generate_ioc_recommendations(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generates recommendations based on IOC correlations."""
        recommendations = []
        
        if not correlations:
            recommendations.append("No threat indicators found in event data")
            return recommendations
        
        # Count by threat level
        threat_levels = [c["threat_level"] for c in correlations]
        critical_count = threat_levels.count("Critical")
        high_count = threat_levels.count("High")
        medium_count = threat_levels.count("Medium")
        
        if critical_count > 0:
            recommendations.append(f"CRITICAL: {critical_count} critical threat indicators found")
            recommendations.append("Immediate investigation and response required")
            recommendations.append("Consider escalating to incident response team")
        elif high_count > 0:
            recommendations.append(f"HIGH: {high_count} high-threat indicators found")
            recommendations.append("Priority investigation required")
            recommendations.append("Implement additional monitoring")
        elif medium_count > 0:
            recommendations.append(f"MEDIUM: {medium_count} medium-threat indicators found")
            recommendations.append("Standard investigation recommended")
            recommendations.append("Monitor for additional indicators")
        
        # Source-specific recommendations
        sources = [source for correlation in correlations for source in correlation["sources"]]
        if "Threat Intelligence Feed" in sources:
            recommendations.append("IOCs confirmed by threat intelligence feeds")
            recommendations.append("Consider sharing intelligence with other organizations")
        
        if any("Threat Actor:" in source for source in sources):
            recommendations.append("IOCs associated with known threat actors")
            recommendations.append("Review threat actor TTPs and indicators")
        
        if any("Attack Pattern:" in source for source in sources):
            recommendations.append("IOCs associated with known attack patterns")
            recommendations.append("Review MITRE ATT&CK techniques and procedures")
        
        return recommendations

    async def get_threat_intelligence_status(self) -> Dict[str, Any]:
        """Gets the current status of the threat intelligence system."""
        return {
            "feeds_configured": len(self.feeds),
            "feeds_enabled": len([f for f in self.feeds.values() if f.get("enabled", False)]),
            "ioc_database_size": sum(len(iocs) for iocs in self.ioc_database.values()),
            "threat_actors_count": len(self.threat_actors),
            "attack_patterns_count": len(self.attack_patterns),
            "last_updates": self.last_update,
            "last_updated": datetime.utcnow().isoformat()
        }
