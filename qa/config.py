import os
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class TargetConfig:
    name: str
    default_since: str
    langfuse: dict[str, Any]
    supabase: dict[str, Any]


def load_target(path: str) -> TargetConfig:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return TargetConfig(
        name=data.get("name", ""),
        default_since=data.get("default_since", "24h"),
        langfuse=data.get("langfuse", {"enabled": False}),
        supabase=data.get("supabase", {"enabled": False}),
    )


def target_path(os_dir: str, target: str) -> str:
    return os.path.join(os_dir, "qa", "targets", f"{target}.yaml")
