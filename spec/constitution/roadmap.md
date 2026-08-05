# Roadmap

## Hecho ✅

1. **001 · Autenticación y usuarios** — login/logout con Django Auth, registro de clientes, gestión de usuarios/grupos/perfiles, LDAP opcional.
2. **002 · Portal público meteorológico** — tiempo hoy/mañana, comentario del tiempo, nota meteorológica, avisos (alertas tempranas, ciclones tropicales, tormentas).
3. **003 · Pronósticos detallados** — CRUD de pronósticos con 3 regiones (norte/interior/sur), 3 períodos, 5 días extendido, datos astronómicos (luna, sol, UV).
4. **004 · Modelos y satélites** — visualización de mapas de modelos numéricos, meteogramas, sondeos, imágenes satelitales con proxy.
5. **005 · Servicios públicos** — listado público de servicios meteorológicos gratuitos.
6. **006 · Servicios comerciales y facturación** — gestión de clientes, servicios comerciales, suscripciones (con soft delete), contratos, facturación con items e invoice PDF, certificados.
7. **007 · Publicaciones científicas** — gestión de autores y publicaciones con PDF y coautores.
8. **008 · API REST** — endpoints públicos para estaciones, observaciones y pronósticos con drf-spectacular (Swagger/Redoc).
9. **009 · Configuración del sitio** — modo mantenimiento (bloquea no-superusers), configuración de empresa (datos fiscales singleton), listas de correo.
10. **010 · Infraestructura y deploy** — Nginx + Gunicorn + Supervisor, WhiteNoise para estáticos, entorno dual dev/prod con `.env` auto-generado.
11. **011 · Reemplazar páginas de eliminación por modales** — modal Bootstrap reutilizable en vez de 17 templates de confirmación independientes; vistas DeleteView convertidas a View (POST-only).
12. **012 · Tests automatizados** — 116 tests unitarios y de integración en 6 apps (common, accounts, dashboard, api, home, login) con cobertura de modelos, vistas, formularios, API REST y utilities.
13. **013 · Normalizar pronósticos** — modelos `ForecastRegions` y `ForecastExtendedDay` normalizados; bridge properties/methods en `Forecasts`; comando `migrate_forecast_data`; API y vistas actualizadas; 89 tests total.
14. **014 · Refactor reportes tiempo** — modelo único `WeatherReport` con campo `type`; forms/vistas/URLs genéricas parametrizadas por tipo; 4 templates de detalle creados; URLs detail/PDF para todos los tipos.
15. **015 · PDF templates para reportes** — 4 templates PDF creadas (hoy, mañana, comentario, nota meteorológica) con logo + fecha + resumen + autor.
16. **021 · Eliminar campos planos de Forecasts** — ~60 columnas redundantes eliminadas del modelo Forecasts; forms, vistas, templates, API y dashboard actualizados para usar ForecastRegions y ForecastExtendedDay.
17. **016 · Soft delete para modelos comerciales** — `SoftDeleteModel` abstracto en `common/utils.py` con `record_active`, `deleted_at`; aplicado a Customer, Service, Invoice, Contract y Certificate; ServiceSubscription refactorizado para heredar del mixin; vistas de borrado con soft/hard delete dual; modales actualizados.
18. **018 · Vistas de Certificados y Contratos** — vistas CRUD (ListView, CreateView, DetailView, DeleteView), templates con DataTable y modal de borrado, entradas en el menú lateral, URLs en `/dashboard/contratos/` y `/dashboard/certificados/`.
19. **019 · Exportación CSV/Excel** — `CSVExportView` genérico en `common/views.py`, export views para Customer, Service, ServiceSubscription, Invoice, Forecasts, WeatherReport, EarlyWarning, TropicalCyclone, StormWarning; botón "Exportar CSV" en list.html y pronósticos.
20. **023 · Model validation** — `clean()` en ForecastExtendedDay (min_temp < max_temp), ServiceSubscription (start_date < end_date), Invoice (amount > 0), InvoiceItem (cantidad > 0, precio > 0); `full_clean()` en save() de ForecastExtendedDay e InvoiceItem; 5 tests nuevos.
21. **024 · API expansion** — 6 nuevos endpoints públicos (avisos, weather reports, publicaciones, servicios); filtros por activos/vigentes; serializers, views y tests (133 total).
22. **022 · Dashboard analytics** — 2 charts (ingresos + suscripciones), KPIs (clientes nuevos, avisos activos), queries optimizadas en DashboardView, 136 tests.
23. **020 · Refactor templates de pronósticos** — templates crear/actualizar unificados en `form_pronostico.html` con 3 partials reutilizables (`region_fields.html`, `extended_day.html`, `astro_fields.html`). Fix de Excel upload: se agregaron `region`, `period`, `day_number`, `date` faltantes en JSON. URL dinámica vía `data-upload-url`. Bugs corregidos: `timezone.now()` en class-level `queryset` de API (→ `get_queryset()`), conteo de suscripciones expiradas (query explícita en vez de `total - active`), ventana de ingresos (días → meses calendario). Flujo SDD mejorado con checklist de revisión en AGENTS.md.
24. **026 · Mejoras UI pronósticos** — tablas vacías con headers y mensaje "No hay datos" cuando no hay pronósticos; botones de acción (CSV, Excel, Editar, Eliminar) como `btn-icon` cuadrados solo icono con tooltips; botones editar/eliminar movidos a header; "Añadir" solo cuando no hay datos; layout responsivo para móvil en formulario de pronóstico extendido.
25. **025 · Tareas asíncronas** — Huey + SqliteHuey configurado; `send_email_task` para envío de correos asíncrono; `generate_invoice_pdf_and_email_task` para generación de PDF de factura + email; `mail_send()` refactorizado manteniendo mensajes UI sincrónicos; PDF de facturación extraído a función standalone en `utils.py`.
26. **027 · Limpieza de código (hallazgos de revisión)** — `huey.db` agregado a `.gitignore`; imports no usados (`Invoice`, `Service`, `ServiceSubscription`, `StormWarning`) removidos de `dashboard/tests/test_views.py`; 10 llamadas `.filter(pk=1).update(maintenance_mode=False)` redundantes removidas en 3 archivos de test.
27. **028 · Refactor CSV exports** — botón CSV en `list.html` unificado a `btn-icon btn-outline-success btn-sm` con tooltip; eliminados 4 CSV exports de metadatos (WeatherReport, EarlyWarning, TropicalCyclone, StormWarning); agregados 3 CSV exports con valor real (Contract, Certificate, EmailRecipientList) con sus URLs y contextos en ListViews.
28. **029 · Newsletter en Profile** — campo `newsletter` movido de Customer a Profile; señales de sincronización automática con EmailRecipientList; data migration; checkbox en formularios de usuario y perfil.
29. **030 · Mejoras al workflow** — AGENTS.md documentado con worker Huey, testing selectivo, política de creación de tests, checklist de seguridad post-cambio.
30. **031 · Seguridad XSS en dashboard** — `html.escape()` en `serialize_sub()`, `escapeHtml()` en JS del dashboard, `except:` → `except (AttributeError, TypeError):` en my_filters.py.
31. **032 · Refactor dashboard template** — `dashboard.html` reducido de 1667 a ~418 líneas; 5 includes en `templates/includes/dashboard/` + `pagination.html`.
32. **033 · Refactor dashboard views** — `views.py` dividido en `dashboard.py`, `excel_json.py`, `maintenance.py`; subqueries y helpers a nivel módulo; `prefetch_related('user_set')` en groups query.
33. **034 · Refactor templatetags** — `my_filters.py` dividido en 4 submódulos (`form_filters`, `meteo_filters`, `perm_filters`, `utils_filters`); `in_group_permissions` eliminado; `id="example"` parametrizado en `list.html`.
34. **035 · Migrar is_staff contextual a request.user.is_staff** — `{% if is_staff %}` reemplazado por `{% if request.user.is_staff %}` en 4 templates; `context['is_staff']` eliminado de 22 vistas; ~42 líneas redundantes removidas.
35. **036 · Externalizar JS del dashboard** — ~310 líneas de JS ApexCharts y ~82 líneas de CSS inline movidas a `static/dist/js/dashboard.js` y `static/dist/css/dashboard.css`; datos pasados via `data-*` attributes en los divs de charts; dashboard.html reducido a 22 líneas.
36. **037 · Serialización consistente de charts** — todas las series de datos ApexCharts envueltas con `json.dumps()` en lugar de `str()` para consistencia y prevención de bugs con strings.
37. **038 · Anidar bloque duplicado** — los dos `{% if show_commercial and not is_client %}` unificados en `resumen_comercial.html`, modal anidado dentro del primer bloque.
38. **039 · Remover load sin usar** — `{% load my_filters %}` eliminado de `alertas_activas.html` (no usaba ningún filtro).
39. **040 · Fix test_func crashes** — 3 vistas con `test_func` crash corregidas (CustomerRegisterView, ServiceDetailView, InvoiceDetailView).
40. **041 · Model Meta fixes** — `ordering` añadido a modelos faltantes, permisos de Contract corregidos, singletons con `unique` constraint.
41. **042 · Form validation fixes** — unicidad en Customer forms + `record_active` filters en Invoice forms.
42. **043 · Cleanup dead code** — modelos WeatherToday, WeatherCommentary, WeatherNote eliminados; forms, vistas y templates obsoletos limpiados.
43. **044 · Template fixes** — `lang="en"` → `lang="es"` en base.html; rutas estáticas corregidas.
44. **045 · JS fixes** — guard para pdfjsLib, removeEventListener corregido, jQuery `$(document).ready()` reemplazado por DOMContentLoaded.
45. **046 · WeatherReport refactor** — campo `type` renombrado a `report_type`; forms, vistas, templates actualizados.
46. **047 · URL consistency** — trailing slashes añadidos a 2 patrones de delete en accounts/urls.py.
47. **048 · Client type (Persona Natural)** — modelo Customer con campo `client_type` (natural/jurídica); campos company_name/reeup/nit opcionales para persona natural; validación condicional en forms público y dashboard; radio toggle + JS en template de registro.
48. **049 · Homepage refactor** — corregir `<spam>` bug, extraer bloques región climática a partial, eliminar hack `invisible`, tooltips redundantes, simplificar SVG UV, `loading="lazy"`, empty states a partial.
49. **050 · XSS safe content** — reemplazar `|safe` en 4 templates por filtro sanitizador que solo permite HTML seguro.
50. **051 · Template fixes auth** — `lang="en"` → `lang="es"` en base-auth.html; `autocomplete` en inputs login.
51. **052 · PDF modal refactor** — extraer modal fullscreen PDF duplicado en 7+ templates a partial reutilizable.
52. **053 · Servicios responsive** — unificar bloques `list-inline-item` duplicados (desktop/mobile) en servicios_comerciales.html y servicios_publicos.html.
53. **054 · Email obfuscation** — ofuscar emails de autores en publicaciones.html para evitar scraping.
54. **055 · Template fixes menor** — `execCommand` → `clipboard` API; `aria-label` en botones PDF; `<figcaption>` huérfano; extraer SVG logo a partial.
55. **056 · Fix bugs críticos templates** — `detailed_forecast`/`detailed_commentary`/`detailed_note` no existen en `WeatherReport` (AttributeError en 3 templates públicas); se agrega campo `content` al modelo; migración; `<spam>` → `<span>` en index.html; `lang="en"` → `lang="es"` en base-auth.html; fix `{% static '' %}`.
56. **057 · Seguridad post-auditoría** — `LoginRequiredMixin` a `ServiceDetailView`; `verify=True` en requests externas; excepciones específicas en delete views; `UserUpdateForm` de `exclude` a `fields`; `get_avatar()` usa `.url`.
57. **058 · Performance y JS** — `select_related` en list views; `.catch()` en fetch calls; URLs API vía `data-*`; `print()` → logging; FontAwesome a Tabler Icons.
58. **060 · URL namespace refactor** — `app_name` añadido a todas las apps; URLs namespaced consistentes en templates y vistas.
59. **069 · Tests comerciales** — 98 tests unitarios y de integración para `apps/commercial/` (modelos, formularios, vistas, tareas Huey); suite completa 233 tests OK.
60. **059 · UI y accesibilidad** — utils.html inline → static files; `aria-label` en icon-links; `<pre>` headings → `<h3>`; SVG `alt=""` → `role="img"`; labels con `for`; limpiar navbar comentado.
61. **061 · Models conventions** — FileHandlerMixin, `Meta.ordering`, `related_name`, UUID en modelos faltantes.
62. **062 · Apps responsibility** — extraer modelos de `dashboard/` a apps especializadas: `apps/geo/` (Province, Town, Station), `apps/crm/` (Customer, Service, ServiceSubscription); `db_table` + `managed=False` para tablas legacy.
63. **063 · Templates y static** — `paginate_by = 20` en ListViews, bloques comentados, accesibilidad.
64. **064 · Tests coverage** — tests faltantes en publications, home, dashboard.
65. **065 · Settings y seguridad** — CORS headers para API REST.
66. **066 · Restructure apps** — migración completa: `core/`, `user_auth/`, `meteo/`, `commercial/`; Warning unificado; templates movidos a cada app; URLs namespaced; migraciones desde cero.
67. **067 · Unify Warning model** — fusionar EarlyWarning, TropicalCyclone, StormWarning en un solo modelo `Warning` con `warning_type`; views parametrizadas; eliminar código duplicado. (Incluido en 066.)
68. **068 · Restructure templates** — mover templates a cada app; reorganizar includes; actualizar `{% url %}`. (Incluido en 066.)
69. **Template polish CRUD (transversal, commits 14f3d1b/b8c2704/4ebd53d)** — templates create/update/detail de meteo, user_auth, core y commercial/publications unificados al patrón de `customer/create.html`: fieldsets con `legend.h4`, `<hr>` entre grupos, grid `row`/`col-md-*`, errores `invalid-feedback d-block`. Bugfixes: formset de `EmailRecipient` con campo `-uuid` (no `-id`) para que edición/borrado hagan round-trip; datetime local en suscripciones (reemplaza `toISOString()` que cambiaba UTC); modal de invoice con API `bootstrap.Modal`; `html_name` en formset de coautores (`BoundField.name` era el nombre sin prefijo y rompía el guardado); value bindings en contract; fecha `d/m/Y` en detail de publicaciones. Tests de regresión añadidos (+7): suite 250 tests OK.
70. **070 · Tests secundarios** — `apps/dashboard/tests/` (acceso staff/cliente, flags de permisos, rangos, KPIs, charts JSON, `serialize_sub` tolera persona natural); `apps/core/tests/test_middleware.py` (`CheckUserProfileMiddleware` + `MaintenanceModeMiddleware`); `apps/core/tests/test_tasks.py` (`send_email_task` vía `call_local` con adjuntos por args y por path); fix `serialize_sub` (crash con `company_name=None`). Suite 278 tests OK.
71. **081 · Pulido templates home** — footer unificado en un solo `<footer>`; `rel="noreferrer"` duplicado eliminado; `document.write` → `{% now 'Y' %}`; wrapper `navbar-nav` anidado removido; bloque comentado de notificaciones eliminado; brand `<h1>` → `<a>`; guard `region_data` en forecast_region_card; rama `{% else %}` con icono por defecto en empty_state. Suite 283+ tests OK.

## Siguiente 🔜

70. **071 · Performance queries** — optimizar queries N+1, agregar `select_related`/`prefetch_related` donde falte. Solo spec.md.
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
