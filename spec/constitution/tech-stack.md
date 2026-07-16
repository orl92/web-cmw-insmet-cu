# Tech stack y convenciones

## Tecnologías

- **Lenguaje:** Python 3.8+
- **Framework:** Django 5.2, Django REST Framework 3.16
- **Base de datos:** SQLite (desarrollo), PostgreSQL o MySQL (producción con SSL configurable)
- **UI:** Tabler mediante Django Templates en `templates/` raíz
- **API docs:** drf-spectacular + drf-spectacular-sidecar (Swagger UI, Redoc)
- **PDF:** xhtml2pdf, reportlab, pyHanko, wkhtmltopdf (requiere `libcairo2-dev`)
- **Modelos meteorológicos:** MetPy, matplotlib, numpy, pandas, xarray
- **Auth:** LDAP opcional via ldap3; fallback a ModelBackend de Django
- **Estáticos:** WhiteNoise `CompressedManifestStaticFilesStorage` en producción
- **Tests:** `python manage.py test` (todos los `tests.py` son stubs actualmente)
- **Despliegue:** Nginx + Gunicorn (`gunicorn.sh`) + Supervisor

## Archivos / módulos clave

- `config/settings.py` — settings con auto-detección de entorno, auto-generación de `.env`, descifrado de SECRET_KEY con Fernet, validación de configuración de producción
- `config/urls.py` — rutas raíz: `login/`, `admin/`, `api/`, `accounts/`, `dashboard/`, `home/`
- `api/urls.py` — endpoints REST: `/api/doc/`, `/api/redoc/`, `/api/schema/`, stations, station-observation, forecast
- `dashboard/models.py` — todos los modelos del dominio: Forecasts, avisos, servicios, clientes, facturación, publicaciones
- `accounts/ldap3_backend.py` — backend de autenticación LDAP personalizado con ldap3
- `accounts/middleware/check_user_profile.py` — middleware de verificación de perfil
- `dashboard/middleware/maintenance_mode.py` — bloquea no-superusers en modo mantenimiento
- `common/utils.py` — `FileHandlerMixin`, upload paths, error views, utilidades de weather icons

## Comandos

- `source .venv/bin/activate && python manage.py runserver` — entorno local (dev)
- `python manage.py runserver --production` — simula producción local
- `python manage.py test` — ejecuta tests
- `python manage.py add_stations_data` — carga inicial de estaciones
- `python manage.py import_ldap_users` — importa usuarios desde LDAP
- `python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --link --no-input` — setup completo

## Modelo de datos / dominio

- **Forecasts** — 3 regiones (north/interior/south) × 3 períodos (mañana/tarde/noche) con temperatura, tiempo, viento, mar + 5 días extendido + datos astronómicos (luna, sol, UV)
- **BaseWarning** (abstracta) — `uuid`, `user`, `summary`, `file` (PDF), `valid_until`, `email_recipient_list`; heredan EarlyWarning, TropicalCyclone, StormWarning
- **WeatherToday / WeatherTomorrow / WeatherCommentary / WeatherNote** — reportes con PDF y lista de correo
- **Customer ↔ User** (OneToOne) — cliente con datos fiscales cubanos (REEUP, NIT, cuenta bancaria)
- **Service** — público o comercial; con precio (CUP), código, PDF e imagen
- **ServiceSubscription** — soft delete (`record_active`), estados: requested → pending → paid → expired; `is_active` property
- **Invoice / InvoiceItem** — facturación con cálculo automático de importe
- **CompanySettings** — singleton (`pk=1`); datos fiscales de la empresa
- **SiteConfiguration** — flag `maintenance_mode`
- **Profile** — vinculado a User por señal post_save; avatar redimensionado a 300×300 cuadrado
- **ScientificPublication / Author** — publicaciones con coautores, ORCID, PDF

## Convenciones

- **Idioma**: todo el texto visible (verbose_name, help_text, mensajes UI, documentación) en español (`es-mx`, `America/Havana`)
- **UUIDs**: todos los modelos expuestos en URLs usan `uuid.UUIDField` como identificador en lugar de PK numérica
- **Archivos**: `FileHandlerMixin` para borrar automáticamente archivos del media al actualizar/eliminar el registro; las rutas se generan con `pdf_upload_path` / `image_upload_path` en `common/utils.py`
- **Permisos**: todos los modelos del dashboard usan `default_permissions = ()` + 4 permisos custom (`view_*`, `add_*`, `change_*`, `delete_*`)
- **Templates**: en `templates/` raíz (no por app); layouts, includes y pages
- **Estáticos**: `static/` en desarrollo, `staticfiles/` en producción con WhiteNoise
- **Migrations**: NO están versionadas (excluidas en `.gitignore`); ejecutar `makemigrations` siempre en setup

## Estilo visual

- **Tema:** Tabler (https://tabler.io) — plantilla Bootstrap 5
- **Layouts base:** `templates/layouts/base.html` (dashboard), `templates/layouts/home.html` (público), `templates/layouts/base-auth.html` (login)
- **Iconos meteorológicos:** imágenes PNG en `static/dist/img/weather_icon/` y `static/dist/img/moon_faces/`

## Límites duros

- No añadir dependencias npm o frontend JS framework sin aprobación (todo es Django Templates + Tabler)
- No exponer `.env`, `db.sqlite3`, o `media/` en el repositorio
- No eliminar `FileHandlerMixin` de modelos que usan campos FileField/ImageField (pérdida de datos)
- No cambiar `default_permissions = ()` en modelos del dashboard sin redefinir los 4 permisos custom
