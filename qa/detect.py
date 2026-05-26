from qa.model import Interaction, ErrorFinding

TIMEOUT_MS = 30_000  # umbral de latencia considerada timeout


def detect_errors(interactions: list[Interaction]) -> list[ErrorFinding]:
    findings: list[ErrorFinding] = []
    for i in interactions:
        for tc in i.tool_calls:
            if not tc.ok:
                findings.append(ErrorFinding(
                    interaction_id=i.id, error_type="tool_error",
                    signal=f"tool_call[{tc.name}].ok=False", severity="high",
                    excerpt=(tc.message or "")[:300]))
        if i.execution_error:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="execution_error",
                signal="execution_error set", severity="high",
                excerpt=i.execution_error[:300]))
        if i.agent_output is not None and i.agent_output.strip() == "":
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="empty_output",
                signal="agent_output vacío", severity="medium", excerpt=""))
        if i.latency_ms is not None and i.latency_ms > TIMEOUT_MS:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="timeout",
                signal=f"latency_ms > {TIMEOUT_MS}",
                severity="medium", excerpt=str(i.latency_ms)))
        err = i.raw.get("error") if isinstance(i.raw, dict) else None
        if err:
            findings.append(ErrorFinding(
                interaction_id=i.id, error_type="explicit_error",
                signal="raw.error presente", severity="high",
                excerpt=str(err)[:300]))
    return findings
