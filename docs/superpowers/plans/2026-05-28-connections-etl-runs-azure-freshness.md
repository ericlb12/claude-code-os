# Connections — `etl_runs` + Azure SQL freshness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar hueco #1 [Connections] del os-audit 2026-05-28: instrumentar todos los ETLs en una tabla `etl_runs` unificada (VIEW `all_runs` con scrapers existentes) y materializar la frescura de Azure SQL en Supabase (`azure_freshness`) para que el dashboard vea ambas fuentes.

**Architecture:** Supabase recibe escrituras de (a) ETLs financieros vía nuevo módulo `etl_logger.py`, (b) sync Cloud-Run-triggered de Azure SQL. Backend `Agente_segmentador` expone `POST /internal/azure-freshness-sync`, llamado por Cloud Scheduler diario. Dashboard solo cambia configuración: apunta panel `etl` a la VIEW `all_runs` y añade tablas Azure al panel `freshness`.

**Tech Stack:** Supabase (Postgres + supabase-py), FastAPI (Cloud Run), Python ETLs en `ETL-Segmentador-Petramora/`, gcloud (Cloud Scheduler), MCP `supabase` para migraciones, pytest.

**Spec base:** `docs/superpowers/specs/2026-05-28-connections-etl-runs-azure-freshness-design.md`

**Repos tocados:**
- `claude_code_os` (este repo): dashboard config, `connections.md`, plan.
- `source_petramora` (sibling): backend `Agente_segmentador/`, ETLs `ETL-Segmentador-Petramora/`.

**Venv para tests del backend / ETLs:** `~/petramora-venv/bin/python` (NO el de claude_code_os).

---

### Task 1: Migración Supabase — tabla `etl_runs`

**Files:**
- Create: `source_petramora/supabase/migrations/20260528_etl_runs.sql`

- [ ] **Step 1: Crear archivo de migración**

```sql
-- 20260528_etl_runs.sql
create table if not exists public.etl_runs (
  id            uuid primary key default gen_random_uuid(),
  run_at        timestamptz      not null default now(),
  kind          text             not null,
  name          text             not null,
  status        text             not null check (status in ('ok','error','running')),
  duration_ms   integer,
  rows_in       integer,
  rows_out      integer,
  error_message text,
  meta          jsonb            not null default '{}'::jsonb
);

create index if not exists etl_runs_run_at_idx on public.etl_runs (run_at desc);
create index if not exists etl_runs_kind_name_idx on public.etl_runs (kind, name);
```

- [ ] **Step 2: Aplicar la migración vía MCP**

Llamar `mcp__supabase__apply_migration` con `name="20260528_etl_runs"` y el SQL de Step 1.

- [ ] **Step 3: Verificar via `mcp__supabase__list_tables`**

Expected: `etl_runs` aparece en el schema `public` con las columnas del DDL.

- [ ] **Step 4: Commit**

```bash
cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/source_petramora
git add supabase/migrations/20260528_etl_runs.sql
git commit -m "feat(supabase): tabla etl_runs (observabilidad ETLs unificada)"
```

---

### Task 2: Migración Supabase — tabla `azure_freshness`

**Files:**
- Create: `source_petramora/supabase/migrations/20260528_azure_freshness.sql`

- [ ] **Step 1: Crear migración**

```sql
-- 20260528_azure_freshness.sql
create table if not exists public.azure_freshness (
  tabla       text primary key,
  max_fecha   date             not null,
  updated_at  timestamptz      not null default now(),
  meta        jsonb            not null default '{}'::jsonb
);
```

- [ ] **Step 2: Aplicar via `mcp__supabase__apply_migration`**

- [ ] **Step 3: Verificar `azure_freshness` listada por `mcp__supabase__list_tables`**

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/20260528_azure_freshness.sql
git commit -m "feat(supabase): tabla azure_freshness (frescura Azure SQL mirror)"
```

---

### Task 3: Confirmar columnas de `scraper_runs` y crear VIEW `all_runs`

**Files:**
- Create: `source_petramora/supabase/migrations/20260528_all_runs_view.sql`

- [ ] **Step 1: Inspeccionar columnas reales de `scraper_runs`**

Usar `mcp__supabase__execute_sql` con:
```sql
select column_name, data_type from information_schema.columns
where table_schema='public' and table_name='scraper_runs'
order by ordinal_position;
```

- [ ] **Step 2: Crear migración mapeando columnas reales**

Plantilla (ajustar nombres si difieren del resultado de Step 1):

```sql
-- 20260528_all_runs_view.sql
create or replace view public.all_runs as
select id, run_at, kind, name, status,
       duration_ms, rows_in, rows_out, error_message, meta
  from public.etl_runs
union all
select id,
       run_at,
       'scraper'                                  as kind,
       coalesce(competitor_id::text, 'unknown')   as name,
       status,
       null::integer                              as duration_ms,
       products_found                             as rows_in,
       products_updated                           as rows_out,
       error_message,
       jsonb_build_object('alerts_generated', alerts_generated) as meta
  from public.scraper_runs;
```

- [ ] **Step 3: Aplicar via `mcp__supabase__apply_migration`**

- [ ] **Step 4: Smoke con `mcp__supabase__execute_sql`**

```sql
select kind, count(*) from public.all_runs group by kind;
```

Expected: filas con `kind='scraper'` (las históricas) y, tras Task 4-7, `kind='etl_financial'`.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/20260528_all_runs_view.sql
git commit -m "feat(supabase): VIEW all_runs (etl_runs + scraper_runs unificados)"
```

---

### Task 4: `etl_logger.log_run()` — función básica (TDD)

**Files:**
- Create: `source_petramora/Agente_segmentador/etl_logger.py`
- Create: `source_petramora/Agente_segmentador/tests/test_etl_logger.py`

- [ ] **Step 1: Escribir test que falla**

```python
# tests/test_etl_logger.py
from unittest.mock import MagicMock
from etl_logger import log_run

def test_log_run_envia_payload_correcto():
    client = MagicMock()
    table = client.table.return_value
    table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "00000000-0000-0000-0000-000000000001"}]
    )

    run_id = log_run(
        client,
        kind="etl_financial",
        name="etl_pyg",
        status="ok",
        rows_in=120,
        rows_out=118,
        duration_ms=4321,
    )

    assert run_id == "00000000-0000-0000-0000-000000000001"
    client.table.assert_called_once_with("etl_runs")
    payload = table.insert.call_args[0][0]
    assert payload["kind"] == "etl_financial"
    assert payload["name"] == "etl_pyg"
    assert payload["status"] == "ok"
    assert payload["rows_in"] == 120
    assert payload["rows_out"] == 118
    assert payload["duration_ms"] == 4321
    assert payload["error_message"] is None
    assert payload["meta"] == {}
```

- [ ] **Step 2: Ejecutar test (debe FALLAR)**

```bash
cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/source_petramora/Agente_segmentador
~/petramora-venv/bin/python -m pytest tests/test_etl_logger.py -v
```

Expected: `ModuleNotFoundError: No module named 'etl_logger'`.

- [ ] **Step 3: Implementar `log_run`**

```python
# etl_logger.py
from __future__ import annotations
from typing import Any, Optional

def log_run(
    client: Any,
    *,
    kind: str,
    name: str,
    status: str,
    duration_ms: Optional[int] = None,
    rows_in: Optional[int] = None,
    rows_out: Optional[int] = None,
    error_message: Optional[str] = None,
    meta: Optional[dict] = None,
) -> str:
    payload = {
        "kind": kind,
        "name": name,
        "status": status,
        "duration_ms": duration_ms,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "error_message": error_message,
        "meta": meta or {},
    }
    resp = client.table("etl_runs").insert(payload).execute()
    return resp.data[0]["id"]
```

- [ ] **Step 4: Ejecutar test (debe PASAR)**

```bash
~/petramora-venv/bin/python -m pytest tests/test_etl_logger.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add Agente_segmentador/etl_logger.py Agente_segmentador/tests/test_etl_logger.py
git commit -m "feat(etl_logger): log_run() escribe a etl_runs"
```

---

### Task 5: `etl_logger.track_run()` — context manager con timing y errores (TDD)

**Files:**
- Modify: `source_petramora/Agente_segmentador/etl_logger.py`
- Modify: `source_petramora/Agente_segmentador/tests/test_etl_logger.py`

- [ ] **Step 1: Escribir tests que fallan**

```python
# añadir a tests/test_etl_logger.py
import pytest
from etl_logger import track_run

def test_track_run_ok_registra_running_y_ok(monkeypatch):
    client = MagicMock()
    insert_resp = MagicMock(data=[{"id": "run-1"}])
    update_resp = MagicMock(data=[{"id": "run-1"}])
    client.table.return_value.insert.return_value.execute.return_value = insert_resp
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_resp

    with track_run(client, kind="etl_financial", name="etl_pyg") as run:
        run.rows_in = 100
        run.rows_out = 99

    # primer call: insert con status='running'
    insert_payload = client.table.return_value.insert.call_args[0][0]
    assert insert_payload["status"] == "running"
    # update final: status='ok', rows_in/out propagados, duration_ms set
    update_payload = client.table.return_value.update.call_args[0][0]
    assert update_payload["status"] == "ok"
    assert update_payload["rows_in"] == 100
    assert update_payload["rows_out"] == 99
    assert update_payload["duration_ms"] is not None and update_payload["duration_ms"] >= 0
    assert update_payload["error_message"] is None

def test_track_run_excepcion_registra_error_y_repropaga():
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "run-2"}])
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "run-2"}])

    with pytest.raises(ValueError, match="boom"):
        with track_run(client, kind="etl_financial", name="etl_pyg"):
            raise ValueError("boom")

    update_payload = client.table.return_value.update.call_args[0][0]
    assert update_payload["status"] == "error"
    assert "boom" in update_payload["error_message"]
```

- [ ] **Step 2: Ejecutar tests (deben FALLAR)**

```bash
~/petramora-venv/bin/python -m pytest tests/test_etl_logger.py -v
```

Expected: 2 failures con `ImportError` o `AttributeError` sobre `track_run`.

- [ ] **Step 3: Implementar `track_run`**

Añadir al final de `etl_logger.py`:

```python
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional

@dataclass
class RunHandle:
    id: str
    rows_in: Optional[int] = None
    rows_out: Optional[int] = None
    meta: dict = field(default_factory=dict)

@contextmanager
def track_run(client: Any, *, kind: str, name: str) -> Iterator[RunHandle]:
    insert_payload = {
        "kind": kind, "name": name, "status": "running",
        "duration_ms": None, "rows_in": None, "rows_out": None,
        "error_message": None, "meta": {},
    }
    resp = client.table("etl_runs").insert(insert_payload).execute()
    run_id = resp.data[0]["id"]
    handle = RunHandle(id=run_id)
    started = time.monotonic()
    err: Optional[BaseException] = None
    try:
        yield handle
    except BaseException as e:
        err = e
        raise
    finally:
        duration_ms = int((time.monotonic() - started) * 1000)
        update_payload = {
            "status": "error" if err else "ok",
            "duration_ms": duration_ms,
            "rows_in": handle.rows_in,
            "rows_out": handle.rows_out,
            "error_message": (
                f"{type(err).__name__}: {err}\n{traceback.format_exc()}"
                if err else None
            ),
            "meta": handle.meta,
        }
        client.table("etl_runs").update(update_payload).eq("id", run_id).execute()
```

- [ ] **Step 4: Ejecutar tests (los 3 deben PASAR)**

```bash
~/petramora-venv/bin/python -m pytest tests/test_etl_logger.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add Agente_segmentador/etl_logger.py Agente_segmentador/tests/test_etl_logger.py
git commit -m "feat(etl_logger): track_run() context manager (timing + errores)"
```

---

### Task 6: Endpoint `POST /internal/azure-freshness-sync` (TDD)

**Files:**
- Modify: `source_petramora/Agente_segmentador/api.py`
- Create: `source_petramora/Agente_segmentador/azure_freshness.py`
- Create: `source_petramora/Agente_segmentador/tests/test_azure_freshness.py`

- [ ] **Step 1: Confirmar columna de fecha de `MS_PETRAMORA_HIST_VENTAS`**

Pregunta a Eric (o grep en `Agente_segmentador/tools_*.py`) cuál es la columna de fecha más reciente de `MS_PETRAMORA_HIST_VENTAS`. Documentarla en `azure_freshness.py` como constante `TABLAS_AZURE`.

- [ ] **Step 2: Escribir test que falla**

```python
# tests/test_azure_freshness.py
from unittest.mock import MagicMock
from azure_freshness import sync_freshness, TABLAS_AZURE

def test_sync_freshness_upserta_max_por_tabla():
    azure_conn = MagicMock()
    cur = azure_conn.cursor.return_value.__enter__.return_value
    cur.execute.return_value = None
    # un fetchone por tabla
    cur.fetchone.side_effect = [("2026-05-15",) for _ in TABLAS_AZURE]

    supabase = MagicMock()
    supabase.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{}])

    result = sync_freshness(azure_conn, supabase)

    assert result["ok"] is True
    assert len(result["tablas"]) == len(TABLAS_AZURE)
    assert supabase.table.call_args_list[-1][0][0] == "azure_freshness"
    upsert_calls = supabase.table.return_value.upsert.call_args_list
    nombres = {c[0][0]["tabla"] for c in upsert_calls}
    assert nombres == {t["tabla"] for t in TABLAS_AZURE}
```

- [ ] **Step 3: Ejecutar test (debe FALLAR)**

```bash
~/petramora-venv/bin/python -m pytest tests/test_azure_freshness.py -v
```

Expected: `ModuleNotFoundError: No module named 'azure_freshness'`.

- [ ] **Step 4: Implementar `azure_freshness.py`**

```python
# azure_freshness.py
from __future__ import annotations
from typing import Any

TABLAS_AZURE: list[dict] = [
    {"tabla": "MS_PETRAMORA_HIST_VENTAS", "col_fecha": "FECHA"},  # confirmar en Step 1
]

def sync_freshness(azure_conn: Any, supabase: Any) -> dict:
    out = []
    for spec in TABLAS_AZURE:
        tabla, col = spec["tabla"], spec["col_fecha"]
        with azure_conn.cursor() as cur:
            cur.execute(f"select max([{col}]) from [{tabla}]")
            row = cur.fetchone()
        max_fecha = row[0] if row else None
        if max_fecha is None:
            continue
        max_fecha_str = str(max_fecha)[:10]
        supabase.table("azure_freshness").upsert({
            "tabla": tabla,
            "max_fecha": max_fecha_str,
            "meta": {"col_fecha": col},
        }).execute()
        out.append({"tabla": tabla, "max_fecha": max_fecha_str})
    return {"ok": True, "tablas": out}
```

- [ ] **Step 5: Ejecutar test (debe PASAR)**

```bash
~/petramora-venv/bin/python -m pytest tests/test_azure_freshness.py -v
```

Expected: 1 passed.

- [ ] **Step 6: Conectar endpoint en `api.py`**

Añadir al final (o en sección de `/internal/*` si existe):

```python
# api.py — añadir handler
from azure_freshness import sync_freshness
# imports existentes ya tienen el cliente Azure SQL y supabase

@app.post("/internal/azure-freshness-sync")
def internal_azure_freshness_sync():
    azure_conn = get_azure_connection()  # reusar helper existente del backend
    try:
        return sync_freshness(azure_conn, supabase)
    finally:
        try:
            azure_conn.close()
        except Exception:
            pass
```

(Si no existe `get_azure_connection()` en el backend, inspeccionar `tools_*.py` y reutilizar el patrón actual. Documentar la decisión en el commit.)

- [ ] **Step 7: Commit**

```bash
git add Agente_segmentador/azure_freshness.py Agente_segmentador/api.py Agente_segmentador/tests/test_azure_freshness.py
git commit -m "feat(api): POST /internal/azure-freshness-sync mirror Azure→Supabase"
```

---

### Task 7: Instrumentar los 5 ETLs financieros

**Files:**
- Modify: `source_petramora/ETL-Segmentador-Petramora/etl_pyg.py`
- Modify: `source_petramora/ETL-Segmentador-Petramora/etl_journal.py`
- Modify: `source_petramora/ETL-Segmentador-Petramora/etl_presupuesto.py`
- Modify: `source_petramora/ETL-Segmentador-Petramora/etl_financiero_v2.py`
- Modify: `source_petramora/ETL-Segmentador-Petramora/etl_segmentador.py`

- [ ] **Step 1: Añadir bloque de import al inicio de CADA ETL**

Inmediatamente después de los imports estándar, añadir:

```python
import sys
from pathlib import Path
# etl_logger vive en Agente_segmentador/ (sibling dir del repo)
_LOGGER_PATH = Path(__file__).resolve().parent.parent / "Agente_segmentador"
if str(_LOGGER_PATH) not in sys.path:
    sys.path.insert(0, str(_LOGGER_PATH))
from etl_logger import track_run
```

- [ ] **Step 2: Envolver `main()` (o equivalente) de CADA ETL**

Patrón (ejemplo para `etl_pyg.py`, adaptar nombre `name=` y `rows_*` por ETL):

ANTES:
```python
def main():
    args = parse_args()
    records = extract(...)
    if not args.dry_run:
        load_to_supabase(records)
```

DESPUÉS:
```python
def main():
    args = parse_args()
    supabase = get_supabase()
    with track_run(supabase, kind="etl_financial", name="etl_pyg") as run:
        records = extract(...)
        run.rows_in = len(records)
        if not args.dry_run:
            load_to_supabase(records)
            run.rows_out = len(records)
```

Mapping de `name=` por archivo:
- `etl_pyg.py` → `"etl_pyg"`
- `etl_journal.py` → `"etl_journal"`
- `etl_presupuesto.py` → `"etl_presupuesto"`
- `etl_financiero_v2.py` → `"etl_financiero_v2"`
- `etl_segmentador.py` → `"etl_segmentador"`

- [ ] **Step 3: Dry-run de UN ETL para verificar logging**

```bash
cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/source_petramora/ETL-Segmentador-Petramora
~/petramora-venv/bin/python etl_pyg.py --dry-run
```

Verificar via MCP:
```sql
select kind, name, status, run_at from public.etl_runs order by run_at desc limit 5;
```

Expected: una fila con `kind='etl_financial'`, `name='etl_pyg'`, `status='ok'`, `duration_ms>0`.

- [ ] **Step 4: Commit**

```bash
git add ETL-Segmentador-Petramora/etl_*.py
git commit -m "feat(etls): instrumentar 5 ETLs financieros con track_run"
```

---

### Task 8: Deploy backend + crear Cloud Scheduler job

**Files:**
- (Sin cambios de código — uso de gcloud)

- [ ] **Step 1: Deploy del backend con el nuevo endpoint**

Eric ejecuta en **PowerShell** (no WSL):

```powershell
cd "C:\Users\Luis Ojeda\Likeik CX Dropbox\Comercial\@PROYECTOS\Agente IA\source_petramora\Agente_segmentador"
gcloud builds submit --config=../cloudbuild.yaml
```

Esperar a que termine y anotar la URL de Cloud Run (`https://...run.app`).

- [ ] **Step 2: Smoke del endpoint (manual, con IAM token)**

```powershell
$TOKEN = gcloud auth print-identity-token
$URL = "<la URL del Step 1>/internal/azure-freshness-sync"
curl -X POST $URL -H "Authorization: Bearer $TOKEN"
```

Expected: `{"ok": true, "tablas": [{"tabla": "MS_PETRAMORA_HIST_VENTAS", "max_fecha": "..."}]}`.

Verificar via MCP:
```sql
select * from public.azure_freshness;
```

- [ ] **Step 3: Crear Service Account para Cloud Scheduler**

```powershell
gcloud iam service-accounts create sa-azure-freshness `
  --display-name="Azure freshness sync invoker"

gcloud run services add-iam-policy-binding <NOMBRE-CLOUD-RUN> `
  --region=<REGION> `
  --member="serviceAccount:sa-azure-freshness@<PROJECT-ID>.iam.gserviceaccount.com" `
  --role="roles/run.invoker"
```

- [ ] **Step 4: Crear Cloud Scheduler job (04:00 Madrid = 02:00 UTC verano)**

```powershell
gcloud scheduler jobs create http azure-freshness-daily `
  --schedule="0 2 * * *" `
  --uri="<URL>/internal/azure-freshness-sync" `
  --http-method=POST `
  --oidc-service-account-email="sa-azure-freshness@<PROJECT-ID>.iam.gserviceaccount.com" `
  --location=<REGION>
```

- [ ] **Step 5: Forzar 1 ejecución y verificar**

```powershell
gcloud scheduler jobs run azure-freshness-daily --location=<REGION>
```

Verificar en MCP que `azure_freshness.updated_at` es reciente.

- [ ] **Step 6: Commit (no hay código que commitear; saltar este step si no hay diff)**

---

### Task 9: Dashboard — apuntar `etl` a `all_runs` y añadir Azure al `freshness`

**Files:**
- Modify: `claude_code_os/qa/config.py` (o el archivo donde se carga `cfg.etl` / `cfg.freshness` por target)

- [ ] **Step 1: Identificar el archivo de config exacto**

```bash
grep -rn "etl\s*=\|\"table\":\s*\"scraper_runs\"\|freshness" "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/qa/" | head -10
```

- [ ] **Step 2: Cambiar `etl.table` a `all_runs`**

Editar el target Petramora: donde diga `"table": "scraper_runs"` (o equivalente), poner `"table": "all_runs"`.

- [ ] **Step 3: Añadir entrada Azure al `freshness.tablas[]`**

```python
{"tabla": "azure_freshness", "col": "max_fecha", "umbral_dias": 2}
```

(Hay solo 1 fila en `azure_freshness` por ahora; el panel mostrará "azure_freshness al día/N días atrás". Para mostrar por nombre de tabla Azure, alternativa: hacer un filtro por `tabla='MS_PETRAMORA_HIST_VENTAS'` — decidir en este step si se quiere granularidad. Por simplicidad, empezar con la primera versión.)

- [ ] **Step 4: Validar en el dashboard**

```bash
bash /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/claude_code_os/scripts/dashboard.sh
```

Abrir http://localhost:8765, comprobar:
- Panel "ETL último": muestra el último run (scraper o etl_financial).
- Panel "Frescura": incluye `azure_freshness` con días recientes.

- [ ] **Step 5: Commit**

```bash
cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/claude_code_os
git add qa/config.py  # o el archivo exacto
git commit -m "feat(dashboard): etl panel apunta a all_runs + azure_freshness en freshness"
```

---

### Task 10: Actualizar `connections.md`

**Files:**
- Modify: `claude_code_os/connections.md`

- [ ] **Step 1: Modificar tabla y sección de gaps**

Cambios:
- Fila 1 (`agent_logs`): sin cambios.
- Fila 2 (`scraper_runs`): añadir nota "leído vía VIEW `all_runs`".
- **Añadir fila 9**: ETLs financieros `etl_runs` — mecanismo `key+ref`, auth `idem Supabase`, revisión `2026-05-28`.
- **Añadir fila 10**: Frescura Azure SQL via `azure_freshness` — mecanismo `script (Cloud Scheduler → Cloud Run → Azure)`, auth `IAM + SA sa-azure-freshness`, revisión `2026-05-28`.
- En sección "Pendientes de cablear (gaps conocidos)": eliminar los 2 primeros bullets (etl_runs y frescura Azure). Mantener solo el de Langfuse.

- [ ] **Step 2: Verificar formato**

```bash
head -25 connections.md
```

- [ ] **Step 3: Commit**

```bash
git add connections.md
git commit -m "docs(connections): nuevos sistemas etl_runs + azure_freshness; cerrados 2 gaps"
```

---

### Task 11: Verificación end-to-end

- [ ] **Step 1: Correr os-audit otra vez**

Desde dashboard pulsar ▶ os-audit. Esperar a que escriba `audits/audit-<fecha>.md`.

- [ ] **Step 2: Verificar nota Connections subió**

```bash
head -3 "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/audits/audit-$(date +%F).md"
```

Expected: `Connections: ≥23/25` (subió desde 19/25). El hueco #1 anterior debe haber salido del top-3.

- [ ] **Step 3: Push final de ambos repos**

```bash
cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/source_petramora
git push origin master  # o la rama elegida

cd /mnt/c/Users/Luis\ Ojeda/Likeik\ CX\ Dropbox/Comercial/@PROYECTOS/Agente\ IA/claude_code_os
git push origin master
```

(`source_petramora` puede preferir PR a `staging` antes de master — consultar a Eric en este step; el repo es el del cliente).

---

## Riesgos a vigilar durante la ejecución

- **`get_azure_connection()`** en el backend: si no existe un helper unificado, el endpoint del Task 6 debe reusar el patrón actual de conexión a Azure (probablemente en `tools_*.py`). Si esto se complica, parar y consultar.
- **`scraper_runs` columnas**: si `competitor_id` no existe o tiene otro tipo, ajustar la VIEW en Task 3.
- **Schedule de Cloud Scheduler**: el horario UTC `0 2 * * *` corresponde a 04:00 Madrid en verano (CEST) y 03:00 en invierno (CET). Documentar el trade-off; si se quiere fijo a 04:00 local exacto, usar `--time-zone="Europe/Madrid"`.
- **PR vs push directo en `source_petramora`**: es repo del cliente — consultar a Eric antes de pushear a master.

## Definition of Done

- [ ] Migraciones Supabase aplicadas y verificadas (tasks 1, 2, 3).
- [ ] `etl_logger` con 3 tests pasando (tasks 4, 5).
- [ ] Endpoint `/internal/azure-freshness-sync` con 1 test pasando + smoke OK (task 6).
- [ ] 5 ETLs instrumentados, dry-run confirma fila en `etl_runs` (task 7).
- [ ] Cloud Scheduler ejecutado al menos 1× y `azure_freshness` poblada (task 8).
- [ ] Dashboard muestra ambos paneles con datos reales (task 9).
- [ ] `connections.md` refleja los 2 nuevos sistemas y los gaps cerrados (task 10).
- [ ] `os-audit` reporta Connections ≥ 23/25 (task 11).
