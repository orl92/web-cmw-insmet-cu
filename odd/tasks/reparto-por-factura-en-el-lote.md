# El reparto de una factura del lote es de ESA factura

## Objetivo

Que ninguna factura creada por el lote de facturación lleve imputada a un centro de
costo que no provenga de sus propios servicios, y que el borrado duro de una factura
devuelva la solicitud al listado en vez de dejarla invisible.

## Problema

### 1. El reparto global se copia a cada factura del lote (defecto observado en pantalla)

Con 3 solicitudes pendientes del cliente **CCS Jesús Suarez Gayol** el operador marcó
las tres, aceptó, y **cada una de las 3 facturas generadas salió con los DOS centros de
costo de la selección**, aunque ninguno de los dos servicios de cada factura comparta
centro con las otras.

Causa verificada por lectura de código — un solo formset para todo el formulario, pasado
a cada vuelta del bucle:

- `views/invoices.py:307` construye **un** `cost_formset` (`InvoiceCreateView.form_valid`).
- `views/invoices.py:318-328` lo pasa entero a `process_batch_invoice`.
- `views/invoices.py:435-443` agrupa por `meses_de_la_suscripcion(sub)` y llama a
  `_facturar_grupo(..., cost_formset)` **una vez por grupo, con el mismo formset**.
- `views/invoices.py:520` lo persiste en cada factura creada:
  `self._save_cost_allocations(invoice, cost_formset)`.

Evidencia en la base real de desarrollo: las 3 suscripciones tienen códigos de servicio
distintos y sólo dos centros aparecen entre las tres (`700.50107` para la suscripción 4
por el servicio `700501072507005`; `700.50207` para las suscripciones 2 y 5 por
`700502072307032` y `700502072507017`). Una factura con el servicio 4 no tiene por qué
declarar el `700.50207`.

Testigo del lado del navegador: `prefijarImputacion()` deriva la **unión** de las
marcadas (`create.html:790`, leyendo `oracle.dataset.centro` de cada
`.subscription-check:checked`), y ese único reparto es el que llega por POST.

### 2. La validación del 100 % también es única para todo el lote

`views/invoices.py:307-316` valida el formset una sola vez. Es la misma raíz: mientras
haya **un** reparto para **N** facturas, no existe forma de darle a cada una el suyo.
Este documento **no** lo cambia (ver "Fuera de alcance"); deja el hecho registrado.

### 3. El borrado duro deja la solicitud invisible

`InvoiceHardDeleteView` (`views/invoices.py:815-830`) borra la factura y sus ítems pero
**no revierte el estado de pago de las suscripciones** que facturó: quedan en `pending`.
`ajax_pending_subscriptions` (`views/invoices.py:880`) lista `payment_status='requested'`
más la que llega por `regenerar` (`:884`), así que esa solicitud **desaparece de la lista
del lote** y ya no hay forma de volver a facturarla desde la pantalla. Anular sí la
devuelve (`views/invoices.py:755-756`), lo que hace que el usuario vea dos
comportamientos distintos para lo que él llama "eliminar".

## Por qué importa

El punto 1 es exactitud de dinero: el reparto a centros de costo es lo que después
distribuye el importe facturado entre centros en la contabilidad del CPM. Una factura
que declara un centro que no le corresponde no es un detalle cosmético: es un asiento
mal imputado. Y es reproducible a mano con los datos que hoy están en la base.

El punto 3 es dinero no cobrado: una solicitud que no se puede volver a ver no se puede
volver a facturar.

## Alcance

- **T1** `process_batch_invoice`: cuando el lote produce **más de un** período, cada
  factura se imputa con **sus propios** centros, derivados de sus propios ítems. Cuando
  produce **uno solo**, el reparto del operador se respeta igual que hoy (no hay
  regresión: es el caso en que su tarjeta sí representa exactamente una factura).
- **T2** `InvoiceHardDeleteView`: devolver a `requested` las suscripciones de sus ítems
  que estén en `pending`/`requested`, con el MISMO criterio que `CancelInvoiceView`; no
  tocar las `paid`.

Fuera de alcance (decidido, no olvidado):

- La **forma de la UI** del reparto cuando el lote produce varias facturas (tarjetas por
  factura vs. derivación automática mostrada como vista previa). Lo bloquea un dato
  duro: **no existe vista de edición de una factura** (`invoices.py` sólo tiene
  `InvoiceCreateView`, `InvoiceListView`, `InvoicePDFDownloadView`,
  `CancelInvoiceView` y `InvoiceHardDeleteView`), así que la imputación se fija al crear
  la factura y no se puede corregir después. Eso obliga a que el reparto de una factura
  del lote se pueda confirmar **al crearla**, y decide el diseño entre tarjetas por
  factura o un camino de edición posterior. Es una decisión de producto del usuario.
- Los datos con valor en la lista de solicitudes (importe, centro legible, unidad) y las
  3 aristas conocidas de `prefijarImputacion()` + la advertencia visible del 100 %: van
  en la misma pasada de `create.html` que resuelva lo anterior.
- La clave de agrupación del lote (`meses_de_la_suscripcion`) **no se toca**: agrupa por
  período facturado, que es la misma derivación de la factura manual, y eso es
  deliberado (`invoices.py:318-322` lo documenta).

## Restricciones

- No se toca `apps/commercial/templates/pages/commercial/invoice/list.html`,
  `.../subscription/list.html`, `templates/includes/commercial/invoice/actions_cell.html`,
  `.../status_cell.html`, `apps/commercial/views/subscriptions.py` ni
  `apps/commercial/views/list_status.py`: hay una sesión paralela trabajando ahí.
- **No se commitea ni se stagea nada.** El índice de git ya tiene cambios preparados de
  otra sesión (renames de `openspec/changes/022-024`, `requirements/base.txt`, borrados
  de docs vendoreados): un `git add`/`git commit`/`git stash` barrería trabajo ajeno.
- No se escribe en `db.sqlite3` ni en `media/`. Las migraciones no se versionan.
- Comentarios y copy en español es-mx neutro (sin voseo), como el resto del archivo.
- Sin JS nuevo en esta tarea: es servidor + tests.

## Criterios de aceptación

1. Un lote con **varios** períodos crea N facturas y cada una queda imputada **sólo** con
   los centros de sus propios ítems. Réplica del caso real: 3 suscripciones con 2 centros
   distintos → 3 facturas, la del servicio 4 con `700.50107` al 100 % y las otras con
   `700.50207` al 100 %.
2. Un lote con **un solo** período sigue usando el reparto que confirmó el operador
   (mismo comportamiento que hoy).
3. Si ningún ítem de una factura tiene un centro derivable (código corto o vacío), esa
   factura **no inventa** filas de imputación.
4. El borrado duro de una factura deja sus suscripciones en `requested` si estaban en
   `pending`/`requested`, y **no** modifica las `paid`.
5. Nada de esto cambia el comportamiento de anular una factura.

## Verificación

| Cambio | Comando |
|---|---|
| Sistema | `.venv/bin/python manage.py check` |
| Focalizado | `.venv/bin/python manage.py test apps.commercial.tests.test_batch_cost_allocation_per_invoice` |
| Suite de la app | `.venv/bin/python manage.py test apps.commercial` |
| Estilo | `.venv/bin/ruff check apps/commercial && .venv/bin/ruff format --check apps/commercial` |

## Progreso

- [x] Diagnóstico con evidencia de código (`invoices.py:307`, `318-328`, `435-443`, `520`,
  `815-830`, `880-884`) y de datos reales (centros por código de servicio).
- [ ] T1 — reparto por factura en el lote (delegado a un writer).
- [ ] T2 — el borrado duro libera la suscripción (delegado al mismo writer).

## Ruta y evidencia

- **Ruta por tarea:** delegada directa → un solo `gentle-ai-worker`.
- **Trigger:** regla de escritura (2+ archivos no triviales: vista + tests nuevos).
- **TDD:** aplicable (runner determinista, resultado esperado claro) → RED observado
  antes de implementar.
- **Espejo en Engram:** PENDIENTE. `mem_save` devuelve
  "gentle-engram could not confirm Engram session registration… verify that the Engram
  server is available and retry". El progreso local queda como fuente; se resincroniza
  cuando Engram vuelva.

## No está commiteado

El árbol comparte cambios sin commitear con una sesión paralela
(`odd/tasks/estados-en-vivo-listados.md`) y hay cambios preparados de otra sesión en el
índice. La entrega queda en el árbol de trabajo a la espera de que el usuario decida.
