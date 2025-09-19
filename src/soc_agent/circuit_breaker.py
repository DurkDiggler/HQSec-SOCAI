"""Circuit breaker pattern implementation for resilient service calls."""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: float = 60.0      # Time to wait before trying again
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 30.0               # Timeout for individual calls
    max_retries: int = 3                # Maximum retry attempts
    retry_delay: float = 1.0            # Delay between retries


class CircuitBreakerError(Exception):
    """Circuit breaker specific error."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_success_time = 0.0
        
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.state == CircuitState.OPEN and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.success_count += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' closed after {self.config.success_threshold} successes")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' opened after {self.failure_count} failures")
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        # Check if circuit should be reset
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            logger.info(f"Circuit breaker '{self.name}' moved to half-open state")
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        # Attempt the call
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self._on_failure()
            raise CircuitBreakerError(f"Circuit breaker '{self.name}': Call timed out")
            
        except Exception as e:
            self._on_failure()
            raise CircuitBreakerError(f"Circuit breaker '{self.name}': {str(e)}")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }
        }


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_states(self) -> dict[str, dict]:
        """Get states of all circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}
    
    def reset_breaker(self, name: str):
        """Reset a circuit breaker to closed state."""
        if name in self._breakers:
            self._breakers[name].state = CircuitState.CLOSED
            self._breakers[name].failure_count = 0
            self._breakers[name].success_count = 0
            logger.info(f"Circuit breaker '{name}' manually reset")


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator for circuit breaker functionality."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            breaker = circuit_manager.get_breaker(name, config)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured circuit breakers for common services
def get_external_api_breaker() -> CircuitBreaker:
    """Get circuit breaker for external API calls."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=10.0
    )
    return circuit_manager.get_breaker("external_api", config)


def get_database_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations."""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=3,
        timeout=30.0
    )
    return circuit_manager.get_breaker("database", config)


def get_notification_breaker() -> CircuitBreaker:
    """Get circuit breaker for notification services."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120.0,
        success_threshold=2,
        timeout=15.0
    )
    return circuit_manager.get_breaker("notifications", config)
