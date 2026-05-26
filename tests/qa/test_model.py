from qa.model import Interaction, ToolCall, ErrorFinding

def test_interaction_minimal_construct():
    i = Interaction(
        id="t1", timestamp="2026-05-26T01:00:00Z", source="langfuse",
        user_input="hola", agent_output="respuesta",
        tool_calls=[ToolCall(name="get_x", ok=True, message=None)],
        execution_error=None, latency_ms=1200, raw={"k": "v"},
    )
    assert i.id == "t1"
    assert i.tool_calls[0].name == "get_x"
    assert i.has_tool_error() is False

def test_interaction_detects_tool_error():
    i = Interaction(
        id="t2", timestamp="2026-05-26T01:00:00Z", source="supabase",
        user_input="x", agent_output="", tool_calls=[ToolCall(name="q", ok=False, message="boom")],
        execution_error=None, latency_ms=None, raw={},
    )
    assert i.has_tool_error() is True

def test_error_finding_construct():
    e = ErrorFinding(interaction_id="t2", error_type="tool_error",
                     signal="tool_call.ok=False", severity="high", excerpt="boom")
    assert e.error_type == "tool_error"
