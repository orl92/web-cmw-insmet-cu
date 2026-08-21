# Roadmap

## Activas (pendientes)

- **071 · Performance queries** — eliminar N+1 (`select_related`/`prefetch_related`, índices `db_index`, API con `Prefetch`, paginación real, cache de context processor).
- **073 · UI polish** — toasts unificados en todas las vistas, spinners de carga, tablas responsivas.
- **074 · Redis cache** — Redis + `CACHES` con fallback LocMemCache para queries y fragments.
- **075 · Monitoreo de tareas** — panel de monitoreo de cola Huey (djhuey, traceback de fallos, alerta >5min).
- **076 · Auditoría de actividad** — modelo `ActivityLog` + middleware + vista de log para superusers.
- **077 · Operaciones masivas** — acciones en lote en listados comerciales (ZIP de certificados, impresión).
- **078 · Tema personalizado** — paleta de marca, dark mode adaptado, logo/favicon del CMP.
- **079 · Exportar gráficos** — botón PNG por chart ApexCharts del dashboard.
- **080 · Debug Toolbar** — Django Debug Toolbar en desarrollo (solo `DEBUG`).

## Backlog / ideas

- **CSP** — cabeceras de Content Security Policy (django-csp).
- **2FA/MFA** — autenticación de dos factores para staff.
- **Validación de archivos subidos** — magic bytes/extensión/tamaño en FileField/ImageField.
- **Health check endpoint** — `/health/` (DB, Redis, Huey).
- **Búsqueda global en navbar**.
- **Auth API (JWT)** — tokens para integraciones externas.
- **WebSockets / notificaciones en tiempo real**.
- **i18n EN del portal público**.

> Las features activas viven en `openspec/changes/` como cambios OpenSpec. Al completar una, se marcan sus `tasks.md` y se archiva con `gentle-ai sdd-archive`.
