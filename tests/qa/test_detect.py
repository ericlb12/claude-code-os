from qa.model import Interaction, ToolCall
from qa.detect import detect_errors, TIMEOUT_MS

def _base(**kw):
    d = dict(id="i", timestamp="2026-05-26T01:00:00Z", source="langfuse",
             user_input="x", agent_output="ok", tool_calls=[],
             execution_error=None, latency_ms=100, raw={})
    d.update(kw)
    return Interaction(**d)

def test_tool_error_detected():
    i = _base(id="a", tool_calls=[ToolCall("q", ok=False, message="boom")])
    f = detect_errors([i])
    assert len(f) == 1 and f[0].error_type == "tool_error" and f[0].interaction_id == "a"

def test_execution_error_detected():
    f = detect_errors([_base(id="b", execution_error="Traceback ...")])
    assert any(x.error_type == "execution_error" for x in f)

def test_empty_output_detected():
    f = detect_errors([_base(id="c", agent_output="")])
    assert any(x.error_type == "empty_output" for x in f)

def test_timeout_detected():
    f = detect_errors([_base(id="d", latency_ms=TIMEOUT_MS + 1)])
    assert any(x.error_type == "timeout" for x in f)

def test_explicit_error_field_detected():
    f = detect_errors([_base(id="e", raw={"error": "rate_limit"})])
    assert any(x.error_type == "explicit_error" for x in f)

def test_clean_interaction_yields_nothing():
    assert detect_errors([_base(id="f")]) == []
