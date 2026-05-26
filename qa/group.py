from dataclasses import dataclass, field
from qa.model import ErrorFinding

_SEV_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class ErrorGroup:
    error_type: str
    signal: str
    severity: str
    count: int
    interaction_ids: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


def group_findings(findings: list[ErrorFinding]) -> list[ErrorGroup]:
    buckets: dict[tuple[str, str], ErrorGroup] = {}
    for f in findings:
        key = (f.error_type, f.signal)
        g = buckets.get(key)
        if g is None:
            g = ErrorGroup(error_type=f.error_type, signal=f.signal,
                           severity=f.severity, count=0)
            buckets[key] = g
        g.count += 1
        g.interaction_ids.append(f.interaction_id)
        if f.excerpt and len(g.examples) < 2:
            g.examples.append(f.excerpt)
        if _SEV_RANK.get(f.severity, 0) > _SEV_RANK.get(g.severity, 0):
            g.severity = f.severity
    return sorted(buckets.values(),
                  key=lambda g: (g.count, _SEV_RANK.get(g.severity, 0)),
                  reverse=True)
