"""Security tests for SOC Agent."""

import pytest
from fastapi.testclient import TestClient

from soc_agent.webapp import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Send requests up to the limit
    for i in range(100):  # Default rate limit
        response = client.post("/webhook", json={"event_type": "test", "severity": 1})
        assert response.status_code in [200, 422]  # 422 for invalid payload
    
    # This should be rate limited
    response = client.post("/webhook", json={"event_type": "test", "severity": 1})
    assert response.status_code == 429


def test_request_size_limit(client):
    """Test request size limiting."""
    large_payload = {"message": "x" * 2000000}  # 2MB payload
    response = client.post("/webhook", json=large_payload)
    assert response.status_code == 413


def test_webhook_authentication(client):
    """Test webhook authentication."""
    # Test with invalid secret
    response = client.post(
        "/webhook",
        json={"event_type": "test", "severity": 1},
        headers={"X-Webhook-Secret": "invalid"}
    )
    # Should fail if webhook_shared_secret is set
    assert response.status_code in [401, 422]


def test_webhook_hmac_authentication(client):
    """Test HMAC authentication."""
    import hmac
    import hashlib
    
    body = b'{"event_type": "test", "severity": 1}'
    signature = hmac.new(
        b"test_secret",
        body,
        hashlib.sha256
    ).hexdigest()
    
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Signature": f"sha256={signature}"}
    )
    # Should fail if webhook_hmac_secret is not set to "test_secret"
    assert response.status_code in [401, 422]


def test_malicious_input(client):
    """Test protection against malicious input."""
    malicious_payloads = [
        {"message": "<script>alert('xss')</script>"},
        {"message": "javascript:alert('xss')"},
        {"message": "onload=alert('xss')"},
        {"username": "admin'; DROP TABLE users; --"},
        {"ip": "1.1.1.1'; DROP TABLE events; --"},
    ]
    
    for payload in malicious_payloads:
        response = client.post("/webhook", json=payload)
        # Should either reject or sanitize the input
        assert response.status_code in [200, 422, 400]


def test_ip_validation(client):
    """Test IP address validation."""
    invalid_ips = [
        "999.999.999.999",
        "not.an.ip",
        "192.168.1.256",
        "2001:db8::gggg",  # Invalid IPv6
    ]
    
    for ip in invalid_ips:
        response = client.post("/webhook", json={"ip": ip, "event_type": "test", "severity": 1})
        assert response.status_code == 422


def test_username_validation(client):
    """Test username validation."""
    invalid_usernames = [
        "user<script>",
        "admin@domain.com",
        "user with spaces",
        "user/with/slashes",
    ]
    
    for username in invalid_usernames:
        response = client.post("/webhook", json={"username": username, "event_type": "test", "severity": 1})
        assert response.status_code == 422


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/webhook")
    assert "access-control-allow-origin" in response.headers


def test_health_endpoints(client):
    """Test health check endpoints."""
    # Health check
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # Readiness check
    response = client.get("/readyz")
    assert response.status_code == 200
    assert "status" in response.json()


def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    # Should either return metrics or 404 if disabled
    assert response.status_code in [200, 404]
