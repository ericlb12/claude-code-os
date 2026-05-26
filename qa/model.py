from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ToolCall:
    name: str
    ok: bool
    message: Optional[str] = None


@dataclass
class Interaction:
    id: str
    timestamp: str            # ISO 8601 UTC
    source: str               # "langfuse" | "supabase"
    user_input: str
    agent_output: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    execution_error: Optional[str] = None
    latency_ms: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def has_tool_error(self) -> bool:
        return any(not tc.ok for tc in self.tool_calls)


@dataclass
class ErrorFinding:
    interaction_id: str
    error_type: str           # tool_error|execution_error|empty_output|timeout|explicit_error
    signal: str
    severity: str             # low|medium|high
    excerpt: str
