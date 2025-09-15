from soc_agent.adapters import normalize_event

WAZUH = {
    "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
    "agent": {"name": "srv01"},
    "data": {"srcip": "203.0.113.4", "srcuser": "bob"},
    "full_log": "Failed password from 203.0.113.4 port 22 ssh2",
}

CS = {
    "eventType": "AuthActivityAuthFail",
    "Severity": 5,
    "ComputerName": "host01",
    "LocalIP": "198.51.100.10",
    "UserName": "alice",
    "Name": "Authentication failed",
}

def test_normalize_wazuh():
    out = normalize_event(WAZUH)
    assert out["event_type"] == "auth_failed"
    assert out["severity"] >= 1
    assert out["ip"] == "203.0.113.4"

def test_normalize_crowdstrike():
    out = normalize_event(CS)
    assert out["event_type"] == "auth_failed"
    assert out["ip"] == "198.51.100.10"
