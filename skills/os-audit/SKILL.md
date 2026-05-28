---
name: os-audit
description: Use cuando Eric pida auditar su Claude Code OS, puntuarlo contra las 4 C, o diga "audita mi OS" / "¿está bien montado mi OS?" / "os-audit". Produce un scoreboard de las 4 C (0-100) con el top-3 de huecos por leverage. Solo lectura.
---

# os-audit — termómetro 4C del Claude Code OS

Audita el OS de Eric (proyecto `claude_code_os` + lo que vive en `~/.claude`).
SOLO LECTURA. Puntúa las 4 C (25 c/u = 100), lista fortalezas y el top-3 de huecos
con el siguiente paso. Re-correr semanal para ver subir la nota.

Alcance: "¿está el OS bien construido?" (estructura). NO es planificador de
capacidades nuevas — eso es `os-level-up`.

## Las 4 C (25 c/u)
- **Context** — conoce el negocio: `CLAUDE.md`, memoria del proyecto y auto-memoria
  del usuario (glob `~/.claude/projects/*/memory/MEMORY.md` y usa la entrada poblada;
  para Eric la canónica es `~/.claude/projects/-mnt-c-Users-Luis-Ojeda/memory/`, NO
  la derivada del cwd cuando se corre en headless desde `$OS_DIR`), el vault Karpathy
  (`/home/eric_likeik/wiki`), `connections.md`.
- **Connections** — alcanza los sistemas: `connections.md` (filas con mecanismo/auth),
  `.env`/Supabase, `references/{tool}-api.md` si existen, MCPs en settings.
- **Capabilities** — sabe hacer el trabajo: `~/.claude/skills/*/SKILL.md` (los `dev-*`,
  `os-*`), paquetes `qa/` y `dashboard/` del repo, plugins referenciados.
- **Cadence** — corre solo: `crontab -l` (tarea nightly), `scripts/nightly.sh`,
  `qa-reports/petramora/cron.log`, el dashboard.

## Ejecución
1. **Descubre la forma** (Glob/Read, por patrón no path fijo): CLAUDE.md, MEMORY.md,
   `~/.claude/skills/*/SKILL.md`, `qa/` y `dashboard/` (cuenta módulos), `connections.md`,
   `references/`, `decisions/`, `crontab -l`, `scripts/`, `audits/` previos.
2. **Puntúa cada C /25** según lo encontrado. No penalices nombres no canónicos si la
   intención está cubierta. Guía:
   - Context: hay CLAUDE.md con persona+prioridades (8) + memoria poblada (8) + vault/
     connections (9).
   - Connections: nº de sistemas reachable en connections.md con mecanismo+auth, frescura.
   - Capabilities: nº y calidad de skills + que existan qa/ y dashboard/ operativos.
   - Cadence: cron instalado + corriendo (mira cron.log reciente) + dashboard.
3. **Top-3 huecos** ponderados por leverage, cada uno con un comando/siguiente paso.
4. **Escribe** el informe en `<OS_DIR>/audits/audit-<YYYY-MM-DD>.md` (donde `<OS_DIR>` =
   `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os`)
   y muéstralo. Si la escritura falla (p.ej. headless sin permiso), cae a
   `/tmp/audit-<YYYY-MM-DD>.md` y avisa en la salida.

## Formato de salida
```
# OS Audit — <fecha>
Context: NN/25 · Connections: NN/25 · Capabilities: NN/25 · Cadence: NN/25 → TOTAL NN/100

## Fortalezas
- ...

## Top-3 huecos (por leverage)
1. [C afectada] hueco — siguiente paso: <comando/acción>
2. ...
3. ...
```

## Reglas
- Solo lectura. No modifiques nada salvo escribir el informe en `audits/`.
- Si falta `connections.md`, penaliza Connections y proponlo como hueco #1.
- Compara con el audit anterior en `audits/` si existe (¿subió la nota?).
