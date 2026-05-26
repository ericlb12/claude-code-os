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
