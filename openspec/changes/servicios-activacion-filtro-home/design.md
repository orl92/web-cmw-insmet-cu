# Design: Activación de servicios, filtro por estado en home, bloqueo de tipo y mejoras de listado/form

## Context / Alcance

Los servicios usan `SoftDeleteModel` (`record_active`, `deleted_at`). Los problemas:
1. Las vistas públicas del home filtran solo por `service_type`, sin `record_active=True` → un servicio desactivado sigue visible en el portal.
2. No existe forma de reactivar un servicio desde el dashboard (solo "Eliminar permanentemente" para superusuarios).
3. En edición, `service_type` es un `<select>` normal y `ServiceUpdateView.post()` incluso limpia `self.object.pdf` si se pasa a comercial.
4. Las cards de PDF/imagen en el form tienen alturas distintas (la imagen es más alta: avatar + contenido).
5. El listado muestra `$0.00` y `0` para públicos, que no tienen precio ni suscripciones.

Es un cambio de vistas (3 home + 2 commercial) + urls (1) + templates (4) + tests. No hay modelo/DB/migraciones.

## Files

| File | Change |
|------|--------|
| `apps/home/views/servicios/publicos/views.py` | `PublicServicesListView`: `record_active=True` |
| `apps/home/views/servicios/comerciales/views.py` | `PublicCommercialServicesListView`, `ServiceDetailView` (dispatch + related): `record_active=True` |
| `apps/commercial/views/services.py` | `ServiceReactivateView` nueva; `ServiceUpdateView.post()` bloquea tipo |
| `apps/commercial/urls.py` | `servicio_reactivate` |
| `apps/commercial/templates/pages/commercial/service/list.html` | Botón Reactivar + `—` para públicos |
| `apps/commercial/templates/pages/commercial/service/create.html` | Cards `h-100` |
| `apps/commercial/templates/pages/commercial/service/update.html` | Cards `h-100` + select tipo disabled + hidden |
| `apps/home/tests/test_views.py` (o clase nueva) | Tests de filtro |
| `apps/commercial/tests/test_views.py` | Tests de reactivación y bloqueo de tipo |

## Approach

### 1. Filtro por estado en home

```python
# publicos/views.py
Service.objects.filter(service_type=Service.PUBLIC, record_active=True).order_by('date')

# comerciales/views.py — PublicCommercialServicesListView
Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True).order_by('title')

# ServiceDetailView.dispatch
get_object_or_404(Service, uuid=kwargs['uuid'], service_type=Service.COMMERCIAL, record_active=True)

# related_services
Service.objects.filter(service_type=Service.COMMERCIAL, record_active=True).exclude(uuid=...).order_by('title')[:4]
```

### 2. Reactivación

`ServiceReactivateView(LoginRequiredMixin, PermissionRequiredMixin, View)`:
```python
permission_required = 'commercial.change_service'

def post(self, request, uuid):
    service = get_object_or_404(Service, uuid=uuid)
    if service.record_active:
        messages.warning(request, 'El servicio ya estaba activo.')
        return redirect('commercial:servicio_list')
    service.record_active = True
    service.deleted_at = None
    service.save(update_fields=['record_active', 'deleted_at'])
    log_action(user=request.user, obj=service, action_flag=CHANGE,
               message=f'Servicio reactivado: {service.title}.')
    messages.success(request, 'Servicio reactivado con éxito.')
    return redirect('commercial:servicio_list')
```

Nota: NO llamar a `service.delete()` (eso sobrescribe a False). Reactivar es simplemente setear los campos; el archivo no se toca (soft delete no borra media, `delete()` de `SoftDeleteModel` no llama `_cleanup_files` real — solo `Service.delete()` lo haría; reactivar no implica nada de archivos).

En `list.html`:
- Botón para `not object.record_active and perms.commercial.change_service`:
  ```html
  <button type="button" class="btn btn-icon btn-outline-success btn-sm action-btn"
          data-action="reactivar" data-uuid="{{ object.uuid }}" data-name="{{ object.title }}"
          data-bs-toggle="tooltip" data-bs-placement="bottom" aria-label="Reactivar"
          data-bs-original-title="Reactivar servicio">
    <i class="icon ti ti-arrow-up"></i>
  </button>
  ```
- JS del modal: agregar branch `reactivar` que setea título/cuerpo y `form.action` → `{% url "commercial:servicio_reactivate" uuid %}` (mismo patrón `replace` con zero-uuid).
- El modal footer usará el mismo botón "Confirmar" (btn-danger); para reactivar conviene un botón de confirmación neutro/verde, pero reutilizamos el existente para no duplicar modales (se puede cambiar el color dinámicamente si se quiere; aquí mínimo: se mantiene).

### 3. Bloqueo de tipo en edición

En `update.html`, reemplazar el `<select name="service_type">` por un select disabled + hidden:

```html
<select class="form-control ..." id="id_service_type" disabled>
  ...opciones con `selected` por form.service_type.value...
</select>
<input type="hidden" name="service_type" value="{{ form.service_type.value }}">
<small class="text-muted">El tipo de servicio no se puede modificar.</small>
```

- Quitar `required` del select (un select disabled no se valida igual; el hidden lleva el valor).
- El JS `toggleFields()` en update ya lee `serviceType.value` del select para mostrar/ocultar. Con `disabled` el `.value` sigue disponible para JS (disabled no afecta `.value` lectura). PERO: `serviceType.value` en update debía reflejar `object.service_type` — ya lo hace el `selected` del template. Al cambiar... no se puede cambiar (disabled). OK.
  - OJO: `imageInput.required = imageInput.dataset.hasImage !== 'true'` etc. dependen del branch público/comercial por `type`. Con disabled, el usuario no cambia el tipo, así que el estado inicial es correcto y el listener de `change` nunca se dispara. Sin problema.
- En `apps/commercial/views/services.py`, `ServiceUpdateView`:
  ```python
  def post(self, request, *args, **kwargs):
      self.object = self.get_object()
      post = request.POST.copy()
      post['service_type'] = self.object.service_type
      request.POST = post
      return super().post(request, *args, **kwargs)
  ```
  `request.POST` es un QueryDict inmutable, pero se puede **reasignar** `request.POST = post` (QueryDict mutable). Esta es la forma estándar de forzar valores. Eliminar el bloque `old_type/new_type` que limpiaba pdf.

### 4. Cards PDF/imagen mismo alto

En `create.html` y `update.html`, dentro de `field_pdf` y `field_image`:
- `<div class="card">` → `<div class="card h-100">` (ambos campos).
- Las columnas son `col-md-6 mb-3` (o imagen full width en comercial sin col-md-6; `h-100` sin columna no afecta).
- Opcional: `card-body d-flex align-items-center` ya existe en ambos.

### 5. Listado: públicos sin precio ni suscripciones

```html
<td>
  {% if object.service_type == 'public' %}
    <span class="text-muted">—</span>
  {% else %}
    ${{ object.price|floatformat:2 }}
  {% endif %}
</td>
...
<td>
  {% if object.service_type == 'public' %}
    <span class="text-muted">—</span>
  {% else %}
    {{ object.num_subscriptions }}
  {% endif %}
</td>
```

## Testing Strategy

- **Home (nuevo test)**: crear servicio público + comercial con `record_active=False`; GET a las listas públicas y detail → los inactivos no aparecen (list) y el detail devuelve 404.
- **Commercial reactivación**: POST a `servicio_reactivate` con permiso → `record_active=True`, `deleted_at=None`; POST de nuevo → warning y sin cambio; GET sin login → redirect.
- **Bloqueo tipo**: GET update → select disabled + hidden con valor; POST con `service_type` manipulado → el objeto conserva su tipo original.
- **Layout**: cards con `h-100` (create y update, ambos campos).
- **Listado**: render con público → `—` en precio y suscripciones; comercial → `$` y número.
- **Regresión**: suite completa `apps.commercial` + `apps.home`; `test_file_preview_modal` intacto.

## Verification

- `python manage.py check`
- `python manage.py test apps.commercial apps.home`
- `djlint apps/commercial/templates/pages/commercial/service/ --reformat --check --lint`
- `ruff check apps/commercial/views/services.py apps/commercial/tests/test_views.py apps/home/views/servicios/ apps/home/tests/test_views.py`

## Risks

- Mutar `request.POST` (QueryDict inmutable): reasignarlo con una copia mutable es el patrón conocido; verificar en test que el tipo original se conserva.
- Los tests existentes de `ServiceUpdateView` que dependían del cambio de tipo y limpieza de pdf pueden romper → buscar y ajustar.
- `PublicServicesListView` usa `context_object_name='pdf_list'` (nombre histórico) — no tocar.
- djlint (indentación) y posibles `h-100` sobrantes.

## Rollback

Revertir vistas + urls + templates + tests; sin migraciones.
