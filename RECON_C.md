# RECON_C — Estado de cron en WSL (Sub-proyecto C)

Fecha: 2026-05-27
Host: WSL (Ubuntu), usuario por defecto `eric_likeik`

## Resumen ejecutivo

Buenas noticias: **cron ya está instalado, el servicio está corriendo y arranca solo** (gracias a systemd). **No hace falta sudo** para montar el cron nocturno: basta con `crontab -e` como usuario normal.

## Hallazgos

### ¿`cron` y `crontab` instalados?
Sí.
- `cron`    → `/usr/sbin/cron`
- `crontab` → `/usr/bin/crontab`

No hace falta `apt install cron`.

### ¿Servicio cron running/stopped?
**Running.** Gestionado por systemd:
```
cron.service - Regular background program processing daemon
   Loaded: loaded (/usr/lib/systemd/system/cron.service; enabled; preset: enabled)
   Active: active (running)
```
- `enabled` → arranca automáticamente al iniciar WSL.
- **No requiere `sudo service cron start`** porque ya está activo y habilitado.

### ¿Existe `/etc/wsl.conf` y tiene `[boot] command`?
Sí existe `/etc/wsl.conf`, con:
```ini
[boot]
systemd=true

[user]
default=eric_likeik
```
- **`systemd=true`** es la clave: con systemd activo, los servicios `enabled` (como `cron.service`) arrancan solos al abrir WSL. **No hace falta un `[boot] command = service cron start`** (ese truco solo se necesita en WSL sin systemd).
- No hay línea `command` bajo `[boot]`, y NO es necesaria en esta configuración.

### ¿Hay crontab del usuario ya?
No. `crontab -l` → `no crontab for eric_likeik`. Limpio para añadir el job nocturno.

## Método recomendado para activar el cron nocturno

Dado el estado actual, el camino es directo y **sin sudo**:

1. (No necesario) ~~`sudo apt install cron`~~ — ya instalado.
2. (No necesario) ~~`sudo service cron start`~~ — ya running.
3. (No necesario) ~~auto-arranque vía `/etc/wsl.conf`~~ — ya cubierto por `systemd=true`.
4. **Único paso real:** crear el job con `crontab -e` (sin sudo) y añadir la línea del script. Ej.:
   ```
   0 3 * * * /ruta/al/script.sh >> /ruta/al/log.log 2>&1
   ```

### Pasos que requerirían sudo/password (acción de Eric) — NO necesarios aquí
- Instalar cron (no hace falta).
- Arrancar/habilitar el servicio (no hace falta).
- Editar `/etc/wsl.conf` (no hace falta).

Si en el futuro se quisiera correr el cron como root (`/etc/cron.d/` o `sudo crontab -e`), eso sí pediría sudo. Para un job de usuario no.

## Realidad LOCAL importante

Esto corre en la **máquina local de Eric (PC Windows + WSL)**, no en un servidor 24/7:
- Si **el PC está apagado/suspendido** a la hora del cron, **el job NO corre** (cron no recupera ejecuciones perdidas por defecto).
- Si **WSL no está abierto** (ninguna terminal/proceso WSL activo), la distro puede no estar arrancada y el cron no corre.
- Para fiabilidad nocturna real habría que: dejar el PC encendido y WSL vivo, o mover el job a la idea del Mac mini servidor 24/7 (ver memoria del proyecto). Alternativa: `anacron` para recuperar trabajos perdidos, pero no resuelve el PC apagado.
