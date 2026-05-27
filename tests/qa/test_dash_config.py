import os
from dashboard.config import load_dash_target

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "dash_target.yaml")

def test_load_dash_target():
    cfg = load_dash_target(FIX)
    assert cfg.supabase["table"] == "agent_logs"
    assert cfg.etl["table"] == "scraper_runs"
    assert cfg.freshness["tablas"][0]["tabla"] == "scraper_runs"
    assert cfg.claude_logs_dir == "~/.claude/projects"
    assert cfg.cron_log == "qa-reports/demo/cron.log"
