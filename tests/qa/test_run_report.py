import os
from qa.model import Interaction, ToolCall
from qa.report import run_report


def test_run_report_writes_file(tmp_path):
    interactions = [
        Interaction(id="1", timestamp="2026-05-26T01:00:00Z", source="langfuse",
                    user_input="x", agent_output="", tool_calls=[ToolCall("q", False, "boom")],
                    execution_error=None, latency_ms=100, raw={}),
    ]
    out = run_report(target="petramora", since="24h", interactions=interactions,
                     sources_ok=["langfuse"], sources_failed=[],
                     out_dir=str(tmp_path))
    assert os.path.isfile(out)
    content = open(out).read()
    assert "QA report — petramora" in content
    assert "tool_error" in content
