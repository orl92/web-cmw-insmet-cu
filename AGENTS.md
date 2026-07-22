# AGENTS.md — Centro Meteorológico Provincial Camagüey

## Stack

Django 5.2 + DRF + drf-spectacular (OpenAPI), Python 3.8+. Virtual env `.venv/`. UI: Tabler via templates raíz (`templates/` con layouts/ includes/ pages/). DB: SQLite dev, PostgreSQL/MySQL prod. Apps dentro de `apps/`.

## Comandos

```bash
source .venv/bin/activate
pip install -r requirements.txt && python manage.py makemigrations migrate
python manage.py collectstatic --link --no-input add_stations_data createsuperuser
python manage.py runserver                    # desarrollo
python manage.py runserver --production       # producción local
python manage.py test <app>                   # testing selectivo
python manage.py test                         # full suite (antes de commit)
./run_huey.sh &                               # worker de correos/PDF (Huey)
```

## Apps + Modelos

| App | Responsabilidad |
|---|---|
| `config/` | settings, urls root, wsgi/asgi, email backend, Huey |
| `apps/api/` | REST endpoints: `/api/doc/`, `/api/redoc/`, stations, observations, forecasts |
| `apps/accounts/` | Users, groups, profiles, LDAP auth (`LDAP3Backend`) |
| `apps/dashboard/` | Admin CRUD: pronósticos, avisos, clientes, servicios, facturación |
| `apps/publications/` | ScientificPublication, Author — publicaciones científicas |
| `apps/home/` | Páginas públicas: tiempo, modelos, satélites, servicios, institucion |
| `apps/login/` | Login/logout |
| `apps/common/` | `FileHandlerMixin`, `utils.py`, error views (400/403/404/500) |
| `spec/` | SDD features en `features/NNN-nombre/` con `{spec,plan,tasks}.md` |

Modelos clave: `Forecasts` (3 regiones × 3 períodos + 5 días + astronomía), `BaseWarning` (abstracta → `EarlyWarning`/`TropicalCyclone`/`StormWarning`), `WeatherReport` (today/tomorrow/commentary/note), `Customer`, `Service`, `ServiceSubscription` (soft delete), `Contract`, `Invoice`/`InvoiceItem`, `Certificate`, `ScientificPublication`/`Author`, `SiteConfiguration`, `CompanySettings`.

## Convenciones

- **Permisos**: `default_permissions = ()` + 4 custom: `view_*`, `add_*`, `change_*`, `delete_*` (en español). NO asumas que existen por defecto.
- **Middleware**: `CheckUserProfileMiddleware` → `MaintenanceModeMiddleware` (bloquea no-superusers excepto `/login/`)
- **Auth**: LDAP opcional (`LDAP3Backend`) → fallback `ModelBackend`; Profile se crea por señal `post_save`; usuarios LDAP con `is_ldap=True`
- **UUIDs** en URLs de modelos expuestos (no `pk`)
- **FileHandlerMixin** para limpieza automática de archivos al actualizar/eliminar
- **Soft delete**: filtrar `record_active=True` en queries internas
- **Migrations** NO versionadas (`.gitignore`)
- **Estáticos**: `static/` dev, `staticfiles/` prod con WhiteNoise
- **Idioma**: español (`es-mx`, `America/Havana`)
- **Tema**: Tabler (Bootstrap 5), iconos meteorológicos PNG en `static/dist/img/weather_icon/`
- **URLs**: toda app con URLs usa `app_name` en urls.py y names estandarizados (`app_name:list`, `create`, `detail`, `update`, `delete`, `pdf`). Templates usan `{% url 'app_name:name' %}`, vistas usan `reverse_lazy('app_name:name')`.
- **Apps**: todas las apps Django viven en `apps/`. Importar como `from apps.dashboard.models import ...`, nunca como `from dashboard.models import ...`.

## Skills

Carga el skill que corresponda según la tarea. Los skills están en `~/.agents/skills/`.

### Meta
- `using-agent-skills` — árbol de decisión completo para descubrir qué skill aplicar

### Lifecycle mapping (intent → skill)

```
Task arrives →
  ├── No sabes qué quieres? ──────── interview-me
  ├── Concepto vago? ────────────── idea-refine
  ├── Feature nueva / cambio? ───── spec-driven-development
  ├── Spec lista, falta plan? ───── planning-and-task-breakdown
  ├── Implementar código? ───────── incremental-implementation
  │   ├── UI/frontend? ─────────── frontend-ui-engineering
  │   ├── API/interfaz? ────────── api-and-interface-design
  │   ├── Duda técnica? ────────── doubt-driven-development
  │   └── Documentación oficial? ─ source-driven-development
  ├── Tests? ────────────────────── test-driven-development
  │   └── Browser testing? ─────── browser-testing-with-devtools
  ├── Bug / error? ──────────────── debugging-and-error-recovery
  ├── Code review? ──────────────── code-review-and-quality
  │   ├── Muy complejo? ───────── code-simplification
  │   ├── Seguridad? ──────────── security-and-hardening
  │   └── Performance? ────────── performance-optimization
  ├── Commit / branch? ──────────── git-workflow-and-versioning
  ├── CI/CD? ────────────────────── ci-cd-and-automation
  ├── Migrar / sunset? ──────────── deprecation-and-migration
  ├── Docs / ADRs? ──────────────── documentation-and-adrs
  ├── Telemetría / logs? ────────── observability-and-instrumentation
  └── Deploy? ───────────────────── shipping-and-launch
```

### Skills complementarias del proyecto
- `django-expert` — modelos, ORM, DRF, auth, tests, performance Django
- `frontend-design` — diseño visual con identidad
- `web-design-guidelines` — auditoría de accesibilidad y UI
- `project-structure-audit` — auditoría de estructura del proyecto contra estándares Django y convenciones locales; genera reporte en `spec/audits/`

### MCP
- `tabler` — búsqueda de iconos, componentes, layouts, colores y documentación de Tabler.io

## Flujo SDD

Cada feature sigue este flujo usando los skills:

1. Cargar `spec-driven-development` → escribir `spec/features/NNN-nombre/spec.md`
2. Cargar `planning-and-task-breakdown` → escribir `plan.md` + `tasks.md`
3. Cargar `incremental-implementation` → implementar un task a la vez
4. Si hay cambios de modelo: `python manage.py makemigrations`
5. Verificar: `python manage.py check && python manage.py test <app>`
6. Si no existe test para el cambio, crearlo
7. Actualizar `constitution/roadmap.md` moviendo la feature a "Hecho"
8. Commit descriptivo (incluir número y nombre de la feature)

Antes de codificar, si hace falta clarificar, preguntar: ¿tipo de cambio? ¿app(s) afectada(s)? ¿cambios de DB? ¿URLs/permisos? ¿templates? ¿criterios de aceptación? ¿número de feature?

## Checklist proyecto-específico

Estos items NO los cubren los skills genéricos. Verificarlos siempre:

- [ ] `default_permissions = ()` + 4 permisos custom (view/add/change/delete) en español
- [ ] Kwarg `uuid` (no `pk`) en URLs de modelos con UUIDField
- [ ] FileHandlerMixin + `file_fields` definido si hay FileField/ImageField
- [ ] Soft delete: filtrar `record_active=True` (usa el manager por defecto, no `all_objects`)
- [ ] `get_queryset()` con `timezone.now()` (nunca queryset a nivel de clase con fechas)
- [ ] Tareas/imports Huey registrados en `AppConfig.ready()`
- [ ] `paginate_by = 20` en ListViews del dashboard
- [ ] Migraciones ejecutadas y NO versionadas (`.gitignore`)

## API + Deploy + Locale

- **API**: DRF con `DjangoModelPermissionsOrAnonReadOnly`; rate limit 100/h anon, 1000/h user; schema en `/api/schema/`
- **Deploy**: Nginx + Gunicorn (`gunicorn.sh`) + Supervisor; estáticos por Nginx en `/static/`, media en `/media/`; socket `/tmp/gunicorn-webcmp.sock`
- **Locale**: `LANGUAGE_CODE = 'es-mx'`, `TIME_ZONE = 'America/Havana'`
