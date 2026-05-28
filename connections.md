# Connections — sistemas que el Claude Code OS / agente Petramora alcanza

Registro de cada sistema alcanzable. Lo leen `os-audit` (cobertura/frescura) y
`os-level-up`. Al cablear algo nuevo, añade una fila (y, si es API, una guía en
`references/{tool}-api.md`).

| # | Dominio | Herramienta | Mecanismo | Auth | Última revisión |
|---|---|---|---|---|---|
| 1 | Trazas/interacciones agente | Supabase `agent_logs` | key+ref | SUPABASE_URL/KEY (en Petramora `.env`) | 2026-05-27 |
| 2 | Competencia / scrapers | Supabase `scraper_runs` (leído vía VIEW `all_runs`) | key+ref | idem Supabase | 2026-05-28 |
| 3 | Segmentación clientes | Supabase `segmentacion_clientes_raw` | key+ref | idem Supabase | 2026-05-27 |
| 4 | Ventas históricas | Azure SQL `MS_PETRAMORA_HIST_VENTAS` | script (solo vía backend Cloud Run, IP fija 34.175.58.90; NO desde WSL) | connection string en backend | 2026-05-27 |
| 5 | Código | GitHub `ericlb12/Petramora_source` | script (gh CLI) | gh auth (ericlb12) | 2026-05-27 |
| 6 | Deploy frontend | Vercel | export (autodeploy con push) | — | 2026-05-27 |
| 7 | Deploy/infra | gcloud | script (desde PowerShell, NO WSL) | gcloud auth | 2026-05-27 |
| 8 | Uso/actividad Claude Code | logs `~/.claude/projects/**/*.jsonl` | export (lectura local) | — | 2026-05-27 |
| 9 | ETLs financieros (PyG, Journal, Presupuesto, Financiero v2, Segmentador) | Supabase `etl_runs` (via `etl_logger.track_run` en backend) | key+ref | idem Supabase | 2026-05-28 |
| 10 | Frescura Azure SQL | Supabase `azure_freshness` (mirror via Cloud Scheduler → backend `POST /internal/azure-freshness-sync`) | script | IAM service account `sa-azure-freshness` | 2026-05-28 |

**Mecanismos:** `mcp` | `script` | `export` | `key+ref` | `not yet connected`.

## Pendientes de cablear (gaps conocidos)
- Langfuse: no integrado en Petramora (adapter listo en `qa/` pero `enabled:false`).
