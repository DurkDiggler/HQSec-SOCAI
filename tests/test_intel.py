from soc_agent.intel.client import IntelClient


class DummySession:
    def __init__(self, payload):
        self.payload = payload
    def get(self, url, **kwargs):
        class Resp:
            def __init__(self, p):
                self._p = p
                self.status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return self._p
        return Resp(self.payload)

class StubClient(IntelClient):
    def __init__(self):
        super().__init__()
        self.session = DummySession(
            {
                "pulse_info": {"pulses": [1]},
                "data": {"attributes": {"last_analysis_stats": {}}},
            }
        )


def test_enrich_ip_shape():
    c = StubClient()
    out = c.enrich_ip("203.0.113.1")
    assert "indicator" in out and "score" in out and "sources" in out
