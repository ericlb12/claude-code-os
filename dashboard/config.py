import os
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class DashConfig:
    name: str
    default_since: str
    supabase: dict[str, Any]
    etl: dict[str, Any]
    freshness: dict[str, Any]
    claude_logs_dir: str
    cron_log: str


def load_dash_target(path: str) -> DashConfig:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        d = yaml.safe_load(fh) or {}
    return DashConfig(
        name=d.get("name", ""),
        default_since=d.get("default_since", "24h"),
        supabase=d.get("supabase", {"enabled": False}),
        etl=d.get("etl", {}),
        freshness=d.get("freshness", {"tablas": []}),
        claude_logs_dir=d.get("claude_logs_dir", "~/.claude/projects"),
        cron_log=d.get("cron_log", ""),
    )
