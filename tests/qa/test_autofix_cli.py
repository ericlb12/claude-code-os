from qa.model import Interaction
from qa.autofix.cli import autofix_interaction


def _fetch_ok(iid):
    return Interaction(id=iid, timestamp="t", source="supabase",
                       user_input="como va la cartera", agent_output="",
                       tool_calls=[], execution_error="boom", latency_ms=1, raw={})


def _exec_pr(prompt, cwd):
    return "PR_URL=https://github.com/ericlb12/Petramora_source/pull/9"


def test_happy_path():
    res = autofix_interaction("42", modo="comercial", base="master", worktree="/wt",
                              fetch=_fetch_ok, executor=_exec_pr, dry_run=False)
    assert res.status == "opened_pr"
    assert res.branch.startswith("qa-autofix/")


def test_skips_unreproducible():
    def _fetch_empty(iid):
        return Interaction(id=iid, timestamp="t", source="supabase", user_input="  ",
                           agent_output="", tool_calls=[], execution_error="boom",
                           latency_ms=1, raw={})
    res = autofix_interaction("42", modo="comercial", base="master", worktree="/wt",
                              fetch=_fetch_empty, executor=_exec_pr, dry_run=False)
    assert res.status == "failed"
    assert "reproducible" in res.detail


def test_not_found():
    res = autofix_interaction("99", modo="comercial", base="master", worktree="/wt",
                              fetch=lambda iid: None, executor=_exec_pr, dry_run=False)
    assert res.status == "failed"
