# QA nocturno remoto (GitHub Actions) — Diseño

**Fecha:** 2026-05-27
**Autor:** Eric (comercial@likeik.com) + Claude Code
**Estado:** Aprobado (diseño) — pendiente plan de implementación

## Contexto

Cierra el **hueco #2 [Cadence]** del primer `os-audit` (81/100): el cron QA es solo
local (exige PC+WSL encendidos). Lo movemos a la nube con **GitHub Actions** para que
el informe nocturno corra con el PC apagado. Decisión de Eric: hacerlo ahora "para
tener la opción" (no tiene Mac mini todavía), asumiendo el trade-off de credenciales.

El QA nocturno (A) es **Python puro** (`qa.cron` → `qa.report`, sin agente) → encaja
en un cron de GitHub Actions, no en una routine de agente. Mover B (autofix) a remoto
queda fuera (eso sí necesitaría agente cloud).

## Decisiones (brainstorming)

1. **Mecanismo: GitHub Actions** (gratis: ~2000 min/mes Free; el job tarda ~1-2 min →
   ~30-60 min/mes). Descartada la routine de Anthropic (más para agentes, límites).
2. **Repo privado en GitHub** (cuenta `ericlb12`). `claude_code_os` ya tiene git +
   historial → crear remoto y push. **Privado** por los informes (posible PII) y por
   higiene.
3. **Credenciales** como *repository secrets*: `SUPABASE_URL`, `SUPABASE_KEY`. Trade-off
   aceptado: las claves de producción de Petramora viven en GitHub (repo privado).
4. **Output**: el run commitea el informe (`qa-reports/petramora/<fecha>.md`) + la línea
   de `cron.log` **de vuelta al repo**. Se ve en GitHub; `git pull` lo baja a local.
5. **Cron local**: tras validar Actions, **se desinstala el crontab local** para evitar
   divergencia (dos copias escribiendo el informe). GitHub Actions pasa a ser el primario.

## Alcance

### Pre-requisito: subir el repo a GitHub (privado)
- **Secret-scan antes de push**: confirmar que NINGÚN fichero trackeado contiene
  secretos reales (el `.env` real está en Petramora, NO aquí; `connections.md` solo
  nombra variables). Revisar `git grep` de patrones de clave antes de crear el remoto.
- Crear repo privado `ericlb12/claude-code-os` con `gh repo create` y `git push`.

### Workflow `.github/workflows/qa-nightly.yml`
```yaml
name: QA nightly (Petramora)
on:
  schedule:
    - cron: "0 1 * * *"      # 01:00 UTC ≈ 03:00 Madrid (CEST). GH cron es UTC y aproximado.
  workflow_dispatch: {}        # botón para lanzarlo a mano
permissions:
  contents: write              # para commitear el informe de vuelta
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - name: Run QA report
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OS_DIR: ${{ github.workspace }}
        run: python -m qa.cron --target petramora --since 24h
      - name: Commit report
        run: |
          git config user.name "qa-bot"
          git config user.email "qa-bot@users.noreply.github.com"
          git add qa-reports/
          git commit -m "chore: QA nightly $(date -u +%F)" || echo "sin cambios"
          git push
```

### Unidades / cómo encaja
- `qa.cron` ya acepta `OS_DIR` por env y escribe en `qa-reports/<target>/`. En Actions,
  `OS_DIR = github.workspace` (la raíz del checkout). Sin cambios de código en `qa/`.
- `requirements.txt` ya lista `pyyaml`, `supabase`, `requests` → `pip install` basta.
- El target `petramora.yaml` (langfuse off, supabase agent_logs) ya está en el repo.

## Robustez / errores
- Si Supabase falla, `qa.cron` ya escribe línea `FAIL` en `cron.log` y el commit la sube.
- Si no hay cambios (informe idéntico), el `commit || echo` evita que el job falle.
- `workflow_dispatch` permite probar y re-lanzar sin esperar al cron.

## Seguridad
- Repo **privado**. Secrets de GitHub (cifrados, no en el código). 
- Caveat: claves de producción del cliente en GitHub + informes con posible PII en el
  repo. Aceptable en privado; revisar si algún día el repo se hace público (NO hacerlo).
- Pre-push secret-scan para no subir nada sensible por error.

## Fuera de alcance (YAGNI)
- Mover B (autofix headless) a remoto (necesita agente cloud / routine).
- Notificación externa (Slack/email) del informe — de momento vive en el repo.
- Borrar el histórico local de `qa-reports/` (se mantiene; Actions añade encima).

## Criterio de éxito
1. Repo privado `ericlb12/claude-code-os` creado y pusheado, sin secretos en el árbol.
2. `workflow_dispatch` corre el job → genera el informe del día y lo **commitea al repo**
   (verificado en GitHub).
3. El `schedule` queda activo (corre de noche con el PC apagado).
4. Crontab local desinstalado tras validar (sin doble informe).
5. Secrets `SUPABASE_URL`/`SUPABASE_KEY` configurados; el run lee Supabase OK.
