from qa.model import ErrorFinding
from qa.group import group_findings, ErrorGroup

def _f(itype, sig, iid, sev="high"):
    return ErrorFinding(interaction_id=iid, error_type=itype, signal=sig, severity=sev, excerpt="")

def test_groups_by_type_and_signal():
    findings = [
        _f("tool_error", "tool_call[q].ok=False", "1"),
        _f("tool_error", "tool_call[q].ok=False", "2"),
        _f("timeout", "latency", "3", sev="medium"),
    ]
    groups = group_findings(findings)
    assert isinstance(groups[0], ErrorGroup)
    assert groups[0].count == 2
    assert groups[0].error_type == "tool_error"
    assert set(groups[0].interaction_ids) == {"1", "2"}

def test_priority_high_before_medium_on_tie():
    findings = [_f("timeout", "l", "1", sev="medium"), _f("tool_error", "t", "2", sev="high")]
    groups = group_findings(findings)
    assert groups[0].error_type == "tool_error"

def test_empty_input():
    assert group_findings([]) == []

def test_timeouts_aggregate_into_one_group():
    from qa.detect import detect_errors, TIMEOUT_MS
    from qa.model import Interaction
    def _i(iid, lat):
        return Interaction(id=iid, timestamp="t", source="supabase", user_input="x",
                           agent_output="ok", tool_calls=[], execution_error=None,
                           latency_ms=lat, raw={})
    findings = detect_errors([_i("1", TIMEOUT_MS + 100), _i("2", TIMEOUT_MS + 9999)])
    groups = group_findings(findings)
    timeout_groups = [g for g in groups if g.error_type == "timeout"]
    assert len(timeout_groups) == 1
    assert timeout_groups[0].count == 2
