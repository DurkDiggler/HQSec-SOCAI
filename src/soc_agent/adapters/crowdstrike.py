from typing import Any, Dict


def normalize_crowdstrike_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a CrowdStrike event into an EventIn‑compatible dict."""

    etype = event.get("eventType") or event.get("Name") or ""
    etype_lower = etype.lower()
    if "auth" in etype_lower and "fail" in etype_lower:
        event_type = "auth_failed"
    else:
        event_type = etype_lower or "unknown"

    return {
        "source": "crowdstrike",
        "event_type": event_type,
        "severity": int(event.get("Severity", 0)),
        "timestamp": event.get("@timestamp"),
        "message": event.get("Name"),
        "ip": event.get("LocalIP"),
        "username": event.get("UserName"),
        "raw": event,
    }
