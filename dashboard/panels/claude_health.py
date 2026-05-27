import os
import glob
import json


def resumir(eventos: list[dict]) -> dict:
    """eventos: [{ts, input_tokens?, output_tokens?}]. Suma uso + serie por día. Puro."""
    tokens_in = sum(int(e.get("input_tokens") or 0) for e in eventos)
    tokens_out = sum(int(e.get("output_tokens") or 0) for e in eventos)
    por_dia: dict[str, dict] = {}
    for e in eventos:
        dia = str(e.get("ts", ""))[:10]
        if not dia:
            continue
        d = por_dia.setdefault(dia, {"dia": dia, "eventos": 0, "tokens": 0})
        d["eventos"] += 1
        d["tokens"] += int(e.get("input_tokens") or 0) + int(e.get("output_tokens") or 0)
    serie = sorted(por_dia.values(), key=lambda d: d["dia"], reverse=True)
    return {"ok": True, "total_eventos": len(eventos), "tokens_in": tokens_in,
            "tokens_out": tokens_out, "actividad_por_dia": serie}


def _leer_eventos(logs_dir: str) -> list[dict]:
    """Extrae eventos de los *.jsonl de Claude Code. Tolerante al formato."""
    base = os.path.expanduser(logs_dir)
    eventos = []
    for f in glob.glob(os.path.join(base, "**", "*.jsonl"), recursive=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = o.get("timestamp") or o.get("ts") or ""
                    usage = o.get("usage") or (o.get("message") or {}).get("usage") or {}
                    eventos.append({"ts": ts,
                                    "input_tokens": usage.get("input_tokens"),
                                    "output_tokens": usage.get("output_tokens")})
        except OSError:
            continue
    return eventos


def data(cfg):
    try:
        eventos = _leer_eventos(cfg.claude_logs_dir)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return resumir(eventos)
