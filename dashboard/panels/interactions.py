def data(cfg, since="24h", gather=None):
    if gather is None:
        from qa.report import gather as gather
    interactions, ok, failed = gather(cfg, since)
    total = len(interactions)
    con_error = sum(1 for i in interactions if i.execution_error)
    recientes = [
        {"id": i.id, "ts": i.timestamp, "input": (i.user_input or "")[:80],
         "error": bool(i.execution_error)}
        for i in interactions[:10]
    ]
    return {"ok": True, "total": total, "con_error": con_error,
            "sources_failed": failed, "recientes": recientes}
