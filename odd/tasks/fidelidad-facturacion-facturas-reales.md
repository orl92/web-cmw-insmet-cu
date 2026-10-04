# Fidelidad de facturación contra facturas reales

## Objetivo

Alinear el módulo de facturación y su PDF con la estructura real de las facturas
del CMP, y corregir los defectos de modelo que impiden facturar correctamente a
personas naturales y en la facturación por lote.

## Problema (verificado contra código y documentos, no supuesto)

El usuario aportó tres facturas reales del CMP (182, 279, 276) en formato `.doc`
binario OLE2. Se extrajeron con un parser del piece table de Word y se compararon
contra el PDF actual.

1. **P0 — Centro de Costo hardcodeado y por tanto falso.**
   `template.html:342` escribe literal `Centro de Costo 700.50107 100 %`. Las tres
   facturas reales reparten entre uno y tres centros, con porcentajes que cambian
   por factura: 182 = `700.50107 100%`; 279 = `700.50207 90%` + `700.50407 10%`;
   276 = `700.50107 25%` + `700.50207 65%` + `700.50407 10%`. **Dos de tres
   facturas reales quedarían con la imputación contable incorrecta.**

2. **El reparto NO es derivable de los ítems.** La factura 276 tiene un único ítem
   (cant 4, $1 281.40) repartido en tres centros 25/65/10. Con un solo ítem es
   imposible generar tres porcentajes desde los montos: es input del operador,
   independiente de las líneas.

3. **El centro por defecto SÍ es derivable.** Los tres centros
   (`700.50107`, `700.50207`, `700.50407`) aparecen como prefijo del código de
   servicio: `700501072507005` → `700.50107|2507|005`;
   `700502072307032` → `700.50207|2307|032`. Permite prellenar, no deducir.

4. **"Período Facturación" no es un rango de fechas: es texto libre.** Los tres
   documentos dicen "Mes de mayo y junio de 2025", "octubre y noviembre del 2025"
   y "Mes de diciembre de 2025". Hoy el PDF compone
   `Desde {start} hasta {end}` (`invoice_utils.py:139`) y, cuando la factura no
   viene de una suscripción, `views/invoices.py:511-512` pasa `issue_date` dos
   veces y produce "Desde 01/08/2025 hasta 01/08/2025".

5. **`U/M` siempre es `U` en las facturas reales**, incluso para "Certificación
   Agrometeorológica Especializada **por meses**" (cant 2): el periodo va en la
   descripción. Hoy `forms/invoice.py:56-59` fuerza `MES`/`DÍA`.

6. **Bug activo — el contrato se pierde en la facturación por lote.**
   `Invoice.status_display` documenta que la facturación "cubre varias
   suscripciones" (`models.py:401-408`) y `InvoiceForm.subscriptions` es
   `ModelMultipleChoiceField`, pero `_contrato_de_factura()` lee **un solo**
   `invoice.subscription.contract` (`invoice_utils.py:51-64`). En un lote con N
   suscripciones muestra el contrato de una arbitraria, o ninguno. El PDF real
   muestra **un contrato por factura**.

7. **Bug — el contrato está anclado a la suscripción, no al cliente.**
   `Contract.subscription` es `OneToOneField` (`models.py:473-478`). El contrato es
   entre la institución y el **cliente**. Un cliente con tres servicios necesita
   hoy tres contratos idénticos duplicados.

8. **Bug — las personas naturales no pueden facturar ni nombrarse bien.**
   - `Contract.__str__` (496) y `Certificate.__str__` (527) imprimen
     `customer.company_name`, vacío en natural → `None`.
   - `InvoiceForm.commercial_registry` es `required=True` (`forms/invoice.py:83-88`).
   - `Customer.account` es `CharField(max_length=16, unique=True)` **sin `blank`
     ni `null`** (`models.py:59-64`): obligatorio y único para todos.

9. **Riesgo a verificar** — `Customer.reeup` y `nit` son `blank=True, null=True,
   unique=True` (`models.py:43-57`). Si el form guarda `''` en vez de `None`, el
   segundo cliente vacío rompe el UNIQUE.

## Decisiones tomadas con el usuario

- **`U/M` se alinea a `U`.** El periodo va en la descripción del ítem.
- **NO partir `Customer` en dos tablas.** `client_type` ya existe
  (`models.py:20-30`) y `display_name` (93-113) ya bifurca por tipo; el
  discriminador ya está. La única diferencia real es qué campos son obligatorios,
  que es el caso canónico de *una tabla con columnas opcionales + validación
  condicional*, no de herencia de tablas. Partirlo duplicaría modelos, forms,
  admins y **8 permisos en vez de 4**, obligaría a una FK polimórfica y tocaría
  ~67 referencias a `ServiceSubscription.customer`, con ganancia de dominio cero.

## Descartado tras verificación

- **`period_start` / `period_end` como `DateField`.** Propuesta mía anterior,
  falsada por los tres documentos: el periodo es una etiqueta de texto libre.
- **Derivar el reparto de Centro de Costo de los ítems.** Falsado por la 276
  (un ítem, tres porcentajes).
- **Copiar las erratas de los documentos originales** ("Centro costo",
  "700. 50207", "Período Facturación::", espacios dobles). El PDF debe quedar
  como la versión consistente; eso es una mejora, no una regresión.
- **"Factura generada el".** El nuestro es correcto; los tres archivos comparten
  el timestamp `18/12/2025 11:31:50` porque se exportaron en lote. No se toca.

## Alcance

### Etapa 1 — autorizada (sin riesgo de datos, reversible)

- [x] **T1** `InvoiceCostAllocation` (`invoice`, `codigo`, `porcentaje`) con
      validación de que las filas suman 100. Prefill desde el prefijo del código
      de los servicios facturados. Render en el PDF en lugar del literal hardcodeado.

      Decisiones que quedaron fijadas al implementarlo:
      - El reparto es dato del operador, no derivado de los ítems (la 276 lo prueba:
        un ítem, tres centros). Por eso es tabla, y el prefill sólo precarga el
        centro, nunca el reparto real.
      - La suma 100 % se valida en el formset, no en el modelo: en el modelo
        impediría borrar una fila y rehacer el reparto con `can_delete`.
      - El formset exige al menos una fila viva: una factura comercial sin
        imputación es el defecto que este modelo viene a cerrar.
      - Las asignaciones se guardan antes de encolar la tarea de PDF, porque el PDF
        se genera aparte y saldría sin imputación si aún no estuvieran en la base.
      - La persistencia es explícita (`_save_cost_allocations`) y no
        `formset.save()`: la factura existe recién cuando se guarda, y un formset
        atado a la línea no resuelve la FK hacia algo que aún no estaba en la base.
      - El prefill del GET sólo se puede derivar cuando ya se sabe el cliente (el
        caso de regenerar); sin él no hay códigos y no se inventa un reparto.
- [x] **T2** `Invoice.period_label` (`CharField`, `blank=True`, `max_length=255`).
      El PDF muestra la etiqueta; si está vacía, cae a la fecha de emisión en vez
      de componer un rango imposible.
      - **No hay data migration, y es deliberado**: en este proyecto las
        migraciones están gitignored y CI regenera con `makemigrations`, así que
        una migración de datos se perdería en silencio y dejaría facturas viejas
        sin período. El respaldo en tiempo de lectura (`_periodo_facturacion`)
        cubre esas facturas sin depender del historial de migraciones.
      - **Firma de `generate_invoice_pdf_standalone` reducida** de
        `(invoice, customer, start_date, end_date, items)` a
        `(invoice, customer, items)`: los dos parámetros de fecha existían sólo
        para componer el texto del período. Mantenerlos habría dejado el bug
        esperando a que alguien los pasara distinto otra vez.
      - Los dos call sites pasaban `invoice.issue_date` **dos veces**, con un
        comentario que lo justificaba como "el único ancla disponible". Ese
        workaround era el origen del defecto y desapareció con la firma nueva.
      - `start_date`/`end_date` **se conservan** en el modelo y el formulario:
        alimentan el cálculo de duración y `ServiceSubscription.start_date`. No
        son el período impreso, y borrarlos sería otra tarea.
      - El campo va en la tarjeta "Período de Facturación", arriba de las fechas,
        que quedan rotuladas como datos operativos del cálculo.
- [ ] **T3** `U/M` = `U`. La descripción del ítem lleva "por meses"/"por días"
      según la categoría del servicio.
- [ ] **T4** `Contract.__str__` y `Certificate.__str__` delegan en
      `Customer.display_name`.
- [ ] **T5** `commercial_registry` deja de ser obligatorio y su obligatoriedad
      depende de `client_type`.
- [ ] **T6** `Customer.clean()` condicional: jurídica exige REEUP + NIT + cuenta;
      natural no. Se resuelve también el riesgo de `''` contra UNIQUE.
- [ ] **T7** `_contrato_de_factura` resuelve el contrato en facturas por lote en
      vez de leer una suscripción arbitraria.

### Etapa 2 — deuda estructural, documento aparte, NO en esta etapa

- `Contract.subscription` (OneToOne) → `Contract.customer` (1:N) + `Invoice.contract`.
- `ServiceSubscription.cost_center`, prellenado desde el prefijo del código.

### Selector de categoría — feature aparte

El selector de categoría de servicio con filtrado real en alta/edición de
suscripciones, con validación de servidor, es un encargo independiente
(sin datos, sin migración). Se entrega en su propio doc y sus propios commits.

## Restricciones

- JS vanilla + Tabler. **Sin npm, bundlers ni transpilación.**
- No quitar `FileHandlerMixin`; `InvoiceCostAllocation` no lleva archivos.
- `default_permissions = ()` + los 4 permisos custom en español en todo modelo nuevo.
- Migraciones **no versionadas** (`.gitignore`).
- Soft delete donde corresponda; si `InvoiceCostAllocation` es parte de la factura
  vive con ella y no se borra lógicamente por separado.
- Nada de secretos ni `media/`.
- Los commits no reescriben historia previa.

## Criterios de aceptación

- [x] El PDF de una factura con reparto de centros muestra exactamente las filas
      guardadas, con sus porcentajes, y valen 100 %.
- [x] No queda ningún literal de centro de costo en el template.
- [ ] El PDF nunca muestra "Desde X hasta X" con X == Y.
- [ ] El periodo se imprime tal como lo escribió el operador.
- [ ] `U/M` sale como `U` y la descripción conserva "por meses"/"por días".
- [ ] Una factura de una persona natural se puede generar sin registro comercial
      y sin contrato, y `Contract`/`Certificate` no imprimen `None`.
- [x] Guardar un reparto que no suma 100 % falla con mensaje en el formulario.
- [ ] Una factura por lote muestra el contrato correcto, no el de una suscripción
      arbitraria.
- [ ] `python manage.py check` y `python manage.py test apps.commercial` verdes;
      Ruff y djLint limpios.

## Verificación prevista

| Cambio | Comando |
|---|---|
| Modelos, vistas, forms, permisos | `python manage.py test apps.commercial` |
| Sólo templates | `djlint . --lint` + test dirigido del PDF |
| Chequeo siempre | `python manage.py check` |

## Modo TDD

El proyecto tiene suite y CI la ejecuta. Para cada tarea con resultado
determinista y esperado observable: **RED** (test que falla), **GREEN**
(corrección), **REFACTOR**. Para el render del PDF hay tests existentes en
`apps/commercial/tests/test_invoice_pdf.py` que sirven de red.

## Tamaño y estrategia de entrega

Pronóstico de líneas authored (adiciones + deleciones): ~285 para T1-T2, ~80 para
T3-T7. **Etapa 1 ≈ 365 authored lines**, dentro del presupuesto de ~400, así que
no hay que encadenar PRs todavía. Los commits van como unidades revisables en la
rama actual `feat/invoice-pdf-y-e2e`, que ya está 68 commits adelante de
`origin/main`.

Estrategia: `ask-on-risk`. Si el acumulado pasa ~400 líneas antes del siguiente
commit, se pregunta una vez por la estrategia de encadenado.

## Progreso

_(pendiente)_

## Próximo paso

T1: `InvoiceCostAllocation` con validación de suma 100, prefill desde el prefijo
del código de servicio, y render en el PDF en lugar del literal hardcodeado.
## Evidencia de T1

RED observado antes de implementar:

```
ImportError: cannot import name 'InvoiceCostAllocationFormSet' from
'apps.commercial.forms.invoice'
```

GREEN y verificación completa:

| Comando | Resultado |
|---|---|
| `python manage.py test apps.commercial.tests.test_invoice_cost_allocation` | 25 tests, OK |
| `python manage.py test apps.commercial` | 440 tests, OK (baseline previo: 415) |
| `python manage.py check` | no issues |
| `ruff check apps/commercial/` | All checks passed |
| `ruff format --check apps/commercial/` | 42 files already formatted |
| `djlint apps/commercial/templates/pages/commercial/invoice/ --check` | 0 files would be updated |

Fallos reales que los tests encontraron durante la implementación, y que están
corregidos:

1. `BaseFormSet` y `BaseModelFormSet` **no** tienen `add_error`; la vía idiomática
   para un error de formset es `raise ValidationError` dentro de `clean()`, que
   `BaseFormSet.full_clean` captura como error no-de-formulario.
2. `modelformset_factory` es obligatorio sobre `formset_factory` para que el
   formset conozca su modelo.
3. `instance` es un kwarg de **form**, no de formset: no se puede pasar la factura
   al formset para que resuelva la FK.

Tests existentes que hubo que actualizar, porque ahora el POST exige la imputación
(los tres POST estaban incompletos respecto del contrato nuevo):

- `apps/commercial/tests/test_invoice_regeneration.py`: `_formulario` y
  `_formulario_manual`.

## Pendiente para T3

`U/M` sigue siendo `M` y la descripción del ítem todavía no lleva "por meses" ni
"por días". El usuario ya confirmó que `U/M` pasa a `U` y que el período va dentro
de la descripción del servicio.

## Hallazgo de T2: un error de render se disfraza de 404

Al cambiar la firma de `generate_invoice_pdf_standalone`, el mock de
`test_download_generates_pdf_if_missing` seguía con los cinco parámetros viejos.
El `TypeError` lo tragaba el `except Exception` de `_generate_pdf_if_missing`, la
vista seguía, el PDF no se guardaba y la descarga respondía **404**. El fallo se
presentaba como un problema de lookup de factura cuando en realidad era una
firma desactualizada dos capas más abajo.

`_generate_pdf_if_missing` se traga cualquier excepción y deja que la descarga
devuelva un 404 sin explicación. Es un problema de diagnosticabilidad preexistente
y fuera del alcance de T2, pero conviene tenerlo anotado: la próxima vez que un
test de descarga falle con 404, revisar primero la firma de lo que se mockeó.
