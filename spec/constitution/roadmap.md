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

## Siguiente 🔜

19. **019 · Exportación CSV/Excel** — botón de exportar en list views.
20. **023 · Model validation** — métodos `clean()` y validadores para modelos clave.
21. **024 · API expansion** — endpoints para avisos, weather reports, publicaciones, servicios.
22. **022 · Dashboard analytics** — gráficos de ingresos, suscripciones, avisos con ApexCharts.
23. **020 · Refactor templates de pronósticos** — descomponer templates en partials reutilizables.
24. **025 · Tareas asíncronas** — Huey/Celery para email y PDF generation.

## Backlog / ideas 💡

- Frontend build pipeline (package.json, bundler, Sass)
- Auth API (JWT, tokens de acceso)
- Traducción EN del portal público
- PWA / service worker
- Notificaciones en tiempo real (WebSockets)

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código.
