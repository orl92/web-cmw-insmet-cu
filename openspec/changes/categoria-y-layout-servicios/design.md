# Design: Categoría de servicio en formularios (solo comercial), layout PDF+imagen lado a lado, imagen obligatoria y filas balanceadas

## Context / Alcance

Product decisions (2026-09-04, corrigen el intent previo):
1. El `<select>` de `service_category` en create/update es **solo visible cuando `service_type == 'commercial'`**; para públicos permanece oculto.
2. En el **formulario** (dashboard create/update), para servicios **públicos**, los campos **PDF e imagen se muestran uno al lado del otro** (dos `col-md-6`). Para **comerciales**, solo imagen a ancho completo (sin cambio visual).
3. La **vista pública** (`public.html`, `service_detail.html`, `commercial*`) **NO se toca** (cambio previo revertido).
4. **Imagen obligatoria para públicos**: backend (`ServiceForm.clean()`) y template (`required` + feedback), con patrón `existing_image` para update.
5. **Fila superior 6+6**: `title` y `service_type` en dos `col-md-6` (antes `col-md-8`/`col-md-4`).
6. **Comerciales 4/4/4**: `service_category`, `code` y `price` en una sola fila de tres `col-md-4`, en ese orden (categoría primero).

Es un cambio de templates (2) + form Python (1) + tests. No hay modelo/DB/migraciones.

## Files

| File | Change |
|------|--------|
| `apps/commercial/templates/pages/commercial/service/create.html` | Select categoría condicional + row PDF/imagen + 6+6 + 4/4/4 + image required |
| `apps/commercial/templates/pages/commercial/service/update.html` | Ídem con estado inicial según `object.service_type` y `data-has-image` para required condicional |
| `apps/commercial/forms/service.py` | `ServiceForm.clean()` exige imagen para públicos |
| `apps/commercial/tests/test_views.py` | Tests de render del select, layout y required |
| `apps/commercial/tests/test_forms.py` | Tests de validación de imagen para públicos |

## Approach

### 1. Select de `service_category` solo para comercial (en fila 4/4/4)

En `create.html`/`update.html`, dentro del bloque **"Datos Específicos"**, los campos `field_category`, `field_code` y `field_price` viven juntos en **una sola fila** de tres `col-md-4`, en ese orden (categoría → código → precio):

```html
<div class="row">
  <div class="col-md-4 mb-3" id="field_category" style="display: none;">
    <label class="form-label" for="id_service_category">...sin required...</label>
    <select name="service_category" id="id_service_category">...</select>
    <small class="text-muted">Período de facturación del servicio (día o mes).</small>
  </div>
  <div class="col-md-4 mb-3" id="field_code" style="display: none;">...</div>
  <div class="col-md-4 mb-3" id="field_price" style="display: none;">...</div>
</div>
```

- En `create.html`: `style="display: none"` por defecto.
- En `update.html`: `style="display: {% if object.service_type == 'commercial' %}block{% else %}none{% endif %}"`.
- Preselección: `form.service_category.value` (create) / `object.service_category` (update).
- **Sin** clase `required` en el label de categoría y **sin** atributo `required`: el form tiene `required=False` y el modelo tiene default `pronostico`. Al ocultarse con público, el input se deshabilita en JS.

### 2. PDF + imagen lado a lado (solo público)

Reestructurar `field_pdf` y `field_image` dentro de un `row` con id `row_files`:

```html
<div class="row" id="row_files">
  <div class="col-md-6 mb-3" id="field_pdf" style="display: none;">... PDF card ...</div>
  <div class="col-md-6 mb-3" id="field_image" style="display: none;">... image card ...</div>
</div>
```

- **Público**: `field_pdf` y `field_image` visibles, ambos `col-md-6` lado a lado.
- **Comercial**: `field_pdf` oculto; `field_image` visible **sin** clase `col-md-6` (full width).
- `toggleFields()` alterna la clase `col-md-6` sobre `field_image` según tipo.

> Nota: el markup interno de `field_image` (avatar + input + fslightbox "Ver imagen actual") NO cambia; solo el contenedor de columna. Igual para `field_pdf` (pdf_avatar + input + botón "Ver PDF" con `data-pdf-url`).

### 3. Imagen obligatoria para públicos

- **Backend** (`apps/commercial/forms/service.py`, `ServiceForm.clean()`), rama `PUBLIC`:
  ```python
  if not image and not existing_image:
      self.add_error('image', 'Para servicios públicos es obligatorio una imagen.')
  ```
  `existing_image` = `self.instance.image if self.instance.pk else None` (mismo patrón que el PDF). La rama `COMMERCIAL` ya exigía imagen; no cambia.
- **Template create**: label con clase `required`, input con atributo `required`; JS público → `imageInput.required = true` (antes `false`).
- **Template update**: label/input `required` **solo cuando no hay imagen existente** (`{% if not object.image %}`); el input lleva `data-has-image="true|false"` y el JS usa `imageInput.required = imageInput.dataset.hasImage !== 'true'` para no forzar re-subida cuando ya hay imagen.
- Feedback de error: ya existente (`is-invalid` + `invalid-feedback` como en PDF/resto).

### 4. Fila superior 6+6

En `create.html`/`update.html`, el primer card: `title` en `col-md-6` y `service_type` en `col-md-6` (antes `col-md-8` + `col-md-4`).

### 5. Estado inicial

- `create.html`: `toggleFields()` arranca con service_type vacío → todo oculto; al elegir tipo se ajusta.
- `update.html`: estado inicial por `object.service_type` (server-side en `style`); `toggleFields()` también corre para sincronizar.

## Testing Strategy

- **Tests de render (Django TestCase)** en `apps/commercial/tests/test_views.py` (clase `ServiceCategorySelectRenderTests`):
  - `create`/`update` público → `field_category` oculto; `field_pdf` y `field_image` en `col-md-6`.
  - `create`/`update` comercial → `field_category` visible con opciones agrometeo/pronostico; imagen full width sin `col-md-6` conflictivo.
  - Filas balanceadas: `title`/`service_type` en `col-md-6`; `field_category`/`field_code`/`field_price` en `col-md-4` y en orden (categoría → código → precio).
  - Imagen required: create → input con `required`; update sin imagen → `required`; update con imagen → sin `required`.
- **Tests de form** (`apps/commercial/tests/test_forms.py`): `test_public_service_requires_image`; actualizar `test_public_service_valid`/`test_public_service_requires_pdf` para incluir imagen.
- **Invariantes**: `test_file_preview_modal` (fslightbox/pdf) sin cambios de aserción.

## Verification

- `python manage.py check`
- `python manage.py test apps.commercial`
- `djlint apps/commercial/templates/pages/commercial/service/ --reformat --check --lint`
- `ruff check apps/commercial/forms/service.py apps/commercial/tests/test_views.py apps/commercial/tests/test_forms.py`

## Risks

- `test_file_preview_modal` aserta `data-fslightbox`/`data-pdf-url` en `update.html` → al mover contenedores, preservar el markup interno intacto.
- `toggleFields()` con nuevas ramas puede romper el JS si no se mantiene la estructura → testear render en ambos tipos.
- **Cambio de semántica**: públicos pasan a exigir imagen → actualizar tests de form/views que enviaban públicos sin imagen (`test_public_service_valid`, `test_post_creates_service`).
- djlint (indentación).

## Rollback

Revertir los 2 templates de formulario + form + tests; sin migraciones.