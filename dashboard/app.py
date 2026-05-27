import os
import glob
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.config import load_dash_target
from qa.config import target_path
from dashboard.panels import errors, interactions, etl, freshness, runs, claude_health, plugins
from dashboard import exec as execmod

app = FastAPI(title="Agentic OS — Dashboard")

_HERE = os.path.dirname(__file__)
_STATIC = os.path.join(_HERE, "static")


def _load_cfg():
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    target = os.environ.get("DASH_TARGET", "petramora")
    return load_dash_target(target_path(os_dir, target))


def _safe(fn, *a, **kw):
    try:
        return JSONResponse(fn(*a, **kw))
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"})


@app.get("/api/errors")
def api_errors():
    cfg = _load_cfg(); return _safe(errors.data, cfg, cfg.default_since)

@app.get("/api/interactions")
def api_interactions():
    cfg = _load_cfg(); return _safe(interactions.data, cfg, cfg.default_since)

@app.get("/api/etl")
def api_etl():
    cfg = _load_cfg(); return _safe(etl.data, cfg)

@app.get("/api/freshness")
def api_freshness():
    cfg = _load_cfg(); return _safe(freshness.data, cfg)

@app.get("/api/runs")
def api_runs():
    cfg = _load_cfg(); return _safe(runs.data, cfg)

@app.get("/api/claude-health")
def api_claude_health():
    cfg = _load_cfg(); return _safe(claude_health.data, cfg)


@app.get("/api/plugins")
def api_plugins():
    cfg = _load_cfg(); return _safe(plugins.data, cfg)


@app.get("/api/report")
def api_report():
    def _read():
        os_dir = os.environ.get("OS_DIR", os.getcwd())
        d = os.path.join(os_dir, "qa-reports", "petramora")
        files = sorted(glob.glob(os.path.join(d, "*.md")))
        if not files:
            return {"ok": True, "fecha": None, "contenido": "(sin informes todavía)"}
        p = files[-1]
        with open(p, encoding="utf-8") as fh:
            return {"ok": True, "fecha": os.path.basename(p)[:-3], "contenido": fh.read()}
    return _safe(_read)


@app.get("/api/cron-log")
def api_cron_log():
    def _read():
        cfg = _load_cfg()
        os_dir = os.environ.get("OS_DIR", os.getcwd())
        p = os.path.join(os_dir, cfg.cron_log) if cfg.cron_log else None
        if not p or not os.path.isfile(p):
            return {"ok": True, "texto": "(sin cron.log todavía)"}
        with open(p, encoding="utf-8") as fh:
            return {"ok": True, "texto": fh.read()}
    return _safe(_read)


@app.post("/api/run")
async def api_run(req: Request):
    body = await req.json()
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    return _safe(execmod.run_prompt, (body or {}).get("prompt", ""), os_dir)


@app.post("/api/run-script")
async def api_run_script(req: Request):
    body = await req.json()
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    return _safe(execmod.run_script, (body or {}).get("id", ""), os_dir)


@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC, "index.html"))


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
