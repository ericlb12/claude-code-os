from qa.autofix.prompt import build_prompt

def test_prompt_includes_guardrails_case_and_modo():
    case = {"id": "qa-autofix-42", "pregunta": "como va la cartera",
            "tools_esperadas": [], "debe_contener": [], "no_debe": [], "valor_esperado": []}
    p = build_prompt(case, modo="comercial", branch="qa-autofix/2026-05-26-exec-42", base="master")
    # guardarraíles
    assert "qa-autofix/2026-05-26-exec-42" in p
    assert "nunca" in p.lower() and "master" in p.lower()
    assert "merge" in p.lower()
    assert "gh pr create" in p
    # caso + modo
    assert "como va la cartera" in p
    assert "comercial" in p
    assert "datasets/comercial.jsonl" in p
    # modo degradado + protocolo de salida
    assert "rojo" in p.lower()
    assert "PR_URL=" in p
