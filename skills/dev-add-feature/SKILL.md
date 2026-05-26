---
name: dev-add-feature
description: Use when Eric wants to add or change a capability of the Petramora agent (a new tool, a prompt rule, a behavior change) and have it verified. Triggers on "añade", "implementa", "cambia el agente", "nueva tool", "regla de prompt".
---

# dev-add-feature — añadir funcionalidad al agente Petramora, dirigido por evals

Flujo eval-driven (TDD a nivel de agente): **primero el caso de eval, lo ves en ROJO, implementas, lo ves en VERDE, commit.** Nunca al revés.

## Rutas y entorno
- Repo: `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora`
- Worktree de evals: `<repo>/.worktrees/feature-agent-evals` (rama `feature/agent-evals`). Si no existe, avisar a Eric y parar.
- Arnés en `Agente_segmentador/evals/`; comandos DESDE `Agente_segmentador/`. Intérprete: `python3`.
- Datasets: `evals/datasets/{comercial,analista,financiero,radar}.jsonl` (un caso JSON por línea).

## Flujo
1. **Aclarar el cambio** con Eric: qué modo, qué debe hacer, cómo se sabe que está bien. Si toca `prompts.py` (comportamiento en prod), describirlo y esperar OK (regla "explicar antes de ejecutar").
2. **Escribir el/los caso(s) de eval primero** en el `.jsonl` del modo. Elegir el tipo de check (ver tabla abajo).
3. **Correr en ROJO**: `python3 -m evals.run_evals --modo <modo>` (añade `--judge` si el caso tiene campo `judge`). Confirmar que falla por la razón esperada.
4. **Implementar** el cambio (tool en `tools_*.py` + map en `agent.py` + AMBOS adapters; o regla en `prompts.py`).
5. **Correr en VERDE**: mismo comando. Confirmar que pasa y que no rompiste otros casos.
6. **Commit** en la rama `feature/agent-evals` con mensaje claro.

## Qué check usar (lección clave)
| Quieres verificar | Check | Robustez |
|---|---|---|
| ¿Llamó la tool correcta? | `tools_esperadas` | determinista |
| ¿El número es correcto? | `valor_esperado` (ground-truth sacado de la BD directamente) | determinista |
| ¿Hubo error de ejecución? | `sin_error` (automático, campo real) | determinista |
| ¿Calidad/honestidad/disclosure? (prosa) | `judge` (criterio NL, requiere `--judge`) | **usa juez, NO substring** |

- `debe_contener`/`no_debe` (substring) son **frágiles** sobre prosa libre — el agente varía el fraseo run-to-run. Úsalos solo para tokens muy estables; para todo lo cualitativo, campo `judge`.
- Ground-truth de `valor_esperado`: consultar la fuente DIRECTAMENTE (Supabase para comercial/financiero/radar; Azure SQL para analista) y pegar el valor con el formato exacto que usa la respuesta del agente.

## Reglas
- NO implementar antes del caso de eval. Si lo hiciste, el caso ya no es una prueba honesta.
- NO tocar `prompts.py` sin describir el cambio y tener OK (cambia comportamiento en prod).
- Casos behavioral no deterministas: medir con `--judge`; aceptar que el agente puede no ser 100% fiable (variación del LLM) — reportar la tasa, no fingir verde.
- analista/radar NO son verificables en local (Azure SQL / IP WSL no whitelisted). Para esos, dejar el caso documentado y verificar en un entorno con acceso.
- Para correr el arnés sin implementar nada: usar la skill `dev-evals`. Para desplegar: `dev-deploy-staging`.
