# Agentic OS — Fase Skills (piloto: Desarrollo) — Diseño

**Fecha:** 2026-05-25
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto y objetivo

Inspirado en el vídeo "Claude Code Agentic OS" de Chase AI
(https://www.youtube.com/watch?v=pfPi04pIfaw). Un "Agentic OS" sobre Claude
Code resuelve tres gaps: **memoria**, **consistencia** (skills + automatizaciones)
y **acceso** (dashboard).

El pilar de **memoria** ya existe (vault Karpathy/Obsidian en
`.../Agente IA/Autoresearch`). Este spec cubre **solo el primer subsistema del
pilar de consistencia: los Skills**, organizados como organigrama.

Las automatizaciones (cron/cloud) y el dashboard son fases 2 y 3 — spec aparte.

## Decisiones de diseño (tomadas en brainstorming)

1. **Enfoque A — skills personales globales + mapa en vault.** Los skills custom
   viven en `~/.claude/skills/` (disponibles desde cualquier proyecto). El
   organigrama es una página en el vault. Descartados: B (skills dentro del repo
   Petramora — no reutilizable) y C (híbrido — más complejo para arrancar).
2. **Rama piloto: Desarrollo (Petramora/BIwise).** Las otras 3 ramas (Research,
   Comercial, Contenido) se construyen después con el mismo molde.
3. **Reality-check: los skills de Claude Code son planos**, no anidados. El
   "organigrama" es (a) convención de nombres + (b) mapa visual. No hay jerarquía
   real en disco.
4. **No duplicar funcionalidad existente.** De las tareas dev candidatas, las
   genuinamente nuevas son los evals y el deploy (este último se separa en
   staging y prod). worktree y code-review ya existen como plugins y se
   **referencian**, no se reconstruyen.

## Alcance: la rama Desarrollo

### Nodos custom (los escribimos) — 🟢

- **`dev-evals`** — ejecuta el arnés pytest de evals del agente Petramora en el
  worktree correcto, resume pass/fail y enlaza el reporte. Parametriza la ruta del
  repo/worktree (la pregunta o la lee del `CLAUDE.md` del repo). Base ya existente:
  Fase 0 en el worktree `feature/agent-evals`.
- **`dev-deploy-staging`** — deploy a staging. Acción: `commit + push` a la rama
  `staging` → autodeploy del entorno staging. Reglas: gcloud por **PowerShell** (no
  WSL); Vercel autodeploya con push.
- **`dev-deploy-prod`** — deploy a prod. Acción: `merge` de `staging` → `master` →
  autodeploy de prod. *Guardarraíl*: no mergear a `master` sin staging + preview
  validados (salvo autorización explícita). Verifica precondiciones antes de mergear.

Son **dos acciones distintas**, por eso son dos skills separados (no un skill con
modos). El ciclo completo de dev:

```
worktree (feature aislada) → integrar a 'staging' → dev-deploy-staging (push) → dev-deploy-prod (merge a master)
```

El **worktree es la fase previa**, no parte del deploy: aísla el desarrollo de la
feature; cuando está lista se integra a `staging` y ahí arranca el ciclo de deploy.
En el mapa se ve la cadena completa, pero los skills de deploy solo cubren
staging-push y prod-merge.

### Nodos plugin (referenciados, NO se tocan) — 🔵

- `superpowers:using-git-worktrees` (sustituye al "dev-worktree" candidato)
- `superpowers:requesting-code-review` + skill `/code-review` (sustituye a "dev-review")
- `superpowers:test-driven-development`
- `superpowers:systematic-debugging`
- `superpowers:verification-before-completion`
- `frontend-design` (UI de BIwise)
- `watch` (transversal — encaja mejor en Research, se marca como compartido)

## Estructura física

```
~/.claude/skills/
  dev-evals/SKILL.md
  dev-deploy-staging/SKILL.md
  dev-deploy-prod/SKILL.md

<vault>/proyectos/agentic-os.md      # organigrama: markdown + diagrama Mermaid
```

- **Convención de nombres:** prefijo por rama → `dev-*`. Futuras ramas:
  `research-*`, `com-*`, `content-*`.
- **El mapa** (`agentic-os.md`) distingue visualmente nodos custom (🟢) de plugin
  (🔵) y lista qué hace cada uno + cómo invocarlo.

## Interfaces / cómo se usa cada unidad

- **`dev-evals`**: se invoca cuando Eric quiere correr los evals. Entrada: (opcional)
  ruta del worktree. Salida: resumen pass/fail + ruta del reporte. Depende de: pytest,
  el repo Petramora, el worktree de evals.
- **`dev-deploy-staging`**: se invoca para publicar a staging. Entrada: ninguna (o
  mensaje de commit). Salida: commit + push a `staging` confirmados. Depende de:
  estado git del repo, rama `staging`, gcloud por PowerShell.
- **`dev-deploy-prod`**: se invoca para promover a prod. Entrada: ninguna. Salida:
  precondiciones verificadas + merge `staging`→`master`. Depende de: que staging +
  preview estén validados, estado git del repo, reglas en memoria.
- **Nodos plugin**: se invocan por su nombre de skill estándar; el mapa solo los
  documenta.

## Patrón replicable

Validado el piloto, cada rama nueva sigue: identificar tareas reales → clasificar
custom vs plugin → nombrar con prefijo → añadir al mapa `agentic-os.md`.

## Fuera de alcance (YAGNI)

- Automatizaciones (cron local / cloud scheduled tasks) — Fase 2.
- Dashboard / command center — Fase 3.
- Las ramas Research, Comercial, Contenido — réplicas posteriores.

## Criterio de éxito

1. `dev-evals`, `dev-deploy-staging` y `dev-deploy-prod` existen en
   `~/.claude/skills/`, se invocan y hacen lo descrito (verificado, no asumido).
2. `agentic-os.md` en el vault muestra el organigrama de la rama Desarrollo con los
   dos tipos de nodo.
3. El patrón queda claro para replicar a las otras 3 ramas.
