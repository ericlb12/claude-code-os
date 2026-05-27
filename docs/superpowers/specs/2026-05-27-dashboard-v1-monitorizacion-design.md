# Dashboard v1 — Monitorización / contexto — Diseño

**Fecha:** 2026-05-27
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Fase 3 del Agentic OS ([[project-claude-code-os]]): el dashboard/command center del
vídeo de Chase AI. La visión de Eric: un **centro de mando + panel de operaciones**
que (1) da contexto de cómo está Claude Code, (2) monitoriza runs, (3) monitoriza
errores y qué hacer, (4) monitoriza el estado de ETLs/BBDD, y (5) deja lanzar skills
headless. Es la imagen mental que Eric tenía del proyecto desde el inicio.

Es un app multi-módulo → se construye en incrementos:
- **v1 (este spec): Monitorización / contexto (solo lectura).** Los paneles para los
  que ya hay fuente de datos legible desde WSL.
- **v2: Ejecución headless** — cuadro de prompt (corazón del dashboard del vídeo:
  escribes/ pulsas un botón-plantilla → `claude -p` headless → salida en vivo) +
  botones de skills. Spec aparte.

## Decisiones tomadas en brainstorming

1. **Stack: app Python FastAPI** que reúsa el paquete `qa/`. Mismo lenguaje que todo
   lo construido, corre local en WSL, soporta la v2 de ejecución de forma natural.
   Descartados: React/Next (otro stack, más trabajo) y HTML estático regenerado (no
   vivo, no soporta v2).
2. **v1 = solo monitorización (lectura).** La ejecución headless —aunque es lo que
   más ilusiona a Eric (el cuadro de texto que corre Claude Code)— va en v2, justo
   después, sobre el mismo app.
3. **Arquitectura modular:** cada cosa a monitorizar = un panel = un adapter + un
   endpoint, aislado. Añadir un panel futuro (ETL financieros, Azure SQL) = enchufar
   otra fuente, sin rehacer.
4. **Los skills de Desarrollo (deploy, add-feature) NO son botones autónomos** — son
   herramientas de sesión. En el dashboard (v2) vivirán como plantillas de prompt,
   no como jobs. (Insight de Eric.)

## Fuentes confirmadas (recon RECON_DASHBOARD_DATA.md)

Factibles desde WSL/Supabase + logs locales:
- **scraper_runs** (Supabase): tabla de control real de los scrapers de competencia
  (Radar) — `run_at`, `status` (success/error), `products_found/updated`,
  `alerts_generated`, `duration_ms`, `error_message`.
- **agent_logs** (Supabase): interacciones usuario↔agente + errores (ya usado por QA).
- Tablas con fecha para frescura: `scraper_runs.run_at`, `segmentacion_clientes_raw.fecha_corte`,
  `fact_pyg`/`fact_pyg_v2`/`fact_balance` (por `anio`+`mes_num`), `competitor_alerts.created_at`.
- Logs locales de Claude Code en `~/.claude` (uso/actividad).
- `cron.log` + informes QA (ya generados por Sub-proyecto C/A).

Fuera de v1 (recon confirmó que faltan pre-requisitos):
- **ETLs financieros** (`etl_pyg.py` etc.): se lanzan a mano y NO registran estado →
  requieren añadir una tabla `etl_runs` en Petramora primero. Módulo futuro.
- **Frescura Azure SQL** (ventas históricas): solo accesible vía backend Cloud Run
  (IP fija `34.175.58.90`), no desde WSL. Requiere endpoint. Módulo futuro.

## Alcance de la v1: 6 paneles

Paquete `dashboard/` en `claude_code_os`. App FastAPI sirve `index.html` + un endpoint
JSON por panel; la página los consume y renderiza (auto-refresh cada ~30s).

### Paneles (unidad = adapter + endpoint, aislado)

- **`claude_health`** — parsea logs de sesiones en `~/.claude` → uso/actividad de
  Claude Code (tokens/coste/ventanas si el formato lo permite; si no, degrada a nº de
  runs). Endpoint `/api/claude-health`.
- **`runs`** — lee `qa-reports/<target>/cron.log` + run-log → runs recientes (cron +
  manuales) y próximo run del cron (forecast). `/api/runs`.
- **`errors`** — reúsa `qa.report.gather` + `qa.detect` + `qa.group` sobre `agent_logs`
  (ventana configurable) → grupos de error priorizados + "qué hacer" (link a autofix).
  `/api/errors`.
- **`interactions`** — `agent_logs` → volumen en ventana, últimas N, % con error.
  `/api/interactions`.
- **`etl`** — Supabase `scraper_runs` → última ejecución por scraper, status, métricas,
  frescura (`_compute_radar_freshness` ya existe como referencia). `/api/etl`.
- **`freshness`** — para una lista configurada de tablas (tabla + columna de fecha),
  consulta el `MAX(fecha)` y lo compara con hoy → al día / desfasado (umbral por
  tabla). `/api/freshness`.

### Ficheros

- `dashboard/__init__.py`
- `dashboard/app.py` — FastAPI: monta `/api/<panel>` y sirve `static/index.html`.
- `dashboard/panels/claude_health.py` · `runs.py` · `errors.py` · `interactions.py` ·
  `etl.py` · `freshness.py` — un módulo por panel, cada uno con una función pura que
  devuelve un dict serializable (testeable con fixtures, sin red).
- `dashboard/static/index.html` (+ `dashboard.js`, `dashboard.css`) — la página con
  las zonas del vídeo: medidores arriba, gráfico de actividad, paneles
  (errores/interacciones/etl/freshness), sidebar de runs + forecast.
- `dashboard/config.py` — qué tablas/umbrales por panel; extiende/lee
  `qa/targets/petramora.yaml` (sección nueva `freshness:` y `etl:`).
- `scripts/dashboard.sh` — lanza `uvicorn dashboard.app:app` con el venv y el .env.

### Interfaces

- Cada panel: `def data(cfg, **opts) -> dict` puro respecto a la forma; el I/O de red
  vive en funciones que se pueden inyectar/fakear en tests.
- `app.py` mapea cada endpoint a `panel.data(cfg)`, captura excepciones y devuelve
  `{"ok": false, "error": "..."}` (un panel caído no tumba la página).

### Flujo de datos

```
navegador abre / → carga index.html → JS llama a cada /api/<panel>
   → app.py → panel.data(cfg) lee su fuente (Supabase / ~/.claude / ficheros)
   → JSON → render en su zona; auto-refresh cada ~30s
```

### Robustez / errores

- Paneles independientes: el endpoint captura cualquier excepción y responde
  `ok:false`; el panel muestra "no disponible" sin afectar al resto.
- Credenciales (Supabase) desde `.env`/env, igual que `qa/`. Nunca en el cliente.
- Solo lectura: la v1 no ejecuta nada ni escribe en las fuentes.

### Cómo se lanza

`bash scripts/dashboard.sh` → `uvicorn dashboard.app:app --port <p>` con venv nativo y
`.env` de Petramora cargado → abrir `http://localhost:<p>` (WSL reenvía a Windows).

## Tests (TDD)

- Cada `panels/*.py`: función `data` testeada con fixtures sintéticas (filas Supabase
  de ejemplo, contenido de cron.log, logs de Claude Code de ejemplo) — sin red.
- `app.py`: TestClient de FastAPI — cada `/api/<panel>` responde 200 con la forma
  esperada inyectando un panel fake; un panel que lanza → `ok:false` (no 500).
- `freshness`/`etl`: probar el cálculo "al día/desfasado" con fechas fijas.

## Fuera de alcance (YAGNI)

- v2 (ejecución headless: cuadro de prompt + botones que lanzan `claude -p`).
- ETL financieros y frescura Azure SQL (módulos futuros con pre-requisito conocido).
- Pulido visual fino estilo vídeo (pasada aparte con `frontend-design`); v1 prioriza
  estructura + datos reales.
- Autenticación (es local, un solo usuario).

## Criterio de éxito

1. `bash scripts/dashboard.sh` levanta el app y `http://localhost:<p>` muestra la
   página con los 6 paneles poblados con **datos reales** (verificado).
2. Cada panel lee su fuente real (scraper_runs, agent_logs, cron.log, ~/.claude,
   tablas de frescura) y, si su fuente falla, muestra "no disponible" sin tumbar el
   resto.
3. La suite de tests (paneles + endpoints con fakes) verde, sin llamadas de red en los
   tests.
4. El panel de uso de Claude Code muestra datos del log o, si el formato no da,
   degrada limpio a actividad por nº de runs (decisión documentada en el plan).
