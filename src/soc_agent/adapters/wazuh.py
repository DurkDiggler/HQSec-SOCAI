from typing import Any, Dict


def normalize_wazuh_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Wazuh alert JSON into an EventIn‑compatible dict."""

    rule = event.get("rule", {})
    data = event.get("data", {})
    desc = (rule.get("description") or "").lower()
    if "authentication failed" in desc:
        event_type = "auth_failed"
    elif "malware detected" in desc:
        event_type = "malware_detected"
    elif "critical" in desc:
        event_type = "critical_event"
    else:
        event_type = "unknown"

    # Safely convert severity to int
    try:
        severity = int(rule.get("level", 0))
        severity = max(0, min(severity, 10))  # Ensure it's between 0-10
    except (ValueError, TypeError):
        severity = 0

    return {
        "source": "wazuh",
        "event_type": event_type,
        "severity": severity,
        "timestamp": event.get("@timestamp"),
        "message": event.get("full_log") or rule.get("description"),
        "ip": data.get("srcip"),
        "username": data.get("srcuser"),
        "raw": event,
    }
