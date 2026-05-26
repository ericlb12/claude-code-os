# RECON_B — Feasibility Sub-proyecto B (repro de errores Petramora → PR auto-fix)

Fecha: 2026-05-26. Recon SOLO LECTURA. Todo lo de abajo está verificado en vivo salvo lo marcado como HUECO.

## 1. claude headless + gh

### `claude` CLI — SÍ
- Binario: `/home/eric_likeik/.local/bin/claude`
- Versión: `2.1.150 (Claude Code)`
- **Soporta headless: SÍ**, flag `-p` / `--print` ("Print response and exit, useful for pipes").
- Flags relevantes para automatizar el PR-fixer:
  - `--output-format text|json|stream-json` (usar `json` para parsear resultado).
  - `--max-budget-usd <amount>` (cap de coste, solo con `--print`).
  - `--fallback-model <model>` (resiliencia ante overload, solo con `--print`).
  - `--no-session-persistence` (no guardar sesión en disco).
  - El diálogo de "workspace trust" se omite en modo `-p` → no bloquea automatización. OJO: settings.json inválidos se ignoran en silencio.
- Invocación típica esperada:
  `claude -p "<prompt con el error reproducido y la instrucción de fix+PR>" --output-format json --max-budget-usd 2`

### `gh` CLI — SÍ y autenticado
- Binario: `/home/eric_likeik/.local/bin/gh`
- `gh auth status`: logged in a `github.com` como **ericlb12**, token activo.
- Scopes del token: `gist`, `read:org`, `repo`. → **`repo` presente ⇒ puede crear PRs.**
- Repo destino: `ericlb12/Petramora_source`
  - `nameWithOwner`: `ericlb12/Petramora_source`
  - **Rama por defecto: `master`**
- Acceso confirmado vía `gh repo view` (responde OK).

> NOTA: el subagente `claude -p` puede crear el PR él mismo con `gh pr create`, o devolver el diff y que el orquestador haga el PR. Ambas vías son viables con los scopes actuales.

## 2. execution_errors reproducibles en Supabase

- Tabla: `agent_logs`. Conexión OK con `.env` de Petramora (`SUPABASE_URL`/`SUPABASE_KEY`).
- Query usada: `error IS NOT NULL`, orden `timestamp` desc.
- **Columnas reales de `agent_logs`:**
  `agent_response, chart_data, created_at, error, id, latency_ms, model_used, session_id, timestamp, tools_called, user_message`

### Ejemplos reales (id | error | model | input)
- `1301` | `RetryError[... _EmptyResponseError]` | gemini-2.5-flash | "Top 10 productos por margen en 2025"
- `1010` | `Respuesta vacía` | gemini-2.5-flash | "¿Como esta la distribucion de clientes por segmento?"
- `1005` | `Respuesta vacía` | gemini-2.5-flash | "Como esta la distribucion de clientes por segmento?"
- `991`  | `Respuesta vacía` | gemini-2.5-flash | "¿Como esta la distribucion de clientes por segmento?"

**¿Traen `user_message` reproducible?** SÍ. Todos los errores tienen `user_message` no vacío → se puede re-ejecutar el mismo input contra `chat_core`.

**Naturaleza de los errores (relevante para feasibility del "fix"):** los dos patrones dominantes son `Respuesta vacía` y `RetryError/_EmptyResponseError`. Son fallos de **respuesta vacía del LLM (gemini-2.5-flash)**, no necesariamente bugs de código en una tool. Esto importa: un repro puede NO ser determinista (depende de la respuesta del modelo). El caso de eval ideal es uno donde el error es reproducible de forma estable (p.ej. una tool que peta), no un empty-response esporádico. HUECO: habría que clasificar errores por reproducibilidad antes de alimentar al fixer.

## 3. ¿Se puede determinar el MODO desde agent_logs?

**NO directamente.** Verificado:
- `agent_logs` **no tiene** columna `modo`/`mode`/`agent_type`/`tipo`.
- `log_interaction()` (`agent.py:133`) inserta solo: `session_id, user_message, agent_response, tools_called, model_used, latency_ms, error, chart_data`. **El modo no se persiste.**
- El modo SÍ existe en runtime: `chat_core(..., mode: str = "comercial", ...)` (`agent.py:657`) y `execute_tool(..., mode="comercial")` (`agent.py:489`). Routing por modo: comercial / analista / financiero / radar.

**Vías para inferir el modo (workarounds):**
1. **Por `tools_called`** (mejor opción): cada modo tiene un set de tools disjunto (comercial = 8 tools RFM Supabase; analista = tools SQL Server; etc.). Si la fila tiene `tools_called`, se mapea a modo. HUECO: filas con error de respuesta vacía suelen NO haber llamado tool → `tools_called` vacío → no se puede inferir.
2. **Fallback a modo por defecto `comercial`** (como pide el encargo) cuando no se puede inferir.

**Recomendación:** usar mapping `tools_called → modo`; si vacío, default `comercial`. Documentar que el repro asume ese modo.

## 4. Esquema EXACTO del dataset de evals + check `sin_error`

### Formato del .jsonl (un caso por línea). Claves REALES:
`id`, `pregunta`, `tools_esperadas`, `debe_contener`, `no_debe`, `valor_esperado`.
(El campo `modo` NO va en el JSON; se deriva del nombre de archivo `<modo>.jsonl` y se inyecta con `case.setdefault("modo", modo)` en `dataset.py:45`.)

### Línea real literal (`evals/datasets/comercial.jsonl`):
```json
{"id": "com-002", "pregunta": "dame los clientes Champions dormido que mas gastaban", "tools_esperadas": ["get_actionable_customers"], "debe_contener": [], "no_debe": [], "valor_esperado": []}
```

### El check `sin_error` (cómo se declara y evalúa)
- **NO es una clave del caso.** `sin_error` es un check **implícito y automático** generado por el evaluador, no algo que declares en el .jsonl.
- En `evaluator.py` (líneas ~52-56):
  ```python
  if result.get("error"):
      checks.append(CheckResult("sin_error", False, f"chat_core error: {result['error']}"))
  else:
      checks.append(CheckResult("sin_error", True))
  ```
- Es decir: el evaluador SIEMPRE añade el check `sin_error`, que pasa si `chat_core` devolvió un `result` sin `error`. Un caso de eval que reproduce un bug fallará automáticamente en `sin_error` mientras el bug exista, y pasará cuando el fix lo elimine. **Esto es exactamente lo que necesita el repro-as-eval: basta con añadir el caso (id + pregunta del error real) al .jsonl del modo correspondiente; el check `sin_error` hace de gate sin configuración extra.**

### Otros checks (todos opcionales; lista vacía ⇒ check omitido):
- `tools_esperadas`: pasa si se llamó AL MENOS UNA de las tools listadas (OR).
- `debe_contener`: pasa si TODOS los substrings están en la respuesta (case-insensitive).
- `no_debe`: pasa si NINGÚN substring está en la respuesta.
- `valor_esperado`: substrings de ground-truth de BD; pasan si TODOS presentes.

### Modos válidos
`{"comercial", "analista", "financiero", "radar"}` (`dataset.py:25`). Archivos en disco hoy: `analista.jsonl`, `comercial.jsonl`, `financiero.jsonl` (no hay `radar.jsonl`).

## Resumen de huecos
- HUECO-1: muchos errores son `Respuesta vacía` del LLM → posiblemente NO reproducibles de forma determinista. Filtrar por reproducibilidad antes de generar caso/fix.
- HUECO-2: el modo no se persiste; inferir por `tools_called`, default `comercial`. Filas con error suelen tener `tools_called` vacío → casi siempre caerá al default.
- HUECO-3: no existe `radar.jsonl`; si un error es de modo radar, hay que crear el dataset.
- HUECO-4: validar que el harness de evals corre OK en el worktree antes de cablear el flujo (skill `dev-evals` existe para esto).
