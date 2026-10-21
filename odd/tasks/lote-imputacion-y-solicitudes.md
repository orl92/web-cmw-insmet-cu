# Facturación por lote: imputación que no se puede enviar y pendientes que no lo son

## Objetivo

Que la facturación por lote se pueda confirmar sin adivinar por qué el servidor la
rechaza, y que la lista de suscripciones que ofrece el formulario muestre **sólo las
solicitudes sin facturar**, sin esconder la suscripción que se vino a regenerar.

## Problema

### 1. «Corrige el reparto entre centros de costo de la factura.» (error genérico y sin salida)

El operador abre el formulario desde la acción **Facturar/Regenerar** de una
suscripción `requested`, deja lo que el formulario ya trae precargado, pulsa
**Aceptar** y el POST vuelve con ese mensaje. No hay forma de saber qué corregir:
la plantilla sólo dibuja `non_form_errors`, y el error real es de una fila.

Causa verificada — no es JavaScript, es el *management form* del formset:

- Con `?regenerar=` el GET precarga una fila (`_prefill_inicial()` →
  `InvoiceCostAllocationFormSet(initial=[...])`), y un **model**formset cuenta las
  filas de `initial` como *existentes*: renderiza
  `INITIAL_FORMS=1`, `TOTAL_FORMS=2` (verificado).
- `INITIAL_FORMS=1` le dice a Django que la fila 0 ya existe en la base, así que su
  **`id` pasa a ser obligatorio**. Las imputaciones son filas nuevas de una factura
  que todavía no existe: el `id` viaja vacío.
- Resultado del POST: `form0.id: Este campo es requerido.` →
  `cost_formset.is_valid()` es `False` → `views/invoices.py:269` muestra el mensaje
  genérico. Reproducido con el payload real:

  | Payload | Resultado |
  |---|---|
  | `INITIAL_FORMS=1`, fila 0 llena, `id` vacío | **inválido** — `form0.id requerido` |
  | el mismo payload con `INITIAL_FORMS=0` | **válido** (arregla el caso) |
  | `INITIAL_FORMS=0`, fila 0 llena (lote fresco) | válido |

- El JS `prefijarImputacion()` reconstruye las filas pero **nunca reescribe
  `INITIAL_FORMS`**, así que el valor viejo sobrevive cualquier cambio de selección.

Segundo camino al mismo mensaje muerto: en el lote fresco, si el JS no prefija
(servicio sin código, o el `change` no se disparó), el formset llega vacío y el
rechazo —correcto— vuelve a ser invisible.

### 2. El listado ofrece suscripciones ya facturadas

`ajax_pending_subscriptions` (`views/invoices.py:810-812`) filtra
`payment_status__in=['requested', 'pending']`. Las `pending` **ya tienen factura
vigente**: ofrecerlas en el lote invita a facturarlas dos veces. El operador espera
ver sólo las solicitadas.

**El trap:** `regenerar` sólo es posible sobre una suscripción `pending`
(`RegenerateInvoiceView` exige una factura vigente, y facturar deja `pending`). Si el
listado se recorta a `requested` a secas, la suscripción que se vino a regenerar
desaparece de la lista, `preseleccionarRegeneracion()` no encuentra su checkbox, el
POST llega sin `subscriptions` y el flujo cae en *facturación manual* avisando
«su factura anterior no se anuló». El recorte tiene que dejarla visible.

## Por qué importa

El error del punto 1 bloquea **toda** la facturación individual: el botón
Facturar/Regenerar del listado es el camino normal para facturar una solicitud, y hoy
termina siempre en un mensaje que no dice qué arreglar. El punto 2 es dinero: una
suscripción facturada dos veces.

## Alcance

- **A1** Normalizar `INITIAL_FORMS=0` en el POST del formset de imputación
  (`cost_allocations_formset`), con el porqué escrito: son filas nuevas de una
  factura que aún no existe, el `id` no aplica.
- **A2** Mostrar los errores **por fila** del formset en `create.html` (además de los
  `non_form_errors` que ya dibuja), para que un rechazo nombre fila y campo.
- **A3** Que el mensaje de la vista nombre el primer error real en vez de quedar
  genérico.
- **A4** `prefijarImputacion()` deja `INITIAL_FORMS=0` al reconstruir las filas.
- **B1** `ajax_pending_subscriptions` lista sólo `requested`, **más** la suscripción
  que llega por `regenerar` (que es `pending`).
- **B2** El `fetch` del lote reenvía el `regenerar` actual; el endpoint lo acepta.
- **B3** Copia de la sección alineada al filtro («Solicitudes por facturar» /
  mensaje de lista vacía).

Fuera de alcance: el queryset de `InvoiceForm.subscriptions` (`forms/invoice.py:250`)
**se deja como está** a propósito — incluye `pending` porque valida el POST del
flujo `regenerar`; recortarlo lo rompería con «Select a valid choice».

## Restricciones

- No se toca `apps/commercial/templates/pages/commercial/invoice/list.html` ni
  `.../subscription/list.html`: hay una sesión paralela trabajando ahí (T18).
- Los datos reales de la BD no se tocan; las migraciones no se versionan.
- JS vanilla, sin bundlers. Comentarios y copy en español es-mx, como el archivo.

## Criterios de aceptación

- Un POST con `INITIAL_FORMS=1` (el que hoy manda el navegador) **crea** la factura
  en vez de devolver el mensaje genérico.
- Un rechazo de imputación nombra la fila y el campo que falla en la plantilla.
- El listado del formulario no ofrece una suscripción `pending` por sí sola, pero sí
  la incluye cuando es la que se está regenerando.
- La facturación por lote de una `requested` sigue funcionando igual que hoy.
- El flujo `regenerar` de una `pending` sigue creando la factura nueva y anulando la
  anterior.

## Verificación

| Cambio | Comando |
|---|---|
| Todo | `.venv/bin/python manage.py test apps.commercial` |
| Sistema | `.venv/bin/python manage.py check` |
| Estilo Python | `.venv/bin/ruff check apps/commercial && .venv/bin/ruff format --check apps/commercial` |
| Plantilla | `.venv/bin/djlint apps/commercial/templates/pages/commercial/invoice/create.html --lint` |

## Progreso

- [x] Diagnóstico con reproducción del payload real (tabla arriba) y localización
      del trap de `regenerar`.
- [x] A1, A2, A3, A4, B1, B2, B3 + tests — delegado a un writer.

## Ruta y evidencia

- **Ruta por tarea:** delegada directa → un solo writer (`gentle-ai-worker`).
- **Trigger:** regla de escritura (2+ archivos no triviales: vista, plantilla, dos
  archivos de tests).
- **TDD:** aplicable (hubo runner determinista y resultado esperado claro) →
  RED observado antes de implementar.
- **Verificación del writer:** `manage.py test apps.commercial` → 481 tests OK;
  `manage.py check` sin issues; `ruff check`/`format --check` limpios; `djlint`
  sobre `create.html` sin errores. RED: `test_un_lote_con_initial_forms_uno_crea_la_factura`
  → `AssertionError: unexpectedly None` (sin la normalización no se crea la factura).
- **Verificación independiente (RDD está `off` en este clon; `review assess`
  devolvió `high`/`unassessable` por los archivos sin trackear de la sesión
  paralela, así que se aplicó la vía RDD-off y se lanzó un verificador):**
  `gentle-ai-verify` confirmó los 6 puntos con evidencia `file:line`, corrió las
  suites focalizadas y `test_invoice_regeneration` (20 tests OK), y dejó dos
  hallazgos: el mensaje de fallback usaba voseo rioplatense («revisá») contra el
  copy neutro `es-mx`, y faltaba test del contenido del aviso.
- **Cierre de esos dos hallazgos:** `invoices.py` dice ahora «revisa» y se agregó
  `test_el_rechazo_nombra_el_motivo_real_y_no_html` (el aviso nombra el motivo y
  no lleva el markup de `ErrorList`). `manage.py test
  apps.commercial.tests.test_invoice_cost_allocation` → 32 tests OK; `ruff` limpio.

## No está commiteado

El árbol de trabajo comparte cambios con una sesión paralela
(`odd/tasks/estados-en-vivo-listados.md`, T18: `list.html`, `list_status.py`,
`actions_cell.html`, `test_list_live_status.py`, `views/subscriptions.py`) y con
trabajo previo sin commitear (`config/mail_backends.py`, `requirements/base.txt`).
Un commit acá barrería trabajo ajeno en curso, así que la entrega queda en el
árbol de trabajo a la espera de que el usuario decida.
