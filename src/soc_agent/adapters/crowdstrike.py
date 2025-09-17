from typing import Any, Dict


def normalize_crowdstrike_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a CrowdStrike event into an EventIn‑compatible dict."""

    etype = event.get("eventType") or event.get("Name") or ""
    etype_lower = etype.lower()
    if "auth" in etype_lower and "fail" in etype_lower:
        event_type = "auth_failed"
    else:
        event_type = etype_lower or "unknown"

    # Safely convert severity to int
    try:
        severity = int(event.get("Severity", 0))
        severity = max(0, min(severity, 10))  # Ensure it's between 0-10
    except (ValueError, TypeError):
        severity = 0

    return {
        "source": "crowdstrike",
        "event_type": event_type,
        "severity": severity,
        "timestamp": event.get("@timestamp"),
        "message": event.get("Name"),
        "ip": event.get("LocalIP"),
        "username": event.get("UserName"),
        "raw": event,
    }
