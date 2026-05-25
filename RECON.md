# RECON — repo Petramora (para skills dev)

> Reconocimiento solo-lectura realizado el 2026-05-25. Todos los valores son reales (verificados con `git` y ejecución de comandos), no placeholders.

- **Ruta repo principal:** `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora`
  - Es un repo git válido (`git rev-parse --is-inside-work-tree` → `true`).
  - El nombre de carpeta es `source_petramora` (no `petramora` ni `biwise`). Hay muchas otras carpetas con "petramora"/"biwise" en el sistema, pero NO son repos git (caches de Claude/Codeium, presupuestos, copias de Dropbox, etc.). El único repo git real es este.

- **Ramas:** (salida real de `git branch -a`)
  - Locales:
    - `comercial-finanzas-multi-llm`
    - `comercial-finanzas-multi-llm-plugins`
    - `comercial-finanzas-multi-llm-plugins-financiero-v2`  ← **rama actualmente checked out en el repo principal** (`*`)
    - `comercial-finanzas-multi-llm-sub`
    - `comercial-finanzas-multi-llm-sub-codex`
    - `comercial-multi-llm`
    - `feature/agent-evals`  ← checked out en el worktree de evals (`+`)
    - `master`
  - Remotas (`origin/`): mismas que las locales arriba + `origin/HEAD -> origin/master`.
  - **`master`: SÍ existe** (local y `origin/master`, que es el HEAD por defecto del remoto).
  - **`staging`: NO existe.** No hay rama `staging` ni local ni remota. (Dato verificado — no inventado.) La rama "de trabajo" actual es `comercial-finanzas-multi-llm-plugins-financiero-v2`.

- **Remoto(s):** (salida real de `git remote -v`)
  ```
  origin	https://github.com/ericlb12/Petramora_source.git (fetch)
  origin	https://github.com/ericlb12/Petramora_source.git (push)
  ```

- **Worktree de evals:** `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/.worktrees/feature-agent-evals` (rama `feature/agent-evals`, commit `3a241e8`).
  - Salida de `git worktree list`:
    ```
    .../source_petramora                                  1121f48 [comercial-finanzas-multi-llm-plugins-financiero-v2]
    .../source_petramora/.worktrees/feature-agent-evals   3a241e8 [feature/agent-evals]
    ```

- **Contenido de `evals/`:** OJO — `evals/` NO está en la raíz del worktree, sino dentro del paquete **`Agente_segmentador/`**.
  - Ruta real: `.../.worktrees/feature-agent-evals/Agente_segmentador/evals/`
  - Ficheros reales:
    - `__init__.py`
    - `README.md`
    - `dataset.py`
    - `evaluator.py`
    - `run_evals.py`  (runner CLI dedicado)
    - `coverage_report.py`
    - `datasets/` (carpeta de datasets `.jsonl`)
    - `__pycache__/`

- **Comando exacto para correr evals:** todos los comandos se ejecutan **desde `Agente_segmentador/`** (no desde la raíz del worktree).

  Ruta base:
  ```bash
  cd "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/.worktrees/feature-agent-evals/Agente_segmentador"
  ```

  - **Runner CLI dedicado** (corre los casos contra el LLM real vía `chat_core`):
    ```bash
    python3 -m evals.run_evals                 # todos los modos con dataset
    python3 -m evals.run_evals --modo analista # solo un modo
    python3 -m evals.run_evals --provider gpt-4o   # default provider: gemini
    ```
    (El README usa `python`, pero en este entorno `python` NO existe → usar `python3`.)

  - **Bajo pytest** (el caso eval específico, skipea sin API key):
    ```bash
    python3 -m pytest tests/test_evals.py -v
    ```

  - **Suite completa de tests** (pytest.ini fija `testpaths = tests`, así que basta):
    ```bash
    python3 -m pytest -v
    ```
    `pytest.ini` real:
    ```
    [pytest]
    testpaths = tests
    markers =
        eval: caso de evaluacion end-to-end contra LLM real (lento, requiere API key)
        addopts = -ra
    ```
    Hay un `conftest.py` en `Agente_segmentador/` que añade el dir a `sys.path` y define fixtures `require_llm` (skip sin API key) y `clean_session`.

- **Notas / gotchas:**
  - **`python` vs `python3`:** `python` NO existe en este entorno (`command not found`). Usar **`python3`** (3.12.3). El README de evals dice `python` — corregir mentalmente a `python3`.
  - **pytest:** versión instalada **9.0.3** (coincide con "pytest 9.x"). `requirements-dev.txt` solo pide `pytest>=8.0` y `pytest-asyncio>=0.23`.
  - **PEP 668 / pip bloqueado:** asumir que `pip install` falla por entorno gestionado; existe un venv del proyecto en `/home/eric_likeik/petramora-venv` que probablemente ya tiene las deps. No intentar instalar paquetes globalmente.
  - **`.env` requerido:** existe `Agente_segmentador/.env` con (nombres de claves, sin valores): `SUPABASE_URL`, `SUPABASE_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`, `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, `AZURE_SQL_USER`, `AZURE_SQL_PASSWORD`, `STEEL_API_KEY`. Los evals end-to-end requieren al menos una API key de LLM (`GOOGLE_API_KEY`/`GEMINI_API_KEY`/`OPENAI_API_KEY`), si no, pytest los skipea vía la fixture `require_llm`.
  - **Ubicación de evals:** el paquete vive en `Agente_segmentador/evals/`, NO en la raíz del repo/worktree. Los `python3 -m evals.run_evals` y `python3 -m pytest` deben lanzarse con cwd = `Agente_segmentador/`.
  - **Ground-truth de datasets:** modos comercial/financiero/radar → Supabase; modo analista → Azure SQL Server (`MS_PETRAMORA_HIST_VENTAS`).
  - **Rama de integración:** no hay `staging`. El flujo de merge (según memoria del usuario) exige staging+preview antes de master, pero la rama "staging" como tal no existe en este repo; la rama de trabajo activa es `comercial-finanzas-multi-llm-plugins-financiero-v2`.
