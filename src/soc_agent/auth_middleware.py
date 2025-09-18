"""Authentication and authorization middleware for SOC Agent."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .auth import AuthenticationError, auth_service
from .database import AuditLog, get_db

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Authentication and authorization middleware."""
    
    def __init__(self):
        self.security = security
    
    async def __call__(self, request: Request, call_next):
        """Process request with authentication and authorization."""
        start_time = time.time()
        
        # Skip auth for certain paths
        if self._should_skip_auth(request.url.path):
            response = await call_next(request)
            return response
        
        # Get current user if authenticated
        current_user = None
        auth_error = None
        
        try:
            current_user = await self._get_current_user(request)
        except AuthenticationError as e:
            auth_error = str(e)
        except Exception as e:
            auth_error = f"Authentication error: {str(e)}"
        
        # Add user to request state
        request.state.current_user = current_user
        request.state.auth_error = auth_error
        
        # Process request
        response = await call_next(request)
        
        # Log audit event
        duration_ms = int((time.time() - start_time) * 1000)
        await self._log_request(request, current_user, duration_ms, response.status_code)
        
        return response
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        skip_paths = [
            "/",
            "/healthz",
            "/readyz",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/oauth",
            "/api/v1/auth/refresh",
        ]
        
        # Skip auth for auth endpoints and health checks
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True
        
        return False
    
    async def _get_current_user(self, request: Request):
        """Get current authenticated user."""
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("No authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Verify token and get user
        with get_db() as db:
            payload = auth_service.verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            user = auth_service.get_user_by_id(db, int(user_id))
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            return user
    
    async def _log_request(self, request: Request, user: Optional[object], 
                          duration_ms: int, status_code: int):
        """Log request for audit purposes."""
        try:
            with get_db() as db:
                # Determine event type based on method and path
                event_type = self._get_event_type(request.method, request.url.path)
                event_category = self._get_event_category(request.url.path)
                action = f"{request.method} {request.url.path}"
                
                # Determine success based on status code
                success = 200 <= status_code < 400
                
                # Create audit log
                audit_log = AuditLog(
                    user_id=user.id if user else None,
                    session_id=request.headers.get("x-session-id", "unknown"),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    event_type=event_type,
                    event_category=event_category,
                    action=action,
                    description=f"HTTP {request.method} request to {request.url.path}",
                    resource_type=self._get_resource_type(request.url.path),
                    resource_id=self._get_resource_id(request.url.path),
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params),
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                    success=success,
                    risk_level=self._get_risk_level(request, user),
                    compliance_tags=["API_ACCESS"],
                    data_classification="internal",
                )
                
                db.add(audit_log)
                db.commit()
                
        except Exception as e:
            # Don't fail the request if audit logging fails
            print(f"Audit logging error: {e}")
    
    def _get_event_type(self, method: str, path: str) -> str:
        """Get event type based on HTTP method and path."""
        if path.startswith("/api/v1/auth/"):
            return "auth"
        elif method == "GET":
            return "read"
        elif method == "POST":
            return "create"
        elif method == "PUT" or method == "PATCH":
            return "update"
        elif method == "DELETE":
            return "delete"
        else:
            return "access"
    
    def _get_event_category(self, path: str) -> str:
        """Get event category based on path."""
        if path.startswith("/api/v1/auth/"):
            return "auth"
        elif path.startswith("/api/v1/alerts/"):
            return "data"
        elif path.startswith("/api/v1/ai/"):
            return "ai"
        elif path.startswith("/api/v1/mcp/"):
            return "security"
        else:
            return "system"
    
    def _get_resource_type(self, path: str) -> Optional[str]:
        """Get resource type based on path."""
        if "/alerts/" in path:
            return "alert"
        elif "/users/" in path:
            return "user"
        elif "/roles/" in path:
            return "role"
        elif "/ai/" in path:
            return "ai_analysis"
        elif "/mcp/" in path:
            return "security_test"
        return None
    
    def _get_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path."""
        parts = path.split("/")
        if len(parts) >= 4 and parts[-1].isdigit():
            return parts[-1]
        return None
    
    def _get_risk_level(self, request: Request, user: Optional[object]) -> str:
        """Determine risk level based on request and user."""
        # High risk for admin actions
        if request.url.path.startswith("/api/v1/auth/") and request.method != "GET":
            return "HIGH"
        
        # Medium risk for data modifications
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return "MEDIUM"
        
        # Low risk for read operations
        return "LOW"


# Global middleware instance
auth_middleware = AuthMiddleware()


def require_auth():
    """Dependency to require authentication."""
    def dependency(request: Request):
        if not hasattr(request.state, 'current_user') or not request.state.current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return request.state.current_user
    return dependency


def require_permission(permission: str):
    """Dependency to require specific permission."""
    def dependency(request: Request):
        user = request.state.current_user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        with get_db() as db:
            if not auth_service.has_permission(db, user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
        
        return user
    return dependency


def optional_auth():
    """Dependency for optional authentication."""
    def dependency(request: Request):
        return getattr(request.state, 'current_user', None)
    return dependency
