import os
import requests
from qa.model import Interaction, ToolCall


def normalize_trace(trace: dict) -> Interaction:
    obs = trace.get("observations", []) or []
    tool_calls = [
        ToolCall(name=o.get("name", "?"),
                 ok=(o.get("level") != "ERROR"),
                 message=o.get("statusMessage"))
        for o in obs
    ]
    latency = trace.get("latency")
    latency_ms = int(latency * 1000) if isinstance(latency, (int, float)) else None
    return Interaction(
        id=trace.get("id", ""),
        timestamp=trace.get("timestamp", ""),
        source="langfuse",
        user_input=str((trace.get("input") or {}).get("user", "")),
        agent_output=str((trace.get("output") or {}).get("text", "")),
        tool_calls=tool_calls,
        execution_error=None,
        latency_ms=latency_ms,
        raw=trace,
    )


def fetch_interactions(cfg: dict, since: str) -> list[Interaction]:
    """Lee traces de Langfuse vía REST. cfg = sección langfuse del target.
    Credenciales desde las env vars nombradas en cfg."""
    if not cfg.get("enabled"):
        return []
    host = os.environ[cfg["host_env"]]
    pk = os.environ[cfg["public_key_env"]]
    sk = os.environ[cfg["secret_key_env"]]
    from qa.window import parse_since
    resp = requests.get(
        f"{host}/api/public/traces",
        params={"limit": 100, "fromTimestamp": parse_since(since)},
        auth=(pk, sk), timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return [normalize_trace(t) for t in data]
