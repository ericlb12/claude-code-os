from dashboard.panels.claude_health import resumir


def test_resumir_con_uso():
    eventos = [
        {"ts": "2026-05-27T01:00:00Z", "input_tokens": 100, "output_tokens": 50},
        {"ts": "2026-05-27T02:00:00Z", "input_tokens": 200, "output_tokens": 80},
        {"ts": "2026-05-26T01:00:00Z", "input_tokens": 10, "output_tokens": 5},
    ]
    out = resumir(eventos)
    assert out["ok"] is True
    assert out["total_eventos"] == 3
    assert out["tokens_in"] == 310
    assert out["tokens_out"] == 135
    dias = {d["dia"]: d for d in out["actividad_por_dia"]}
    assert dias["2026-05-27"]["eventos"] == 2


def test_resumir_sin_tokens_degrada_a_conteo():
    eventos = [{"ts": "2026-05-27T01:00:00Z"}, {"ts": "2026-05-27T02:00:00Z"}]
    out = resumir(eventos)
    assert out["tokens_in"] == 0
    assert out["total_eventos"] == 2
    assert out["actividad_por_dia"][0]["eventos"] == 2
