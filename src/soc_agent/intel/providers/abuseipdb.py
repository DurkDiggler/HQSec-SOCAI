from __future__ import annotations

from typing import Any, Dict

import requests

from ...config import SETTINGS


def lookup_ip(session: requests.Session, ip: str, timeout: float) -> Dict[str, Any]:
    url = "https://api.abuseipdb.com/api/v2/check"
    r = session.get(
        url,
        params={"ipAddress": ip, "maxAgeInDays": 90},
        headers={"Key": SETTINGS.abuseipdb_api_key, "Accept": "application/json"},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()
