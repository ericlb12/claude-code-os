from qa.model import Interaction
from dashboard.panels.interactions import data


def _gather(cfg, since):
    inter = [
        Interaction(id="1", timestamp="t1", source="supabase", user_input="hola mundo",
                    agent_output="ok", tool_calls=[], execution_error=None, latency_ms=1, raw={}),
        Interaction(id="2", timestamp="t2", source="supabase", user_input="otra",
                    agent_output="", tool_calls=[], execution_error="boom", latency_ms=1, raw={}),
    ]
    return inter, ["supabase"], []


def test_interactions_counts():
    out = data(cfg=None, since="24h", gather=_gather)
    assert out["ok"] is True
    assert out["total"] == 2
    assert out["con_error"] == 1
    assert out["recientes"][0]["id"] == "1"
    assert out["recientes"][0]["input"].startswith("hola")
