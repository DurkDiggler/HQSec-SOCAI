"""Integration tests for SOC Agent."""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from soc_agent.webapp import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_intel_client():
    """Mock intelligence client for testing."""
    with patch("soc_agent.analyzer.intel_client") as mock:
        mock.enrich_ip.return_value = {
            "indicator": "1.2.3.4",
            "score": 80,
            "labels": ["malicious"],
            "sources": {"otx": {"pulse_info": {"pulses": [1]}}},
            "enriched_at": 1234567890
        }
        yield mock


@pytest.fixture
def mock_email():
    """Mock email sending."""
    with patch("soc_agent.webapp.send_email") as mock:
        mock.return_value = (True, "sent")
        yield mock


@pytest.fixture
def mock_autotask():
    """Mock Autotask integration."""
    with patch("soc_agent.webapp.create_autotask_ticket") as mock:
        mock.return_value = (True, "created", {"id": 12345})
        yield mock


def test_complete_webhook_flow(client, mock_intel_client, mock_email):
    """Test complete webhook processing flow."""
    payload = {
        "source": "wazuh",
        "event_type": "auth_failed",
        "severity": 7,
        "timestamp": "2023-01-01T00:00:00Z",
        "message": "Failed login from 1.2.3.4",
        "ip": "1.2.3.4",
        "username": "admin"
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "analysis" in data
    assert "actions" in data
    assert "processed_at" in data
    
    # Check analysis results
    analysis = data["analysis"]
    assert "iocs" in analysis
    assert "intel" in analysis
    assert "scores" in analysis
    assert "category" in analysis
    assert "recommended_action" in analysis
    
    # Check that intelligence was enriched
    assert len(analysis["intel"]["ips"]) > 0
    assert analysis["intel"]["ips"][0]["indicator"] == "1.2.3.4"
    
    # Check scoring
    assert analysis["scores"]["base"] > 0
    assert analysis["scores"]["intel"] > 0
    assert analysis["scores"]["final"] > 0


def test_wazuh_event_processing(client, mock_intel_client):
    """Test Wazuh event processing."""
    wazuh_payload = {
        "rule": {
            "id": 5710,
            "level": 7,
            "description": "sshd: authentication failed"
        },
        "agent": {"name": "srv01"},
        "data": {
            "srcip": "203.0.113.4",
            "srcuser": "bob"
        },
        "full_log": "Failed password from 203.0.113.4 port 22 ssh2",
        "@timestamp": "2023-01-01T00:00:00Z"
    }
    
    response = client.post("/webhook", json=wazuh_payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    
    # Should be normalized to auth_failed
    assert analysis["category"] in ["LOW", "MEDIUM", "HIGH"]
    assert "203.0.113.4" in str(analysis["iocs"])


def test_crowdstrike_event_processing(client, mock_intel_client):
    """Test CrowdStrike event processing."""
    cs_payload = {
        "eventType": "AuthActivityAuthFail",
        "Severity": 5,
        "ComputerName": "host01",
        "LocalIP": "198.51.100.10",
        "UserName": "alice",
        "Name": "Authentication failed",
        "@timestamp": "2023-01-01T00:00:00Z"
    }
    
    response = client.post("/webhook", json=cs_payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    
    # Should be normalized to auth_failed
    assert analysis["category"] in ["LOW", "MEDIUM", "HIGH"]
    assert "198.51.100.10" in str(analysis["iocs"])


def test_high_severity_event_creates_ticket(client, mock_intel_client, mock_autotask):
    """Test that high severity events create tickets."""
    payload = {
        "source": "test",
        "event_type": "malware_detected",
        "severity": 10,
        "message": "Malware detected on system",
        "ip": "1.2.3.4"
    }
    
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    actions = data["actions"]
    
    # Should be high category and recommend ticket
    assert analysis["category"] == "HIGH"
    assert analysis["recommended_action"] == "ticket"
    
    # Should have created a ticket
    assert "autotask_ticket" in actions
    assert actions["autotask_ticket"]["ok"] is True


def test_medium_severity_event_sends_email(client, mock_intel_client, mock_email):
    """Test that medium severity events send emails."""
    payload = {
        "source": "test",
        "event_type": "bruteforce",
        "severity": 6,
        "message": "Multiple failed login attempts",
        "ip": "1.2.3.4"
    }
    
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    actions = data["actions"]
    
    # Should be medium category and recommend email
    assert analysis["category"] == "MEDIUM"
    assert analysis["recommended_action"] == "email"
    
    # Should have sent an email
    assert "email" in actions
    assert actions["email"]["ok"] is True


def test_low_severity_event_no_action(client, mock_intel_client):
    """Test that low severity events don't trigger actions."""
    payload = {
        "source": "test",
        "event_type": "port_scan",
        "severity": 2,
        "message": "Port scan detected",
        "ip": "1.2.3.4"
    }
    
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    actions = data["actions"]
    
    # Should be low category and recommend no action
    assert analysis["category"] == "LOW"
    assert analysis["recommended_action"] == "none"
    
    # Should not have any actions
    assert not actions or "error" in actions


def test_ioc_extraction(client, mock_intel_client):
    """Test IOC extraction from various fields."""
    payload = {
        "source": "test",
        "event_type": "suspicious_activity",
        "severity": 5,
        "message": "Connection to malicious domain evil.com from 1.2.3.4",
        "ip": "1.2.3.4",
        "src_ip": "192.168.1.100",
        "dst_ip": "1.2.3.4"
    }
    
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    analysis = data["analysis"]
    iocs = analysis["iocs"]
    
    # Should extract IPs from multiple fields
    assert "1.2.3.4" in iocs["ips"]
    assert "192.168.1.100" in iocs["ips"]
    
    # Should extract domains from message
    assert "evil.com" in iocs["domains"]


def test_error_handling(client):
    """Test error handling for various scenarios."""
    # Test invalid JSON
    response = client.post("/webhook", data="invalid json")
    assert response.status_code == 400
    
    # Test missing required fields
    response = client.post("/webhook", json={})
    assert response.status_code == 422
    
    # Test invalid payload structure
    response = client.post("/webhook", json={"invalid": "structure"})
    assert response.status_code == 422


def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    # Make some requests first
    for i in range(5):
        client.post("/webhook", json={"event_type": "test", "severity": 1})
    
    response = client.get("/metrics")
    
    if response.status_code == 200:
        data = response.json()
        assert "requests_total" in data
        assert "active_clients" in data
        assert "cache_size" in data
        assert data["requests_total"] >= 5


def test_health_checks(client):
    """Test health check endpoints."""
    # Health check
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    
    # Readiness check
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_cors_headers(client):
    """Test CORS headers."""
    response = client.options("/webhook")
    assert "access-control-allow-origin" in response.headers


def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Send requests up to the limit
    for i in range(100):
        response = client.post("/webhook", json={"event_type": "test", "severity": 1})
        if response.status_code == 429:
            break
    
    # Should eventually hit rate limit
    response = client.post("/webhook", json={"event_type": "test", "severity": 1})
    assert response.status_code == 429
