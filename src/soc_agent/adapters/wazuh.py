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

    return {
        "source": "wazuh",
        "event_type": event_type,
        "severity": min(int(rule.get("level", 0)), 10),
        "timestamp": event.get("@timestamp"),
        "message": event.get("full_log") or rule.get("description"),
        "ip": data.get("srcip"),
        "username": data.get("srcuser"),
        "raw": event,
    }
