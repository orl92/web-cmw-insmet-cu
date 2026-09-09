# Tasks: categoria-y-layout-servicios

> Alcance corregido 2026-09-04: categoría solo en comercial + PDF/imagen lado a lado en el form. Los cambios previos en `public.html` se revirtieron y NO se rehacen.
> Ampliación 2026-09-04 (usuario): imagen obligatoria en públicos + fila superior 6+6 + comerciales 4/4/4 (categoría → código → precio).

## Fase 1 — Select de categoría (solo comercial)

- [x] 1.1 create.html: añadir contenedor `field_category` (select `service_category`, patrón `service_type`) en "Datos Específicos", oculto por defecto (`display:none`), sin `required`, preselección `form.service_category.value`; agregar `small` hint y manejo de errores.
- [x] 1.2 update.html: idem `field_category`, estado inicial `display: block/none` según `object.service_type == 'commercial'`, preselección `object.service_category`.
- [x] 1.3 test RED: `ServiceCategorySelectRenderTests` — `test_create_field_category_hidden_by_default` y `test_create_select_present_without_required`.
- [x] 1.4 test RED: `test_update_field_category_hidden_for_public` y `test_update_field_category_visible_for_commercial_with_preselection`.
- [x] 1.5 Ajustar `toggleFields()` en ambos templates: mostrar/ocultar `field_category` según tipo (visible ⇒ commercial; oculto y disabled ⇒ public) y sincronizar estado inicial.

## Fase 2 — PDF + imagen lado a lado (solo público, en el form)

- [x] 2.1 create.html: agrupar `field_pdf` y `field_image` en `row` con dos `col-md-6` (contenedor `row_files_public`→`row_files`), oculto por defecto; markup interno de ambos campos intacto (pdf_avatar, fslightbox, `data-pdf-url`).
- [x] 2.2 update.html: idem `row_files` con estado inicial según `object.service_type == 'public'`; preservar `data-fslightbox` y `data-pdf-url`.
- [x] 2.3 Ajustar `toggleFields()`: público → ambos `col-md-6` visibles; comercial → `field_image` full width (sin `col-md-6`), `field_pdf` oculto.
- [x] 2.4 test RED: `test_update_public_form_shows_pdf_and_image_side_by_side` (col-md-6 en ambos) + `test_update_commercial_form_keeps_image_full_width` (sin col-md-6 para imagen / pdf oculto).

## Fase 3 — Imagen obligatoria para públicos

- [x] 3.1 `ServiceForm.clean()`: rama `PUBLIC` exige imagen (`not image and not existing_image` → `add_error('image', 'Para servicios públicos es obligatorio una imagen.')`); `existing_image` = `self.instance.image if self.instance.pk else None`.
- [x] 3.2 create.html: label/input de imagen con `required` (JS público → `imageInput.required = true` — antes false).
- [x] 3.3 update.html: label/input `required` solo si no hay imagen existente (`{% if not object.image %}`); input con `data-has-image` y JS `imageInput.required = data-has-image !== 'true'` (no exige re-subida si ya hay imagen).
- [x] 3.4 test form: `test_public_service_requires_image`; actualizar `test_public_service_valid` y `test_public_service_requires_pdf` para incluir imagen.
- [x] 3.5 test render: `test_create_public_image_is_required`, `test_update_image_required_only_when_missing`, `test_update_image_not_required_when_exists`; actualizar `test_post_creates_service` con PNG válido (`_make_png` desde test_forms).

## Fase 4 — Filas balanceadas (6+6 y 4/4/4)

- [x] 4.1 create.html: primer card `title` `col-md-8`→`col-md-6` y `service_type` `col-md-4`→`col-md-6` (6+6).
- [x] 4.2 update.html: idem 6+6.
- [x] 4.3 create.html: `field_category` (4) + `field_code` (4) + `field_price` (4) en una sola fila, en ese orden (categoría primero); quitar la fila separada `col-md-6` de categoría y el `col-md-6`+`col-md-6` de code/price.
- [x] 4.4 update.html: idem 4/4/4 con estado inicial por `object.service_type`.
- [x] 4.5 tests render: `test_create_title_and_type_balanced_6_6`, `test_update_title_and_type_balanced_6_6`, `test_create_commercial_fields_each_col_4_in_order`, `test_update_commercial_fields_each_col_4_in_order` (verifican `col-md-4` y orden categoría→código→precio).

## Fase 5 — Verificación y limpieza

- [x] 5.1 `python manage.py check && python manage.py test apps.commercial` — 165 tests OK (incluye invariantes fslightbox/pdf).
- [x] 5.2 `djlint apps/commercial/templates/pages/commercial/service/ --reformat --check --lint` y `ruff check apps/commercial/forms/service.py apps/commercial/tests/test_views.py apps/commercial/tests/test_forms.py`.
- [x] 5.3 Confirmar que `apps/home` y `public.html`/`service_detail.html` NO cambiaron (git diff vacío en `apps/home`).