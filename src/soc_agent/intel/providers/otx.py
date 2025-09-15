from __future__ import annotations

from typing import Any, Dict

import requests

from ...config import SETTINGS


def lookup_ip(session: requests.Session, ip: str, timeout: float) -> Dict[str, Any]:
    url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
    r = session.get(url, headers={"X-OTX-API-KEY": SETTINGS.otx_api_key}, timeout=timeout)
    r.raise_for_status()
    return r.json()
