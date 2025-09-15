from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import SETTINGS
from .providers import abuseipdb, otx, virustotal

logger = logging.getLogger(__name__)


class IntelClient:
    def __init__(self):
        """Initialize the intelligence client with caching and retry logic."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=SETTINGS.max_retries,
            backoff_factor=SETTINGS.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Simple in-memory cache (in production, use Redis or similar)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

    def _get_cached_result(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid."""
        if not SETTINGS.enable_caching:
            return None
            
        if ip in self._cache:
            cache_time = self._cache_timestamps.get(ip, 0)
            if time.time() - cache_time < SETTINGS.ioc_cache_ttl:
                logger.debug(f"Cache hit for IP: {ip}")
                return self._cache[ip]
            else:
                # Remove expired entry
                self._cache.pop(ip, None)
                self._cache_timestamps.pop(ip, None)
        return None

    def _cache_result(self, ip: str, result: Dict[str, Any]) -> None:
        """Cache the result."""
        if SETTINGS.enable_caching:
            self._cache[ip] = result
            self._cache_timestamps[ip] = time.time()
            logger.debug(f"Cached result for IP: {ip}")

    def enrich_ip(self, ip: str) -> Dict[str, Any]:
        """Enrich IP with threat intelligence from multiple sources."""
        # Check cache first
        cached_result = self._get_cached_result(ip)
        if cached_result:
            return cached_result

        results: Dict[str, Any] = {
            "indicator": ip, 
            "sources": {}, 
            "score": 0, 
            "labels": [],
            "enriched_at": time.time()
        }
        votes: List[int] = []
        errors: List[str] = []

        # OTX lookup
        if SETTINGS.otx_api_key:
            try:
                data = otx.lookup_ip(self.session, ip, SETTINGS.http_timeout)
                results["sources"]["otx"] = data
                pulses = len(data.get("pulse_info", {}).get("pulses", []))
                if pulses:
                    score = min(30, 10 + pulses)
                    votes.append(score)
                    logger.debug(f"OTX score for {ip}: {score}")
            except Exception as e:
                error_msg = f"OTX lookup failed: {str(e)}"
                errors.append(error_msg)
                results["sources"]["otx_error"] = error_msg
                logger.warning(error_msg)

        # VirusTotal lookup
        if SETTINGS.vt_api_key:
            try:
                data = virustotal.lookup_ip(self.session, ip, SETTINGS.http_timeout)
                results["sources"]["virustotal"] = data
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = int(stats.get("malicious", 0))
                suspicious = int(stats.get("suspicious", 0))
                if malicious or suspicious:
                    score = min(40, 5 * (malicious + suspicious))
                    votes.append(score)
                    logger.debug(f"VT score for {ip}: {score}")
            except Exception as e:
                error_msg = f"VirusTotal lookup failed: {str(e)}"
                errors.append(error_msg)
                results["sources"]["vt_error"] = error_msg
                logger.warning(error_msg)

        # AbuseIPDB lookup
        if SETTINGS.abuseipdb_api_key:
            try:
                data = abuseipdb.lookup_ip(self.session, ip, SETTINGS.http_timeout)
                results["sources"]["abuseipdb"] = data
                score = int(data.get("data", {}).get("abuseConfidenceScore", 0))
                if score:
                    score = min(50, score)
                    votes.append(score)
                    logger.debug(f"AbuseIPDB score for {ip}: {score}")
            except Exception as e:
                error_msg = f"AbuseIPDB lookup failed: {str(e)}"
                errors.append(error_msg)
                results["sources"]["abuseipdb_error"] = error_msg
                logger.warning(error_msg)

        # Calculate final score
        agg = max(votes) if votes else 0
        results["score"] = agg
        results["errors"] = errors
        
        # Determine labels based on score
        if agg >= 70:
            results["labels"].append("malicious")
        elif agg >= 40:
            results["labels"].append("suspicious")
        elif agg > 0:
            results["labels"].append("low_risk")
        else:
            results["labels"].append("unknown")

        # Cache the result
        self._cache_result(ip, results)
        
        logger.info(f"Enriched IP {ip}: score={agg}, labels={results['labels']}")
        return results

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")


intel_client = IntelClient()
