# PDF de factura y fecha de inicio de la línea

Rama: `feat/invoice-form-period-redesign` (ya es rama de trabajo; no hay que crear una).

## Objetivo

Dejar el PDF de la factura y el formulario de facturación manual sin los defectos
que reportó el operador: datos del contrato que no se ven, pie de firma
desalineado y una fecha de inicio de línea que el propio modelo rechaza.

## Problema (medido, no supuesto)

1. **`No. Contrato:` / `Fecha:` salen con el valor vacío en todo PDF.**
   Las etiquetas se imprimen (`template.html:311`, bbox y=294.87) pero el valor
   viene `''`. Causa: `Contract.objects.count() == 0` (y `_base_manager.count() == 0`):
   no hay contratos cargados. `_contrato_de_factura()` los resuelve por
   `Contract.objects.vigente_para(customer, period_start or issue_date.date())` y
   `_datos_proveedor()` deja `''` cuando no hay contrato.
   → **Hueco de datos, no de código.** Ya existe la UI en `/comercial/crear/contrato/`.
   Sin cambios de código en este frente (decisión del usuario).

2. **Pie de firma desalineado.** Medido con `pdftotext -bbox` sobre la misma fila:
   izquierda a y=568.6 / 620.4 / 672.1 / 723.9 y derecha a y=568.6 / 607.6 / 646.6 /
   685.6 → deriva acumulada de **12.75 pt (un renglón) por bloque**. Causa: dos
   columnas flex independientes (`template.html:174-193`) y los bloques de la
   izquierda tienen dos renglones (etiqueta + cargo) mientras los de la derecha
   tienen uno; nada obliga a que las filas de ambas columnas coincidan.

3. **`Inicio` con un valor que el modelo rechaza.** `InvoiceItem.save()` llama
   `full_clean()` (`models.py:633`) y `_validar_periodo()` exige que el inicio caiga
   dentro del período facturado. El default es `timezone.localdate()`
   (`_items_inicial`, `invoices.py:199-206`) y el JS propone lo mismo
   (`fechaDeFactura()`, `create.html:541`). Reproducido: período 2026-01-01..2026-03-31
   con el default de hoy → `RECHAZADA: "La línea no puede empezar el 13/10/2026: ese
   día está fuera del período facturado (De enero a marzo de 2026)."` Cualquier
   período que no incluya el día de hoy rompe el formulario.

4. **Mes en inglés en el PDF.** `fecha_facturacion` usa
   `strftime('%d de %B del %Y')` (`invoice_utils.py:172`) y `%B` respeta el locale
   del proceso, no `LANGUAGE_CODE='es-mx'` → "11 de October del 2026".

5. **El formset de centros de costo renderiza filas ajenas.** `InvoiceCostAllocationFormSet`
   (`forms/invoice.py:182-188`) es un `modelformset_factory` **sin `queryset=`**: un
   `modelformset` no acotado cae al manager por defecto y `initial_form_count()`
   pasa a ser `len(get_queryset())`, así que el formulario abre con **todas las
   imputaciones de la base** como filas editables (más la fila en blanco de
   `extra=1`). Con la base de dev son las dos filas `700.50207 / 100.00`; si suman
   100, la factura se imputa al centro de otro cliente sin que nadie lo note, y si
   no suman 100 el POST se rechaza sin explicar de dónde salen esas filas.

## Alcance

Entra: los puntos 2, 3, 4 y 5. No entra: el punto 1 (dato) ni el rename de rótulos,
ocultar el período sin cliente o "Regenerar" en el listado (quedan pendientes aparte).

## Restricciones

- JS 100% vanilla, sin build. Tabler. Templates con djlint (2 espacios).
- No tocar `default_permissions` ni el flujo de permisos.
- No commitear en esta pasada: el árbol se comparte con trabajo de otra sesión
  (hay cambios sin stagear ajenos). Los work-unit commits quedan para cuando el
  usuario lo pida.

## Tareas

- [x] **T1 — Formset de centros de costo acotado.** El `queryset=` va en la
  **instanciación**, no en el factory: `modelformset_factory()` no lo acepta y con
  `queryset=` adentro `manage.py check` rompía con
  `TypeError: modelformset_factory() got an unexpected keyword argument 'queryset'`
  (así lo había dejado el writer delegado). Queda en
  `InvoiceCreateView.cost_allocations_formset` (`views/invoices.py`), un
  `InvoiceCostAllocation.objects.none()` para el GET y para el POST. Test de
  regresión: con una imputación de OTRA factura en la base, `GET factura_create`
  rinde una sola fila de imputación, en blanco.
- [x] **T2 — Mes en español en el PDF.** `_fecha_en_espanol()` (`invoice_utils.py:164`)
  con la tabla `MESES`, sin depender del locale del proceso. Medido en el PDF:
  `Fecha de Facturación: 11 de octubre del 2026`.
- [x] **T3 — Default de `Inicio` dentro del período.** Server: `_items_inicial()` +
  `_primer_dia_del_periodo()` leen el período del POST o del GET; sin período caen a
  hoy (mantiene el GET vacío). JS: `fechaDeFactura()` propone el primer día del
  período elegido y, al cambiar año/mes desde/mes hasta, `normalizarLineasAlPeriodo()`
  mueve al primer día del período las filas cuya fecha queda vacía o fuera de él
  (nunca toca una fecha que ya cae dentro).
- [x] **T4 — Pie de firma alineado.** Las dos columnas flex son ahora una tabla de 4
  filas (una por firma): `.firmas-tabla` con celdas 45/10/45 y `table-layout: fixed`.
  La alineación la garantiza el layout, no la suerte de que ambos bloques midan igual.
- [x] **T5 — Verificación.** Ver abajo. Deriva medida: **0.000000** en las 4 filas.

## Criterios de aceptación

- [x] Con una imputación ajena en la base, el formulario abre con una sola fila vacía.
- [x] Un PDF de factura dice "Fecha de Facturación: 11 de octubre del 2026".
- [x] Con período enero–marzo 2026, la línea propone `01/01/2026` y el POST pasa sin
  correcciones manuales.
- [x] Firmas: 4 filas alineadas, deriva 0.000000 (antes 12.75 pt por bloque).
- [x] `python manage.py check` sin issues y `test apps.commercial` en verde (519 tests).
- Las cuatro filas de firma de la izquierda y las cuatro de la derecha arrancan a
  la misma altura en el PDF (deriva 0).
- `python manage.py test apps.commercial` en verde.

## Verificación

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test apps.commercial
.venv/bin/ruff check apps/commercial
.venv/bin/djlint apps/commercial/templates --check
```

## Verificación ejecutada

| Comando | Resultado |
|---|---|
| `.venv/bin/python manage.py check` | `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py test apps.commercial` | `Ran 519 tests ... OK` (118 s) |
| `test_invoice_cost_allocation` + `test_invoice_line_period` + `test_invoice_pdf` | `Ran 97 tests ... OK` |
| `.venv/bin/ruff check apps/commercial` | `All checks passed!` |
| `.venv/bin/djlint apps/commercial/templates --check` | `0 files would be updated.` |
| PDF real (`factura #1`, `render_pdf.py` → `pdftotext -bbox`) | deriva de firmas **0.000000** |

Coordenadas medidas en el PDF regenerado (factura `2026-0001`):

| Fila | Firma del CMP (`x=32.096`) | Firma del cliente (x=324.192) | `yMin` |
|---|---|---|---|
| 1 | Confeccionado | Recibido | 568.605905 |
| 2 | Revisado | Cargo: | 620.355905 |
| 3 | Entregado | CI: | 672.105905 |
| 4 | Fecha: | Firma: | 723.855905 |

Antes de T4 la derecha caía en 568.6 / 607.6 / 646.6 / 685.6: un renglón de
diferencia por bloque, acumulativo.

## Progreso

- 2026-10-13 — Diagnóstico cerrado y autorizado. Doc creado. Ruta: delegada al
  writer si el mecanismo de subagentes responde; si no, inline (el runtime ya
  devolvió error de free tier en `gentle-ai-explore`, a confirmar).
- 2026-10-13 — El subagente `gentle-ai-worker` se interrumpió a mitad de T3 y dejó
  T1 mal ubicado (`queryset=` en el factory). Ruta degradada a **inline** para T3
  (JS), T4 y T5; el server de T1 y T2 se conservó y se corrigió.
- 2026-10-13 — T1..T5 cerrados y verificados (tabla de arriba). Sin commit: el árbol
  sigue compartido.

## Próximo paso

- Decisión de producto abierta: **¿el card de "Período" en la facturación manual debe
  desaparecer y derivarse de las líneas?** La evidencia apoya que sí: en lote el
  período ya no se elige a mano sino que lo deduce `meses_de_la_suscripcion()`
  (`views/invoices.py:53`) de `start_date` + `cantidad` + categoría del servicio, y la
  línea manual trae exactamente esos tres datos (el rótulo de `cantidad` se renombra a
  "Cantidad de meses/días" según la categoría en `forms/invoice.py:83`). Hoy la
  duplicación obliga a que el período sea superconjunto de los inicios
  (`_validar_periodo`, `models.py:617`) y es la causa de la familia de bugs del punto 3.
  Pendiente de respuesta del operador: si alguna vez necesita un período **más ancho**
  que las líneas (facturar febrero y que la factura diga "enero–marzo"), el card se
  precarga derivado y editable; si no, se elimina.
- Fuera de alcance, siguen pendientes: renombrar "Mes desde/hasta" → "Primer/Último mes
  facturado", ocultar `#period-months-group` hasta elegir cliente, "Regenerar" en el
  listado cuando `items_total == 1`.
