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

## Reglas
- Una pasada = un artefacto. No multi-candidato.
- El usuario hace el pensamiento; tú conduces la entrevista.
- "Boring is beautiful": prefiere workflow determinista a agente autónomo cuando valga.
