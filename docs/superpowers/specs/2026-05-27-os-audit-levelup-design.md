# os-audit + os-level-up + connections.md — Diseño

**Fecha:** 2026-05-27
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Inspirado en el repo MIT de Nate Herk ([[repo-ais-os-nate-herk]] / curso
[[curso-build-sell-claude-code-os-nate-analisis]]). Su kit aporta dos meta-skills que
a nuestro [[project-claude-code-os]] le faltan: un **termómetro estructural** del OS y
un **generador de backlog** de automatizaciones. Los adoptamos adaptados a nuestro
layout real (que es más maduro en ingeniería: qa/, dashboard/, evals, cron).

## Decisiones (brainstorming)

1. **Dos skills + un registro**: `os-audit`, `os-level-up`, y `connections.md`.
   **Sin `/onboard`** — el contexto de negocio ya vive en el vault Karpathy, claude-mem
   y `CLAUDE.md`; el wizard duplicaría.
2. **Son skills markdown (SKILL.md)**, no código Python. Igual patrón que los `dev-*`:
   fuente en `claude_code_os/skills/`, symlink a `~/.claude/skills/`. Validación =
   invocarlos (no pytest).
3. **Prefijo `os-`** para no chocar con palabras genéricas ni otros plugins.
4. **Solo lectura / entrevista**: no escriben en sistemas de negocio. `os-audit` solo
   lee; `os-level-up` entrevista y propone (a lo sumo escribe un scoreboard / sugiere
   registrar una decisión).

## Entregables

### 1. `connections.md` (en `claude_code_os/`)
Registro de los sistemas reales que el OS/agente alcanza. Tabla:
`# | Dominio | Herramienta | Mecanismo | Auth | Última revisión`. Filas con datos
reales conocidos:
- Trazas/datos agente → Supabase (`agent_logs`) — mecanismo `key+ref` (SUPABASE_URL/KEY).
- Competencia/scrapers → Supabase (`scraper_runs`) — `key+ref`.
- Ventas históricas → Azure SQL (`MS_PETRAMORA_HIST_VENTAS`) — solo vía backend Cloud Run (IP fija `34.175.58.90`), NO desde WSL.
- Código → GitHub `ericlb12/Petramora_source` — `gh` CLI.
- Deploy → Vercel (autodeploy con push) + gcloud (desde PowerShell, no WSL).
- Uso/actividad → logs Claude Code en `~/.claude/projects` — lectura local.
Mecanismos posibles: `mcp` | `script` | `export` | `key+ref` | `not yet connected`.
Es input de los dos skills y documentación útil por sí mismo.

### 2. `os-audit` — SKILL.md (símlink a `~/.claude/skills/os-audit`)
Adaptado del `audit` de Nate, apuntando a NUESTRO layout. Solo lectura.
- **Lee (por patrón, no path fijo):** `CLAUDE.md`; memoria en `~/.claude/projects/<id>/memory/MEMORY.md` + el `MEMORY.md` del proyecto; `~/.claude/skills/*/SKILL.md` (los `dev-*` y `os-*`); paquetes `qa/` y `dashboard/` (Capabilities); cadencia = crontab + `scripts/nightly.sh` + `qa-reports/petramora/cron.log`; `connections.md`; el vault Karpathy (Context/memoria de negocio); `.env`/Supabase.
- **Puntúa las 4 C, 25 c/u = 100:** Context (conoce el negocio), Connections (alcanza los sistemas), Capabilities (skills + dashboard + qa), Cadence (corre solo: cron). No penaliza nombres no canónicos si la intención está cubierta.
- **Salida:** scoreboard con la nota por C, fortalezas, y **top-3 huecos** ponderados por leverage, cada uno con un comando/siguiente paso concreto. Escribe el informe en `claude_code_os/audits/audit-<YYYY-MM-DD>.md` y lo muestra. Re-correr semanal (gancho de mejora compuesta).

### 3. `os-level-up` — SKILL.md (símlink a `~/.claude/skills/os-level-up`)
Adaptado del `level-up` de Nate. Entrevista → una automatización scopeada.
- **Lee:** `connections.md`, `CLAUDE.md` + memoria (prioridades/pain), `~/.claude/skills/*` (qué capacidades ya existen), últimos `audits/audit-*.md` si hay.
- **Flujo:** Fase 1 entrevista (5 preguntas: frecuencia "¿qué hiciste 3+ veces?", drudgery, smart-intern, constraint "¿qué rompe al escalar?", growth lever) → 1-3 candidatos con "por qué es leverage" → elige uno → Fase 2 scope (qué hace, inputs, criterio de hecho, nivel de autonomía) → Fase 3 sugiere enviar/registrar.
- **Encadenado:** si la automatización es una capacidad del agente Petramora, derivar a `dev-add-feature` (flujo eval-driven). Si es una tarea recurrente, derivar al patrón cron/qa. Sugerir registrar la decisión.

## Estructura física
```
claude_code_os/
  connections.md
  skills/os-audit/SKILL.md       -> symlink ~/.claude/skills/os-audit
  skills/os-level-up/SKILL.md    -> symlink ~/.claude/skills/os-level-up
  audits/                        (lo crea os-audit en su 1er run)
```

## Validación
- Correr `os-audit` de verdad sobre el repo → produce una nota 4C real y un
  `audits/audit-<fecha>.md` con top-3 huecos coherentes (verificado, no asumido).
- `os-level-up`: arrancar la entrevista y confirmar que lee los inputs y propone
  candidatos sensatos (checkpoint con Eric, es conversacional).
- Ambos descubiertos por Claude Code (aparecen en la lista de skills).

## Fuera de alcance (YAGNI)
- `/onboard` y un `context/` propio (ya cubierto por vault/CLAUDE.md/memoria).
- Que los skills escriban en sistemas de negocio.
- Automatizar la cadencia de correrlos (de momento se invocan a mano; se podría
  añadir al cron/dashboard luego).

## Criterio de éxito
1. `os-audit` y `os-level-up` existen en `~/.claude/skills/` (símlink desde el repo),
   descubiertos por Claude Code.
2. `os-audit` corrido sobre el repo da una nota 4C real + top-3 huecos con siguiente
   paso, y escribe `audits/audit-<fecha>.md`.
3. `connections.md` refleja los sistemas reales y es legible por `os-audit`/`os-level-up`.
4. Añadidos al organigrama del vault.
