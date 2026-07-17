# AGENTS.md — Centro Meteorológico Provincial Camagüey

## Stack

- Django 5.2 + DRF + drf-spectacular (OpenAPI), Python 3.8+
- Virtual env: `.venv/` (activa con `source .venv/bin/activate`)
- UI: Tabler via Django templates; root `templates/` (layouts/, includes/, pages/) — NOT per-app
- DB: SQLite auto en dev, PostgreSQL o MySQL en prod

## Entorno y arranque

- `.env` se auto-genera al arrancar si no existe; `SECRET_KEY` cifrada con Fernet, se descifra en `config/settings.py:309`
- `python manage.py runserver` → desarrollo (DEBUG=True, SQLite, consola email)
- `python manage.py runserver --production` → producción (DEBUG=False, forza validaciones DB/email/LDAP)
- `python manage.py runserver --production` espera `EXTERNAL_HOSTNAME`, `DB_*`, `EMAIL_*` en `.env`

## Setup completo

```bash
source .venv/bin/activate
sudo apt install libcairo2-dev pkg-config python3-dev wkhtmltopdf
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --link --no-input
python manage.py add_stations_data
python manage.py createsuperuser
```

- Iniciar el worker de correos (Huey):
  ```bash
  ./run_huey.sh &
  ```
  Sin este worker los correos se encolan pero nunca se envían.

## Comandos custom

- `python manage.py add_stations_data` — carga inicial de estaciones
- `python manage.py import_ldap_users` — importa usuarios desde LDAP

## Testing

136 tests en 6 apps (common, accounts, dashboard, api, home, login). Ejecutar con:
```bash
python manage.py test
```

## Apps y rutas clave

| App | Responsabilidad |
|---|---|
| `config/` | settings, urls root, wsgi/asgi, email backend |
| `api/` | REST endpoints: `/api/doc/`, `/api/redoc/`, stations, observations, forecasts |
| `accounts/` | Users, groups, profiles, LDAP auth (`ldap3_backend.LDAP3Backend`) |
| `dashboard/` | Admin CRUD: pronósticos, avisos, clientes, servicios, facturación, publicaciones |
| `home/` | Páginas públicas: tiempo, modelos, satélites, servicios, institucion |
| `login/` | Login/logout |
| `common/` | `FileHandlerMixin`, `utils.py`, error views (400/403/404/500) |
| `spec/` | Planificación SDD: `features/NNN-nombre/` con `{spec,plan,tasks}.md`. Una feature puede crear una app nueva o modificar existentes. |

## Modelos clave

- `Forecasts` — pronóstico detallado con 3 regiones (north/interior/south) + 5 días extendido + luna/sol/UV
- `EarlyWarning`, `TropicalCyclone`, `StormWarning` — avisos con PDF (heredan `BaseWarning`)
- `WeatherToday`, `WeatherTomorrow`, `WeatherCommentary`, `WeatherNote` — reportes meteorológicos con PDF
- `Customer`, `Service`, `ServiceSubscription`, `Contract`, `Invoice`, `InvoiceItem`, `Certificate` — gestión comercial
- `ScientificPublication`, `Author` — publicaciones científicas
- `SiteConfiguration` — maintenance mode flag
- `CompanySettings` — datos fiscales de la empresa (singleton, pk=1)

## Permisos

Todos los modelos del dashboard usan `default_permissions = ()` + 4 permisos custom: `view_*`, `add_*`, `change_*`, `delete_*`. NO asumas que `add`/`change`/`delete`/`view` existen por defecto.

## Middleware (orden en settings.py)

1. `accounts.middleware.check_user_profile.CheckUserProfileMiddleware`
2. `dashboard.middleware.maintenance_mode.MaintenanceModeMiddleware` — bloquea no-superusers excepto `/login/` cuando `maintenance_mode=True`

## Auth

- LDAP opcional via `accounts.ldap3_backend.LDAP3Backend`; se activa si `LDAP_SERVER_URI` está en `.env`
- Fallback a `django.contrib.auth.backends.ModelBackend`
- `Profile` se crea por señal `post_save` de `User`; usuarios LDAP se marcan con `is_ldap=True`

## Convenciones

- **Idioma**: todo el contenido de UI/admin está en español (`es-mx`, `America/Havana`)
- **UUIDs**: todos los modelos expuestos usan `uuid.UUIDField` como identificador en URLs
- **Archivos**: `FileHandlerMixin` para limpieza automática al actualizar/eliminar; rutas `pdf_upload_path` / `image_upload_path`
- **Estáticos**: `static/` (desarrollo), `staticfiles/` (producción con WhiteNoise `CompressedManifestStaticFilesStorage`)
- **Migrations**: NO están en el repo (excluidas en `.gitignore`); ejecutar `makemigrations` siempre en setup
- **Spec-Driven Development**: toda modificación (nueva app, corrección, adición, refactor, UI, infraestructura) sigue este flujo sin excepción. Si el usuario pide un cambio sin pasar por este flujo, completar las preguntas de la sección "Si el usuario pide un cambio..." antes de escribir código.

  1. Crear `spec/features/NNN-nombre/` (siguiente número libre).
  2. Escribir `spec.md`: qué hace la feature y criterios de aceptación.
  3. Escribir `plan.md`: enfoque técnico, detallando qué app(s) crea o modifica.
  4. Desglosar en `tasks.md` con referencias a archivos concretos.
  5. **Escribir código** siguiendo el plan.
  6. **Migraciones** — si hay cambios de modelo:
     ```bash
     python manage.py makemigrations
     ```
  7. **Verificar** siempre:
     ```bash
     python manage.py check && python manage.py test
     ```
  8. **Revisar código** — aplicar items del checklist según lo modificado (ver más abajo).
  9. **Actualizar** `constitution/roadmap.md` moviendo la feature a "Hecho".
  10. **Commit** con mensaje descriptivo (incluir número y nombre de la feature).

  Si el plan crea una app nueva, seguir el patrón de apps existentes (ver tabla).

  Si el usuario pide un cambio sin pasar por este flujo, preguntar antes de codificar:

  ```
  - ¿Qué tipo de cambio es? (feature nueva, corrección, refactor, infraestructura)
  - ¿Afecta a una app existente o requiere una nueva?
    - Si es nueva app: ¿nombre tentativo? ¿Qué modelos, vistas y templates incluye?
    - Si es app existente: ¿cuál(es)? ¿qué archivos/contenido se modifica?
  - ¿Tiene cambios de base de datos? (nuevos modelos, campos, migraciones)
  - ¿Afecta URLs, API endpoints o permisos?
  - ¿Afecta templates? (nuevos páginas/includes, o cambios en existentes)
  - ¿Cuáles son los criterios de aceptación? (qué debe funcionar al terminar)
  - Número de feature en spec/features/ (si aplica, o se asigna el siguiente)
  ```

  Completar spec.md / plan.md / tasks.md con esas respuestas antes de tocar código.

## Checklist de revisión

  Aplicar solo los items relevantes al tipo de cambio realizado:

### Modelos
- [ ] `__str__` y `Meta.ordering` definidos
- [ ] `Meta.permissions` idioma español (`view_*`, `add_*`, `change_*`, `delete_*`)
- [ ] `unique_together` / `constraints` si hay relaciones 1-1
- [ ] Soft delete: filtrar `record_active` en queries internas
- [ ] FileField/ImageField: `upload_to` con `pdf_upload_path`/`image_upload_path`

### Vistas (Dashboard)
- [ ] `LoginRequiredMixin` + `PermissionRequiredMixin` con permiso correcto
- [ ] `queryset` a nivel de clase con `timezone.now()`? → usar `get_queryset()`
- [ ] `select_related`/`prefetch_related` para evitar N+1 en list/detail
- [ ] Conteos derivados con resta (`total - activo = expirado`)? → query explícita
- [ ] Ventanas de tiempo consistentes (días sueltos vs meses calendario)
- [ ] `paginate_by = 20` en ListViews

### API
- [ ] `get_queryset()` filtra por vigencia con `timezone.now()` (no class attr)
- [ ] Sin `__all__` ni `fields` que expongan campos sensibles
- [ ] Paginación y rate limiting aplican automáticamente

### Templates
- [ ] `csrf_token` en todo `<form>` (excepto GET)
- [ ] `enctype="multipart/form-data"` si hay input type=file
- [ ] IDs de campos únicos si JS (Litepicker, forecast.js) depende de ellos
- [ ] Sin `|safe` en datos ingresados por usuarios no confiables
- [ ] URLs generadas con `{% url %}` (no hardcodeadas)

### JavaScript / Estáticos
- [ ] URLs obtenidas de atributos `data-*` (no hardcodeadas en JS)
- [ ] Manejo de errores en llamadas AJAX (callback error/fail)
- [ ] `python manage.py collectstatic --link --no-input` si se agregó/modificó archivo en `static/`

### URLs
- [ ] Kwarg `uuid` (no `pk`) para modelos con UUIDField
- [ ] Nombres de ruta únicos y descriptivos

### Seguridad
- [ ] Vistas requieren permiso específico (no solo login)
- [ ] Formularios: `fields` explícito (no `exclude` ni `__all__` si hay campos sensibles)
- [ ] Mass assignment prevenido: ModelForms listan campos permitidos

## API

- DRF con `DjangoModelPermissionsOrAnonReadOnly` por defecto
- Rate limiting: anon 100/h, user 1000/h
- Schema OpenAPI en `/api/schema/`

## Deploy

- Nginx + Gunicorn (`gunicorn.sh`) + Supervisor
- WSGI: `config.wsgi:application`
- Stats: staticfiles servidos por Nginx en `/static/`, media en `/media/`
- Socket: `/tmp/gunicorn-webcmp.sock`

## Locale

`LANGUAGE_CODE = 'es-mx'`, `TIME_ZONE = 'America/Havana'`
