from fastapi.testclient import TestClient
import dashboard.app as appmod


def test_run_endpoint(monkeypatch):
    monkeypatch.setattr(appmod.execmod, "run_prompt",
                        lambda texto, os_dir, **k: {"ok": True, "output": "hecho:" + texto})
    c = TestClient(appmod.app)
    r = c.post("/api/run", json={"prompt": "hola"})
    assert r.status_code == 200
    assert r.json()["ok"] is True and "hecho:hola" in r.json()["output"]


def test_run_script_endpoint(monkeypatch):
    monkeypatch.setattr(appmod.execmod, "run_script",
                        lambda sid, os_dir, **k: {"ok": True, "output": "script:" + sid})
    c = TestClient(appmod.app)
    r = c.post("/api/run-script", json={"id": "informe_qa"})
    assert r.status_code == 200
    assert r.json()["output"] == "script:informe_qa"
