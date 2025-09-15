"""Tests for data models."""

import pytest
from pydantic import ValidationError

from soc_agent.models import EventIn


def test_valid_event():
    """Test valid event creation."""
    event = EventIn(
        source="wazuh",
        event_type="auth_failed",
        severity=5,
        timestamp="2023-01-01T00:00:00Z",
        message="Authentication failed",
        ip="192.168.1.1",
        username="admin"
    )
    assert event.source == "wazuh"
    assert event.severity == 5


def test_invalid_ip():
    """Test invalid IP address validation."""
    with pytest.raises(ValidationError) as exc_info:
        EventIn(ip="999.999.999.999", event_type="test", severity=1)
    
    assert "Invalid IP address format" in str(exc_info.value)


def test_invalid_timestamp():
    """Test invalid timestamp validation."""
    with pytest.raises(ValidationError) as exc_info:
        EventIn(timestamp="not-a-timestamp", event_type="test", severity=1)
    
    assert "Invalid timestamp format" in str(exc_info.value)


def test_invalid_username():
    """Test invalid username validation."""
    with pytest.raises(ValidationError) as exc_info:
        EventIn(username="user<script>", event_type="test", severity=1)
    
    assert "Username contains invalid characters" in str(exc_info.value)


def test_malicious_message():
    """Test malicious message detection."""
    with pytest.raises(ValidationError) as exc_info:
        EventIn(message="<script>alert('xss')</script>", event_type="test", severity=1)
    
    assert "potentially dangerous content" in str(exc_info.value)


def test_severity_validation():
    """Test severity range validation."""
    # Valid severity
    event = EventIn(severity=5, event_type="test")
    assert event.severity == 5
    
    # Invalid severity (too high)
    with pytest.raises(ValidationError):
        EventIn(severity=15, event_type="test")
    
    # Invalid severity (negative)
    with pytest.raises(ValidationError):
        EventIn(severity=-1, event_type="test")


def test_event_type_validation():
    """Test event type pattern validation."""
    # Valid event type
    event = EventIn(event_type="auth_failed", severity=1)
    assert event.event_type == "auth_failed"
    
    # Invalid event type
    with pytest.raises(ValidationError):
        EventIn(event_type="invalid event type!", severity=1)


def test_field_length_limits():
    """Test field length limits."""
    # Test message length limit
    long_message = "x" * 10001
    with pytest.raises(ValidationError):
        EventIn(message=long_message, event_type="test", severity=1)
    
    # Test username length limit
    long_username = "x" * 256
    with pytest.raises(ValidationError):
        EventIn(username=long_username, event_type="test", severity=1)


def test_extra_fields_forbidden():
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError):
        EventIn(
            event_type="test",
            severity=1,
            extra_field="not allowed"
        )


def test_ipv6_support():
    """Test IPv6 address support."""
    event = EventIn(ip="2001:db8::1", event_type="test", severity=1)
    assert event.ip == "2001:db8::1"


def test_private_ip_handling():
    """Test private IP handling."""
    # Private IPs should be accepted by the model
    event = EventIn(ip="192.168.1.1", event_type="test", severity=1)
    assert event.ip == "192.168.1.1"
    
    event = EventIn(ip="10.0.0.1", event_type="test", severity=1)
    assert event.ip == "10.0.0.1"