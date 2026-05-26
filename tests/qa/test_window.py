from datetime import datetime, timezone
from qa.window import parse_since

def test_parse_hours_returns_iso_in_past():
    ts = parse_since("24h")
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    assert 23 * 3600 < delta.total_seconds() < 25 * 3600

def test_parse_days_and_minutes():
    assert parse_since("7d").endswith("Z")
    assert parse_since("30m").endswith("Z")

def test_parse_invalid_defaults_24h():
    ts = parse_since("basura")
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    assert 23 * 3600 < delta.total_seconds() < 25 * 3600
