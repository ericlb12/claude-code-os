# QA Observabilidad — Sub-proyecto B — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el paquete `qa/autofix/` que selecciona errores `execution_error` reproducibles del informe de A, los reproduce como caso de eval (`sin_error`), y lanza un agente `claude -p` headless que reproduce en rojo, intenta el fix (verde) y abre un PR en Petramora — con guardarraíles y modo degradado.

**Architecture:** Núcleo puro (`select`, `repro`, `prompt`) testeable con fixtures; `runner` con el ejecutor de procesos **inyectado** para testear con un fake (sin lanzar agente real); `cli` orquesta select→fetch(Supabase)→repro→runner. Reusa `qa.model`, `qa.config`, `qa.sources.supabase` de A.

**Tech Stack:** Python 3.12, pytest, `claude` CLI (headless `-p`), `gh` CLI, git. venv nativo WSL.

> **Setup (una vez por shell):**
> ```bash
> export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
> PY=~/.venvs/claude_code_os/bin/python   # venv NATIVO WSL (NO crear venv en Dropbox)
> ```
> Tests en `tests/qa/` SIN `__init__.py`; `conftest.py` ya en la raíz.

---

## File Structure

- `$OS_DIR/qa/autofix/__init__.py` — paquete
- `$OS_DIR/qa/autofix/select.py` — filtra candidatos reproducibles (`execution_error`)
- `$OS_DIR/qa/autofix/repro.py` — construye el caso de eval reproductor
- `$OS_DIR/qa/autofix/prompt.py` — texto del prompt para el agente headless (con guardarraíles)
- `$OS_DIR/qa/autofix/runner.py` — `FixResult` + `run_fix` con ejecutor inyectable
- `$OS_DIR/qa/autofix/cli.py` — `python3 -m qa.autofix ...`
- `$OS_DIR/qa/autofix/__main__.py` — entry point que llama a `cli.main`
- `$OS_DIR/RECON_B.md` — hallazgos del recon (Task 0)
- `$OS_DIR/tests/qa/test_autofix_*.py` — tests

Nota de seguridad: el `runner` invoca el agente con `subprocess.run([...])` en forma
de **lista** (sin `shell=True`), por lo que no hay riesgo de inyección de shell.

---

## Task 0: Recon de feasibility (claude headless, gh, datos)

Solo lectura + escribir RECON_B.md.

**Files:** Create `$OS_DIR/RECON_B.md`

- [ ] **Step 1: Confirmar el CLI claude headless y gh**

```bash
which claude gh
claude --version 2>&1 | head -1
gh auth status 2>&1 | head -5
gh repo view ericlb12/Petramora_source --json nameWithOwner,defaultBranchRef 2>&1 | head -5
```
Expected: rutas de `claude` y `gh`; versión de claude; `gh auth status` autenticado; el repo accesible y su rama por defecto. Si `claude -p` headless no está disponible o `gh` no está autenticado, anotarlo como hallazgo crítico.

- [ ] **Step 2: Confirmar execution_errors reproducibles en agent_logs**

```bash
ENV="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
cd "$OS_DIR"; set -a; source "$ENV" 2>/dev/null; set +a
~/.venvs/claude_code_os/bin/python - <<'PY'
import os
from supabase import create_client
c = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
rows = c.table("agent_logs").select("id,user_message,error,model_used,timestamp").not_.is_("error","null").order("timestamp",desc=True).limit(10).execute().data
for r in rows:
    um = (r.get("user_message") or "")[:80]
    print(r["id"], "|", repr(r.get("error"))[:60], "| input:", repr(um))
PY
```
Expected: filas con `error` no nulo y su `user_message`. Anotar: ¿los `execution_error` traen `user_message` reproducible? ¿hay un campo que indique el `modo`/agente (p.ej. `model_used` u otro)? Si no hay forma de saber el modo, anotarlo (el repro usará un modo por defecto o lo inferirá del input).

- [ ] **Step 3: Confirmar el formato del dataset de evals y el check sin_error**

```bash
WT="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/.worktrees/feature-agent-evals/Agente_segmentador"
head -2 "$WT/evals/datasets/comercial.jsonl"
grep -rin "sin_error" "$WT/evals/" | head
```
Expected: la forma real de un caso JSON en el `.jsonl` (campos `input`, `checks`/`tipo`, `modo`...) y cómo se expresa el check `sin_error`. Anotar el esquema EXACTO para que `repro.py` lo genere idéntico.

- [ ] **Step 4: Escribir `RECON_B.md`** con valores reales: claude headless ok?, gh auth ok? + repo/rama, ejemplos de execution_error con input, esquema EXACTO del caso de eval y del check sin_error, cómo se determina el modo. Huecos explícitos.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add RECON_B.md && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: recon feasibility Sub-proyecto B (claude headless, gh, esquema eval)"
```

> **Checkpoint del controlador:** leer `RECON_B.md`. Si `claude -p` o `gh` no están listos, escalar a Eric. El esquema real del caso de eval (Step 3) alimenta Task 3 (`repro.py`).

---

## Task 1: Scaffold del paquete autofix

**Files:** Create `$OS_DIR/qa/autofix/__init__.py`

- [ ] **Step 1: Crear el paquete**

```bash
cd "$OS_DIR" && mkdir -p qa/autofix && touch qa/autofix/__init__.py
```

- [ ] **Step 2: Verificar import**

Run: `cd "$OS_DIR" && $PY -c "import qa.autofix; print('ok')"`
Expected: imprime `ok`.

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/__init__.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "chore: scaffold paquete qa.autofix"
```

---

## Task 2: `select.py` — candidatos reproducibles

**Files:** Create `$OS_DIR/qa/autofix/select.py`, `$OS_DIR/tests/qa/test_autofix_select.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_autofix_select.py`

```python
from qa.model import ErrorFinding
from qa.autofix.select import reproducible_interaction_ids

def _f(itype, iid):
    return ErrorFinding(interaction_id=iid, error_type=itype, signal="s", severity="high", excerpt="x")

def test_picks_only_execution_errors():
    findings = [_f("execution_error", "1"), _f("timeout", "2"),
                _f("execution_error", "1"), _f("explicit_error", "3")]
    ids = reproducible_interaction_ids(findings)
    assert ids == ["1"]   # dedup, solo execution_error, orden de aparición

def test_empty():
    assert reproducible_interaction_ids([]) == []
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_select.py -v`
Expected: FAIL (ModuleNotFoundError qa.autofix.select).

- [ ] **Step 3: Implementar `$OS_DIR/qa/autofix/select.py`**

```python
from qa.model import ErrorFinding

REPRODUCIBLE_TYPES = {"execution_error"}


def reproducible_interaction_ids(findings: list[ErrorFinding]) -> list[str]:
    """IDs de interacción con un error reproducible (execution_error), sin duplicar,
    en orden de aparición."""
    seen: list[str] = []
    for f in findings:
        if f.error_type in REPRODUCIBLE_TYPES and f.interaction_id not in seen:
            seen.append(f.interaction_id)
    return seen
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_select.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/select.py tests/qa/test_autofix_select.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.autofix.select (candidatos execution_error)"
```

---

## Task 3: `repro.py` — caso de eval reproductor

> Ajustar el esquema del dict al formato REAL del dataset confirmado en RECON_B.md (Step 3). El test abajo usa el esquema base `{input, modo, checks:[{tipo:"sin_error"}]}`; si el real difiere, ajustar test e impl de forma coherente.

**Files:** Create `$OS_DIR/qa/autofix/repro.py`, `$OS_DIR/tests/qa/test_autofix_repro.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_autofix_repro.py`

```python
from qa.model import Interaction
from qa.autofix.repro import build_repro_case, ReproError

def _interaction(uin):
    return Interaction(id="42", timestamp="2026-05-26T01:00:00Z", source="supabase",
                       user_input=uin, agent_output="", tool_calls=[],
                       execution_error="Traceback boom", latency_ms=100, raw={})

def test_build_repro_case_shape():
    case = build_repro_case(_interaction("como va la cartera"), modo="comercial")
    assert case["input"] == "como va la cartera"
    assert case["modo"] == "comercial"
    assert {"tipo": "sin_error"} in case["checks"]
    assert "42" in case["origen"]   # trazabilidad al id original

def test_build_repro_case_rejects_empty_input():
    import pytest
    with pytest.raises(ReproError):
        build_repro_case(_interaction("   "), modo="comercial")
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_repro.py -v`
Expected: FAIL (ModuleNotFoundError qa.autofix.repro).

- [ ] **Step 3: Implementar `$OS_DIR/qa/autofix/repro.py`**

```python
from qa.model import Interaction


class ReproError(Exception):
    """No se puede construir un caso reproductor a partir de la interacción."""


def build_repro_case(interaction: Interaction, modo: str) -> dict:
    user_input = (interaction.user_input or "").strip()
    if not user_input:
        raise ReproError(f"interacción {interaction.id} sin user_input reproducible")
    return {
        "input": user_input,
        "modo": modo,
        "checks": [{"tipo": "sin_error"}],
        "origen": f"qa-autofix: reproduce execution_error de interacción {interaction.id}",
    }
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_repro.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/repro.py tests/qa/test_autofix_repro.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.autofix.repro (caso de eval sin_error)"
```

---

## Task 4: `prompt.py` — prompt del agente headless

**Files:** Create `$OS_DIR/qa/autofix/prompt.py`, `$OS_DIR/tests/qa/test_autofix_prompt.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_autofix_prompt.py`

```python
from qa.autofix.prompt import build_prompt

def test_prompt_includes_guardrails_and_case():
    case = {"input": "como va la cartera", "modo": "comercial",
            "checks": [{"tipo": "sin_error"}], "origen": "interaccion 42"}
    p = build_prompt(case, branch="qa-autofix/2026-05-26-exec-42", base="master")
    assert "qa-autofix/2026-05-26-exec-42" in p
    assert "nunca" in p.lower() and "master" in p.lower()
    assert "merge" in p.lower()
    assert "gh pr create" in p
    assert "como va la cartera" in p
    assert "sin_error" in p
    assert "rojo" in p.lower()
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_prompt.py -v`
Expected: FAIL (ModuleNotFoundError qa.autofix.prompt).

- [ ] **Step 3: Implementar `$OS_DIR/qa/autofix/prompt.py`**

```python
import json


def build_prompt(case: dict, branch: str, base: str) -> str:
    case_json = json.dumps(case, ensure_ascii=False)
    return f"""\
Eres un agente de fix automatico para el agente Petramora (Agente_segmentador).
Trabajas en el worktree de evals. Sigue EXACTAMENTE este flujo eval-driven y
respeta los guardarrailes. No te desvies.

GUARDARRAILES (innegociables):
- Crea y trabaja en la rama `{branch}` partiendo de `{base}`.
- NUNCA hagas commits, push ni merge sobre `master` ni `staging`. NUNCA mergees.
- Solo abres un Pull Request; la decision de mergear es de un humano.

CASO REPRODUCTOR (un execution_error real de produccion):
{case_json}

FLUJO:
1. `git checkout {base} && git checkout -b {branch}`.
2. Anade el caso reproductor al dataset del modo `{case['modo']}`
   (`evals/datasets/{case['modo']}.jsonl`), una linea JSON.
3. Corre los evals de ese modo y confirma que el caso falla (ROJO) por el
   execution_error esperado.
4. Diagnostica e implementa el fix MINIMO del bug en el codigo del agente.
5. Corre de nuevo los evals del modo y confirma VERDE (el caso pasa, sin romper
   otros casos del modo).
6. Commit en `{branch}` y abre PR con `gh pr create --base {base}` con un cuerpo
   que explique: error original, caso anadido, que cambiaste, resultado de evals.

MODO DEGRADADO: si tras un esfuerzo razonable NO consigues VERDE, NO fuerces un fix
falso. Haz commit solo del caso reproductor (ROJO) y abre el PR etiquetando en el
titulo y cuerpo que REQUIERE FIX HUMANO. Nunca afirmes verde si no lo es.

Al terminar, imprime en la ultima linea: `PR_URL=<url>` si abriste PR, o
`RESULT=failed` si no pudiste.
"""
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_prompt.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/prompt.py tests/qa/test_autofix_prompt.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.autofix.prompt (prompt headless con guardarrailes)"
```

---

## Task 5: `runner.py` — FixResult + run_fix con ejecutor inyectable

Seguridad: el ejecutor por defecto usa `subprocess.run([...])` en forma de lista
(sin `shell=True`) — sin riesgo de inyección de shell.

**Files:** Create `$OS_DIR/qa/autofix/runner.py`, `$OS_DIR/tests/qa/test_autofix_runner.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_autofix_runner.py`

```python
from qa.autofix.runner import run_fix, FixResult

CASE = {"input": "x", "modo": "comercial", "checks": [{"tipo": "sin_error"}], "origen": "i42"}

def test_dry_run_does_not_execute():
    calls = []
    def fake_exec(prompt, cwd):
        calls.append((prompt, cwd))
        return "PR_URL=http://nope"
    res = run_fix(CASE, branch="qa-autofix/x", base="master", worktree="/wt",
                  executor=fake_exec, dry_run=True)
    assert isinstance(res, FixResult)
    assert res.status == "dry_run"
    assert calls == []
    assert "sin_error" in res.detail

def test_opened_pr_parsed_from_output():
    def fake_exec(prompt, cwd):
        return "blah\nPR_URL=https://github.com/ericlb12/Petramora_source/pull/7\n"
    res = run_fix(CASE, branch="qa-autofix/x", base="master", worktree="/wt",
                  executor=fake_exec, dry_run=False)
    assert res.status == "opened_pr"
    assert res.pr_url.endswith("/pull/7")

def test_failed_when_no_pr_url():
    def fake_exec(prompt, cwd):
        return "RESULT=failed\n"
    res = run_fix(CASE, branch="qa-autofix/x", base="master", worktree="/wt",
                  executor=fake_exec, dry_run=False)
    assert res.status == "failed"
    assert res.pr_url is None
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_runner.py -v`
Expected: FAIL (ModuleNotFoundError qa.autofix.runner).

- [ ] **Step 3: Implementar `$OS_DIR/qa/autofix/runner.py`**

```python
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from qa.autofix.prompt import build_prompt

# executor: (prompt, cwd) -> stdout str
Executor = Callable[[str, str], str]


@dataclass
class FixResult:
    status: str                    # dry_run | opened_pr | failed
    pr_url: Optional[str] = None
    branch: Optional[str] = None
    detail: str = ""


def _default_executor(prompt: str, cwd: str) -> str:
    # Lista de args (sin shell=True): sin riesgo de inyeccion de shell.
    proc = subprocess.run(["claude", "-p", prompt], cwd=cwd,
                          capture_output=True, text=True, timeout=1800)
    return (proc.stdout or "") + "\n" + (proc.stderr or "")


def run_fix(case: dict, branch: str, base: str, worktree: str,
            executor: Executor = _default_executor, dry_run: bool = False) -> FixResult:
    prompt = build_prompt(case, branch=branch, base=base)
    if dry_run:
        return FixResult(status="dry_run", branch=branch, detail=prompt)
    out = executor(prompt, worktree)
    m = re.search(r"PR_URL=(\S+)", out or "")
    if m:
        return FixResult(status="opened_pr", pr_url=m.group(1), branch=branch,
                         detail=(out or "")[-2000:])
    return FixResult(status="failed", branch=branch, detail=(out or "")[-2000:])
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_runner.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/runner.py tests/qa/test_autofix_runner.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.autofix.runner (run_fix + FixResult, ejecutor inyectable)"
```

---

## Task 6: `cli.py` + `__main__.py` — orquestador

Une: re-fetch interacción por id (Supabase) → repro → runner. El test inyecta un
`fetch` fake y un `executor` fake (no toca red ni lanza agente).

**Files:** Create `$OS_DIR/qa/autofix/cli.py`, `$OS_DIR/qa/autofix/__main__.py`, `$OS_DIR/tests/qa/test_autofix_cli.py`; Modify `$OS_DIR/qa/sources/supabase.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_autofix_cli.py`

```python
from qa.model import Interaction
from qa.autofix.cli import autofix_interaction

def _fetch_ok(interaction_id):
    return Interaction(id=interaction_id, timestamp="t", source="supabase",
                       user_input="como va la cartera", agent_output="",
                       tool_calls=[], execution_error="boom", latency_ms=1, raw={})

def _exec_pr(prompt, cwd):
    return "PR_URL=https://github.com/ericlb12/Petramora_source/pull/9"

def test_autofix_interaction_happy_path():
    res = autofix_interaction(interaction_id="42", modo="comercial", base="master",
                              worktree="/wt", fetch=_fetch_ok, executor=_exec_pr,
                              dry_run=False)
    assert res.status == "opened_pr"
    assert res.branch.startswith("qa-autofix/")

def test_autofix_interaction_skips_unreproducible():
    def _fetch_empty(iid):
        return Interaction(id=iid, timestamp="t", source="supabase", user_input="  ",
                           agent_output="", tool_calls=[], execution_error="boom",
                           latency_ms=1, raw={})
    res = autofix_interaction(interaction_id="42", modo="comercial", base="master",
                              worktree="/wt", fetch=_fetch_empty, executor=_exec_pr,
                              dry_run=False)
    assert res.status == "failed"
    assert "reproducible" in res.detail
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_autofix_cli.py -v`
Expected: FAIL (ModuleNotFoundError qa.autofix.cli).

- [ ] **Step 3: Implementar `$OS_DIR/qa/autofix/cli.py`**

```python
import os
from datetime import datetime, timezone
from typing import Callable, Optional

from qa.model import Interaction
from qa.autofix.repro import build_repro_case, ReproError
from qa.autofix.runner import run_fix, FixResult, Executor


def _branch_for(interaction_id: str) -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"qa-autofix/{day}-exec-{interaction_id}"


def autofix_interaction(interaction_id: str, modo: str, base: str, worktree: str,
                        fetch: Callable[[str], Optional[Interaction]],
                        executor: Optional[Executor] = None,
                        dry_run: bool = False) -> FixResult:
    interaction = fetch(interaction_id)
    if interaction is None:
        return FixResult(status="failed", detail=f"interaccion {interaction_id} no encontrada")
    try:
        case = build_repro_case(interaction, modo=modo)
    except ReproError as e:
        return FixResult(status="failed", detail=f"no reproducible: {e}")
    branch = _branch_for(interaction_id)
    kwargs = dict(case=case, branch=branch, base=base, worktree=worktree, dry_run=dry_run)
    if executor is not None:
        kwargs["executor"] = executor
    return run_fix(**kwargs)


def main(argv=None):
    import argparse
    from qa.config import load_target, target_path
    from qa.sources import supabase as sb

    os_dir = os.environ.get("OS_DIR", os.getcwd())
    p = argparse.ArgumentParser(description="QA autofix — reproduce+fix+PR (headless)")
    p.add_argument("--target", required=True)
    p.add_argument("--interaction", required=True, help="id de la interaccion con execution_error")
    p.add_argument("--modo", required=True, help="modo del eval (comercial|financiero|...)")
    p.add_argument("--worktree", required=True, help="ruta del worktree de evals de Petramora")
    p.add_argument("--base", default="master")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    cfg = load_target(target_path(os_dir, args.target))

    def fetch(iid: str):
        rows = (sb._client(cfg.supabase).table(cfg.supabase["table"])
                .select("*").eq("id", iid).limit(1).execute().data)
        return sb.normalize_row(rows[0]) if rows else None

    res = autofix_interaction(args.interaction, args.modo, args.base, args.worktree,
                              fetch=fetch, dry_run=args.dry_run)
    print(f"status={res.status} branch={res.branch} pr={res.pr_url}")
    if res.status == "dry_run":
        print("---- PROMPT ----")
        print(res.detail)
    return res
```

- [ ] **Step 4: Crear `$OS_DIR/qa/autofix/__main__.py`**

```python
from qa.autofix.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Añadir helper `_client` a `qa/sources/supabase.py`** (refactor menor para reutilizar la creación de cliente)

En `$OS_DIR/qa/sources/supabase.py`, añadir tras los imports:
```python
def _client(cfg: dict):
    import os
    from supabase import create_client
    return create_client(os.environ[cfg["url_env"]], os.environ[cfg["key_env"]])
```
Y en `fetch_interactions`, sustituir las líneas `from supabase import create_client` + `client = create_client(os.environ[...], os.environ[...])` por:
```python
    client = _client(cfg)
```
(El resto de `fetch_interactions` igual.)

- [ ] **Step 6: Correr y ver pasar (suite completa)**

Run: `cd "$OS_DIR" && $PY -m pytest -q`
Expected: PASS — toda la suite (A + B) verde.

- [ ] **Step 7: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/autofix/cli.py qa/autofix/__main__.py qa/sources/supabase.py tests/qa/test_autofix_cli.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.autofix.cli orquestador + _client helper"
```

---

## Task 7: Smoke `--dry-run` contra un execution_error real

**Files:** ninguno (validación)

- [ ] **Step 1: Elegir un id real con execution_error**

Usar un id de los listados por A (p.ej. el `1301` del informe) o consultar Supabase. Determinar su `modo` (de RECON_B.md; si no hay campo de modo, usar `comercial` por defecto y anotarlo).

- [ ] **Step 2: Correr el CLI en dry-run**

```bash
export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
WT="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/.worktrees/feature-agent-evals/Agente_segmentador"
cd "$OS_DIR"; set -a; source "$ENV" 2>/dev/null; set +a
~/.venvs/claude_code_os/bin/python -m qa.autofix --target petramora --interaction 1301 --modo comercial --worktree "$WT" --dry-run
```
Expected: `status=dry_run branch=qa-autofix/<fecha>-exec-1301 ...` + el PROMPT impreso con el caso reproductor real (input del usuario) y los guardarraíles. Sin tocar el repo Petramora.

- [ ] **Step 3: Verificación de no-efecto**

```bash
PET="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora"
git -C "$PET" status --short
git -C "$PET" branch | grep qa-autofix || echo "sin ramas qa-autofix (correcto)"
```
Expected: el repo Petramora intacto, ninguna rama `qa-autofix` creada.

> El run REAL (sin `--dry-run`, que lanza `claude -p` y abre PR de verdad) NO se ejecuta como parte del plan automático: lo dispara Eric a mano cuando quiera probar el fix headless sobre un caso concreto, porque modifica el repo Petramora y abre un PR. Documentar este paso como manual.

---

## Self-Review (hecho al escribir el plan)

- **Cobertura del spec:** select (execution_error)→Task2; repro (sin_error)→Task3;
  prompt+guardarraíles→Task4; runner+FixResult+ejecutor inyectable+3 estados→Task5;
  cli orquestador (fetch→repro→runner) + skip no-reproducible→Task6; recon (claude
  headless, gh, esquema eval)→Task0; dry-run smoke + no-efecto→Task7; tests con fakes
  sin agente real→Tasks2-6. ✅
- **Placeholders:** el ajuste del esquema del caso de eval (Task3) es dependencia
  explícita de Task0 (RECON_B.md), no un TODO suelto. ✅
- **Consistencia de tipos:** `FixResult{status,pr_url,branch,detail}`, `Executor`,
  `run_fix`, `build_repro_case`/`ReproError`, `build_prompt`,
  `reproducible_interaction_ids`, `autofix_interaction`, `_client` — usados igual en
  todas las tasks. Estados `dry_run|opened_pr|failed` coherentes entre runner (Task5)
  y cli (Task6). ✅
- **Seguridad:** ejecutor por defecto con `subprocess.run([...])` en lista, sin
  `shell=True` — sin inyección. Guardarraíles del agente headless en el prompt
  (Task4) + dry-run + nunca master/merge. ✅
