from qa.sources.supabase import normalize_row
from qa.model import Interaction


def test_normalize_row_to_interaction():
    row = {
        "id": 42,
        "timestamp": "2026-05-26T01:00:00Z",
        "session_id": "s1",
        "user_message": "hola",
        "agent_response": "",
        "tools_called": [{"name": "get_x", "args": {}}],
        "model_used": "gemini",
        "latency_ms": 5000,
        "error": "Respuesta vacía",
    }
    i = normalize_row(row)
    assert isinstance(i, Interaction)
    assert i.id == "42"
    assert i.source == "supabase"
    assert i.user_input == "hola"
    assert i.agent_output == ""
    assert i.execution_error == "Respuesta vacía"
    assert i.latency_ms == 5000
    assert i.tool_calls[0].name == "get_x"
    assert i.tool_calls[0].ok is True


def test_normalize_row_handles_missing_tools_and_error():
    row = {"id": 1, "timestamp": "t", "user_message": "x", "agent_response": "ok"}
    i = normalize_row(row)
    assert i.tool_calls == []
    assert i.execution_error is None
