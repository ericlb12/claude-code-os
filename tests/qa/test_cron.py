import os
from qa.model import Interaction
from qa.cron import nightly

def _interactions():
    return [Interaction(id="1", timestamp="t", source="supabase", user_input="x",
                        agent_output="out", tool_calls=[], execution_error="boom",
                        latency_ms=1, raw={})]

def _gather_ok(cfg, since):
    return _interactions(), ["supabase"], []

def _gather_boom(cfg, since):
    raise RuntimeError("sin credenciales")

class _Cfg:
    name = "petramora"; default_since = "24h"
    langfuse = {"enabled": False}; supabase = {"enabled": True}

def test_nightly_writes_report_and_ok_log(tmp_path):
    path = nightly(os_dir=str(tmp_path), target="petramora", since="24h",
                   load=lambda od, t: _Cfg(), gather=_gather_ok)
    assert path is not None and os.path.isfile(path)
    log = open(os.path.join(str(tmp_path), "qa-reports", "petramora", "cron.log")).read()
    assert "| ok |" in log
    assert "interacciones=1" in log
    assert "grupos_error=1" in log

def test_nightly_logs_fail_on_gather_error(tmp_path):
    path = nightly(os_dir=str(tmp_path), target="petramora", since="24h",
                   load=lambda od, t: _Cfg(), gather=_gather_boom)
    assert path is None
    log = open(os.path.join(str(tmp_path), "qa-reports", "petramora", "cron.log")).read()
    assert "| FAIL |" in log
    assert "sin credenciales" in log
