# RECON_DASH — reconocimiento de fuentes para el dashboard QA

Fecha: 2026-05-27

## 1. Logs locales de Claude Code

- Directorio: `~/.claude/projects/<slug-del-cwd>/<sessionId>.jsonl`
- Formato: **JSONL** (un objeto JSON por línea). No todas las líneas son mensajes de
  conversación; hay entradas de control (`custom-title`, `system`, `hook_success`,
  `attachment`, `worktree-state`, etc.).

### ¿Uso por día o solo conteo?
**Uso por día (tokens) SÍ es calculable.** Las líneas con `"type":"assistant"`
contienen `message.usage` con el desglose completo y la línea trae un `timestamp`
ISO-8601 de nivel superior.

Campos reales de una línea de tipo `assistant`:
- Nivel superior: `parentUuid`, `isSidechain`, `message`, `requestId`, `type`,
  `uuid`, `timestamp`, `userType`, `entrypoint`, `cwd`, `sessionId`, `version`,
  `gitBranch`.
- `message.usage`: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`,
  `cache_read_input_tokens`, `server_tool_use` (`web_search_requests`,
  `web_fetch_requests`), `service_tier`, `cache_creation`
  (`ephemeral_1h_input_tokens`, `ephemeral_5m_input_tokens`), `iterations[]`, `speed`.

Para uso por día: filtrar `type=="assistant"`, agrupar por `timestamp[:10]`, sumar
`input_tokens + output_tokens (+ cache_* si se quiere coste total)`.

> Nota: como degradación, si una sesión no tuviera `usage` se podría caer a un
> simple conteo de entradas, pero en los datos actuales el `usage` está presente.

## 2. Columnas reales de Supabase (verificadas)

### scraper_runs (ETL de scrapers)
`id`, `competitor_id`, `status`, `products_found`, `products_updated`,
`alerts_generated`, `error_message`, `duration_ms`, `run_at`
- Columna de fecha → **`run_at`**
- Columna de estado → **`status`**

### segmentacion_clientes_raw
`cliente_id`, `fecha_corte`, `fecha_ultima_compra`, `segmento_rfm`,
`ventas_2024/2025/2026`, `facturas_2024/2025/2026`, `gasto_total`,
`gasto_reciente`, `email`, `phone_number`, `rfm_score`
- Columna de fecha → **`fecha_corte`**

### agent_logs
`id`, `session_id`, `timestamp`, `user_message`, `agent_response`,
`tools_called`, `model_used`, `latency_ms`, `error`, `created_at`, `chart_data`
- Hay **dos** columnas de fecha: `timestamp` y `created_at`.
- Columna de fecha elegida para freshness → **`timestamp`** (la del evento del agente).

## 3. Columna de fecha elegida por tabla (freshness)

| Tabla                     | Columna fecha | Umbral (días) |
|---------------------------|---------------|---------------|
| scraper_runs              | run_at        | 2             |
| segmentacion_clientes_raw | fecha_corte   | 35            |
| agent_logs                | timestamp     | 2             |
