from fastapi.testclient import TestClient

from soc_agent.webapp import app

client = TestClient(app)

def test_webhook_ok(monkeypatch):
    monkeypatch.setattr(
        "soc_agent.webapp.create_autotask_ticket",
        lambda **kw: (True, "created", {"id": 1}),
    )
    monkeypatch.setattr(
        "soc_agent.webapp.send_email",
        lambda **kw: (True, "sent"),
    )

    payload = {
        "source": "wazuh",
        "event_type": "auth_failed",
        "severity": 5,
        "message": "Failed logins from 9.9.9.9",
        "ip": "9.9.9.9"
    }
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "analysis" in data and "actions" in data
