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
28. **031 · Seguridad XSS en dashboard** — `html.escape()` en `serialize_sub()`, `escapeHtml()` en JS del dashboard, `except:` → `except (AttributeError, TypeError):` en my_filters.py.
29. **032 · Refactor dashboard template** — `dashboard.html` reducido de 1667 a ~418 líneas; 5 includes en `templates/includes/dashboard/` + `pagination.html`.
30. **033 · Refactor dashboard views** — `views.py` dividido en `dashboard.py`, `excel_json.py`, `maintenance.py`; subqueries y helpers a nivel módulo; `prefetch_related('user_set')` en groups query.
31. **034 · Refactor templatetags** — `my_filters.py` dividido en 4 submódulos (`form_filters`, `meteo_filters`, `perm_filters`, `utils_filters`); `in_group_permissions` eliminado; `id="example"` parametrizado en `list.html`.
32. **035 · Migrar is_staff contextual a request.user.is_staff** — `{% if is_staff %}` reemplazado por `{% if request.user.is_staff %}` en 4 templates; `context['is_staff']` eliminado de 22 vistas; ~42 líneas redundantes removidas.
33. **036 · Externalizar JS del dashboard** — ~310 líneas de JS ApexCharts y ~82 líneas de CSS inline movidas a `static/dist/js/dashboard.js` y `static/dist/css/dashboard.css`; datos pasados via `data-*` attributes en los divs de charts; dashboard.html reducido a 22 líneas.

## Siguiente 🔜

*(ninguno — backlog)*

## Backlog / ideas 💡

- Frontend build pipeline (package.json, bundler, Sass)
- Auth API (JWT, tokens de acceso)
- Traducción EN del portal público
- PWA / service worker
- Notificaciones en tiempo real (WebSockets)

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código.
