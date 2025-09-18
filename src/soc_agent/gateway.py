"""API Gateway for SOC Agent microservices."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import SETTINGS

logger = logging.getLogger(__name__)

# Service registry
SERVICES = {
    "auth-service": {
        "url": "http://auth-service:8001",
        "health_endpoint": "/health",
        "routes": ["/api/v1/auth", "/api/v1/users", "/api/v1/roles"],
        "timeout": 30,
        "retries": 3
    },
    "alert-service": {
        "url": "http://alert-service:8002",
        "health_endpoint": "/health",
        "routes": ["/api/v1/alerts", "/api/v1/statistics"],
        "timeout": 30,
        "retries": 3
    },
    "ai-service": {
        "url": "http://ai-service:8003",
        "health_endpoint": "/health",
        "routes": ["/api/v1/ai", "/api/v1/analysis"],
        "timeout": 60,
        "retries": 2
    },
    "intel-service": {
        "url": "http://intel-service:8004",
        "health_endpoint": "/health",
        "routes": ["/api/v1/intel", "/api/v1/threats"],
        "timeout": 30,
        "retries": 3
    },
    "response-service": {
        "url": "http://response-service:8005",
        "health_endpoint": "/health",
        "routes": ["/api/v1/response", "/api/v1/incidents"],
        "timeout": 30,
        "retries": 3
    },
    "analytics-service": {
        "url": "http://analytics-service:8006",
        "health_endpoint": "/health",
        "routes": ["/api/v1/analytics", "/api/v1/reports"],
        "timeout": 60,
        "retries": 2
    },
    "notification-service": {
        "url": "http://notification-service:8007",
        "health_endpoint": "/health",
        "routes": ["/api/v1/notifications", "/api/v1/email"],
        "timeout": 30,
        "retries": 3
    },
    "storage-service": {
        "url": "http://storage-service:8008",
        "health_endpoint": "/health",
        "routes": ["/api/v1/storage", "/api/v1/search", "/api/v1/metrics"],
        "timeout": 30,
        "retries": 3
    }
}

# Circuit breaker states
CIRCUIT_BREAKER_STATES = {
    "CLOSED": "closed",
    "OPEN": "open",
    "HALF_OPEN": "half_open"
}

class CircuitBreaker:
    """Circuit breaker for service resilience."""
    
    def __init__(self, service_name: str, failure_threshold: int = 5, 
                 recovery_timeout: int = 60):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CIRCUIT_BREAKER_STATES["CLOSED"]
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CIRCUIT_BREAKER_STATES["CLOSED"]:
            return True
        elif self.state == CIRCUIT_BREAKER_STATES["OPEN"]:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CIRCUIT_BREAKER_STATES["HALF_OPEN"]
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = CIRCUIT_BREAKER_STATES["CLOSED"]
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CIRCUIT_BREAKER_STATES["OPEN"]

class LoadBalancer:
    """Simple round-robin load balancer."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.current_index = 0
        self.instances = []
        self.circuit_breakers = {}
    
    def add_instance(self, instance_url: str):
        """Add service instance."""
        self.instances.append(instance_url)
        self.circuit_breakers[instance_url] = CircuitBreaker(
            f"{self.service_name}-{instance_url}"
        )
    
    def get_next_instance(self) -> Optional[str]:
        """Get next available instance."""
        if not self.instances:
            return None
        
        for _ in range(len(self.instances)):
            instance = self.instances[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.instances)
            
            if self.circuit_breakers[instance].can_execute():
                return instance
        
        return None

class ServiceRegistry:
    """Service registry for microservices."""
    
    def __init__(self):
        self.services = {}
        self.load_balancers = {}
        self.health_checks = {}
        
        # Initialize services
        for service_name, config in SERVICES.items():
            self.services[service_name] = config
            self.load_balancers[service_name] = LoadBalancer(service_name)
            self.load_balancers[service_name].add_instance(config["url"])
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL with load balancing."""
        if service_name not in self.load_balancers:
            return None
        
        return self.load_balancers[service_name].get_next_instance()
    
    def get_service_for_route(self, route: str) -> Optional[str]:
        """Get service name for a given route."""
        for service_name, config in self.services.items():
            for service_route in config["routes"]:
                if route.startswith(service_route):
                    return service_name
        return None
    
    async def health_check_service(self, service_name: str) -> bool:
        """Check service health."""
        if service_name not in self.services:
            return False
        
        service_config = self.services[service_name]
        health_url = urljoin(service_config["url"], service_config["health_endpoint"])
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    async def health_check_all_services(self) -> Dict[str, bool]:
        """Check health of all services."""
        health_status = {}
        
        for service_name in self.services:
            health_status[service_name] = await self.health_check_service(service_name)
        
        return health_status

class GatewayMiddleware(BaseHTTPMiddleware):
    """Gateway middleware for request routing."""
    
    def __init__(self, app, service_registry: ServiceRegistry):
        super().__init__(app)
        self.service_registry = service_registry
    
    async def dispatch(self, request: Request, call_next):
        """Route requests to appropriate services."""
        # Skip gateway health checks and static files
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get service for route
        service_name = self.service_registry.get_service_for_route(request.url.path)
        if not service_name:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Service not found for route"}
            )
        
        # Get service URL
        service_url = self.service_registry.get_service_url(service_name)
        if not service_url:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Service unavailable"}
            )
        
        # Forward request to service
        try:
            return await self.forward_request(request, service_url)
        except Exception as e:
            logger.error(f"Request forwarding failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    async def forward_request(self, request: Request, service_url: str) -> Response:
        """Forward request to target service."""
        # Build target URL
        target_url = urljoin(service_url, str(request.url.path))
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None)  # Remove host header
        
        # Get request body
        body = await request.body()
        
        # Make request to target service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

class APIGateway:
    """Main API Gateway class."""
    
    def __init__(self):
        self.app = FastAPI(
            title="SOC Agent API Gateway",
            description="API Gateway for SOC Agent microservices",
            version="1.0.0"
        )
        self.service_registry = ServiceRegistry()
        self.setup_middleware()
        self.setup_routes()
    
    def setup_middleware(self):
        """Setup gateway middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=SETTINGS.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            allow_headers=["*"],
        )
        
        # Gateway middleware
        self.app.add_middleware(GatewayMiddleware, service_registry=self.service_registry)
    
    def setup_routes(self):
        """Setup gateway routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Gateway health check."""
            return {"status": "healthy", "timestamp": time.time()}
        
        @self.app.get("/services/health")
        async def services_health():
            """Check health of all services."""
            health_status = await self.service_registry.health_check_all_services()
            return {
                "gateway": "healthy",
                "services": health_status,
                "timestamp": time.time()
            }
        
        @self.app.get("/services")
        async def list_services():
            """List all registered services."""
            return {
                "services": list(self.service_registry.services.keys()),
                "count": len(self.service_registry.services)
            }
        
        @self.app.get("/metrics")
        async def gateway_metrics():
            """Gateway metrics."""
            return {
                "gateway_requests": 0,  # Would be tracked in production
                "active_services": len(self.service_registry.services),
                "circuit_breakers": {
                    service: {
                        "state": lb.circuit_breakers[instance].state,
                        "failure_count": lb.circuit_breakers[instance].failure_count
                    }
                    for service, lb in self.service_registry.load_balancers.items()
                    for instance in lb.instances
                }
            }

# Global gateway instance
gateway = APIGateway()
app = gateway.app
