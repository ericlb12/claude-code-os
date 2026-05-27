# os-audit + os-level-up + connections.md — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir dos meta-skills markdown (`os-audit`, `os-level-up`) adaptados del kit AIS-OS de Nate, más un `connections.md` real, al Claude Code OS de Eric.

**Architecture:** Skills de Claude Code (SKILL.md, instrucciones — NO código). Fuente versionada en `claude_code_os/skills/os-*/`, symlink a `~/.claude/skills/` (igual patrón que los `dev-*`). `connections.md` en la raíz del repo. Sin pytest: la validación es invocarlos (correr `os-audit` de verdad).

**Tech Stack:** Markdown (SKILL.md con frontmatter name/description), bash (symlinks), git. El propio Claude Code ejecuta los skills.

> **Setup:** `export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"`

---

## File Structure
- `$OS_DIR/connections.md` — registro de sistemas reales
- `$OS_DIR/skills/os-audit/SKILL.md` → symlink `~/.claude/skills/os-audit`
- `$OS_DIR/skills/os-level-up/SKILL.md` → symlink `~/.claude/skills/os-level-up`
- `$OS_DIR/audits/` — lo crea os-audit en su primer run

---

## Task 1: `connections.md`

**Files:** Create `$OS_DIR/connections.md`

- [ ] **Step 1: Escribir el fichero** con EXACTAMENTE este contenido:

```markdown
# Connections — sistemas que el Claude Code OS / agente Petramora alcanza

Registro de cada sistema alcanzable. Lo leen `os-audit` (cobertura/frescura) y
`os-level-up`. Al cablear algo nuevo, añade una fila (y, si es API, una guía en
`references/{tool}-api.md`).

| # | Dominio | Herramienta | Mecanismo | Auth | Última revisión |
|---|---|---|---|---|---|
| 1 | Trazas/interacciones agente | Supabase `agent_logs` | key+ref | SUPABASE_URL/KEY (en Petramora `.env`) | 2026-05-27 |
| 2 | Competencia / scrapers | Supabase `scraper_runs` | key+ref | idem Supabase | 2026-05-27 |
| 3 | Segmentación clientes | Supabase `segmentacion_clientes_raw` | key+ref | idem Supabase | 2026-05-27 |
| 4 | Ventas históricas | Azure SQL `MS_PETRAMORA_HIST_VENTAS` | script (solo vía backend Cloud Run, IP fija 34.175.58.90; NO desde WSL) | connection string en backend | 2026-05-27 |
| 5 | Código | GitHub `ericlb12/Petramora_source` | script (gh CLI) | gh auth (ericlb12) | 2026-05-27 |
| 6 | Deploy frontend | Vercel | export (autodeploy con push) | — | 2026-05-27 |
| 7 | Deploy/infra | gcloud | script (desde PowerShell, NO WSL) | gcloud auth | 2026-05-27 |
| 8 | Uso/actividad Claude Code | logs `~/.claude/projects/**/*.jsonl` | export (lectura local) | — | 2026-05-27 |

**Mecanismos:** `mcp` | `script` | `export` | `key+ref` | `not yet connected`.

## Pendientes de cablear (gaps conocidos)
- ETLs financieros (`etl_pyg`, etc.): se lanzan a mano, sin tabla de control → no observables. Falta tabla `etl_runs`.
- Frescura Azure SQL desde el dashboard: necesita endpoint en el backend Cloud Run.
- Langfuse: no integrado en Petramora (adapter listo en `qa/` pero `enabled:false`).
```

- [ ] **Step 2: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add connections.md && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: connections.md (registro de sistemas reales)"
```

---

## Task 2: skill `os-audit`

**Files:** Create `$OS_DIR/skills/os-audit/SKILL.md`; Symlink `~/.claude/skills/os-audit`

- [ ] **Step 1: Escribir `$OS_DIR/skills/os-audit/SKILL.md`** con EXACTAMENTE este contenido:

```markdown
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
- **Context** — conoce el negocio: `CLAUDE.md`, memoria (`MEMORY.md` del proyecto y
  `~/.claude/projects/<id>/memory/`), el vault Karpathy (`/home/eric_likeik/wiki`),
  `connections.md`.
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
4. **Escribe** `claude_code_os/audits/audit-<YYYY-MM-DD>.md` con el scoreboard y muéstralo.

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
```

- [ ] **Step 2: Symlink**

```bash
ln -sfn "$OS_DIR/skills/os-audit" ~/.claude/skills/os-audit
test -L ~/.claude/skills/os-audit && head -3 ~/.claude/skills/os-audit/SKILL.md
```
Expected: imprime el frontmatter `name: os-audit`.

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add skills/os-audit && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: skill os-audit (termómetro 4C)"
```

---

## Task 3: skill `os-level-up`

**Files:** Create `$OS_DIR/skills/os-level-up/SKILL.md`; Symlink `~/.claude/skills/os-level-up`

- [ ] **Step 1: Escribir `$OS_DIR/skills/os-level-up/SKILL.md`** con EXACTAMENTE este contenido:

```markdown
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
```

- [ ] **Step 2: Symlink**

```bash
ln -sfn "$OS_DIR/skills/os-level-up" ~/.claude/skills/os-level-up
test -L ~/.claude/skills/os-level-up && head -3 ~/.claude/skills/os-level-up/SKILL.md
```
Expected: frontmatter `name: os-level-up`.

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add skills/os-level-up && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: skill os-level-up (backlog de automatizaciones)"
```

---

## Task 4: Validación real + organigrama

**Files:** crea `$OS_DIR/audits/audit-<fecha>.md` (vía el skill); modifica `/home/eric_likeik/wiki/proyectos/agentic-os.md`

- [ ] **Step 1: Confirmar descubrimiento de ambos skills**

```bash
ls -l ~/.claude/skills/ | grep -E 'os-audit|os-level-up'
```
Expected: dos symlinks apuntando al repo.

- [ ] **Step 2: Correr `os-audit` de verdad** (invocarlo en la sesión: "audita mi OS" o vía Skill). Confirmar que: lee el layout real, produce una nota 4C con total /100, top-3 huecos con siguiente paso, y escribe `claude_code_os/audits/audit-<fecha>.md`. Es checkpoint manual de Eric (revisa que la nota y los huecos tengan sentido).

- [ ] **Step 3: Añadir al organigrama del vault** `/home/eric_likeik/wiki/proyectos/agentic-os.md` una sección "Meta-skills del OS" con `os-audit` y `os-level-up` (qué hacen, una línea cada uno), tras la sección de comparables. Commit en el vault:

```bash
cd /home/eric_likeik/wiki && git -c user.name="Eric" -c user.email="comercial@likeik.com" add proyectos/agentic-os.md && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: meta-skills os-audit/os-level-up en el organigrama"
```

- [ ] **Step 4: Commit del audit generado** (si Eric quiere versionarlo)

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add audits && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: primer audit 4C del OS"
```

---

## Self-Review (hecho al escribir el plan)
- **Cobertura del spec:** connections.md → Task 1; os-audit (4C, lee layout real, escribe audits/) → Task 2; os-level-up (entrevista, encadena a dev-add-feature) → Task 3; validación real + organigrama → Task 4. ✅
- **Placeholders:** los SKILL.md llevan contenido completo; `<fecha>`/`<id>` son tokens que el skill resuelve en runtime (fecha del día, id de proyecto), no TODOs. ✅
- **Consistencia:** nombres `os-audit`/`os-level-up` idénticos en frontmatter, symlinks, commits y organigrama; rutas reales (qa/, dashboard/, ~/.claude/skills, vault `/home/eric_likeik/wiki`, connections.md) coherentes con el resto del proyecto; encadenado a `dev-add-feature` (skill existente). ✅
- **Naturaleza:** markdown, sin pytest — coherente con el patrón de los `dev-*`. ✅
```
