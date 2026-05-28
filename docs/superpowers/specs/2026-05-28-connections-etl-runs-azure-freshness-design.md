# Connections — `etl_runs` + Azure SQL freshness — Diseño

**Fecha:** 2026-05-28
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Cierra el **hueco #1 [Connections]** del `os-audit` 2026-05-28 (88/100): los ETLs
financieros se lanzan a mano sin tabla de control (no observables) y la frescura
de Azure SQL no es alcanzable desde WSL → los paneles `etl` y `freshness` del
dashboard tienen plumbing pero no datos para las tablas financieras de producción.

Tras esto, los 8 sistemas listados en `connections.md` quedan totalmente
observables desde el dashboard local.

## Decisiones (brainstorming)

1. **Scope**: trackear *todos* los ETLs (financieros + scrapers) en una tabla
   unificada, pero **sin migrar** `scraper_runs` — una **VIEW `all_runs`** une las
   dos tablas para lectura. Riesgo cero sobre datos históricos.
2. **Frescura Azure SQL**: **mirror a Supabase** (`azure_freshness` table) en lugar
   de endpoint HTTP en vivo. El panel `freshness` ya soporta este patrón sin
   cambios; cero plumbing nuevo en el dashboard.
3. **ETLs financieros**: siguen lanzándose a mano (no se programan en este scope).
   Solo se instrumentan con logging.
4. **Auth del endpoint de sync**: Cloud Run `--no-allow-unauthenticated` +
   Cloud Scheduler con cuenta de servicio IAM (patrón estándar del repo).

## Componentes

### 1. Supabase — schema nuevo

**Tabla `etl_runs`** (genérica, para nuevos eventos):

```sql
create table etl_runs (
  id           uuid primary key default gen_random_uuid(),
  run_at       timestamptz      not null default now(),
  kind         text             not null,              -- 'scraper' | 'etl_financial' | ...
  name         text             not null,              -- 'vivagym' | 'etl_pyg' | ...
  status       text             not null,              -- 'ok' | 'error' | 'running'
  duration_ms  integer,
  rows_in      integer,
  rows_out     integer,
  error_message text,
  meta         jsonb            not null default '{}'::jsonb
);

create index etl_runs_run_at_idx on etl_runs (run_at desc);
create index etl_runs_kind_name_idx on etl_runs (kind, name);
```

**VIEW `all_runs`** (lectura unificada, mapea `scraper_runs` a la shape de `etl_runs`):

```sql
create view all_runs as
select id, run_at, kind, name, status, duration_ms,
       rows_in, rows_out, error_message, meta
from etl_runs
union all
select id, run_at,
       'scraper'                 as kind,
       coalesce(competitor_id::text, 'unknown') as name,
       status,
       null                      as duration_ms,
       products_found            as rows_in,
       products_updated          as rows_out,
       error_message,
       jsonb_build_object('alerts_generated', alerts_generated) as meta
from scraper_runs;
```

(Las columnas exactas de `scraper_runs` se confirman en la fase de implementación.)

**Tabla `azure_freshness`**:

```sql
create table azure_freshness (
  tabla        text primary key,                       -- 'MS_PETRAMORA_HIST_VENTAS', ...
  max_fecha    date             not null,
  updated_at   timestamptz      not null default now(),
  meta         jsonb            not null default '{}'::jsonb
);
```

### 2. Backend `Agente_segmentador` (Cloud Run)

**`etl_logger.py`** (nuevo módulo):

- Función `log_run(kind, name, status, *, rows_in=None, rows_out=None,
  duration_ms=None, error_message=None, meta=None) → run_id`.
- Context manager `track_run(kind, name) → run_id`: registra `status='running'`
  al entrar, `'ok'`/`'error'` al salir con `duration_ms` y `error_message` si
  hubo excepción.
- Usa el cliente `supabase` global del backend.

**Endpoint `POST /internal/azure-freshness-sync`** (en `api.py`):

- Lee la conexión a Azure SQL del entorno (ya existe en el backend, IP
  34.175.58.90 autorizada).
- Para cada tabla configurada (lista hard-codeada en el módulo: empezamos con
  `MS_PETRAMORA_HIST_VENTAS`, ampliable), ejecuta
  `select max(<col>) from <tabla>` y upsert en `azure_freshness`.
- Devuelve `{ok: true, tablas: [...]}`.
- Protegido por IAM (no público): `--no-allow-unauthenticated`.

**Cloud Scheduler** (config nueva, gcloud desde PowerShell):

- Job diario (p. ej. 04:00 Madrid) que invoca el endpoint con OIDC token de una
  service account autorizada.

### 3. ETLs financieros (`ETL-Segmentador-Petramora/etl_*.py`)

5 scripts a instrumentar (lo que detecte la fase 1; primero confirmados):
`etl_pyg.py`, `etl_journal.py`, `etl_presupuesto.py`, `etl_financiero_v2.py`,
`etl_segmentador.py`.

Cada uno envuelve su `main()` (o `if __name__ == "__main__":`) con:

```python
from etl_logger import track_run

with track_run(kind="etl_financial", name="etl_pyg") as run:
    rows_in, rows_out = run_etl_pyg()
    run.rows_in = rows_in
    run.rows_out = rows_out
```

`etl_logger` se publica como módulo importable (paquete compartido o vendoring
ligero; la decisión exacta es del plan de implementación).

### 4. Dashboard `claude_code_os`

**Cambios mínimos**, solo de configuración:

- `qa/config.py` o equivalente: `cfg.etl.table = "all_runs"` (la VIEW).
- `cfg.freshness.tablas`: añadir `{tabla: "MS_PETRAMORA_HIST_VENTAS", col: "max_fecha"}`
  (apuntando a `azure_freshness`, no a la tabla de Azure — el panel ya genérico).
- `connections.md`: actualizar las filas 1–4 marcando "frescura observable" y
  retirar los 2 primeros gaps de la sección "Pendientes de cablear".

### Data flow

```
ETL financiero (manual)  ─▶ etl_logger ─▶ Supabase.etl_runs
Scraper (existente)      ─▶ scraper_runs  (sin cambios)
                                  │
                           ┌──────┴──────┐
                           ▼             ▼
                         VIEW all_runs  ──▶  dashboard panel "etl"

Cloud Scheduler ─▶ POST /internal/azure-freshness-sync
                              │
                              ▼
                       Azure SQL ─▶ Supabase.azure_freshness ─▶ dashboard panel "freshness"
```

## Testing

- **`etl_logger`**: tests unitarios (`pytest`) — mockear cliente Supabase, validar
  payloads, manejo de excepciones en context manager.
- **`/internal/azure-freshness-sync`**: test de integración contra un mock de Azure
  (sqlite o stub) — confirma upsert correcto.
- **VIEW `all_runs`**: test SQL en migraciones (Supabase CLI) o smoke contra
  staging — confirma que devuelve filas combinadas con shape correcta.
- **Dashboard panels**: tests existentes siguen pasando (no se toca lógica, solo
  configuración).

## Alcance excluido (YAGNI)

- Programar/automatizar los ETLs financieros (siguen manuales).
- Migrar `scraper_runs` (la VIEW resuelve la lectura unificada).
- UI para listar/inspeccionar runs (el panel actual basta).
- Alarmas/alertas por ETL fallido (capa separada, fuera de "Connections").
- Endpoint HTTP en vivo a Azure SQL (no es necesario; mirror cubre el caso).

## Riesgos y mitigaciones

- **Drift de `azure_freshness`** si Cloud Scheduler falla: añadir `updated_at` y
  un umbral de alerta en el panel `freshness` (si `updated_at` > 36 h, marca rojo).
- **Permisos Cloud Run/Scheduler**: requiere `gcloud` (PowerShell). Plan debe
  incluir comandos exactos para Eric.
- **Acoplamiento de `etl_logger` a Supabase**: aceptable; toda la
  observabilidad del repo ya depende de Supabase.

## Próximos pasos

1. Eric revisa este spec.
2. Crear plan de implementación (`writing-plans` skill) con tasks ordenados
   (migración Supabase → módulo Python → endpoint → instrumentar ETLs →
   Cloud Scheduler → dashboard config → connections.md).
