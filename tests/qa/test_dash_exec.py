from dashboard import exec as ex

def _fake_ok(cmd, cwd):
    return 0, "salida simulada: " + " ".join(cmd[-2:])

def _fake_boom(cmd, cwd):
    raise RuntimeError("explota")

def test_run_prompt_ok():
    out = ex.run_prompt("dame el estado", os_dir="/wd", executor=_fake_ok)
    assert out["ok"] is True
    assert "salida simulada" in out["output"]

def test_run_prompt_error():
    out = ex.run_prompt("x", os_dir="/wd", executor=_fake_boom)
    assert out["ok"] is False
    assert "explota" in out["error"]

def test_run_script_allowlisted():
    calls = {}
    def fake(cmd, cwd): calls["cmd"]=cmd; calls["cwd"]=cwd; return 0, "ok-script"
    out = ex.run_script("informe_qa", os_dir="/wd", executor=fake)
    assert out["ok"] is True and out["output"] == "ok-script"
    assert "qa.cron" in " ".join(calls["cmd"])

def test_run_script_rejects_unknown():
    out = ex.run_script("rm_rf_todo", os_dir="/wd", executor=lambda c, w: (0, "no deberia"))
    assert out["ok"] is False
    assert "permitido" in out["error"].lower()
