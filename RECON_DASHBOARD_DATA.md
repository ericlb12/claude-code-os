# RECON — Fuentes de datos para Dashboard de Operaciones

Subagente de reconocimiento (solo lectura). Fecha: 2026-05-27.
Objetivo: saber de dónde leer programáticamente (a) estado/última ejecución de ETLs y (b) frescura/salud de BBDD, para decidir qué paneles del dashboard son factibles.

Raíz inspeccionada: `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/`

## TL;DR (veredicto)

- **Panel de ETLs (scrapers de competencia / Radar): FACTIBLE YA.** Existe tabla de control `scraper_runs` en Supabase (status, timestamp `run_at`, productos, alertas, duración, error) + endpoint REST `GET /api/competitors/runs`. Es la fuente ideal y ya está poblada.
- **Panel de ETLs financieros (P&G, Balance, Segmentación RFM): NO factible directamente — falta montar captura.** Estos ETLs (`etl_*.py`) se lanzan a mano desde la línea de comandos y NO escriben ninguna tabla de control/log. Solo se puede inferir "cuándo se cargó por última vez" mirando la columna de fecha del dato (frescura), no la ejecución del job.
- **Panel de frescura de BBDD Supabase: FACTIBLE** vía columnas de fecha de las tablas de datos (`scraper_runs.run_at`, `competitor_alerts.created_at`, `competitor_plans.last_seen_at`, `segmentacion_clientes_raw.fecha_corte`, `fact_pyg`/`fact_pyg_v2`/`fact_balance` por `anio`+`mes_num`, `agent_logs.created_at`). Supabase es accesible vía REST desde WSL.
- **Panel de frescura BBDD Azure SQL: FACTIBLE EN TEORÍA** (tabla `MS_PETRAMORA_HIST_VENTAS` tiene columna `FECHA`, se puede hacer `MAX(FECHA)`), pero **NO accesible desde WSL**: Azure SQL solo admite la IP fija de Cloud NAT (`34.175.58.90`, whitelisted). Desde WSL la conexión no entra. Habría que consultarlo a través del backend en Cloud Run, no directamente.

---

## 1. Inventario de ETLs / cargas encontrados

Todo vive dentro de un único repo: **`source_petramora`** (GitHub: `ericlb12/Petramora_source`). No existe un repo "Radar" separado — el Radar (scrapers de competidores + briefing) está dentro de este mismo repo, en `ETL-Segmentador-Petramora/scraper_competitors/`. Los otros directorios de la raíz (`Autoresearch` = wiki Obsidian, `claude_power_bi`, `Agente_onboarding`, `Agente-comercial-likeik`, `Cuestionario IA`) no contienen ETLs de operaciones relevantes para este dashboard.

### A. Scrapers de competidores (Radar) — `ETL-Segmentador-Petramora/scraper_competitors/`
- **Qué cargan:** planes/precios de gimnasios competidores (Basic-Fit, Altafit, FitUp, FitnessPark, Dreamfit, Synergym, VivaGym, genéricos). Browser Use 0.7.5 + Playwright.
- **A dónde escriben (Supabase):** `competitors` (catálogo), `competitor_plans` (planes activos), `plan_price_history` (histórico precios), `competitor_alerts` (alertas), y **`scraper_runs` (tabla de control de ejecución)**.
- **Cómo se lanzan:**
  - CLI manual: `python -m scraper_competitors.main [--competitor N] [--dry-run]` (`main.py::run_scraper`).
  - HTTP: endpoint `POST /api/competitors/{id}/scrape` (en `api_competitors.py`, Cloud Run prod) — también inserta en `scraper_runs`.
  - **Programado:** Google **Cloud Scheduler** (región `europe-west1`), un job por competidor (`scrape-comp-{id}`) que hace POST al endpoint `/scrape`. Config en `scheduler_sync.py`. La definición de schedule (cron) se guarda en tabla Supabase `scraper_schedules`.

### B. ETL financiero / segmentación — `ETL-Segmentador-Petramora/etl_*.py`
- `etl_segmentador.py` → `segmentacion_clientes_raw`, `lineas_cliente_producto`, `catalogo_productos` (input: `Segmento_RFM_raw.csv` de Power BI).
- `etl_pyg.py` → `fact_pyg` (input: `p&g.csv`).
- `etl_presupuesto.py` → `fact_presupuesto` (input: `PPTO 2026 VS 2025.csv`).
- `etl_journal.py` → `fact_balance` + `fact_pyg_v2`.
- **Cómo se lanzan:** SOLO manual, desde la línea de comandos (ver CLAUDE.md `# Commands`). No hay cron, ni GitHub Actions, ni Supabase function, ni endpoint que los dispare.
- **A dónde escriben:** tablas de datos Supabase (upsert/insert directo). **No escriben ninguna tabla de log/control de ejecución.**

### C. Carga Azure SQL (ventas históricas)
- Tabla `MS_PETRAMORA_HIST_VENTAS` (~728K filas, 2024-01 a 2026-02). El agente solo LEE (modo Analista, `tools_sales.py`). No se ha encontrado en el repo el proceso que CARGA esta tabla (probablemente carga externa / Power BI, fuera de este repo). No hay log de su carga.

---

## 2. ¿Se puede saber si cada ETL corrió bien y cuándo?

| ETL / carga | ¿Estado de ejecución registrado? | Fuente | Cómo leerlo |
|---|---|---|---|
| Scrapers competidores | **SÍ** | tabla `scraper_runs` (Supabase) | REST `GET /api/competitors/runs?limit=&status=&competitor_id=` o query directa a la tabla |
| `etl_segmentador.py` | **NO** (sin log de ejecución) | — | Solo frescura indirecta vía `segmentacion_clientes_raw.fecha_corte` |
| `etl_pyg.py` | **NO** | — | Frescura indirecta vía `fact_pyg` (`anio`,`mes_num`) |
| `etl_presupuesto.py` | **NO** | — | `fact_presupuesto` no tiene fecha de carga |
| `etl_journal.py` | **NO** | — | Frescura indirecta vía `fact_balance` / `fact_pyg_v2` |
| Carga Azure SQL ventas | **NO** | — | Frescura indirecta vía `MAX(FECHA)` (solo desde backend, no WSL) |

### `scraper_runs` — esquema (columnas confirmadas en código)
`id, competitor_id, status, products_found, products_updated, alerts_generated, error_message, duration_ms, run_at` + join a `competitors(name)`.
- `status` ∈ {`success`, `error`, (`empty`)}.
- `run_at` = timestamp de la ejecución (lo usa `_compute_radar_freshness` y el endpoint `/runs`).
- Insert tanto en éxito como en error → cubre fallos.
- **Ya hay lógica de frescura escrita:** `_compute_radar_freshness(stale_days=7)` en `Agente_segmentador/tools_competitors.py` lee el último `run_at` por competidor activo y marca "stale" si >7 días o sin run. Test: `Agente_segmentador/tests/test_radar_freshness.py`.

---

## 3. Tablas con columnas de frescura aprovechables

### Supabase (accesible desde WSL vía REST)
| Tabla | Columna(s) de fecha | "¿Está al día?" se mide así |
|---|---|---|
| `scraper_runs` | `run_at` | Último run por competidor vs hoy (ya implementado) |
| `competitor_alerts` | `created_at` | Última alerta generada |
| `competitor_plans` | `first_seen_at`, `last_seen_at` | Último visto de cada plan |
| `plan_price_history` | (histórico, ver columna fecha del registro) | Último cambio de precio capturado |
| `segmentacion_clientes_raw` | `fecha_corte` | Snapshot RFM más reciente vs mes actual (es snapshot mensual, no histórico) |
| `fact_pyg` | `anio`, `mes_num` | Último mes de P&G cargado (real hasta marzo 2026) |
| `fact_pyg_v2` | `anio`, `mes_num` | Último mes P&G v2 |
| `fact_balance` | `anio`, `mes_num` | Último mes de balance |
| `fact_presupuesto` | `anio`, `mes`, `mes_num` | (presupuesto fijo 2026; no aporta "frescura de carga") |
| `agent_logs` | `created_at` | Actividad del agente (salud de uso, no ETL) |
| `agent_sessions` | (upsert por `session_id`) | Sesiones activas |

Nota: `fact_*` y `segmentacion_clientes_raw` solo tienen fecha **del dato de negocio** (qué mes/corte cubre), no fecha de carga física. Sirven para "¿hay datos del mes en curso?" pero no para "¿cuándo corrió el ETL?".

### Azure SQL (NO accesible desde WSL)
| Tabla | Columna | Medida |
|---|---|---|
| `MS_PETRAMORA_HIST_VENTAS` | `FECHA` | `MAX(FECHA)` = última venta cargada |

---

## 4. Conexiones y accesibilidad desde WSL

- **Supabase (PostgreSQL vía REST):** credenciales en `Agente_segmentador/.env` y `ETL-Segmentador-Petramora/.env` → vars `SUPABASE_URL`, `SUPABASE_KEY` (también acepta `SUPABASE_SERVICE_KEY`). Cliente Python `supabase.create_client`. **Accesible desde WSL** (REST sobre HTTPS, sin restricción de IP relevante).
- **Azure SQL Server (pymssql):** vars `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, `AZURE_SQL_USER`, `AZURE_SQL_PASSWORD` (en `config.py`/`.env`). **NO accesible desde WSL:** Azure SQL solo permite la IP fija de Cloud NAT `34.175.58.90` (whitelisted, confirmado en CLAUDE.md). Una IP de WSL no está en la whitelist → conexión bloqueada. Para leer frescura de ventas hay que pasar por el backend Cloud Run (que sí tiene esa IP).
- **Backend prod:** `https://petramora-api-434232851779.europe-southwest1.run.app` (FastAPI en Cloud Run). Expone `/api/competitors/runs`, `/api/competitors/schedules`, etc. Endpoints abiertos (`allow-unauthenticated`).
- **Cloud Scheduler:** `europe-west1`, proyecto `gen-lang-client-0613772357`. Estado de los jobs consultable vía API de Cloud Scheduler / `gcloud scheduler jobs list` (recordatorio del memory: gcloud preferible desde PowerShell, no WSL).

---

## 5. Veredicto por panel

1. **Panel "Estado de ETLs (scrapers/Radar)" → FACTIBLE VÍA `scraper_runs`.**
   Fuente directa: `GET /api/competitors/runs` (Cloud Run) o query Supabase a `scraper_runs`. Da por competidor: último run, status success/error, productos, alertas, duración, mensaje de error. Próximo run programado vía `scraper_schedules` + `croniter`. Nada que montar.

2. **Panel "Estado de ETLs financieros (P&G/Balance/RFM)" → NECESITA MONTAR CAPTURA.**
   No hay log de ejecución. Opciones: (a) añadir una tabla `etl_runs` y un par de líneas de insert al final de cada `etl_*.py` (timestamp, script, status, filas, error) — barato; o (b) conformarse con frescura del dato (sección 3) que NO distingue "el ETL falló" de "no se ha lanzado".

3. **Panel "Frescura BBDD Supabase" → FACTIBLE VÍA columnas de fecha** (sección 3), leíble desde WSL por REST. La lógica de stale ya existe para Radar (`_compute_radar_freshness`, umbral 7 días) y se puede replicar para `fact_*` (umbral mensual) y `segmentacion_clientes_raw`.

4. **Panel "Frescura BBDD Azure SQL (ventas)" → FACTIBLE SOLO VÍA BACKEND.**
   `MAX(FECHA)` sobre `MS_PETRAMORA_HIST_VENTAS`. No desde WSL (IP no whitelisted). Requiere un endpoint nuevo en Cloud Run que devuelva el MAX(FECHA), o reutilizar uno de los `tools_sales`. La carga de esa tabla no está en el repo, así que "¿corrió el ETL de ventas?" no es observable; solo "¿hasta qué fecha hay datos?".

### Qué falta para un dashboard de operaciones completo
- Tabla/insert de log para los ETLs financieros (hoy ciegos).
- Endpoint backend para frescura de Azure SQL (o aceptar que ese panel pase por Cloud Run).
- Opcional: leer estado de jobs de Cloud Scheduler (last attempt status) para distinguir "scheduler no disparó" de "scraper corrió y falló".
