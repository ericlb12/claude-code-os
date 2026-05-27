from qa.detect import detect_errors
from qa.group import group_findings


def data(cfg, since="24h", gather=None):
    """Panel de errores: reusa el pipeline QA. gather inyectable para tests."""
    if gather is None:
        from qa.report import gather as gather
    interactions, ok, failed = gather(cfg, since)
    groups = group_findings(detect_errors(interactions))
    return {
        "ok": True,
        "n_interactions": len(interactions),
        "sources_failed": failed,
        "grupos": [
            {"error_type": g.error_type, "signal": g.signal, "severity": g.severity,
             "count": g.count, "interaction_ids": g.interaction_ids[:10],
             "ejemplos": g.examples}
            for g in groups
        ],
    }
