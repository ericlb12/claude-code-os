from qa.model import Interaction


class ReproError(Exception):
    """No se puede construir un caso reproductor a partir de la interacción."""


def build_repro_case(interaction: Interaction) -> dict:
    """Construye un caso de eval reproductor en el esquema real de Petramora.
    El check `sin_error` lo aplica el evaluador automáticamente; el `modo` se
    decide por el archivo de dataset, no aquí."""
    pregunta = (interaction.user_input or "").strip()
    if not pregunta:
        raise ReproError(f"interacción {interaction.id} sin user_input reproducible")
    return {
        "id": f"qa-autofix-{interaction.id}",
        "pregunta": pregunta,
        "tools_esperadas": [],
        "debe_contener": [],
        "no_debe": [],
        "valor_esperado": [],
    }
