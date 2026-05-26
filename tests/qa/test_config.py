import os
from qa.config import load_target, TargetConfig

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "target_ok.yaml")

def test_load_target_parses_fields():
    cfg = load_target(FIX)
    assert isinstance(cfg, TargetConfig)
    assert cfg.name == "demo"
    assert cfg.default_since == "24h"
    assert cfg.langfuse["enabled"] is True
    assert cfg.langfuse["project"] == "demo-project"
    assert cfg.supabase["table"] == "agent_interactions"

def test_load_missing_file_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_target("/no/existe.yaml")
