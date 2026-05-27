# Dashboard v1 (Monitorización) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un dashboard FastAPI local (paquete `dashboard/`) que reúsa `qa/` y muestra 6 paneles de monitorización (salud Claude Code, runs, errores, interacciones, ETL scrapers, frescura BBDD) con datos reales, solo lectura.

**Architecture:** FastAPI sirve `static/index.html` + un endpoint `/api/<panel>` por panel. Cada panel es un módulo con una función `data(...)` cuyo I/O de red se inyecta (testeable con fixtures, sin red). Un panel que falla devuelve `{"ok": false, "error": ...}` y no tumba la página. Reúsa `qa.report.gather`, `qa.detect`, `qa.group`, `qa.sources.supabase`.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, pytest, FastAPI TestClient (httpx). venv nativo WSL. HTML/CSS/JS vanilla (JS construye DOM con textContent — sin innerHTML, sin XSS).

> **Setup (una vez por shell):**
> ```bash
> export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
> PY=~/.venvs/claude_code_os/bin/python   # venv NATIVO WSL (NO crear venv en Dropbox)
> ```
> Tests en `tests/qa/` SIN `__init__.py`; `conftest.py` ya en la raíz (mete la raíz del repo en sys.path).

---

## File Structure

- `dashboard/__init__.py`
- `dashboard/config.py` — carga target extendido (secciones `freshness`, `etl`)
- `dashboard/panels/__init__.py`
- `dashboard/panels/errors.py` · `interactions.py` · `etl.py` · `freshness.py` · `runs.py` · `claude_health.py`
- `dashboard/app.py` — FastAPI (endpoints + servir static)
- `dashboard/static/index.html` · `dashboard.css` · `dashboard.js`
- `scripts/dashboard.sh` — lanzador uvicorn
- `tests/qa/test_dash_*.py` — tests
- `RECON_DASH.md` — recon (Task 0)

Reutilizable existente: `qa.report.gather(cfg, since) -> (interactions, ok, failed)`, `qa.detect.detect_errors`, `qa.group.group_findings`, `qa.sources.supabase._client(cfg_section)` y `normalize_row`, `qa.config.load_target/target_path`, `qa.model.Interaction`.

---

## Task 0: Recon — formato de logs Claude Code + columnas Supabase + extender target

Solo lectura + escribir RECON_DASH.md + extender petramora.yaml.

**Files:** Create `$OS_DIR/RECON_DASH.md`; Modify `$OS_DIR/qa/targets/petramora.yaml`

- [ ] **Step 1: Inspeccionar logs locales de Claude Code**

```bash
ls -la ~/.claude 2>&1 | head
ls ~/.claude/projects 2>/dev/null | head
f=$(find ~/.claude/projects -name '*.jsonl' 2>/dev/null | head -1); echo "$f"; head -1 "$f" 2>/dev/null | cut -c1-400
```
Expected: ver si hay `*.jsonl` de sesiones y qué campos trae cada línea (busca `usage`, `input_tokens`, `output_tokens`, `timestamp`). Anotar en RECON_DASH.md si se puede calcular uso por día o si solo se puede contar nº de entradas (degradación).

- [ ] **Step 2: Confirmar columnas reales de scraper_runs y tablas de frescura**

```bash
ENV="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
cd "$OS_DIR"; set -a; source "$ENV" 2>/dev/null; set +a
~/.venvs/claude_code_os/bin/python - <<'PY'
import os
from supabase import create_client
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
for t in ["scraper_runs","segmentacion_clientes_raw","agent_logs"]:
    try:
        r = c.table(t).select("*").limit(1).execute().data
        print(t, "->", list(r[0].keys()) if r else "vacía")
    except Exception as e:
        print(t, "ERROR", type(e).__name__, str(e)[:80])
PY
```
Expected: las claves reales de cada tabla. Confirmar `scraper_runs` (run_at, status, products_found...) y `segmentacion_clientes_raw.fecha_corte`. Anotar.

- [ ] **Step 3: Extender `$OS_DIR/qa/targets/petramora.yaml`** añadiendo estas secciones (sin tocar `langfuse`/`supabase`):
```yaml
etl:
  table: scraper_runs
  run_at_col: run_at
  status_col: status
freshness:
  tablas:
    - { tabla: scraper_runs, col: run_at, umbral_dias: 2 }
    - { tabla: segmentacion_clientes_raw, col: fecha_corte, umbral_dias: 35 }
    - { tabla: agent_logs, col: timestamp, umbral_dias: 2 }
claude_logs_dir: "~/.claude/projects"
cron_log: "qa-reports/petramora/cron.log"
```
(Ajustar `col`/`umbral_dias` a lo confirmado en Step 2 si difiere; p.ej. si `agent_logs` usa `timestamp` o `created_at`.)

- [ ] **Step 4: Escribir RECON_DASH.md** con: formato de logs Claude Code (campos de uso o "solo conteo"), columnas reales de las 3 tablas, y confirmación de la config añadida.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add RECON_DASH.md qa/targets/petramora.yaml && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: recon logs Claude Code + extender target (etl/freshness)"
```

> **Checkpoint:** lo de Step 1 decide si `claude_health` muestra tokens o degrada a conteo. El resto no se bloquea.

---

## Task 1: Scaffold dashboard + deps

**Files:** Create `$OS_DIR/dashboard/__init__.py`, `$OS_DIR/dashboard/panels/__init__.py`

- [ ] **Step 1: Instalar deps en el venv nativo**

```bash
~/.venvs/claude_code_os/bin/pip install -q fastapi uvicorn httpx
printf "fastapi\nuvicorn\nhttpx\n" >> "$OS_DIR/requirements.txt"
```

- [ ] **Step 2: Crear paquete**

```bash
cd "$OS_DIR" && mkdir -p dashboard/panels dashboard/static && touch dashboard/__init__.py dashboard/panels/__init__.py
```

- [ ] **Step 3: Verificar imports**

Run: `cd "$OS_DIR" && $PY -c "import fastapi, uvicorn, httpx, dashboard, dashboard.panels; print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard requirements.txt && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "chore: scaffold paquete dashboard + deps fastapi/uvicorn"
```

---

## Task 2: `dashboard/config.py` — cargar target extendido

**Files:** Create `$OS_DIR/dashboard/config.py`, `$OS_DIR/tests/qa/test_dash_config.py`, `$OS_DIR/tests/qa/fixtures/dash_target.yaml`

- [ ] **Step 1: Fixture + test que fallan**

`$OS_DIR/tests/qa/fixtures/dash_target.yaml`:
```yaml
name: demo
default_since: 24h
supabase: { enabled: true, url_env: SUPABASE_URL, key_env: SUPABASE_KEY, table: agent_logs }
etl: { table: scraper_runs, run_at_col: run_at, status_col: status }
freshness:
  tablas:
    - { tabla: scraper_runs, col: run_at, umbral_dias: 2 }
claude_logs_dir: "~/.claude/projects"
cron_log: "qa-reports/demo/cron.log"
```

`$OS_DIR/tests/qa/test_dash_config.py`:
```python
import os
from dashboard.config import load_dash_target

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "dash_target.yaml")

def test_load_dash_target():
    cfg = load_dash_target(FIX)
    assert cfg.supabase["table"] == "agent_logs"
    assert cfg.etl["table"] == "scraper_runs"
    assert cfg.freshness["tablas"][0]["tabla"] == "scraper_runs"
    assert cfg.claude_logs_dir == "~/.claude/projects"
    assert cfg.cron_log == "qa-reports/demo/cron.log"
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_config.py -v`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/config.py`**

```python
import os
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class DashConfig:
    name: str
    default_since: str
    supabase: dict[str, Any]
    etl: dict[str, Any]
    freshness: dict[str, Any]
    claude_logs_dir: str
    cron_log: str


def load_dash_target(path: str) -> DashConfig:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        d = yaml.safe_load(fh) or {}
    return DashConfig(
        name=d.get("name", ""),
        default_since=d.get("default_since", "24h"),
        supabase=d.get("supabase", {"enabled": False}),
        etl=d.get("etl", {}),
        freshness=d.get("freshness", {"tablas": []}),
        claude_logs_dir=d.get("claude_logs_dir", "~/.claude/projects"),
        cron_log=d.get("cron_log", ""),
    )
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/config.py tests/qa/test_dash_config.py tests/qa/fixtures/dash_target.yaml && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard.config (target extendido etl/freshness)"
```

---

## Task 3: panel `errors`

**Files:** Create `$OS_DIR/dashboard/panels/errors.py`, `$OS_DIR/tests/qa/test_dash_errors.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_errors.py`:
```python
from qa.model import Interaction
from dashboard.panels.errors import data

def _fake_gather(cfg, since):
    inter = [Interaction(id="1", timestamp="t", source="supabase", user_input="x",
                         agent_output="", tool_calls=[], execution_error="boom",
                         latency_ms=1, raw={})]
    return inter, ["supabase"], []

def test_errors_panel_groups():
    out = data(cfg=None, since="24h", gather=_fake_gather)
    assert out["ok"] is True
    assert out["n_interactions"] == 1
    assert out["grupos"][0]["error_type"] == "execution_error"
    assert out["grupos"][0]["count"] == 1
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_errors.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/errors.py`**

```python
from qa.detect import detect_errors
from qa.group import group_findings


def data(cfg, since="24h", gather=None):
    """Panel de errores: reúsa el pipeline QA. gather inyectable para tests."""
    if gather is None:
        from qa.report import gather as gather
    interactions, ok, failed = gather(cfg, since)
    groups = group_findings(detect_errors(interactions))
    return {
        "ok": True,
        "n_interactions": len(interactions),
        "sources_failed": failed,
        "grupos": [
            {"error_type": g.error_type, "signal": g.signal, "severity": g.severity,
             "count": g.count, "interaction_ids": g.interaction_ids[:10],
             "ejemplos": g.examples}
            for g in groups
        ],
    }
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_errors.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/errors.py tests/qa/test_dash_errors.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel errores (reusa QA)"
```

---

## Task 4: panel `interactions`

**Files:** Create `$OS_DIR/dashboard/panels/interactions.py`, `$OS_DIR/tests/qa/test_dash_interactions.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_interactions.py`:
```python
from qa.model import Interaction
from dashboard.panels.interactions import data

def _gather(cfg, since):
    inter = [
        Interaction(id="1", timestamp="t1", source="supabase", user_input="hola mundo",
                    agent_output="ok", tool_calls=[], execution_error=None, latency_ms=1, raw={}),
        Interaction(id="2", timestamp="t2", source="supabase", user_input="otra",
                    agent_output="", tool_calls=[], execution_error="boom", latency_ms=1, raw={}),
    ]
    return inter, ["supabase"], []

def test_interactions_counts():
    out = data(cfg=None, since="24h", gather=_gather)
    assert out["ok"] is True
    assert out["total"] == 2
    assert out["con_error"] == 1
    assert out["recientes"][0]["id"] == "1"
    assert out["recientes"][0]["input"].startswith("hola")
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_interactions.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/interactions.py`**

```python
def data(cfg, since="24h", gather=None):
    if gather is None:
        from qa.report import gather as gather
    interactions, ok, failed = gather(cfg, since)
    total = len(interactions)
    con_error = sum(1 for i in interactions if i.execution_error)
    recientes = [
        {"id": i.id, "ts": i.timestamp, "input": (i.user_input or "")[:80],
         "error": bool(i.execution_error)}
        for i in interactions[:10]
    ]
    return {"ok": True, "total": total, "con_error": con_error,
            "sources_failed": failed, "recientes": recientes}
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_interactions.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/interactions.py tests/qa/test_dash_interactions.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel interacciones"
```

---

## Task 5: panel `etl`

**Files:** Create `$OS_DIR/dashboard/panels/etl.py`, `$OS_DIR/tests/qa/test_dash_etl.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_etl.py`:
```python
from dashboard.panels.etl import summarize_runs

def test_summarize_runs():
    rows = [
        {"run_at": "2026-05-27T03:00:00Z", "status": "success", "products_found": 120,
         "products_updated": 30, "alerts_generated": 2, "error_message": None},
        {"run_at": "2026-05-26T03:00:00Z", "status": "error", "products_found": 0,
         "products_updated": 0, "alerts_generated": 0, "error_message": "timeout"},
    ]
    out = summarize_runs(rows)
    assert out["ok"] is True
    assert out["ultima"]["status"] == "success"
    assert out["ultima"]["run_at"].startswith("2026-05-27")
    assert out["total_runs"] == 2
    assert out["ultimo_error"]["error_message"] == "timeout"
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_etl.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/etl.py`**

```python
def summarize_runs(rows: list[dict]) -> dict:
    """Resume filas de scraper_runs (ordenadas desc por run_at). Puro, testeable."""
    if not rows:
        return {"ok": True, "total_runs": 0, "ultima": None, "ultimo_error": None}
    ultima = rows[0]
    ultimo_error = next((r for r in rows if r.get("status") == "error"), None)
    return {
        "ok": True,
        "total_runs": len(rows),
        "ultima": {"run_at": ultima.get("run_at"), "status": ultima.get("status"),
                   "products_found": ultima.get("products_found"),
                   "products_updated": ultima.get("products_updated"),
                   "alerts_generated": ultima.get("alerts_generated")},
        "ultimo_error": ({"run_at": ultimo_error.get("run_at"),
                          "error_message": ultimo_error.get("error_message")}
                         if ultimo_error else None),
    }


def data(cfg, fetch=None):
    try:
        rows = (fetch or _fetch)(cfg)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return summarize_runs(rows)


def _fetch(cfg) -> list[dict]:
    from qa.sources.supabase import _client
    etl = cfg.etl
    client = _client(cfg.supabase)
    return (client.table(etl["table"]).select("*")
            .order(etl.get("run_at_col", "run_at"), desc=True).limit(50).execute().data or [])
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_etl.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/etl.py tests/qa/test_dash_etl.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel ETL (scraper_runs)"
```

---

## Task 6: panel `freshness`

**Files:** Create `$OS_DIR/dashboard/panels/freshness.py`, `$OS_DIR/tests/qa/test_dash_freshness.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_freshness.py`:
```python
from datetime import datetime, timezone, timedelta
from dashboard.panels.freshness import evaluar

def test_evaluar_al_dia_y_desfasado():
    hoy = datetime.now(timezone.utc)
    reciente = (hoy - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    viejo = (hoy - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    specs = [
        {"tabla": "a", "col": "run_at", "umbral_dias": 2},
        {"tabla": "b", "col": "run_at", "umbral_dias": 2},
    ]
    maxfechas = {"a": reciente, "b": viejo}
    out = evaluar(specs, maxfechas)
    assert out["ok"] is True
    by = {t["tabla"]: t for t in out["tablas"]}
    assert by["a"]["al_dia"] is True
    assert by["b"]["al_dia"] is False
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_freshness.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/freshness.py`**

```python
from datetime import datetime, timezone


def _parse(ts: str):
    if not ts:
        return None
    s = str(ts).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.fromisoformat(str(ts)[:10])
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def evaluar(specs: list[dict], maxfechas: dict) -> dict:
    """specs: [{tabla,col,umbral_dias}]; maxfechas: {tabla: max_fecha}. Puro."""
    ahora = datetime.now(timezone.utc)
    tablas = []
    for s in specs:
        dt = _parse(maxfechas.get(s["tabla"]))
        if dt is None:
            tablas.append({"tabla": s["tabla"], "al_dia": False, "ultima": None, "dias": None})
            continue
        dias = (ahora - dt).total_seconds() / 86400
        tablas.append({"tabla": s["tabla"], "al_dia": dias <= s["umbral_dias"],
                       "ultima": maxfechas.get(s["tabla"]), "dias": round(dias, 1)})
    return {"ok": True, "tablas": tablas}


def data(cfg, fetch_max=None):
    specs = cfg.freshness.get("tablas", [])
    try:
        getter = fetch_max or _fetch_max
        maxfechas = {s["tabla"]: getter(cfg, s["tabla"], s["col"]) for s in specs}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return evaluar(specs, maxfechas)


def _fetch_max(cfg, tabla: str, col: str):
    from qa.sources.supabase import _client
    client = _client(cfg.supabase)
    rows = (client.table(tabla).select(col).order(col, desc=True).limit(1).execute().data or [])
    return rows[0][col] if rows else None
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_freshness.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/freshness.py tests/qa/test_dash_freshness.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel frescura BBDD"
```

---

## Task 7: panel `runs`

**Files:** Create `$OS_DIR/dashboard/panels/runs.py`, `$OS_DIR/tests/qa/test_dash_runs.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_runs.py`:
```python
from dashboard.panels.runs import parse_cron_log

def test_parse_cron_log():
    text = (
        "2026-05-26T03:00Z | ok | interacciones=5 | grupos_error=0 | informe=qa-reports/petramora/2026-05-26.md\n"
        "2026-05-27T03:00Z | FAIL | RuntimeError: boom\n"
    )
    out = parse_cron_log(text)
    assert out["ok"] is True
    assert out["total"] == 2
    assert out["runs"][0]["status"] == "FAIL"      # más reciente primero
    assert out["runs"][1]["status"] == "ok"
    assert out["runs"][1]["interacciones"] == "5"
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_runs.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/runs.py`**

```python
import os


def parse_cron_log(text: str) -> dict:
    """Parsea líneas 'ts | ok|FAIL | k=v | ...'. Runs más reciente primero."""
    runs = []
    for line in [l for l in text.splitlines() if l.strip()]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        entry = {"ts": parts[0], "status": parts[1]}
        for p in parts[2:]:
            if "=" in p:
                k, v = p.split("=", 1)
                entry[k.strip()] = v.strip()
        runs.append(entry)
    runs.reverse()
    return {"ok": True, "total": len(runs), "runs": runs[:15]}


def data(cfg, os_dir=None):
    os_dir = os_dir or os.environ.get("OS_DIR", os.getcwd())
    path = os.path.join(os_dir, cfg.cron_log) if cfg.cron_log else None
    if not path or not os.path.isfile(path):
        return {"ok": True, "total": 0, "runs": [], "nota": "sin cron.log todavía"}
    with open(path, "r", encoding="utf-8") as fh:
        out = parse_cron_log(fh.read())
    out["proximo_cron"] = "03:00 (diario)"
    return out
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_runs.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/runs.py tests/qa/test_dash_runs.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel runs (cron.log)"
```

---

## Task 8: panel `claude_health`

Lee los `*.jsonl` de `~/.claude/projects`. Suma uso si el formato lo trae; si no, cuenta entradas por día (degradación, según RECON_DASH.md). El resumen es puro y testeable.

**Files:** Create `$OS_DIR/dashboard/panels/claude_health.py`, `$OS_DIR/tests/qa/test_dash_claude_health.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_claude_health.py`:
```python
from dashboard.panels.claude_health import resumir

def test_resumir_con_uso():
    eventos = [
        {"ts": "2026-05-27T01:00:00Z", "input_tokens": 100, "output_tokens": 50},
        {"ts": "2026-05-27T02:00:00Z", "input_tokens": 200, "output_tokens": 80},
        {"ts": "2026-05-26T01:00:00Z", "input_tokens": 10, "output_tokens": 5},
    ]
    out = resumir(eventos)
    assert out["ok"] is True
    assert out["total_eventos"] == 3
    assert out["tokens_in"] == 310
    assert out["tokens_out"] == 135
    dias = {d["dia"]: d for d in out["actividad_por_dia"]}
    assert dias["2026-05-27"]["eventos"] == 2

def test_resumir_sin_tokens_degrada_a_conteo():
    eventos = [{"ts": "2026-05-27T01:00:00Z"}, {"ts": "2026-05-27T02:00:00Z"}]
    out = resumir(eventos)
    assert out["tokens_in"] == 0
    assert out["total_eventos"] == 2
    assert out["actividad_por_dia"][0]["eventos"] == 2
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_claude_health.py -v`

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/panels/claude_health.py`**

```python
import os
import glob
import json


def resumir(eventos: list[dict]) -> dict:
    """eventos: [{ts, input_tokens?, output_tokens?}]. Suma uso + serie por día. Puro."""
    tokens_in = sum(int(e.get("input_tokens") or 0) for e in eventos)
    tokens_out = sum(int(e.get("output_tokens") or 0) for e in eventos)
    por_dia: dict[str, dict] = {}
    for e in eventos:
        dia = str(e.get("ts", ""))[:10]
        if not dia:
            continue
        d = por_dia.setdefault(dia, {"dia": dia, "eventos": 0, "tokens": 0})
        d["eventos"] += 1
        d["tokens"] += int(e.get("input_tokens") or 0) + int(e.get("output_tokens") or 0)
    serie = sorted(por_dia.values(), key=lambda d: d["dia"], reverse=True)
    return {"ok": True, "total_eventos": len(eventos), "tokens_in": tokens_in,
            "tokens_out": tokens_out, "actividad_por_dia": serie}


def _leer_eventos(logs_dir: str) -> list[dict]:
    """Extrae eventos de los *.jsonl de Claude Code. Tolerante al formato."""
    base = os.path.expanduser(logs_dir)
    eventos = []
    for f in glob.glob(os.path.join(base, "**", "*.jsonl"), recursive=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = o.get("timestamp") or o.get("ts") or ""
                    usage = o.get("usage") or (o.get("message") or {}).get("usage") or {}
                    eventos.append({"ts": ts,
                                    "input_tokens": usage.get("input_tokens"),
                                    "output_tokens": usage.get("output_tokens")})
        except OSError:
            continue
    return eventos


def data(cfg):
    try:
        eventos = _leer_eventos(cfg.claude_logs_dir)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return resumir(eventos)
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_claude_health.py -v`

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/panels/claude_health.py tests/qa/test_dash_claude_health.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard panel salud Claude Code (uso/actividad)"
```

---

## Task 9: `dashboard/app.py` — FastAPI + endpoints + servir static

**Files:** Create `$OS_DIR/dashboard/app.py`, `$OS_DIR/dashboard/static/index.html` (placeholder), `$OS_DIR/tests/qa/test_dash_app.py`

- [ ] **Step 1: Test que falla**

`$OS_DIR/tests/qa/test_dash_app.py`:
```python
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
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_app.py -v`

- [ ] **Step 3: Crear placeholder `$OS_DIR/dashboard/static/index.html`** (Task 10 lo completa)

```html
<!DOCTYPE html><html><head><meta charset="utf-8"><title>AGENTIC OS</title></head>
<body><h1>AGENTIC OS — Dashboard</h1></body></html>
```

- [ ] **Step 4: Implementar `$OS_DIR/dashboard/app.py`**

```python
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
```

- [ ] **Step 5: Correr → PASS + suite + commit**

```bash
cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_app.py -v && $PY -m pytest -q
git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/app.py dashboard/static/index.html tests/qa/test_dash_app.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard.app FastAPI (endpoints + servir static)"
```
Expected: endpoints 200, panel caído → ok:false, `/` sirve HTML; suite completa verde.

---

## Task 10: Frontend — `index.html` + `dashboard.js` + `dashboard.css`

Página estilo vídeo (oscura) que consume los 6 endpoints. **El JS construye el DOM con `createElement`/`textContent` (NO `innerHTML`)** para evitar XSS al pintar datos reales de usuarios.

**Files:** Modify `$OS_DIR/dashboard/static/index.html`; Create `$OS_DIR/dashboard/static/dashboard.css`, `$OS_DIR/dashboard/static/dashboard.js`

- [ ] **Step 1: Escribir `$OS_DIR/dashboard/static/dashboard.css`**

```css
:root{--bg:#0c0c0e;--panel:#161619;--border:#26262c;--muted:#8a8a92;--accent:#d2502a;--ok:#4ad07a;--text:#e8e8ea}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,sans-serif}
.nav{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;border-bottom:1px solid var(--border)}
.brand{font-weight:700;letter-spacing:2px}.brand b{color:var(--accent)}
.wrap{padding:16px;display:grid;grid-template-columns:2fr 1fr;gap:14px}
.meters{grid-column:1/-1;display:flex;gap:10px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px}
.card h3{margin:0 0 8px;font-size:11px;letter-spacing:1px;color:var(--muted);text-transform:uppercase}
.big{font-size:22px}.ok{color:var(--ok)}.bad{color:var(--accent)}.muted{color:var(--muted)}
.row{display:flex;justify-content:space-between;border-bottom:1px solid var(--border);padding:4px 0;font-size:12px;gap:10px}
.row span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
```

- [ ] **Step 2: Escribir `$OS_DIR/dashboard/static/index.html`** (sustituye el placeholder de Task 9)

```html
<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AGENTIC OS — Dashboard</title>
<link rel="stylesheet" href="/static/dashboard.css">
</head><body>
<div class="nav"><div class="brand">AGENTIC<b>OS</b></div><div class="muted" id="reloj"></div></div>
<div class="wrap">
  <div class="meters">
    <div class="card" style="flex:1"><h3>Claude Code · tokens</h3><div class="big" id="m-tokens">—</div></div>
    <div class="card" style="flex:1"><h3>Interacciones 24h</h3><div class="big" id="m-inter">—</div></div>
    <div class="card" style="flex:1"><h3>Errores 24h</h3><div class="big" id="m-err">—</div></div>
    <div class="card" style="flex:1"><h3>ETL último</h3><div class="big" id="m-etl">—</div></div>
  </div>
  <div class="card"><h3>Errores del agente — qué hacer</h3><div id="p-errors">cargando…</div></div>
  <div class="card"><h3>Runs recientes</h3><div id="p-runs">cargando…</div></div>
  <div class="card"><h3>Interacciones recientes</h3><div id="p-inter">cargando…</div></div>
  <div class="card"><h3>Frescura BBDD</h3><div id="p-fresh">cargando…</div></div>
  <div class="card" style="grid-column:1/-1"><h3>ETL / scrapers</h3><div id="p-etl">cargando…</div></div>
</div>
<script src="/static/dashboard.js"></script>
</body></html>
```

- [ ] **Step 3: Escribir `$OS_DIR/dashboard/static/dashboard.js`** (DOM seguro con textContent — sin innerHTML)

```javascript
async function get(p){ try{ const r=await fetch(p); return await r.json(); }catch(e){ return {ok:false,error:String(e)}; } }
function el(tag, cls, text){ const e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
function clear(node){ while(node.firstChild) node.removeChild(node.firstChild); }
function rowEl(left, right, rightCls){
  const r=el("div","row"); r.appendChild(el("span",null,left)); r.appendChild(el("span",rightCls,right)); return r;
}
function fill(id, ok, items, makeRow){
  const c=document.getElementById(id); clear(c);
  if(!ok){ c.appendChild(el("div","bad","no disponible")); return; }
  if(!items.length){ c.appendChild(el("div","muted","sin datos")); return; }
  items.forEach(it=>c.appendChild(makeRow(it)));
}
function setText(id, v){ document.getElementById(id).textContent = v; }

async function refresh(){
  setText("reloj", new Date().toLocaleString());

  const ch=await get("/api/claude-health");
  setText("m-tokens", ch.ok ? (ch.tokens_in+ch.tokens_out).toLocaleString() : "n/d");

  const inter=await get("/api/interactions");
  setText("m-inter", inter.ok ? inter.total : "n/d");
  fill("p-inter", inter.ok, inter.ok?inter.recientes:[],
       i=>rowEl(i.input||"—", i.error?"error":"ok", i.error?"bad":"muted"));

  const err=await get("/api/errors");
  setText("m-err", err.ok ? err.grupos.reduce((a,g)=>a+g.count,0) : "n/d");
  fill("p-errors", err.ok, err.ok?err.grupos:[],
       g=>rowEl(g.error_type+" · "+g.signal, "x"+g.count, "bad"));

  const runs=await get("/api/runs");
  fill("p-runs", runs.ok, runs.ok?runs.runs:[],
       r=>rowEl(r.ts, r.status, r.status==="ok"?"ok":"bad"));

  const fr=await get("/api/freshness");
  fill("p-fresh", fr.ok, fr.ok?fr.tablas:[],
       t=>rowEl(t.tabla, (t.al_dia?"al día":"desfasado")+" ("+(t.dias==null?"?":t.dias)+"d)", t.al_dia?"ok":"bad"));

  const etl=await get("/api/etl");
  setText("m-etl", (etl.ok&&etl.ultima)?etl.ultima.status:"n/d");
  const ce=document.getElementById("p-etl"); clear(ce);
  if(etl.ok&&etl.ultima){
    ce.appendChild(rowEl("última: "+etl.ultima.run_at, etl.ultima.status, etl.ultima.status==="success"?"ok":"bad"));
    ce.appendChild(rowEl("productos / alertas", etl.ultima.products_found+" / "+etl.ultima.alerts_generated, "muted"));
  } else { ce.appendChild(el("div","bad","no disponible")); }
}
refresh(); setInterval(refresh, 30000);
```

- [ ] **Step 4: Verificar que la página se sigue sirviendo**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_app.py -v`
Expected: verde (sirve la página; el render real se valida en Task 11).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/static && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard frontend (página oscura, DOM seguro sin innerHTML)"
```

---

## Task 11: `scripts/dashboard.sh` + smoke real

**Files:** Create `$OS_DIR/scripts/dashboard.sh`

- [ ] **Step 1: Escribir el lanzador `$OS_DIR/scripts/dashboard.sh`**

```bash
#!/bin/bash
# Lanza el dashboard de monitorización (solo lectura).
set -uo pipefail
OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV_FILE="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
PY="$HOME/.venvs/claude_code_os/bin/python"
PORT="${1:-8765}"
export OS_DIR
cd "$OS_DIR"
[[ -f "$ENV_FILE" ]] && { set -a; source "$ENV_FILE"; set +a; }
echo "Dashboard en http://localhost:$PORT  (Ctrl+C para parar)"
exec "$PY" -m uvicorn dashboard.app:app --host 127.0.0.1 --port "$PORT"
```

- [ ] **Step 2: Smoke real — levantar y consultar endpoints**

```bash
chmod +x "$OS_DIR/scripts/dashboard.sh"
cd "$OS_DIR"; set -a; source "$ENV_FILE" 2>/dev/null; set +a; export OS_DIR
~/.venvs/claude_code_os/bin/python -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8765 &
SRV=$!; sleep 4
echo "--- /api/etl ---"; curl -s http://127.0.0.1:8765/api/etl | head -c 400; echo
echo "--- /api/freshness ---"; curl -s http://127.0.0.1:8765/api/freshness | head -c 400; echo
echo "--- /api/interactions ---"; curl -s http://127.0.0.1:8765/api/interactions | head -c 300; echo
echo "--- / (HTML) ---"; curl -s http://127.0.0.1:8765/ | head -c 120; echo
kill $SRV 2>/dev/null
```
Expected: cada endpoint responde JSON `ok:true` con datos reales (etl con última ejecución de scraper_runs; freshness con al_dia; interactions con total). `/` devuelve el HTML. Si un panel da `ok:false`, anotar motivo (no bloqueante).

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add scripts/dashboard.sh && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: scripts/dashboard.sh + smoke endpoints reales"
```

> El usuario abre el dashboard con `bash scripts/dashboard.sh` y va a `http://localhost:8765` (WSL reenvía el puerto a Windows).

---

## Self-Review (hecho al escribir el plan)

- **Cobertura del spec:** 6 paneles → Tasks 3-8; FastAPI+endpoints+captura por panel → Task 9; frontend zonas del vídeo → Task 10; lanzador + smoke real → Task 11; config extendida → Task 0/2; recon logs Claude Code con degradación → Task 0/8; reúso de qa → Tasks 3,4,5,6; tests sin red → todas; robustez panel caído → Task 9 (`_safe`) + test. ✅
- **Placeholders:** columnas/umbral en Task 0/2 a confirmar en recon (marcado); `index.html` placeholder de Task 9 → completado en Task 10 (marcado). Sin TODOs sueltos. ✅
- **Consistencia de tipos/firmas:** cada panel expone `data(cfg, ...)` → dict con `ok`; endpoints `/api/errors|interactions|etl|freshness|runs|claude-health` coinciden entre `app.py` (Task 9) y `dashboard.js` (Task 10); `DashConfig` (supabase/etl/freshness/claude_logs_dir/cron_log) usado igual en config (Task 2) y paneles (Tasks 5-8); `gather` inyectable coherente con `qa.report.gather`; claves de salida usadas en JS (`grupos`, `recientes`, `tablas`, `ultima`, `tokens_in/out`, `runs`) coinciden con las que devuelven los paneles. ✅
- **Seguridad:** solo lectura; credenciales desde `.env`/env (nunca al cliente); FastAPI en 127.0.0.1; **JS sin innerHTML** (DOM con textContent → sin XSS al pintar datos de usuarios). ✅
