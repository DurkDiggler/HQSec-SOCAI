"""Request and response logging middleware for security and debugging."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app, log_body: bool = False, sensitive_headers: Optional[list] = None):
        super().__init__(app)
        self.log_body = log_body
        self.sensitive_headers = sensitive_headers or [
            "authorization", "x-api-key", "x-auth-token", "cookie", "set-cookie"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and response with logging."""
        start_time = time.time()
        
        # Log request
        await self._log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        await self._log_response(request, response, process_time)
        
        return response
    
    async def _log_request(self, request: Request):
        """Log incoming request details."""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Prepare headers (filter sensitive ones)
            headers = dict(request.headers)
            for header in self.sensitive_headers:
                if header.lower() in headers:
                    headers[header.lower()] = "***REDACTED***"
            
            # Prepare body if logging is enabled
            body = None
            if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = body_bytes.decode("utf-8")
                        # Truncate very large bodies
                        if len(body) > 10000:
                            body = body[:10000] + "... [TRUNCATED]"
                except Exception as e:
                    body = f"[ERROR reading body: {e}]"
            
            # Log request
            request_data = {
                "type": "request",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
                "headers": headers,
                "body": body,
                "timestamp": time.time()
            }
            
            logger.info(f"Request: {request.method} {request.url.path}", extra=request_data)
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def _log_response(self, request: Request, response: Response, process_time: float):
        """Log outgoing response details."""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Prepare headers (filter sensitive ones)
            headers = dict(response.headers)
            for header in self.sensitive_headers:
                if header.lower() in headers:
                    headers[header.lower()] = "***REDACTED***"
            
            # Log response
            response_data = {
                "type": "response",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": client_ip,
                "process_time": round(process_time, 4),
                "headers": headers,
                "timestamp": time.time()
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                logger.error(f"Response: {response.status_code} {request.method} {request.url.path}", extra=response_data)
            elif response.status_code >= 400:
                logger.warning(f"Response: {response.status_code} {request.method} {request.url.path}", extra=response_data)
            else:
                logger.info(f"Response: {response.status_code} {request.method} {request.url.path}", extra=response_data)
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


class SecurityEventLogger:
    """Logger for security-related events."""
    
    @staticmethod
    def log_authentication_attempt(
        username: str,
        success: bool,
        client_ip: str,
        user_agent: str,
        reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        event_data = {
            "event_type": "authentication_attempt",
            "username": username,
            "success": success,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "reason": reason,
            "timestamp": time.time()
        }
        
        if success:
            logger.info(f"Authentication successful for user: {username}", extra=event_data)
        else:
            logger.warning(f"Authentication failed for user: {username}", extra=event_data)
    
    @staticmethod
    def log_authorization_failure(
        username: str,
        resource: str,
        action: str,
        client_ip: str,
        reason: str
    ):
        """Log authorization failures."""
        event_data = {
            "event_type": "authorization_failure",
            "username": username,
            "resource": resource,
            "action": action,
            "client_ip": client_ip,
            "reason": reason,
            "timestamp": time.time()
        }
        
        logger.warning(f"Authorization failed: {username} tried to {action} {resource}", extra=event_data)
    
    @staticmethod
    def log_rate_limit_exceeded(
        client_ip: str,
        endpoint: str,
        limit: int,
        window: int
    ):
        """Log rate limit violations."""
        event_data = {
            "event_type": "rate_limit_exceeded",
            "client_ip": client_ip,
            "endpoint": endpoint,
            "limit": limit,
            "window": window,
            "timestamp": time.time()
        }
        
        logger.warning(f"Rate limit exceeded: {client_ip} on {endpoint}", extra=event_data)
    
    @staticmethod
    def log_suspicious_activity(
        client_ip: str,
        activity_type: str,
        details: Dict[str, Any],
        severity: str = "medium"
    ):
        """Log suspicious activities."""
        event_data = {
            "event_type": "suspicious_activity",
            "client_ip": client_ip,
            "activity_type": activity_type,
            "details": details,
            "severity": severity,
            "timestamp": time.time()
        }
        
        if severity == "high":
            logger.error(f"Suspicious activity detected: {activity_type} from {client_ip}", extra=event_data)
        else:
            logger.warning(f"Suspicious activity detected: {activity_type} from {client_ip}", extra=event_data)
    
    @staticmethod
    def log_data_access(
        username: str,
        resource_type: str,
        resource_id: str,
        action: str,
        client_ip: str
    ):
        """Log data access events."""
        event_data = {
            "event_type": "data_access",
            "username": username,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "client_ip": client_ip,
            "timestamp": time.time()
        }
        
        logger.info(f"Data access: {username} {action} {resource_type}:{resource_id}", extra=event_data)
