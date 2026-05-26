# QA Observabilidad — Sub-proyecto A — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el paquete `qa/` en `claude_code_os` que ingiere trazas reales (Langfuse + Supabase) de un repo configurable, detecta errores con señales deterministas, y emite un informe markdown priorizado con histórico.

**Architecture:** Pipeline puro `config → sources → detect → group → report`. Los adapters de fuente normalizan a un contrato común (`Interaction`); la detección/agrupación/render son funciones puras testeables con fixtures sintéticas (sin API en vivo). Agnóstico del repo vía `qa/targets/<repo>.yaml`.

**Tech Stack:** Python 3.12, pytest, PyYAML, `requests` (Langfuse API), cliente Supabase/psycopg (según recon). venv dedicado del proyecto.

> **Setup (una vez por shell):**
> ```bash
> export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
> ```
> El intérprete del sistema es `python3` (no existe `python`). `pip` global bloqueado por PEP 668 → usar el venv del proyecto (Task 1 lo crea).

---

## File Structure

- `$OS_DIR/qa/__init__.py` — paquete
- `$OS_DIR/qa/model.py` — dataclasses `Interaction`, `ToolCall`, `ErrorFinding`
- `$OS_DIR/qa/detect.py` — señales deterministas → `ErrorFinding[]`
- `$OS_DIR/qa/group.py` — agrupa + prioriza
- `$OS_DIR/qa/report.py` — render markdown + CLI `python3 -m qa.report`
- `$OS_DIR/qa/config.py` — carga `qa/targets/<repo>.yaml`
- `$OS_DIR/qa/sources/__init__.py`
- `$OS_DIR/qa/sources/langfuse.py` — Langfuse API → `Interaction[]`
- `$OS_DIR/qa/sources/supabase.py` — Supabase SQL → `Interaction[]`
- `$OS_DIR/qa/targets/petramora.yaml` — config del target piloto
- `$OS_DIR/tests/qa/` — tests + fixtures
- `$OS_DIR/RECON_QA.md` — hallazgos del recon (Task 0)
- `$OS_DIR/requirements.txt` — deps
- `$OS_DIR/pytest.ini` — config pytest

---

## Task 0: Recon de feasibility de las fuentes

Sin datos reales, los adapters serían inventados. Solo lectura + escribir `RECON_QA.md`.

**Files:**
- Create: `$OS_DIR/RECON_QA.md`

- [ ] **Step 1: Localizar la config de Langfuse en el repo Petramora**

Run:
```bash
PET="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora"
grep -rin "langfuse" "$PET/Agente_segmentador" --include=*.py -l
grep -rin "LANGFUSE" "$PET/Agente_segmentador/.env" 2>/dev/null | sed 's/=.*/=<oculto>/'
```
Expected: ficheros que integran Langfuse + nombres de variables de entorno (host, public/secret key, project). Si NO aparece nada → Langfuse NO está integrado; anotarlo como hallazgo crítico.

- [ ] **Step 2: Identificar dónde quedan los logs de interacción en Supabase**

Run:
```bash
grep -rin "supabase\|insert\|log\|trace\|conversation\|interaccion" "$PET/Agente_segmentador" --include=*.py -l | head
grep -rin "SUPABASE" "$PET/Agente_segmentador/.env" 2>/dev/null | sed 's/=.*/=<oculto>/'
```
Expected: tabla(s) donde se guardan interacciones del agente y las credenciales Supabase. Anotar nombre de tabla y columnas si se ven en el código.

- [ ] **Step 3: Capturar el formato real de una traza**

A partir del código hallado, documentar la forma de una interacción: qué campos hay para input usuario, output agente, tools llamadas, errores, timestamp, latencia. Si hay acceso de lectura (claves en `.env`), opcionalmente traer 1 ejemplo real y anonimizarlo. Si NO hay acceso, dejar constancia y usar el shape del código.

- [ ] **Step 4: Escribir `RECON_QA.md`**

Volcar valores REALES: ¿Langfuse integrado? (sí/no + host/project + nombres de env vars), ¿tabla Supabase de interacciones? (nombre + columnas + env vars), shape de una interacción (campos por fuente), y qué librería cliente conviene (`requests` para Langfuse REST, `psycopg`/cliente `supabase-py` para Supabase). Si una fuente NO existe aún, decirlo explícitamente — es input para ajustar el alcance.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add RECON_QA.md && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "docs: recon feasibility fuentes QA (Langfuse + Supabase)"
```

> **Checkpoint del controlador:** tras Task 0, leer `RECON_QA.md`. Si una fuente no existe, decidir con Eric si A arranca solo con la que sí existe. Las Tasks 7-8 (adapters) usan estos valores reales.

---

## Task 1: Scaffolding del paquete y entorno

**Files:**
- Create: `$OS_DIR/qa/__init__.py`, `$OS_DIR/qa/sources/__init__.py`, `$OS_DIR/tests/qa/__init__.py`, `$OS_DIR/requirements.txt`, `$OS_DIR/pytest.ini`

- [ ] **Step 1: Crear venv e instalar deps**

```bash
cd "$OS_DIR" && python3 -m venv .venv && ./.venv/bin/pip install -q pytest pyyaml requests
printf "pytest\npyyaml\nrequests\n" > requirements.txt
```
Expected: venv creado, deps instaladas. (psycopg/supabase-py se añade en Task 8 según recon.)

- [ ] **Step 2: Crear estructura de paquete**

```bash
cd "$OS_DIR" && mkdir -p qa/sources qa/targets tests/qa && touch qa/__init__.py qa/sources/__init__.py tests/qa/__init__.py
```

- [ ] **Step 3: Crear `pytest.ini`**

Escribir `$OS_DIR/pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 4: Verificar que pytest colecta 0 tests sin error**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest -q`
Expected: "no tests ran" sin errores de colección.

- [ ] **Step 5: Añadir `.venv/` al .gitignore y commit**

```bash
cd "$OS_DIR" && grep -qx ".venv/" .gitignore || echo ".venv/" >> .gitignore
git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa tests pytest.ini requirements.txt .gitignore && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "chore: scaffold paquete qa + entorno pytest"
```

---

## Task 2: Modelo de datos (`qa/model.py`)

**Files:**
- Create: `$OS_DIR/qa/model.py`, `$OS_DIR/tests/qa/test_model.py`

- [ ] **Step 1: Escribir el test que falla**

`$OS_DIR/tests/qa/test_model.py`:
```python
from qa.model import Interaction, ToolCall, ErrorFinding

def test_interaction_minimal_construct():
    i = Interaction(
        id="t1", timestamp="2026-05-26T01:00:00Z", source="langfuse",
        user_input="hola", agent_output="respuesta",
        tool_calls=[ToolCall(name="get_x", ok=True, message=None)],
        execution_error=None, latency_ms=1200, raw={"k": "v"},
    )
    assert i.id == "t1"
    assert i.tool_calls[0].name == "get_x"
    assert i.has_tool_error() is False

def test_interaction_detects_tool_error():
    i = Interaction(
        id="t2", timestamp="2026-05-26T01:00:00Z", source="supabase",
        user_input="x", agent_output="", tool_calls=[ToolCall(name="q", ok=False, message="boom")],
        execution_error=None, latency_ms=None, raw={},
    )
    assert i.has_tool_error() is True

def test_error_finding_construct():
    e = ErrorFinding(interaction_id="t2", error_type="tool_error",
                     signal="tool_call.ok=False", severity="high", excerpt="boom")
    assert e.error_type == "tool_error"
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.model'`.

- [ ] **Step 3: Implementar `qa/model.py`**

```python
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ToolCall:
    name: str
    ok: bool
    message: Optional[str] = None


@dataclass
class Interaction:
    id: str
    timestamp: str            # ISO 8601 UTC
    source: str               # "langfuse" | "supabase"
    user_input: str
    agent_output: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    execution_error: Optional[str] = None
    latency_ms: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def has_tool_error(self) -> bool:
        return any(not tc.ok for tc in self.tool_calls)


@dataclass
class ErrorFinding:
    interaction_id: str
    error_type: str           # tool_error|execution_error|empty_output|timeout|explicit_error
    signal: str               # qué disparó la detección
    severity: str             # low|medium|high
    excerpt: str
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_model.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/model.py tests/qa/test_model.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.model (Interaction, ToolCall, ErrorFinding)"
```

---

## Task 3: Detección determinista (`qa/detect.py`)

**Files:**
- Create: `$OS_DIR/qa/detect.py`, `$OS_DIR/tests/qa/test_detect.py`

- [ ] **Step 1: Escribir el test que falla**

`$OS_DIR/tests/qa/test_detect.py`:
```python
from qa.model import Interaction, ToolCall
from qa.detect import detect_errors, TIMEOUT_MS

def _base(**kw):
    d = dict(id="i", timestamp="2026-05-26T01:00:00Z", source="langfuse",
             user_input="x", agent_output="ok", tool_calls=[],
             execution_error=None, latency_ms=100, raw={})
    d.update(kw)
    return Interaction(**d)

def test_tool_error_detected():
    i = _base(id="a", tool_calls=[ToolCall("q", ok=False, message="boom")])
    f = detect_errors([i])
    assert len(f) == 1 and f[0].error_type == "tool_error" and f[0].interaction_id == "a"

def test_execution_error_detected():
    f = detect_errors([_base(id="b", execution_error="Traceback ...")])
    assert any(x.error_type == "execution_error" for x in f)

def test_empty_output_detected():
    f = detect_errors([_base(id="c", agent_output="")])
    assert any(x.error_type == "empty_output" for x in f)

def test_timeout_detected():
    f = detect_errors([_base(id="d", latency_ms=TIMEOUT_MS + 1)])
    assert any(x.error_type == "timeout" for x in f)

def test_explicit_error_field_detected():
    f = detect_errors([_base(id="e", raw={"error": "rate_limit"})])
    assert any(x.error_type == "explicit_error" for x in f)

def test_clean_interaction_yields_nothing():
    assert detect_errors([_base(id="f")]) == []
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.detect'`.

- [ ] **Step 3: Implementar `qa/detect.py`**

```python
from qa.model import Interaction, ErrorFinding

TIMEOUT_MS = 30_000  # umbral de latencia considerada timeout


def detect_errors(interactions: list[Interaction]) -> list[ErrorFinding]:
    findings: list[ErrorFinding] = []
    for i in interactions:
        for tc in i.tool_calls:
            if not tc.ok:
                findings.append(ErrorFinding(
                    interaction_id=i.id, error_type="tool_error",
                    signal=f"tool_call[{tc.name}].ok=False", severity="high",
                    excerpt=(tc.message or "")[:300]))
        if i.execution_error:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="execution_error",
                signal="execution_error set", severity="high",
                excerpt=i.execution_error[:300]))
        if i.agent_output is not None and i.agent_output.strip() == "":
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="empty_output",
                signal="agent_output vacío", severity="medium", excerpt=""))
        if i.latency_ms is not None and i.latency_ms > TIMEOUT_MS:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="timeout",
                signal=f"latency_ms={i.latency_ms} > {TIMEOUT_MS}",
                severity="medium", excerpt=str(i.latency_ms)))
        err = i.raw.get("error") if isinstance(i.raw, dict) else None
        if err:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="explicit_error",
                signal="raw.error presente", severity="high",
                excerpt=str(err)[:300]))
    return findings
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_detect.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/detect.py tests/qa/test_detect.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.detect (5 señales deterministas)"
```

---

## Task 4: Agrupación y priorización (`qa/group.py`)

**Files:**
- Create: `$OS_DIR/qa/group.py`, `$OS_DIR/tests/qa/test_group.py`

- [ ] **Step 1: Escribir el test que falla**

`$OS_DIR/tests/qa/test_group.py`:
```python
from qa.model import ErrorFinding
from qa.group import group_findings, ErrorGroup

def _f(itype, sig, iid, sev="high"):
    return ErrorFinding(interaction_id=iid, error_type=itype, signal=sig, severity=sev, excerpt="")

def test_groups_by_type_and_signal():
    findings = [
        _f("tool_error", "tool_call[q].ok=False", "1"),
        _f("tool_error", "tool_call[q].ok=False", "2"),
        _f("timeout", "latency", "3", sev="medium"),
    ]
    groups = group_findings(findings)
    assert isinstance(groups[0], ErrorGroup)
    # el grupo más frecuente va primero
    assert groups[0].count == 2
    assert groups[0].error_type == "tool_error"
    assert set(groups[0].interaction_ids) == {"1", "2"}

def test_priority_high_before_medium_on_tie():
    findings = [_f("timeout", "l", "1", sev="medium"), _f("tool_error", "t", "2", sev="high")]
    groups = group_findings(findings)
    # ambos count=1; high severity primero
    assert groups[0].error_type == "tool_error"

def test_empty_input():
    assert group_findings([]) == []
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_group.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.group'`.

- [ ] **Step 3: Implementar `qa/group.py`**

```python
from dataclasses import dataclass, field
from qa.model import ErrorFinding

_SEV_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class ErrorGroup:
    error_type: str
    signal: str
    severity: str
    count: int
    interaction_ids: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


def group_findings(findings: list[ErrorFinding]) -> list[ErrorGroup]:
    buckets: dict[tuple[str, str], ErrorGroup] = {}
    for f in findings:
        key = (f.error_type, f.signal)
        g = buckets.get(key)
        if g is None:
            g = ErrorGroup(error_type=f.error_type, signal=f.signal,
                           severity=f.severity, count=0)
            buckets[key] = g
        g.count += 1
        g.interaction_ids.append(f.interaction_id)
        if f.excerpt and len(g.examples) < 2:
            g.examples.append(f.excerpt)
        if _SEV_RANK.get(f.severity, 0) > _SEV_RANK.get(g.severity, 0):
            g.severity = f.severity
    # prioridad: primero por count desc, luego por severidad desc
    return sorted(buckets.values(),
                  key=lambda g: (g.count, _SEV_RANK.get(g.severity, 0)),
                  reverse=True)
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_group.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/group.py tests/qa/test_group.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.group (agrupar + priorizar findings)"
```

---

## Task 5: Render del informe (`qa/report.py` — render puro)

**Files:**
- Create: `$OS_DIR/qa/report.py`, `$OS_DIR/tests/qa/test_report.py`

- [ ] **Step 1: Escribir el test que falla**

`$OS_DIR/tests/qa/test_report.py`:
```python
from qa.group import ErrorGroup
from qa.report import render_markdown

def test_render_includes_summary_and_groups():
    groups = [ErrorGroup(error_type="tool_error", signal="tool_call[q].ok=False",
                         severity="high", count=2, interaction_ids=["1", "2"],
                         examples=["boom"])]
    md = render_markdown(target="petramora", since="24h",
                         n_interactions=10, groups=groups,
                         sources_ok=["langfuse"], sources_failed=["supabase"])
    assert "# QA report — petramora" in md
    assert "24h" in md
    assert "10" in md                       # nº interacciones
    assert "tool_error" in md
    assert "x2" in md or "count: 2" in md    # frecuencia
    assert "supabase" in md                  # fuente fallida reportada

def test_render_no_errors():
    md = render_markdown(target="petramora", since="24h", n_interactions=5,
                         groups=[], sources_ok=["langfuse"], sources_failed=[])
    assert "Sin errores" in md
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.report'`.

- [ ] **Step 3: Implementar el render en `qa/report.py`**

```python
from qa.group import ErrorGroup


def render_markdown(target: str, since: str, n_interactions: int,
                    groups: list[ErrorGroup], sources_ok: list[str],
                    sources_failed: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"# QA report — {target}")
    lines.append("")
    lines.append(f"- Ventana: {since}")
    lines.append(f"- Interacciones analizadas: {n_interactions}")
    lines.append(f"- Grupos de error: {len(groups)}")
    lines.append(f"- Fuentes OK: {', '.join(sources_ok) or 'ninguna'}")
    if sources_failed:
        lines.append(f"- Fuentes con fallo: {', '.join(sources_failed)}")
    lines.append("")
    if not groups:
        lines.append("Sin errores detectados en la ventana. ✅")
        return "\n".join(lines) + "\n"
    lines.append("## Top errores (priorizados)")
    for g in groups:
        lines.append(f"### {g.error_type} · x{g.count} · sev={g.severity}")
        lines.append(f"- Señal: `{g.signal}`")
        lines.append(f"- Interacciones: {', '.join(g.interaction_ids[:10])}")
        for ex in g.examples:
            lines.append(f"  - ejemplo: {ex}")
        lines.append("")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_report.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/report.py tests/qa/test_report.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.report render markdown"
```

---

## Task 6: Config por target (`qa/config.py`)

**Files:**
- Create: `$OS_DIR/qa/config.py`, `$OS_DIR/qa/targets/petramora.yaml`, `$OS_DIR/tests/qa/test_config.py`, `$OS_DIR/tests/qa/fixtures/target_ok.yaml`

- [ ] **Step 1: Escribir el fixture YAML y el test que falla**

`$OS_DIR/tests/qa/fixtures/target_ok.yaml`:
```yaml
name: demo
default_since: 24h
langfuse:
  enabled: true
  host_env: LANGFUSE_HOST
  public_key_env: LANGFUSE_PUBLIC_KEY
  secret_key_env: LANGFUSE_SECRET_KEY
  project: demo-project
supabase:
  enabled: true
  url_env: SUPABASE_URL
  key_env: SUPABASE_KEY
  table: agent_interactions
```

`$OS_DIR/tests/qa/test_config.py`:
```python
import os
from qa.config import load_target, TargetConfig

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "target_ok.yaml")

def test_load_target_parses_fields():
    cfg = load_target(FIX)
    assert isinstance(cfg, TargetConfig)
    assert cfg.name == "demo"
    assert cfg.default_since == "24h"
    assert cfg.langfuse["enabled"] is True
    assert cfg.langfuse["project"] == "demo-project"
    assert cfg.supabase["table"] == "agent_interactions"

def test_load_missing_file_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_target("/no/existe.yaml")
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.config'`.

- [ ] **Step 3: Implementar `qa/config.py`**

```python
import os
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class TargetConfig:
    name: str
    default_since: str
    langfuse: dict[str, Any]
    supabase: dict[str, Any]


def load_target(path: str) -> TargetConfig:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return TargetConfig(
        name=data.get("name", ""),
        default_since=data.get("default_since", "24h"),
        langfuse=data.get("langfuse", {"enabled": False}),
        supabase=data.get("supabase", {"enabled": False}),
    )


def target_path(os_dir: str, target: str) -> str:
    return os.path.join(os_dir, "qa", "targets", f"{target}.yaml")
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_config.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Crear `qa/targets/petramora.yaml` con los valores REALES de RECON_QA.md**

Rellenar con lo confirmado en Task 0 (nombres de env vars, proyecto Langfuse, tabla Supabase). Si una fuente no existe aún, poner `enabled: false`. Ejemplo de forma (sustituir por valores reales):
```yaml
name: petramora
default_since: 24h
langfuse:
  enabled: true            # según RECON_QA.md
  host_env: LANGFUSE_HOST
  public_key_env: LANGFUSE_PUBLIC_KEY
  secret_key_env: LANGFUSE_SECRET_KEY
  project: <real>
supabase:
  enabled: true            # según RECON_QA.md
  url_env: SUPABASE_URL
  key_env: SUPABASE_KEY
  table: <real>
```

- [ ] **Step 6: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/config.py qa/targets/petramora.yaml tests/qa/test_config.py tests/qa/fixtures/target_ok.yaml && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.config + target petramora.yaml"
```

---

## Task 7: Adapter Langfuse (`qa/sources/langfuse.py`)

Usar los valores y el shape real de `RECON_QA.md`. El test NO llama a la API: prueba la función pura de normalización contra un payload de ejemplo.

**Files:**
- Create: `$OS_DIR/qa/sources/langfuse.py`, `$OS_DIR/tests/qa/test_langfuse.py`, `$OS_DIR/tests/qa/fixtures/langfuse_trace.json`

- [ ] **Step 1: Guardar un payload de ejemplo y escribir el test que falla**

`$OS_DIR/tests/qa/fixtures/langfuse_trace.json` — un trace de ejemplo con la forma documentada en RECON_QA.md. Forma mínima de partida (ajustar a la real):
```json
{
  "id": "trace-1",
  "timestamp": "2026-05-26T01:00:00Z",
  "input": {"user": "como va la cartera"},
  "output": {"text": "aqui tienes"},
  "observations": [{"name": "get_segment_distribution", "level": "DEFAULT"}],
  "latency": 1.2
}
```

`$OS_DIR/tests/qa/test_langfuse.py`:
```python
import json, os
from qa.sources.langfuse import normalize_trace
from qa.model import Interaction

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "langfuse_trace.json")

def test_normalize_trace_to_interaction():
    with open(FIX) as fh:
        trace = json.load(fh)
    i = normalize_trace(trace)
    assert isinstance(i, Interaction)
    assert i.id == "trace-1"
    assert i.source == "langfuse"
    assert i.user_input == "como va la cartera"
    assert i.agent_output == "aqui tienes"
    assert i.tool_calls[0].name == "get_segment_distribution"
    assert i.latency_ms == 1200
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_langfuse.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.sources.langfuse'`.

- [ ] **Step 3: Implementar `qa/sources/langfuse.py`** (ajustar el mapeo de campos al shape REAL de RECON_QA.md)

```python
import os
import requests
from qa.model import Interaction, ToolCall


def normalize_trace(trace: dict) -> Interaction:
    obs = trace.get("observations", []) or []
    tool_calls = [
        ToolCall(name=o.get("name", "?"),
                 ok=(o.get("level") != "ERROR"),
                 message=o.get("statusMessage"))
        for o in obs
    ]
    latency = trace.get("latency")
    latency_ms = int(latency * 1000) if isinstance(latency, (int, float)) else None
    return Interaction(
        id=trace.get("id", ""),
        timestamp=trace.get("timestamp", ""),
        source="langfuse",
        user_input=str((trace.get("input") or {}).get("user", "")),
        agent_output=str((trace.get("output") or {}).get("text", "")),
        tool_calls=tool_calls,
        execution_error=None,
        latency_ms=latency_ms,
        raw=trace,
    )


def fetch_interactions(cfg: dict, since: str) -> list[Interaction]:
    """Lee traces de Langfuse vía REST. cfg = sección langfuse del target.
    Las credenciales salen de las env vars nombradas en cfg."""
    if not cfg.get("enabled"):
        return []
    host = os.environ[cfg["host_env"]]
    pk = os.environ[cfg["public_key_env"]]
    sk = os.environ[cfg["secret_key_env"]]
    resp = requests.get(
        f"{host}/api/public/traces",
        params={"limit": 100},  # ventana 'since' se filtra abajo si la API no lo soporta
        auth=(pk, sk), timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return [normalize_trace(t) for t in data]
```

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_langfuse.py -v`
Expected: PASS (el test de `normalize_trace`; `fetch_interactions` no se testea en vivo).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/sources/langfuse.py tests/qa/test_langfuse.py tests/qa/fixtures/langfuse_trace.json && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.sources.langfuse (normalize + fetch)"
```

---

## Task 8: Adapter Supabase (`qa/sources/supabase.py`)

Usar la tabla/columnas reales de `RECON_QA.md`. Test sobre la normalización de una fila, sin DB en vivo.

**Files:**
- Create: `$OS_DIR/qa/sources/supabase.py`, `$OS_DIR/tests/qa/test_supabase.py`

- [ ] **Step 1: Escribir el test que falla**

`$OS_DIR/tests/qa/test_supabase.py`:
```python
from qa.sources.supabase import normalize_row
from qa.model import Interaction

def test_normalize_row_to_interaction():
    row = {
        "id": 42,
        "created_at": "2026-05-26T01:00:00Z",
        "user_message": "hola",
        "agent_response": "",
        "error": "tool timeout",
        "latency_ms": 5000,
    }
    i = normalize_row(row)
    assert isinstance(i, Interaction)
    assert i.id == "42"
    assert i.source == "supabase"
    assert i.user_input == "hola"
    assert i.agent_output == ""
    assert i.execution_error == "tool timeout"
    assert i.latency_ms == 5000
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_supabase.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'qa.sources.supabase'`.

- [ ] **Step 3: Implementar `qa/sources/supabase.py`** (ajustar nombres de columna al esquema REAL de RECON_QA.md)

```python
import os
from qa.model import Interaction


def normalize_row(row: dict) -> Interaction:
    return Interaction(
        id=str(row.get("id", "")),
        timestamp=str(row.get("created_at", "")),
        source="supabase",
        user_input=str(row.get("user_message", "") or ""),
        agent_output=str(row.get("agent_response", "") or ""),
        tool_calls=[],
        execution_error=(row.get("error") or None),
        latency_ms=row.get("latency_ms"),
        raw=row,
    )


def fetch_interactions(cfg: dict, since: str) -> list[Interaction]:
    """Lee filas de la tabla de interacciones de Supabase. cfg = sección supabase.
    Implementación con el cliente confirmado en RECON_QA.md (supabase-py o psycopg)."""
    if not cfg.get("enabled"):
        return []
    from supabase import create_client  # añadir 'supabase' a requirements en este paso
    client = create_client(os.environ[cfg["url_env"]], os.environ[cfg["key_env"]])
    resp = client.table(cfg["table"]).select("*").order("created_at", desc=True).limit(200).execute()
    return [normalize_row(r) for r in (resp.data or [])]
```
Añadir la dep: `cd "$OS_DIR" && ./.venv/bin/pip install -q supabase && echo "supabase" >> requirements.txt` (o `psycopg[binary]` si RECON_QA.md indicó SQL directo).

- [ ] **Step 4: Correr y ver pasar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_supabase.py -v`
Expected: PASS (test de `normalize_row`).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/sources/supabase.py tests/qa/test_supabase.py requirements.txt && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.sources.supabase (normalize + fetch)"
```

---

## Task 9: CLI orquestador (`qa/report.py` — main)

Une todo: config → sources → detect → group → render → escribir archivo.

**Files:**
- Modify: `$OS_DIR/qa/report.py` (añadir `main`/`run_report`)
- Test: `$OS_DIR/tests/qa/test_run_report.py`

- [ ] **Step 1: Escribir el test que falla** (inyecta interacciones, no toca red)

`$OS_DIR/tests/qa/test_run_report.py`:
```python
import os, tempfile
from qa.model import Interaction, ToolCall
from qa.report import run_report

def test_run_report_writes_file(tmp_path):
    interactions = [
        Interaction(id="1", timestamp="2026-05-26T01:00:00Z", source="langfuse",
                    user_input="x", agent_output="", tool_calls=[ToolCall("q", False, "boom")],
                    execution_error=None, latency_ms=100, raw={}),
    ]
    out = run_report(target="petramora", since="24h", interactions=interactions,
                     sources_ok=["langfuse"], sources_failed=[],
                     out_dir=str(tmp_path))
    assert os.path.isfile(out)
    content = open(out).read()
    assert "QA report — petramora" in content
    assert "tool_error" in content
```

- [ ] **Step 2: Correr y ver fallar**

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest tests/qa/test_run_report.py -v`
Expected: FAIL — `ImportError: cannot import name 'run_report'`.

- [ ] **Step 3: Añadir `run_report` + `main` a `qa/report.py`**

```python
import os
from datetime import datetime, timezone
from qa.detect import detect_errors
from qa.group import group_findings
from qa.model import Interaction


def run_report(target: str, since: str, interactions: list[Interaction],
               sources_ok: list[str], sources_failed: list[str],
               out_dir: str) -> str:
    findings = detect_errors(interactions)
    groups = group_findings(findings)
    md = render_markdown(target=target, since=since,
                         n_interactions=len(interactions), groups=groups,
                         sources_ok=sources_ok, sources_failed=sources_failed)
    dest_dir = os.path.join(out_dir, target)
    os.makedirs(dest_dir, exist_ok=True)
    fname = datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".md"
    path = os.path.join(dest_dir, fname)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md)
    return path


def main(argv=None):
    import argparse
    from qa.config import load_target, target_path
    from qa.sources import langfuse as lf
    from qa.sources import supabase as sb

    os_dir = os.environ.get("OS_DIR", os.getcwd())
    p = argparse.ArgumentParser(description="QA observabilidad — informe")
    p.add_argument("--target", required=True)
    p.add_argument("--since", default=None)
    p.add_argument("--out-dir", default=os.path.join(os_dir, "qa-reports"))
    args = p.parse_args(argv)

    cfg = load_target(target_path(os_dir, args.target))
    since = args.since or cfg.default_since
    interactions: list[Interaction] = []
    ok, failed = [], []
    for name, mod, sect in (("langfuse", lf, cfg.langfuse), ("supabase", sb, cfg.supabase)):
        try:
            got = mod.fetch_interactions(sect, since)
            interactions.extend(got)
            if sect.get("enabled"):
                ok.append(name)
        except Exception as e:  # robustez: una fuente caída no aborta el informe
            failed.append(f"{name} ({type(e).__name__})")
    path = run_report(args.target, since, interactions, ok, failed, args.out_dir)
    print(f"Informe escrito en: {path}")
    return path


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr y ver pasar** (suite completa)

Run: `cd "$OS_DIR" && ./.venv/bin/python -m pytest -v`
Expected: PASS — toda la suite verde.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa/report.py tests/qa/test_run_report.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: qa.report run_report + CLI main"
```

---

## Task 10: Smoke test end-to-end contra datos reales

Validación real (no asumida). Requiere las env vars de Langfuse/Supabase cargadas.

**Files:** ninguno (validación)

- [ ] **Step 1: Cargar credenciales y correr el CLI**

```bash
cd "$OS_DIR"
set -a; source "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"; set +a
./.venv/bin/python -m qa.report --target petramora --since 24h
```
Expected: imprime "Informe escrito en: .../qa-reports/petramora/YYYY-MM-DD.md" sin excepción no controlada. Si una fuente falla, el informe debe anotarlo y aun así escribirse.

- [ ] **Step 2: Inspeccionar el informe**

```bash
cat "$OS_DIR/qa-reports/petramora/$(date -u +%F).md"
```
Expected: resumen con nº de interacciones reales, fuentes OK/fallidas, y (si hay) grupos de error priorizados con ids trazables.

- [ ] **Step 3: Añadir qa-reports/ al control de versiones y commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add qa-reports && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "test: smoke e2e qa report sobre datos reales de Petramora"
```

> Si las credenciales no están disponibles o una fuente no existe (según RECON_QA.md), este task se documenta como pendiente de un entorno con acceso, igual que la nota analista/radar de Fase 1.

---

## Self-Review (hecho al escribir el plan)

- **Cobertura del spec:** model→Task2; detect (5 señales)→Task3; group+prioriza→Task4; report markdown→Task5/9; config por target YAML→Task6; sources Langfuse/Supabase→Task7/8; informe con histórico en `qa-reports/<target>/`→Task9; agnóstico del repo (otro YAML)→Task6; robustez fuente caída→Task9 main; tests con fixtures sintéticas→Tasks2-9; recon de feasibility→Task0; criterio de éxito (CLI sobre datos reales)→Task10. ✅
- **Placeholders:** los `<real>` de Task6/7/8 son valores que Task0 resuelve y se sustituyen al escribir; señalados explícitamente, no son TODOs sueltos. ✅
- **Consistencia de tipos:** `Interaction`, `ToolCall`, `ErrorFinding`, `ErrorGroup`, `TargetConfig`, `detect_errors`, `group_findings`, `render_markdown`, `run_report`, `fetch_interactions`, `normalize_trace`, `normalize_row` — nombres usados igual en todas las tasks. `TIMEOUT_MS` definido en detect y referenciado en su test. ✅
