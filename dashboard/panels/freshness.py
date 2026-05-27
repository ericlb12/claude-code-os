from datetime import datetime, timezone


def _parse(ts: str):
    if not ts:
        return None
    s = str(ts).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.fromisoformat(str(ts)[:10])
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def evaluar(specs: list[dict], maxfechas: dict) -> dict:
    """specs: [{tabla,col,umbral_dias}]; maxfechas: {tabla: max_fecha}. Puro."""
    ahora = datetime.now(timezone.utc)
    tablas = []
    for s in specs:
        dt = _parse(maxfechas.get(s["tabla"]))
        if dt is None:
            tablas.append({"tabla": s["tabla"], "al_dia": False, "ultima": None, "dias": None})
            continue
        dias = (ahora - dt).total_seconds() / 86400
        tablas.append({"tabla": s["tabla"], "al_dia": dias <= s["umbral_dias"],
                       "ultima": maxfechas.get(s["tabla"]), "dias": round(dias, 1)})
    return {"ok": True, "tablas": tablas}


def data(cfg, fetch_max=None):
    specs = cfg.freshness.get("tablas", [])
    try:
        getter = fetch_max or _fetch_max
        maxfechas = {s["tabla"]: getter(cfg, s["tabla"], s["col"]) for s in specs}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return evaluar(specs, maxfechas)


def _fetch_max(cfg, tabla: str, col: str):
    from qa.sources.supabase import _client
    client = _client(cfg.supabase)
    rows = (client.table(tabla).select(col).order(col, desc=True).limit(1).execute().data or [])
    return rows[0][col] if rows else None
