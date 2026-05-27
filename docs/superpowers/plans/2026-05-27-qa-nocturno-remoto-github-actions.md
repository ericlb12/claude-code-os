# QA nocturno remoto (GitHub Actions) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir `claude_code_os` a un repo privado de GitHub y montar un workflow de GitHub Actions que corre el informe QA nocturno en la nube (con el PC apagado), commiteando el informe de vuelta.

**Architecture:** Repo privado `ericlb12/claude-code-os` (push del repo existente). `.github/workflows/qa-nightly.yml` corre `python -m qa.cron --target petramora` con `OS_DIR=github.workspace` y `SUPABASE_*` como secrets, y commitea `qa-reports/` de vuelta. Sin cambios en `qa/`. No es código/TDD: son operaciones git/gh + un YAML.

**Tech Stack:** GitHub Actions, gh CLI (autenticado como ericlb12), git, Python 3.12 (en el runner).

> **Setup:** `export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"`

---

## File Structure
- `$OS_DIR/.github/workflows/qa-nightly.yml` — NUEVO: el workflow programado.
- Resto del repo: se sube tal cual (ya versionado).

---

## Task 0: Secret-scan ANTES de subir nada

**Files:** ninguno (verificación)

- [ ] **Step 1: Confirmar que NO hay `.env` ni secretos trackeados**

```bash
cd "$OS_DIR"
echo "=== ¿algún .env trackeado? ==="; git ls-files | grep -iE '\.env' || echo "ninguno (bien)"
echo "=== patrones de secreto en ficheros trackeados ==="
git grep -nEi "(supabase_key|service_role|secret_key|api[_-]?key|password|bearer|ghp_|sk-)[\"'[:space:]]*[:=]" -- . ':(exclude)docs/*' ':(exclude)*.md' || echo "sin coincidencias en código/config (bien)"
echo "=== sanity: connections.md solo nombra variables, no valores ==="
grep -nE "SUPABASE|KEY" connections.md | head
```
Expected: ningún `.env` trackeado; sin valores de secreto reales (solo NOMBRES de variables en connections.md/specs). Si aparece un valor real, PARAR y limpiarlo antes de continuar.

- [ ] **Step 2: Revisar que `.gitignore` cubre lo sensible/pesado**

```bash
cd "$OS_DIR" && cat .gitignore
```
Expected: incluye `.venv/`, `__pycache__/`, `*.pyc`. (No hay `.env` en este repo; vive en Petramora.)

---

## Task 1: Crear repo privado + push

**Files:** ninguno (operación git/gh)

- [ ] **Step 1: Confirmar gh autenticado**

```bash
gh auth status 2>&1 | head -3
```
Expected: autenticado como `ericlb12` con scope repo.

- [ ] **Step 2: Crear el repo privado y pushear el repo existente**

```bash
cd "$OS_DIR"
git branch --show-current   # confirmar rama (master)
gh repo create ericlb12/claude-code-os --private --source=. --remote=origin --push
```
Expected: crea `github.com/ericlb12/claude-code-os` (privado) y sube `master`. Si el remote `origin` ya existe, usar `git push -u origin master` en su lugar.

- [ ] **Step 3: Verificar**

```bash
gh repo view ericlb12/claude-code-os --json visibility,nameWithOwner,defaultBranchRef -q '{vis: .visibility, repo: .nameWithOwner, branch: .defaultBranchRef.name}'
```
Expected: `vis: PRIVATE`, repo correcto, branch `master`.

---

## Task 2: Workflow `qa-nightly.yml`

**Files:** Create `$OS_DIR/.github/workflows/qa-nightly.yml`

- [ ] **Step 1: Escribir el workflow**

```yaml
name: QA nightly (Petramora)

on:
  schedule:
    - cron: "0 1 * * *"      # 01:00 UTC ≈ 03:00 Madrid (CEST). GH cron es UTC y aproximado.
  workflow_dispatch: {}        # permite lanzarlo a mano

permissions:
  contents: write              # para commitear el informe de vuelta

jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run QA report
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OS_DIR: ${{ github.workspace }}
        run: python -m qa.cron --target petramora --since 24h
      - name: Commit report
        run: |
          git config user.name "qa-bot"
          git config user.email "qa-bot@users.noreply.github.com"
          git add qa-reports/
          git commit -m "chore: QA nightly $(date -u +%F)" || echo "sin cambios que commitear"
          git push
```

- [ ] **Step 2: Commit y push del workflow**

```bash
cd "$OS_DIR"
git -c user.name="Eric" -c user.email="comercial@likeik.com" add .github/workflows/qa-nightly.yml
git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: workflow GitHub Actions QA nocturno"
git push
```

---

## Task 3: Configurar los secrets de Supabase

**Files:** ninguno (gh secret). REQUIERE los valores reales (están en el `.env` de Petramora).

- [ ] **Step 1: Leer los valores del `.env` de Petramora y ponerlos como secrets**

```bash
ENV="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
SUPABASE_URL=$(grep -E '^SUPABASE_URL=' "$ENV" | head -1 | cut -d= -f2- | tr -d '"'"'"' ')
SUPABASE_KEY=$(grep -E '^SUPABASE_KEY=' "$ENV" | head -1 | cut -d= -f2- | tr -d '"'"'"' ')
[ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_KEY" ] && echo "leídos OK (no se imprimen)" || echo "FALTAN valores en .env"
gh secret set SUPABASE_URL --repo ericlb12/claude-code-os --body "$SUPABASE_URL"
gh secret set SUPABASE_KEY --repo ericlb12/claude-code-os --body "$SUPABASE_KEY"
```
Expected: `gh secret set` confirma ambos. NO imprimir los valores. (Si Eric prefiere, los pone él en GitHub → Settings → Secrets.)

- [ ] **Step 2: Verificar que existen (sin ver valores)**

```bash
gh secret list --repo ericlb12/claude-code-os
```
Expected: lista `SUPABASE_URL` y `SUPABASE_KEY`.

---

## Task 4: Validar con run manual (workflow_dispatch)

**Files:** ninguno (validación)

- [ ] **Step 1: Lanzar el workflow a mano**

```bash
gh workflow run "QA nightly (Petramora)" --repo ericlb12/claude-code-os
sleep 5
gh run list --repo ericlb12/claude-code-os --workflow "QA nightly (Petramora)" --limit 1
```
Expected: aparece un run en estado queued/in_progress.

- [ ] **Step 2: Esperar y ver el resultado**

```bash
RUN_ID=$(gh run list --repo ericlb12/claude-code-os --workflow "QA nightly (Petramora)" --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN_ID" --repo ericlb12/claude-code-os --exit-status; echo "exit=$?"
```
Expected: el run termina con éxito (exit 0). Si falla, `gh run view "$RUN_ID" --log-failed` para ver el motivo (lo más probable: secret mal puesto o dep faltante).

- [ ] **Step 3: Confirmar que el informe se commiteó al repo**

```bash
gh api repos/ericlb12/claude-code-os/commits --jq '.[0].commit.message' | head -1
gh api "repos/ericlb12/claude-code-os/contents/qa-reports/petramora" --jq '.[].name' 2>&1 | tail -5
```
Expected: el último commit es del `qa-bot` ("chore: QA nightly ...") y existe el `.md` del día en `qa-reports/petramora/`.

> Checkpoint de Eric: confirmar en GitHub que el informe se ve. El `schedule` ya queda activo para las noches siguientes.

---

## Task 5: Desinstalar el cron local (evitar doble informe)

**Files:** ninguno (crontab del usuario). Solo tras validar Task 4.

- [ ] **Step 1: Quitar la línea nightly del crontab local**

```bash
( crontab -l 2>/dev/null | grep -v 'nightly.sh' ) | crontab -
echo "=== crontab tras limpieza ==="; crontab -l 2>/dev/null || echo "(crontab vacío)"
```
Expected: ya no aparece la línea `nightly.sh`. (El script `scripts/nightly.sh` se queda en el repo por si quieres correrlo a mano; solo se quita la programación local.)

- [ ] **Step 2: Anotar en connections.md / memoria** que el QA nocturno ahora corre en GitHub Actions (no en cron local). Commit:

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -aqm "docs: QA nocturno migrado a GitHub Actions (cron local retirado)" 2>/dev/null; git push 2>/dev/null || true
```

---

## Self-Review (hecho al escribir el plan)
- **Cobertura del spec:** secret-scan→Task0; repo privado+push→Task1; workflow→Task2; secrets→Task3; validación workflow_dispatch + commit del informe→Task4; retirar cron local→Task5. ✅
- **Placeholders:** ninguno; los valores de Supabase se leen del `.env` real en Task3 (no hardcodeados). El nombre del repo `ericlb12/claude-code-os` es fijo y consistente en todas las tasks. ✅
- **Consistencia:** `OS_DIR=github.workspace`, `python -m qa.cron --target petramora`, secrets `SUPABASE_URL`/`SUPABASE_KEY`, repo `ericlb12/claude-code-os` — idénticos en spec, workflow y comandos gh. `qa.cron` ya acepta OS_DIR por env (no requiere cambios). ✅
- **Seguridad:** Task0 bloquea push si hay secretos; repo privado; secrets cifrados; valores nunca impresos. ✅
- **Dependencias de Eric:** crear el repo (outward, privado) y meter las claves de prod del cliente como secrets — ambos autorizados por Eric en el brainstorming.
```
