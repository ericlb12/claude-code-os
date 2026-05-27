#!/bin/bash
# Lanza el dashboard de monitorización (solo lectura).
set -uo pipefail
OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV_FILE="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
PY="$HOME/.venvs/claude_code_os/bin/python"
PORT="${1:-8765}"
export OS_DIR
cd "$OS_DIR"
[[ -f "$ENV_FILE" ]] && { set -a; source "$ENV_FILE"; set +a; }
echo "Dashboard en http://localhost:$PORT  (Ctrl+C para parar)"
exec "$PY" -m uvicorn dashboard.app:app --host 127.0.0.1 --port "$PORT"
