# Período de facturación como meses seleccionables

## Objetivo

Que el período facturado deje de ser texto libre y pase a ser un rango de meses
elegible (desde / hasta), para que se pueda validar, agrupar en la facturación por
lote e imprimir igual que las facturas reales del CMP.

## Problema (verificado contra código)

`Invoice.period_label` es un `CharField(255)` con `help_text='Texto libre tal como
se imprime'`. Consecuencias:

1. **No valida nada.** Nada impide que una línea de servicio sea de un mes fuera
   del período escrito. No hay forma: es una frase, no un dato.
2. **El lote no agrupa por período.** `InvoiceQuerySet.for_subscription`
   documenta que "la facturación por lote agrupa suscripciones con el mismo
   período", pero no hay código que agrupe. El docstring describe intención.
3. **Un texto único no describe dos ventanas.** Un cliente con pronóstico desde
   el 10 y agrometeorológico desde el 3 tiene dos ventanas distintas; una sola
   frase o miente o queda ambigua.
4. **El operador lo teclea.** El usuario pidió poder elegirlo.

## Decisiones tomadas

- **Rango desde/hasta, confirmado por el usuario:** el operador elige mes y año
  de arranque y mes y año de cierre; el texto se acomoda solo. Un solo par año/mes
  no puede expresar un rango, así que hacen falta dos.
- **Sin tabla `InvoicePeriod`.** Se descartó: con un rango, dos `DateField`
  (`period_start` = primer día del mes inicial, `period_end` = último día del mes
  final) expresan lo mismo con menos piezas, y la validación de una línea pasa a
  ser una comparación de fechas en vez de una consulta.
- **Sin checkboxes de meses.** Descartado por el usuario: quince casillas para
  elegir dos meses es la fricción que complained del principio.
- **`issue_date` sigue siendo automática.** Se emite hoy; el período puede estar
  en el pasado. Es el caso real de la certificación agrometeorológica que el
  cliente no pudo cumplir a tiempo.
- **No hay nada en producción**, así que no hay backfill ni decisión de datos.

## Restricciones

- `apps/commercial/migrations/*` está en `.gitignore`: sólo se versiona
  `__init__.py`. El esquema no viaja en el repo y una migración de datos se
  perdería en silencio. Nada puede depender de backfill.
- El PDF imprime una sola línea: `template.html:304`
  (`Período Facturación: {{ periodo_facturacion }}`). La salida debe seguir
  diciendo "Mes de mayo y junio de 2025" y "octubre y noviembre del 2025".
- Ningún filtro ORM usa hoy `period_label`. Verificado sobre los 4 archivos de
  código y 3 de tests que lo referencian.
- Sin JavaScript obligatorio: el selector tiene que dejar elegir meses con el
  markup de Tabler, no depender de un widget de terceros.

## Tareas

- [x] **T1 — Rango en el modelo.** `Invoice.period_start` y `Invoice.period_end`
      como `DateField(null, blank)`. `period_start` se normaliza al primer día del
      mes elegido y `period_end` al último, en el form, no en el modelo.
- [x] **T2 — `period_label` pasa a propiedad derivada.** Se borra el `CharField`
      y se define la propiedad componiendo la frase: un solo mes → "Mes de enero
      de 2026"; varios → "De enero a febrero de 2026". Con respaldo en
      `issue_date` cuando no hay período. Así el PDF y `_periodo_facturacion()` no
      cambian, y no quedan dos fuentes de verdad que diverjan.
- [x] **T3 — Formulario.** Cuatro selects: mes+año desde, mes+año hasta. Debe
      rechazar un período vacío y un rango invertido (`hasta` anterior a `desde`).
- [x] **T4 — Validación de integridad.** Cada línea de la factura manual debe caer
      dentro de `[period_start, period_end]`. Vive en el modelo, no en la vista.
- [x] **T5 — Agrupación por lote.** La facturación por lote agrupa suscripciones
      por su rango de período y emite una factura por grupo.
- [x] **T6 — Selector en el template.** Reemplazar el input de texto por los cuatro
      selects, con el estilo de las demás cards de sección
      (`subheader text-muted fw-medium`) y espacio vertical consistente.
- [x] **T7 — Tests.** Reescribir los que codifican el contrato viejo
      (`test_invoice_period_label.py`, las partes de `period_label` en
      `test_invoice_line_period.py` y `test_invoice_regeneration.py`) y agregar
      los de integridad: línea fuera del período, rango invertido, período
      vacío, un mes vs rango en el texto del PDF, agrupación del lote.
- [x] **T7b — Espaciado del formulario de factura.** El botón "Facturación
      manual" y el card "Añadir servicios" no tienen separación con el card de
      arriba: alinearlos con el resto (`mt-3`), como el card de imputación.

## Ronda 2 (feedback del usuario sobre la pantalla)

La pantalla quedó con defectos que la suite no ve porque son de interacción/HTML.
El `<div>` de cierre del card de período faltaba, así que `#dynamic-fields`
(contenido de lote y de facturación manual) quedaba *dentro* del card de período.
Esa única etiqueta sin cerrar explica casi todos los síntomas.

- [x] **T14 — Selector de período de un solo año.** En `InvoiceForm` reemplazar
      `year_from`/`year_to` por un único `year`; `month_from`/`month_to` quedan
      dentro de ese año (se elimina el rango "febrero 2026 → febrero 2025").
      `anios_del_periodo` pasa a devolver años. `clean()`: el período es
      obligatorio **sólo** cuando no hay suscripciones elegidas (facturación
      manual); en lote no se pide ni se valida. `year` arranca en el año actual.
- [x] **T15 — Card de período oculto en lote + "Aceptar" funcional.** Cerrar el
      `</div>` faltante para que `#dynamic-fields` sea hermano del card;
      `ocultarPeriodo` oculta la **columna entera** del card (`closest('.col-12')`)
      y no sólo la fila de selects; se muestra en facturación manual y se oculta
      mientras el lote está visible; guarda en el submit con aviso si no hay
      suscripción marcada ni modo manual, para que Aceptar nunca sea un no-op
      silencioso.
- [x] **T16 — Alineación y espaciado.** Quitar el `mb-3` del include de fecha en
      la fila de ítems (parámetro opcional `compact`) para que el botón "eliminar
      servicio" quede alineado con los inputs (hoy el margen del include estira la
      fila 16 px y el botón baja); revisar que el card "Añadir servicios" y el
      header de lote queden separados del card de período.
- [x] **T17 — Podar tests muertos.** Borrar los tests que sólo verifican la
      ausencia de cosas ya removidas o introspeccionan firmas privadas
      (`test_el_formulario_de_factura_no_tiene_fechas`,
      `test_la_pantalla_no_tiene_el_rango_de_fechas`,
      `test_el_conteo_de_dias_desaparece`, los dos
      `test_process_*_no_declara_fechas` y
      `test_un_post_con_las_fechas_viejas_se_ignora`). Conservar el resto.
- [ ] **T18 — Estados en vivo en listados (movido).** En el listado de
      suscripciones (botón "Aprobar pago" / estado del PDF) y en el de
      facturación, refrescar el estado sin recargar la página ni la tabla.
      Se separó a `odd/tasks/estados-en-vivo-listados.md`: es otra feature y no
      toca el formulario de período.

## Criterios de aceptación

- El operador elige mes y año; no escribe texto. Un mes → texto de un mes; varios
  → texto de rango.
- Una línea cuyo `start_date` cae fuera de los meses elegidos no se guarda.
- El PDF sigue imprimiendo un período legible: "Mes de diciembre de 2025" para uno
  solo, y un rango para varios. Las tres facturas reales dicen "Mes de mayo y junio
  de 2025", "octubre y noviembre del 2025" y "Mes de diciembre de 2025": el texto
  debe conservar el sentido, no clonar la redacción antigua del CMP.
- La facturación por lote emite una factura por período.
- `apps.commercial` y `apps.home` completos en verde, ruff y djlint limpios.

## Checks

- `.venv/bin/python manage.py test apps.commercial`
- `.venv/bin/python manage.py test apps.home`
- `.venv/bin/ruff check apps/` y `.venv/bin/ruff format --check apps/`
- `.venv/bin/djlint apps/commercial/templates/pages/commercial/invoice/ --check`

## Progreso

T1–T13 y T7b implementados sobre `feat/invoice-form-period-redesign`. La limpieza
de comentarios y el fix de layout originales están en `fba6ecf` y `69f9b8f`.

Verificación observada (2026-10-11):

- `.venv/bin/python manage.py test apps.commercial` → `Ran 471 tests ... OK`
- `.venv/bin/python manage.py test apps.home` → `Ran 259 tests ... OK`
- `.venv/bin/python manage.py check` → sin issues
- `.venv/bin/ruff check apps/` → All checks passed
- `.venv/bin/ruff format --check apps/` → 251 files already formatted
- `.venv/bin/djlint <invoice+contract templates> --check` → 0 files would be updated

Correcciones de la sesión:

- `_contrato_de_factura` (`invoice_utils.py`): se eliminó el bloque muerto que
  usaba `date` sin importar (F821) y convertía una `date` a sí misma; `fecha` ya
  era siempre `date`.
- Tests obsoletos alineados a la API nueva (`Contract` por cliente con
  `start_date`/`validity_years`; payloads de factura con `month_from`/`year_from`/
  `month_to`/`year_to`; `process_batch_invoice(customer, commercial_registry,
  subscriptions)`).
- Limpieza ruff (F401/W292) y reformateo ruff/djlint.

Commit de la unidad de trabajo: `70c2203`.

Ronda 2 (T14–T17) implementada sobre la misma rama. Verificación observada
(2026-10-11):

- `.venv/bin/python manage.py test apps.commercial` → `Ran 465 tests ... OK`
  (471 base − 6 tests muertos podados)
- `.venv/bin/python manage.py test apps.home` → `Ran 259 tests ... OK`
- `.venv/bin/python manage.py check` → sin issues
- `.venv/bin/ruff check apps/` y `ruff format --check apps/` → limpios
- `.venv/bin/djlint <invoice + date_field> --check` → 0 files would be updated
- Spot check del parent: `test_invoice_line_period` + `test_invoice_period_label`
  → `Ran 49 tests ... OK`; `#dynamic-fields` quedó hermano del card de período
  (L90-92 cierran `card-body`, `card` y el `col-12` del include).

El guard de submit se engancha a `form.needs-validation`: el único listener
`submit` que existía pertenecía al modal `#company-settings-form` (guardado AJAX)
y el modal no lleva `needs-validation`, así que el selector es único en la página
y no puede interferir con el modal.

Commit de la unidad de trabajo (Ronda 2): `f71c865`.

---

# Contrato por cliente con vigencia

## Objetivo

Que el contrato tenga vigencia real y que no se pueda facturar a una jurídica un
mes que no estuvo cubierto por ningún contrato suyo. Es la regla que el usuario
definió: el contrato es por cliente, es una medida del centro, y las personas
naturales se facturan sin contrato.

## Problema (verificado contra código)

`Contract` existe pero **no es el contrato que el usuario describe**:

1. **Es por suscripción, no por cliente.** `Contract.subscription` es un
   `OneToOneField` a `ServiceSubscription`. Un cliente con dos servicios tiene
   dos contratos distintos. El usuario lo define por cliente.
2. **No tiene vigencia.** Tiene `date` (la fecha del contrato) y
   `commercial_registry`. No hay `start_date` ni `end_date`. "No se puede facturar
   a un cliente con contrato vencido" hoy es imposible de cumplir: no hay ningún
   vencimiento que mirar.
3. **`OneToOne` impide renovar.** Una suscripción no puede tener dos contratos,
   así que una renovación obliga a editar el primero y perder el histórico.
4. **El modelo no puede expresar la excepción de las naturales.** No sabe si el
   cliente es natural o jurídica. El discriminador sí existe y ya se usa:
   `Customer.ClientType.JURIDICA` y `es_juridica` en `invoice_utils.py:163`.
5. **El PDF resuelve el contrato por suscripción.** `_contrato_de_factura`
   (`invoice_utils.py:110`) usa `subscription.contract`. Con contrato por cliente
   tiene que resolver el que cubre el período facturado.

## Decisiones tomadas por el usuario

- **Un contrato por cliente**, con varios registros cuando hay renovación (cada
  uno con su `number` y su rango).
- **Fecha + vigencia en años.** El contrato guarda la fecha del contrato
  (`start_date`) y los años de vigencia (`validity_years`, 2 por default,
  ampliables por el usuario). La fecha de vencimiento (`end_date`) se **deriva**
  de esos dos datos: no se edita ni se guarda aparte, para que no existan dos
  fuentes de verdad que puedan divergir.
- **El registro comercial no es del contrato.** Es un dato de la empresa
  emisora (`CompanySettings.registro_comercial`), se edita en Configuración
  Empresa, y el formulario de contratos no lo pide.
- **Las personas naturales no llevan contrato** y se facturan igual: es una
  medida del centro, no un descuido.
- **No se factura a una jurídica un mes no cubierto** por ninguno de sus contratos.

## La regla de vigencia

Un mes es facturable si estuvo dentro de la vigencia de algún contrato del
cliente. Un mes anterior al inicio o posterior al fin no lo es.

Esto **no** se deduce de las facturas de muestra, que son de 2025 y están
vencidas: la regla sale de la definición de vigencia y del caso real del
usuario, que necesita facturar meses pasados para avalar una certificación
agrometeorológica cuando el cliente no pudo cumplir su plan. Un bloqueo por
"el contrato está vencido hoy" haría ese caso imposible.

Supuesto explícito, a corregir por el usuario si no es lo que quiere: la
renovación de un contrato vencido para cubrir meses pasados se hace creando un
contrato nuevo con vigencia retroactiva, no editando el anterior.

## Impacto en el resto del cambio

La validación "cada línea cae dentro del período" (T4) y "el mes facturado está
cubierto por un contrato" comparten la misma forma: una comparación de fechas.
Viven en el modelo, no en la vista.

## Tareas

- [x] **T8 — `Contract` por cliente con vigencia derivada.** `customer` FK con
      `related_name='contracts'`; `start_date` (fecha del contrato) y
      `validity_years` (años, default 2, mínimo 1); se borran `subscription`
      (OneToOne), `date` y `commercial_registry`. `end_date` es una **propiedad
      derivada** (`start_date` + `validity_years` años, con 29/02 → 28/02).
      Varios contratos por cliente, para renovaciones.
- [x] **T9 — Default de 2 años.** El form propone `start_date`=hoy y
      `validity_years`=2, editables.
- [x] **T10 — Cobertura.** Un método que diga si un contrato cubre una fecha, y una
      consulta que devuelva el contrato vigente de un cliente para una fecha.
- [x] **T11 — Bloqueo de facturación.** La factura de una jurídica exige que el
      período facturado esté cubierto. Las naturales no se chequean. Error legible
      en español.
- [x] **T12 — PDF.** `_contrato_de_factura` resuelve el contrato vigente del
      cliente para el período facturado. El registro comercial que imprime el PDF
      sale de `CompanySettings.registro_comercial`, no del contrato.
- [x] **T13 — Tests.** Contrato por cliente con varios registros, cobertura por
      fecha, natural exenta, jurídica sin cobertura rechazada, PDF con el contrato
      correcto, default de 2 años.

## Checks

Iguales que los de esta feature.
