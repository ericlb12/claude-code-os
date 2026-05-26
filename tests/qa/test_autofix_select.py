from qa.model import ErrorFinding
from qa.autofix.select import reproducible_interaction_ids


def _f(itype, iid):
    return ErrorFinding(interaction_id=iid, error_type=itype, signal="s", severity="high", excerpt="x")


def test_picks_only_execution_errors():
    findings = [_f("execution_error", "1"), _f("timeout", "2"),
                _f("execution_error", "1"), _f("explicit_error", "3")]
    assert reproducible_interaction_ids(findings) == ["1"]


def test_empty():
    assert reproducible_interaction_ids([]) == []
