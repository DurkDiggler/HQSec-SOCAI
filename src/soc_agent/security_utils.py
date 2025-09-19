"""Security utilities for input validation and sanitization."""

import re
import html
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class SecurityValidator:
    """Security validation utilities."""
    
    # Dangerous patterns for XSS prevention
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"exec\s*\(",
        r"expression\s*\(",
        r"vbscript:",
        r"data:text/html",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
        r"(\b(OR|AND)\s+\".*\"\s*=\s*\".*\")",
        r"(--|#|\/\*|\*\/)",
        r"(\b(UNION|UNION ALL)\b)",
        r"(\b(CHAR|ASCII|SUBSTRING|LEN|LENGTH)\b)",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """Sanitize a string by removing dangerous content."""
        if not isinstance(value, str):
            return str(value)
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # HTML escape
        value = html.escape(value, quote=True)
        
        # Remove dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE | re.DOTALL)
        
        return value.strip()
    
    @classmethod
    def validate_ip_address(cls, ip: str) -> bool:
        """Validate IP address format."""
        if not ip:
            return True  # Allow None/empty
        
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format."""
        if not url:
            return True  # Allow None/empty
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """Validate username format."""
        if not username:
            return True  # Allow None/empty
        
        # Username should be alphanumeric with dots, underscores, hyphens
        pattern = r"^[a-zA-Z0-9._-]+$"
        return bool(re.match(pattern, username)) and len(username) <= 255
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format."""
        if not email:
            return True  # Allow None/empty
        
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection."""
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """Check for path traversal attempts."""
        if not isinstance(value, str):
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_string_length: int = 10000) -> Dict[str, Any]:
        """Sanitize all string values in a dictionary."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value, max_string_length)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, max_string_length)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_string(item, max_string_length) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    @classmethod
    def validate_event_data(cls, event_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate event data and return validation errors."""
        errors = {}
        
        # Validate IP address
        if "ip" in event_data and event_data["ip"]:
            if not cls.validate_ip_address(event_data["ip"]):
                errors.setdefault("ip", []).append("Invalid IP address format")
        
        # Validate username
        if "username" in event_data and event_data["username"]:
            if not cls.validate_username(event_data["username"]):
                errors.setdefault("username", []).append("Invalid username format")
        
        # Check for SQL injection in text fields
        text_fields = ["message", "event_type", "source", "category"]
        for field in text_fields:
            if field in event_data and event_data[field]:
                if cls.check_sql_injection(event_data[field]):
                    errors.setdefault(field, []).append("Potential SQL injection detected")
        
        # Check for path traversal
        if "source" in event_data and event_data["source"]:
            if cls.check_path_traversal(event_data["source"]):
                errors.setdefault("source", []).append("Potential path traversal detected")
        
        return errors


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for HTTP responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


class RateLimitConfig:
    """Rate limiting configuration for different endpoints."""
    
    # Rate limit configurations per endpoint
    ENDPOINT_LIMITS = {
        "/api/v1/alerts": {"requests": 200, "window": 3600},
        "/api/v1/ai/analyze": {"requests": 50, "window": 3600},
        "/api/v1/mcp/scan": {"requests": 10, "window": 3600},
        "/api/v1/database/optimize": {"requests": 5, "window": 3600},
        "/api/v1/settings/test-email": {"requests": 3, "window": 300},
        "/api/v1/settings/test-intel": {"requests": 10, "window": 300},
        "/webhook": {"requests": 1000, "window": 3600},
    }
    
    @classmethod
    def get_limit_for_endpoint(cls, endpoint: str) -> Dict[str, int]:
        """Get rate limit configuration for an endpoint."""
        return cls.ENDPOINT_LIMITS.get(endpoint, {"requests": 100, "window": 3600})
