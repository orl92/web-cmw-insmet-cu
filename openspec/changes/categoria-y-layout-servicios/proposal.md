# Proposal: Categoría de servicio en formularios (solo comercial) y layout PDF+imagen lado a lado en el form

## Intent

`Service.service_category` (agrometeo/pronostico) ya existe y define el período de facturación (mes/día), pero **ningún template lo renderiza**: create/update lo omiten, dejando siempre `pronostico`. Se necesita exponer la categoría en los formularios de servicio, **visible únicamente cuando el tipo es comercial** (los públicos no la usan). Además, en el formulario de crear/editar servicio (dashboard), los servicios públicos hoy muestran el PDF y la imagen apilados verticalmente: se necesita que **PDF e imagen se muestren uno al lado del otro** (dos columnas). Los servicios comerciales solo muestran imagen y se mantienen como están.

Ajustes de layout adicionales decididos por el usuario (2026-09-04):
- En los **servicios públicos**, la **imagen pasa a ser obligatoria**, con el mismo feedback visual (label `required` + error) que el resto de campos.
- En la **fila superior** del form, `title` y `service_type` quedan **parejos (6+6)**.
- En los **comerciales**, los campos `service_category`, `code` y `price` se muestran **uno al lado del otro en 4/4/4**, en ese orden (categoría primero).

> Nota histórica: un intent previo de este change reestructuró la vista pública `public.html` y dejó la categoría siempre visible; **ambos cambios se revirtieron** por decisión del usuario (el layout lado a lado era del formulario, no de la vista pública; y la categoría solo aplica a comerciales).

## Scope

### In Scope
- Select de `service_category` en `create.html`/`update.html`, **visible solo cuando `service_type == 'commercial'`**; con `service_type == 'public'` queda **oculto** (y sin valor forzado: sigue el default `pronostico`).
- En el formulario (create/update), para **servicios públicos**: los campos PDF e imagen se muestran **uno al lado del otro** (`row` con dos `col-md-6`).
- Para **servicios comerciales**: solo imagen, layout actual **sin cambios** (imagen a su ancho normal, sin columnas lado a lado).
- **Imagen obligatoria en públicos**: `ServiceForm.clean()` rechaza públicos sin imagen (create y update, con patrón `existing_image`); la template marca label/input `required` con el mismo feedback del resto.
- **Fila superior 6+6**: `title` y `service_type` en dos `col-md-6` (antes `col-md-8`/`col-md-4`).
- **Comerciales 4/4/4**: `service_category`, `code` y `price` en tres `col-md-4`, en ese orden (categoría primero), en una sola fila.
- Reutilizar el patrón existente de `toggleFields()` en JS para mostrar/ocultar según tipo.

### Out of Scope
- Vista pública de servicios (`public.html`, `service_detail.html`, `commercial*.html`) — queda intacta.
- Migraciones de datos o cambios de modelo (el campo `image` ya es `blank=True, null=True`; la obligatoriedad se aplica a nivel de form/template, no del modelo).
- Cambiar la lógica comercial existente en `ServiceForm` (code/price/imagen exigidos, PDF rechazado) — solo se añade la validación de imagen para públicos.

## Capabilities

### New Capabilities
- (ninguna nueva; el layout de formulario se agrega al alcance de `commercial-service-categories` como escenario del form)

### Modified Capabilities
- `commercial-service-categories`: el formulario de servicio renderiza el `select` de `service_category` **solo para tipo comercial**; para públicos permanece oculto. El form para públicos muestra PDF e imagen en dos columnas, requiere imagen (backend + template), la fila superior es 6+6 y los comerciales usan 4/4/4 (categoría → código → precio).

## Approach

En `apps/commercial/templates/pages/commercial/service/{create,update}.html`:
1. Añadir un bloque `field_category` (select `service_category`) con `style="display:none"` por defecto, orquestado por `toggleFields()`: visible solo cuando `service_type == 'commercial'`; en ese caso el input no se deshabilita. Para `public`, oculto y deshabilitado (sin valor enviado → default `pronostico`).
2. Agrupar `field_pdf` y `field_image` en un `row` con **dos `col-md-6`** cuando el tipo es público. Para comercial, la imagen se muestra a ancho completo (como hoy) y el PDF oculto.
3. Ajustar la fila superior a **`title` + `service_type` en 6+6** y agrupar en una sola fila `field_category` + `field_code` + `field_price` en **4/4/4** (categoría primero).
4. En `apps/commercial/forms/service.py`, `ServiceForm.clean()`: para `PUBLIC`, exigir imagen (`not image and not existing_image` → `add_error('image', ...)`).
5. Templates: label/input de imagen con `required` para públicos sin imagen existente; en update usar `data-has-image` para que el JS no fuerce re-subida cuando ya existe imagen.
6. Ajustar `toggleFields()` y el estado inicial (server-side en update según `object.service_type`; JS en create al elegir tipo).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/commercial/templates/pages/commercial/service/create.html` | Modified | Select de `service_category` condicional a comercial + row PDF/imagen lado a lado (público) + fila superior 6+6 + comerciales 4/4/4 |
| `apps/commercial/templates/pages/commercial/service/update.html` | Modified | Idem con estado inicial según `object.service_type`; `data-has-image` para required condicional |
| `apps/commercial/forms/service.py` | Modified | `ServiceForm.clean()` exige imagen para públicos |
| Tests de formularios/views (`test_forms.py`, `test_views.py`) | Modified | Tests de render del select según tipo, layout de columnas, required de imagen y validación de form |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Romper `test_servicio_update_nodblank` en `test_file_preview_modal.py` | Med | Conservar `data-fslightbox` y `data-pdf-url` en `update.html` |
| `toggleFields()` con más ramas puede romper la lógica JS | Med | Mantener la estructura actual y solo añadir el caso category; testear render con `service_type` público y comercial |
| djlint falla en templates | Med | Correr `djlint . --reformat --check` y `--lint` |

## Rollback Plan

Revertir los 2 templates de formulario y sus tests a estado previo (git checkout); no hay migraciones ni cambios de modelo que deshacer.

## Dependencies

- Ninguna externa. Requiere mantener invariantes del spec `018-dashboard-file-preview-modal` (REQ-001/002/004) en `update.html`.

## Success Criteria

- [x] `create.html`/`update.html` muestran el `<select>` de `service_category` **solo cuando `service_type == 'commercial'`**; con `public` está oculto.
- [x] En formulario con tipo **público**: `field_pdf` y `field_image` se muestran en **dos columnas (`col-md-6`) lado a lado**.
- [x] En formulario con tipo **comercial**: solo imagen a ancho completo (sin columnas); PDF oculto.
- [x] **Imagen obligatoria en públicos**: `ServiceForm.clean()` rechaza públicos sin imagen (con `existing_image` en update), y el template/label marcan `required` con feedback igual al resto de campos.
- [x] **Fila superior 6+6**: `title` y `service_type` en dos `col-md-6`.
- [x] **Comerciales 4/4/4**: `service_category`, `code` y `price` en tres `col-md-4` en una fila, en ese orden.
- [x] `test_file_preview_modal` (fslightbox/pdf) pasa sin cambios de aserción.
- [x] `djlint . --reformat --check` y `--lint` pasan sobre las templates tocadas.