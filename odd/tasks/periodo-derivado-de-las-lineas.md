# Período derivado de las líneas

Rama: `feat/invoice-form-period-redesign` (ya es rama de trabajo).

## Objetivo

Que el período facturado **no se declare: se reporte**. Sale de lo que hay en la
factura (o en la solicitud) y nunca es más ancho que eso. Con eso, el formulario de
facturación manual pierde tres selects que duplicaban un dato que las líneas ya
traen, y el operador ve el período calculado mientras carga en vez de tener que
mantenerlo a mano.

## Problema (medido, no supuesto)

1. **El período está duplicado.** En lote nadie lo elige: `meses_de_la_suscripcion()`
  (`views/invoices.py:53`) lo deduce de `start_date` + `cantidad` + categoría, y
  `_facturar_grupo` escribe `period_start/period_end = rango_desde_meses(meses)`.
  En manual el operador lo vuelve a escribir en tres selects. Dos fuentes de verdad
  para el mismo hecho.
2. **La duplicación es la causa de una familia de bugs.** `_validar_periodo`
  (`models.py:605`) exige `period_start <= inicio <= period_end` y la fecha de la
  línea se derivaba *del* período: el default "hoy" con un período que no incluye
  hoy rompía el formulario (bug cerrado en `pdf-factura-y-fecha-de-inicio.md`).
  Si el período se deriva *de* las líneas, esa clase de bug no puede existir.
3. **El dato que el card agrega es el FIN.** El período debe contener todos los
  inicios, así que el único valor libre es el fin — y el fin lo determina la
  cantidad (`agrometeo` = meses, `pronostico` = días). El operador lo escribe dos
  veces: como cantidad en la línea y como "mes hasta" en el card.

## Evidencia de que la derivación es total (no hay casos sin cubrir)

`InvoiceItemForm` (`forms/invoice.py:23-77`) vuelve obligatorios los tres datos:
`service` (`required=True`, acotado a servicios comerciales activos), `start_date`
(`Inicio`, requerido) y `cantidad` (`min_value=1`, requerido). Y dos categorías
existen en el catálogo: `agrometeo` (meses) y `pronostico` (días) —
`Service.SERVICE_CATEGORY_CHOICES`. No hay línea válida sin mes computable.

## Alcance

**Entra:**
- Una única derivación a nivel de línea, usada por los dos caminos (solicitud y línea manual).
- El período de la factura manual se calcula desde las líneas y se guarda en
  `period_start`/`period_end` como hoy (el PDF, la búsqueda de contrato y las
  facturas ya emitidas dependen de esas columnas).
- El card de Período desaparece del formulario; en su lugar se muestra el período
  derivado, de sólo lectura, actualizándose mientras se cargan las líneas.
- El default de `Inicio` deja de depender del período: si la línea viene de una
  solicitud (`?regenerar=`) toma la fecha de esa solicitud; si es nueva, hoy.
- Los tests que fijan el acoplamiento viejo se reescriben.

**No entra:**
- `_validar_contrato` (`models.py:454`): **no se toca**. Observación registrada: en
  estos caminos no corre (la factura se crea con `Invoice.objects.create`/`save()`,
  y `Invoice.save()` no llama `full_clean()`), y con `Contract.objects.count() == 0`
  convertirlo en un gate duro bloquearía toda la facturación. Queda como está.
- El hueco de datos de contratos (cargar contratos) y los pendientes ya conocidos:
  "Regenerar" en el listado con `items_total == 1`. El pendiente "ocultar el período
  hasta elegir cliente" queda **obsoleto**: el card desaparece.
- Las facturas ya emitidas: sus `period_start/period_end` guardados no se tocan.

## Restricciones

- JS 100% vanilla, sin build. Sin tocar `models.py` en lo que refiere a validaciones
  existentes (`_validar_periodo` se conserva como invariante defensiva, ahora
  garantizada por la derivación).
- Sin commit: el árbol está compartido.
- Artefactos en español neutro.
- Líneas ya emitidas y el PDF no cambian de formato: sólo cambia de dónde sale el rango.

## Tareas

- [ ] **T1 — Una sola derivación.** `meses_de_la_linea(inicio, cantidad, categoria)`
  y `rango_desde_meses(meses)` en `models.py` (junto a `primer_dia_del_mes` y
  `mes_siguiente`, que ya viven ahí). `meses_de_la_suscripcion` pasa a ser un adaptador
  que saca los tres datos de la suscripción y delega: el lote no cambia de resultado.
  Ruta: inline (2 archivos, mecánica una vez leído el código).
- [ ] **T2 — El manual deriva el período.** `_guardar_factura_manual` arma la lista de
  líneas limpias, calcula los meses de cada una, une los conjuntos y crea la factura
  con `rango_desde_meses(union)`. `process_manual_invoice` deja de pasar `periodo`.
  Ruta: inline.
- [ ] **T3 — El formulario deja de pedir el período.** Quitar `year`, `month_from`,
  `month_to` de `InvoiceForm` (y su `__init__`/`clean`), `periodos_desde_el_formulario`,
  `meses_del_periodo` y `anios_del_periodo` si quedan sin uso. Ruta: inline.
- [ ] **T4 — El período se muestra, no se pide.** En `create.html`: fuera el card de
  período; una línea de solo lectura que muestra el período derivado y se actualiza
  con las líneas (mismo cálculo que el servidor, sobre `data-categoria` del servicio).
  `_items_inicial` toma la fecha de la solicitud a regenerar, o hoy. Ruta: inline.
- [ ] **T5 — Tests.** Reescribir los dos que fijan "la línea arranca en el primer día
  del período" (`test_la_fecha_por_defecto_es_la_fecha_de_la_factura`,
  `test_cada_linea_nueva_arranca_en_la_fecha_de_la_factura`) y los que exijan el
  período en el POST manual. Nuevos: la unión de dos líneas, una línea por días que
  cruza de mes, y que el formulario ya no pida período.
- [ ] **T6 — Verificación.** `manage.py check`, `test apps.commercial`, `ruff`, `djlint`,
  y un PDF real para confirmar que el período impreso es el de las líneas.

## Criterios de aceptación

- El lote factura exactamente lo mismo que antes (mismos `period_start/period_end`).
- Una factura manual con una línea `agrometeo` de 1 mes desde mayo dice "mayo" en el PDF.
- Con dos líneas desde mayo y junio, el período es el de la unión (mayo..junio o más).
- El formulario manual no tiene selects de año/mes y no rechaza un POST por falta de período.
- `manage.py check` sin issues y `test apps.commercial` en verde.

## Presupuesto de entrega

Forecast: ~200 líneas autoradas (models ~35, view ~30, form ~40 de borrado, template/JS
~60, tests ~60). Bajo el umbral de ~400 → un solo PR/slice, se entrega junto con la
feature anterior. Sin commit hasta que el usuario lo pida.

## Progreso

- 2026-10-13 — Autorizado por el usuario ("si"), con el alcance cerrado: el período se
  deriva siempre, nunca es más ancho que lo facturado. Doc creado. Ruta: inline.

## Próximo paso

Implementar T1.
