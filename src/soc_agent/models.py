from __future__ import annotations

import ipaddress
import re
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator
from .security_utils import SecurityValidator


class EventIn(BaseModel):
    source: Optional[str] = Field(default=None, max_length=100, description="Event source identifier")
    event_type: Optional[str] = Field(
        default=None, 
        max_length=100, 
        description="Canonical event type",
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    severity: int = Field(default=0, ge=0, le=10, description="Event severity (0-10)")

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity(cls, v):
        if v is None:
            return 0
        try:
            result = int(v)
            return max(0, min(result, 10))  # Ensure it's between 0-10
        except (ValueError, TypeError):
            return 0
    timestamp: Optional[str] = Field(default=None, description="Event timestamp (ISO format)")
    message: Optional[str] = Field(default=None, max_length=10000, description="Event message")
    ip: Optional[str] = Field(default=None, description="IP address")
    username: Optional[str] = Field(default=None, max_length=255, description="Username")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw event data")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v):
        if v is None:
            return v
        if not SecurityValidator.validate_ip_address(v):
            raise ValueError("Invalid IP address format")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        if v is None:
            return v
        try:
            # Try to parse ISO format timestamp
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("Invalid timestamp format. Use ISO format (e.g., 2023-01-01T00:00:00Z)")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is None:
            return v
        if not SecurityValidator.validate_username(v):
            raise ValueError("Username contains invalid characters")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if v is None:
            return v
        # Sanitize the message content
        return SecurityValidator.sanitize_string(v)

    model_config = {
        "extra": "forbid",  # Changed from "allow" to "forbid" for security
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
