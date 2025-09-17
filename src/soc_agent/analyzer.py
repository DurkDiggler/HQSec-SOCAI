from __future__ import annotations

import ipaddress
import logging
import re
from typing import Any, Dict, List, Optional

from .config import SETTINGS
from .intel import intel_client
from .ai.threat_analyzer import AIThreatAnalyzer

logger = logging.getLogger(__name__)

RULE_WEIGHTS = {
    "auth_failed": 15,
    "multiple_auth_failed": 25,
    "malware_detected": 40,
    "ransomware": 60,
    "port_scan": 15,
    "bruteforce": 35,
    "geo_anomaly": 20,
    "privilege_escalation": 50,
    "lateral_movement": 45,
    "exfil": 55,
    "data_exfiltration": 55,
    "suspicious_activity": 20,
    "network_anomaly": 15,
    "file_modification": 25,
    "process_injection": 45,
    "persistence_mechanism": 40,
}
SEVERITY_WEIGHT = 6

# Private IP ranges for filtering
PRIVATE_IP_RANGES = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("127.0.0.0/8"),
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local
]


def is_valid_ip(value: str) -> bool:
    """Validate IP address using ipaddress module (supports both IPv4 and IPv6)."""
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Check if IP is in private ranges."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            return any(ip_obj in network for network in PRIVATE_IP_RANGES)
        return False
    except ValueError:
        return False


def extract_iocs(event: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract IOCs from event data with improved validation and filtering."""
    ips: List[str] = []
    domains: List[str] = []
    
    # Extract IPs from known fields
    ip_fields = ("ip", "src_ip", "dst_ip", "attacker_ip", "host_ip", "source_ip", "dest_ip")
    for key in ip_fields:
        v = event.get(key)
        if isinstance(v, str) and is_valid_ip(v):
            ips.append(v)
    
    # Extract IPs from message using regex
    msg = event.get("message", "") or ""
    ip_matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", msg)
    for ip in ip_matches:
        if is_valid_ip(ip):
            ips.append(ip)
    
    # Extract domains from message
    domain_matches = re.findall(r"\b([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b", msg)
    domains.extend(domain_matches)
    
    # Remove duplicates and sort
    ips = sorted({ip for ip in ips if is_valid_ip(ip)})
    domains = sorted(set(domains))
    
    # Filter out private IPs if configured
    # Note: In production, you might want to keep private IPs for internal threat hunting
    # but filter them for external threat intelligence lookups
    if SETTINGS.enable_caching:  # Filter private IPs when caching is enabled
        ips = [ip for ip in ips if not is_private_ip(ip)]
    
    logger.debug(f"Extracted IOCs: {len(ips)} IPs, {len(domains)} domains")
    return {"ips": ips, "domains": domains}


def base_score(event: Dict[str, Any]) -> int:
    ev = (event.get("event_type") or "").lower()
    sev = int(event.get("severity") or 0)
    score = min(100, sev * SEVERITY_WEIGHT)
    score += RULE_WEIGHTS.get(ev, 0)
    raw = event.get("raw") or {}
    if isinstance(raw, dict):
        fail_count = int(raw.get("fail_count") or 0)
        if fail_count >= 5:
            score += min(20, 3 * (fail_count // 5))
        if raw.get("geo") in {"RU", "KP", "IR", "CN"}:
            score += 10
        if raw.get("new_admin_user"):
            score += 25
    return min(100, score)


def enrich_and_score(event: Dict[str, Any]) -> Dict[str, Any]:
    iocs = extract_iocs(event)
    intel_scores: List[int] = []
    intel_details: Dict[str, Any] = {"ips": [], "domains": []}

    for ip in iocs["ips"]:
        enriched = intel_client.enrich_ip(ip)
        intel_details["ips"].append(enriched)
        intel_scores.append(enriched.get("score", 0))

    bscore = base_score(event)
    isig = max(intel_scores) if intel_scores else 0
    final = min(100, int(round(0.6 * bscore + 0.4 * isig)))

    if final >= SETTINGS.score_high:
        category = "HIGH"
        action = "ticket"
    elif final >= SETTINGS.score_medium:
        category = "MEDIUM"
        action = "email"
    else:
        category = "LOW"
        action = "none"

    return {
        "iocs": iocs,
        "intel": intel_details,
        "scores": {"base": bscore, "intel": isig, "final": final},
        "category": category,
        "recommended_action": action,
    }


async def enrich_and_score_with_ai(event: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced analysis with AI integration."""
    # Get traditional analysis
    traditional_analysis = enrich_and_score(event)
    
    # Add AI analysis if enabled
    if SETTINGS.enable_ai_analysis:
        try:
            ai_analyzer = AIThreatAnalyzer()
            ai_analysis = await ai_analyzer.analyze_threat(event)
            
            # Combine traditional and AI analysis
            combined_analysis = traditional_analysis.copy()
            combined_analysis["ai_analysis"] = ai_analysis
            
            # Adjust final score based on AI confidence
            ai_confidence = ai_analysis.get("confidence_score", 50)
            traditional_score = traditional_analysis["scores"]["final"]
            
            # Weight AI analysis more heavily if confidence is high
            if ai_confidence >= 80:
                final_score = int(0.7 * ai_confidence + 0.3 * traditional_score)
            elif ai_confidence >= 60:
                final_score = int(0.5 * ai_confidence + 0.5 * traditional_score)
            else:
                final_score = int(0.3 * ai_confidence + 0.7 * traditional_score)
            
            combined_analysis["scores"]["final"] = min(100, final_score)
            combined_analysis["scores"]["ai_confidence"] = ai_confidence
            
            # Update category and action based on AI analysis
            if ai_analysis.get("risk_level") == "CRITICAL":
                combined_analysis["category"] = "CRITICAL"
                combined_analysis["recommended_action"] = "ticket"
            elif ai_analysis.get("risk_level") == "HIGH":
                combined_analysis["category"] = "HIGH"
                combined_analysis["recommended_action"] = "ticket"
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed, falling back to traditional: {e}")
            return traditional_analysis
    
    return traditional_analysis
