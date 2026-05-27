from fastapi.testclient import TestClient
import dashboard.app as appmod

class _Cfg:
    name="demo"; default_since="24h"
    supabase={"enabled": False}; etl={"table":"scraper_runs"}
    freshness={"tablas": []}; claude_logs_dir="/no/existe"; cron_log=""

def test_endpoints_ok_y_panel_caido_no_rompe(monkeypatch):
    monkeypatch.setattr(appmod, "_load_cfg", lambda: _Cfg())
    monkeypatch.setattr(appmod.etl, "data", lambda cfg: (_ for _ in ()).throw(RuntimeError("x")))
    c = TestClient(appmod.app)
    r = c.get("/api/runs"); assert r.status_code == 200 and r.json()["ok"] is True
    r = c.get("/api/etl"); assert r.status_code == 200 and r.json()["ok"] is False
    r = c.get("/"); assert r.status_code == 200 and "AGENTIC" in r.text.upper()
