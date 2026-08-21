# Roadmap

## Hecho ✅

### Autenticación y usuarios
- **001 · Autenticación y usuarios** — login/logout con Django Auth, registro de clientes, gestión de usuarios/grupos/perfiles, LDAP opcional.
- **029 · Newsletter en Profile** — campo `newsletter` movido a Profile con sincronización automática a EmailRecipientList; data migration. ⚠️ **Fase 2 pendiente**: registrar señales en `ready()` (nunca se importaron; ver 091).
- **035 · Migrar is_staff contextual** — `{% if is_staff %}` → `{% if request.user.is_staff %}` en templates; `context['is_staff']` eliminado de vistas.
- **040 · Fix test_func crashes** — 3 vistas con `test_func` crash corregidas.
- **048 · Client type** — Customer con `client_type` (natural/jurídica) y validación condicional en forms.
- **051 · Template fixes auth** — `lang="es"` en base-auth; `autocomplete` en login.

### Portal público
- **002 · Portal público meteorológico** — tiempo hoy/mañana, comentario del tiempo, nota meteorológica, avisos (alertas tempranas, ciclones tropicales, tormentas).
- **004 · Modelos y satélites** — mapas de modelos numéricos, meteogramas, sondeos, imágenes satelitales con proxy.
- **049 · Homepage refactor** — fixes de markup (`<spam>`), partials reutilizables, empty states, `loading="lazy"`.
- **053 · Servicios responsive** — bloques desktop/mobile unificados en servicios comerciales y públicos.
- **054 · Email obfuscation** — ofuscar emails de autores en publicaciones.
- **081 · Pulido templates home** — footer unificado, `{% now 'Y' %}` sin document.write, brand `<a>`, empty states.
- **082 · Rediseño páginas públicas home** — páginas de contenido con PDF embebido + partials DRY (spec/plan/tasks listos).

### Pronósticos
- **003 · Pronósticos detallados** — CRUD con 3 regiones × 3 períodos × 5 días extendido + datos astronómicos.
- **013 · Normalizar pronósticos** — `ForecastRegions` y `ForecastExtendedDay` normalizados; bridge en `Forecasts`.
- **020 · Refactor templates de pronósticos** — templates crear/actualizar unificados con partials reutilizables; fix de Excel upload.
- **021 · Eliminar campos planos de Forecasts** — columnas redundantes eliminadas; forms/vistas/templates/API actualizados.
- **023 · Model validation** — `clean()` en ForecastExtendedDay, ServiceSubscription, Invoice, InvoiceItem.
- **026 · Mejoras UI pronósticos** — tablas con empty states, botones `btn-icon` con tooltips, layout responsivo.
- **042 · Form validation fixes** — unicidad en Customer forms + filtros `record_active` en Invoice forms.
- **046 · WeatherReport refactor** — campo `type` → `report_type`; forms, vistas y templates actualizados.
- **014 · Refactor reportes tiempo** — modelo único `WeatherReport` con campo `type`; forms/vistas/URLs parametrizadas; 4 templates de detalle.
- **015 · PDF templates para reportes** — 4 templates PDF con logo + fecha + resumen + autor.
- **043 · Cleanup dead code** — modelos WeatherToday/WeatherCommentary/WeatherNote eliminados; código obsoleto limpiado.

### Servicios comerciales y facturación
- **005 · Servicios públicos** — listado público de servicios meteorológicos gratuitos.
- **006 · Servicios comerciales y facturación** — clientes, servicios, suscripciones (soft delete), contratos, facturación con items e invoice PDF, certificados.
- **016 · Soft delete para modelos comerciales** — `SoftDeleteModel` con `record_active`/`deleted_at` aplicado a Customer, Service, Invoice, Contract, Certificate; vistas dual soft/hard delete. ⚠️ **Fase 2 pendiente**: SoftDeleteManager, cleanup en hard_delete, races (ver 090).
- **018 · Vistas de Certificados y Contratos** — CRUD completo con DataTables y modales de borrado.
- **019 · Exportación CSV/Excel** — `CSVExportView` genérico y exports para los modelos comerciales y pronósticos.
- **028 · Refactor CSV exports** — botón CSV unificado `btn-icon btn-outline-success btn-sm`; exports con valor real (Contract, Certificate, EmailRecipientList).

### Publicaciones
- **007 · Publicaciones científicas** — gestión de autores y publicaciones con PDF y coautores.

### API REST
- **008 · API REST** — endpoints públicos para estaciones, observaciones y pronósticos con drf-spectacular.
- **024 · API expansion** — 6 endpoints nuevos (avisos, weather reports, publicaciones, servicios); filtros por activos/vigentes.

### Configuración del sitio
- **009 · Configuración del sitio** — modo mantenimiento (bloquea no-superusers), configuración de empresa, listas de correo.
- **086 · Modales nativos Tabler y auth de datos de empresa** — modales con data API/Bootstrap.Modal; `CompanySettingsAjaxUpdateView` con permisos reales; fix 405 en vistas de error; normalización de teléfonos.

### Infraestructura y deploy
- **010 · Infraestructura y deploy** — Nginx + Gunicorn + Supervisor, WhiteNoise, entorno dual dev/prod con `.env` auto-generado.
- **083 · Automatización de dependencias y CI/CD** — CI completo (tests + Ruff + pip-audit + migraciones-check), Dependabot con auto-merge, `pyproject.toml` (Ruff), `requirements-dev.txt`, `.pre-commit-config.yaml`, `SECURITY.md`. ⚠️ **Fase E pendiente**: Django sigue en 5.1.4 (la prometida 5.2.16 no se aplicó); fijar deps con `==` (ver 093).

### Templates y UI
- **011 · Modales de confirmación** — modal Bootstrap reutilizable en vez de templates de eliminación independientes.
- **032 · Refactor dashboard template** — `dashboard.html` reducido a includes en `templates/includes/dashboard/`.
- **033 · Refactor dashboard views** — `views.py` dividido en `dashboard.py`, `excel_json.py`, `maintenance.py`.
- **034 · Refactor templatetags** — `my_filters.py` dividido en submódulos (`form_filters`, `meteo_filters`, `perm_filters`, `utils_filters`).
- **036 · Externalizar JS del dashboard** — ApexCharts a `static/dist/js/dashboard.js`; datos vía `data-*`.
- **037 · Serialización consistente de charts** — series envueltas con `json.dumps()`.
- **044 · Template fixes** — `lang="es"` en base; rutas estáticas corregidas.
- **045 · JS fixes** — guard para pdfjsLib, removeEventListener corregido, DOMContentLoaded.
- **052 · PDF modal refactor** — modal fullscreen PDF extraído a partial reutilizable.
- **055 · Template fixes menor** — clipboard API, `aria-label` en PDF, `<figcaption>` huérfano, logo SVG a partial.
- **056 · Fix bugs críticos templates** — `content` agregado a WeatherReport (AttributeError en templates públicas).
- **059 · UI y accesibilidad** — `aria-label` en icon-links, headings, `role="img"`, labels con `for`.
- **060 · URL namespace refactor** — `app_name` en todas las apps; URLs namespaced consistentes.
- **063 · Templates y static** — `paginate_by = 20`, bloques comentados, accesibilidad.
- **068 · Restructure templates** — templates movidos a cada app; includes reorganizados.
- **084 · Formato de templates con djlint** — templates reindentados a 2 espacios; hooks djlint en pre-commit.
- **085 · Iconos Tabler (webfont `ti`)** — SVG inline sustituidos por `<i class="icon ti ti-*">`; `get_icon_for_action` a webfont.
- **087 · Formularios en cards por sección** — `layouts/form.html` rediseñado con `row row-cards`; partial `form_card.html`; 46 templates migrados.

### Dashboard
- **022 · Dashboard analytics** — 2 charts (ingresos + suscripciones), KPIs, queries optimizadas.
- **038 · Anidar bloque duplicado** — bloques `show_commercial` unificados en `resumen_comercial.html`.
- **039 · Remover load sin usar** — `{% load my_filters %}` eliminado donde no aplicaba.

### Tareas asíncronas
- **025 · Tareas asíncronas** — Huey + SqliteHuey; `send_email_task` y `generate_invoice_pdf_and_email_task`; `mail_send()` refactorizado. ⚠️ **Fase 2 pendiente**: registrar tasks en `ready()` (huey_consumer ve 0 tareas; ver 089).

### Tests
- **012 · Tests automatizados** — suite base de unit e integración.
- **064 · Tests coverage** — tests faltantes en publications, home, dashboard.
- **069 · Tests comerciales** — 98 tests para `apps/commercial/` (modelos, forms, vistas, tareas Huey).
- **070 · Tests secundarios** — dashboard, core middleware, core tasks; fix `serialize_sub`.

### Seguridad
- **031 · Seguridad XSS en dashboard** — `html.escape()` en `serialize_sub`, `escapeHtml()` en JS.
- **050 · XSS safe content** — `|safe` reemplazado por filtro sanitizador.
- **057 · Seguridad post-auditoría** — `LoginRequiredMixin`, `verify=True` en requests, excepciones específicas.
- **065 · Settings y seguridad** — CORS headers para API REST. ⚠️ **Fase 2 pendiente**: rate limiting real (throttle classes; ver 088).
- **088 · Seguridad crítica** — credenciales FTP movidas a `.env` + rotación manual documentada, rate limiting real (throttle classes + anon 100/h), auth en endpoints expuestos (ExcelJSON con login+permiso, ajax_pending_subscriptions con login+permiso+ownership, proxys de imagen con rate limit IP), fix ASGI (`'config.settings'`), open redirect saneado en login, backend de correo custom cableado para certificado autofirmado, `generate_env.py` interactivo (prod/dev + valores reales).
- **089 · Operación en producción** — `whitenoise`/`gunicorn` en requirements (pinneados), `SECURE_PROXY_SSL_HEADER` + políticas modernas (referrer/coop) y eliminado `SECURE_BROWSER_XSS_FILTER` deprecado, tasks Huey registradas en `CoreConfig.ready()`, `DEBUG` default `False` + `get_database_config()` fail-closed (DB obligatoria en prod, fallback SQLite en dev), `gunicorn.sh`/`README` sin root (usuario `webcmp`), tests de configuración de producción.

### Performance
- **058 · Performance y JS** — `select_related` en list views, `.catch()` en fetch, `print()` → logging, FontAwesome a Tabler Icons.

### Estructura de apps
- **062 · Apps responsibility** — modelos extraídos de `dashboard/` a apps especializadas (Province/Town/Station a meteo; Customer/Service a commercial).
- **066 · Restructure apps** — migración a `core/`, `user_auth/`, `meteo/`, `commercial/`; Warning unificado; templates por app.
- **067 · Unify Warning model** — EarlyWarning/TropicalCyclone/StormWarning fusionados en `Warning` con `warning_type`. ⚠️ **Fase 2 pendiente**: Warning con soft delete (ver 090).

## Siguiente 🔜

70. **071 · Performance queries** — optimizar queries N+1, agregar `select_related`/`prefetch_related` donde falte. Spec + tasks.md (fase 2: API N+1, paginación, context processor, índices).
71. **072 · Dark mode** — implementar alternador claro/oscuro persistente con Tabler. Solo spec.md.
72. **073 · UI polish** — refinamientos visuales: espaciado, tipografía, estados vacíos, micro-interacciones. Solo spec.md.
73. **074 · Redis cache** — integrar Redis para caché de consultas frecuentes y sesiones. Solo spec.md.
74. **075 · Monitoreo de tareas** — panel de monitoreo para cola Huey: tareas pendientes, fallidas, tiempos de ejecución. Solo spec.md.
75. **076 · Auditoría de actividad** — registro de actividad de usuarios (login, CRUD, exportaciones) con filtros y búsqueda. Solo spec.md.
76. **077 · Operaciones masivas** — acciones en lote en listados (exportar, eliminar, cambiar estado). Solo spec.md.
77. **078 · Tema personalizado** — personalización visual: colores de marca, logo, favicon desde admin. Solo spec.md.
78. **079 · Exportar gráficos** — botón de descarga PNG/PDF para gráficos ApexCharts del dashboard. Solo spec.md.
79. **080 · Debug Toolbar** — Django Debug Toolbar en entorno de desarrollo. Solo spec.md.
80. **082 · Rediseño páginas públicas home** — páginas de contenido (tiempo, comentario, nota, avisos, publicaciones) como documentos con PDF embebido + partials DRY (pdf_scripts, weather_article, paginación Tabler, campos UTC). Spec/plan/tasks listos.

### 🔒 Bloque auditoría 2026 (nuevas)

- **090 · Soft delete e integridad** — `SoftDeleteManager` (filtra `record_active`), cleanup de archivos en `hard_delete()`, Warning con soft delete, race conditions (facturas, SiteConfiguration singleton).
- **091 · Newsletter signals wiring** — registrar señales de newsletter en `ready()`, unicidad `EmailRecipient`, tests de sync.
- **092 · Performance y paginación** — N+1 en serializers API (Prefetch), paginación real en listados, índices, cache en context processor, templatetags.
- **093 · Deps y docs alineadas** — fijar versiones (`==`), decidir Django 5.1.4 vs 5.2, alinear `env.sample`/`generate_env`, choices unificados.

## Backlog / ideas 💡

### 🔴 Seguridad

- **Content Security Policy (CSP)** — Cabeceras HTTP para prevenir XSS y exfiltración de datos. Usar `django-csp` o middleware manual.
- **Proxy SSL y cabeceras de seguridad** — Configurar `SECURE_PROXY_SSL_HEADER`, `SECURE_REFERRER_POLICY`, `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY` explícitos. Sin proxy SSL header, Django detrás de Nginx rompe cookies seguras.
- **2FA / MFA para usuarios admin** — Autenticación de dos factores con `django-otp` o `django-two-factor-auth` para staff y superusuarios del dashboard.
- **Validación de archivos subidos** — Magic bytes, extensión, tamaño máximo en todos los FileField/ImageField (Service, Invoice, Certificate, Profile.avatar). Actualmente solo `ScientificPublication.pdf` tiene validación.
- **Eliminar `.env` del repositorio** — Los archivos `/.env` y `/apps/.env` contienen credenciales reales. Agregar a `.gitignore`, generar `.env.example` con valores dummy.

### 🟡 Automatización

- **Pre-commit hooks** — Ruff (lint + format), djlint para templates Django, verificación de migraciones.
- **CI/CD con GitHub Actions** — Test suite en cada push/PR, lint, `pip-audit` para vulnerabilidades, typecheck.
- **Health check endpoint** — `/health/` que verifique DB, Redis y Huey worker. Necesario para monitoreo de deploy.
- **Docker Compose para desarrollo** — Postgres, Redis, Mailpit (email de prueba). Elimina dependencias del sistema anfitrión.

### 🟢 Developer Experience

- **Backup automatizado de base de datos** — Script + cron para dump diario SQLite/PostgreSQL con purge de backups viejos.
- **Validación de entorno al startup** — Verificar en `settings.py` que todas las variables obligatorias existen antes de arrancar.
- **Búsqueda global en navbar** — SearchBar que busque en clientes, facturas, servicios, contratos y pronósticos.
- **Loading states / skeletons** — Esqueletos de carga para DataTables, charts del dashboard y tablas de pronósticos.

### 🔵 Evolución

- **Auth API (JWT)** — Tokens JWT para autenticación de API REST sin cookies de sesión. Útil para integraciones externas y apps móviles.
- **Notificaciones en tiempo real (WebSockets)** — Push de alertas meteorológicas y cambios de estado vía Django Channels + Redis.
- **Traducción EN del portal público** — Internacionalización con i18n de Django para audiencia angloparlante.

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código. Al completar, actualizar `spec/constitution/roadmap.md` moviendo la feature a Hecho antes de empezar la siguiente.
