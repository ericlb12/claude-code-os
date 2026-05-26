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
