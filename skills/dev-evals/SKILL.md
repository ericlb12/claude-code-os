---
name: dev-evals
description: Use when Eric wants to run the Petramora agent evals (Agente_segmentador). Locates the agent-evals worktree, runs the pytest/run_evals harness from the right directory, and reports pass/fail with skipped cases.
---

# dev-evals — correr evals del agente Petramora

## Cuándo
Cuando Eric dice "corre los evals", "evalúa el agente", "evals de Petramora" o similar.

## Rutas y entorno
- Repo: `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora`
- Worktree de evals: `<repo>/.worktrees/feature-agent-evals` (rama `feature/agent-evals`)
- El paquete `evals/` vive en `Agente_segmentador/` → los comandos se ejecutan DESDE ese subdirectorio.
- Intérprete: `python3` (no existe `python`). venv en `/home/eric_likeik/petramora-venv`.

## Pasos
1. Ir al worktree de evals. Si no existe, avisar a Eric y parar (no crearlo en silencio).
2. `cd` a `Agente_segmentador/` dentro del worktree.
3. Ejecutar el arnés. Por defecto el runner:
   `python3 -m evals.run_evals`
   (o, si Eric quiere pytest: `python3 -m pytest tests/test_evals.py -v`).
4. Resumir: nº de casos, pass / fail / **skipped**, y los fallos con su mensaje.
5. Si hay casos skipped por falta de API key, decirlo (la key va en `Agente_segmentador/.env`).

## Reglas
- NO modificar el código del agente para "arreglar" un eval salvo que Eric lo pida.
- Si faltan deps: `pip` está bloqueado por PEP 668 — reportarlo, NO romper el entorno; usar el venv `/home/eric_likeik/petramora-venv` si hace falta.
