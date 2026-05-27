# Dashboard v2 — Ejecución + pulido — Diseño

**Fecha:** 2026-05-27
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Segundo incremento del dashboard ([[project-claude-code-os]], Fase 3). La v1
(monitorización, solo lectura) ya corre. Feedback de Eric: "se ve muy simple y no hay
botones accionables". La v2 añade la **capa de ejecución** (el cuadro de prompt que
lanza Claude Code headless + botones seguros) y da una **pasada de pulido visual**.
Sobre el mismo app FastAPI `dashboard/`. Reúsa el patrón headless del Sub-proyecto B
(`qa/autofix/runner.py`: ejecutor inyectable, testeable sin agente).

## Decisiones tomadas en brainstorming

1. **Alcance de acción: botones seguros + cuadro de prompt libre.** Las acciones
   delicadas (deploy/add-feature/autofix real) NO tienen botón; se hacen escribiendo
   en el prompt si se quiere. Eric lo eligió explícitamente.
2. **Seguridad (aprobado):**
   - App solo en `127.0.0.1` (nadie externo acciona la máquina).
   - Working dir del prompt = `claude_code_os` por defecto (no el repo Petramora, para
     no tocar producción sin querer).
   - Claude headless en modo **normal** (NO `--dangerously-skip-permissions`).
   - **Allowlist** para botones-script: solo comandos predefinidos, nunca texto
     arbitrario del cliente.
3. **Salida síncrona** (clic → spinner → resultado) con timeout; sin streaming en vivo
   en esta v2.
4. **Pulido visual** con `frontend-design` sobre toda la página, manteniendo DOM
   seguro (textContent, sin innerHTML).

## Alcance de la v2

### Backend (nuevo)
- **`dashboard/exec.py`**:
  - `run_prompt(texto, cfg, executor=...) -> dict`: envuelve `claude -p "<texto>"`
    headless con cwd = `OS_DIR`; ejecutor inyectable (por defecto `subprocess.run`
    con lista de args, sin shell). Devuelve `{ok, output, returncode}`. Timeout 600s.
  - `run_script(script_id, cfg, executor=...) -> dict`: ejecuta un comando de una
    **allowlist** fija `{informe_qa: [...], evals: [...]}`; un id no permitido →
    `{ok: false, error: "script no permitido"}`. Para `ver_informe`/`ver_cron_log`
    el "script" es lectura de fichero (no ejecuta proceso).
- **`dashboard/app.py`** (modificar): añadir `POST /api/run` (body `{prompt}`) →
  `exec.run_prompt`; `POST /api/run-script` (body `{id}`) → `exec.run_script`. Ambos
  envueltos en `_safe`. Registrar cada ejecución en el run-log (que ya lee el panel
  `runs`).

### Frontend (modificar)
- Zona "RUN A SKILL": textarea + botón Run + botones-atajo (Informe QA, Correr evals,
  Ver informe, Ver cron.log). Los atajos llaman a `/api/run-script` con su id; Run
  llama a `/api/run` con el texto. Spinner mientras ejecuta; al volver, muestra la
  salida en un panel de resultado (con textContent).
- Pasada de pulido visual (frontend-design): medidores con barras, gráfico de
  actividad real (de `claude-health.actividad_por_dia`), tarjetas cuidadas, zona RUN
  destacada. Sin innerHTML.

### Allowlist de scripts (fija en el código)
```
informe_qa  -> ["<venv>/python", "-m", "qa.cron", "--target", "petramora"]
evals       -> ["<venv>/python", "-m", "evals.run_evals", "--modo", "comercial"]  (cwd = worktree evals)
ver_informe -> leer el último qa-reports/petramora/<fecha>.md
ver_cron_log-> leer qa-reports/petramora/cron.log
```

### Interfaces

- `run_prompt(texto, cfg, executor=_default) -> {ok, output, returncode}`.
- `run_script(script_id, cfg, executor=_default) -> {ok, output}` o `{ok: false, error}`.
- `executor(cmd_list, cwd) -> (returncode, stdout)` inyectable; en tests se pasa un
  fake (no lanza agente ni procesos reales).

### Robustez / errores

- `_safe` en los endpoints (ya existe) → un fallo no devuelve 500, devuelve `ok:false`.
- Timeout en `run_prompt`; si expira → `{ok: false, error: "timeout"}`.
- Allowlist estricta en `run_script`: id desconocido se rechaza sin ejecutar nada.
- El prompt corre en cwd `OS_DIR`, permisos normales de Claude.

### Tests (TDD)

- `run_prompt`: ejecutor fake devuelve salida simulada → `{ok:true, output:...}`; fake
  que lanza/timeout → `{ok:false}`. No se invoca `claude` real.
- `run_script`: id permitido → llama al ejecutor con el comando esperado de la
  allowlist; id NO permitido → `{ok:false, "no permitido"}` sin ejecutar.
- Endpoints `/api/run` y `/api/run-script` con TestClient + ejecutor fake monkeypatch.

## Fuera de alcance (YAGNI)

- Streaming de salida en vivo (SSE/websocket) — síncrono basta en v2.
- Botones para acciones delicadas (deploy/add-feature/autofix).
- Multi-usuario / autenticación.
- Permisos elevados (`--dangerously-skip-permissions`).

## Criterio de éxito

1. `POST /api/run {prompt}` lanza `claude -p` headless en `OS_DIR` y devuelve su salida
   (verificado en smoke real disparado por Eric).
2. Los botones-atajo (informe QA, evals, ver informe, ver cron.log) funcionan vía
   allowlist; un id no permitido se rechaza.
3. Cada ejecución queda registrada y aparece en el panel Runs.
4. La página queda con aspecto pulido (frontend-design), sin innerHTML.
5. Tests (run_prompt/run_script/endpoints con fakes) verdes, sin lanzar agente real.
