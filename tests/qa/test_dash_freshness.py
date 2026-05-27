from datetime import datetime, timezone, timedelta
from dashboard.panels.freshness import evaluar


def test_evaluar_al_dia_y_desfasado():
    hoy = datetime.now(timezone.utc)
    reciente = (hoy - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    viejo = (hoy - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    specs = [
        {"tabla": "a", "col": "run_at", "umbral_dias": 2},
        {"tabla": "b", "col": "run_at", "umbral_dias": 2},
    ]
    maxfechas = {"a": reciente, "b": viejo}
    out = evaluar(specs, maxfechas)
    assert out["ok"] is True
    by = {t["tabla"]: t for t in out["tablas"]}
    assert by["a"]["al_dia"] is True
    assert by["b"]["al_dia"] is False
