from qa.autofix.runner import run_fix, FixResult

CASE = {"id": "qa-autofix-42", "pregunta": "x", "tools_esperadas": [],
        "debe_contener": [], "no_debe": [], "valor_esperado": []}

def test_dry_run_does_not_execute():
    calls = []
    def fake_exec(prompt, cwd):
        calls.append((prompt, cwd))
        return "PR_URL=http://nope"
    res = run_fix(CASE, modo="comercial", branch="qa-autofix/x", base="master",
                  worktree="/wt", executor=fake_exec, dry_run=True)
    assert isinstance(res, FixResult)
    assert res.status == "dry_run"
    assert calls == []
    assert "comercial" in res.detail   # el prompt menciona el modo

def test_opened_pr_parsed():
    def fake_exec(prompt, cwd):
        return "blah\nPR_URL=https://github.com/ericlb12/Petramora_source/pull/7\n"
    res = run_fix(CASE, modo="comercial", branch="qa-autofix/x", base="master",
                  worktree="/wt", executor=fake_exec, dry_run=False)
    assert res.status == "opened_pr"
    assert res.pr_url.endswith("/pull/7")

def test_failed_when_no_pr_url():
    def fake_exec(prompt, cwd):
        return "RESULT=failed\n"
    res = run_fix(CASE, modo="comercial", branch="qa-autofix/x", base="master",
                  worktree="/wt", executor=fake_exec, dry_run=False)
    assert res.status == "failed"
    assert res.pr_url is None
