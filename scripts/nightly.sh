#!/bin/bash
# Wrapper de cron para el run nocturno de QA (Sub-proyecto C).
# Corre A sobre Petramora y registra en cron.log. NO toca B / no abre PRs.
set -uo pipefail

OS_DIR="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os"
ENV_FILE="/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora/Agente_segmentador/.env"
PY="$HOME/.venvs/claude_code_os/bin/python"
TARGET="petramora"
LOG="$OS_DIR/qa-reports/$TARGET/cron.log"

export OS_DIR
mkdir -p "$OS_DIR/qa-reports/$TARGET"

ts() { date -u +%Y-%m-%dT%H:%MZ; }
trap 'echo "$(ts) | FAIL | nightly.sh aborto (codigo $?)" >> "$LOG"' ERR

if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
else
  echo "$(ts) | FAIL | no se encontro .env en $ENV_FILE" >> "$LOG"
  exit 1
fi

cd "$OS_DIR" || { echo "$(ts) | FAIL | no se pudo cd a $OS_DIR" >> "$LOG"; exit 1; }
"$PY" -m qa.cron --target "$TARGET" --since 24h
