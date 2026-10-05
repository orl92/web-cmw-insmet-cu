# Integridad de cliente, facturas y PDFs

## Objetivo

Cerrar tres defectos verificados en el flujo comercial y fijar las invariantes de
documentos, sin dejar datos de prueba a medias ni perder trazabilidad de facturas.

## Problema (verificado contra código, no supuesto)

1. **Naturales aparecen como `None`.** `Customer.company_name` es `NULL` para
   `client_type='natural'` (el nombre vive en `User.first_name/last_name`). Los
   listados de suscripción y factura leen el campo crudo:
   `subscription/list.html:31-32,154,167` y `invoice/list.html:31-32,37`.
   `Customer.__str__` (`models.py:96-99`) ya cae a `get_full_name() or username`,
   pero los templates nunca lo usan.

2. **Regenerar factura deja la factura anterior anulada sin reemplazo.**
   `RegenerateInvoiceView.post` (`views/subscriptions.py:260-303`) anula las
   facturas, borra certificados y revierte a `requested` en un único POST, y sólo
   después redirige al formulario. Si el staff abandona el formulario, la factura
   vieja queda anulada y no existe ninguna nueva.

3. **Invariante de documentos inexistente.** Nada impide que:
   - una factura con `status_display == 'pagada'` tenga `pdf_ready == False`;
   - una suscripción `paid` tenga cero certificados.
   Confirmado en la DB de desarrollo: la suscripción `ebb07492` está `paid` con
   `certificados=0`. La vía es `ServiceSubscriptionBulkActionView._handle_update`
   (`views/bulk.py:128-172`), cuyo allow-list incluye `payment_status='paid'` y
   no comprueba documentos.

### Descartado tras verificación

- **"Un usuario no cliente puede hacer una solicitud" NO es bug.** El guard de
  `ServiceDetailView.post` (`apps/home/views/servicios/comerciales/views.py:150`)
  y el del template (`service_detail.html:64`) funcionan. Probado contra el
  usuario real sin `Customer`: POST → 302 al login, `subs_created=0`. Lo que se
  observó fue `CheckUserProfileMiddleware` (`apps/core/middleware.py:19-43`)
  redirigiendo a `/accounts/profile/update/` por perfil incompleto.
- **`except ValueError, IndexError:` (`invoices.py:324,335`) NO es bug.** Es PEP
  758: Python 3.14 permite `except` sin paréntesis. El proyecto apunta a `py314`.

## Alcance

### Autorizado

- [x] **T1** Nombre completo para naturales en listados de suscripción y factura,
      más columna Identificación según tipo de cliente (documento para natural,
      `—` para el resto).
- [x] **T2** `first_name` / `last_name` en el formulario de alta de cliente,
      escribiendo sobre `User.first_name` / `User.last_name`.
- [x] **T3** Regeneración de factura con reversión: la factura anterior sobrevive
      hasta que la nueva existe (decisión A del usuario).
- [x] **T4** Invariante de documentos: factura pagada ⇒ PDF; suscripción pagada ⇒
      certificado.
- [x] **T5** Acciones de factura cancelada: sin Facturar ni Editar; Ver/Descargar
      sólo si el PDF existe realmente.
- [x] **T6** Espaciado de botones de acción en móvil, igual al layout en fila.
- [x] **T7** Fixtures de test que construyan clientes naturales válidos y fallen
      con diagnóstico explícito si falta un prerrequisito, en lugar de dejar
      `company_name=None` / `identity_document=None`.

### Fuera de alcance (decidido en otra etapa)

- B2/B3: inicio libre, cantidad/unidad, método de pago, eliminación del período
  fijo de 30 días.
- Reenvío de factura por el cliente (requiere decisión de seguridad aparte).
- QR por factura (integración estática, decisión de producto pendiente).

## Restricciones

- Tests: datos realistas y válidos, todos los prerrequisitos explícitos, y fallo
  con diagnóstico en lugar de `None` silencioso. Se permite que los datos queden
  persistidos en la base de desarrollo para inspección o borrado manual, pero
  **nunca** archivos residuales (perfiles, imágenes, PDFs).
- Las tareas pueden aparecer realmente en la cola y en las tablas; el estado real
  es parte de la verificación.
- Sin trabajo fuera de alcance en estos commits. Sin secretos ni `media/`.
- Solo archivos de esta etapa. B2/B3 no se mezclan en los mismos commits.
- Migraciones no versionadas (`.gitignore`).

## Criterios de aceptación

- [ ] Un natural con `first_name`/`last_name` muestra el nombre completo en
      suscripción, factura y cliente; `company_name` nunca se imprime en crudo
      para naturales.
- [ ] Identificación muestra el documento para natural y `—` para el resto.
- [ ] El alta de cliente persiste nombre y apellido en el `User`.
- [ ] Regenerar y abandonar el formulario **no** deja ninguna factura anulada.
- [ ] Regenerar y confirmar produce factura nueva viva y la anterior anulada.
- [ ] No existe forma (vía UI ni acción masiva) de dejar una factura pagada sin
      PDF o una suscripción pagada sin certificado; el intento falla con mensaje.
- [ ] Factura cancelada no muestra Facturar ni Editar.
- [ ] Botones apilados en móvil conservan el mismo `gap` que en fila.
- [ ] `python manage.py test` verde; Ruff y djLint limpios.

## Verificación prevista

| Cambio | Comando |
|---|---|
| Modelos, vistas, permisos, formularios | `python manage.py test` |
| Sólo templates | `python manage.py test` + `djlint . --lint` |
| Chequeo siempre | `python manage.py check` |

## Modo TDD

Resuelto desde la configuración del proyecto (`sdd-init` cachea capacidades de
testing). El proyecto tiene suite y la ejecuta en CI: se escribe primero el test
que reproduce el defecto, se observa RED, luego la corrección, luego GREEN.

## Progreso

Todo implementado y verificado, en cuatro work-unit commits:

| Unidad | Commit | Verificación del snapshot |
| --- | --- | --- |
| T1/T2/T7 nombre completo del natural | `c595809` | `test apps.commercial` → 309 tests, OK |
| T3 regeneración sin pérdida | `7ebfa75` | `test apps.commercial` → 329 tests, OK |
| T4 invariantes de documentos | `744c15f` | `test apps.commercial` → 349 tests, OK |
| T5/T6 acciones y responsive + este doc | (este commit) | `test apps.commercial` → 360 tests, OK |

Cada commit se verificó por separado con `git stash --keep-index -u`, no sobre
el árbol completo: un commit que sólo funciona con los siguientes no es una
unidad revisable.

- **T1/T2** `Customer.display_name` como única fuente de verdad de presentación;
  `__str__` delega en ella. Listados de suscripción y factura, y los correos, ya
  no imprimen `company_name` crudo. El alta persiste `first_name`/`last_name`
  en el `User`.
- **T3** `RegenerateInvoiceView` dejó de ser destructivo: su POST no toca
  ningún registro, sólo valida que haya factura vigente y redirige con
  `?regenerar=<uuid>`. La anulación se movió a `InvoiceCreateView.form_valid`,
  que crea la factura nueva **primero** y recién después anula la anterior por
  diferencia. Facturación manual, o suscripción no incluida: avisa y no anula
  nada.
- **T4** La acción masiva rechaza `payment_status='paid'` sin certificado con
  HTTP 400 y `processed=0`, mediante un hook `validate_update()` que corre una
  vez antes de cualquier `save`. Para "pagada sin PDF" se eligió visibilidad +
  reparación en vez de bloqueo: el PDF se genera en una tarea Huey asíncrona,
  así que `paid` sin PDF es un estado legítimo y transitorio; bloquearlo
  obligaría a volver síncrono el envío. Se añadió el badge "Pagada sin PDF" y
  `RetryInvoicePdfView` (`solo_paso='pdf'`, idempotente, no reenvía el correo).
- **T5** Una suscripción anulada ya no ofrece Facturar, Editar, Aprobar Pago ni
  Regenerar. Ver/Descargar factura exige `latest_invoice_pdf_ready`, que replica
  `Invoice.pdf_ready` en SQL para no disparar una consulta por fila.
- **T6** Celdas de acciones de suscripción y factura con
  `d-flex flex-wrap justify-content-end gap-2`.
- **T7** `apps/commercial/tests/factories.py` con validación y diagnóstico
  explícito (`IncompleteCustomerDataError`).

### Decisiones que conviene no olvidar

- **Sin `transaction.atomic` en la anulación.** `process_batch_invoice` encola
  la tarea Huey del PDF dentro de la transacción; con `atomic` el worker podría
  renderizar contra filas sin confirmar. El orden crear→anular ya da la garantía
  que importa: la factura anterior sobrevive hasta que la nueva existe.
- **Baja lógica del certificado, uno por uno.** `Certificate` es
  `SoftDeleteModel` y `QuerySet.delete()` ignora su `delete()`: borra la fila de
  verdad y deja el PDF huérfano en `media/`. Se itera con `certificado.delete()`
  para conservar la trazabilidad y limpiar el archivo.

### Tests que hubo que corregir (no el código)

- `test_bulk_update_payment_status` marcaba `paid` **sin certificado**: codificaba
  el defecto como comportamiento esperado. Ahora crea el certificado.
- Varios asserts de `test_views.py` y `test_invoice_invariants.py` buscaban el
  **nombre** de la ruta (`factura_cancel`, `factura_resend_email`) en el HTML.
  `{% url %}` renderiza el path, así que el nombre nunca aparece: esos asserts
  pasaban vacíos. Ahora se asserta sobre la URL resuelta o, para "Anular" y
  "Eliminar" (cuya URL arma el JS con un UUID placeholder), sobre el marcador
  `data-action` atado al `data-uuid` de la fila.
- Fixtures que creaban facturas sin PDF real y aun así esperaban los botones de
  descarga: los botones sólo existen si `pdf_ready`.

### Bugs encontrados en la verificación

- `test_factura_anulada_muestra_pdf_y_borrado_para_superusuario` **ya fallaba en
  HEAD** (se comprobó guardando los cambios en stash), o sea el reporte de
  "suite en verde" del subagente anterior no era reproducible.
- `assertNotIn('Anular factura', html)` no puede fallar: ese literal vive en el
  JS del modal y está siempre en la página.

## Próximo paso

Revisar el diff completo y commitear. Después, B2/B3 (inicio libre,
cantidad/unidad, método de pago, eliminación del período fijo de 30 días), que
siguen fuera de alcance de este documento.
