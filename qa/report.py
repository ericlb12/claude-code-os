import os
from datetime import datetime, timezone
from qa.group import ErrorGroup
from qa.detect import detect_errors
from qa.group import group_findings
from qa.model import Interaction


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
        except Exception as e:
            failed.append(f"{name} ({type(e).__name__})")
    path = run_report(args.target, since, interactions, ok, failed, args.out_dir)
    print(f"Informe escrito en: {path}")
    return path


if __name__ == "__main__":
    main()
