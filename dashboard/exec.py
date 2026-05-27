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
