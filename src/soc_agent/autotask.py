from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import SETTINGS

logger = logging.getLogger(__name__)


def create_autotask_ticket(
    title: str,
    description: str,
    priority: Optional[int] = None,
) -> Tuple[bool, str, Optional[Any]]:
    """Create an Autotask ticket with improved error handling and retry logic."""
    if not SETTINGS.enable_autotask:
        logger.debug("Autotask integration disabled")
        return False, "Autotask disabled", None
    
    # Validate required configuration
    required_config = {
        "base_url": SETTINGS.at_base_url,
        "api_integration_code": SETTINGS.at_api_integration_code,
        "username": SETTINGS.at_username,
        "secret": SETTINGS.at_secret,
        "account_id": SETTINGS.at_account_id,
        "queue_id": SETTINGS.at_queue_id,
    }
    
    missing_config = [key for key, value in required_config.items() if not value]
    if missing_config:
        logger.warning(f"Autotask not fully configured. Missing: {', '.join(missing_config)}")
        return False, f"Autotask not fully configured. Missing: {', '.join(missing_config)}", None

    # Prepare request
    url = f"{SETTINGS.at_base_url.rstrip('/')}/tickets"
    headers = {
        "ApiIntegrationCode": SETTINGS.at_api_integration_code,
        "UserName": SETTINGS.at_username,
        "Secret": SETTINGS.at_secret,
        "Content-Type": "application/json",
    }
    
    # Validate and prepare payload
    try:
        payload = {
            "title": title[:255],  # Truncate title if too long
            "description": description[:10000],  # Truncate description if too long
            "status": 1,  # New status
            "queueID": int(SETTINGS.at_queue_id),
            "accountID": int(SETTINGS.at_account_id),
            "priority": int(priority or SETTINGS.at_ticket_priority),
        }
        
        # Validate priority range
        if not (1 <= payload["priority"] <= 5):
            logger.warning(f"Invalid priority {payload['priority']}, using default")
            payload["priority"] = SETTINGS.at_ticket_priority
            
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid payload data: {e}")
        return False, f"Invalid payload data: {e}", None

    # Create session with retry logic
    session = requests.Session()
    retry_strategy = Retry(
        total=SETTINGS.max_retries,
        backoff_factor=SETTINGS.retry_delay,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Make request with retry logic
    try:
        logger.info(f"Creating Autotask ticket: {title[:50]}...")
        response = session.post(
            url,
            headers=headers,
            json=payload,
            timeout=SETTINGS.http_timeout,
        )
        
        # Handle different response codes
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Autotask ticket created successfully: {result.get('id', 'unknown')}")
                return True, "created", result
            except ValueError as e:
                logger.error(f"Invalid JSON response from Autotask: {e}")
                return False, f"Invalid response format: {e}", None
                
        elif response.status_code == 401:
            logger.error("Autotask authentication failed")
            return False, "Authentication failed", None
            
        elif response.status_code == 403:
            logger.error("Autotask access forbidden")
            return False, "Access forbidden", None
            
        elif response.status_code == 429:
            logger.warning("Autotask rate limit exceeded")
            return False, "Rate limit exceeded", None
            
        elif response.status_code >= 400:
            error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
            logger.error(f"Autotask API error: {error_msg}")
            return False, error_msg, None
            
        else:
            logger.warning(f"Unexpected response code: {response.status_code}")
            return False, f"Unexpected response: {response.status_code}", None
            
    except requests.exceptions.Timeout:
        logger.error("Autotask request timed out")
        return False, "Request timed out", None
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Autotask connection error: {e}")
        return False, f"Connection error: {e}", None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Autotask request error: {e}")
        return False, f"Request error: {e}", None
        
    except Exception as e:
        logger.error(f"Unexpected error creating Autotask ticket: {e}")
        return False, f"Unexpected error: {e}", None
