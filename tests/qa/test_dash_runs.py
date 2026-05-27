from dashboard.panels.runs import parse_cron_log


def test_parse_cron_log():
    text = (
        "2026-05-26T03:00Z | ok | interacciones=5 | grupos_error=0 | informe=qa-reports/petramora/2026-05-26.md\n"
        "2026-05-27T03:00Z | FAIL | RuntimeError: boom\n"
    )
    out = parse_cron_log(text)
    assert out["ok"] is True
    assert out["total"] == 2
    assert out["runs"][0]["status"] == "FAIL"
    assert out["runs"][1]["status"] == "ok"
    assert out["runs"][1]["interacciones"] == "5"
