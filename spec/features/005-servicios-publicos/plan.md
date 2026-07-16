# 005 · Servicios públicos — Plan

## Enfoque

Modelo `Service` con campo `service_type` (public/commercial). Vista pública `PublicServicesListView` filtrada por tipo público con paginación. Dashboard CRUD con validación condicional de campos según tipo.

## Implementación

1. **Modelo**: `Service` con `FileHandlerMixin`, campos `title`, `summary`, `service_type`, `pdf` (FileField), `image` (ImageField), `code`, `price`. `file_fields = ['pdf', 'image']`.
2. **Público**: `PublicServicesListView` en `home/views/servicios/publicos/views.py` — filtro `service_type='public'`, paginación 10, template con visor PDF.js modal.
3. **Dashboard**: `ServiceListView`, `ServiceCreateView`, `ServiceUpdateView`, `ServiceDeleteView` en `dashboard/views/servicios/views.py`. Formulario `ServiceForm` con validación condicional.

## Decisiones

- **Servicio único polimórfico** — un solo modelo con `service_type` evita tablas duplicadas; la validación condicional en el form maneja required fields distintos.
- **PDF.js para visor** — liviano, sin dependencias npm, incluido en Tabler.

## Riesgos

- **Archivos pesados** — PDFs grandes pueden ralentizar la carga; se delega en `FileHandlerMixin` para limpieza.
