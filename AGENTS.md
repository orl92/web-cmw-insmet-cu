# AGENTS.md — Centro Meteorológico Provincial Camagüey

## Stack

Django 5.2 + DRF + drf-spectacular (OpenAPI), Python 3.12 (CI y ruff apuntan a `py312`). Virtual env `.venv/`. UI: Tabler vía Django Templates; raíz `templates/` con `layouts/` e `includes/`, y páginas en `apps/<app>/templates/pages/`. DB: SQLite dev, PostgreSQL/MySQL prod. Apps dentro de `apps/`.

**Restricción de frontend:** JS 100% vanilla, **SIN Node.js, SIN bundlers ni paso de build**. Las librerías de terceros (Tabler, Tempus Dominus, etc.) se vendorean como `*.min.js` en `static/dist/libs/` y se sirven directo. No introducir npm, transpilación ni tooling JS en el proyecto.

## Misión, alcance y límites duros

**Misión:** portal web del Centro Meteorológico Provincial Camagüey (CMP) — portal público meteorológico + dashboard administrativo (pronósticos, avisos, servicios comerciales, facturación, publicaciones) + API REST para terceros.

**No es:** una SPA / frontend desacoplado (React/Vue/Angular), una red social o foro, ni un proyecto OSS genérico — está diseñado específicamente para el CMP Camagüey.

**Límites duros (no negociables):**
- No commitear secretos ni datos: `.env`, `db.sqlite3` ni `media/` (ya excluidos en `.gitignore`).
- No introducir dependencias npm, bundlers o frameworks JS (todo es Django Templates + Tabler + JS vanilla vendoreado en `static/dist/libs/`).
- No quitar `FileHandlerMixin` de modelos con `FileField`/`ImageField` (pérdida de archivos en media).
- No cambiar `default_permissions = ()` sin redefinir los 4 permisos custom (`view_*`/`add_*`/`change_*`/`delete_*`).
- No saltarse el flujo SDD para features (proposal → design → tasks → implementación → archive en `openspec/changes/`).

## Comandos

```bash
source .venv/bin/activate
pip install -r requirements.txt && python manage.py makemigrations migrate
python manage.py collectstatic --link --no-input
python manage.py add_stations_data createsuperuser
python manage.py runserver                    # desarrollo
python manage.py test apps.<app>              # testing selectivo (label completo, ej: apps.meteo)
python manage.py test                         # full suite (antes de commit)
PRODUCTION=true python manage.py runserver    # producción local (usa DB real, SSL, etc.)
./run_huey.sh &                               # worker de correos/PDF (Huey)
```

## Pre-commit

Los hooks de pre-commit garantizan Ruff, djlint y detect-secrets en cada commit (`.pre-commit-config.yaml`). Instalación (una vez, tras clonar/instalar dev deps):

```bash
pip install -r requirements-dev.txt   # incluye pre-commit
pre-commit install --install-hooks    # activa el hook git Y descarga los entornos de hooks (una vez, no en el primer commit)
pre-commit run --all-files            # ejecutar todos los hooks una vez
```

> **⚠️ IMPORTANTE (PC nueva / red con proxy):** usa SIEMPRE `pre-commit install --install-hooks` en el setup, no `pre-commit install` a secas. Los entornos de hooks (ruff, djlint, detect-secrets) se descargan desde PyPI en la primera ejecución; si se deja para el primer commit, un fallo de red puede colgar el commit y **pre-commit stash los archivos modificados sin stagear en un patch temporal que puede perderse si el proceso se interrumpe** (ver más abajo).
>
> Si la instalación falla con `Could not find a version that satisfies ...` / `No matching distribution found` / timeouts, el problema suele ser el proxy de red (verificar con `pip config list`). Es intermitente: reintentar `pre-commit install --install-hooks` suele resolver. Para hacerlo más resiliente, añade a `~/.pip/pip.conf` (o `~/.config/pip/pip.conf`):
> ```ini
> [global]
> timeout = 120
> retries = 10
> ```
> Y antes de cualquier `pre-commit run` / commit con hooks, asegúrate de que el working tree esté limpio o haz `git stash` manual: pre-commit guarda los archivos modificados sin stagear en un patch temporal antes de correr los hooks y, si el proceso muere (Ctrl-C, timeout, crash), esos cambios quedan fuera del working tree y el patch se pierde con `pre-commit clean`.

- Si `detect-secrets` reporta un falso positivo nuevo, actualizar el baseline con `detect-secrets scan --exclude-files "static/|staticfiles/|.*\.min\.js$|.*\.map$|\.venv/" > .secrets.baseline` y commitear el `.secrets.baseline`.
- El mismo job `pre-commit` corre en CI (`.github/workflows/ci.yml`).

## CI — tests selectivos

El job `test` de CI NO corre la suite completa en cada PR (tarda demasiado):

- **PR**: un job `detect` (`dorny/paths-filter@v3`) detecta qué apps cambiaron (`apps/<app>/**`) y el job `test` corre solo `python manage.py test apps.<app> ...` para las afectadas.
- **Push a main / merge**: siempre corre la suite completa (`python manage.py test`) como red de seguridad.
- Cambios globales (`config/**`, `manage.py`, `requirements*.txt`, `pyproject.toml`, `.github/**`, `templates/**`, `static/**`) fuerzan la suite completa.
- Los labels de app deben ir como ruta completa (`apps.meteo`, no `meteo`): en Django 5.2 el label corto ya no resuelve el paquete de tests.

## Apps + Modelos

| App | Responsabilidad |
|---|---|
| `config/` | settings, urls root, wsgi/asgi, email backend, Huey |
| `apps/api/` | REST endpoints: `/api/doc/`, `/api/redoc/`, stations, observations, forecasts |
| `apps/user_auth/` | Profile, login/logout, users, groups, LDAP auth (`LDAP3Backend`), password management |
| `apps/core/` | FileHandlerMixin, SoftDeleteModel, utils, error views, CompanySettings, SiteConfiguration, EmailRecipientList/Recipient, templatetags, context_processors, middleware, mail_send |
| `apps/dashboard/` | Solo DashboardView principal (vista agregada del panel) |
| `apps/commercial/` | Customer, Service, ServiceSubscription, Invoice/InvoiceItem, Contract, Certificate — servicios comerciales y facturación |
| `apps/meteo/` | Forecasts/ForecastRegions/ForecastExtendedDay, Warning (con warning_type), WeatherReport (today/tomorrow/commentary/note), Province, Town, Station |
| `apps/home/` | Páginas públicas: tiempo, modelos, satélites, servicios, institución |
| `apps/publications/` | ScientificPublication, Author — publicaciones científicas |
| `openspec/changes/` | SDD features (OpenSpec); gentle-ai lee este directorio |

## Convenciones

- **UI Framework**: exclusivamente Tabler.io (Bootstrap 5). No usar otros frameworks CSS/UI.
- **Permisos**: `default_permissions = ()` + 4 personalizados: `view_*`, `add_*`, `change_*`, `delete_*` (en español). NO asumas que existen por defecto.
- **Middleware**: `CheckUserProfileMiddleware` → `MaintenanceModeMiddleware` (bloquea no-superusers excepto `/login/`)
- **Auth**: LDAP opcional (`LDAP3Backend`) → fallback `ModelBackend`; Profile se crea por señal `post_save`; usuarios LDAP con `is_ldap=True`
- **UUIDs** en URLs de modelos expuestos (no `pk`)
- **FileHandlerMixin** obligatorio en todo modelo que tenga FileField/ImageField
- **Soft delete** en modelos de negocio con datos sensibles (Customer, Service, ServiceSubscription, Invoice, Contract, Certificate, Warning). NO forzar en modelos auxiliares/transaccionales (InvoiceItem, ForecastRegions, EmailRecipient).
- **Paginación**: `paginate_by = 20` solo en vistas SIN DataTables. Las vistas con DataTables cargan todos los registros y delegan la paginación al cliente.
- **Migrations** NO versionadas (`.gitignore`)
- **Estáticos**: `static/` dev, `staticfiles/` prod con WhiteNoise
- **Idioma**: español (`es-mx`, `America/Havana`)
- **Tema**: Tabler (Bootstrap 5), iconos meteorológicos PNG en `static/dist/img/weather_icon/`
- **URLs**: toda app con URLs usa `app_name` en urls.py y names estandarizados (`app_name:list`, `create`, `detail`, `update`, `delete`, `pdf`). Templates usan `{% url 'app_name:name' %}`, vistas usan `reverse_lazy('app_name:name')`.
- **Templates (formato)**: indentación de 2 espacios, formateados con djlint (`profile = "django"`, config en `pyproject.toml`). Verificar con `djlint . --reformat --check` y `djlint . --lint` antes de commit (hooks de pre-commit). Los templates de correo en `*/emails/` están excluidos (whitespace-sensitive): NO reindentarlos a mano ni con djlint.
- **Apps**: todas las apps Django viven en `apps/`. Importar como `from apps.commercial.models import ...`, nunca como `from commercial.models import ...`.

## Skills

La lista `<available_skills>` del sistema es la fuente autoritativa de skills cargadas en la sesión. Las skills de proyecto viven en `.opencode/skills/` (viajan con el repo en cualquier clon); las globales en `~/.config/opencode/skills/`.

> **Uso automático**: usa MCPs y skills de forma proactiva cuando la tarea lo requiera, sin esperar a que el usuario los pida. Ver reglas globales en `~/.config/opencode/AGENTS.md`.

### Skills del proyecto (`.opencode/skills/`)
- `using-agent-skills` — árbol de decisión para elegir la skill correcta según la tarea
- `django-expert` — modelos, ORM, DRF, auth, tests, performance Django
- `frontend-design` — diseño visual con identidad (Tabler.io)
- `web-design-guidelines` — auditoría de accesibilidad y UI

### Skills globales (opencode)
- **SDD**: `sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-onboard`
- **Git/PR**: `branch-pr`, `chained-pr`, `work-unit-commits`, `issue-creation`, `systemic-issue-triage`
- **Revisión**: `judgment-day`, `rdd-defect-workflow`, `go-testing`, `gentle-ai-bench`
- **Meta**: `skill-creator`, `skill-improver`, `skill-registry`, `cognitive-doc-design`, `comment-writer`, `customize-opencode`

### MCP
- `context7` — documentación actualizada de librerías/frameworks (Django, DRF, drf-spectacular, etc.). Usarlo siempre que se necesiten APIs, ejemplos o configuración de una librería; formato `use library /django/django`
- `engram` — memoria persistente del proyecto (decisiones, descubrimientos, convenciones)

## Flujo SDD (gentle-ai / OpenSpec)

El proyecto ya existía antes de adoptar gentle-ai; la herramienta se usa para refinar y evolucionar el código de forma trazable. El código ya construido es el repo en sí; los **cambios activos** (work pendiente) viven en `openspec/changes/` como features OpenSpec. No se versiona historial de features previas.

Cada cambio nuevo sigue este flujo (layout **OpenSpec**; gentle-ai lee `openspec/changes/`):

1. `openspec/changes/NNN-nombre/proposal.md` (motivación + solución + criterios de aceptación)
2. `design.md` (plan técnico) + `tasks.md` (checkboxes `- [ ]`/`- [x]`) + `specs/NNN-nombre/spec.md` (requisitos delta)
3. Implementar un task a la vez
4. Si hay cambios de modelo: `python manage.py makemigrations`
5. Verificar: `python manage.py check && python manage.py test apps.<app>`; crear test si falta
6. Marcar tasks `[x]` y commitear (incluir número y nombre del cambio)
7. Al cerrar: `gentle-ai sdd-archive` promueve los specs y archiva el cambio

> El bootstrap (`openspec/config.yaml`, `.atl/skill-registry.md`) lo genera `gentle-ai` vía el skill `sdd-init`.

Antes de codificar, si hace falta clarificar, preguntar: ¿tipo de cambio? ¿app(s) afectada(s)? ¿cambios de DB? ¿URLs/permisos? ¿templates? ¿criterios de aceptación? ¿número de feature?

## Checklist proyecto-específico

Estos items NO los cubren los skills genéricos. Verificarlos siempre:

- [ ] `default_permissions = ()` + 4 permisos custom (view/add/change/delete) en español
- [ ] Kwarg `uuid` (no `pk`) en URLs de modelos con UUIDField
- [ ] FileHandlerMixin + `file_fields` definido si hay FileField/ImageField
- [ ] Soft delete: filtrar `record_active=True` (usa el manager por defecto, no `all_objects`)
- [ ] Tareas/imports Huey registrados en `AppConfig.ready()`
- [ ] Migraciones ejecutadas y NO versionadas (`.gitignore`)

## Modelo de dominio (referencia rápida)

- **Forecasts**: 3 regiones (north/interior/south) × 3 períodos (mañana/tarde/noche) + 5 días extendido + datos astronómicos (luna, sol, UV). `ForecastRegions` y `ForecastExtendedDay` normalizados.
- **Warning**: modelo unificado con `warning_type` (early/tropical_cyclone/storm); `uuid`, `user`, `summary`, `file` (PDF), `valid_until`, `email_recipient_list`.
- **WeatherReport**: por tipo (today/tomorrow/commentary/note) con PDF y lista de correo.
- **Province / Town / Station**: geografía y estaciones meteorológicas.
- **Customer**: datos fiscales cubanos (REEUP, NIT, cuenta bancaria), `client_type` (natural/jurídica).
- **Service**: público o comercial; precio (CUP), código, PDF e imagen.
- **ServiceSubscription**: soft delete (`record_active`); estados `requested → pending → paid → expired`.
- **Invoice / InvoiceItem**: facturación con cálculo automático de importe.
- **Contract / Certificate**: servicios comerciales con PDF.
- **CompanySettings**: singleton (`pk=1`); datos fiscales de la empresa.
- **SiteConfiguration**: flag `maintenance_mode`.
- **Profile**: vinculado a User por señal `post_save`; `newsletter` sincronizado con `EmailRecipientList`.
- **ScientificPublication / Author**: publicaciones con coautores, ORCID, PDF.

## Layouts base (UI)

- `templates/layouts/base.html` (dashboard), `home.html` (público), `base-auth.html` (login), `form.html`, `list.html`, `maintenance.html`.
- Iconos: webfont Tabler (`<i class="icon ti ti-*">`); iconos meteorológicos PNG en `static/dist/img/weather_icon/`.
- Modales: mecanismo nativo de Tabler (data API / `Bootstrap.Modal`).

## Roadmap / Backlog (snapshot histórico)

> Tracking vivo en `openspec/changes/`. Esta lista es un snapshot de la constitución eliminada (commit `a66238d`); verificar vigencia antes de usarlo.

**Activas (históricas):** 071 Performance queries (N+1, índices, cache) · 073 UI polish (toasts/spinners/tablas) · 074 Redis cache · 075 Monitoreo tareas Huey · 076 Auditoría de actividad · 077 Operaciones masivas · 078 Tema personalizado · 079 Exportar gráficos · 080 Debug Toolbar (dev).

**Backlog / ideas:** CSP (django-csp) · 2FA/MFA para staff · validación de archivos subidos (magic bytes/tamaño) · health check `/health/` · búsqueda global en navbar · Auth API (JWT) · WebSockets/notificaciones en tiempo real · i18n EN del portal público.

## Revisión antes de commit

Antes de cada commit (o push/PR), lanzar un subagente de revisión que lea el diff y los archivos cambiados, detecte bugs/errores y los resuelva antes de commitear. Verificar luego con djlint, tests Django y `manage.py check`.

## API + Deploy + Locale

- **API**: DRF con `DjangoModelPermissionsOrAnonReadOnly`; rate limit 100/h anon, 1000/h user; schema en `/api/schema/`
- **Deploy**: Nginx + Gunicorn (`gunicorn.sh`) + Supervisor; estáticos por Nginx en `/static/`, media en `/media/`; socket `/tmp/gunicorn-webcmp.sock`
- **Locale**: `LANGUAGE_CODE = 'es-mx'`, `TIME_ZONE = 'America/Havana'`
