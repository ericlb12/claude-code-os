---
name: dev-deploy-staging
description: Use when Eric wants to deploy Petramora/BIwise to staging — gets the current work onto the `staging` branch and pushes it (Vercel auto-deploys the staging environment). Creates `staging` on first use if missing, asking Eric for the base.
---

# dev-deploy-staging — publicar a staging

## Cuándo
Cuando Eric dice "deploy a staging", "sube a staging", "publica staging".

## Repo
- `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora`
- Remoto: `origin` → `https://github.com/ericlb12/Petramora_source.git`. Vercel autodeploya con push.

## Pasos
1. `git -C <repo> status` y rama actual. Revisar si hay cambios sin commitear.
2. Comprobar si existe `staging`:
   `git -C <repo> rev-parse --verify staging` y `... origin/staging`.
   - **Si NO existe:** avisar a Eric y PREGUNTAR desde qué base crearla (normalmente `master` o la rama de trabajo actual). NO crearla en silencio. Crear solo tras su confirmación: `git -C <repo> branch staging <base>`.
3. Llevar el trabajo a `staging`. Si Eric está en otra rama, confirmar CÓMO (merge de la rama de trabajo a `staging`, o trabajar directo en `staging`). No asumir el modelo de ramas — preguntar si hay duda.
4. Commit de los cambios pendientes (pedir mensaje o proponer uno claro).
5. `git -C <repo> push origin staging` → Vercel autodeploya staging.
6. Confirmar a Eric: rama pusheada y que el deploy de staging se dispara solo.

## Reglas duras (memoria de Eric)
- gcloud, si hace falta, se ejecuta desde **PowerShell**, NO desde WSL.
- Esto es SOLO staging — nunca tocar `master` aquí (eso es `dev-deploy-prod`).
