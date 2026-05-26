from qa.group import ErrorGroup
from qa.report import render_markdown

def test_render_includes_summary_and_groups():
    groups = [ErrorGroup(error_type="tool_error", signal="tool_call[q].ok=False",
                         severity="high", count=2, interaction_ids=["1", "2"],
                         examples=["boom"])]
    md = render_markdown(target="petramora", since="24h",
                         n_interactions=10, groups=groups,
                         sources_ok=["langfuse"], sources_failed=["supabase"])
    assert "# QA report — petramora" in md
    assert "24h" in md
    assert "10" in md
    assert "tool_error" in md
    assert "x2" in md or "count: 2" in md
    assert "supabase" in md

def test_render_no_errors():
    md = render_markdown(target="petramora", since="24h", n_interactions=5,
                         groups=[], sources_ok=["langfuse"], sources_failed=[])
    assert "Sin errores" in md
