# Deploy automático a producción

Objetivo: que lo que entra a `main` llegue a producción sin intervención manual, con backup previo de la base y una decisión explícita de cuándo se publica.
Rama: cambios desde `dev` en `chore/deploy-*`; llegan a `main` por PR.
Entrega: cambios pequeños y verificables; el merge lo decide el humano.
Runner: `python manage.py test` (Django), `bash -n deploy/deploy.sh` (script), schema oficial `json.schemastore.org/github-workflow.json` (workflows). El script corre en el servidor: probarlo aquí solo valida sintaxis.

## Specs

- **S1** — El workflow de deploy debe ser válido para GitHub y dispararse por `workflow_run` de `CI` en `main` con `conclusion == success`, más `workflow_dispatch` para reintento, rollback o hotfix. **Cumplido.**
- **S2** — Antes de `migrate`, `deploy.sh` debe dejar un dump de PostgreSQL fuera del checkout, con retención configurable, y el deploy **no debe continuar** si el dump falla. Supuesto: la base de producción es PostgreSQL (`psycopg[binary]` en `requirements/prod.txt`). Retención y ruta por definir.
- **S3** — El environment `production` debe existir y tener `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_SSH_KNOWN_HOSTS`. Los secretos los carga el humano: no pasan por chat ni por el repo. **Environment creado; secrets pendientes.**
- **S4** — Gate de release, una de dos: **(a)** tag `vX.Y.Z` — `main` puede ir por delante de producción y se despliega solo lo etiquetado; **(b)** merge verde en `main` + aprobación en el environment `production`. **Decisión pendiente.**

## Tasks

| ID | Spec | Tarea | Ruta | Estado |
|---|---|---|---|---|
| T1 | S1 | Corregir el YAML del workflow (`environment` en la raíz) y renombrar a `deploy-production.yml` | inline | hecho — `6bfa76b`, PR #112 |
| T2 | S1 | Mergear #112 a `dev` y abrir `dev → main` (el `workflow_run` se lee de la rama por defecto) | humano | pendiente |
| T3 | S3 | Cargar los 4 secrets en el environment `production` | humano | pendiente |
| T4 | S2 | Dump previo a `migrate` en `deploy.sh`, con retención y fallo cerrado | inline + prueba en servidor | pendiente |
| T5 | S4 | Definir el gate y ajustar el trigger del workflow | inline | pendiente (bloquea T4 por diseño, no por código) |

## Log

- **L1** (2026-10-28): "ya le dije lo de los permisos y que me invitara, ahora vamos con los pendientes, que me recomiendas hacer primero".
- **L2**: el repo pasó de `orl92/web-cmw-insmet-cu` a la organización `cmp-camaguey`, y `yoelvismr` quedó con `role_name: admin`. Sigue sin ser miembro de la org: es *outside collaborator*.
- **L3** (diagnóstico, corregido): el deploy automático nunca corrió — 0 eventos `workflow_run` en todo el historial, 58 runs de 0 jobs. Primero se atribuyó a un registro viejo de GitHub; la causa real es YAML inválido: `environment:` en la raíz del workflow. `environment` solo es válido a nivel de job.
- **L4** (verificación): con el archivo inválido, cada push generaba un run de 0 jobs; con el archivo corregido, un push **no** genera run — que es lo correcto, porque ese workflow no escucha `push`.
- **L5**: el workflow fantasma `375100808` quedó `disabled_manually`. Con el rename, la ruta `deploy.yml` deja de existir.
