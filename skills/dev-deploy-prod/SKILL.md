---
name: dev-deploy-prod
description: Use when Eric wants to promote Petramora/BIwise to production — verifies staging + preview are validated, then merges `staging` into `master` (Vercel auto-deploys prod). Guardrail skill; never merges to master without validation.
---

# dev-deploy-prod — promover a prod

## Cuándo
Cuando Eric dice "deploy a prod", "promociona a producción", "merge a master".

## Repo
- `/mnt/c/Users/Luis Ojeda/Likeik CX Dropbox/Comercial/@PROYECTOS/Agente IA/source_petramora`
- Remoto: `origin` → `https://github.com/ericlb12/Petramora_source.git`. Vercel autodeploya prod con push a `master`.

## Guardarraíl — verificar ANTES de mergear
1. Confirmar que existe `staging` y que su deploy se hizo y está validado.
2. Confirmar que el **preview** correspondiente está validado.
3. Si CUALQUIERA falta o no está claro → PARAR y avisar a Eric. No mergear sin su autorización explícita.

## Pasos (solo si el guardarraíl pasa)
1. `git -C <repo> checkout master && git -C <repo> pull origin master`
2. `git -C <repo> merge staging`
3. Si hay conflictos → parar y avisar (no auto-resolver).
4. `git -C <repo> push origin master` → Vercel autodeploya prod.
5. Confirmar a Eric que prod se está desplegando.

## Reglas duras (memoria de Eric)
- NUNCA merge a `master` sin staging + preview previos, salvo autorización explícita de Eric.
- gcloud, si hace falta, desde **PowerShell**, NO desde WSL.
