# QA Observabilidad — Sub-proyecto B (Reproduce + Fix + PR) — Diseño

**Fecha:** 2026-05-26
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Segundo incremento del pipeline de QA/observabilidad del Agentic OS
([[project-claude-code-os]]). Sub-proyecto A (ya hecho) ingiere trazas reales de
Supabase (`agent_logs`), detecta errores con señales deterministas y emite un
informe priorizado. B toma ese informe y cierra el lazo hacia la corrección:
**reproduce un error como caso de eval → un agente headless implementa el fix
(rojo→verde) → abre un PR** para revisión humana. Nunca mergea.

Pipeline completo: `[1 Ingesta] → [2 Detección] (=A) → [3 Reproducción] → [4 Fix+PR] (=B) → [5 cron] (=C)`.

## Decisiones tomadas en brainstorming

1. **B actúa solo sobre errores reproducibles/lógica**, en concreto la clase
   **`execution_error`** (el agente petó con un input dado). Los transitorios
   (timeout, retry/empty) se quedan en el informe de A, NO van a PR.
   - *Por qué execution_error es el caso dulce:* su reproducción no necesita
     ground-truth ni juez — el check es `sin_error` (el agente no debe petar con
     ese input). Determinista.
2. **Autonomía: reproduce + intenta fix (rojo→verde) + abre PR.** Humano revisa el
   PR; **nunca auto-merge**.
3. **Ejecución desatendida (headless):** el fix lo implementa un agente
   `claude -p`, de cara a poder cron-ear B en Sub-proyecto C. Eric revisa el PR
   resultante.
4. **Modo degradado:** si el agente NO llega a verde, no fuerza un fix malo — abre
   PR solo con el caso rojo, o reporta fallo. Nunca PR con verde falso.

## Alcance de Sub-proyecto B

Paquete `qa/autofix/` en `claude_code_os`. Flujo:
```
informe A (o re-run) → select(execution_error reproducibles)
  → re-fetch interacción por id desde Supabase (traer user_input real; A no guarda PII)
  → repro: construir caso de eval { input, check: sin_error } en el modo correcto
  → runner: claude -p headless en el worktree de evals de Petramora:
       crea rama qa-autofix/<fecha>-<slug>  (nunca master/staging)
       añade el caso → corre (ROJO) → implementa fix → corre (VERDE)
       commit → abre PR (base master) vía gh
  → devuelve URL del PR (o estado degradado)
```

### Unidades (una responsabilidad, testeable aislada)

- **`qa/autofix/select.py`** — de los `ErrorGroup[]`/findings del informe, filtra los
  candidatos reproducibles (`error_type == "execution_error"`). Devuelve los
  `interaction_id` a atacar. Puro.
- **`qa/autofix/repro.py`** — dada una `Interaction` (con `user_input` real),
  construye el caso de eval reproductor: `{"input": <user_input>, "checks": [{"tipo": "sin_error"}], "modo": <modo>}` con el formato del dataset de Petramora. Puro.
- **`qa/autofix/runner.py`** — lanza el agente headless (`claude -p`) con el prompt
  de fix y captura el resultado (URL del PR o estado). Efecto lateral; se inyecta el
  comando ejecutor para poder testear con un fake.
- **`qa/autofix/prompt.py`** — construye el texto del prompt para el agente headless,
  con los guardarraíles embebidos.
- **`qa/autofix/cli.py`** — `python3 -m qa.autofix --target petramora [--interaction <id>] [--dry-run]`.

### Interfaces

- `select(findings|groups) -> list[str]` (interaction_ids reproducibles).
- `build_repro_case(interaction, modo) -> dict` (caso de eval).
- `runner.run_fix(repro_case, interaction, cfg, dry_run) -> FixResult` con
  `FixResult{status: opened_pr|red_only|failed, pr_url, branch, detail}`.
- El CLI orquesta: select → fetch interacción (vía `qa.sources.supabase`) → repro →
  runner; imprime el resultado.

### El agente headless (runner) — contrato y guardarraíles

El `runner` invoca `claude -p "<prompt>"` (modo no interactivo) ejecutándose en el
worktree de evals de Petramora. El prompt (de `prompt.py`) instruye al agente a:
1. Crear una rama `qa-autofix/<YYYY-MM-DD>-<slug>` desde `master`. **Nunca** trabajar
   sobre `master` ni `staging`, **nunca** mergear, **nunca** pushear a esas ramas.
2. Añadir el caso de eval reproductor al dataset del modo correspondiente.
3. Correr el modo y confirmar **ROJO** por la razón esperada (el agente petaba).
4. Implementar el fix mínimo del bug.
5. Correr el modo y confirmar **VERDE**.
6. Commit en la rama + abrir PR con `gh pr create` (base `master`), cuerpo que
   explique: error original (id), caso añadido, qué se cambió, resultado de evals.
7. Si NO consigue verde: abrir PR solo con el caso rojo (modo degradado) etiquetando
   que requiere fix humano, o devolver `failed`. Nunca PR con verde falso.

`--dry-run`: el runner construye el prompt y muestra lo que haría, sin lanzar el
agente ni tocar el repo.

### Robustez / errores

- Si no hay `execution_error` reproducibles en el informe → B no hace nada y lo dice.
- Si la interacción no trae `user_input` (vacío/PII filtrada) → se descarta ese
  candidato con motivo, no se inventa.
- Si `gh` no está autenticado o `claude` headless falla → `FixResult.failed` con el
  detalle; no deja el repo en estado sucio (el agente trabaja en rama aparte).

### Tests (TDD)

- `select` y `repro`: fixtures sintéticas (`Interaction`/findings), puros, sin red.
- `runner`: se inyecta un ejecutor **fake** que simula la salida de `claude -p` y de
  `gh`; se verifican los 3 estados (`opened_pr`, `red_only`, `failed`) y que en
  `--dry-run` no se invoca nada. NO se lanza un agente real en los tests.
- `prompt`: verifica que el texto incluye los guardarraíles (rama, no-master,
  no-merge, modo degradado).

## Recon previo (primera tarea del plan)

Confirmar: (a) el CLI `claude` headless (`claude -p`) está disponible y funciona en
WSL; (b) `gh` está autenticado para `github.com/ericlb12/Petramora_source` (la
memoria registra gh v2.92.0 autenticado como `ericlb12` — verificar); (c) que los
`execution_error` de `agent_logs` traen un `user_input` reproducible y a qué `modo`
corresponden. Sin esto, el runner sería inventado.

## Fuera de alcance (YAGNI)

- Errores no-`execution_error` (timeouts, retry, calidad vía juez).
- El cron nocturno (Sub-proyecto C).
- Auto-merge o cualquier escritura a `master`/`staging`.
- Correr la suite COMPLETA de evals antes del PR (Eric eligió la variante sin esto;
  el agente corre el modo afectado, no todos).

## Criterio de éxito

1. `python3 -m qa.autofix --target petramora --dry-run` muestra el plan (caso
   reproductor + prompt) sin tocar nada.
2. Sobre un `execution_error` real, B crea rama, reproduce en rojo, intenta fix y
   abre un PR en `Petramora_source` (verificado con la URL), o cae en modo degradado
   de forma limpia.
3. En ningún caso B toca `master`/`staging` ni mergea.
4. `select`/`repro`/`runner`/`prompt` cubiertos por tests con fakes (sin agente real).
