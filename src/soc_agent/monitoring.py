"""Advanced monitoring and observability for SOC Agent."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import psutil
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
from prometheus_client.core import REGISTRY

from .config import SETTINGS
from .database_cluster import db_cluster
from .messaging import event_bus, MessageType

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Metric types for monitoring."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricData:
    """Metric data structure."""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    metric_type: MetricType

class PrometheusMetrics:
    """Prometheus metrics collection."""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics."""
        # API metrics
        self.metrics["api_requests_total"] = Counter(
            "soc_agent_api_requests_total",
            "Total number of API requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry
        )
        
        self.metrics["api_request_duration"] = Histogram(
            "soc_agent_api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
            registry=self.registry
        )
        
        # Alert metrics
        self.metrics["alerts_total"] = Counter(
            "soc_agent_alerts_total",
            "Total number of alerts",
            ["source", "severity", "status"],
            registry=self.registry
        )
        
        self.metrics["alerts_processing_duration"] = Histogram(
            "soc_agent_alerts_processing_duration_seconds",
            "Alert processing duration in seconds",
            ["source"],
            registry=self.registry
        )
        
        # Database metrics
        self.metrics["database_connections"] = Gauge(
            "soc_agent_database_connections",
            "Number of active database connections",
            ["database", "type"]
        )
        
        self.metrics["database_query_duration"] = Histogram(
            "soc_agent_database_query_duration_seconds",
            "Database query duration in seconds",
            ["query_type", "database"],
            registry=self.registry
        )
        
        # System metrics
        self.metrics["system_cpu_usage"] = Gauge(
            "soc_agent_system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry
        )
        
        self.metrics["system_memory_usage"] = Gauge(
            "soc_agent_system_memory_usage_bytes",
            "System memory usage in bytes",
            registry=self.registry
        )
        
        self.metrics["system_disk_usage"] = Gauge(
            "soc_agent_system_disk_usage_bytes",
            "System disk usage in bytes",
            ["device"],
            registry=self.registry
        )
        
        # Service metrics
        self.metrics["service_health"] = Gauge(
            "soc_agent_service_health",
            "Service health status (1=healthy, 0=unhealthy)",
            ["service_name"],
            registry=self.registry
        )
        
        self.metrics["service_response_time"] = Histogram(
            "soc_agent_service_response_time_seconds",
            "Service response time in seconds",
            ["service_name", "endpoint"],
            registry=self.registry
        )
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metric."""
        self.metrics["api_requests_total"].labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.metrics["api_request_duration"].labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_alert(self, source: str, severity: str, status: str):
        """Record alert metric."""
        self.metrics["alerts_total"].labels(
            source=source,
            severity=severity,
            status=status
        ).inc()
    
    def record_alert_processing(self, source: str, duration: float):
        """Record alert processing duration."""
        self.metrics["alerts_processing_duration"].labels(
            source=source
        ).observe(duration)
    
    def record_database_connection(self, database: str, connection_type: str, count: int):
        """Record database connection metric."""
        self.metrics["database_connections"].labels(
            database=database,
            type=connection_type
        ).set(count)
    
    def record_database_query(self, query_type: str, database: str, duration: float):
        """Record database query duration."""
        self.metrics["database_query_duration"].labels(
            query_type=query_type,
            database=database
        ).observe(duration)
    
    def record_system_metrics(self):
        """Record system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics["system_cpu_usage"].set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics["system_memory_usage"].set(memory.used)
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.metrics["system_disk_usage"].labels(
                    device=partition.device
                ).set(usage.used)
            except PermissionError:
                continue
    
    def record_service_health(self, service_name: str, is_healthy: bool):
        """Record service health status."""
        self.metrics["service_health"].labels(
            service_name=service_name
        ).set(1 if is_healthy else 0)
    
    def record_service_response_time(self, service_name: str, endpoint: str, duration: float):
        """Record service response time."""
        self.metrics["service_response_time"].labels(
            service_name=service_name,
            endpoint=endpoint
        ).observe(duration)

class HealthChecker:
    """Health checking for services and dependencies."""
    
    def __init__(self):
        self.checks = {}
        self.health_status = {}
        self.last_check = {}
        self.check_interval = 30  # seconds
    
    def register_check(self, name: str, check_func: Callable[[], bool], 
                      interval: int = 30, critical: bool = True):
        """Register a health check."""
        self.checks[name] = {
            "function": check_func,
            "interval": interval,
            "critical": critical,
            "last_check": 0
        }
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        current_time = time.time()
        results = {}
        
        for name, check_info in self.checks.items():
            # Skip if not time for check
            if current_time - check_info["last_check"] < check_info["interval"]:
                continue
            
            try:
                # Run check
                is_healthy = await self._run_check(check_info["function"])
                
                results[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "critical": check_info["critical"],
                    "last_check": current_time,
                    "error": None
                }
                
                check_info["last_check"] = current_time
                
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "status": "error",
                    "critical": check_info["critical"],
                    "last_check": current_time,
                    "error": str(e)
                }
        
        self.health_status = results
        return results
    
    async def _run_check(self, check_func: Callable[[], bool]) -> bool:
        """Run a single health check."""
        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health status."""
        if not self.health_status:
            return {"status": "unknown", "checks": {}}
        
        critical_checks = [name for name, info in self.checks.items() if info["critical"]]
        critical_results = [self.health_status.get(name, {}) for name in critical_checks]
        
        # Check if any critical checks are unhealthy
        critical_unhealthy = any(
            result.get("status") in ["unhealthy", "error"] 
            for result in critical_results
        )
        
        overall_status = "unhealthy" if critical_unhealthy else "healthy"
        
        return {
            "status": overall_status,
            "checks": self.health_status,
            "critical_checks": critical_checks,
            "timestamp": datetime.utcnow().isoformat()
        }

class PerformanceMonitor:
    """Performance monitoring and profiling."""
    
    def __init__(self):
        self.metrics = []
        self.performance_data = {}
        self.slow_query_threshold = 1.0  # seconds
        self.slow_request_threshold = 2.0  # seconds
    
    def record_metric(self, metric: MetricData):
        """Record a metric."""
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def record_performance(self, operation: str, duration: float, 
                          labels: Optional[Dict[str, str]] = None):
        """Record performance data."""
        if operation not in self.performance_data:
            self.performance_data[operation] = {
                "count": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "slow_operations": 0
            }
        
        data = self.performance_data[operation]
        data["count"] += 1
        data["total_duration"] += duration
        data["min_duration"] = min(data["min_duration"], duration)
        data["max_duration"] = max(data["max_duration"], duration)
        
        # Check for slow operations
        if duration > self.slow_query_threshold:
            data["slow_operations"] += 1
            logger.warning(f"Slow operation detected: {operation} took {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        for operation, data in self.performance_data.items():
            if data["count"] > 0:
                summary[operation] = {
                    "count": data["count"],
                    "avg_duration": data["total_duration"] / data["count"],
                    "min_duration": data["min_duration"],
                    "max_duration": data["max_duration"],
                    "slow_operations": data["slow_operations"],
                    "slow_percentage": (data["slow_operations"] / data["count"]) * 100
                }
        
        return summary
    
    def get_slow_operations(self, threshold: float = None) -> List[Dict[str, Any]]:
        """Get slow operations above threshold."""
        if threshold is None:
            threshold = self.slow_query_threshold
        
        slow_ops = []
        for operation, data in self.performance_data.items():
            if data["max_duration"] > threshold:
                slow_ops.append({
                    "operation": operation,
                    "max_duration": data["max_duration"],
                    "slow_operations": data["slow_operations"],
                    "total_operations": data["count"]
                })
        
        return sorted(slow_ops, key=lambda x: x["max_duration"], reverse=True)

class MonitoringService:
    """Main monitoring service."""
    
    def __init__(self):
        self.prometheus = PrometheusMetrics()
        self.health_checker = HealthChecker()
        self.performance_monitor = PerformanceMonitor()
        self.running = False
        self.monitoring_task = None
        
        # Register health checks
        self._register_health_checks()
    
    def _register_health_checks(self):
        """Register default health checks."""
        # Database health check
        self.health_checker.register_check(
            "database",
            self._check_database_health,
            interval=30,
            critical=True
        )
        
        # Redis health check
        self.health_checker.register_check(
            "redis",
            self._check_redis_health,
            interval=30,
            critical=True
        )
        
        # Storage health check
        self.health_checker.register_check(
            "storage",
            self._check_storage_health,
            interval=60,
            critical=False
        )
        
        # Elasticsearch health check
        self.health_checker.register_check(
            "elasticsearch",
            self._check_elasticsearch_health,
            interval=60,
            critical=False
        )
    
    async def _check_database_health(self) -> bool:
        """Check database health."""
        try:
            cluster_status = db_cluster.get_cluster_status()
            return cluster_status["cluster_status"] == "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            import redis
            r = redis.Redis(
                host=SETTINGS.redis_host,
                port=SETTINGS.redis_port,
                password=SETTINGS.redis_password,
                db=SETTINGS.redis_db
            )
            return r.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def _check_storage_health(self) -> bool:
        """Check storage health."""
        try:
            from .storage import storage_service
            stats = storage_service.get_storage_stats()
            return stats is not None
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
    
    async def _check_elasticsearch_health(self) -> bool:
        """Check Elasticsearch health."""
        try:
            from .elasticsearch_service import elasticsearch_service
            health = elasticsearch_service.get_cluster_health()
            return health["status"] == "green"
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False
    
    async def start_monitoring(self):
        """Start monitoring service."""
        if self.running:
            return
        
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Start Prometheus metrics server
        start_http_server(8000, registry=self.prometheus.registry)
        
        logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop monitoring service."""
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Run health checks
                await self.health_checker.run_checks()
                
                # Record system metrics
                self.prometheus.record_system_metrics()
                
                # Record database metrics
                await self._record_database_metrics()
                
                # Record service metrics
                await self._record_service_metrics()
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _record_database_metrics(self):
        """Record database metrics."""
        try:
            cluster_status = db_cluster.get_cluster_status()
            
            # Record connection counts
            for pool_name, pool in db_cluster.connection_pools.items():
                self.prometheus.record_database_connection(
                    database=pool_name,
                    connection_type="active",
                    count=pool.closed
                )
            
        except Exception as e:
            logger.error(f"Failed to record database metrics: {e}")
    
    async def _record_service_metrics(self):
        """Record service metrics."""
        try:
            # Check service health
            services = [
                "auth-service", "alert-service", "ai-service", "intel-service",
                "response-service", "analytics-service", "notification-service", "storage-service"
            ]
            
            for service in services:
                # Implement actual service health checks
                try:
                    # Check database connectivity
                    with get_db() as db:
                        db.execute("SELECT 1")
                    checks["database"] = True
                except Exception as e:
                    checks["database"] = False
                    logger.error(f"Database health check failed: {e}")
                
                try:
                    # Check Redis connectivity
                    from .caching import cache_manager
                    cache_manager.ping()
                    checks["redis"] = True
                except Exception as e:
                    checks["redis"] = False
                    logger.error(f"Redis health check failed: {e}")
                
                try:
                    # Check external APIs (if configured)
                    if SETTINGS.otx_api_key:
                        from .intel.client import intel_client
                        await intel_client.check_ip("8.8.8.8", "otx")
                        checks["external_apis"] = True
                    else:
                        checks["external_apis"] = True  # Not configured, so healthy
                except Exception as e:
                    checks["external_apis"] = False
                    logger.error(f"External APIs health check failed: {e}")
                
                try:
                    # Check MCP servers
                    from .mcp.server_registry import MCPServerRegistry
                    async with MCPServerRegistry() as mcp_registry:
                        status = await mcp_registry.get_server_status()
                        checks["mcp_servers"] = all(server.get("status") == "available" for server in status.values())
                except Exception as e:
                    checks["mcp_servers"] = False
                    logger.error(f"MCP servers health check failed: {e}")
                self.prometheus.record_service_health(service, True)
                
        except Exception as e:
            logger.error(f"Failed to record service metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "prometheus_metrics": len(self.prometheus.metrics),
            "health_checks": self.health_checker.get_overall_health(),
            "performance_summary": self.performance_monitor.get_performance_summary(),
            "slow_operations": self.performance_monitor.get_slow_operations()
        }

# Global monitoring service
monitoring_service = MonitoringService()
