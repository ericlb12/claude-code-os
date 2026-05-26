# QA Observabilidad — Sub-proyecto A (Ingesta + Detección + Informe) — Diseño

**Fecha:** 2026-05-26
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Fase 2 del Agentic OS ([[project-claude-code-os]]): automatizaciones. En vez de
automatizar `dev-evals` (casos predefinidos de Petramora), Eric quiere un **agente
de QA/observabilidad agnóstico del repo** que mire el **uso real** del agente en
producción, detecte errores y, en fases posteriores, los corrija vía PR.

Pipeline completo (visión, NO todo en este spec):
```
[1 Ingesta] → [2 Detección] → [3 Reproducción con eval] → [4 Fix + PR] → [5 Scheduling cron]
```

Decisión de descomposición: se construye en incrementos, cada uno su spec→plan→impl.
- **Sub-proyecto A (este spec):** Etapas 1+2 — ingesta + detección + informe priorizado.
- **Sub-proyecto B:** Etapas 3+4 — reproducción con eval + abrir PR (reusa `dev-add-feature` y la disciplina de ramas de `dev-deploy`).
- **Sub-proyecto C:** Etapa 5 — cron WSL nocturno, agnóstico del repo.

## Decisiones tomadas en brainstorming

1. **Fuente de datos = trazas de producción reales** (no casos simulados). Infra
   existente: **Langfuse + Supabase**.
2. **Detección = señales deterministas primero** (sin LLM-judge en A). Judge se
   considerará en una iteración futura, no aquí.
3. **Meta final = detectar + abrir PR** (Sub-proyecto B). A se queda en detectar +
   reportar.
4. **Agnóstico del repo** vía fichero de config por target. Piloto = Petramora.
5. **Salida = informe markdown con histórico** (no notificación en A).
6. **On-demand en A** (el scheduling es Sub-proyecto C).

## Alcance de Sub-proyecto A

Una herramienta Python en `claude_code_os` (paquete `qa/`). Flujo:
```
config(target) → ingesta(Langfuse API + Supabase SQL) → Interaction[]
  → detect(señales deterministas) → ErrorFinding[]
  → group+priorizar → informe markdown con fecha
```

### Unidades (una responsabilidad cada una)

- **`qa/model.py`** — dataclasses `Interaction` y `ErrorFinding` (contrato común).
  - `Interaction`: id, timestamp, fuente (`langfuse`|`supabase`), input usuario,
    output agente, tools llamadas (nombre + ok/error + mensaje), error de ejecución
    (bool + mensaje), latencia, metadata cruda.
  - `ErrorFinding`: interaction_id, tipo de error, señal que lo disparó, severidad,
    extracto relevante.
- **`qa/config.py`** — carga `qa/targets/<repo>.yaml`. Campos: nombre target,
  proyecto Langfuse + var de entorno de su key, fuente Supabase (tabla/consulta) +
  var de entorno de credenciales, ventana temporal por defecto, definición de qué
  señales de error aplican.
- **`qa/sources/langfuse.py`** — trae trazas de Langfuse vía API en una ventana
  temporal → `Interaction[]`. Normaliza al modelo común.
- **`qa/sources/supabase.py`** — trae logs de Supabase vía SQL en la ventana →
  `Interaction[]`. Normaliza al modelo común.
- **`qa/detect.py`** — aplica señales deterministas sobre `Interaction[]` →
  `ErrorFinding[]`. Señales: (a) excepción/error en una tool, (b) error de
  ejecución del agente, (c) output vacío/null, (d) timeout/latencia sobre umbral,
  (e) campo de error explícito en la traza.
- **`qa/group.py`** — agrupa `ErrorFinding[]` por patrón (tool / tipo / firma
  normalizada del mensaje) y prioriza por frecuencia y recencia.
- **`qa/report.py`** — renderiza markdown y expone el CLI:
  `python3 -m qa.report --target petramora --since 24h`.

### Interfaces

- Cada source devuelve `Interaction[]` normalizado (mismo contrato, distinta fuente).
- `detect` consume `Interaction[]`, emite `ErrorFinding[]`. No conoce las fuentes.
- `group` consume `ErrorFinding[]`, emite grupos priorizados. Puro.
- `report` orquesta: config → sources → detect → group → markdown.

### Salida

Informe en `claude_code_os/qa-reports/<target>/YYYY-MM-DD.md`. Contenido:
- Resumen: ventana, nº interacciones, nº errores, nº grupos.
- Top grupos de error priorizados: patrón, frecuencia, severidad, 1-2 ejemplos de
  traza (id + extracto).
- Fuentes consultadas y cuáles fallaron (si alguna).

### Robustez / errores

- Si una fuente no responde o faltan keys → anotar el hueco en el informe y seguir
  con la(s) que funcionen. No abortar.
- Keys de Langfuse/Supabase desde `.env`/entorno, referenciadas por el YAML, nunca
  commiteadas. Repo ya tiene `.gitignore`.

### Tests (TDD)

- `detect`, `group`, `report`: fixtures sintéticas de `Interaction`/`ErrorFinding`,
  sin API en vivo. Cubren cada señal de error y la priorización.
- `sources/langfuse.py` y `sources/supabase.py`: probados contra payloads de
  ejemplo grabados (no llamadas en vivo en los tests).
- `config.py`: carga un YAML de ejemplo y valida campos.

## Fuera de alcance (YAGNI)

- LLM-as-judge, reproducción con eval, abrir PR, scheduling/cron, autocorrección.
- Tiempo real / streaming. A trabaja sobre una ventana temporal a petición.

## Riesgo / supuesto a verificar (primera tarea del plan)

- Confirmar que **Langfuse ya emite trazas de Petramora** en producción. La memoria
  `[[project-agent-evals]]` registraba "Langfuse Fase 1" como pendiente; Eric indica
  que ya existe. El plan empezará con un recon de feasibility de AMBAS fuentes
  (Langfuse + Supabase): qué proyecto/tabla, qué credenciales, formato real del
  payload. Sin esto, los adapters serían inventados.

## Criterio de éxito

1. `python3 -m qa.report --target petramora --since 24h` produce un informe markdown
   en `qa-reports/petramora/` a partir de trazas reales (verificado, no asumido).
2. La detección identifica al menos las 5 señales deterministas sobre datos reales.
3. El informe agrupa y prioriza, con ejemplos de traza trazables a su id.
4. Añadir otro repo = crear otro `qa/targets/<repo>.yaml`, sin tocar código.
