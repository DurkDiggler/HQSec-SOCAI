"""Bridge between MCP tools and analytics system for interactive security testing."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import numpy as np
import pandas as pd

from ..config import SETTINGS
from ..database import get_db, save_alert, save_incident

logger = logging.getLogger(__name__)

class MCPAnalyticsBridge:
    """
    Bridge between MCP tools and analytics system that enables
    interactive security testing and analysis from the dashboard.
    """

    def __init__(self):
        self.kali_mcp_url = SETTINGS.kali_mcp_url
        self.vuln_scanner_url = SETTINGS.vuln_scanner_url
        self.mcp_timeout = SETTINGS.mcp_timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.mcp_timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def run_security_scan(self, 
                              target: str, 
                              scan_type: str = "comprehensive",
                              options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs a security scan using MCP tools and correlates results with analytics.
        
        Args:
            target: Target IP, domain, or range to scan
            scan_type: Type of scan (nmap, vuln, web, network, comprehensive)
            options: Additional scan options
            
        Returns:
            Scan results with analytics correlation
        """
        try:
            logger.info(f"Starting {scan_type} security scan for target: {target}")
            
            # Initialize scan results
            scan_results = {
                "target": target,
                "scan_type": scan_type,
                "start_time": datetime.utcnow().isoformat(),
                "status": "running",
                "findings": [],
                "analytics": {},
                "recommendations": []
            }
            
            # Run appropriate scan based on type
            if scan_type == "nmap":
                findings = await self._run_nmap_scan(target, options or {})
            elif scan_type == "vuln":
                findings = await self._run_vulnerability_scan(target, options or {})
            elif scan_type == "web":
                findings = await self._run_web_scan(target, options or {})
            elif scan_type == "network":
                findings = await self._run_network_scan(target, options or {})
            elif scan_type == "comprehensive":
                findings = await self._run_comprehensive_scan(target, options or {})
            else:
                raise ValueError(f"Unknown scan type: {scan_type}")
            
            scan_results["findings"] = findings
            scan_results["status"] = "completed"
            scan_results["end_time"] = datetime.utcnow().isoformat()
            
            # Correlate findings with analytics
            analytics_results = await self._correlate_scan_findings(findings, target)
            scan_results["analytics"] = analytics_results
            
            # Generate recommendations
            recommendations = await self._generate_scan_recommendations(findings, analytics_results)
            scan_results["recommendations"] = recommendations
            
            # Save findings to database
            await self._save_scan_findings(scan_results)
            
            logger.info(f"Security scan completed: {len(findings)} findings")
            return scan_results
            
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            return {
                "target": target,
                "scan_type": scan_type,
                "status": "failed",
                "error": str(e),
                "start_time": datetime.utcnow().isoformat()
            }

    async def _run_nmap_scan(self, target: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Runs Nmap scan via MCP."""
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            
            # Prepare Nmap scan request
            scan_request = {
                "target": target,
                "scan_type": "nmap",
                "options": {
                    "ports": options.get("ports", "1-1000"),
                    "timing": options.get("timing", "T4"),
                    "service_detection": options.get("service_detection", True),
                    "os_detection": options.get("os_detection", True),
                    "script_scan": options.get("script_scan", True)
                }
            }
            
            # Send request to Kali MCP
            async with self.session.post(
                f"{self.kali_mcp_url}/api/v1/tools/nmap",
                json=scan_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_nmap_results(result)
                else:
                    raise Exception(f"Nmap scan failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error running Nmap scan: {e}")
            return []

    async def _run_vulnerability_scan(self, target: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Runs vulnerability scan via MCP."""
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            
            # Prepare vulnerability scan request
            scan_request = {
                "target": target,
                "scan_type": "vulnerability",
                "options": {
                    "intensity": options.get("intensity", "medium"),
                    "plugins": options.get("plugins", []),
                    "timeout": options.get("timeout", 300)
                }
            }
            
            # Send request to vulnerability scanner MCP
            async with self.session.post(
                f"{self.vuln_scanner_url}/api/v1/scan",
                json=scan_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_vulnerability_results(result)
                else:
                    raise Exception(f"Vulnerability scan failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error running vulnerability scan: {e}")
            return []

    async def _run_web_scan(self, target: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Runs web application scan via MCP."""
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            
            # Prepare web scan request
            scan_request = {
                "target": target,
                "scan_type": "web",
                "options": {
                    "crawl_depth": options.get("crawl_depth", 3),
                    "scan_types": options.get("scan_types", ["sql_injection", "xss", "csrf"]),
                    "authentication": options.get("authentication", None)
                }
            }
            
            # Send request to Kali MCP
            async with self.session.post(
                f"{self.kali_mcp_url}/api/v1/tools/web_scanner",
                json=scan_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_web_scan_results(result)
                else:
                    raise Exception(f"Web scan failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error running web scan: {e}")
            return []

    async def _run_network_scan(self, target: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Runs network discovery scan via MCP."""
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            
            # Prepare network scan request
            scan_request = {
                "target": target,
                "scan_type": "network",
                "options": {
                    "discovery_methods": options.get("discovery_methods", ["ping", "arp", "dns"]),
                    "port_scan": options.get("port_scan", True),
                    "service_detection": options.get("service_detection", True)
                }
            }
            
            # Send request to Kali MCP
            async with self.session.post(
                f"{self.kali_mcp_url}/api/v1/tools/network_scanner",
                json=scan_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._parse_network_scan_results(result)
                else:
                    raise Exception(f"Network scan failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error running network scan: {e}")
            return []

    async def _run_comprehensive_scan(self, target: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Runs comprehensive security scan combining multiple tools."""
        try:
            all_findings = []
            
            # Run Nmap scan
            nmap_findings = await self._run_nmap_scan(target, options)
            all_findings.extend(nmap_findings)
            
            # Run vulnerability scan
            vuln_findings = await self._run_vulnerability_scan(target, options)
            all_findings.extend(vuln_findings)
            
            # Run web scan if target appears to be a web service
            if any(finding.get("service", "").lower() in ["http", "https", "www"] for finding in nmap_findings):
                web_findings = await self._run_web_scan(target, options)
                all_findings.extend(web_findings)
            
            # Run network scan
            network_findings = await self._run_network_scan(target, options)
            all_findings.extend(network_findings)
            
            return all_findings
            
        except Exception as e:
            logger.error(f"Error running comprehensive scan: {e}")
            return []

    def _parse_nmap_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses Nmap scan results."""
        findings = []
        
        for host in result.get("hosts", []):
            for port in host.get("ports", []):
                finding = {
                    "type": "port_scan",
                    "target": host.get("ip", "unknown"),
                    "port": port.get("port", 0),
                    "protocol": port.get("protocol", "tcp"),
                    "state": port.get("state", "unknown"),
                    "service": port.get("service", {}).get("name", "unknown"),
                    "version": port.get("service", {}).get("version", ""),
                    "severity": self._determine_port_severity(port),
                    "description": f"Port {port.get('port')} is {port.get('state')}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                findings.append(finding)
        
        return findings

    def _parse_vulnerability_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses vulnerability scan results."""
        findings = []
        
        for vuln in result.get("vulnerabilities", []):
            finding = {
                "type": "vulnerability",
                "target": vuln.get("target", "unknown"),
                "cve_id": vuln.get("cve_id", ""),
                "name": vuln.get("name", "Unknown Vulnerability"),
                "description": vuln.get("description", ""),
                "severity": vuln.get("severity", "medium"),
                "cvss_score": vuln.get("cvss_score", 0.0),
                "port": vuln.get("port", 0),
                "service": vuln.get("service", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
            findings.append(finding)
        
        return findings

    def _parse_web_scan_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses web application scan results."""
        findings = []
        
        for issue in result.get("issues", []):
            finding = {
                "type": "web_vulnerability",
                "target": issue.get("url", "unknown"),
                "vulnerability_type": issue.get("type", "unknown"),
                "name": issue.get("name", "Web Vulnerability"),
                "description": issue.get("description", ""),
                "severity": issue.get("severity", "medium"),
                "parameter": issue.get("parameter", ""),
                "method": issue.get("method", "GET"),
                "timestamp": datetime.utcnow().isoformat()
            }
            findings.append(finding)
        
        return findings

    def _parse_network_scan_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses network discovery scan results."""
        findings = []
        
        for device in result.get("devices", []):
            finding = {
                "type": "network_device",
                "target": device.get("ip", "unknown"),
                "mac_address": device.get("mac", ""),
                "hostname": device.get("hostname", ""),
                "os": device.get("os", ""),
                "vendor": device.get("vendor", ""),
                "severity": "info",
                "description": f"Network device discovered: {device.get('hostname', device.get('ip'))}",
                "timestamp": datetime.utcnow().isoformat()
            }
            findings.append(finding)
        
        return findings

    def _determine_port_severity(self, port: Dict[str, Any]) -> str:
        """Determines severity based on port information."""
        port_num = port.get("port", 0)
        service = port.get("service", {}).get("name", "").lower()
        state = port.get("state", "").lower()
        
        if state != "open":
            return "info"
        
        # High-risk ports
        if port_num in [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5900]:
            return "high"
        
        # Medium-risk ports
        if port_num in [135, 139, 445, 1433, 1521, 3306, 5432, 6379, 27017]:
            return "medium"
        
        # Service-based severity
        if service in ["ftp", "telnet", "rlogin", "rsh"]:
            return "high"
        elif service in ["mysql", "postgresql", "mongodb", "redis"]:
            return "medium"
        
        return "low"

    async def _correlate_scan_findings(self, 
                                     findings: List[Dict[str, Any]], 
                                     target: str) -> Dict[str, Any]:
        """Correlates scan findings with analytics system."""
        try:
            correlation_results = {
                "threat_level": "low",
                "risk_score": 0.0,
                "vulnerability_count": 0,
                "high_severity_count": 0,
                "service_count": 0,
                "attack_surface": [],
                "recommendations": []
            }
            
            if not findings:
                return correlation_results
            
            # Count findings by type and severity
            vuln_count = len([f for f in findings if f.get("type") == "vulnerability"])
            high_severity = len([f for f in findings if f.get("severity") == "high"])
            services = len(set(f.get("service", "") for f in findings if f.get("service")))
            
            correlation_results["vulnerability_count"] = vuln_count
            correlation_results["high_severity_count"] = high_severity
            correlation_results["service_count"] = services
            
            # Calculate risk score
            risk_score = 0.0
            for finding in findings:
                severity = finding.get("severity", "low")
                if severity == "high":
                    risk_score += 3
                elif severity == "medium":
                    risk_score += 2
                elif severity == "low":
                    risk_score += 1
            
            # Normalize risk score
            max_possible_score = len(findings) * 3
            if max_possible_score > 0:
                correlation_results["risk_score"] = min(risk_score / max_possible_score, 1.0)
            
            # Determine threat level
            if correlation_results["risk_score"] >= 0.8:
                correlation_results["threat_level"] = "critical"
            elif correlation_results["risk_score"] >= 0.6:
                correlation_results["threat_level"] = "high"
            elif correlation_results["risk_score"] >= 0.4:
                correlation_results["threat_level"] = "medium"
            else:
                correlation_results["threat_level"] = "low"
            
            # Identify attack surface
            attack_surface = []
            for finding in findings:
                if finding.get("type") == "port_scan" and finding.get("state") == "open":
                    attack_surface.append({
                        "port": finding.get("port"),
                        "service": finding.get("service"),
                        "version": finding.get("version")
                    })
            
            correlation_results["attack_surface"] = attack_surface
            
            return correlation_results
            
        except Exception as e:
            logger.error(f"Error correlating scan findings: {e}")
            return {"error": str(e)}

    async def _generate_scan_recommendations(self, 
                                           findings: List[Dict[str, Any]], 
                                           analytics: Dict[str, Any]) -> List[str]:
        """Generates recommendations based on scan findings and analytics."""
        recommendations = []
        
        if not findings:
            recommendations.append("No security issues found in scan")
            return recommendations
        
        # Vulnerability-based recommendations
        vuln_findings = [f for f in findings if f.get("type") == "vulnerability"]
        if vuln_findings:
            recommendations.append(f"Found {len(vuln_findings)} vulnerabilities - prioritize patching")
            
            high_severity_vulns = [f for f in vuln_findings if f.get("severity") == "high"]
            if high_severity_vulns:
                recommendations.append(f"CRITICAL: {len(high_severity_vulns)} high-severity vulnerabilities require immediate attention")
        
        # Port-based recommendations
        open_ports = [f for f in findings if f.get("type") == "port_scan" and f.get("state") == "open"]
        if open_ports:
            recommendations.append(f"Found {len(open_ports)} open ports - review and close unnecessary services")
            
            risky_ports = [f for f in open_ports if f.get("port") in [21, 23, 135, 139, 445]]
            if risky_ports:
                recommendations.append("WARNING: Found potentially risky open ports (FTP, Telnet, SMB)")
        
        # Web vulnerability recommendations
        web_findings = [f for f in findings if f.get("type") == "web_vulnerability"]
        if web_findings:
            recommendations.append(f"Found {len(web_findings)} web application vulnerabilities - review web security")
        
        # General recommendations
        if analytics.get("threat_level") in ["high", "critical"]:
            recommendations.append("High threat level detected - implement additional security controls")
            recommendations.append("Consider network segmentation and access controls")
        
        if analytics.get("service_count", 0) > 10:
            recommendations.append("Large attack surface detected - consider service reduction")
        
        return recommendations

    async def _save_scan_findings(self, scan_results: Dict[str, Any]):
        """Saves scan findings to the database."""
        try:
            with get_db() as db:
                # Save each finding as an alert
                for finding in scan_results.get("findings", []):
                    alert_data = {
                        "event_type": finding.get("type", "security_scan"),
                        "severity": finding.get("severity", "medium"),
                        "message": finding.get("description", ""),
                        "source_ip": finding.get("target", ""),
                        "timestamp": finding.get("timestamp", datetime.utcnow().isoformat()),
                        "metadata": {
                            "scan_type": scan_results.get("scan_type"),
                            "finding_details": finding
                        }
                    }
                    save_alert(db, alert_data)
                
                # Create incident if high severity findings
                high_severity_count = scan_results.get("analytics", {}).get("high_severity_count", 0)
                if high_severity_count > 0:
                    incident_data = {
                        "incident_type": "security_scan_findings",
                        "severity": "high" if high_severity_count > 3 else "medium",
                        "title": f"Security scan findings for {scan_results.get('target')}",
                        "description": f"Found {high_severity_count} high-severity security issues",
                        "status": "open",
                        "assigned_to": None,
                        "metadata": {
                            "scan_results": scan_results
                        }
                    }
                    save_incident(db, incident_data)
            
            logger.info(f"Saved {len(scan_results.get('findings', []))} scan findings to database")
            
        except Exception as e:
            logger.error(f"Error saving scan findings: {e}")

    async def get_available_tools(self) -> Dict[str, Any]:
        """Gets available MCP tools and their capabilities."""
        return {
            "kali_tools": {
                "nmap": {
                    "name": "Nmap Network Scanner",
                    "description": "Network discovery and port scanning",
                    "capabilities": ["port_scan", "service_detection", "os_detection", "script_scan"]
                },
                "web_scanner": {
                    "name": "Web Application Scanner",
                    "description": "Web application vulnerability scanning",
                    "capabilities": ["sql_injection", "xss", "csrf", "directory_traversal"]
                },
                "network_scanner": {
                    "name": "Network Discovery Scanner",
                    "description": "Network device discovery and enumeration",
                    "capabilities": ["device_discovery", "mac_address_resolution", "os_fingerprinting"]
                }
            },
            "vulnerability_tools": {
                "vuln_scanner": {
                    "name": "Vulnerability Scanner",
                    "description": "Comprehensive vulnerability assessment",
                    "capabilities": ["cve_scanning", "plugin_scanning", "risk_assessment"]
                }
            }
        }

    async def get_scan_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets scan history from the database."""
        try:
            with get_db() as db:
                # This would query scan history from the database
                # For now, return empty list
                return []
        except Exception as e:
            logger.error(f"Error getting scan history: {e}")
            return []

    async def get_mcp_status(self) -> Dict[str, Any]:
        """Gets MCP server status and connectivity."""
        try:
            status = {
                "kali_mcp": {"status": "unknown", "url": self.kali_mcp_url},
                "vuln_scanner": {"status": "unknown", "url": self.vuln_scanner_url},
                "last_check": datetime.utcnow().isoformat()
            }
            
            # Check Kali MCP connectivity
            try:
                if self.session:
                    async with self.session.get(f"{self.kali_mcp_url}/health") as response:
                        status["kali_mcp"]["status"] = "online" if response.status == 200 else "offline"
            except:
                status["kali_mcp"]["status"] = "offline"
            
            # Check vulnerability scanner connectivity
            try:
                if self.session:
                    async with self.session.get(f"{self.vuln_scanner_url}/health") as response:
                        status["vuln_scanner"]["status"] = "online" if response.status == 200 else "offline"
            except:
                status["vuln_scanner"]["status"] = "offline"
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking MCP status: {e}")
            return {
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
