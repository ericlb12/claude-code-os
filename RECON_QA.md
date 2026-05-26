# RECON_QA — Fuentes de trazas del agente Petramora

Reconocimiento de solo lectura del repo `source_petramora/Agente_segmentador/` para
construir un agente de QA/observabilidad. Objetivo: confirmar qué existe HOY y el
**shape real** de los datos. No se han extraído datos reales de usuarios (privacidad);
todo el shape sale del código.

Fecha: 2026-05-26.

---

## 1. Langfuse — NO INTEGRADO

**No existe integración Langfuse en el repo.**

- `grep -rin "langfuse"` sobre `Agente_segmentador/**.py` → **0 resultados**.
- `.env` no contiene ninguna var `LANGFUSE_*` (claves presentes: `SUPABASE_URL`,
  `SUPABASE_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`,
  `AZURE_SQL_*`, `STEEL_API_KEY`).
- `requirements.txt` no incluye `langfuse`.
- Langfuse aparece solo como **pendiente futuro** en `CLAUDE.md` (sección "Do not / Pendientes":
  *"CORS restrictivo, Auth JWT, Rate limiting, Observabilidad (Langfuse)"*) — es un TODO, no código.

**Conclusión:** no hay traces de Langfuse que ingerir. El adapter Langfuse del agente de QA
NO se puede construir contra datos reales hoy. La única fuente de trazas real es **Supabase**.

---

## 2. Supabase — INTEGRADO (única fuente de trazas)

### Cliente
- Librería: **`supabase-py`** (`supabase` en requirements.txt). NO se usa psycopg/SQL directo
  para las interacciones.
- Instanciación singleton en `Agente_segmentador/config.py`:
  ```python
  from supabase import create_client
  SUPABASE_URL = os.getenv("SUPABASE_URL")
  SUPABASE_KEY = os.getenv("SUPABASE_KEY")
  def get_supabase():   # singleton _supabase_client
      _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
      return _supabase_client
  ```
- Acceso REST PostgREST (`.table().select()/.insert()/.upsert()`). Aplica el límite de
  **1000 filas por request** de PostgREST (relevante para paginar al ingerir histórico).
- Env vars de credenciales: **`SUPABASE_URL`**, **`SUPABASE_KEY`** (en `Agente_segmentador/.env`).

### Cliente recomendado para el agente de QA
`supabase-py` con las mismas `SUPABASE_URL` / `SUPABASE_KEY`. Paginar con `.order("id")` o
`.order("timestamp")` + `.range()` porque PostgREST tope 1000 filas (gotcha documentado en el repo).

### Tabla de interacciones usuario↔agente: `agent_logs`  ← FUENTE PRINCIPAL

Escritura en `agent.py::log_interaction()` (líneas ~133-147), llamada desde
`agent.py::chat()` y desde `api.py` (endpoint `/api/chat/stream`, línea ~271).
Una fila = un turno completo (input usuario + respuesta agente).

Columnas insertadas (shape real del insert):

| Columna | Tipo aprox. | Contenido |
|---|---|---|
| `session_id` | text | ID de sesión (uuid4) — agrupa turnos de una conversación |
| `user_message` | text | Input del usuario (texto crudo) |
| `agent_response` | text | Respuesta final del agente |
| `tools_called` | jsonb | Lista de tools llamadas (ver shape abajo) |
| `model_used` | text | Modelo efectivo (`gemini-...` / `gpt-4o...`, refleja fallback) |
| `latency_ms` | int | Latencia total del turno en ms (`time.time()` start→fin en `chat_core`) |
| `error` | text / null | Mensaje de error del turno (str), `None` si OK |
| `chart_data` | jsonb / null | Datos de gráfica (recharts); añadido vía DDL `ADD COLUMN IF NOT EXISTS chart_data JSONB` |
| `timestamp` | timestamptz | **No se inserta explícitamente** — default de la tabla. Se usa para ordenar (`get_session_messages` hace `.order('timestamp')`) → existe en el esquema. |
| `id` | int/uuid | PK implícita (no se setea en insert) |

**Shape de `tools_called`** (en `agent.py::chat_core`, línea ~732):
```python
tools_called.append({"name": tool_name, "args": tool_args})
# => [{"name": "get_customer_detail", "args": {"cliente_id": "..."}}, ...]
```
GOTCHA QA: **`tools_called` NO registra ok/error ni resultado por tool**. Solo nombre + args.
El éxito/fallo de una tool individual no queda persistido; solo se ve el `error` agregado del
turno. Si una tool devuelve `{"error": "..."}`, eso va dentro del flujo del LLM pero NO a `agent_logs`.

**Campo `error`** (turno): se rellena con el `str(e)` de excepciones del modelo (fallo de
LLM primario+fallback, fallo post-tool) o el literal `"Respuesta vacía"` cuando el modelo no
devuelve texto. Es error a nivel de turno, no por tool.

### Tabla de sesiones: `agent_sessions` (secundaria, no es traza de QA)

`agent.py::save_session()` (upsert, on_conflict `session_id`). Guarda el historial serializado
para continuidad de conversación, no para QA:

| Columna | Contenido |
|---|---|
| `session_id` | PK lógica (upsert) |
| `user_id` | id de usuario (puede ser None) |
| `history` | historial serializado por el adapter (gemini/openai) |
| `provider` | `gemini` \| `openai` |
| `updated_at` | ISO timestamp (`datetime.now().isoformat()`) |

Útil como complemento (provider, user_id), pero el grano de QA está en `agent_logs`.

### Otras tablas (NO son interacciones del agente conversacional)
- `research_conversations` / `research_messages` — sub-agente Research (api_research.py). Modelo
  distinto (conversación + mensajes). Si el QA debe cubrir Research, es una segunda fuente con
  shape propio (no detallado aquí; confirmar columnas de `research_messages` si entra en alcance).
- `competitors`, `scraper_runs`, `scraper_schedules`, `social_posts` — pipeline de scrapers de
  competencia, no interacciones usuario↔agente. `scraper_runs` sí tiene `status`/`error_message`/
  `duration_ms` (útil para QA de scrapers, fuera del alcance "agente conversacional").
- `segmentacion_clientes_raw`, `lineas_cliente_producto`, `catalogo_productos`, `fact_pyg`,
  `fact_presupuesto` — datos de negocio que consumen las tools, no trazas.

---

## 3. Mapeo a modelo común `Interaction`

Modelo objetivo:
`Interaction{id, timestamp, source, user_input, agent_output, tool_calls[], execution_error, latency_ms, raw}`

### Fuente A — Supabase `agent_logs` (principal, recomendada)

| Campo Interaction | Sale de `agent_logs` | Notas |
|---|---|---|
| `id` | `id` (PK) | implícita |
| `timestamp` | `timestamp` | default de tabla; usar para orden/ventanas |
| `source` | constante `"supabase:agent_logs"` | — |
| `user_input` | `user_message` | directo |
| `agent_output` | `agent_response` | directo |
| `tool_calls[]` | `tools_called` | lista `{name, args}`. **Sin ok/error por tool** → mapear cada uno con `status=unknown` |
| `execution_error` | `error` | error a nivel de turno (str o null); incluye `"Respuesta vacía"` |
| `latency_ms` | `latency_ms` | directo |
| `raw` | fila completa | incluye `model_used`, `chart_data`, `session_id` |

Enriquecimiento opcional uniendo por `session_id` con `agent_sessions` para `provider` y `user_id`.

### Fuente B — Langfuse
**No disponible.** Sin datos. Mapeo no construible hoy.

---

## 4. Huecos / lo que NO existe o no se pudo confirmar

1. **Langfuse: no integrado** en absoluto. Cambia el alcance: el agente de QA solo tiene
   **una fuente real (Supabase `agent_logs`)**, no dos. El adapter Langfuse debe quedar como
   stub/futuro hasta que se integre (es un TODO en CLAUDE.md).
2. **Estado por tool (ok/error/resultado) NO se persiste.** `tools_called` = solo `{name, args}`.
   El QA no puede saber qué tool concreta falló a partir de `agent_logs`; solo el error agregado
   del turno. Si esto es requisito, hay que instrumentar el agente (cambio en `chat_core`) — fuera
   del alcance de solo-recon.
3. **Esquema exacto de columnas (tipos, defaults, nullability) no verificado contra la BD viva** —
   inferido del código de insert/select. `timestamp`, `id` y `chart_data` se deducen de
   `.order('timestamp')`, la PK implícita y el DDL `ADD COLUMN chart_data JSONB` (en CLAUDE.md),
   no se leyó el DDL real. Confirmar con `list_tables` / `inspect_schema.py` antes de fijar adapter.
4. **No hay timestamp de inicio por tool ni latencia por tool**; `latency_ms` es total del turno.
5. **Research** (`research_conversations`/`research_messages`) es un modelo de datos distinto; si
   entra en alcance del QA, requiere un segundo adapter con shape propio (columnas no confirmadas aquí).
6. **PII**: `agent_logs` contiene `user_message`/`agent_response` con datos de clientes (nombres,
   móvil, mail vía tools RFM). El agente de QA debe tratar esto como dato sensible.

---

## Resumen ejecutivo

- **Langfuse:** NO integrado (solo TODO futuro). Sin trazas.
- **Supabase:** integrado, cliente `supabase-py` (singleton `get_supabase()`, vars `SUPABASE_URL`/`SUPABASE_KEY`).
- **Tabla de interacciones:** `agent_logs` (session_id, user_message, agent_response, tools_called[jsonb {name,args}], model_used, latency_ms, error, chart_data, timestamp). Una fila por turno.
- **Limitación clave:** no hay estado ok/error por tool, solo error agregado del turno.
