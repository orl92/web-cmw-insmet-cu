# Solicitudes libres, periodos elegibles y estado real de la factura

## Objetivo

Que el cliente pueda pedir un servicio **las veces que quiera, en las fechas que
quiera y con la duración que elija en días o meses**, y que el dashboard diga la
verdad sobre si el PDF se generó y si el correo salió, en lugar de un único
"reintentando" que no distingue nada.

## Problema

Son tres problemas distintos que se NOS diagnosticaron en producción y que hoy
viven en el mismo flujo.

### 1. El periodo no lo elige el cliente

> **Estado: cerrado y superado.** Este es el diagnóstico original, cuando la
> suscripción *sí* tenía vigencia. Ya no describe el modelo: `end_date` y
> `Service.compute_end_date()` se eliminaron en `61197ac` porque la suscripción no
> vence, y `quantity` es sólo cantidad facturable. Se conserva como registro de
> por qué se quitó el selector de periodo, no como descripción del código actual.

`ServiceSubscription` ya **es** la solicitud: tiene `start_date`, `end_date`,
`quantity` y `payment_status`. No hay modelo nuevo que crear. El problema es
quién decide la duración:

- La **unidad** sale del servicio, no del cliente. `Service.compute_end_date()`
  hace `agrometeo → relativedelta(months=quantity)`, todo lo demás
  `timedelta(days=quantity)`.
- El **formulario del dashboard** tiene un `period` rígido de cuatro opciones
  (`1m`, `3m`, `6m`, `1y`, `custom`) que no corresponde a la unidad real.
- El **formulario público de home** sí usa `start_date` + `quantity`, pero con
  la unidad forzada por el servicio.

Consecuencia: un cliente que necesita 45 días no tiene forma de pedirlo sin
elegir `custom` y calcular la fecha a mano, y no puede pedir "2 años".

### 2. El guard de duplicados va al revés de lo que se recuerda

`apps/home/views/servicios/comerciales/views.py:152-160` bloquea una segunda
petición si ya hay una en `requested` o `pending`:

```python
existing = (
    ServiceSubscription.objects.filter(customer=customer, service=self.service)
    .filter(payment_status__in=['requested', 'pending'])
    .first()
)
if existing:
    messages.warning(request, 'Ya tienes una solicitud o suscripción para este servicio.')
```

Esto es lo **opuesto** al comportamiento buscado, y está fijado por tests
(`apps/commercial/tests/test_views.py:1371` y `:1394` aceptan el mensaje;
`apps/home/tests/test_services_ui.py:947` exige que no aparezca). Hay que
eliminar el guard **y** los tests que lo.codifican.

### 3. El estado del worker no distingue PDF de correo

`generate_invoice_pdf_and_email_task` hace las dos cosas en una sola función. Si
el correo falla, Huey reintenta la tarea **entera** y vuelve a renderizar el PDF
que ya estaba bien. El dashboard muestra `RETRYING` y el usuario no sabe si lo
que falló fue el PDF o el correo. En `Invoice` hoy existen `email_sent` y
`email_error`, pero **no hay estado ni error del PDF**: la única señal de que el
PDF existe es que el archivo esté en disco.

De ahí salen las dos quejas de UX:

- **Botones siempre visibles.** `invoice/list.html:69` y `:81-87` pintan el
  enlace de descarga y el modal de vista previa sin condicionar a que el PDF
  exista.
- **El reintento abre una fila nueva.** `TaskMonitoringActionView.post()`
  (`apps/dashboard/views/dashboard/dashboard.py:462-477`) reencola la función y
  **nunca toca el registro**: la tarea nueva nace con otro `task.id`, y
  `apps/core/apps.py:108-120` hace `update_or_create(task_id=task.id)`, así que
  crea una fila nueva. La fila del error original queda congelada para siempre.

La tabla tampoco dice de quién es la tarea: solo `task_name` y `task_id`.

## Por qué importa

El PDF se genera bien y el correo falla —que es el caso normal sin SMTP real— y
el operador ve "reintentando" sobre un PDF que ya existe. Eso hace creer que
hay un problema de renderizado que no existe, y hace que el botón de "ver
factura" aparezca para facturas que quizá ni siquiera tienen archivo.

## Alcance

### A. Persona natural con nombre y carnet

- **A1** Nombre y apellidos en la persona natural, junto al documento de
  identidad, para que el bloque de la factura no sea un campo suelto.
- **A2** El listado de clientes debe mostrar el carnet en la columna
  Identificación cuando es persona natural. Hoy `customer/list.html:42-44` solo
  renderiza `reeup` y `nit`, que son de la jurídica.

### B. Solicitudes y periodos

- **B1** Quitar el guard de duplicados: tantas solicitudes como quiera el
  cliente. Actualizar los tests que lo codifican.
- **B2** Fecha de inicio libre, incluso en el pasado, y **cantidad** de días o
  meses. La unidad no la elige quien captura: sale de la categoría del servicio
  (`service_category` → `Service.get_billing_period_display()`), igual que en la
  facturación manual (B4) y en el alta pública de Home. Cerrado en `5d4fa30` y
  revisado en la UI (el vencimiento se calcula y guarda, pero no se presenta
  mientras la suscripción está `requested`).
- **B3** Formularios de crear y editar suscripción alineados al modelo nuevo:
  método de pago elegible al crear, estado de pago no elegible, y el estilo de
  formulario del dashboard. Cerrado con la revisión de B2.
- **B4** Facturación manual alineada al mismo modelo.
- **B5** Quitar la columna Expiración del listado de suscripciones
  (`subscription/list.html:15` y celda `:46-47`): con historial completo la
  expiración deja de ser el eje de la tabla.
- **B6** Home "mis servicios" y dashboard: mostrar **todas** las solicitudes
  como histórico, no solo las vigentes.

### C. Estado real de la factura

- **C1** Estado y error explícitos del PDF en `Invoice`, no implícitos en la
  existencia del archivo.
- **C2** Botones de ver y descargar solo cuando el PDF se generó bien.
- **C3** Poder reintentar solo el paso que falló, sin re-renderizar el PDF.
- **C4** El reintento actualiza la **misma** fila de la tabla de tareas.
- **C5** La tabla de tareas dice de qué cliente es cada tarea.

### D. Pendientes anteriores

- **D1** `Invoice #14` quedó con `subscription_id = NULL`, así que no encuentra
  el contrato aunque exista en su suscripción. Averiguar por qué la factura
  manual no enganchó la suscripción.
- **D2** `Profile.save()` revienta con `OSError: Truncated File Read` al
  re-guardar el avatar (Pillow). Falla en aislamiento; `apps/user_auth` no fue
  tocado por este trabajo.
- **D3** Documentar que **todo cambio en `apps/core/tasks.py` exige reiniciar el
  consumer**. El módulo se importa al arrancar el worker, mientras que
  `invoice_utils` se importa dentro de la función: si no se reinicia, el worker
  ejecuta una llamada vieja contra una firma nueva y tira
  `TypeError: takes 5 positional arguments but 6 were given`. Es exactamente lo
  que pasó hoy.

## Decisiones abiertas (bloquean la implementación)

1. **¿Dónde vive el nombre de la persona natural?** Reusar
   `User.first_name`/`last_name` (ya existen, la factura ya lee
   `get_full_name()`, cero migración, una sola fuente de verdad) o agregar campos
   a `Customer` (migración, autosuficiente, sobrevive a que se edite el usuario).
2. **¿Cómo se separa el estado del PDF del correo?** Agregar a `Invoice` estado
   y error de PDF y mantener **una sola** tarea Huey que va marcando cada paso
   (recomendado: los botones dependen del estado del PDF, y el reintento
   naturally cae en la misma fila) o partir en **dos** tareas Huey independientes
   (más fiel a "saber qué falló", pero duplica filas en la tabla de monitoreo).
3. **¿Cómo se representa el periodo? — CERRADA en `5d4fa30`.** No se agregó
   `period_unit`. La unidad ya sale de `service_category`
   (`Service.get_billing_period_display()`), que B4 y el alta pública de Home ya
   trataban como única fuente; preguntarla al usuario en el formulario abriría
   una segunda fuente de verdad y dejaría el precio por período sin coherencia
   con el vencimiento. La alternativa de pedir inicio y fin y derivar la
   cantidad del delta se descartó porque el precio necesita una magnitud
   (`quantity`), no una cantidad de días implícita.

## Restricciones

- `requirements/` ya no es WIP del usuario: `redis` y `whitenoise` pasaron a
  `prod.txt` en el commit `534286b`, junto con el fix que impedía que un driver
  ausente se convirtiera en un 500.
- Las migraciones no se versionan en este repo.
- Los datos reales de la BD (`admin`, `osniel`, factura `2026-0001`) no se tocan.
- Nada de npm ni bundler; el frontend es JS vanilla.

## Criterios de aceptación

- Un cliente natural ve nombre, apellidos y carnet en la factura y en el listado
  de clientes, sin líneas vacías.
- Un cliente puede crear una segunda suscripción del mismo servicio sin
  bloqueo, con fecha de inicio pasada y duración en días o en meses.
- El listado de suscripciones no tiene columna Expiración y muestra el histórico
  completo.
- La factura manual acepta el mismo modelo de periodo.
- Los botones de ver y descargar una factura solo existen si el PDF se generó.
- Un fallo de correo no hace que el PDF se vuelva a renderizar ni que la tarea
  aparezca como reintentándose cuando el PDF ya está bien.
- Reintentar una tarea actualiza su fila y no crea otra.
- La tabla de tareas muestra el cliente.

## Checks aplicables

| Cambio | Verificación |
|---|---|
| Modelos, vistas, formularios, permisos | `python manage.py test apps.commercial apps.home apps.core apps.dashboard` |
| Plantillas | `djlint . --lint` y `djlint . --reformat --check` (los hooks) |
| Todo | `python manage.py check` + Ruff |

## Progreso

- [x] Diagnóstico completo de los tres problemas, con file:line.
- [ ] A1, A2
- [x] B1, B2, B3, B5, B6 → B1 y B5 cerrados en `2a7dbad`, B2 y B3 en `5d4fa30` y
      corregidos en la revisión de UI (alcance y cifras al final del documento)
- [x] B4 — commit `385c12a`
- [x] C1, C2, C3, C4, C5 — commit `4b1dff5`
- [x] D1 — commit `7e36058`
- [x] D2 — commits `0ce468a`…`1b644fc`
- [ ] D3

**B4 cerrado.** La línea manual ya deriva `codigo`, `precio` y `unidad_medida`
del `Service` en `clean()`, así que el POST no fija el precio; `cantidad` es
required y editable, y la plantilla propone. `service_category` viaja al
navegador porque la unidad no es elegible: sale de la categoría.

**Un límite del modelo que conviene no olvidar:** el servidor calcula el
vencimiento como `start + relativedelta(months=N)`, y eso no reproduce
cualquier par (inicio, fin) — entre 01/01 y 31/01 no existe ningún N entero.
La cantidad en meses que propone el navegador redondea contra el promedio real
del año (mediana de 2 días de desvío), pero el residuo no baja de medio mes
mientras el modelo acepte sólo meses enteros. **B2 resolvió el lado de la
captura** (quien entra elige inicio y cantidad, nunca inicio y fin, así que el
par imposible ya no se puede escribir), pero **el residuo de meses enteros
sigue abierto** y es una decisión de modelo: `period_unit` por servicio con
fracción de mes, o aceptar el redondeo.

**B1 cerrado.** El bloqueo de duplicados estaba en **dos** capas: `form_valid`
descartaba el POST (`apps/home/views/servicios/comerciales/views.py:152`) y el
template escondía el formulario (`service_detail.html:65`). Quitar solo una
deja el comportamiento a medias, así que caerán las dos: el aviso queda
informativo sobre lo ya solicitado y la vía de pedir sigue abierta. Los
cuatro tests que afirmaban el bloqueo se reescribieron como afirmaciones del
comportamiento nuevo, no se borraron.

**B5 cerrado.** El listado de suscripciones perdió la columna Expiración y el
badge Vencido que colgaba de ella. Ningún test dependía de esa columna.

**D1 cerrado.** La factura canónica de una suscripción se resuelve por línea
(`InvoiceItem`) con `Invoice.objects.for_subscription()`, con el ancla
`Invoice.subscription` como fallback para facturas de una sola suscripción. El
comando `repair_invoice_subscriptions` reparó 2 facturas huérfanas y es
idempotente.

**Estados unificados (este bloque).** El estado de suscripción y el de factura
son DERIVADOS, no campos nuevos:

- `ServiceSubscription.status_display` devuelve `solicitado` / `pendiente` /
  `pagado` / `cancelada`; `cancelada` deriva de `record_active=False` (baja
  lógica) y no se duplica en `payment_status`.
- `payment_status='expired'` era un estado muerto: ninguna ruta productiva lo
  escribía, sólo los tests. Se eliminó de `PAYMENT_STATUS_CHOICES`.
- `Invoice.status_display` devuelve `pagada` (tiene suscripciones y todas
  `paid`), `cancelada` (`is_cancelled`) o `pendiente`. `InvoiceQuerySet
  .with_display_status()` anota `items_total` / `items_paid` para que la columna
  Estado no dispare una consulta por fila.
- Los contadores y badges `expired` se eliminaron; `menu_notifications()` pasó
  a agregados condicionales (una consulta por lado).
- Los listados de suscripción y factura colapsan las columnas Pago/Registro en
  una sola columna Estado.

**Documentos acumulativos.** Antes la rama `is_active` del card de Home y la
del listado mostraban sólo el certificado, así que la factura desaparecía
justo cuando el cliente la necesitaba como respaldo. Ahora el botón de factura
y el de certificado se renderizan por separado en ambos listados, con labels
distinguibles (`Ver Factura` / `Ver Certificado`) en vez del ambiguo `Ver PDF`.
El botón de factura del card de Home pasó a abrir el modal `data-pdf-*`.

**Orden de acciones.** Editar y el botón destructivo quedan siempre al final de
la fila; las acciones de estado (Facturar / Aprobar Pago / Regenerar) van
primero.

**Sobre `record_active` y la visibilidad de canceladas:** `SoftDeleteModel` no
filtra en el manager, cada vista lo hace explícitamente. El listado staff de
suscripciones NO filtra, así que las canceladas aparecen con el label
`Cancelada`; el listado de Home del cliente sí filtra `record_active=True`, así
que no se ven ahí. Esa asimetría es intencional y está cubierta por tests.

**Verificación (bloque de estados):** `python manage.py test` → 1058 tests OK.
`ruff check apps templates` limpio. La aserción de no-N+1 compara el conteo de
consultas entre un listado de 1 y de 4 facturas (en vez de fijar un número
absoluto, porque el layout y los context processors aportan consultas fijas).

## B2/B3 cerrados — `5d4fa30`, revisados en la UI

**Qué cambió.** `SubscriptionForm` ya no tiene `period` ni `end_date`: quien
captura elige **fecha de inicio** (el pasado está permitido) y **cantidad**, y el
vencimiento lo derivaba `Service.compute_end_date` —función que `61197ac`
eliminó junto con `end_date` al decidir que la suscripción no vence. La unidad no
es un campo: sale de la categoría del servicio, que cada `<option>` publica en
`data-period-unit`. `quantity` es la magnitud que multiplica el precio, igual que
en B4, y por eso sigue siendo necesaria aunque ya no mida vigencia.

**Por qué no `period_unit`.** Ver la decisión 3 de "Decisiones abiertas". La
fuerza estaba en el mismo sitio donde B4 ya la había puesto: la categoría.

**Un detalle que salió en el camino:** `start_date` es un campo declarado, así
que sin `label` explícito Django lo rotula con el nombre del atributo
("Start date") e ignora el `verbose_name` del modelo. Llevaba así desde antes de
este bloque y salía en inglés en una interfaz `es-mx`; ahora dice "Fecha de
inicio", con test que lo ata.

### Revisión de la interfaz (B2/B3, segunda pasada)

La primera entrega resolvió el modelo pero no la pantalla: el formulario quedó
con la apariencia de una maqueta y con piezas que ya no servían. Lo corrigió la
revisión de UI, y el alcance de B2/B3 queda así:

- **El vencimiento desapareció del modelo, no sólo de la pantalla.** Una primera
  pasada lo había quitado de la UI y de la facturación, pero `end_date` seguía en
  `ServiceSubscription` porque `_post_clean` validaba `start < end`. La decisión
  de producto fue más tajante: **una suscripción no vence por tiempo**. Se
  solicita, se factura, se aprueba el pago y queda viva; el único fin de su
  existencia es la cancelación, y sólo se permite si todavía no se emitió una
  factura vigente ni se aprobó el pago. `61197ac` eliminó `end_date`,
  `Service.compute_end_date()`, `SubscriptionRenewView` y las métricas de
  vencidas y por vencer (`c15f428`). Consecuencia directa: `quantity` dejó de
  medir vigencia y es sólo cantidad facturable; la unidad sale de la categoría.
- **`payment_status` no es elegible al crear.** `SubscriptionCreateView.form_valid`
  fija `requested` explícitamente para que ni el formulario ni un POST a mano
  puedan crear una suscripción ya pagada. **Motivo:** el estado no lo elige quien
  captura, lo mueven las acciones (Facturar / Aprobar Pago); ofrecer un selector
  invita a saltárselas. Al no estar en `Meta.fields`, el ModelForm de la edición
  tampoco lo toca: una suscripción `paid` sigue `paid`.
- **`payment_method` sí se elige al crear**, y es required: las choices salen de
  `ServiceSubscription.PAYMENT_METHOD_CHOICES` y los radios son los mismos de
  Home. Se pidió para que la solicitud llegue con el medio de pago decided, que
  es lo que la factura necesita después.
- **Se conserva un JS mínimo para la etiqueta de la cantidad.** El que había
  (`subscription-period.js`) hacía dos cosas y una ya no era correcta:
  previsualizar el vencimiento. Se sustituyó por
  `static/dist/js/subscription-quantity-label.js`, que **sólo** rotula. **Motivo:**
  "3" son tres meses en agrometeo y tres días en pronóstico, y una etiqueta fija
  "Cantidad" esconde justo lo que explica el importe. Sin JavaScript el rótulo
  igual es correcto: el servidor lo imprime con la unidad cuando el servicio ya
  está elegido (edición y POST que rebota), y en el alta en blanco, donde todavía
  no hay unidad que nombrar, lo que la comunica es el `help_text`.
- **Cinco campos, dos cards**: "Datos de la Solicitud" (cliente, servicio, inicio,
  cantidad) y "Método de pago". Tres cards partían el formulario en trozos sin
  sentido. El título de la segunda nombra el grupo: los radios llevan
  `role="radiogroup"` con `aria-labelledby` al título, que es lo que un
  `form-selectgroup` necesita para tener nombre accesible (un `<label>` suelto no
  era label de nada). Para eso `includes/dashboard/form_card.html` acepta un
  `card_title_id` opcional; sin él la salida no cambia.

**Un defecto que ningún test de Python veía:** los dos templates pedían
`{% static 'dist/js/subscription-period.js' %}` con el archivo borrado, así que
cada alta y cada edición pedía un asset inexistente (404 silencioso; Django no
se queja). Ahora hay un test que resuelve contra el finder **cada** `<script
src>` estático que pide la página del formulario, que es la clase de defecto que
no se ve desde Python.

**Verificación (esta revisión):** `python manage.py test` → 1170 tests,
`FAILED (failures=1)`. El único fallo es
`apps.core.tests.test_site_configuration_template.test_reset_theme_defaults_button_and_modal`,
**preexistente**: se reproduce en `0061521` con el árbol limpio, antes de tocar
nada, y no lo causa este cambio. `python manage.py test apps.commercial apps.home`
→ 659 tests OK. `python manage.py check` sin issues, `ruff check apps templates`
limpio, `djlint . --lint` y `djlint . --reformat --check` limpios.

**Pendiente de esta etapa:** nada de B2/B3 quedó pendiente dentro del alcance
acordado. Queda abierto, pero es decisión de modelo y no de formulario: el
residuo de meses enteros (ver el límite del modelo más arriba).

**Ruta prevista:** B6 y D3 siguen abiertos. B6 toca Home y el dashboard; D3 es
documentación y va inline.

---

## La suscripción no vence — `61197ac`, `c15f428`, `4296f4b`, `e7d2049`

**Decisión de producto.** La suscripción nace viva y **no muere por tiempo**. Se
solicita, se factura, se aprueba el pago, se entrega el certificado y sigue
funcionando. Su única condición de fin es la **cancelación**, y sólo se permite
mientras no haya una factura vigente ni un pago aprobado.

**Por qué se tira `end_date` y no se oculta.** La primera pasada lo había
escalonado en la capa de presentación: `end_date` seguía en el modelo y
`_post_clean` seguía validando `start < end`, así que "ocultar el vencimiento"
era una mentira de la pantalla. La regla real es más simple y más dura, y la
decisión fue borrarlo. Eso arrastra tres consecuencias que conviene no volver a
inventar:

- `quantity` dejó de medir vigencia. Es **cantidad facturable**: multiplica el
  precio, y la unidad (días o meses) la sigue imponiendo la categoría del
  servicio. Por eso el campo no se fue con `end_date`.
- `is_active` pasó a ser `record_active AND payment_status == 'paid'`. No mira
  fechas, así que una suscripción pagada de hace un año sigue activa.
- Desaparecieron `SubscriptionRenewView`, la URL `suscripcion_renew`, la
  plantilla `renew.html`, `subscription-period.js` y las métricas de *vencidas* y
  *por vencer* del dashboard.

**La regla de cancelación y su borde.** Cancelar está permitido si `requested` y
no hay facturas, y también si la única factura asociada está **anulada**: una
factura anulada ya no compromete un cobro, que es la diferencia entre "tiene
factura" y "tiene factura vigente". Con una factura vigente o el pago aprobado, la
anulación se rechaza. Están los cuatro casos con test en `test_views.py`.

**Una decisión que sigue siendo del usuario, no del código.** El periodo
facturado vive en `InvoiceForm.start_date`/`end_date` y **no** está persistido en
`Invoice`: el PDF lo recibe por parámetro y el modelo sólo guarda `issue_date`.
Mientras la suscripción no vence eso es coherente (el periodo es un dato de la
factura, no de la suscripción), pero si alguna vez se necesita reimprimir una
factura vieja con su periodo original, hoy no está de donde sacarlo.

**Qué rompió el agrupado de la pantalla de factura.** Las pendientes se agrupaban
por período con un switch por grupo que fijaba las fechas y bloqueaba el resto de
los checkboxes. Ese agrupamiento existía *porque* la suscripción traía su
vencimiento. Sin `end_date` no hay nada que agrupar y el código quedó inerte
leyendo `dataset.end` y `dataset.days`, que el endpoint ya no emitía. Ahora las
pendientes se listan planas y las marcadas se facturan juntas en el período del
formulario (`4296f4b`).

**Verificación:** `python manage.py test` → 1175 tests,
`FAILED (failures=1)`. El único fallo sigue siendo
`apps.core.tests.test_site_configuration_template.test_reset_theme_defaults_button_and_modal`
("Restablecer tema"), preexistente y ajeno: se reproduce en `0061521` con el
árbol limpio. `python manage.py check` sin issues, `ruff check apps` y
`ruff format --check apps` limpios, `djlint . --lint` y
`djlint . --reformat --check` limpios.
