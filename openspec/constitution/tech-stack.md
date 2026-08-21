# Tech stack y convenciones

## Tecnologías

- **Lenguaje:** Python 3.12 (CI y ruff apuntan a `py312`)
- **Framework:** Django 5.2, Django REST Framework 3.17, drf-spectacular + drf-spectacular-sidecar (Swagger UI, Redoc)
- **Base de datos:** SQLite (desarrollo), PostgreSQL o MySQL (producción con SSL configurable)
- **UI:** Tabler (Bootstrap 5) mediante Django Templates
- **PDF:** xhtml2pdf, pdfkit, pyHanko, reportlab (requiere `libcairo2-dev` en CI)
- **Modelos meteorológicos:** MetPy, matplotlib, numpy, pandas, xarray
- **Excel:** openpyxl (generación), xlrd (lectura de `*.xls`)
- **Auth:** LDAP opcional via `ldap3`; fallback a `ModelBackend` de Django
- **Tareas asíncronas:** Huey + SqliteHuey (NO Celery)
- **Estáticos:** `static/` dev, `staticfiles/` prod con WhiteNoise
- **Tests:** `python manage.py test apps.<app>` (label completo); suite completa antes de commit
- **Despliegue:** Nginx + Gunicorn (`gunicorn.sh`) + Supervisor

## Estructura

- `config/` — settings, urls root, wsgi/asgi, huey
- `apps/api/` — REST endpoints: `/api/doc/`, `/api/redoc/`, stations, observations, forecasts
- `apps/user_auth/` — Profile, login/logout, users/groups, LDAP (`backends.py`), password management
- `apps/core/` — `FileHandlerMixin`, `SoftDeleteModel`, utils (`log_action`, iconos weather, `mail_send`, error views), SiteConfiguration, CompanySettings, EmailRecipientList/Recipient, templatetags, context_processors, middleware
- `apps/dashboard/` — vista agregada del panel
- `apps/commercial/` — Customer, Service, ServiceSubscription, Invoice/InvoiceItem, Contract, Certificate
- `apps/meteo/` — Forecasts/ForecastRegions/ForecastExtendedDay, Warning, WeatherReport, Province, Town, Station; utils para parser Excel
- `apps/home/` — páginas públicas: tiempo, modelos, satélites, servicios, institución
- `apps/publications/` — ScientificPublication, Author

## Comandos

- `source .venv/bin/activate && python manage.py runserver` — entorno local (dev)
- `PRODUCTION=true python manage.py runserver` — simula producción local
- `python manage.py test apps.<app>` — testing selectivo
- `python manage.py add_stations_data` — carga inicial de estaciones
- `python manage.py import_ldap_users` — importa usuarios desde LDAP
- `python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --link --no-input` — setup completo
- `./run_huey.sh &` — worker de correos/PDF

## Modelo de datos / dominio

- **Forecasts** — 3 regiones (north/interior/south) × 3 períodos (mañana/tarde/noche) con temperatura, tiempo, viento, mar + 5 días extendido + datos astronómicos (luna, sol, UV); `ForecastRegions` y `ForecastExtendedDay` normalizados
- **Warning** — modelo unificado con `warning_type` (early/tropical_cyclone/storm); `uuid`, `user`, `summary`, `file` (PDF), `valid_until`, `email_recipient_list`
- **WeatherReport** — reportes por tipo (today/tomorrow/commentary/note) con PDF y lista de correo
- **Province / Town / Station** — geografía y estaciones meteorológicas
- **Customer** — cliente con datos fiscales cubanos (REEUP, NIT, cuenta bancaria), `client_type` (natural/jurídica)
- **Service** — público o comercial; con precio (CUP), código, PDF e imagen
- **ServiceSubscription** — soft delete (`record_active`), estados: requested → pending → paid → expired
- **Invoice / InvoiceItem** — facturación con cálculo automático de importe
- **Contract / Certificate** — servicios comerciales con PDF
- **CompanySettings** — singleton (`pk=1`); datos fiscales de la empresa
- **SiteConfiguration** — flag `maintenance_mode`
- **Profile** — vinculado a User por señal post_save; `newsletter` sincronizado con EmailRecipientList
- **ScientificPublication / Author** — publicaciones con coautores, ORCID, PDF

## Convenciones

- **Idioma**: todo el texto visible (verbose_name, help_text, mensajes UI, documentación) en español (`es-mx`, `America/Havana`)
- **UUIDs**: todos los modelos expuestos en URLs usan `uuid.UUIDField` como identificador en lugar de PK numérica
- **Archivos**: `FileHandlerMixin` para borrar automáticamente archivos del media al actualizar/eliminar el registro
- **Permisos**: `default_permissions = ()` + 4 permisos custom (`view_*`, `add_*`, `change_*`, `delete_*`)
- **URLs**: toda app usa `app_name` en urls.py y nombres estandarizados: `list`, `create`, `detail`, `update`, `delete`, `pdf`. Templates usan `{% url 'app_name:name' %}`, vistas usan `reverse_lazy('app_name:name')`
- **Apps**: todas las apps Django viven en `apps/`. Importar siempre como `from apps.meteo.models import ...`, nunca `from meteo.models import ...`
- **Templates**: raíz `templates/` con `layouts/` e `includes/`; páginas en `apps/<app>/templates/pages/`; indentación de 2 espacios con djlint (`profile = "django"`); emails whitespace-sensitive excluidos
- **Paginación**: `paginate_by = 20` solo en vistas SIN DataTables
- **Migrations**: NO versionadas (excluidas en `.gitignore`); ejecutar `makemigrations` siempre en setup
- **Soft delete**: `SoftDeleteModel` en modelos de negocio sensibles (Customer, Service, ServiceSubscription, Invoice, Contract, Certificate, Warning); NO forzar en modelos auxiliares (InvoiceItem, ForecastRegions, EmailRecipient)

## Estilo visual

- **Tema:** Tabler (https://tabler.io) — plantilla Bootstrap 5
- **Layouts base:** `templates/layouts/base.html` (dashboard), `home.html` (público), `base-auth.html` (login), `form.html`, `list.html`, `maintenance.html`
- **Iconos:** webfont Tabler (`<i class="icon ti ti-*">`); iconos meteorológicos PNG en `static/dist/img/weather_icon/`
- **Modales:** mecanismo nativo de Tabler (data API / `Bootstrap.Modal`)

## Skills del agente

Skills instalados en `~/.agents/skills/`. Se cargan según la tarea vía `using-agent-skills`. Skills complementarias del proyecto: `django-expert`, `frontend-design`, `web-design-guidelines`. MCP: `tabler`, `context7`. Ver AGENTS.md.

## Límites duros

- No añadir dependencias npm o frontend JS framework sin aprobación (todo es Django Templates + Tabler)
- No exponer `.env`, `db.sqlite3`, o `media/` en el repositorio
- No eliminar `FileHandlerMixin` de modelos que usan campos FileField/ImageField (pérdida de datos)
- No cambiar `default_permissions = ()` en modelos sin redefinir los 4 permisos custom
- No saltarse el flujo SDD (spec → plan → tasks → implementación → roadmap)
