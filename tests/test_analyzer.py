from soc_agent.analyzer import base_score, enrich_and_score


class DummyIntel:
    def enrich_ip(self, ip: str):
        return {
            "indicator": ip,
            "score": 80 if ip == "9.9.9.9" else 0,
            "labels": ["unknown"],
            "sources": {},
        }


def test_extract_and_score(monkeypatch):
    monkeypatch.setattr("soc_agent.analyzer.intel_client", DummyIntel())
    event = {"event_type": "port_scan", "severity": 3, "message": "src 9.9.9.9"}
    out = enrich_and_score(event)
    assert out["scores"]["intel"] >= 0
    assert out["category"] in {"LOW", "MEDIUM", "HIGH"}


def test_base_score_monotonic():
    low = base_score({"event_type": "auth_failed", "severity": 1})
    high = base_score({"event_type": "auth_failed", "severity": 8})
    assert high > low
