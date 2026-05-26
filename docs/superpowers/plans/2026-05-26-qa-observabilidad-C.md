# QA Observabilidad — Sub-proyecto C — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatizar la ejecución nocturna de A: un cron WSL lanza `scripts/nightly.sh` → `python -m qa.cron --target petramora`, que reúsa el pipeline de A, escribe el informe del día y añade una línea de resumen (ok/FAIL) a `cron.log`. No toca B, no abre PRs.

**Architecture:** Refactor menor de `qa/report.py` para extraer `gather(cfg, since)` (reusable). Nuevo `qa/cron.py` con `nightly(...)` (gather/run_report inyectables → testeable sin red) + CLI. Wrapper fino `scripts/nightly.sh` para cron (carga .env, venv, trap FAIL).

**Tech Stack:** Python 3.12, pytest, bash, cron (WSL). venv nativo WSL.

> **Setup (una vez por shell):**
> ```bash
> export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
> PY=~/.venvs/claude_code_os/bin/python   # venv NATIVO WSL (NO crear venv en Dropbox)
> ```
> Tests en `tests/qa/` SIN `__init__.py`; `conftest.py` ya en la raíz.

---

## File Structure

- `$OS_DIR/qa/report.py` — MODIFICAR: extraer `gather(cfg, since)` de `main`
- `$OS_DIR/qa/cron.py` — NUEVO: `nightly(...)` + `main` + `__main__`
- `$OS_DIR/scripts/nightly.sh` — NUEVO: wrapper de cron
- `$OS_DIR/RECON_C.md` — NUEVO: hallazgos del recon (Task 0)
- `$OS_DIR/tests/qa/test_cron.py` — NUEVO: tests de `nightly`
- `$OS_DIR/tests/qa/test_report_gather.py` — NUEVO: test de `gather`

Contexto de A (ya existe, NO reescribir):
- `qa/report.py` tiene `render_markdown(...)`, `run_report(target, since, interactions, sources_ok, sources_failed, out_dir) -> path`, y `main(argv)` que hace el fetch inline de `langfuse`/`supabase`.
- `qa/config.py`: `load_target(path)`, `target_path(os_dir, target)`, `TargetConfig{name, default_since, langfuse, supabase}`.
- `qa/sources/langfuse.py` y `qa/sources/supabase.py`: `fetch_interactions(cfg_section, since) -> list[Interaction]`.
- `qa/group.py`: `group_findings(findings) -> list[ErrorGroup]`. `qa/detect.py`: `detect_errors(interactions) -> list[ErrorFinding]`.

---

## Task 0: Recon — estado de cron en WSL

Solo lectura + escribir RECON_C.md.

**Files:** Create `$OS_DIR/RECON_C.md`

- [ ] **Step 1: Comprobar disponibilidad y estado de cron**

```bash
which cron crontab 2>&1
service cron status 2>&1 | head -5 || true
cat /etc/wsl.conf 2>/dev/null || echo "no /etc/wsl.conf"
crontab -l 2>&1 | head -5 || true
```
Expected: si `cron`/`crontab` existen y el servicio está `running` o `stopped`. Anotar: ¿está instalado cron? ¿el servicio arranca? ¿hay `[boot] command` en `/etc/wsl.conf` para auto-arrancar cron? ¿hay crontab del usuario ya?

- [ ] **Step 2: Documentar cómo habilitar cron en WSL (si hace falta)**

Anotar en RECON_C.md las opciones reales según lo visto: (a) `sudo service cron start` manual; (b) auto-arranque vía `/etc/wsl.conf` con `[boot]\ncommand = service cron start`; (c) si no hay cron instalado, `sudo apt install cron` (requiere sudo con password — marcar como acción de Eric). Incluir la realidad LOCAL (PC/WSL encendido a las 03:00).

- [ ] **Step 3: Escribir `RECON_C.md`** con: cron instalado sí/no, servicio activo sí/no, método de auto-arranque recomendado, y si se requiere acción manual de Eric (sudo). Sin inventar.

- [ ] **Step 4: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add RECON_C.md && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: recon estado cron en WSL (Sub-proyecto C)"
```

> **Checkpoint:** si cron no está instalado o requiere sudo, anotarlo; el cron real lo activa Eric. El resto del plan (código + script) no depende de tener cron corriendo ya.

---

## Task 1: Refactor — extraer `gather` en `qa/report.py`

Hoy `main` hace el fetch de fuentes inline. Lo extraemos a `gather(cfg, since)` para reusar en C, sin cambiar el comportamiento externo de A.

**Files:** Modify `$OS_DIR/qa/report.py`; Create `$OS_DIR/tests/qa/test_report_gather.py`

- [ ] **Step 1: Escribir el test que falla** — `$OS_DIR/tests/qa/test_report_gather.py`

```python
from qa.config import TargetConfig
from qa.report import gather

def _cfg():
    return TargetConfig(
        name="t", default_since="24h",
        langfuse={"enabled": False},
        supabase={"enabled": False},
    )

def test_gather_disabled_sources_yield_empty():
    interactions, ok, failed = gather(_cfg(), "24h")
    assert interactions == []
    assert ok == []          # ninguna fuente habilitada
    assert failed == []      # ninguna falló (estaban deshabilitadas)
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_report_gather.py -v`
Expected: FAIL (`ImportError: cannot import name 'gather'`).

- [ ] **Step 3: Refactor en `$OS_DIR/qa/report.py`**

Añadir la función `gather` (arriba, junto a las demás) con esta firma exacta, moviendo a ella el bucle de fuentes que hoy vive en `main`:

```python
def gather(cfg, since):
    """Reúne interacciones de las fuentes habilitadas del target.
    Devuelve (interactions, sources_ok, sources_failed). Una fuente caída
    no aborta: se registra en sources_failed."""
    from qa.model import Interaction
    from qa.sources import langfuse as lf
    from qa.sources import supabase as sb
    interactions: list[Interaction] = []
    ok: list[str] = []
    failed: list[str] = []
    for name, mod, sect in (("langfuse", lf, cfg.langfuse), ("supabase", sb, cfg.supabase)):
        try:
            got = mod.fetch_interactions(sect, since)
            interactions.extend(got)
            if sect.get("enabled"):
                ok.append(name)
        except Exception as e:
            failed.append(f"{name} ({type(e).__name__})")
    return interactions, ok, failed
```

Y en `main`, sustituir el bucle inline equivalente por:
```python
    interactions, ok, failed = gather(cfg, since)
```
(El resto de `main` —argparse, `run_report`, el print— queda igual.)

- [ ] **Step 4: Correr y ver pasar (test nuevo + suite completa)**

Run: `cd "$OS_DIR" && $PY -m pytest -q`
Expected: PASS — el test de `gather` y toda la suite existente (A+B) siguen verdes.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/report.py tests/qa/test_report_gather.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "refactor: extraer qa.report.gather (reusable por cron)"
```

---

## Task 2: `qa/cron.py` — nightly() con gather/run_report inyectables

**Files:** Create `$OS_DIR/qa/cron.py`, `$OS_DIR/tests/qa/test_cron.py`

- [ ] **Step 1: Escribir el test que falla** — `$OS_DIR/tests/qa/test_cron.py`

```python
import os
from qa.model import Interaction, ToolCall
from qa.cron import nightly

def _interactions():
    return [
        Interaction(id="1", timestamp="t", source="supabase", user_input="x",
                    agent_output="", tool_calls=[], execution_error="boom",
                    latency_ms=1, raw={}),
    ]

def _gather_ok(cfg, since):
    return _interactions(), ["supabase"], []

def _gather_boom(cfg, since):
    raise RuntimeError("sin credenciales")

class _Cfg:
    name = "petramora"; default_since = "24h"
    langfuse = {"enabled": False}; supabase = {"enabled": True}

def test_nightly_writes_report_and_ok_log(tmp_path, monkeypatch):
    monkeypatch.setenv("OS_DIR", str(tmp_path))
    # config fake: evitamos load_target real inyectando loader
    path = nightly(os_dir=str(tmp_path), target="petramora", since="24h",
                   load=lambda od, t: _Cfg(), gather=_gather_ok)
    assert os.path.isfile(path)                                  # informe escrito
    log = open(os.path.join(str(tmp_path), "qa-reports", "petramora", "cron.log")).read()
    assert "| ok |" in log
    assert "interacciones=1" in log
    assert "grupos_error=1" in log     # un execution_error -> un grupo

def test_nightly_logs_fail_on_gather_error(tmp_path):
    nightly(os_dir=str(tmp_path), target="petramora", since="24h",
            load=lambda od, t: _Cfg(), gather=_gather_boom)
    log = open(os.path.join(str(tmp_path), "qa-reports", "petramora", "cron.log")).read()
    assert "| FAIL |" in log
    assert "sin credenciales" in log
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_cron.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'qa.cron'`).

- [ ] **Step 3: Implementar `$OS_DIR/qa/cron.py`**

```python
import os
from datetime import datetime, timezone

from qa.detect import detect_errors
from qa.group import group_findings
from qa.report import gather as _real_gather, run_report as _real_run_report
from qa.config import load_target, target_path


def _default_load(os_dir, target):
    return load_target(target_path(os_dir, target))


def _log_line(log_path: str, line: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def nightly(os_dir: str, target: str, since: str = "24h",
            load=_default_load, gather=_real_gather, run_report=_real_run_report) -> str | None:
    """Corre A una vez: informe + línea en cron.log. Devuelve la ruta del informe
    (o None si falló). `load`/`gather`/`run_report` son inyectables para tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out_dir = os.path.join(os_dir, "qa-reports")
    log_path = os.path.join(out_dir, target, "cron.log")
    try:
        cfg = load(os_dir, target)
        interactions, ok, failed = gather(cfg, since)
        path = run_report(target=target, since=since, interactions=interactions,
                          sources_ok=ok, sources_failed=failed, out_dir=out_dir)
        n_groups = len(group_findings(detect_errors(interactions)))
        rel = os.path.relpath(path, os_dir)
        _log_line(log_path,
                  f"{ts} | ok | interacciones={len(interactions)} | "
                  f"grupos_error={n_groups} | informe={rel}")
        return path
    except Exception as e:
        _log_line(log_path, f"{ts} | FAIL | {type(e).__name__}: {e}")
        return None


def main(argv=None):
    import argparse
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    p = argparse.ArgumentParser(description="QA cron nocturno (corre A)")
    p.add_argument("--target", required=True)
    p.add_argument("--since", default="24h")
    args = p.parse_args(argv)
    path = nightly(os_dir=os_dir, target=args.target, since=args.since)
    print(f"nightly: {'ok ' + path if path else 'FAIL (ver cron.log)'}")
    return path


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Crear `$OS_DIR/qa/cron.py` como módulo ejecutable** — ya incluye `if __name__ == "__main__"`, así que `python -m qa.cron` funciona sin `__main__.py` aparte. Verificar:

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_cron.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Correr la suite completa**

Run: `cd "$OS_DIR" && $PY -m pytest -q`
Expected: PASS — toda la suite (A+B+C) verde.

- [ ] **Step 6: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/cron.py tests/qa/test_cron.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.cron.nightly (corre A + cron.log ok/FAIL)"
```

---

## Task 3: `scripts/nightly.sh` — wrapper de cron

**Files:** Create `$OS_DIR/scripts/nightly.sh`

- [ ] **Step 1: Escribir el wrapper**

`$OS_DIR/scripts/nightly.sh`:
```bash
#!/bin/bash
# Wrapper de cron para el run nocturno de QA (Sub-proyecto C).
# Corre A sobre Petramora y registra en cron.log. NO toca B / no abre PRs.
set -uo pipefail

OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV_FILE="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
PY="$HOME/.venvs/claude_code_os/bin/python"
TARGET="petramora"
LOG="$OS_DIR/qa-reports/$TARGET/cron.log"

export OS_DIR

mkdir -p "$OS_DIR/qa-reports/$TARGET"

ts() { date -u +%Y-%m-%dT%H:%MZ; }

# trap: si algo peta antes de que qa.cron escriba su propia línea, dejamos rastro
trap 'echo "$(ts) | FAIL | nightly.sh aborto (codigo $?)" >> "$LOG"' ERR

if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
else
  echo "$(ts) | FAIL | no se encontro .env en $ENV_FILE" >> "$LOG"
  exit 1
fi

"$PY" -m qa.cron --target "$TARGET" --since 24h
```

- [ ] **Step 2: Hacerlo ejecutable y smoke (a mano, con credenciales)**

```bash
chmod +x "$OS_DIR/scripts/nightly.sh"
bash "$OS_DIR/scripts/nightly.sh"
tail -2 "$OS_DIR/qa-reports/petramora/cron.log"
```
Expected: imprime `nightly: ok ...` y la última línea del `cron.log` es `... | ok | interacciones=.. | grupos_error=.. | informe=...`. (Si las credenciales no se cargan, debe quedar una línea `FAIL`.)

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add scripts/nightly.sh && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: scripts/nightly.sh (wrapper cron para qa.cron)"
```

---

## Task 4: Documentar instalación del cron + smoke final

**Files:** Create `$OS_DIR/scripts/README.md`

- [ ] **Step 1: Escribir `$OS_DIR/scripts/README.md`** con instrucciones reales (usar lo confirmado en RECON_C.md)

```markdown
# Cron nocturno QA (Sub-proyecto C)

`nightly.sh` corre A (informe de errores) sobre Petramora cada noche y registra en
`qa-reports/petramora/cron.log`. NO toca B ni abre PRs.

## Activar cron en WSL
1. (Si no está) instalar: `sudo apt install cron`.
2. Arrancar el servicio: `sudo service cron start`.
3. Auto-arranque al abrir WSL — añadir a `/etc/wsl.conf`:
   ```
   [boot]
   command = service cron start
   ```

## Instalar la tarea (crontab del usuario)
`crontab -e` y añadir (corre a las 03:00; el PC/WSL debe estar encendido):
```
0 3 * * * /bin/bash "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/scripts/nightly.sh" >> "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/qa-reports/petramora/cron.boot.log" 2>&1
```

## Realidad LOCAL
Es un cron local: si el equipo o WSL están apagados a las 03:00, esa noche no corre.
Encaja con un futuro Mac mini 24/7. Revisa `cron.log` para ver qué noches corrió.

## Ejecutar a mano
```bash
bash "<...>/claude_code_os/scripts/nightly.sh"
```
```

- [ ] **Step 2: Smoke final + verificación de la suite**

```bash
cd "$OS_DIR" && ~/.venvs/claude_code_os/bin/python -m pytest -q
tail -3 "$OS_DIR/qa-reports/petramora/cron.log"
```
Expected: suite verde; el `cron.log` muestra las líneas de los smokes (al menos un `ok`).

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add scripts/README.md qa-reports && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: README instalacion cron + smoke nocturno"
```

> La instalación REAL del crontab y el `sudo service cron start` los hace Eric (requieren su decisión y, el apt/servicio, sudo con password). El plan deja todo listo y documentado.

---

## Self-Review (hecho al escribir el plan)

- **Cobertura del spec:** refactor `gather`→Task1; `qa/cron.py` nightly (informe +
  cron.log ok/FAIL)→Task2; `scripts/nightly.sh` (env, venv, trap FAIL)→Task3; recon
  estado cron WSL→Task0; línea de crontab + cómo activar cron documentado→Task4;
  realidad LOCAL→Task0/Task4; tests con gather/run_report inyectables→Task2; suite
  verde tras refactor→Task1/Task2. ✅
- **Placeholders:** ninguno; los comandos de RECON alimentan Task4 (README) con
  valores reales, marcado explícito. ✅
- **Consistencia de tipos/firmas:** `gather(cfg, since) -> (interactions, ok, failed)`
  igual en report (Task1), cron (Task2) y sus tests; `run_report(target, since,
  interactions, sources_ok, sources_failed, out_dir)` coincide con la firma real de A;
  `nightly(os_dir, target, since, load=, gather=, run_report=)` coherente entre impl y
  tests; formato de `cron.log` (`| ok | interacciones= | grupos_error= | informe=`)
  idéntico en impl y aserciones de test. ✅
