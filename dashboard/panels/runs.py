import os


def parse_cron_log(text: str) -> dict:
    """Parsea líneas 'ts | ok|FAIL | k=v | ...'. Runs más reciente primero."""
    runs = []
    for line in [l for l in text.splitlines() if l.strip()]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        entry = {"ts": parts[0], "status": parts[1]}
        for p in parts[2:]:
            if "=" in p:
                k, v = p.split("=", 1)
                entry[k.strip()] = v.strip()
        runs.append(entry)
    runs.reverse()
    return {"ok": True, "total": len(runs), "runs": runs[:15]}


def data(cfg, os_dir=None):
    os_dir = os_dir or os.environ.get("OS_DIR", os.getcwd())
    path = os.path.join(os_dir, cfg.cron_log) if cfg.cron_log else None
    if not path or not os.path.isfile(path):
        return {"ok": True, "total": 0, "runs": [], "nota": "sin cron.log todavía"}
    with open(path, "r", encoding="utf-8") as fh:
        out = parse_cron_log(fh.read())
    out["proximo_cron"] = "03:00 (diario)"
    return out
