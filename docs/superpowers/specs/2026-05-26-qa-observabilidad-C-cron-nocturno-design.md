# QA Observabilidad — Sub-proyecto C (Cron nocturno) — Diseño

**Fecha:** 2026-05-26
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Tercer y último incremento del pipeline de QA/observabilidad del Agentic OS
([[project-claude-code-os]]). A (ingesta+detección+informe) y B (reproduce+fix+PR)
ya están hechos. C automatiza la ejecución nocturna.

Pipeline completo: `[1 Ingesta]+[2 Detección]=A → [3 Reproducción]+[4 Fix+PR]=B → [5 cron]=C`.

## Decisiones tomadas en brainstorming

1. **El cron nocturno corre SOLO A** (informe). Eric descartó explícitamente la
   generación automática de PRs "al comienzo" — B sigue siendo manual, lo dispara
   él sobre el caso que elija. Cero PRs automáticos, cero ruido.
2. **Aviso = informe + log de runs.** Cada noche: el informe de A con histórico
   (`qa-reports/petramora/<fecha>.md`) + una línea de resumen en `cron.log`. Sin
   notificación externa (sería otro mini-proyecto).
3. **Mecanismo = cron en WSL.** Es LOCAL: si el PC/WSL está apagado a la hora
   programada, esa noche no corre. Aceptado; encaja con el futuro Mac mini 24/7
   ([[project-macmini-server]]). El `cron.log` permite ver qué noches corrió.

## Alcance de Sub-proyecto C

Flujo nocturno:
```
cron (WSL, ~03:00) → scripts/nightly.sh:
   export OS_DIR; source .env de Petramora (SUPABASE_*); usa venv ~/.venvs/claude_code_os
   → python -m qa.cron --target petramora --since 24h
        gather(cfg, since)  → interacciones (reusa el pipeline de A)
        run_report(...)      → escribe qa-reports/petramora/<fecha>.md
        añade línea de resumen a qa-reports/petramora/cron.log
```

### Unidades

- **Refactor menor en `qa/report.py`:** extraer la lógica de fetch de `main` a una
  función reutilizable `gather(cfg, since) -> tuple[list[Interaction], list[str], list[str]]`
  (interacciones, sources_ok, sources_failed). `main` pasa a llamar a `gather`. El
  comportamiento externo de A (CLI `python -m qa.report`) NO cambia.
- **`qa/cron.py`** (nuevo) — `nightly(os_dir, target, since) -> str`: carga config
  (`load_target`/`target_path`) → `gather` → `run_report` (escribe el `.md`) →
  calcula nº interacciones y nº grupos de error → añade una línea a
  `qa-reports/<target>/cron.log`. Devuelve la ruta del informe. CLI vía `main`:
  `python -m qa.cron --target petramora [--since 24h]`. Incluye `__main__`.
- **`scripts/nightly.sh`** (nuevo) — wrapper fino para cron: `export OS_DIR`,
  `set -a; source <petramora>/Agente_segmentador/.env; set +a`, lanza
  `~/.venvs/claude_code_os/bin/python -m qa.cron --target petramora`. Un `trap` en
  error escribe una línea `FAIL` en `cron.log` para que también los fallos del run
  queden registrados.

### Interfaces

- `gather(cfg, since)` — puro respecto a la lógica de selección de fuentes; hace I/O
  de red (Supabase/Langfuse) vía los adapters existentes. Reutilizado por `report.main`
  y por `cron.nightly`.
- `nightly(os_dir, target, since, *, gather=..., run_report=...)` — acepta `gather` y
  `run_report` inyectables (por defecto los reales) para poder testear sin red.

### Formato de `cron.log`

Una línea por ejecución, append:
```
2026-05-26T03:00Z | ok | interacciones=12 | grupos_error=3 | informe=qa-reports/petramora/2026-05-26.md
2026-05-27T03:00Z | FAIL | <motivo>
```

### Instalación del cron (manual, documentada en el plan)

Línea de crontab que Eric instala (`crontab -e`):
```
0 3 * * * /bin/bash "<OS_DIR>/scripts/nightly.sh" >> "<OS_DIR>/qa-reports/petramora/cron.boot.log" 2>&1
```
El plan incluye un paso de recon que comprueba si el servicio `cron` está activo en
WSL (`service cron status`) y cómo habilitarlo si no lo está, más la nota de la
realidad LOCAL (máquina encendida).

### Robustez / errores

- Si una fuente falla, A ya lo anota en el informe y sigue (no aborta). C hereda eso.
- Si `nightly` peta entero (p.ej. credenciales ausentes), el `trap` del `.sh` escribe
  `FAIL` + motivo en `cron.log`; el cron no deja el sistema en estado raro (solo
  lectura de Supabase + escritura de ficheros locales).
- Idempotencia: dos runs el mismo día sobrescriben el `.md` de esa fecha (es un
  snapshot diario) y añaden dos líneas al `cron.log`. Aceptable.

### Tests (TDD)

- `nightly()`: inyectar `gather` fake (devuelve interacciones de prueba) y `run_report`
  fake (o real con `tmp_path`); verificar que (a) se escribe el informe, (b) se añade
  la línea `ok` con los contadores correctos al `cron.log`, (c) si `gather` lanza, se
  añade una línea `FAIL`.
- `gather` (tras el refactor): test ligero de que A sigue verde (la suite existente de
  A cubre `report`/`run_report`; añadir un test de `gather` con adapters fake si aplica).
- `scripts/nightly.sh`: thin; smoke manual (Task de validación).

## Fuera de alcance (YAGNI)

- B / PRs automáticos (descartado por Eric en este incremento).
- Notificación externa (Slack/WhatsApp/email).
- Multi-target en un solo run (el cron apunta a `petramora`; otro target = otra línea
  de crontab o un arg distinto).
- Wake/scheduling robusto tipo Windows Task Scheduler (se eligió cron WSL).

## Criterio de éxito

1. `python -m qa.cron --target petramora --since 24h` corre A, escribe el informe del
   día y añade una línea `ok | interacciones=.. | grupos_error=..` al `cron.log`
   (verificado sobre datos reales).
2. Si el run falla (p.ej. sin credenciales), queda una línea `FAIL` en `cron.log`.
3. `scripts/nightly.sh` ejecutado a mano produce lo mismo que el CLI (smoke).
4. La línea de crontab queda documentada y el plan explica cómo activar `cron` en WSL.
5. La suite completa (A + B + C) sigue verde tras el refactor de `gather`.
