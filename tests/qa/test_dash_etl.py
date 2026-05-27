from dashboard.panels.etl import summarize_runs

def test_summarize_runs():
    rows = [
        {"run_at": "2026-05-27T03:00:00Z", "status": "success", "products_found": 120,
         "products_updated": 30, "alerts_generated": 2, "error_message": None},
        {"run_at": "2026-05-26T03:00:00Z", "status": "error", "products_found": 0,
         "products_updated": 0, "alerts_generated": 0, "error_message": "timeout"},
    ]
    out = summarize_runs(rows)
    assert out["ok"] is True
    assert out["ultima"]["status"] == "success"
    assert out["ultima"]["run_at"].startswith("2026-05-27")
    assert out["total_runs"] == 2
    assert out["ultimo_error"]["error_message"] == "timeout"
