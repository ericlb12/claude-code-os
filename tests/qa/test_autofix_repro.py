from qa.model import Interaction
from qa.autofix.repro import build_repro_case, ReproError


def _interaction(uin, iid="42"):
    return Interaction(id=iid, timestamp="2026-05-26T01:00:00Z", source="supabase",
                       user_input=uin, agent_output="", tool_calls=[],
                       execution_error="Traceback boom", latency_ms=100, raw={})


def test_build_repro_case_real_schema():
    case = build_repro_case(_interaction("como va la cartera"))
    assert case["pregunta"] == "como va la cartera"
    assert case["id"].startswith("qa-autofix-")
    assert "42" in case["id"]
    # arrays del esquema presentes y vacíos
    assert case["tools_esperadas"] == []
    assert case["debe_contener"] == []
    assert case["no_debe"] == []
    assert case["valor_esperado"] == []


def test_build_repro_case_rejects_empty_input():
    import pytest
    with pytest.raises(ReproError):
        build_repro_case(_interaction("   "))
