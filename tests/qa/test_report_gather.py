from qa.config import TargetConfig
from qa.report import gather


def _cfg():
    return TargetConfig(name="t", default_since="24h",
                        langfuse={"enabled": False}, supabase={"enabled": False})


def test_gather_disabled_sources_yield_empty():
    interactions, ok, failed = gather(_cfg(), "24h")
    assert interactions == []
    assert ok == []
    assert failed == []
