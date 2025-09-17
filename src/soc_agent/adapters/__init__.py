"""Vendor specific payload normalization utilities."""

from .crowdstrike import normalize_crowdstrike_event
from .wazuh import normalize_wazuh_event


def normalize_event(event):
    """Detect the vendor of ``event`` and normalise it accordingly.

    If the event does not look like a known vendor payload it is normalized
    to ensure it has the required fields for EventIn validation.
    """

    if "rule" in event and "agent" in event:
        return normalize_wazuh_event(event)
    if "eventType" in event or "Name" in event:
        return normalize_crowdstrike_event(event)
    
    # Normalize unknown events to ensure they have required fields
    normalized = {
        "source": event.get("source", "unknown"),
        "event_type": event.get("event_type", "unknown"),
        "severity": _safe_int(event.get("severity", 0), 0, 10),
        "timestamp": event.get("timestamp"),
        "message": event.get("message"),
        "ip": event.get("ip"),
        "username": event.get("username"),
        "raw": event,
    }
    return normalized


def _safe_int(value, default=0, min_val=None, max_val=None):
    """Safely convert a value to int with bounds checking."""
    try:
        result = int(value)
        if min_val is not None:
            result = max(result, min_val)
        if max_val is not None:
            result = min(result, max_val)
        return result
    except (ValueError, TypeError):
        return default


__all__ = ["normalize_wazuh_event", "normalize_crowdstrike_event", "normalize_event"]
