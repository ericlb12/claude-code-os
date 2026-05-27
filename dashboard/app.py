import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.config import load_dash_target
from qa.config import target_path
from dashboard.panels import errors, interactions, etl, freshness, runs, claude_health

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


@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC, "index.html"))


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
