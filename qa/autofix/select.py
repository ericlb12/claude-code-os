from qa.model import ErrorFinding

REPRODUCIBLE_TYPES = {"execution_error"}


def reproducible_interaction_ids(findings: list[ErrorFinding]) -> list[str]:
    """IDs de interacción con error reproducible (execution_error), sin duplicar,
    en orden de aparición."""
    seen: list[str] = []
    for f in findings:
        if f.error_type in REPRODUCIBLE_TYPES and f.interaction_id not in seen:
            seen.append(f.interaction_id)
    return seen
