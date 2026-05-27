# Panel informativo de plugins/herramientas: para que alguien nuevo sepa qué hay y
# cómo usarlo desde Claude Code. Read-only. Lista editable en petramora.yaml (plugins:).

DEFAULT_PLUGINS = [
    {"nombre": "superpowers",
     "para_que": "Disciplina de desarrollo: brainstorming, planes, TDD, debugging, "
                 "ejecución por subagentes, code review.",
     "como_usar": "Se activan solos al pedir desarrollo (\"añade X\", \"arregla Y\"). "
                  "También invocables: di \"usa brainstorming\" o el skill concreto."},
    {"nombre": "frontend-design",
     "para_que": "Crear interfaces web con buena calidad de diseño (no genéricas).",
     "como_usar": "Pide construir una UI/página/componente; o di \"usa frontend-design\"."},
    {"nombre": "watch",
     "para_que": "Ver/analizar un vídeo (YouTube o local): transcribe y responde sobre él.",
     "como_usar": "/watch <url-o-ruta> [pregunta]   (ej. /watch https://youtu.be/... )"},
    {"nombre": "karpathy-wiki",
     "para_que": "Segundo cerebro: captura conocimiento durable y responde desde el wiki.",
     "como_usar": "Captura automática al surgir info durable; pregunta \"¿qué sabemos de X?\"."},
    {"nombre": "claude-mem",
     "para_que": "Memoria entre sesiones: recuerda trabajo previo.",
     "como_usar": "Pregunta \"¿cómo hicimos X la última vez?\" o usa el skill mem-search."},
]


def data(cfg):
    plugins = getattr(cfg, "plugins", None) or DEFAULT_PLUGINS
    return {"ok": True, "plugins": plugins}
