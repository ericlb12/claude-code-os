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
        case = build_repro_case(interaction)
    except ReproError as e:
        return FixResult(status="failed", detail=f"no reproducible: {e}")
    branch = _branch_for(interaction_id)
    kwargs = dict(case=case, modo=modo, branch=branch, base=base,
                  worktree=worktree, dry_run=dry_run)
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
    p.add_argument("--interaction", required=True)
    p.add_argument("--modo", required=True)
    p.add_argument("--worktree", required=True)
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
