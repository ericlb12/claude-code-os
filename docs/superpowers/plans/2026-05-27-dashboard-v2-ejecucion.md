# Dashboard v2 (Ejecución + pulido) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir al dashboard una capa de ejecución (cuadro de prompt que lanza `claude -p` headless + botones-atajo seguros vía allowlist) y dar una pasada de pulido visual, manteniendo todo local y seguro.

**Architecture:** Nuevo `dashboard/exec.py` con `run_prompt` (envuelve `claude -p`, ejecutor inyectable) y `run_script` (allowlist fija de comandos). `app.py` añade `POST /api/run` y `POST /api/run-script` (envueltos en `_safe`). Frontend añade la zona "RUN A SKILL". Pulido visual con frontend-design (DOM con textContent, sin innerHTML). Tests con ejecutor fake (no se lanza agente real).

**Tech Stack:** Python 3.12, FastAPI, pytest + TestClient, subprocess (lista de args, sin shell). venv nativo WSL. HTML/CSS/JS vanilla.

> **Setup (una vez por shell):**
> ```bash
> export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
> PY=~/.venvs/claude_code_os/bin/python   # venv NATIVO WSL (NO crear venv en Dropbox)
> ```
> Tests en `tests/qa/` SIN `__init__.py`; `conftest.py` en la raíz. El dashboard v1 ya existe (`dashboard/app.py`, `panels/`, `static/`, `config.py` con `DashConfig`).
> Seguridad: `subprocess.run([...])` SIEMPRE en lista (sin `shell=True`). El frontend usa `textContent` (NUNCA innerHTML).

---

## File Structure

- `dashboard/exec.py` — NUEVO: `run_prompt`, `run_script`, allowlist `SCRIPTS`, `_default_executor`
- `dashboard/app.py` — MODIFICAR: añadir `POST /api/run`, `POST /api/run-script`
- `dashboard/static/index.html` — MODIFICAR: zona "RUN A SKILL"
- `dashboard/static/dashboard.js` — MODIFICAR: lógica de la zona RUN
- `dashboard/static/dashboard.css` — MODIFICAR (pulido)
- `tests/qa/test_dash_exec.py` · `test_dash_run_endpoints.py` — NUEVO

Reutilizable: `dashboard/config.py` (`DashConfig` con `cron_log`, etc.), patrón de B `qa/autofix/runner.py` (ejecutor inyectable).

---

## Task 1: `dashboard/exec.py` — run_prompt + run_script + allowlist

**Files:** Create `$OS_DIR/dashboard/exec.py`, `$OS_DIR/tests/qa/test_dash_exec.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_dash_exec.py`

```python
from dashboard import exec as ex

def _fake_ok(cmd, cwd):
    return 0, "salida simulada: " + " ".join(cmd[-2:])

def _fake_boom(cmd, cwd):
    raise RuntimeError("explota")

def test_run_prompt_ok():
    out = ex.run_prompt("dame el estado", os_dir="/wd", executor=_fake_ok)
    assert out["ok"] is True
    assert "salida simulada" in out["output"]

def test_run_prompt_error():
    out = ex.run_prompt("x", os_dir="/wd", executor=_fake_boom)
    assert out["ok"] is False
    assert "explota" in out["error"]

def test_run_script_allowlisted():
    calls = {}
    def fake(cmd, cwd): calls["cmd"]=cmd; calls["cwd"]=cwd; return 0, "ok-script"
    out = ex.run_script("informe_qa", os_dir="/wd", executor=fake)
    assert out["ok"] is True and out["output"] == "ok-script"
    assert "qa.cron" in " ".join(calls["cmd"])   # ejecutó el comando de la allowlist

def test_run_script_rejects_unknown():
    out = ex.run_script("rm_rf_todo", os_dir="/wd", executor=lambda c, w: (0, "no deberia"))
    assert out["ok"] is False
    assert "permitido" in out["error"].lower()
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_exec.py -v`
Expected: ModuleNotFoundError / AttributeError.

- [ ] **Step 3: Implementar `$OS_DIR/dashboard/exec.py`**

```python
import os
import subprocess

VENV_PY = os.path.expanduser("~/.venvs/claude_code_os/bin/python")
EVALS_WT = ("/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/"
            "Agente IA/source_petramora/.worktrees/feature-agent-evals/Agente_segmentador")

# Allowlist: id -> (comando en lista, cwd | None=os_dir). NUNCA texto arbitrario.
SCRIPTS = {
    "informe_qa": ([VENV_PY, "-m", "qa.cron", "--target", "petramora"], None),
    "evals": ([VENV_PY, "-m", "evals.run_evals", "--modo", "comercial"], EVALS_WT),
}

PROMPT_TIMEOUT_S = 600


def _default_executor(cmd: list, cwd: str):
    """Ejecuta cmd (lista, sin shell). Devuelve (returncode, stdout+stderr)."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=PROMPT_TIMEOUT_S)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_prompt(texto: str, os_dir: str, executor=_default_executor) -> dict:
    """Lanza `claude -p <texto>` headless en os_dir (permisos normales)."""
    if not (texto or "").strip():
        return {"ok": False, "error": "prompt vacío"}
    cmd = ["claude", "-p", texto]
    try:
        rc, out = executor(cmd, os_dir)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": rc == 0, "returncode": rc, "output": out[-8000:]}


def run_script(script_id: str, os_dir: str, executor=_default_executor) -> dict:
    """Ejecuta SOLO un comando de la allowlist SCRIPTS."""
    spec = SCRIPTS.get(script_id)
    if spec is None:
        return {"ok": False, "error": f"script no permitido: {script_id}"}
    cmd, cwd = spec
    try:
        rc, out = executor(cmd, cwd or os_dir)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": rc == 0, "returncode": rc, "output": out[-8000:]}
```

- [ ] **Step 4: Correr → PASS**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_exec.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/exec.py tests/qa/test_dash_exec.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard.exec (run_prompt + run_script allowlist)"
```

---

## Task 2: endpoints `/api/run` y `/api/run-script` en `app.py`

**Files:** Modify `$OS_DIR/dashboard/app.py`; Create `$OS_DIR/tests/qa/test_dash_run_endpoints.py`

- [ ] **Step 1: Test que falla** — `$OS_DIR/tests/qa/test_dash_run_endpoints.py`

```python
from fastapi.testclient import TestClient
import dashboard.app as appmod

def test_run_endpoint(monkeypatch):
    monkeypatch.setattr(appmod.execmod, "run_prompt",
                        lambda texto, os_dir, **k: {"ok": True, "output": "hecho:" + texto})
    c = TestClient(appmod.app)
    r = c.post("/api/run", json={"prompt": "hola"})
    assert r.status_code == 200
    assert r.json()["ok"] is True and "hecho:hola" in r.json()["output"]

def test_run_script_endpoint(monkeypatch):
    monkeypatch.setattr(appmod.execmod, "run_script",
                        lambda sid, os_dir, **k: {"ok": True, "output": "script:" + sid})
    c = TestClient(appmod.app)
    r = c.post("/api/run-script", json={"id": "informe_qa"})
    assert r.status_code == 200
    assert r.json()["output"] == "script:informe_qa"
```

- [ ] **Step 2: Correr → FAIL**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_run_endpoints.py -v`

- [ ] **Step 3: Modificar `$OS_DIR/dashboard/app.py`**

Añadir el import arriba (junto a los otros), con alias para poder monkeypatch en tests:
```python
from dashboard import exec as execmod
from fastapi import Request
```
Y añadir estos dos endpoints (antes del `@app.get("/")`):
```python
@app.post("/api/run")
async def api_run(req: Request):
    body = await req.json()
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    return _safe(execmod.run_prompt, (body or {}).get("prompt", ""), os_dir)


@app.post("/api/run-script")
async def api_run_script(req: Request):
    body = await req.json()
    os_dir = os.environ.get("OS_DIR", os.getcwd())
    return _safe(execmod.run_script, (body or {}).get("id", ""), os_dir)
```
(`_safe` ya existe y envuelve la llamada devolviendo `ok:false` si lanza.)

- [ ] **Step 4: Correr → PASS + suite**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_run_endpoints.py -v && $PY -m pytest -q`
Expected: PASS; suite completa verde.

- [ ] **Step 5: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/app.py tests/qa/test_dash_run_endpoints.py && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: endpoints /api/run + /api/run-script"
```

---

## Task 3: Frontend — zona "RUN A SKILL"

**Files:** Modify `$OS_DIR/dashboard/static/index.html`, `$OS_DIR/dashboard/static/dashboard.js`

- [ ] **Step 1: Añadir la zona RUN a `index.html`** (insertar dentro de `.wrap`, como primer hijo tras `.meters`)

```html
  <div class="card" style="grid-column:1/-1" id="run-zone">
    <h3>Run a skill</h3>
    <div class="run-actions">
      <button class="btn" data-script="informe_qa">Informe QA</button>
      <button class="btn" data-script="evals">Correr evals</button>
      <button class="btn" data-script="ver_informe">Ver informe</button>
      <button class="btn" data-script="ver_cron_log">Ver cron.log</button>
    </div>
    <textarea id="run-prompt" rows="3" placeholder="escribe un prompt para Claude Code…"></textarea>
    <div class="run-bar"><button class="btn primary" id="run-btn">RUN</button><span id="run-state" class="muted"></span></div>
    <pre id="run-output" class="run-output"></pre>
  </div>
```
Nota: `ver_informe` y `ver_cron_log` NO están en la allowlist de `exec.SCRIPTS` (que solo ejecuta procesos). Para esta v2, esos dos botones llaman a endpoints de LECTURA ya existentes del panel: reutiliza `/api/runs` (para cron.log) y, para "ver informe", muestra el contenido del último informe — si no hay endpoint de lectura del .md, deja esos dos botones llamando a `/api/run-script` y AÑADE a la allowlist de Task 1 dos entradas de lectura. **Decisión para mantener simple:** añadir a `SCRIPTS` en Task 1 NO (son lectura, no proceso). En su lugar, en el JS estos dos botones hacen `GET /api/runs` (cron.log) y `GET` del informe vía un endpoint nuevo trivial. Para no ampliar el backend aquí, en esta v2 `ver_informe`/`ver_cron_log` se implementan en el JS abriendo `/api/runs` y mostrando su JSON; el informe completo queda para v2.1. Mantén SOLO `informe_qa` y `evals` como scripts ejecutables; `ver_*` muestran datos ya disponibles.

- [ ] **Step 2: Añadir lógica a `dashboard.js`** (al final, sin innerHTML)

```javascript
async function post(p, body){ try{ const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}); return await r.json(); }catch(e){ return {ok:false,error:String(e)}; } }

function setOutput(text){ const o=document.getElementById("run-output"); o.textContent = text; }
function setRunState(text){ document.getElementById("run-state").textContent = text; }

async function runPrompt(){
  const texto=document.getElementById("run-prompt").value.trim();
  if(!texto){ setRunState("escribe algo primero"); return; }
  setRunState("ejecutando…"); setOutput("");
  const res=await post("/api/run",{prompt:texto});
  setRunState(res.ok?"ok":"error");
  setOutput(res.ok ? (res.output||"(sin salida)") : ("ERROR: "+(res.error||"")));
}

async function runScript(id){
  if(id==="ver_cron_log"){ const r=await get("/api/runs"); setOutput(JSON.stringify(r.runs||r, null, 2)); setRunState("cron.log"); return; }
  if(id==="ver_informe"){ const r=await get("/api/errors"); setOutput(JSON.stringify(r, null, 2)); setRunState("último informe (resumen)"); return; }
  setRunState("ejecutando "+id+"…"); setOutput("");
  const res=await post("/api/run-script",{id});
  setRunState(res.ok?"ok":"error");
  setOutput(res.ok ? (res.output||"(sin salida)") : ("ERROR: "+(res.error||"")));
}

document.getElementById("run-btn").addEventListener("click", runPrompt);
document.querySelectorAll(".run-actions .btn").forEach(b=>{
  b.addEventListener("click", ()=>runScript(b.getAttribute("data-script")));
});
```

- [ ] **Step 3: Verificar que la página sigue sirviéndose**

Run: `cd "$OS_DIR" && $PY -m pytest tests/qa/test_dash_app.py -v`
Expected: verde.

- [ ] **Step 4: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/static/index.html dashboard/static/dashboard.js && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: dashboard zona RUN (prompt + botones-atajo)"
```

---

## Task 4: Pulido visual con frontend-design

**Files:** Modify `$OS_DIR/dashboard/static/dashboard.css`, `index.html`, `dashboard.js` (solo estética; no cambia la lógica de fetch ni introduce innerHTML)

- [ ] **Step 1: Invocar el skill frontend-design** para rediseñar la estética de la página (tema oscuro tipo vídeo: medidores con barras de progreso, gráfico de actividad real usando `claude-health.actividad_por_dia`, tarjetas con jerarquía, zona RUN destacada con los estilos `.btn`/`.btn.primary`/`.run-output`). Restricciones que el skill DEBE respetar:
  - Mantener los `id`/clases que usa `dashboard.js` (`m-tokens`, `m-inter`, `m-err`, `m-etl`, `p-errors`, `p-runs`, `p-inter`, `p-fresh`, `p-etl`, `run-prompt`, `run-btn`, `run-state`, `run-output`, `.run-actions .btn[data-script]`).
  - NO usar innerHTML en el JS (DOM con textContent). Si añade un mini-gráfico, que lo dibuje con elementos/SVG por DOM o un `<svg>` estático en el HTML.
  - Añadir las clases `.btn`, `.btn.primary`, `.run-output`, `.run-actions`, `.run-bar`, `textarea` al CSS.

- [ ] **Step 2: Verificar que nada se rompió**

Run: `cd "$OS_DIR" && $PY -m pytest -q`
Expected: suite completa verde (el pulido es CSS/HTML; no toca paneles ni endpoints).

- [ ] **Step 3: Commit**

```bash
cd "$OS_DIR" && git -c user.name="Eric" -c user.email="comercial@likeik.com" add dashboard/static && git -c user.name="Eric" -c user.email="comercial@likeik.com" commit -m "feat: pulido visual dashboard (frontend-design, estilo vídeo)"
```

---

## Task 5: Smoke real (endpoints de ejecución)

**Files:** ninguno (validación)

- [ ] **Step 1: Levantar el server y probar un script seguro (no lanza agente)**

```bash
export OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
cd "$OS_DIR"; set -a; source "$ENV" 2>/dev/null; set +a; export OS_DIR
~/.venvs/claude_code_os/bin/python -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8770 >/tmp/dashv2.log 2>&1 &
SRV=$!; sleep 5
echo "--- run-script informe_qa ---"
curl -s -X POST http://127.0.0.1:8770/api/run-script -H "Content-Type: application/json" -d '{"id":"informe_qa"}' | head -c 300; echo
echo "--- run-script no permitido ---"
curl -s -X POST http://127.0.0.1:8770/api/run-script -H "Content-Type: application/json" -d '{"id":"hackeo"}' | head -c 200; echo
kill $SRV 2>/dev/null
```
Expected: `informe_qa` → `ok:true` con salida del informe (genera el .md del día); `hackeo` → `ok:false` "script no permitido". (NO probamos `/api/run` con claude real aquí; eso lo dispara Eric a mano por coste/tiempo.)

- [ ] **Step 2: (Manual, Eric) probar el prompt real**

Documentar que Eric, con el server levantado (`bash scripts/dashboard.sh`), abre `http://localhost:8765`, escribe un prompt en la zona RUN y pulsa RUN para ver a Claude Code headless ejecutar y devolver salida. No se automatiza (lanza agente / consume).

- [ ] **Step 3: (sin commit — es validación)** Anotar el resultado del smoke en el reporte final.

---

## Self-Review (hecho al escribir el plan)

- **Cobertura del spec:** run_prompt + run_script + allowlist → Task 1; endpoints /api/run y /api/run-script con _safe → Task 2; zona RUN (prompt + botones) → Task 3; pulido frontend-design → Task 4; smoke (script seguro + rechazo allowlist) → Task 5; tests con ejecutor fake sin agente → Tasks 1-2; seguridad (subprocess lista, 127.0.0.1, cwd OS_DIR, permisos normales, allowlist) → Task 1 + spec. ✅
- **Placeholders:** Task 3 Step 1 aclara explícitamente que `ver_informe`/`ver_cron_log` se resuelven en el JS con endpoints de lectura existentes (no son scripts ejecutables); `informe_qa`/`evals` son los únicos ejecutables. Sin TODOs colgando. ✅
- **Consistencia:** `run_prompt(texto, os_dir, executor=)` y `run_script(script_id, os_dir, executor=)` con misma firma en impl (Task 1), tests (Task 1) y endpoints (Task 2, vía `execmod`); claves de salida `{ok, output, error, returncode}` usadas igual en backend y JS; ids de la allowlist (`informe_qa`, `evals`) coinciden entre `SCRIPTS` (Task 1) y los `data-script` del HTML (Task 3); `execmod` alias usado en app y en el monkeypatch del test. ✅
- **Seguridad:** subprocess en lista sin shell; allowlist estricta; 127.0.0.1; permisos normales de claude; JS sin innerHTML (restricción explícita a frontend-design en Task 4). ✅
