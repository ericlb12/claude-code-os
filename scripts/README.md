# Cron nocturno QA (Sub-proyecto C)

`nightly.sh` corre A (informe de errores) sobre Petramora cada noche y registra en
`qa-reports/petramora/cron.log`. NO toca B ni abre PRs.

## Estado de cron en este WSL
Ya está listo: cron instalado, servicio activo y con auto-arranque (este WSL usa
`systemd=true` en `/etc/wsl.conf`). No hace falta `apt install`, `service cron start`
ni el truco `[boot] command`. Solo instalar la tarea.

## Instalar la tarea (sin sudo)
`crontab -e` y añadir (corre a las 03:00; el PC/WSL debe estar encendido):
```
0 3 * * * /bin/bash "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/scripts/nightly.sh" >> "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/qa-reports/petramora/cron.boot.log" 2>&1
```
Verificar que quedó instalada: `crontab -l`.

## Realidad LOCAL
Es un cron local: si el equipo o WSL están apagados/suspendidos a las 03:00, esa
noche NO corre (cron no recupera ejecuciones perdidas). Encaja con un futuro
Mac mini 24/7. Revisa `qa-reports/petramora/cron.log` para ver qué noches corrió.

## Ejecutar a mano
```bash
bash "/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/claude_code_os/scripts/nightly.sh"
```

## Qué hace exactamente
1. Carga el `.env` de Petramora (credenciales Supabase).
2. `python -m qa.cron --target petramora --since 24h` (venv `~/.venvs/claude_code_os`).
3. Escribe el informe del día en `qa-reports/petramora/<fecha>.md` y una línea
   `ok|FAIL` en `qa-reports/petramora/cron.log`.
