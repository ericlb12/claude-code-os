import os
from qa.model import Interaction, ToolCall


def _client(cfg: dict):
    import os
    from supabase import create_client
    return create_client(os.environ[cfg["url_env"]], os.environ[cfg["key_env"]])


def normalize_row(row: dict) -> Interaction:
    raw_tools = row.get("tools_called") or []
    # NOTA: agent_logs.tools_called solo guarda {name,args}, sin estado ok/error por tool.
    # Por eso ok=True siempre: la señal `tool_error` queda inerte en Supabase hasta que
    # se instrumente el éxito/fallo por tool. Los errores de turno se captan vía `error`.
    tool_calls = [
        ToolCall(name=str(t.get("name", "?")), ok=True, message=None)
        for t in raw_tools if isinstance(t, dict)
    ]
    return Interaction(
        id=str(row.get("id", "")),
        timestamp=str(row.get("timestamp", "")),
        source="supabase",
        user_input=str(row.get("user_message", "") or ""),
        agent_output=str(row.get("agent_response", "") or ""),
        tool_calls=tool_calls,
        execution_error=(row.get("error") or None),
        latency_ms=row.get("latency_ms"),
        raw=row,
    )


def fetch_interactions(cfg: dict, since: str) -> list[Interaction]:
    """Lee filas de la tabla de interacciones de Supabase (agent_logs).
    cfg = sección supabase del target."""
    if not cfg.get("enabled"):
        return []
    from qa.window import parse_since
    client = _client(cfg)
    resp = (client.table(cfg["table"]).select("*")
            .gte("timestamp", parse_since(since))
            .order("timestamp", desc=True).limit(200).execute())
    return [normalize_row(r) for r in (resp.data or [])]
