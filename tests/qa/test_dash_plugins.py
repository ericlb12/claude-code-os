from dashboard.panels.plugins import data, DEFAULT_PLUGINS


class _CfgVacia:
    plugins = []


class _CfgConLista:
    plugins = [{"nombre": "mio", "para_que": "x", "como_usar": "y"}]


def test_usa_default_si_no_hay_lista():
    out = data(_CfgVacia())
    assert out["ok"] is True
    assert out["plugins"] == DEFAULT_PLUGINS
    # cada plugin trae las 3 claves (incluida cómo usar)
    for p in out["plugins"]:
        assert {"nombre", "para_que", "como_usar"} <= set(p)


def test_usa_config_si_existe():
    out = data(_CfgConLista())
    assert out["plugins"][0]["nombre"] == "mio"
