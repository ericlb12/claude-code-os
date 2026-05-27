from qa.model import Interaction
from dashboard.panels.errors import data


def _fake_gather(cfg, since):
    inter = [Interaction(id="1", timestamp="t", source="supabase", user_input="x",
                         agent_output="", tool_calls=[], execution_error="boom",
                         latency_ms=1, raw={})]
    return inter, ["supabase"], []


def test_errors_panel_groups():
    out = data(cfg=None, since="24h", gather=_fake_gather)
    assert out["ok"] is True
    assert out["n_interactions"] == 1
    assert out["grupos"][0]["error_type"] == "execution_error"
    assert out["grupos"][0]["count"] == 1
