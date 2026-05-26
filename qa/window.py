import re
from datetime import datetime, timedelta, timezone

_UNITS = {"h": "hours", "d": "days", "m": "minutes"}


def parse_since(since: str) -> str:
    """Convierte '24h'/'7d'/'30m' en un timestamp ISO8601 UTC en el pasado.
    Si no parsea, usa 24h por defecto."""
    m = re.fullmatch(r"\s*(\d+)\s*([hdm])\s*", since or "")
    if m:
        delta = timedelta(**{_UNITS[m.group(2)]: int(m.group(1))})
    else:
        delta = timedelta(hours=24)
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%dT%H:%M:%SZ")
