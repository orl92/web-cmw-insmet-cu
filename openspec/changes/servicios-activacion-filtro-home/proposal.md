# Proposal: Activación de servicios, filtro por estado en home, bloqueo de tipo y mejoras de listado/form

## Intent

Los servicios usan soft delete (`record_active`, `SoftDeleteModel`): desactivar un servicio lo oculta de la gestión pero **hoy sigue apareciendo en el portal público** porque las vistas públicas del home filtran solo por `service_type`, sin `record_active=True`. Además, una vez desactivado **no hay forma de volver a activarlo** desde el dashboard. En el formulario de edición, el tipo (`public`/`commercial`) **se puede cambiar libremente**, lo que obliga a lógica extraña en la vista (limpiar el PDF al pasar a comercial). Y el listado muestra `$0.00` en los públicos, que no tienen precio ni suscripciones.

## Scope

### In Scope
- **Filtro por estado en el home**: `PublicServicesListView`, `PublicCommercialServicesListView` y `ServiceDetailView` (incluidos `related_services`) filtran `record_active=True` — los servicios desactivados no se ven en el portal público.
- **Reactivación desde el listado**: nuevo botón "Reactivar" (verde, solo staff con permiso `change_service`), visible cuando `record_active` es falso; modal de confirmación; nueva vista `ServiceReactivateView` que pone `record_active=True` y `deleted_at=None`.
- **Bloqueo de tipo en edición**: en `update.html` el `select` de `service_type` queda deshabilitado (visible pero no modificable) con hidden input del valor real; server-side `ServiceUpdateView` fuerza `service_type` al valor original del objeto y se elimina la lógica de `post()` que limpiaba el PDF.
- **Cards PDF/imagen del mismo alto**: en create/update, `field_pdf` y `field_image` usan `h-100` en sus cards para igualar altura.
- **Listado: públicos sin precio ni suscripciones**: cuando `service_type == 'public'`, las columnas Precio y Suscripciones muestran `—` en gris (las de comerciales mantienen `$X.XX` y el conteo real).

### Out of Scope
- Reactivar desde operaciones masivas (bulk) — se decide dejarlo solo por fila en el listado.
- Botones de reactivación para Customer/Contract/Certificate/Subscription (mismo patrón a futuro, no en este change).
- Filtro por estado en el listado de servicios del dashboard (se muestran todos, ya hay badge Activa/Desactivada).
- Vista pública de servicios (`public.html`, `service_detail.html`, `commercial*.html`) — solo cambian las querysets, no el markup.

## Capabilities

### New Capabilities
- `service-reactivation`: reactivación de servicios desactivados desde el listado del dashboard.

### Modified Capabilities
- `home-services-visibility`: las vistas públicas de servicios solo exponen `record_active=True`.
- `commercial-service-type-lock`: el tipo de servicio no se puede cambiar al editar.
- `commercial-service-form-layout`: cards PDF/imagen con altura igualada.
- `commercial-service-list`: públicos sin precio ni suscripciones (`—`).

## Approach

### 1. Filtro por estado en el home

`apps/home/views/servicios/publicos/views.py`: `Service.objects.filter(service_type=Service.PUBLIC, record_active=True)`.
`apps/home/views/servicios/comerciales/views.py`:
- `PublicCommercialServicesListView.get_queryset()`: `record_active=True`.
- `ServiceDetailView.dispatch()`: `get_object_or_404(..., record_active=True)`.
- `related_services`: `record_active=True`.

### 2. Reactivación

- `apps/commercial/views/services.py`: nueva `ServiceReactivateView(LoginRequiredMixin, PermissionRequiredMixin, View)` con `permission_required = 'commercial.change_service'`; `post()`: si `record_active` ya es True → warning; si no → `record_active=True`, `deleted_at=None` (sin `_cleanup_files`, no es borrado), `save(update_fields=['record_active', 'deleted_at'])`, `log_action(CHANGE)`, message de éxito.
- `apps/commercial/urls.py`: `path('reactivar/servicios/<uuid:uuid>/', ServiceReactivateView.as_view(), name='servicio_reactivate')`.
- `apps/commercial/templates/pages/commercial/service/list.html`: botón verde (`btn-outline-success`, `ti ti-arrow-up` o `ti ti-refresh`) con `data-action="reactivar"` cuando `not object.record_active and perms.commercial.change_service`; se reutiliza el modal existente; nuevo branch en el JS para `reactivar` (form.action → `servicio_reactivate`).

### 3. Bloqueo de tipo en edición

- `update.html`: `select` de `service_type` con atributo `disabled` (sin `required`), + `<input type="hidden" name="service_type" value="{{ form.service_type.value }}">`; el select muestra las opciones con la selección actual (usar `form.service_type.value` para `selected`, que ya es así).
- `apps/commercial/views/services.py` `ServiceUpdateView`:
  ```python
  def post(self, request, *args, **kwargs):
      self.object = self.get_object()
      post = request.POST.copy()
      post['service_type'] = self.object.service_type  # nunca se cambia al editar
      request.POST = post
      return super().post(request, *args, **kwargs)
  ```
  Nota: `request.POST` no es mutable → se reasigna. O alternativamente `self.request.POST._mutable = True`; mejor crear una copia y re-asignar no es trivial porque `get_form` lee `self.request.POST`. Lo más limpio: sobreescribir `get_form_kwargs` y pasar `data=self.request.POST.copy()` con el valor forzado? No — `UpdateView.get_form()` ya arma `data=self.request.POST`. Verificar en implementación; opción robusta: en `post()`, mutar `request.POST` vía `request.POST._mutable = True` y fijar la clave, o construir el form manualmente con `ServiceForm(data=..., instance=...)`. Se decide en diseño (ver design.md).
  - Eliminar la lógica de `post()` actual que limpiaba `self.object.pdf = None` al pasar a comercial.
- `ServiceForm` no cambia.

### 4. Cards PDF/imagen mismo alto

En create/update: `<div class="card h-100">` en `field_pdf` y `field_image`. Las columnas ya son `col-md-6` (o full-width en imagen comercial sin `col-md-6`, donde h-100 no afecta).

### 5. Listado: públicos sin precio ni suscripciones

`list.html`:
- Precio: `{% if object.service_type == 'public' %}<span class="text-muted">—</span>{% else %}${{ object.price|floatformat:2 }}{% endif %}`
- Suscripciones: `{% if object.service_type == 'public' %}<span class="text-muted">—</span>{% else %}{{ object.num_subscriptions }}{% endif %}`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/home/views/servicios/publicos/views.py` | Modified | Filtro `record_active=True` |
| `apps/home/views/servicios/comerciales/views.py` | Modified | Filtro `record_active=True` en listado público, detail y related |
| `apps/commercial/views/services.py` | Modified | `ServiceReactivateView` nueva; `ServiceUpdateView` bloquea tipo |
| `apps/commercial/urls.py` | Modified | URL `servicio_reactivate` |
| `apps/commercial/templates/pages/commercial/service/list.html` | Modified | Botón Reactivar + `—` para públicos |
| `apps/commercial/templates/pages/commercial/service/{create,update}.html` | Modified | Cards `h-100`; select tipo disabled + hidden |
| `apps/home/tests/*`, `apps/commercial/tests/*` | Modified | Tests de filtro, reactivación, bloqueo de tipo, layout |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Bloquear tipo rompe POST de update existente (si algo enviaba service_type distinto) | Baja | Forzar server-side el tipo original; el hidden input asegura envío correcto |
| Mutar `request.POST` es frágil | Med | Verificar en implementación; alternativa: construir form con `ServiceForm(data=post, instance=...)` en `post()` |
| Test existente de update que cambia public→commercial y limpia pdf | Media | Buscar y ajustar/eliminar ese test en test_views.py |
| `test_servicio_update_nodblank` (fslightbox/pdf) sigue pasando | Baja | No se toca markup interno de files |

## Rollback Plan

Revertir vistas + urls + templates + tests; no hay migraciones.

## Dependencies

- Ninguna externa.

## Success Criteria

- [ ] Servicio desactivado NO aparece en listado público del home ni en detalle ni en relacionados.
- [ ] Botón "Reactivar" visible solo para staff con `change_service` y solo en servicios desactivados; reactiva correctamente.
- [ ] Al editar un servicio, el tipo no se puede modificar (select deshabilitado) y el POST no lo cambia aunque se manipule.
- [ ] Cards PDF/imagen del mismo alto en create y update.
- [ ] Públicos en el listado muestran `—` en Precio y Suscripciones; comerciales intactos.
- [ ] Suite `apps.commercial` + `apps.home` verde; djlint/ruff limpios.
