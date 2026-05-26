import json, os
from qa.sources.langfuse import normalize_trace
from qa.model import Interaction

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "langfuse_trace.json")

def test_normalize_trace_to_interaction():
    with open(FIX) as fh:
        trace = json.load(fh)
    i = normalize_trace(trace)
    assert isinstance(i, Interaction)
    assert i.id == "trace-1"
    assert i.source == "langfuse"
    assert i.user_input == "como va la cartera"
    assert i.agent_output == "aqui tienes"
    assert i.tool_calls[0].name == "get_segment_distribution"
    assert i.latency_ms == 1200
