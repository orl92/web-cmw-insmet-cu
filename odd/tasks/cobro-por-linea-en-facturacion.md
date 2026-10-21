# Cobro por línea en el listado de facturación

Cierra el circuito de aprobación de pago desde el lado de **Facturación**: hoy el
listado dice `Pendiente`, pero no **qué línea** falta cobrar ni ofrece llegar a
aprobarla. La aprobación en sí se queda donde está (listado de suscripciones):
ésta es una vista de lectura con acceso directo, no una mudanza de flujo.

## Objetivo

Que cada fila del listado de facturas muestre, cuando la factura agrupa
suscripciones, el desglose `pagadas/total` de sus líneas y permita saltar a
**Aprobar Pago** de cada suscripción pendiente sin salir de Facturación.

## Problema (evidencia en código)

- `Invoice.status_display` (`apps/commercial/models.py:472-495`) ya deriva
  `pagada`/`pendiente` de las líneas, y `InvoiceQuerySet.with_display_status()`
  (`:339-357`) anota `items_total`/`items_paid` para no pagar una consulta por
  fila. Pero el listado
  (`apps/commercial/templates/includes/commercial/invoice/status_cell.html`, 7
  líneas) imprime **sólo la insignia**: no dice cuántas líneas son ni cuál falta.
- La acción "Aprobar Pago" existe **sólo** en el listado de suscripciones
  (`apps/commercial/templates/includes/commercial/subscription/actions_cell.html:65-74`,
  link a `commercial:suscripcion_approve`, gateado por
  `record_active and payment_status == 'pending' and latest_invoice_pdf_ready`).
  Desde Facturación no hay camino: hay que ir a Suscripciones y buscar la
  suscripción a mano.
- T18 (`64ce37b`) ya dejó la celda **Estado** extraída a partial y **refrescada
  en vivo** por `ajax_invoice_status` (`apps/commercial/views/list_status.py:43-78`).
  El desglose entra ahí y hereda el refresco sin JS nuevo.

## Decisiones

- **El desglose va dentro de la celda Estado**, no en una columna nueva: la
  celda ya es un partial y ya se re-renderiza en vivo; una columna nueva
  obligaría a tocar `invoice/list.html` y a mover el `columns` de DataTables sin
  ninguna ganancia. `layouts/list.html:55-69` no declara `columns` por índice,
  así que el riesgo de índices no existe — pero no se agrega columna igual.
- **Bloque plegable nativo** (`<details>`), sin JS ni modal: el contenido crece
  en flujo (el `.table-responsive` del layout tiene `overflow`, y un modal o un
  dropdown posicionado adentro se recortaría). Cero JS también significa cero
  estado que se pierda cuando el polling reemplaza la celda.
- **Gate del link = `commercial.change_subscription` (el permiso que exige
  `ApproveSubscriptionView`) + línea en `pending` + `invoice.pdf_ready` de la
  factura de la fila + no anulada.** Es la misma
  garantía que pide T18 ("Aprobar Pago sólo con factura emitida") y se lee de un
  campo ya cargado: no hace falta el `Subquery` de `latest_invoice_pdf_ready`
  (`apps/commercial/views/subscriptions.py:43-66`) ni una consulta por línea.
  Además no se ofrece sobre una factura anulada.
- **Sin N+1**: el acceso por línea (`item.subscription.payment_status`,
  `record_active`) y por servicio (`service.title`) se resuelve con
  `Prefetch('items', queryset=InvoiceItem.objects.select_related('subscription__service'))`
  en las dos querysets que renderizan la celda (listado y endpoint). El proyecto
  ya paga caro este error: T14/T15/T17 fueron justamente N+1.
- **Los conteos no se recalculan**: la insignia usa `items_total`/`items_paid`
  que ya anota `with_display_status()`, que es lo que `status_display` usa para
  decidir `pagada`/`pendiente`. Dos fuentes divergirían.
- **La aprobación no se muda.** El certificado es por suscripción
  (`apps/commercial/views/subscriptions.py:196-202`) y la factura no tiene campo
  de estado a propósito (`models.py:472-481`). Acá sólo se lee y se enlaza.
- **Copy en español neutro** (`es-mx`): "Aprobar pago", "por cobrar", "cobrada".

## Restricciones

- JS vanilla; de hecho esta feature **no agrega JS**. Prohibido npm/bundlers.
- Permisos: se hereda `commercial.view_invoice` del listado. El link a aprobar
  se ofrece con `request.user.is_staff` (mismo gate que el listado de
  suscripciones). No exponer datos de clientes ajenos: el listado de facturas ya
  está gateado por `view_invoice`.
- Plantillas: 2 espacios, formato djlint (`profile = "django"`).
- No commitear: el árbol comparte cambios con la sesión paralela del usuario.

## Tareas

- [x] **T1 — Datos por línea en el modelo.** En `Invoice`, una propiedad que
      devuelva las líneas con suscripción con `uuid`, `descripcion`, `importe` y
      `estado` (`pagado`/`pendiente`/`cancelada`) derivado de
      `subscription.payment_status` + `record_active`. Sin consultas propias:
      itera `self.items.all()` (prefetcheado). Docstring explicando por qué no
      vive en la plantilla ni en la vista.
- [x] **T2 — Partial del desglose.** `includes/commercial/invoice/line_payments.html`:
      resumen `n/N cobradas` + `<details>` con una fila por línea (servicio,
      importe, estado) y, cuando la factura está emitida, no anulada, el usuario
      es staff y la línea está pendiente, el link a
      `commercial:suscripcion_approve`. Accesible: `aria-label` en el link,
      `<summary>` con texto legible.
- [x] **T3 — Enganchar y prefetchear.** `status_cell.html` incluye el partial
      cuando hay líneas con suscripción; `InvoiceListView.get_queryset`
      (`apps/commercial/views/invoices.py:122-134`) y el queryset de
      `ajax_invoice_status` (`apps/commercial/views/list_status.py:46-53`) usan
      el `Prefetch` con `select_related('subscription__service')`.
- [x] **T4 — Tests.** Módulo nuevo
      `apps/commercial/tests/test_invoice_line_payments.py`: desglose correcto en
      el listado; el link aparece sólo con PDF listo y siendo staff; no aparece
      en factura anulada ni en línea cobrada; el endpoint `ajax_invoice_status`
      devuelve el mismo desglose; `assertNumQueries` con dos facturas de dos
      líneas fijando que no hay consulta por línea.

## Criterios de aceptación

- En Facturación, una factura por lote muestra `1/2 cobradas` y, al desplegar,
  qué línea falta y el link a Aprobar Pago de esa suscripción.
- Sin PDF listo, o con la factura anulada, el link **no** se ofrece.
- Un no-staff no ve el link.
- El desglose se actualiza solo cuando el polling reemplaza la celda Estado.
- Sin consultas por línea (test de conteo de queries en verde).
- `apps.commercial` completo en verde, ruff y djlint limpios.

## Checks

- `.venv/bin/python manage.py test apps.commercial`
- `.venv/bin/python manage.py test apps.commercial.tests.test_invoice_line_payments`
- `.venv/bin/python manage.py check`
- `.venv/bin/ruff check apps/ && .venv/bin/ruff format --check apps/`
- `.venv/bin/djlint apps/commercial/templates/ --check`

## Ruta y presupuesto

- Ruta: **delegada directa** (un writer). Disparador: 4 archivos no triviales +
  lectura previa que prepara la escritura.
- Pronóstico de líneas autoradas: ~150 (tope ~400/tarea, heurística de
  planificación, no criterio de aceptación). Sin encadenado de PRs.

## Progreso

Implementado y verificado (sin commitear, sobre `64ce37b`).

- **T1** — `Invoice.line_payments` en `apps/commercial/models.py` (property, ~40
  líneas): por cada línea con suscripción devuelve `uuid` (de la suscripción),
  `descripcion`, `servicio`, `importe`, `estado` (`pagado`/`pendiente`/`cancelada`)
  y `aprobable`. Sin consultas propias: itera `self.items.all()`.
- **T2** — `includes/commercial/invoice/line_payments.html`: resumen
  `n/N cobradas` + `<details>` con la fila por línea y el link a
  `commercial:suscripcion_approve` (`title`/`aria-label` con el servicio).
- **T3** — `status_cell.html` incluye el partial; `InvoiceListView.get_queryset`
  y `ajax_invoice_status` usan `Prefetch('items', select_related('subscription__service'))`.
- **T4** — `apps/commercial/tests/test_invoice_line_payments.py`: 16 tests.
- **Verificación**: RED observado antes de implementar (módulo completo: 5 FAIL +
  5 ERROR, incluido el `assertNumQueries` esperando 2 contra 10); triangulación
  sacando el `Prefetch` -> 2 fallos con 10 queries, restaurado -> verde. Post-fix:
  `manage.py test apps.commercial` -> **505 tests OK**; `check` sin issues;
  `ruff check` limpio; `djlint --check` 0 pendientes.
- **Corrección acotada del padre** (tras revisar la verificación): el link se
  ofrecía sobre líneas en `requested`, estado que `ApproveSubscriptionView`
  rechaza (`subscriptions.py:190-193`) y que el listado de suscripciones tampoco
  ofrece -> enlace muerto. Se agregó `aprobable` (solo `pending`), se cambió el gate
  a `perms.commercial.change_subscription` y se agregó
  `test_una_linea_solicitada_no_ofrece_aprobar_pago`; también `|floatformat:2` al
  importe, que salía sin formato frente al `$ ...|floatformat:2` del listado.
- **Caveat honesto**: el verificador independiente devolvió un informe con código
  y nombres de tests inventados (alucinaciones), así que su salida se descartó y
  el padre re-verificó a mano los puntos: uuid de suscripción en la URL, gate,
  `Prefetch`, conteo de queries y el caso `requested`.

Pendiente: nada de esta feature. Sigue sin commitear, junto al trabajo previo.
