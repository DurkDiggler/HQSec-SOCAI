from typing import Any, Dict


def normalize_wazuh_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Wazuh alert JSON into an EventIn‑compatible dict."""

    rule = event.get("rule", {})
    data = event.get("data", {})
    desc = (rule.get("description") or "").lower()
    if "authentication failed" in desc:
        event_type = "auth_failed"
    else:
        event_type = desc or "unknown"

    return {
        "source": "wazuh",
        "event_type": event_type,
        "severity": int(rule.get("level", 0)),
        "timestamp": event.get("@timestamp"),
        "message": event.get("full_log") or rule.get("description"),
        "ip": data.get("srcip"),
        "username": data.get("srcuser"),
        "raw": event,
    }
