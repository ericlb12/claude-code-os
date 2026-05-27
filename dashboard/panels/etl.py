def summarize_runs(rows: list[dict]) -> dict:
    """Resume filas de scraper_runs (ordenadas desc por run_at). Puro, testeable."""
    if not rows:
        return {"ok": True, "total_runs": 0, "ultima": None, "ultimo_error": None}
    ultima = rows[0]
    ultimo_error = next((r for r in rows if r.get("status") == "error"), None)
    return {
        "ok": True,
        "total_runs": len(rows),
        "ultima": {"run_at": ultima.get("run_at"), "status": ultima.get("status"),
                   "products_found": ultima.get("products_found"),
                   "products_updated": ultima.get("products_updated"),
                   "alerts_generated": ultima.get("alerts_generated")},
        "ultimo_error": ({"run_at": ultimo_error.get("run_at"),
                          "error_message": ultimo_error.get("error_message")}
                         if ultimo_error else None),
    }


def data(cfg, fetch=None):
    try:
        rows = (fetch or _fetch)(cfg)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return summarize_runs(rows)


def _fetch(cfg) -> list[dict]:
    from qa.sources.supabase import _client
    etl = cfg.etl
    client = _client(cfg.supabase)
    return (client.table(etl["table"]).select("*")
            .order(etl.get("run_at_col", "run_at"), desc=True).limit(50).execute().data or [])
