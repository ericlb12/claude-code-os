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
            load=_default_load, gather=_real_gather, run_report=_real_run_report):
    """Corre A una vez: informe + línea en cron.log. Devuelve la ruta del informe
    (o None si falló). load/gather/run_report inyectables para tests."""
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
