# Tasks: servicios-activacion-filtro-home

> Filtro por estado en home + reactivación desde listado + bloqueo de tipo en edición + layout de cards y listado.

## Fase 1 — Filtro por estado en el home

- [x] 1.1 `apps/home/views/servicios/publicos/views.py`: `PublicServicesListView` filtra `record_active=True`.
- [x] 1.2 `apps/home/views/servicios/comerciales/views.py`: `PublicCommercialServicesListView` filtra `record_active=True`; `ServiceDetailView.dispatch` lo incluye en `get_object_or_404`; `related_services` lo filtra también.
- [x] 1.3 Test: servicio público/comercial con `record_active=False` no aparece en listas públicas; detail de inactivo → 404.

## Fase 2 — Reactivación desde el listado

- [x] 2.1 `apps/commercial/views/services.py`: nueva `ServiceReactivateView` (permiso `change_service`; `record_active=True` + `deleted_at=None`; warning si ya estaba activo; log + message).
- [x] 2.2 `apps/commercial/urls.py`: `servicio_reactivate`.
- [x] 2.3 `list.html`: botón verde "Reactivar" solo si `not record_active` y permiso; branch `reactivar` en el JS del modal.
- [x] 2.4 Tests: reactiva (campos), no-op si activo, permiso/redirect.

## Fase 3 — Bloqueo de tipo en edición

- [x] 3.1 `update.html`: select `service_type` disabled + hidden input con `form.service_type.value` + hint.
- [x] 3.2 `apps/commercial/views/services.py`: `ServiceUpdateView.post()` reasigna `request.POST` forzando `service_type` al valor del objeto; eliminar la lógica `old_type/new_type` que limpiaba pdf.
- [x] 3.3 Tests: GET muestra select disabled + hidden; POST manipulado conserva el tipo original; ajustar tests existentes si dependían del cambio de tipo.

## Fase 4 — Layout cards PDF/imagen y listado de públicos

- [x] 4.1 `create.html` y `update.html`: `card h-100` en `field_pdf` y `field_image`.
- [x] 4.2 `list.html`: públicos muestran `<span class="text-muted">—</span>` en Precio y Suscripciones; comerciales intactos.
- [x] 4.3 Tests: cards con `h-100`; listado render para público (`—` sin `$` ni número) y comercial (`$` + conteo).

## Fase 5 — Verificación y limpieza

- [x] 5.1 `python manage.py check && python manage.py test apps.commercial apps.home` — suite verde (incluye invariantes fslightbox/pdf).
- [x] 5.2 `djlint apps/commercial/templates/pages/commercial/service/ --reformat --check --lint` y `ruff check` sobre vistas/tests tocados.
- [x] 5.3 Marcar tasks `[x]` y confirmar diff sin archivos fuera de alcance.