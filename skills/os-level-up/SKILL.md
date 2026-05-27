---
name: os-level-up
description: Use semanalmente para encontrar y scopear UNA automatización nueva para el Claude Code OS / agente Petramora. Entrevista corta → un candidato → scope → enviar. Triggers "os-level-up", "¿qué automatizo ahora?", "encuéntrame leverage esta semana", ritual de viernes.
---

# os-level-up — una automatización nueva por semana

Entrevista al usuario para sacar y scopear UNA automatización de alto leverage.
Una pasada = un artefacto scopeado. NO es `os-audit` (eso es estructura); esto es
funcional ("¿qué leverage me falta?").

## Lee primero (contexto)
- `connections.md` — qué es alcanzable y con qué mecanismo.
- `CLAUDE.md` + memoria del proyecto (prioridades, pain).
- `~/.claude/skills/*/SKILL.md` — qué capacidades ya existen (no repetir).
- Último `audits/audit-*.md` si existe.

## Fase 1 — encontrar el candidato (entrevista)
Pregunta de una en una, conversacional:
1. "Repasa tu semana: ¿qué hiciste 3+ veces?" (frecuencia)
2. "¿Algo que fue manual, aburrido o copy-paste?" (drudgery)
3. "¿Algo donde pensaste 'esto lo haría un becario espabilado'?" (delegación)
4. "Si llegaran 500 clientes mañana, ¿qué se rompe primero?" (constraint)
5. "¿Qué te daría 500 clientes más?" (growth lever)
→ Devuelve 1-3 candidatos con una línea de "por qué es leverage". Pide elegir uno.

## Fase 2 — scope (el elegido)
- Qué hace exactamente (entrada → salida).
- Inputs/fuentes (¿están en `connections.md`? si no, marcar que hay que cablear).
- Criterio de "hecho".
- Nivel de autonomía (on-demand / programado / con confirmación).
- ¿Es local o remoto? (toca ficheros/CLIs locales = local; tools nativas = remoto).

## Fase 3 — enviar / encadenar
- Si la automatización es una **capacidad del agente Petramora** (tool/regla de prompt)
  → derivar a la skill `dev-add-feature` (flujo eval-driven).
- Si es una **tarea recurrente** → derivar al patrón cron (`qa.cron`/`scripts/nightly.sh`)
  o a una routine.
- Si es de **research/contenido/comercial** → nueva skill de esa área.
- Sugerir registrar la decisión (en `decisions/log.md` si existe, o en memoria).

## Modo auto (headless / desde el dashboard)
Si te invocan sin un humano con quien conversar (p.ej. `claude -p` desde el botón del
dashboard, o el prompt pide "modo auto"): **NO entrevistes.** En su lugar, propón
1-3 candidatos de automatización a partir de lo que SÍ puedes leer —
`connections.md`, la memoria/CLAUDE.md (prioridades/pain), el último `audits/audit-*.md`
(huecos), `qa-reports/petramora/cron.log` (runs recientes) y los skills existentes —
cada uno con una línea de "por qué es leverage" + un scope breve (entrada→salida,
local/remoto, encadenado a `dev-add-feature`/cron). Marca que es una propuesta auto
(menos personalizada que la entrevista) y que para afinar conviene correrlo interactivo.

## Reglas
- Una pasada = un artefacto (modo entrevista). En modo auto, máx 3 propuestas.
- En entrevista, el usuario hace el pensamiento; tú conduces. En auto, deduces del contexto.
- "Boring is beautiful": prefiere workflow determinista a agente autónomo cuando valga.
