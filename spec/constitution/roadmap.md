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

## Siguiente 🔜

*(ninguno — backlog)*

## Backlog / ideas 💡

- Frontend build pipeline (package.json, bundler, Sass)
- Auth API (JWT, tokens de acceso)
- Traducción EN del portal público
- PWA / service worker
- Notificaciones en tiempo real (WebSockets)

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código.
