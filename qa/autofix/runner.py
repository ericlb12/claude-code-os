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


def run_fix(case: dict, modo: str, branch: str, base: str, worktree: str,
            executor: Executor = _default_executor, dry_run: bool = False) -> FixResult:
    prompt = build_prompt(case, modo=modo, branch=branch, base=base)
    if dry_run:
        return FixResult(status="dry_run", branch=branch, detail=prompt)
    out = executor(prompt, worktree)
    m = re.search(r"PR_URL=(\S+)", out or "")
    if m:
        return FixResult(status="opened_pr", pr_url=m.group(1), branch=branch,
                         detail=(out or "")[-2000:])
    return FixResult(status="failed", branch=branch, detail=(out or "")[-2000:])
